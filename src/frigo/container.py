from dependency_injector import containers, providers

from frigo.adapters.in_memory_pantry_repository import InMemoryPantryRepository
from frigo.ports.pantry_repository import PantryRepository
from frigo.use_cases.add_ingredient import AddIngredient
from frigo.use_cases.remove_ingredient import RemoveIngredient


class Container(containers.DeclarativeContainer):
    pantry_repository: providers.Provider[PantryRepository] = providers.Singleton(InMemoryPantryRepository)

    add_ingredient = providers.Factory(AddIngredient, pantry=pantry_repository)
    remove_ingredient = providers.Factory(RemoveIngredient, pantry=pantry_repository)
