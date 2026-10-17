from collections.abc import Sequence

from recto.domain.deck import Deck
from recto.domain.knowledge import Knowledge
from recto.domain.review import Review
from recto.ports.deck_repository import DeckRepository


class InMemoryDeckRepository(DeckRepository):
    def __init__(self) -> None:
        self._decks: dict[str, Deck] = {}
        self._knowledge: dict[str, dict[str, Knowledge]] = {}
        self._reviews: list[Review] = []

    def save_deck(self, deck: Deck, knowledge: Sequence[Knowledge]) -> None:
        kept = {item.id for item in knowledge}
        self._reviews = [r for r in self._reviews if r.deck_id != deck.id or r.knowledge_id in kept]
        self._decks[deck.id] = deck
        self._knowledge[deck.id] = {item.id: item for item in knowledge}

    def decks(self) -> list[Deck]:
        return sorted(self._decks.values(), key=lambda deck: deck.name)

    def deck(self, deck_id: str) -> Deck | None:
        return self._decks.get(deck_id)

    def knowledge(self, deck_id: str) -> list[Knowledge]:
        return sorted(self._knowledge.get(deck_id, {}).values(), key=lambda item: item.position)

    def get_knowledge(self, deck_id: str, knowledge_id: str) -> Knowledge | None:
        return self._knowledge.get(deck_id, {}).get(knowledge_id)

    def save_knowledge(self, knowledge: Knowledge) -> None:
        self._knowledge[knowledge.deck_id][knowledge.id] = knowledge

    def add_review(self, review: Review) -> None:
        self._reviews.append(review)

    def reviews(self, deck_id: str, knowledge_id: str) -> list[Review]:
        return [r for r in self._reviews if (r.deck_id, r.knowledge_id) == (deck_id, knowledge_id)]
