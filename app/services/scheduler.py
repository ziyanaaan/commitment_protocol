from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.commitment import Commitment


def process_expired_commitments():
    """
    DISABLED: This function no longer marks commitments as expired.
    Commitments will stay in their current state regardless of deadline.
    The deadline is only used for calculating decay/payout, not for expiry.
    """
    # Do nothing - expiry is disabled
    pass


def start_scheduler():
    """Start the background scheduler (currently disabled)."""
    # Scheduler is disabled - no automatic expiry
    # If you want to re-enable expiry in the future, uncomment the code below
    
    # scheduler = BackgroundScheduler(timezone="UTC")
    # scheduler.add_job(
    #     process_expired_commitments,
    #     trigger="interval",
    #     minutes=1,
    #     id="expired_commitment_processor",
    #     replace_existing=True,
    # )
    # scheduler.start()
    
    print(">>> Scheduler disabled - no automatic expiry")
    pass
