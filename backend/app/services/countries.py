from __future__ import annotations

COUNTRY_NAMES = {
    "BR": "Brazil",
    "CA": "Canada",
    "CN": "China",
    "DE": "Germany",
    "FR": "France",
    "GB": "United Kingdom",
    "IN": "India",
    "JP": "Japan",
    "KR": "South Korea",
    "MX": "Mexico",
    "SG": "Singapore",
    "US": "United States",
    "VN": "Vietnam",
}


def country_name(country_code: str) -> str:
    normalized = country_code.strip().upper()
    return COUNTRY_NAMES.get(normalized, normalized)
