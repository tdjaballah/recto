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
    remaining: int


class NextCard:
    def __init__(self, repository: DeckRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, deck_id: str) -> Question | None:
        queue = plan_today(self._repository.knowledge(deck_id), self._clock.now()).queue
        if not queue:
            return None
        knowledge = queue[0]
        return Question(knowledge=knowledge, variant=random.choice(knowledge.variants), remaining=len(queue))
