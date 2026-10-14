from typing import Tuple
from backend.app.models.tables import Route, Stop, RouteStop

DEFAULT_RATES = {
    "Ordinary": 0.85,
    "Express": 1.25,
    "Deluxe": 1.60,
    "AC-Sleeper": 2.20
}

def calculate_fare(
    from_stop_seq: int,
    to_stop_seq: int,
    total_stages: int,
    base_route_fare: float,
    bus_type: str = "Ordinary"
) -> Tuple[float, float, float]:
    """
    Calculates stage fare based on travel distance/stages and bus class multiplier.
    Returns (base_amount, tax_amount, total_amount).
    """
    stages_traveled = abs(to_stop_seq - from_stop_seq)
    if stages_traveled == 0:
        stages_traveled = 1

    stage_ratio = stages_traveled / max(total_stages - 1, 1)
    class_multiplier = DEFAULT_RATES.get(bus_type, 1.0) / DEFAULT_RATES["Ordinary"]

    raw_fare = max(10.0, base_route_fare * stage_ratio * class_multiplier)
    base_amount = round(raw_fare, 2)
    tax_amount = round(base_amount * 0.05, 2) # 5% GST
    total_amount = round(base_amount + tax_amount, 2)

    return base_amount, tax_amount, total_amount
