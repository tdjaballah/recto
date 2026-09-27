from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.add_ingredient import AddIngredient
from tests.container import build_test_container
from tests.object_mothers.ingredient import IngredientMother


def setup() -> tuple[AddIngredient, PantryRepository]:
    container = build_test_container()

    return container.add_ingredient(), container.pantry_repository()


def test_added_ingredient_is_stored_under_its_normalized_name() -> None:
    add_ingredient, pantry = setup()

    add_ingredient.execute("  Eggs ", 6)

    assert pantry.get("eggs") is not None


def test_adding_an_ingredient_already_in_the_fridge_restocks_it() -> None:
    add_ingredient, pantry = setup()
    pantry.save(IngredientMother.fresh().with_name("eggs").with_quantity(2).build())

    ingredient = add_ingredient.execute("eggs", 6)

    assert ingredient.quantity == 8
    assert len(pantry.list()) == 1
