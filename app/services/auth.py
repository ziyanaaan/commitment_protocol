"""
Authentication service layer.
Handles user creation, authentication, and account security.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    generate_public_id,
    create_token_pair,
    verify_refresh_token,
)
from app.core.config import settings
from app.services.audit import (
    log_signup,
    log_login_success,
    log_login_failed,
    log_logout,
    log_token_refresh,
    log_account_locked,
)


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""
    pass


class AccountLockedError(AuthError):
    """Raised when account is locked."""
    def __init__(self, locked_until: datetime):
        self.locked_until = locked_until
        super().__init__(f"Account locked until {locked_until}")


class AccountNotActiveError(AuthError):
    """Raised when account is not active."""
    pass


class EmailAlreadyExistsError(AuthError):
    """Raised when email is already registered."""
    pass


# ============================================================================
# User Creation
# ============================================================================

def create_user(
    db: Session,
    email: str,
    password: str,
    role: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> User:
    """
    Create a new user account.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password (will be hashed)
        role: User role (client, freelancer)
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
        
    Returns:
        Created User object
        
    Raises:
        EmailAlreadyExistsError: If email is already registered
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise EmailAlreadyExistsError(f"Email {email} is already registered")
    
    # Create user
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        public_id=generate_public_id(role),
        is_active=True,
        is_verified=False,  # Require email verification
        failed_login_attempts=0,
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyExistsError(f"Email {email} is already registered")
    
    # Audit log
    log_signup(
        db=db,
        user_id=user.id,
        email=email,
        role=role,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return user


# ============================================================================
# Authentication
# ============================================================================

def authenticate_user(
    db: Session,
    email: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> User:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
        
    Returns:
        Authenticated User object
        
    Raises:
        InvalidCredentialsError: If credentials are invalid
        AccountLockedError: If account is locked
        AccountNotActiveError: If account is deactivated
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Log failed attempt even if user doesn't exist (prevents enumeration timing)
        log_login_failed(
            db=db,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="user_not_found",
        )
        raise InvalidCredentialsError("Invalid email or password")
    
    # Check if account is locked
    if is_account_locked(user):
        log_login_failed(
            db=db,
            email=email,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="account_locked",
        )
        raise AccountLockedError(user.locked_until)
    
    # Check if account is active
    if not user.is_active:
        log_login_failed(
            db=db,
            email=email,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="account_inactive",
        )
        raise AccountNotActiveError("Account is deactivated")
    
    # Verify password
    if not user.password_hash or not verify_password(password, user.password_hash):
        increment_failed_attempts(db, user, ip_address, user_agent)
        raise InvalidCredentialsError("Invalid email or password")
    
    # Reset failed attempts on successful login
    reset_failed_attempts(db, user)
    
    # Log successful login
    log_login_success(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return user


def generate_tokens_for_user(user: User) -> Tuple[str, str]:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user: User object
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    return create_token_pair(user.id, user.public_id, user.role)


def refresh_user_tokens(
    db: Session,
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[User, str, str]:
    """
    Refresh an expired access token using a valid refresh token.
    
    Args:
        db: Database session
        refresh_token: Valid refresh token
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
        
    Returns:
        Tuple of (User, new_access_token, new_refresh_token)
        
    Raises:
        InvalidCredentialsError: If refresh token is invalid
    """
    payload = verify_refresh_token(refresh_token)
    
    if not payload:
        raise InvalidCredentialsError("Invalid or expired refresh token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise InvalidCredentialsError("User not found")
    
    if not user.is_active:
        raise AccountNotActiveError("Account is deactivated")
    
    # Generate new token pair (token rotation)
    access_token, new_refresh_token = generate_tokens_for_user(user)
    
    # Log token refresh
    log_token_refresh(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return user, access_token, new_refresh_token


def logout_user(
    db: Session,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log out a user (just logs the event, real invalidation happens via cookie clearing).
    
    Args:
        db: Database session
        user: User object
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
    """
    log_logout(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================================================
# Account Security
# ============================================================================

def is_account_locked(user: User) -> bool:
    """
    Check if a user account is locked.
    
    Args:
        user: User object
        
    Returns:
        True if account is currently locked
    """
    if not user.locked_until:
        return False
    
    return user.locked_until > datetime.now(timezone.utc)


def increment_failed_attempts(
    db: Session,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Increment failed login attempts and lock account if threshold reached.
    
    Args:
        db: Database session
        user: User object
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
    """
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    
    # Lock account if threshold exceeded
    if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCOUNT_LOCK_DURATION_MINUTES
        )
        
        # Log account lock
        log_account_locked(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            failed_attempts=user.failed_login_attempts,
        )
    
    db.add(user)
    db.commit()
    
    # Log failed login
    log_login_failed(
        db=db,
        email=user.email,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        reason="invalid_password",
    )


def reset_failed_attempts(db: Session, user: User) -> None:
    """
    Reset failed login attempts after successful login.
    
    Args:
        db: Database session
        user: User object
    """
    if user.failed_login_attempts > 0 or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(user)
        db.commit()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by internal ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_public_id(db: Session, public_id: str) -> Optional[User]:
    """Get a user by public ID."""
    return db.query(User).filter(User.public_id == public_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()
