import random
from dataclasses import dataclass

from recto.domain.knowledge import Knowledge, Variant
from recto.domain.today import plan_today
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository


@dataclass(frozen=True)
class Question:
    knowledge: Knowledge
    variant: Variant
    to_review: int
    learning: int
    new: int


@dataclass(frozen=True)
class DoneForToday:
    unseen: int


class NextCard:
    def __init__(self, repository: DeckRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, deck_id: str) -> Question | DoneForToday:
        now = self._clock.now()
        today = plan_today(
            self._repository.knowledge(deck_id), now, extra_new=self._repository.extra_new(deck_id, now.date())
        )
        if not today.queue:
            return DoneForToday(unseen=today.unseen)
        knowledge = today.queue[0]
        return Question(
            knowledge=knowledge,
            variant=random.choice(knowledge.variants),
            to_review=today.to_review,
            learning=today.learning,
            new=len(today.new),
        )
