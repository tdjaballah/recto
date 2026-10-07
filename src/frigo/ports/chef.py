from abc import ABC, abstractmethod
from dataclasses import dataclass

from frigo.domain.recipe import Recipe


@dataclass(frozen=True)
class RecipeRequest:
    ingredients: tuple[str, ...]
    use_first: tuple[str, ...]
    servings: int
    max_missing: int
    feedback: str | None = None


class Chef(ABC):
    @abstractmethod
    def suggest(self, request: RecipeRequest) -> Recipe: ...
