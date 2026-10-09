import pytest
from dependency_injector import providers

from frigo.domain.errors import EmptyPantry, RecipeRejected
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.suggest_recipe import SuggestRecipe
from tests.container import build_test_container
from tests.fakes.fake_chef import FakeChef
from tests.object_mothers.ingredient import IngredientMother
from tests.object_mothers.recipe import RecipeMother


def setup() -> tuple[SuggestRecipe, PantryRepository, FakeChef]:
    chef = FakeChef()
    container = build_test_container(chef=providers.Object(chef))

    return container.suggest_recipe(), container.pantry_repository(), chef


def test_recipe_made_of_what_is_in_the_fridge_is_returned() -> None:
    suggest_recipe, pantry, chef = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").build())
    omelette = RecipeMother.omelette().build()
    chef.will_suggest(omelette)

    assert suggest_recipe.execute(servings=2) == omelette


def test_empty_fridge_has_no_recipe() -> None:
    suggest_recipe, _, _ = setup()

    with pytest.raises(EmptyPantry):
        suggest_recipe.execute(servings=2)


def test_expired_ingredients_are_never_offered_to_the_chef() -> None:
    suggest_recipe, pantry, chef = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").build())
    pantry.save(IngredientMother.expired().with_name("ham").build())
    chef.will_suggest(RecipeMother.omelette().build())

    suggest_recipe.execute(servings=2)

    assert chef.requests[0].ingredients == ("eggs",)


def test_rejected_recipe_is_asked_again_with_the_reason() -> None:
    suggest_recipe, pantry, chef = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").build())
    invented = RecipeMother.omelette().with_ingredients("eggs", "truffle").build()
    omelette = RecipeMother.omelette().build()
    chef.will_suggest(invented, omelette)

    recipe = suggest_recipe.execute(servings=2)

    assert recipe == omelette
    assert chef.requests[1].feedback == "not in the fridge: truffle"


def test_recipe_rejected_twice_fails() -> None:
    suggest_recipe, pantry, chef = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").build())
    invented = RecipeMother.omelette().with_ingredients("eggs", "truffle").build()
    chef.will_suggest(invented, invented)

    with pytest.raises(RecipeRejected):
        suggest_recipe.execute(servings=2)
