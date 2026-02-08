"""
Background Scheduler for Pledgos.

Manages scheduled jobs:
- Daily financial reconciliation
- Webhook event processing
- Payout execution
- Refund execution
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


logger = logging.getLogger(__name__)


def process_expired_commitments():
    """
    DISABLED: This function no longer marks commitments as expired.
    Commitments will stay in their current state regardless of deadline.
    The deadline is only used for calculating decay/payout, not for expiry.
    """
    pass


def run_daily_reconciliation_job():
    """
    Daily reconciliation job.
    
    Compares ledger totals with gateway data.
    Runs once per day at 2 AM UTC.
    """
    from app.services.financial.reconciliation import run_daily_reconciliation
    
    logger.info("Starting daily reconciliation job")
    
    db = SessionLocal()
    try:
        result = run_daily_reconciliation(db)
        logger.info(f"Reconciliation completed: status={result.status}, difference={result.difference}")
    except Exception as e:
        logger.error(f"Reconciliation job failed: {e}")
    finally:
        db.close()


def process_webhook_events_job():
    """
    Process pending webhook events.
    
    Runs every minute to handle incoming webhooks.
    """
    from app.services.financial.webhook_processor import process_all_pending_events
    
    db = SessionLocal()
    try:
        stats = process_all_pending_events(db, limit=50)
        if stats["processed"] > 0 or stats["errors"]:
            logger.info(f"Webhooks processed: {stats['processed']}, errors: {len(stats['errors'])}")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
    finally:
        db.close()


def process_payouts_job():
    """
    Process queued payouts.
    
    Runs every 5 minutes to send payouts to gateway.
    """
    from app.services.financial.payout_executor import process_pending_payouts
    from app.core.config import settings
    
    if not settings.TRANSFERS_ENABLED:
        return
    
    db = SessionLocal()
    try:
        stats = process_pending_payouts(db, limit=10)
        if stats["processed"] > 0 or stats["failed"] > 0:
            logger.info(f"Payouts: processed={stats['processed']}, failed={stats['failed']}")
    except Exception as e:
        logger.error(f"Payout processing failed: {e}")
    finally:
        db.close()


def process_refunds_job():
    """
    Process created refunds.
    
    Runs every 5 minutes to send refunds to gateway.
    """
    from app.services.financial.refund_executor import process_pending_refunds
    from app.core.config import settings
    
    if not settings.TRANSFERS_ENABLED:
        return
    
    db = SessionLocal()
    try:
        stats = process_pending_refunds(db, limit=10)
        if stats["processed"] > 0 or stats["failed"] > 0:
            logger.info(f"Refunds: processed={stats['processed']}, failed={stats['failed']}")
    except Exception as e:
        logger.error(f"Refund processing failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler with financial jobs."""
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Daily reconciliation at 2 AM UTC
    scheduler.add_job(
        run_daily_reconciliation_job,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_reconciliation",
        replace_existing=True,
    )
    
    # Webhook processing every minute
    scheduler.add_job(
        process_webhook_events_job,
        trigger="interval",
        minutes=1,
        id="webhook_processor",
        replace_existing=True,
    )
    
    # Payout processing every 5 minutes
    scheduler.add_job(
        process_payouts_job,
        trigger="interval",
        minutes=5,
        id="payout_processor",
        replace_existing=True,
    )
    
    # Refund processing every 5 minutes
    scheduler.add_job(
        process_refunds_job,
        trigger="interval",
        minutes=5,
        id="refund_processor",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(">>> Scheduler started with financial jobs")
    print(">>> Scheduler started with financial jobs")

