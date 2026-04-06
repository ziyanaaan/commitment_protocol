"""
Admin API routes for financial oversight and platform control.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.admin_auth import get_current_admin, log_admin_action, get_client_ip
from app.models.user import User
from app.models.commitment import Commitment
from app.models.payment import Payment
from app.models.settlement import Settlement
from app.models.ledger import LedgerEntry
from app.models.admin_audit import AdminAuditLog
from app.models.system_settings import SystemSetting


router = APIRouter(prefix="/admin", tags=["admin"])


# =============================================================================
# FINANCIAL OVERVIEW
# =============================================================================

@router.get("/overview")
def get_financial_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get financial overview metrics.
    All admins have access.
    """
    # Total captured funds (sum of all paid payments)
    total_captured = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "paid"
    ).scalar()
    
    # Total payouts (sum of all settlement payouts)
    total_payouts = db.query(func.coalesce(func.sum(Settlement.payout_amount), 0)).scalar()
    
    # Total refunds (sum of all settlement refunds)
    total_refunds = db.query(func.coalesce(func.sum(Settlement.refund_amount), 0)).scalar()
    
    # Held funds (paid but not settled)
    held_funds = db.query(func.coalesce(func.sum(Payment.amount), 0)).join(
        Commitment, Commitment.id == Payment.commitment_id
    ).filter(
        Payment.status == "paid",
        Commitment.status.notin_(["settled", "expired"])
    ).scalar()
    
    # Today's volume
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    todays_volume = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "paid"
    ).scalar()  # Note: Would need created_at on Payment for actual today filter
    
    # Pending settlements (delivered but not settled)
    pending_settlements = db.query(func.count(Commitment.id)).filter(
        Commitment.status == "delivered"
    ).scalar()
    
    return {
        "total_captured": float(total_captured),
        "total_payouts": float(total_payouts),
        "total_refunds": float(total_refunds),
        "held_funds": float(held_funds),
        "available_balance": float(Decimal(str(total_captured)) - Decimal(str(total_payouts)) - Decimal(str(total_refunds))),
        "todays_volume": float(todays_volume),
        "pending_settlements": pending_settlements,
    }


