"""
Audit logging service for security events.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_auth_event(
    db: Session,
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Log an authentication-related event.
    
    Args:
        db: Database session
        event_type: Type of event (login, logout, signup, etc.)
        user_id: User ID if known
        ip_address: Client IP address
        user_agent: Client user agent string
        details: Additional event details as JSON
        
    Returns:
        Created AuditLog record
    """
    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log


def log_login_success(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a successful login."""
    return log_auth_event(
        db=db,
        event_type="login",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_login_failed(
    db: Session,
    email: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: str = "invalid_credentials",
) -> AuditLog:
    """Log a failed login attempt."""
    return log_auth_event(
        db=db,
        event_type="login_failed",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"email": email, "reason": reason},
    )


def log_signup(
    db: Session,
    user_id: int,
    email: str,
    role: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a new account signup."""
    return log_auth_event(
        db=db,
        event_type="signup",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"email": email, "role": role},
    )


def log_logout(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a user logout."""
    return log_auth_event(
        db=db,
        event_type="logout",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_token_refresh(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a token refresh."""
    return log_auth_event(
        db=db,
        event_type="token_refresh",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_account_locked(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    failed_attempts: int = 0,
) -> AuditLog:
    """Log an account being locked."""
    return log_auth_event(
        db=db,
        event_type="account_locked",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"failed_attempts": failed_attempts},
    )


def log_password_change(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a password change."""
    return log_auth_event(
        db=db,
        event_type="password_change",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
