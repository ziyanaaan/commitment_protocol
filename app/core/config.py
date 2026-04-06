"""
Application configuration settings.
Loads from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Security
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_DURATION_MINUTES: int = 30
    
    # Rate Limiting
    AUTH_RATE_LIMIT: str = "5/minute"  # 5 attempts per minute per IP
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    RAZORPAYX_BASE_URL: str = os.getenv("RAZORPAYX_BASE_URL", "https://api.razorpay.com/v1")
    
    # Financial Transfer Configuration
    # CRITICAL: Set to False in production until ready for live transfers
    TRANSFERS_ENABLED: bool = os.getenv("TRANSFERS_ENABLED", "false").lower() == "true"
    
    # Retry Configuration
    MAX_PAYOUT_RETRIES: int = int(os.getenv("MAX_PAYOUT_RETRIES", "5"))
    RETRY_BASE_DELAY_SECONDS: int = int(os.getenv("RETRY_BASE_DELAY_SECONDS", "60"))
    MANUAL_REVIEW_AFTER_RETRIES: int = int(os.getenv("MANUAL_REVIEW_AFTER_RETRIES", "3"))
    
    def validate(self) -> None:
        """Validate that required settings are present."""
        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        if not self.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not set")
        if not self.JWT_REFRESH_SECRET_KEY:
            raise RuntimeError("JWT_REFRESH_SECRET_KEY is not set")
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters")


settings = Settings()
