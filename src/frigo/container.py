from pathlib import Path

from dependency_injector import containers, providers
from ollama import Client

from frigo.adapters.ollama_chef import OllamaChef
from frigo.adapters.sqlite_pantry_repository import SqlitePantryRepository
from frigo.adapters.system_clock import SystemClock
from frigo.ports.chef import Chef
from frigo.ports.clock import Clock
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.add_ingredient import AddIngredient
from frigo.use_cases.list_pantry import ListPantry
from frigo.use_cases.remove_ingredient import RemoveIngredient
from frigo.use_cases.suggest_recipe import SuggestRecipe


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    pantry_repository: providers.Provider[PantryRepository] = providers.Singleton(
        SqlitePantryRepository, path=config.db_path.as_(Path)
    )
    ollama_client = providers.Singleton(Client, host=config.ollama.url)
    chef: providers.Provider[Chef] = providers.Singleton(OllamaChef, client=ollama_client, model=config.ollama.model)
    clock: providers.Provider[Clock] = providers.Singleton(SystemClock)

    add_ingredient = providers.Factory(AddIngredient, pantry=pantry_repository)
    remove_ingredient = providers.Factory(RemoveIngredient, pantry=pantry_repository)
    list_pantry = providers.Factory(ListPantry, pantry=pantry_repository, clock=clock)
    suggest_recipe = providers.Factory(SuggestRecipe, pantry=pantry_repository, chef=chef, clock=clock)
