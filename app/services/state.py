ALLOWED_TRANSITIONS = {
    "draft": {"funded"},
    "funded": {"locked"},
    "locked": {"delivered", "expired"},
}

def assert_transition(current: str, target: str):
    if current == target:
        return
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition {current} → {target}")
