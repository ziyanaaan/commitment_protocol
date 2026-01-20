FLEXIBLE = [
    (0.00, 1.00),
    (0.10, 0.95),
    (0.20, 0.85),
    (0.40, 0.60),
    (0.70, 0.30),
    (1.00, 0.00),
]

BALANCED = [
    (0.00, 1.00),
    (0.05, 0.90),
    (0.10, 0.80),
    (0.20, 0.60),
    (0.30, 0.40),
    (0.50, 0.00),
]

STRICT = [
    (0.00, 1.00),
    (0.02, 0.90),
    (0.05, 0.70),
    (0.10, 0.40),
    (0.20, 0.00),
]

CURVES = {
    "flexible": FLEXIBLE,
    "balanced": BALANCED,
    "strict": STRICT,
}

def interpolate(points, x):
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if x1 <= x <= x2:
            ratio = (x - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)
    return points[-1][1]


def calculate_time_scaled_payout(
    amount, created_at, deadline, delivered_at, curve_type
):
    if delivered_at <= deadline:
        return amount

    total_window = (deadline - created_at).total_seconds()
    if total_window <= 0:
        return 0

    delay = (delivered_at - deadline).total_seconds()
    delay_ratio = min(delay / total_window, 1.0)

    curve = CURVES[curve_type]
    payout_ratio = interpolate(curve, delay_ratio)

    return int(amount * payout_ratio)
