from datetime import date

from frigo.domain.ingredient import Ingredient, new_ingredient
from frigo.ports.pantry_repository import PantryRepository


class AddIngredient:
    def __init__(self, pantry: PantryRepository) -> None:
        self._pantry = pantry

    def execute(self, raw_name: str, quantity: int, expires_on: date | None = None) -> Ingredient:
        ingredient = new_ingredient(raw_name, quantity, expires_on)
        if existing := self._pantry.get(ingredient.name):
            ingredient = existing.restocked_with(ingredient)

        self._pantry.save(ingredient)
        return ingredient
