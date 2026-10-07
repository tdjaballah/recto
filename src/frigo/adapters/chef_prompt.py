from pydantic import BaseModel, Field

from frigo.domain.ingredient import normalize_name
from frigo.domain.recipe import Recipe
from frigo.ports.chef import RecipeRequest

INSTRUCTIONS = """
You suggest one home recipe from what is in the fridge.
Name each ingredient exactly as it is written in the fridge list, one ingredient per entry, without quantities.
Salt, pepper, water and oil are always available.
"""
MAX_TOKENS = 700


class RecipeDraft(BaseModel):
    title: str
    ingredients: list[str] = Field(min_length=1, max_length=12)
    steps: list[str] = Field(min_length=1, max_length=8)

    def to_recipe(self) -> Recipe:
        return Recipe(
            title=self.title,
            ingredients=tuple(normalize_name(ingredient) for ingredient in self.ingredients),
            steps=tuple(self.steps),
        )


def prompt(request: RecipeRequest) -> str:
    lines = [
        f"Fridge: {', '.join(request.ingredients)}",
        f"Servings: {request.servings}",
        f"Ingredients you may add that are not in the fridge: {request.max_missing}",
    ]
    if request.use_first:
        lines.append(f"Use at least one of these, they expire soon: {', '.join(request.use_first)}")
    if request.feedback:
        lines.append(f"Your previous recipe was rejected: {request.feedback}")
    return "\n".join(lines)
