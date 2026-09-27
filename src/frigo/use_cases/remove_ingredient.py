from frigo.domain.errors import IngredientNotFound
from frigo.domain.ingredient import normalize_name
from frigo.ports.pantry_repository import PantryRepository


class RemoveIngredient:
    def __init__(self, pantry: PantryRepository) -> None:
        self._pantry = pantry

    def execute(self, raw_name: str) -> None:
        name = normalize_name(raw_name)
        if self._pantry.get(name) is None:
            raise IngredientNotFound(name)

        self._pantry.remove(name)
