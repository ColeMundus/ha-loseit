"""Public immutable client results and sanitized failure types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class LoseItError(Exception):
    """Safe-to-display service failure."""


class LoseItAuthError(LoseItError):
    """Missing credentials or verified session rejection (401/RPC auth error)."""


class LoseItAccessError(LoseItError):
    """Access denied or challenged without proof of session expiry."""


class LoseItProtocolError(LoseItError):
    """Unsupported or changed response schema; never an empty diary."""


class LoseItConnectionError(LoseItError):
    """Transient transport or service failure."""


class LoseItRateLimitError(LoseItError):
    """Request throttled. No automatic retries are performed."""

    def __init__(self, retry_after: float | None = None):
        super().__init__("Lose It request rate limited")
        self.retry_after = retry_after


@dataclass(frozen=True)
class Account:
    account_id: str
    timezone: str | None = None


@dataclass(frozen=True)
class DailySnapshot:
    day: date
    budget_kcal: Decimal | None = None
    food_kcal: Decimal | None = None
    exercise_kcal: Decimal | None = None
    net_kcal: Decimal | None = None
    remaining_kcal: Decimal | None = None
    protein_g: Decimal | None = None
    carbohydrates_g: Decimal | None = None
    fat_g: Decimal | None = None
    weight_kg: Decimal | None = None
    goal_weight_kg: Decimal | None = None
    logged_food_count: int | None = None
