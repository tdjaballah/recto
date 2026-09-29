from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.list_pantry import ListPantry
from tests.container import build_test_container
from tests.object_mothers.ingredient import IngredientMother


def setup() -> tuple[ListPantry, PantryRepository]:
    container = build_test_container()

    return container.list_pantry(), container.pantry_repository()


def test_ingredients_are_listed_by_expiry_with_undated_ones_last() -> None:
    list_pantry, pantry = setup()
    pantry.save(IngredientMother.without_expiry().build())
    pantry.save(IngredientMother.fresh().build())
    pantry.save(IngredientMother.expiring_soon().build())

    names = [ingredient.name for ingredient in list_pantry.execute()]

    assert names == ["cream", "eggs", "rice"]


def test_expired_ingredients_are_thrown_away() -> None:
    list_pantry, pantry = setup()
    pantry.save(IngredientMother.expired().build())
    pantry.save(IngredientMother.fresh().build())

    listed = list_pantry.execute()

    assert [ingredient.name for ingredient in listed] == ["eggs"]
    assert pantry.get("ham") is None
