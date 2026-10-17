from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from recto.domain.knowledge import Knowledge

NEW_PER_DAY = 10
LEARN_AHEAD = timedelta(minutes=20)


@dataclass(frozen=True)
class Today:
    due: tuple[Knowledge, ...]
    new: tuple[Knowledge, ...]
    ahead: tuple[Knowledge, ...]

    @property
    def queue(self) -> tuple[Knowledge, ...]:
        return (*self.due, *self.new, *self.ahead)

    @property
    def to_review(self) -> int:
        return len(self.due) + len(self.ahead)


def plan_today(knowledge: Sequence[Knowledge], now: datetime) -> Today:
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    due: list[tuple[datetime, Knowledge]] = []
    ahead: list[tuple[datetime, Knowledge]] = []
    new: list[Knowledge] = []
    introduced_today = 0
    for item in knowledge:
        memory = item.memory
        if memory is None:
            new.append(item)
            continue
        if memory.introduced_at >= start_of_day:
            introduced_today += 1
        if memory.due <= now:
            due.append((memory.due, item))
        elif memory.due <= now + LEARN_AHEAD:
            ahead.append((memory.due, item))

    new.sort(key=lambda item: item.position)
    return Today(
        due=_by_date(due),
        new=tuple(new[: max(0, NEW_PER_DAY - introduced_today)]),
        ahead=_by_date(ahead),
    )


def _by_date(dated: list[tuple[datetime, Knowledge]]) -> tuple[Knowledge, ...]:
    return tuple(item for _, item in sorted(dated, key=lambda pair: pair[0]))
