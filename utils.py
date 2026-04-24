"""Small reusable helper functions."""

from datetime import datetime, timezone
from typing import Any


def current_utc_time() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(timezone.utc)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float, returning a default if conversion fails."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_money(value: float) -> str:
    """Format a number as a USDT-style money string."""

    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    """Format a decimal percentage value for display."""

    return f"{value:.4f}%"


def round_price(value: float) -> float:
    """Round a price to two decimals for easier report reading."""

    return round(value, 2)


def print_warning(message: str) -> None:
    """Print a readable warning message."""

    print(f"Warning: {message}")
