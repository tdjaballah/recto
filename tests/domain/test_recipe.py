import pytest

from frigo.domain.errors import RecipeRejected
from frigo.domain.recipe import check_recipe, missing_ingredients
from tests.object_mothers.ingredient import TODAY, IngredientMother
from tests.object_mothers.recipe import RecipeMother


def test_staples_are_never_missing() -> None:
    recipe = RecipeMother.omelette().with_ingredients("eggs", "salt", "oil").build()

    assert missing_ingredients(recipe, [IngredientMother.fresh().build()]) == []


def test_recipe_is_rejected_when_too_much_is_missing() -> None:
    recipe = RecipeMother.omelette().with_ingredients("eggs", "cheese", "ham").build()

    with pytest.raises(RecipeRejected, match="cheese, ham"):
        check_recipe(recipe, [IngredientMother.fresh().build()], TODAY, max_missing=1)


def test_recipe_may_miss_as_many_ingredients_as_allowed() -> None:
    recipe = RecipeMother.omelette().with_ingredients("eggs", "cheese").build()

    check_recipe(recipe, [IngredientMother.fresh().build()], TODAY, max_missing=1)


def test_recipe_is_rejected_when_it_ignores_what_expires_soon() -> None:
    stock = [IngredientMother.fresh().build(), IngredientMother.expiring_soon().build()]
    recipe = RecipeMother.omelette().with_ingredients("eggs").build()

    with pytest.raises(RecipeRejected, match="cream"):
        check_recipe(recipe, stock, TODAY, max_missing=0)
