"""
Beneficiary API Router.

Endpoints for managing payout beneficiary accounts.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.api.auth import get_current_user


router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


# ============================================================================
# Schemas
# ============================================================================

class BeneficiaryCreate(BaseModel):
    """Request to create a beneficiary account."""
    account_type: str  # 'bank_account', 'vpa', 'wallet'
    
    # For display only - actual details are handled by gateway
    display_name: str  # e.g., "HDFC ****1234" or "user@upi"


class BeneficiaryResponse(BaseModel):
    """Beneficiary account response."""
    id: str
    account_type: str
    display_name: str
    is_primary: bool
    is_active: bool
    created_at: str


class BeneficiaryListResponse(BaseModel):
    """List of beneficiary accounts."""
    beneficiaries: List[BeneficiaryResponse]
    payout_ready: bool
    message: Optional[str] = None


class PayoutReadinessResponse(BaseModel):
    """Payout readiness status."""
    has_beneficiary: bool
    has_primary: bool
    is_active: bool
    ready: bool
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=BeneficiaryListResponse)
async def list_beneficiaries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's beneficiary accounts.
    """
    user_id = current_user["id"]
    
    result = db.execute(
        text("""
            SELECT id, account_type, is_primary, is_active, created_at,
                   gateway_fund_account_id
            FROM beneficiary_accounts
            WHERE user_id = :user_id
            ORDER BY is_primary DESC, created_at DESC
        """),
        {"user_id": user_id}
    )
    
    beneficiaries = []
    has_primary = False
    has_active = False
    
    for row in result.fetchall():
        # Create masked display name from gateway ID
        gateway_id = row[5] or ""
        display_name = f"Account ending {gateway_id[-4:]}" if len(gateway_id) >= 4 else "Linked Account"
        
        beneficiaries.append(BeneficiaryResponse(
            id=str(row[0]),
            account_type=row[1],
            display_name=display_name,
            is_primary=row[2],
            is_active=row[3],
            created_at=row[4].isoformat() if row[4] else "",
        ))
        
        if row[2]:  # is_primary
            has_primary = True
        if row[3]:  # is_active
            has_active = True
    
    payout_ready = len(beneficiaries) > 0 and has_primary and has_active
    message = None
    
    if len(beneficiaries) == 0:
        message = "Add a payout account to receive funds."
    elif not has_primary:
        message = "Set a primary account to receive payouts."
    elif not has_active:
        message = "Your payout account is inactive."
    
    return BeneficiaryListResponse(
        beneficiaries=beneficiaries,
        payout_ready=payout_ready,
        message=message,
    )


@router.get("/status", response_model=PayoutReadinessResponse)
async def get_payout_readiness(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get payout readiness status.
    """
    user_id = current_user["id"]
    
    result = db.execute(
        text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_primary THEN 1 ELSE 0 END) as primary_count,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
            FROM beneficiary_accounts
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    total = int(row[0]) if row else 0
    primary_count = int(row[1]) if row and row[1] else 0
    active_count = int(row[2]) if row and row[2] else 0
    
    has_beneficiary = total > 0
    has_primary = primary_count > 0
    is_active = active_count > 0
    ready = has_beneficiary and has_primary and is_active
    
    if not has_beneficiary:
        message = "Add a payout account to receive funds."
    elif not has_primary:
        message = "Set a primary account to receive payouts."
    elif not is_active:
        message = "Your payout account is inactive."
    else:
        message = "Ready to receive payouts."
    
    return PayoutReadinessResponse(
        has_beneficiary=has_beneficiary,
        has_primary=has_primary,
        is_active=is_active,
        ready=ready,
        message=message,
    )


@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
async def create_beneficiary(
    data: BeneficiaryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Add a beneficiary account.
    
    NOTE: In production, this would call Razorpay to create a contact
    and fund account. For now, we create a placeholder entry.
    """
    user_id = current_user["id"]
    
    # Validate account type
    if data.account_type not in ("bank_account", "vpa", "wallet"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account type. Must be 'bank_account', 'vpa', or 'wallet'."
        )
    
    # Check if this is the first beneficiary (make it primary)
    result = db.execute(
        text("SELECT COUNT(*) FROM beneficiary_accounts WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    is_first = result.scalar() == 0
    
    # In production, call Razorpay here to create contact + fund account
    # For now, generate placeholder gateway IDs
    import uuid
    gateway_contact_id = f"cont_{uuid.uuid4().hex[:14]}"
    gateway_fund_account_id = f"fa_{uuid.uuid4().hex[:14]}"
    
    # Insert beneficiary
    result = db.execute(
        text("""
            INSERT INTO beneficiary_accounts (
                user_id, gateway_contact_id, gateway_fund_account_id,
                account_type, is_primary, is_active, created_at
            ) VALUES (
                :user_id, :contact_id, :fund_account_id,
                :account_type, :is_primary, true, NOW()
            )
            RETURNING id, created_at
        """),
        {
            "user_id": user_id,
            "contact_id": gateway_contact_id,
            "fund_account_id": gateway_fund_account_id,
            "account_type": data.account_type,
            "is_primary": is_first,
        }
    )
    row = result.fetchone()
    db.commit()
    
    return BeneficiaryResponse(
        id=str(row[0]),
        account_type=data.account_type,
        display_name=data.display_name,
        is_primary=is_first,
        is_active=True,
        created_at=row[1].isoformat() if row[1] else "",
    )


@router.put("/{beneficiary_id}/primary")
async def set_primary_beneficiary(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Set beneficiary as primary account.
    """
    user_id = current_user["id"]
    
    # Verify ownership
    result = db.execute(
        text("""
            SELECT id FROM beneficiary_accounts
            WHERE id = :beneficiary_id AND user_id = :user_id
        """),
        {"beneficiary_id": beneficiary_id, "user_id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficiary account not found."
        )
    
    # Unset all as primary
    db.execute(
        text("""
            UPDATE beneficiary_accounts
            SET is_primary = false
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    
    # Set this one as primary
    db.execute(
        text("""
            UPDATE beneficiary_accounts
            SET is_primary = true
            WHERE id = :beneficiary_id
        """),
        {"beneficiary_id": beneficiary_id}
    )
    
    db.commit()
    
    return {"message": "Primary account updated."}


@router.put("/{beneficiary_id}/disable")
async def disable_beneficiary(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Disable beneficiary account (soft delete).
    """
    user_id = current_user["id"]
    
    # Verify ownership
    result = db.execute(
        text("""
            SELECT id, is_primary FROM beneficiary_accounts
            WHERE id = :beneficiary_id AND user_id = :user_id
        """),
        {"beneficiary_id": beneficiary_id, "user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficiary account not found."
        )
    
    # Disable the account
    db.execute(
        text("""
            UPDATE beneficiary_accounts
            SET is_active = false, is_primary = false
            WHERE id = :beneficiary_id
        """),
        {"beneficiary_id": beneficiary_id}
    )
    
    db.commit()
    
    return {"message": "Account disabled."}
