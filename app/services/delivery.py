from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.delivery_evidence import DeliveryEvidence
from app.schemas.delivery import DeliveryCreate
from app.schemas.delivery_evidence import EvidenceItem
from app.services.settlement import settle_commitment
from app.services.evidence_validator import validate_evidence
from app.core.logging import log


class EvidenceValidationFailedError(Exception):
    """Raised when evidence validation fails."""
    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__(f"Evidence validation failed. Provide valid Repo: {errors}")


def deliver_commitment(
    db: Session,
    commitment_id: int,
    payload: DeliveryCreate,
    evidences: Optional[List[EvidenceItem]] = None,
):
    """
    Deliver a commitment. This is idempotent:
    - If already delivered/settled, returns existing delivery
    - If locked, creates new delivery and auto-settles
    - Otherwise raises ValueError
    
    If evidences are provided:
    - Each evidence is validated (GitHub repos, screenshots)
    - All evidences must pass validation OR be deferred (rate limited/timeout)
    - At least one evidence must be successfully validated
    - Delivery fails if no evidence can be validated
    """
    print(">>> deliver_commitment CALLED for", commitment_id)

    # Use FOR UPDATE to lock the row and prevent race conditions
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .with_for_update()
        .one_or_none()
    )
    if not commitment:
        raise ValueError("Commitment not found")

    print(f">>> Commitment status: {commitment.status}")

    # IDEMPOTENT: If already delivered or settled, return existing delivery
    if commitment.status in ("delivered", "settled"):
        existing = (
            db.query(Delivery)
            .filter(Delivery.commitment_id == commitment_id)
            .first()
        )
        if existing:
            print(">>> Already delivered/settled, returning existing delivery")
            return existing
        else:
            # Settled without delivery (e.g., expired) - still return success info
            raise ValueError(f"Commitment is already {commitment.status}")
    
    # IDEMPOTENT: If expired, cannot deliver anymore
    if commitment.status == "expired":
        raise ValueError("Cannot deliver - commitment has expired")
    
    # Only allow delivery if locked
    if commitment.status != "locked":
        raise ValueError(f"Cannot deliver in status '{commitment.status}'")

    # Double-check for existing delivery with lock held
    existing = (
        db.query(Delivery)
        .filter(Delivery.commitment_id == commitment_id)
        .first()
    )
    if existing:
        print(">>> Existing delivery found (race condition prevented), returning it")
        return existing

    # =====================================================================
    # EVIDENCE VALIDATION (NEW)
    # =====================================================================
    evidence_records: List[DeliveryEvidence] = []
    validation_errors: List[Dict[str, Any]] = []
    validated_count = 0
    
    if evidences:
        log.info(
            "delivery: evidence submission started",
            extra={"commitment_id": commitment_id, "evidence_count": len(evidences)}
        )
        
        for evidence in evidences:
            log.info(
                "delivery: validating evidence",
                extra={
                    "commitment_id": commitment_id,
                    "type": evidence.type,
                    "url": evidence.url
                }
            )
            
            is_valid, metadata, error = validate_evidence(evidence.type, evidence.url)
            
            if is_valid:
                validated_count += 1
                log.info(
                    "delivery: evidence validation success",
                    extra={"commitment_id": commitment_id, "type": evidence.type, "url": evidence.url}
                )
            else:
                # Check if this is a deferrable error (rate limit / timeout)
                is_deferrable = metadata and (metadata.get("rate_limited") or metadata.get("timeout"))
                
                if not is_deferrable:
                    log.warning(
                        "delivery: evidence validation failed",
                        extra={
                            "commitment_id": commitment_id,
                            "type": evidence.type,
                            "url": evidence.url,
                            "error": error
                        }
                    )
                    validation_errors.append({
                        "type": evidence.type,
                        "url": evidence.url,
                        "error": error
                    })
            
            # Create evidence record (will be inserted later if no hard failures)
            evidence_record = DeliveryEvidence(
                type=evidence.type,
                url=evidence.url,
                evidence_metadata=metadata,
                validated=is_valid,
                validated_at=datetime.now(timezone.utc) if is_valid else None,
            )

            evidence_records.append(evidence_record)
        
        # Check if there are hard validation failures (not rate limited/timeout)
        if validation_errors:
            log.warning(
                "delivery: evidence validation failed - rolling back",
                extra={"commitment_id": commitment_id, "errors": validation_errors}
            )
            raise EvidenceValidationFailedError(validation_errors)
        
        # Check if at least one evidence was validated
        if validated_count == 0:
            log.warning(
                "delivery: no evidence validated (all rate limited/timeout)",
                extra={"commitment_id": commitment_id}
            )
            # Still allow delivery but settlement will block later
    
    # =====================================================================
    # CREATE DELIVERY (EXISTING LOGIC, UNCHANGED)
    # =====================================================================
    
    # Create new delivery
    delivery = Delivery(
        commitment_id=commitment_id,
        artifact_type=payload.artifact_type,
        artifact_reference=payload.artifact_reference,
    )

    commitment.status = "delivered"

    print(">>> Inserting delivery row")
    db.add(delivery)
    db.add(commitment)
    
    try:
        db.commit()
        db.refresh(delivery)
    except IntegrityError:
        db.rollback()
        # Race condition: another request created the delivery
        existing = db.query(Delivery).filter(Delivery.commitment_id == commitment_id).first()
        if existing:
            print(">>> IntegrityError caught, returning existing delivery")
            return existing
        raise

    # =====================================================================
    # INSERT EVIDENCE RECORDS (NEW)
    # =====================================================================
    if evidence_records:
        for record in evidence_records:
            record.delivery_id = delivery.id
            db.add(record)
        
        try:
            db.commit()
            log.info(
                "delivery: evidence records saved",
                extra={
                    "commitment_id": commitment_id,
                    "delivery_id": delivery.id,
                    "evidence_count": len(evidence_records),
                    "validated_count": validated_count
                }
            )
        except Exception as e:
            log.error(
                "delivery: failed to save evidence records",
                extra={"commitment_id": commitment_id, "error": str(e)}
            )
            # Don't fail delivery if evidence insert fails
            db.rollback()

    print(">>> Delivery committed, now settling")
    
    # Auto-settle after delivery
    try:
        settlement = settle_commitment(db, commitment_id)
        print(">>> Settlement complete")
        return {
            "delivery": delivery,
            "settlement": settlement,
            "evidence_count": len(evidence_records),
            "validated_count": validated_count,
        }
    except Exception as e:
        print(f">>> Settlement failed: {e}")
        # Delivery was successful, just return it
        return {
            "delivery": delivery,
            "settlement": None,
            "settlement_error": str(e),
            "evidence_count": len(evidence_records),
            "validated_count": validated_count,
        }
