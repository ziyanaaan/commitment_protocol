from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # Existing columns (UNCHANGED)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # client | freelancer | admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NEW: Authentication columns
    public_id = Column(String(40), unique=True, index=True, nullable=True)  # cli_xxx, fre_xxx, adm_xxx
    password_hash = Column(String(255), nullable=True)  # Nullable for existing users
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")
    is_verified = Column(Boolean, default=False, nullable=False, server_default="false")
    
    # NEW: Security tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Timestamp tracking
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

