from pathlib import Path

from dependency_injector import containers, providers

from recto.adapters.pydantic_ai_models import PydanticAIVariantGenerator
from recto.adapters.sqlite_deck_repository import SqliteDeckRepository
from recto.adapters.system_clock import SystemClock
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository
from recto.ports.variant_generator import VariantGenerator
from recto.use_cases.import_deck import ImportDeck
from recto.use_cases.list_decks import ListDecks


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    deck_repository: providers.Provider[DeckRepository] = providers.Singleton(
        SqliteDeckRepository, path=config.db_path.as_(Path)
    )
    variant_generator: providers.Provider[VariantGenerator] = providers.Singleton(
        PydanticAIVariantGenerator, model=config.model
    )
    clock: providers.Provider[Clock] = providers.Singleton(SystemClock)

    import_deck = providers.Factory(ImportDeck, repository=deck_repository, generator=variant_generator)
    list_decks = providers.Factory(ListDecks, repository=deck_repository, clock=clock)