@router.get("/health")
def get_platform_health(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get platform balance health status.
    GREEN = balanced, ORANGE = drift detected, RED = critical mismatch
    """
    # Calculate expected balance
    total_captured = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "paid"
    ).scalar()
    
    total_payouts = db.query(func.coalesce(func.sum(Settlement.payout_amount), 0)).scalar()
    total_refunds = db.query(func.coalesce(func.sum(Settlement.refund_amount), 0)).scalar()
    
    expected_balance = Decimal(str(total_captured)) - Decimal(str(total_payouts)) - Decimal(str(total_refunds))
    
    # Get ledger balance (if using ledger)
    ledger_balance = db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).scalar()
    
    # Calculate drift
    drift = abs(expected_balance - Decimal(str(ledger_balance))) if ledger_balance else Decimal("0")
    
    # Determine status
    if drift == 0:
        status = "GREEN"
        message = "Platform balance is healthy"
    elif drift < Decimal("100"):
        status = "ORANGE"
        message = f"Minor drift detected: ₹{drift}"
    else:
        status = "RED"
        message = f"Critical mismatch: ₹{drift}"
    
    return {
        "status": status,
        "message": message,
        "expected_balance": float(expected_balance),
        "ledger_balance": float(ledger_balance) if ledger_balance else 0,
        "drift": float(drift),
        "total_captured": float(total_captured),
        "total_payouts": float(total_payouts),
        "total_refunds": float(total_refunds),
    }


# =============================================================================
# COMMITMENT FINANCIAL VIEW
# =============================================================================

@router.get("/commitments/search")
def search_commitments(
    q: Optional[str] = Query(None, description="Search by ID, title, or user ID"),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Search commitments with filters."""
    query = db.query(Commitment)
    
    if q:
        # Try to parse as ID
        try:
            commit_id = int(q)
            query = query.filter(Commitment.id == commit_id)
        except ValueError:
            # Search by title
            query = query.filter(Commitment.title.ilike(f"%{q}%"))
    
    if status:
        query = query.filter(Commitment.status == status)
    
    total = query.count()
    commitments = query.order_by(desc(Commitment.id)).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "amount": float(c.amount),
                "deadline": c.deadline.isoformat() if c.deadline else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in commitments
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/commitments/{commitment_id}/financial")
def get_commitment_financial_timeline(
    commitment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get full financial timeline for a commitment (dispute resolution view)."""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    # Get payment
    payment = db.query(Payment).filter(Payment.commitment_id == commitment_id).first()
    
    # Get settlement
    settlement = db.query(Settlement).filter(Settlement.commitment_id == commitment_id).first()
    
    # Get ledger entries for this commitment
    ledger_entries = db.query(LedgerEntry).filter(
        LedgerEntry.commitment_id == commitment_id
    ).order_by(LedgerEntry.created_at).all()
    
    # Log this action
    log_admin_action(
        db=db,
        admin_user_id=admin.id,
        action_type="commitment_view",
        target_type="commitment",
        target_id=commitment_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return {
        "commitment": {
            "id": commitment.id,
            "title": commitment.title,
            "description": commitment.description,
            "status": commitment.status,
            "amount": float(commitment.amount),
            "deadline": commitment.deadline.isoformat() if commitment.deadline else None,
            "decay_curve": commitment.decay_curve,
            "created_at": commitment.created_at.isoformat() if commitment.created_at else None,
        },
        "payment": {
            "id": payment.id if payment else None,
            "order_id": payment.order_id if payment else None,
            "payment_id": payment.payment_id if payment else None,
            "amount": float(payment.amount) if payment else None,
            "status": payment.status if payment else None,
        } if payment else None,
        "settlement": {
            "id": settlement.id if settlement else None,
            "payout_amount": float(settlement.payout_amount) if settlement else None,
            "refund_amount": float(settlement.refund_amount) if settlement else None,
            "delay_minutes": settlement.delay_minutes if settlement else None,
            "decay_applied": settlement.decay_applied if settlement else None,
            "settled_at": settlement.settled_at.isoformat() if settlement and settlement.settled_at else None,
        } if settlement else None,
        "ledger_entries": [
            {
                "id": le.id,
                "entry_type": le.entry_type,
                "amount": float(le.amount),
                "running_balance": float(le.running_balance),
                "reference_type": le.reference_type,
                "reference_id": le.reference_id,
                "created_at": le.created_at.isoformat() if le.created_at else None,
            }
            for le in ledger_entries
        ],
    }


# =============================================================================
# LEDGER EXPLORER
# =============================================================================

@router.get("/ledger")
def get_ledger_entries(
    user_id: Optional[int] = Query(None),
    commitment_id: Optional[int] = Query(None),
    entry_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Explore ledger entries with filters."""
    query = db.query(LedgerEntry)
    
    if user_id:
        query = query.filter(LedgerEntry.user_id == user_id)
    if commitment_id:
        query = query.filter(LedgerEntry.commitment_id == commitment_id)
    if entry_type:
        query = query.filter(LedgerEntry.entry_type == entry_type)
    if date_from:
        query = query.filter(LedgerEntry.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(LedgerEntry.created_at <= datetime.fromisoformat(date_to))
    
    total = query.count()
    entries = query.order_by(desc(LedgerEntry.created_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": e.id,
                "commitment_id": e.commitment_id,
                "user_id": e.user_id,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "running_balance": float(e.running_balance),
                "reference_type": e.reference_type,
                "reference_id": e.reference_id,
                "description": e.description,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# =============================================================================
# SYSTEM SETTINGS / KILL SWITCHES
# =============================================================================

@router.get("/settings/kill-switch")
def get_kill_switches(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get all kill switch statuses."""
    # Default switches
    switches = {
        "payouts_paused": False,
        "refunds_paused": False,
        "all_transfers_paused": False,
    }
    
    # Get from database
    settings = db.query(SystemSetting).filter(
        SystemSetting.key.in_(switches.keys())
    ).all()
    
    for s in settings:
        switches[s.key] = s.value
    
    return switches


@router.post("/settings/kill-switch")
def toggle_kill_switch(
    key: str,
    value: bool,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Toggle a kill switch."""
    valid_keys = ["payouts_paused", "refunds_paused", "all_transfers_paused"]
    if key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Invalid key. Must be one of: {valid_keys}")
    
    # Get or create setting
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        old_value = setting.value
        setting.value = value
        setting.updated_by = admin.id
    else:
        old_value = False
        setting = SystemSetting(
            key=key,
            value=value,
            description=f"Kill switch: {key}",
            updated_by=admin.id,
        )
        db.add(setting)
    
    db.commit()
    
    # Log this action
    log_admin_action(
        db=db,
        admin_user_id=admin.id,
        action_type="kill_switch_toggle",
        target_type="setting",
        details={"key": key, "old_value": old_value, "new_value": value},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return {"key": key, "value": value, "message": f"Kill switch '{key}' set to {value}"}


# =============================================================================
# AUDIT LOGS
# =============================================================================

@router.get("/audit-logs")
def get_admin_audit_logs(
    admin_user_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get admin audit logs."""
    query = db.query(AdminAuditLog)
    
    if admin_user_id:
        query = query.filter(AdminAuditLog.admin_user_id == admin_user_id)
    if action_type:
        query = query.filter(AdminAuditLog.action_type == action_type)
    
    total = query.count()
    logs = query.order_by(desc(AdminAuditLog.created_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": log.id,
                "admin_user_id": log.admin_user_id,
                "action_type": log.action_type,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# =============================================================================
# PAYOUT & REFUND CONTROL
# =============================================================================

@router.get("/payouts")
def get_payouts(
    status: Optional[str] = Query(None, description="Filter by settlement status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get payout records (settlements with payout > 0)."""
    query = db.query(Settlement).filter(Settlement.payout_amount > 0)
    
    total = query.count()
    settlements = query.order_by(desc(Settlement.settled_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": s.id,
                "commitment_id": s.commitment_id,
                "payout_amount": float(s.payout_amount),
                "refund_amount": float(s.refund_amount),
                "delay_minutes": s.delay_minutes,
                "decay_applied": s.decay_applied,
                "settled_at": s.settled_at.isoformat() if s.settled_at else None,
            }
            for s in settlements
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/payouts/queue")
def get_payout_queue(
    status: Optional[str] = Query(None, description="Filter by payout status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get financial payout queue from payouts table."""
    from sqlalchemy import text
    
    # Build query with optional status filter
    where_clause = ""
    params = {"limit": limit, "offset": offset}
    
    if status:
        where_clause = "WHERE status = :status"
        params["status"] = status
    
    result = db.execute(
        text(f"""
            SELECT id, commitment_id, user_id, amount, currency, status,
                   idempotency_key, gateway_payout_id, retry_count, 
                   created_at, processed_at
            FROM payouts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    )
    
    items = []
    for row in result.fetchall():
        items.append({
            "id": str(row[0]),
            "commitment_id": row[1],
            "user_id": row[2],
            "amount": int(row[3]),
            "currency": row[4],
            "status": row[5],
            "idempotency_key": row[6],
            "gateway_payout_id": row[7],
            "retry_count": row[8],
            "created_at": row[9].isoformat() if row[9] else None,
            "processed_at": row[10].isoformat() if row[10] else None,
        })
    
    # Get total count
    count_result = db.execute(
        text(f"SELECT COUNT(*) FROM payouts {where_clause}"),
        params if status else {}
    )
    total = count_result.scalar() or 0
    
    # Get counts by status
    status_result = db.execute(
        text("""
            SELECT status, COUNT(*) as count
            FROM payouts
            GROUP BY status
        """)
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "status_counts": status_counts,
    }


@router.post("/payouts/{payout_id}/retry")
def retry_payout(
    payout_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Retry a failed payout."""
    from sqlalchemy import text
    
    # Get payout
    result = db.execute(
        text("SELECT id, status, retry_count FROM payouts WHERE id = :id"),
        {"id": payout_id}
    )
    payout = result.fetchone()
    
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    if payout[1] not in ("failed", "manual_review"):
        raise HTTPException(status_code=400, detail=f"Cannot retry payout with status '{payout[1]}'")
    
    # Reset to queued for retry
    db.execute(
        text("""
            UPDATE payouts
            SET status = 'queued', retry_count = 0
            WHERE id = :id
        """),
        {"id": payout_id}
    )
    db.commit()
    
    # Log action
    log_admin_action(
        db=db,
        admin_user_id=admin.id,
        action_type="payout_retry",
        target_type="payout",
        target_id=payout_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return {"message": "Payout queued for retry", "payout_id": payout_id}


@router.get("/refunds")
def get_refunds(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get refund records (settlements with refund > 0)."""
    query = db.query(Settlement).filter(Settlement.refund_amount > 0)
    
    total = query.count()
    settlements = query.order_by(desc(Settlement.settled_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": s.id,
                "commitment_id": s.commitment_id,
                "payout_amount": float(s.payout_amount),
                "refund_amount": float(s.refund_amount),
                "delay_minutes": s.delay_minutes,
                "decay_applied": s.decay_applied,
                "settled_at": s.settled_at.isoformat() if s.settled_at else None,
            }
            for s in settlements
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/refunds/queue")
def get_refund_queue(
    status: Optional[str] = Query(None, description="Filter by refund status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get financial refund queue from refunds table."""
    from sqlalchemy import text
    
    # Build query with optional status filter
    where_clause = ""
    params = {"limit": limit, "offset": offset}
    
    if status:
        where_clause = "WHERE status = :status"
        params["status"] = status
    
    result = db.execute(
        text(f"""
            SELECT id, payment_id, commitment_id, amount, currency, status,
                   gateway_refund_id, created_at
            FROM refunds
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    )
    
    items = []
    for row in result.fetchall():
        items.append({
            "id": str(row[0]),
            "payment_id": str(row[1]),
            "commitment_id": row[2],
            "amount": int(row[3]),
            "currency": row[4],
            "status": row[5],
            "gateway_refund_id": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        })
    
    # Get total count
    count_result = db.execute(
        text(f"SELECT COUNT(*) FROM refunds {where_clause}"),
        params if status else {}
    )
    total = count_result.scalar() or 0
    
    # Get counts by status
    status_result = db.execute(
        text("""
            SELECT status, COUNT(*) as count
            FROM refunds
            GROUP BY status
        """)
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "status_counts": status_counts,
    }


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get platform statistics."""
    # Count by status
    status_counts = db.query(
        Commitment.status,
        func.count(Commitment.id)
    ).group_by(Commitment.status).all()
    
    # User counts
    client_count = db.query(func.count(User.id)).filter(User.role == "client").scalar()
    freelancer_count = db.query(func.count(User.id)).filter(User.role == "freelancer").scalar()
    admin_count = db.query(func.count(User.id)).filter(User.role == "admin").scalar()
    
    return {
        "commitment_counts": {s: c for s, c in status_counts},
        "user_counts": {
            "clients": client_count,
            "freelancers": freelancer_count,
            "admins": admin_count,
        },
        "total_commitments": sum(c for _, c in status_counts),
        "total_users": client_count + freelancer_count + admin_count,
    }
