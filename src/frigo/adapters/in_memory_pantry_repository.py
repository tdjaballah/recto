from frigo.domain.ingredient import Ingredient
from frigo.ports.pantry_repository import PantryRepository


class InMemoryPantryRepository(PantryRepository):
    def __init__(self) -> None:
        self._ingredients: dict[str, Ingredient] = {}

    def get(self, name: str) -> Ingredient | None:
        return self._ingredients.get(name)

    def save(self, ingredient: Ingredient) -> None:
        self._ingredients[ingredient.name] = ingredient

    def remove(self, name: str) -> None:
        self._ingredients.pop(name, None)

    def list(self) -> list[Ingredient]:
        return list(self._ingredients.values())
