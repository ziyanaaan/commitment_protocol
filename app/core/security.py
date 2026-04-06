"""
Security utilities for authentication.
- Password hashing with Argon2
- JWT token creation and validation
- Public ID generation with ULID
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash
from ulid import ULID

from app.core.config import settings


# Argon2 password hasher with secure defaults
_password_hasher = PasswordHasher(
    time_cost=2,        # Number of iterations
    memory_cost=65536,  # 64 MB memory usage
    parallelism=1,      # Number of threads
)


# ============================================================================
# Password Hashing
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.
    
    Args:
        password: Plain text password
        
    Returns:
        Argon2 hash string
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored Argon2 hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        _password_hasher.verify(password_hash, password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed (e.g., after parameter changes).
    """
    return _password_hasher.check_needs_rehash(password_hash)


# ============================================================================
# JWT Token Management
# ============================================================================

def create_access_token(
    user_id: int,
    public_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived access token.
    
    Args:
        user_id: Internal user ID (for DB lookups)
        public_id: Public user ID (for external reference)
        role: User role (client, freelancer, admin)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT access token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    payload = {
        "sub": str(user_id),
        "public_id": public_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a long-lived refresh token.
    
    Args:
        user_id: Internal user ID
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> Optional[dict]:
    """
    Verify and decode an access token.
    
    Args:
        token: JWT access token
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # Verify this is an access token
        if payload.get("type") != "access":
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Verify and decode a refresh token.
    
    Args:
        token: JWT refresh token
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_token_pair(user_id: int, public_id: str, role: str) -> Tuple[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: Internal user ID
        public_id: Public user ID
        role: User role
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = create_access_token(user_id, public_id, role)
    refresh_token = create_refresh_token(user_id)
    return access_token, refresh_token


# ============================================================================
# Public ID Generation
# ============================================================================

def generate_public_id(role: str) -> str:
    """
    Generate a unique public ID with role prefix.
    
    Format: {role_prefix}_{ulid}
    Examples:
        - cli_01J1QF9G2H3M8V7K5Z4R2P1A9B (client)
        - fre_01J1QF9G2H3M8V7K5Z4R2P1A9C (freelancer)
        - adm_01J1QF9G2H3M8V7K5Z4R2P1A9D (admin)
    
    Args:
        role: User role (client, freelancer, admin)
        
    Returns:
        Formatted public ID string
    """
    prefix_map = {
        "client": "cli",
        "freelancer": "fre",
        "admin": "adm",
    }
    
    prefix = prefix_map.get(role, "usr")
    ulid = ULID()
    
    return f"{prefix}_{ulid}"
