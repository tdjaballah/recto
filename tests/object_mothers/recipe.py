from dataclasses import replace
from typing import Self

from frigo.domain.recipe import Recipe


class RecipeMother:
    _recipe: Recipe

    def __init__(self) -> None:
        raise TypeError("Use a named factory such as RecipeMother.omelette()")

    @classmethod
    def _of(cls, recipe: Recipe) -> Self:
        mother = cls.__new__(cls)
        mother._recipe = recipe
        return mother

    @classmethod
    def omelette(cls) -> Self:
        return cls._of(
            Recipe(title="Omelette", ingredients=("eggs", "salt"), steps=("Beat the eggs", "Cook in a hot pan"))
        )

    def with_ingredients(self, *ingredients: str) -> Self:
        self._recipe = replace(self._recipe, ingredients=ingredients)
        return self

    def build(self) -> Recipe:
        return replace(self._recipe)
