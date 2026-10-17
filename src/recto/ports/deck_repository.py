from abc import ABC, abstractmethod
from collections.abc import Sequence

from recto.domain.deck import Deck
from recto.domain.knowledge import Knowledge
from recto.domain.review import Review


class DeckRepository(ABC):
    @abstractmethod
    def save_deck(self, deck: Deck, knowledge: Sequence[Knowledge]) -> None:
        """Save the deck with exactly this knowledge; knowledge left out is deleted with its reviews."""

    @abstractmethod
    def decks(self) -> list[Deck]: ...

    @abstractmethod
    def deck(self, deck_id: str) -> Deck | None: ...

    @abstractmethod
    def knowledge(self, deck_id: str) -> list[Knowledge]: ...

    @abstractmethod
    def get_knowledge(self, deck_id: str, knowledge_id: str) -> Knowledge | None: ...

    @abstractmethod
    def save_knowledge(self, knowledge: Knowledge) -> None: ...

    @abstractmethod
    def add_review(self, review: Review) -> None: ...

    @abstractmethod
    def reviews(self, deck_id: str, knowledge_id: str) -> list[Review]: ...
