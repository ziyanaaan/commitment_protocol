"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.user import User


# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    # Check X-Forwarded-For header (for proxied requests)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Fall back to direct client address
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the access token.
    Raises 401 if not authenticated.
    
    Usage:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.public_id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    payload = verify_access_token(token)
    
    if not payload:
        raise credentials_exception
    
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Does NOT raise exceptions - useful for optional auth.
    
    Usage:
        @router.get("/optional-auth")
        def optional_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"user_id": user.public_id}
            return {"message": "Anonymous user"}
    """
    if not token:
        return None
    
    payload = verify_access_token(token)
    
    if not payload:
        return None
    
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        return None
    
    return user


def require_role(*allowed_roles: str):
    """
    Create a dependency that requires the user to have one of the allowed roles.
    
    Usage:
        @router.post("/admin-only")
        def admin_route(user: User = Depends(require_role("admin"))):
            return {"admin_user": user.public_id}
            
        @router.post("/client-or-admin")
        def mixed_route(user: User = Depends(require_role("client", "admin"))):
            return {"user_id": user.public_id}
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role checks
def require_client() -> User:
    """Require client role."""
    return Depends(require_role("client"))


def require_freelancer() -> User:
    """Require freelancer role."""
    return Depends(require_role("freelancer"))


def require_admin() -> User:
    """Require admin role."""
    return Depends(require_role("admin"))


def require_client_or_freelancer():
    """Require either client or freelancer role."""
    return require_role("client", "freelancer")


def require_system_or_admin():
    """Require system or admin role for sensitive operations."""
    return require_role("admin", "system")
