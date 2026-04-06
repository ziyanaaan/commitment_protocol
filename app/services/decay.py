from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Import curve definitions from core
from app.core.decay import CURVES, interpolate


def calculate_time_decay_payout(
    *,
    amount: Decimal,
    deadline: datetime,
    delivered_at: datetime | None,
    decay_curve: str | list[tuple[int, int]],
):
    """
    Calculate payout and refund based on delivery timing.
    
    Args:
        amount: The commitment amount
        deadline: When delivery was due
        delivered_at: When delivery happened (None = no delivery)
        decay_curve: Either a curve name ("flexible", "balanced", "strict")
                    or a list of (delay_minutes, payout_percent) tuples
    
    Returns:
        dict with keys: delay_minutes, payout, refund
    """

    if delivered_at is None:
        # No delivery → full refund
        return {
            "delay_minutes": None,
            "payout": Decimal("0.00"),
            "refund": amount.quantize(Decimal("0.01")),
        }

    # Calculate delay
    delay_seconds = (delivered_at - deadline).total_seconds()
    delay_minutes = max(0, int(delay_seconds // 60))
    
    # Handle curve name strings (e.g., "flexible", "balanced", "strict")
    if isinstance(decay_curve, str):
        curve_name = decay_curve.lower()
        if curve_name not in CURVES:
            curve_name = "balanced"  # default
        
        curve_points = CURVES[curve_name]
        
        # For early delivery, full payout
        if delay_seconds <= 0:
            payout_ratio = 1.0
        else:
            # Calculate delay ratio based on time window (use 1 hour as reference)
            # The curves in core/decay.py use ratio 0-1 for delay
            delay_ratio = min(delay_minutes / 60.0, 1.0)  # Normalize to 1 hour
            payout_ratio = interpolate(curve_points, delay_ratio)
        
        payout = (amount * Decimal(str(payout_ratio))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        # Handle legacy tuple list format: [(delay_minutes, payout_percent), ...]
        payout_percent = 0
        for max_delay, percent in decay_curve:
            if delay_minutes <= max_delay:
                payout_percent = percent
                break
        
        payout = (amount * Decimal(payout_percent) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    
    refund = (amount - payout).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "delay_minutes": delay_minutes,
        "payout": payout,
        "refund": refund,
    }
