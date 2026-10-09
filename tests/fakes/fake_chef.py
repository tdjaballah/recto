from frigo.domain.errors import ChefUnavailable
from frigo.domain.recipe import Recipe
from frigo.ports.chef import Chef, RecipeRequest


class FakeChef(Chef):
    def __init__(self) -> None:
        self._recipes: list[Recipe] = []
        self.requests: list[RecipeRequest] = []

    def will_suggest(self, *recipes: Recipe) -> None:
        self._recipes = list(recipes)

    def suggest(self, request: RecipeRequest) -> Recipe:
        self.requests.append(request)
        if not self._recipes:
            raise ChefUnavailable("no recipe left")
        return self._recipes.pop(0)
