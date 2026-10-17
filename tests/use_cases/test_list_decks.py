from datetime import timedelta

from recto.domain.deck import Deck
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.list_decks import DeckSummary, ListDecks
from tests.container import build_test_container
from tests.object_mothers.knowledge import NOW, KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales")


def setup() -> tuple[ListDecks, DeckRepository]:
    container = build_test_container()

    return container.list_decks(), container.deck_repository()


def test_each_deck_shows_what_is_left_to_do_today() -> None:
    list_decks, repository = setup()
    repository.save_deck(
        GEOGRAPHY,
        [
            KnowledgeMother.due().with_id("due").build(),
            KnowledgeMother.new().with_id("new").at_position(1).build(),
            KnowledgeMother.new().with_id("later").due_at(NOW + timedelta(days=2)).build(),
        ],
    )

    assert list_decks.execute() == [DeckSummary(GEOGRAPHY, to_review=1, new=1)]


def test_no_deck_lists_nothing() -> None:
    list_decks, _ = setup()

    assert list_decks.execute() == []
