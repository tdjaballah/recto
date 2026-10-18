from dataclasses import dataclass
from datetime import UTC, datetime

import fsrs

from recto.domain.grading import Rating

_SCHEDULER = fsrs.Scheduler(enable_fuzzing=False)
_FSRS_RATINGS = {Rating.AGAIN: fsrs.Rating.Again, Rating.HARD: fsrs.Rating.Hard, Rating.GOOD: fsrs.Rating.Good}


@dataclass(frozen=True)
class Memory:
    due: datetime
    introduced_at: datetime
    fsrs_card: str

    @property
    def learning(self) -> bool:
        return fsrs.Card.from_json(self.fsrs_card).state != fsrs.State.Review


def remember(memory: Memory | None, rating: Rating, now: datetime) -> Memory:
    now = now.astimezone(UTC)
    card = fsrs.Card.from_json(memory.fsrs_card) if memory else fsrs.Card(due=now)
    card, _ = _SCHEDULER.review_card(card, _FSRS_RATINGS[rating], now)
    introduced_at = memory.introduced_at if memory else now
    return Memory(due=card.due, introduced_at=introduced_at, fsrs_card=card.to_json())
