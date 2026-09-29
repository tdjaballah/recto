from frigo.domain.ingredient import Ingredient
from frigo.ports.clock import Clock
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.discard_expired import discard_expired


class ListPantry:
    def __init__(self, pantry: PantryRepository, clock: Clock) -> None:
        self._pantry = pantry
        self._clock = clock

    def execute(self) -> list[Ingredient]:
        return discard_expired(self._pantry, self._clock.today())
