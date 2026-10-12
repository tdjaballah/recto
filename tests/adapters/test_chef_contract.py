from collections.abc import Callable

import pytest
from ollama import Client
from openai import OpenAI

from frigo.adapters.ollama_chef import OllamaChef
from frigo.adapters.openai_chef import OpenAIChef
from frigo.domain.errors import ChefUnavailable
from frigo.domain.ingredient import normalize_name
from frigo.ports.chef import Chef, RecipeRequest
from tests.adapters.conftest import OLLAMA_MODEL

pytestmark = pytest.mark.container

REQUEST = RecipeRequest(ingredients=("eggs", "cream"), use_first=("cream",), servings=2, max_missing=0)


def ollama_chef(url: str, model: str = OLLAMA_MODEL) -> Chef:
    return OllamaChef(Client(host=url), model)


def openai_chef(url: str, model: str = OLLAMA_MODEL) -> Chef:
    return OpenAIChef(OpenAI(base_url=f"{url}/v1", api_key="unused"), model)


@pytest.fixture(params=[ollama_chef, openai_chef])
def new_chef(request: pytest.FixtureRequest) -> Callable[..., Chef]:
    return request.param


def test_suggested_recipe_is_complete_and_names_ingredients_like_the_fridge(
    new_chef: Callable[..., Chef], ollama_url: str
) -> None:
    chef = new_chef(ollama_url)

    recipe = chef.suggest(REQUEST)

    assert recipe.title
    assert recipe.steps
    assert recipe.ingredients
    assert all(name == normalize_name(name) for name in recipe.ingredients)


def test_unknown_model_is_reported_as_an_unavailable_chef(new_chef: Callable[..., Chef], ollama_url: str) -> None:
    chef = new_chef(ollama_url, model="no-such-model")

    with pytest.raises(ChefUnavailable):
        chef.suggest(REQUEST)


def test_unreachable_server_is_reported_as_an_unavailable_chef(new_chef: Callable[..., Chef]) -> None:
    chef = new_chef("http://localhost:1")

    with pytest.raises(ChefUnavailable):
        chef.suggest(REQUEST)
