from datetime import date

from frigo.domain.ingredient import Ingredient


def expired(ingredients: list[Ingredient], today: date) -> list[Ingredient]:
    return [ingredient for ingredient in ingredients if ingredient.is_expired(today)]


def fresh(ingredients: list[Ingredient], today: date) -> list[Ingredient]:
    kept = [ingredient for ingredient in ingredients if not ingredient.is_expired(today)]
    return sorted(
        kept, key=lambda ingredient: (ingredient.expires_on is None, ingredient.expires_on or date.max, ingredient.name)
    )
