from __future__ import annotations

COUNTRY_SEARCH_FOCUS = {
    "AE": (
        "gulf shipping",
        "Dubai logistics",
        "Abu Dhabi energy facilities",
        "air cargo disruption",
    ),
    "IN": (
        "heatwave",
        "power demand",
        "port congestion",
        "export logistics",
    ),
    "IR": (
        "Strait of Hormuz",
        "port blockade",
        "shipping restrictions",
        "energy exports",
    ),
    "KR": (
        "labor strike",
        "semiconductor production",
        "petrochemical supply",
        "export disruption",
    ),
    "OM": (
        "Strait of Hormuz",
        "Gulf of Oman",
        "shipping lanes",
        "maritime disruption",
    ),
    "SA": (
        "petrochemical complex",
        "energy infrastructure",
        "pipeline exports",
        "industrial disruption",
    ),
}

COUNTRY_NAMES = {
    "AE": "United Arab Emirates",
    "BR": "Brazil",
    "CA": "Canada",
    "CN": "China",
    "DE": "Germany",
    "FR": "France",
    "GB": "United Kingdom",
    "IN": "India",
    "IR": "Iran",
    "JP": "Japan",
    "KR": "South Korea",
    "MX": "Mexico",
    "OM": "Oman",
    "SA": "Saudi Arabia",
    "SG": "Singapore",
    "US": "United States",
    "VN": "Vietnam",
}


def country_name(country_code: str) -> str:
    normalized = country_code.strip().upper()
    return COUNTRY_NAMES.get(normalized, normalized)


def country_search_focus(country_code: str) -> tuple[str, ...]:
    normalized = country_code.strip().upper()
    return COUNTRY_SEARCH_FOCUS.get(normalized, ())


def map_watchlist_country_codes() -> list[str]:
    return sorted(COUNTRY_SEARCH_FOCUS)
