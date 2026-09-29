from datetime import date

from frigo.domain.ingredient import Ingredient
from frigo.domain.pantry import expired, fresh
from frigo.ports.pantry_repository import PantryRepository


def discard_expired(pantry: PantryRepository, today: date) -> list[Ingredient]:
    ingredients = pantry.list()
    for ingredient in expired(ingredients, today):
        pantry.remove(ingredient.name)
    return fresh(ingredients, today)
