"""
Authentication schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================================
# Request Schemas
# ============================================================================

class SignupRequest(BaseModel):
    """Request schema for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., pattern="^(client|freelancer)$")  # admin created differently
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh (if not using cookies)."""
    refresh_token: Optional[str] = None  # Optional if using httpOnly cookie


class ChangePasswordRequest(BaseModel):
    """Request schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============================================================================
# Response Schemas
# ============================================================================

class TokenResponse(BaseModel):
    """Response schema for login/refresh operations."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class UserResponse(BaseModel):
    """Response schema for user profile - NEVER includes internal ID."""
    public_id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignupResponse(BaseModel):
    """Response schema for successful signup."""
    message: str = "Account created successfully"
    public_id: str
    email: str
    role: str


class AuthStatusResponse(BaseModel):
    """Response schema for auth status check."""
    authenticated: bool
    user: Optional[UserResponse] = None


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True
