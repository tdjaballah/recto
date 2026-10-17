from typing import Any

from dependency_injector import providers

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.container import Container
from tests.fakes.fake_variant_generator import FakeVariantGenerator
from tests.fakes.fixed_clock import FixedClock
from tests.object_mothers.knowledge import NOW


def build_test_container(**overrides: providers.Provider[Any]) -> Container:
    fakes: dict[str, providers.Provider[Any]] = {
        "deck_repository": providers.Singleton(InMemoryDeckRepository),
        "variant_generator": providers.Singleton(FakeVariantGenerator),
        "clock": providers.Singleton(FixedClock, now=NOW),
    }
    return Container(**(fakes | overrides))
