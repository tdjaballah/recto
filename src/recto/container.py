from pathlib import Path

from dependency_injector import containers, providers

from recto.adapters.sqlite_deck_repository import SqliteDeckRepository
from recto.adapters.system_clock import SystemClock
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.list_decks import ListDecks


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    deck_repository: providers.Provider[DeckRepository] = providers.Singleton(
        SqliteDeckRepository, path=config.db_path.as_(Path)
    )
    clock: providers.Provider[Clock] = providers.Singleton(SystemClock)

    list_decks = providers.Factory(ListDecks, repository=deck_repository, clock=clock)
