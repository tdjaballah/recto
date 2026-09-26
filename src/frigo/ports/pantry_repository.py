from abc import ABC, abstractmethod

from frigo.domain.ingredient import Ingredient


class PantryRepository(ABC):
    @abstractmethod
    def get(self, name: str) -> Ingredient | None: ...

    @abstractmethod
    def save(self, ingredient: Ingredient) -> None: ...

    @abstractmethod
    def remove(self, name: str) -> None: ...

    @abstractmethod
    def list(self) -> list[Ingredient]: ...
