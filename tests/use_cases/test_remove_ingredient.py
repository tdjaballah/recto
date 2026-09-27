import pytest

from frigo.domain.errors import IngredientNotFound
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.remove_ingredient import RemoveIngredient
from tests.container import build_test_container
from tests.object_mothers.ingredient import IngredientMother


def setup() -> tuple[RemoveIngredient, PantryRepository]:
    container = build_test_container()

    return container.remove_ingredient(), container.pantry_repository()


def test_removed_ingredient_leaves_the_fridge() -> None:
    remove_ingredient, pantry = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").build())

    remove_ingredient.execute("Eggs")

    assert pantry.list() == []


def test_removing_an_unknown_ingredient_fails() -> None:
    remove_ingredient, _ = setup()

    with pytest.raises(IngredientNotFound):
        remove_ingredient.execute("eggs")
