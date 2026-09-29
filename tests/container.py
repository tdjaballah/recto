from typing import Any

from dependency_injector import providers

from frigo.adapters.in_memory_pantry_repository import InMemoryPantryRepository
from frigo.container import Container
from tests.fakes.fixed_clock import FixedClock
from tests.object_mothers.ingredient import TODAY


def build_test_container(**overrides: providers.Provider[Any]) -> Container:
    fakes: dict[str, providers.Provider[Any]] = {
        "pantry_repository": providers.Singleton(InMemoryPantryRepository),
        "clock": providers.Singleton(FixedClock, today=TODAY),
    }
    return Container(**(fakes | overrides))
