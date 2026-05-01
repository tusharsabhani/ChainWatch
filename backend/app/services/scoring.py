from __future__ import annotations


def clamp(value: float, minimum: float = 1.0, maximum: float = 5.0) -> float:
    return max(minimum, min(maximum, value))


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
