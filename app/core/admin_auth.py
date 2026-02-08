"""
Admin authentication and authorization utilities.
"""

from functools import wraps
from typing import Optional
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.admin_audit import AdminAuditLog
from app.core.security import verify_access_token


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Dependency that verifies the current user is an admin.
    Raises 401 if not authenticated, 403 if not admin.
    """
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check admin role
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


def log_admin_action(
    db: Session,
    admin_user_id: int,
    action_type: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AdminAuditLog:
    """
    Log an admin action to the audit log.
    """
    log_entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    # Check for forwarded headers first (for proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    if request.client:
        return request.client.host
    
    return None
