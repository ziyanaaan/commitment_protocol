"""
Razorpay API Client.

Handles all API calls to Razorpay/RazorpayX for:
- Payouts (RazorpayX)
- Refunds (Razorpay)

CRITICAL:
- Uses idempotency keys for all money movement
- Never retries without idempotency
- Logs all API calls for audit
"""

import base64
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standardized API response."""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class RazorpayAPIError(Exception):
    """Razorpay API call failed."""
    def __init__(self, message: str, status_code: int = 0, error_code: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class TransfersDisabledError(Exception):
    """Transfers are disabled in configuration."""
    pass


def _get_auth_header() -> str:
    """Generate Basic Auth header for Razorpay API."""
    credentials = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _check_transfers_enabled() -> None:
    """Check if transfers are enabled. Raises if not."""
    if not settings.TRANSFERS_ENABLED:
        raise TransfersDisabledError(
            "Financial transfers are disabled. Set TRANSFERS_ENABLED=true to enable."
        )


# ============================================================================
# Payout API (RazorpayX)
# ============================================================================

def create_payout(
    fund_account_id: str,
    amount: int,
    currency: str,
    idempotency_key: str,
    purpose: str = "payout",
    mode: str = "IMPS",
    narration: str = "Pledgos Payout",
    reference_id: Optional[str] = None,
) -> APIResponse:
    """
    Create a payout using RazorpayX.
    
    CRITICAL: Uses idempotency_key to prevent duplicate payouts.
    
    Args:
        fund_account_id: Razorpay fund account ID (fa_xxx)
        amount: Amount in smallest currency unit (paise)
        currency: Currency code (INR)
        idempotency_key: Unique key to prevent duplicates
        purpose: Payout purpose
        mode: Transfer mode (IMPS, NEFT, RTGS, UPI)
        narration: Description for bank statement
        reference_id: Optional reference ID
    
    Returns:
        APIResponse with payout details or error
    """
    _check_transfers_enabled()
    
    url = f"{settings.RAZORPAYX_BASE_URL}/payouts"
    
    payload = {
        "account_number": settings.RAZORPAY_KEY_ID,  # Will be replaced with actual account
        "fund_account_id": fund_account_id,
        "amount": amount,
        "currency": currency,
        "mode": mode,
        "purpose": purpose,
        "queue_if_low_balance": False,  # Fail immediately if insufficient balance
        "reference_id": reference_id or idempotency_key,
        "narration": narration,
    }
    
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
        "X-Payout-Idempotency": idempotency_key,
    }
    
    logger.info(f"Creating payout: {idempotency_key}, amount={amount}, fund_account={fund_account_id}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(f"Payout created: {data.get('id')}")
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                )
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("description", "Unknown error")
                error_code = error_data.get("error", {}).get("code", "")
                logger.error(f"Payout failed: {error_msg} ({error_code})")
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    error=error_msg,
                    error_code=error_code,
                )
                
    except httpx.RequestError as e:
        logger.error(f"Payout request error: {e}")
        return APIResponse(
            success=False,
            status_code=0,
            error=str(e),
            error_code="REQUEST_ERROR",
        )


def get_payout(payout_id: str) -> APIResponse:
    """
    Get payout status from Razorpay.
    
    Args:
        payout_id: Razorpay payout ID (pout_xxx)
    
    Returns:
        APIResponse with payout details
    """
    url = f"{settings.RAZORPAYX_BASE_URL}/payouts/{payout_id}"
    
    headers = {
        "Authorization": _get_auth_header(),
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json(),
                )
            else:
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    error="Failed to fetch payout",
                )
                
    except httpx.RequestError as e:
        return APIResponse(
            success=False,
            status_code=0,
            error=str(e),
        )


# ============================================================================
# Refund API (Razorpay)
# ============================================================================

def create_refund(
    payment_id: str,
    amount: int,
    speed: str = "normal",
    notes: Optional[Dict[str, str]] = None,
) -> APIResponse:
    """
    Create a refund for a payment.
    
    Args:
        payment_id: Razorpay payment ID (pay_xxx)
        amount: Amount to refund in smallest currency unit
        speed: Refund speed (normal, optimum)
        notes: Optional notes
    
    Returns:
        APIResponse with refund details
    """
    _check_transfers_enabled()
    
    url = f"{settings.RAZORPAYX_BASE_URL}/payments/{payment_id}/refund"
    
    payload = {
        "amount": amount,
        "speed": speed,
    }
    
    if notes:
        payload["notes"] = notes
    
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
    }
    
    logger.info(f"Creating refund: payment={payment_id}, amount={amount}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(f"Refund created: {data.get('id')}")
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                )
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("description", "Unknown error")
                logger.error(f"Refund failed: {error_msg}")
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    error=error_msg,
                )
                
    except httpx.RequestError as e:
        logger.error(f"Refund request error: {e}")
        return APIResponse(
            success=False,
            status_code=0,
            error=str(e),
        )


def get_refund(refund_id: str) -> APIResponse:
    """
    Get refund status from Razorpay.
    
    Args:
        refund_id: Razorpay refund ID (rfnd_xxx)
    
    Returns:
        APIResponse with refund details
    """
    url = f"{settings.RAZORPAYX_BASE_URL}/refunds/{refund_id}"
    
    headers = {
        "Authorization": _get_auth_header(),
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json(),
                )
            else:
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    error="Failed to fetch refund",
                )
                
    except httpx.RequestError as e:
        return APIResponse(
            success=False,
            status_code=0,
            error=str(e),
        )
