from dataclasses import replace

from frigo.domain.errors import EmptyPantry, RecipeRejected
from frigo.domain.pantry import urgent
from frigo.domain.recipe import Recipe, check_recipe
from frigo.ports.chef import Chef, RecipeRequest
from frigo.ports.clock import Clock
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.discard_expired import discard_expired


class SuggestRecipe:
    def __init__(self, pantry: PantryRepository, chef: Chef, clock: Clock) -> None:
        self._pantry = pantry
        self._chef = chef
        self._clock = clock

    def execute(self, servings: int, max_missing: int = 0) -> Recipe:
        today = self._clock.today()
        stock = discard_expired(self._pantry, today)
        if not stock:
            raise EmptyPantry

        request = RecipeRequest(
            ingredients=tuple(ingredient.name for ingredient in stock),
            use_first=tuple(ingredient.name for ingredient in urgent(stock, today)),
            servings=servings,
            max_missing=max_missing,
        )
        recipe = self._chef.suggest(request)
        try:
            check_recipe(recipe, stock, today, max_missing)
        except RecipeRejected as rejection:
            recipe = self._chef.suggest(replace(request, feedback=rejection.reason))
            check_recipe(recipe, stock, today, max_missing)

        return recipe
