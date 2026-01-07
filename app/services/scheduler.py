from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.commitment import Commitment
from app.services.settlement import settle_commitment


def process_expired_commitments():
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        expired_commitments = (
            db.query(Commitment)
            .filter(
                Commitment.status == "locked",
                Commitment.deadline < now,
            )
            .all()
        )

        for commitment in expired_commitments:
            commitment.status = "expired"
            db.add(commitment)
            db.commit()

            # Immediately settle after expiry
            settle_commitment(db, commitment.id)

    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        process_expired_commitments,
        trigger="interval",
        minutes=1,
        id="expired_commitment_processor",
        replace_existing=True,
    )
    scheduler.start()
