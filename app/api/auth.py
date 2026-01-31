"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_client_ip, get_user_agent
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.services.auth import (
    create_user,
    authenticate_user,
    generate_tokens_for_user,
    refresh_user_tokens,
    logout_user,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountNotActiveError,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Signup
# ============================================================================

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Create a new user account.
    
    - Email must be unique
    - Password must be at least 8 characters with uppercase, lowercase, and digit
    - Role must be 'client' or 'freelancer'
    """
    try:
        user = create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        return SignupResponse(
            message="Account created successfully",
            public_id=user.public_id,
            email=user.email,
            role=user.role,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


# ============================================================================
# Login
# ============================================================================

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return access token.
    
    - Access token returned in response body (15 min expiry)
    - Refresh token set as httpOnly cookie (7 day expiry)
    """
    try:
        user = authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        access_token, refresh_token = generate_tokens_for_user(user)
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Only send over HTTPS
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/auth",  # Only send to auth endpoints
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again after {e.locked_until.isoformat()}",
        )
    except AccountNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


# ============================================================================
# Logout
# ============================================================================

@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log out the current user.
    
    - Clears the refresh token cookie
    - Logs the logout event for audit trail
    """
    logout_user(
        db=db,
        user=current_user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )
    
    return MessageResponse(
        message="Logged out successfully",
        success=True,
    )


# ============================================================================
# Token Refresh
# ============================================================================

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = None,
):
    """
    Refresh the access token using the refresh token.
    
    - Refresh token can be provided in cookie (preferred) or request body
    - Both tokens are rotated (old refresh token becomes invalid)
    """
    # Try to get refresh token from cookie first
    cookie_token = request.cookies.get("refresh_token")
    token = cookie_token or refresh_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user, new_access_token, new_refresh_token = refresh_user_tokens(
            db=db,
            refresh_token=token,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        # Set new refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/auth",
        )
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


# ============================================================================
# Current User Profile
# ============================================================================

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile.
    
    Returns public user information (never internal IDs).
    """
    return UserResponse(
        public_id=current_user.public_id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )
