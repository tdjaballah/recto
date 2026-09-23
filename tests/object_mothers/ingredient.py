from dataclasses import replace
from datetime import date, timedelta
from typing import Self

from frigo.domain.ingredient import Ingredient

TODAY = date(2026, 10, 13)


class IngredientMother:
    _ingredient: Ingredient

    def __init__(self) -> None:
        raise TypeError("Use a named factory such as IngredientMother.fresh()")

    @classmethod
    def _of(cls, ingredient: Ingredient) -> Self:
        mother = cls.__new__(cls)
        mother._ingredient = ingredient
        return mother

    @classmethod
    def fresh(cls) -> Self:
        return cls._of(Ingredient(name="eggs", quantity=6, expires_on=TODAY + timedelta(days=10)))

    @classmethod
    def expiring_soon(cls) -> Self:
        return cls._of(Ingredient(name="cream", quantity=1, expires_on=TODAY + timedelta(days=1)))

    @classmethod
    def expired(cls) -> Self:
        return cls._of(Ingredient(name="ham", quantity=2, expires_on=TODAY - timedelta(days=1)))

    @classmethod
    def without_expiry(cls) -> Self:
        return cls._of(Ingredient(name="rice", quantity=1))

    def with_name(self, name: str) -> Self:
        self._ingredient = replace(self._ingredient, name=name)
        return self

    def with_quantity(self, quantity: int) -> Self:
        self._ingredient = replace(self._ingredient, quantity=quantity)
        return self

    def expiring_on(self, expires_on: date) -> Self:
        self._ingredient = replace(self._ingredient, expires_on=expires_on)
        return self

    def build(self) -> Ingredient:
        return replace(self._ingredient)
