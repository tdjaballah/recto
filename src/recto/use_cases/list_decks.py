from dataclasses import dataclass

from recto.domain.deck import Deck
from recto.domain.today import plan_today
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository


@dataclass(frozen=True)
class DeckSummary:
    deck: Deck
    to_review: int
    learning: int
    new: int


class ListDecks:
    def __init__(self, repository: DeckRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self) -> list[DeckSummary]:
        now = self._clock.now()
        summaries: list[DeckSummary] = []
        for deck in self._repository.decks():
            today = plan_today(self._repository.knowledge(deck.id), now)
            summaries.append(
                DeckSummary(deck=deck, to_review=today.to_review, learning=today.learning, new=len(today.new))
            )
        return summaries
