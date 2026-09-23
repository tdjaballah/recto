from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Self

from frigo.domain.errors import InvalidIngredientName, InvalidQuantity


@dataclass(frozen=True)
class Ingredient:
    name: str
    quantity: int
    expires_on: date | None = None

    def is_expired(self, today: date) -> bool:
        return self.expires_on is not None and self.expires_on < today

    def expires_within(self, today: date, days: int) -> bool:
        return self.expires_on is not None and today <= self.expires_on <= today + timedelta(days=days)

    def restocked_with(self, other: Self) -> Self:
        dates = [d for d in (self.expires_on, other.expires_on) if d is not None]
        return replace(self, quantity=self.quantity + other.quantity, expires_on=min(dates, default=None))


def normalize_name(raw: str) -> str:
    return " ".join(raw.lower().split())


def new_ingredient(raw_name: str, quantity: int, expires_on: date | None = None) -> Ingredient:
    name = normalize_name(raw_name)
    if not name:
        raise InvalidIngredientName(raw_name)
    if quantity < 1:
        raise InvalidQuantity(quantity)
    return Ingredient(name=name, quantity=quantity, expires_on=expires_on)
