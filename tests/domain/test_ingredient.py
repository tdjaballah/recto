from datetime import timedelta

import pytest

from frigo.domain.errors import InvalidIngredientName, InvalidQuantity
from frigo.domain.ingredient import new_ingredient, normalize_name
from tests.object_mothers.ingredient import TODAY, IngredientMother


def test_name_is_lowercased_and_trimmed() -> None:
    assert normalize_name("  Crème   Fraîche ") == "crème fraîche"


def test_ingredient_needs_a_name() -> None:
    with pytest.raises(InvalidIngredientName):
        new_ingredient("   ", 1)


def test_ingredient_needs_a_positive_quantity() -> None:
    with pytest.raises(InvalidQuantity):
        new_ingredient("eggs", 0)


def test_ingredient_expires_the_day_after_its_date() -> None:
    ingredient = IngredientMother.fresh().expiring_on(TODAY).build()

    assert not ingredient.is_expired(TODAY)
    assert ingredient.is_expired(TODAY + timedelta(days=1))


def test_ingredient_without_expiry_never_expires() -> None:
    ingredient = IngredientMother.without_expiry().build()

    assert not ingredient.is_expired(TODAY + timedelta(days=3650))


def test_restocking_adds_quantities_and_keeps_the_earliest_expiry() -> None:
    older = IngredientMother.fresh().with_quantity(2).expiring_on(TODAY + timedelta(days=2)).build()
    newer = IngredientMother.fresh().with_quantity(6).expiring_on(TODAY + timedelta(days=9)).build()

    restocked = older.restocked_with(newer)

    assert restocked.quantity == 8
    assert restocked.expires_on == TODAY + timedelta(days=2)
