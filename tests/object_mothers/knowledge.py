from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Self

from recto.domain.deck import SourceCard
from recto.domain.grading import Rating
from recto.domain.knowledge import Knowledge, Variant, new_knowledge
from recto.domain.memory import Memory, remember

NOW = datetime(2026, 10, 16, 9, 0, tzinfo=UTC)


class KnowledgeMother:
    _knowledge: Knowledge

    def __init__(self) -> None:
        raise TypeError("Use a named factory such as KnowledgeMother.new()")

    @classmethod
    def _of(cls, knowledge: Knowledge) -> Self:
        mother = cls.__new__(cls)
        mother._knowledge = knowledge
        return mother

    @classmethod
    def new(cls) -> Self:
        return cls._of(new_knowledge("geographie", SourceCard("france", "Capitale de la France ?", "Paris"), 0))

    @classmethod
    def due(cls) -> Self:
        return cls.new().due_at(NOW - timedelta(days=1))

    def with_id(self, knowledge_id: str) -> Self:
        self._knowledge = replace(self._knowledge, id=knowledge_id)
        return self

    def at_position(self, position: int) -> Self:
        self._knowledge = replace(self._knowledge, position=position)
        return self

    def with_variants(self, *variants: Variant) -> Self:
        self._knowledge = self._knowledge.with_variants(*variants)
        return self

    def due_at(self, when: datetime) -> Self:
        memory = self._knowledge.memory or _learnt(when - timedelta(days=3))
        self._knowledge = replace(self._knowledge, memory=replace(memory, due=when))
        return self

    def answered(self, rating: Rating, at: datetime) -> Self:
        self._knowledge = replace(self._knowledge, memory=remember(self._knowledge.memory, rating, at))
        return self

    def introduced_at(self, when: datetime) -> Self:
        memory = self._knowledge.memory or remember(None, Rating.GOOD, when)
        self._knowledge = replace(self._knowledge, memory=replace(memory, introduced_at=when))
        return self

    def build(self) -> Knowledge:
        return replace(self._knowledge)


def _learnt(at: datetime) -> Memory:
    seen = remember(None, Rating.GOOD, at)
    return remember(seen, Rating.GOOD, seen.due)
