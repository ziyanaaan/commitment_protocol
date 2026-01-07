from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def calculate_time_decay_payout(
    *,
    amount: Decimal,
    deadline: datetime,
    delivered_at: datetime | None,
    decay_curve: list[tuple[int, int]],
):
    """
    decay_curve: list of (delay_minutes_upper_bound, payout_percentage)
    Example:
        [
            (0, 100),
            (60, 80),
            (180, 50),
            (360, 20),
        ]
    """

    if delivered_at is None:
        # No delivery → full refund
        return {
            "delay_minutes": None,
            "payout": Decimal("0.00"),
            "refund": amount.quantize(Decimal("0.01")),
        }

    delay_seconds = (delivered_at - deadline).total_seconds()
    delay_minutes = max(0, int(delay_seconds // 60))

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
