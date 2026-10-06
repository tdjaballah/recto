from dataclasses import dataclass
from datetime import date

from frigo.domain.errors import RecipeRejected
from frigo.domain.ingredient import Ingredient
from frigo.domain.pantry import urgent

STAPLES = frozenset({"salt", "pepper", "water", "oil"})


@dataclass(frozen=True)
class Recipe:
    title: str
    ingredients: tuple[str, ...]
    steps: tuple[str, ...]


def missing_ingredients(recipe: Recipe, stock: list[Ingredient]) -> list[str]:
    in_stock = {ingredient.name for ingredient in stock} | STAPLES
    return [name for name in recipe.ingredients if name not in in_stock]


def check_recipe(recipe: Recipe, stock: list[Ingredient], today: date, max_missing: int) -> None:
    missing = missing_ingredients(recipe, stock)
    if len(missing) > max_missing:
        raise RecipeRejected(f"not in the fridge: {', '.join(missing)}")

    use_first = {ingredient.name for ingredient in urgent(stock, today)}
    if use_first and use_first.isdisjoint(recipe.ingredients):
        raise RecipeRejected(f"uses none of what expires soon: {', '.join(sorted(use_first))}")
