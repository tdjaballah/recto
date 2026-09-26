import pytest

from frigo.adapters.in_memory_pantry_repository import InMemoryPantryRepository
from frigo.ports.pantry_repository import PantryRepository
from tests.object_mothers.ingredient import IngredientMother


@pytest.fixture
def repo() -> PantryRepository:
    return InMemoryPantryRepository()


def test_saved_ingredient_is_found_by_name(repo: PantryRepository) -> None:
    ingredient = IngredientMother.fresh().build()

    repo.save(ingredient)

    assert repo.get(ingredient.name) == ingredient


def test_ingredient_without_expiry_is_saved_as_such(repo: PantryRepository) -> None:
    ingredient = IngredientMother.without_expiry().build()

    repo.save(ingredient)

    assert repo.get(ingredient.name) == ingredient


def test_unknown_ingredient_is_not_found(repo: PantryRepository) -> None:
    assert repo.get("eggs") is None


def test_saving_an_ingredient_twice_replaces_it(repo: PantryRepository) -> None:
    repo.save(IngredientMother.fresh().with_quantity(2).build())

    repo.save(IngredientMother.fresh().with_quantity(8).build())

    assert [ingredient.quantity for ingredient in repo.list()] == [8]


def test_removed_ingredient_is_gone(repo: PantryRepository) -> None:
    ingredient = IngredientMother.fresh().build()
    repo.save(ingredient)

    repo.remove(ingredient.name)

    assert repo.list() == []


def test_removing_an_unknown_ingredient_does_nothing(repo: PantryRepository) -> None:
    repo.remove("eggs")

    assert repo.list() == []
