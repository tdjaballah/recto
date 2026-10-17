import uuid
from dataclasses import dataclass, replace
from typing import Self

from recto.domain.deck import SourceCard
from recto.domain.errors import EmptyVariant, OriginalIsReadOnly, VariantNotFound
from recto.domain.memory import Memory

ORIGINAL = "original"


@dataclass(frozen=True)
class Variant:
    id: str
    question: str
    answer: str

    @property
    def is_original(self) -> bool:
        return self.id == ORIGINAL


def new_variant(question: str, answer: str) -> Variant:
    question, answer = question.strip(), answer.strip()
    if not question or not answer:
        raise EmptyVariant
    return Variant(id=uuid.uuid4().hex, question=question, answer=answer)


@dataclass(frozen=True)
class Knowledge:
    deck_id: str
    id: str
    position: int
    variants: tuple[Variant, ...]
    memory: Memory | None = None

    @property
    def original(self) -> Variant:
        return self.variant(ORIGINAL)

    def variant(self, variant_id: str) -> Variant:
        for variant in self.variants:
            if variant.id == variant_id:
                return variant
        raise VariantNotFound(variant_id)

    def matches(self, card: SourceCard) -> bool:
        return (self.original.question, self.original.answer) == (card.question, card.answer)

    def with_variants(self, *variants: Variant) -> Self:
        return replace(self, variants=(*self.variants, *variants))

    def with_edited_variant(self, variant_id: str, question: str, answer: str) -> Self:
        edited = replace(new_variant(question, answer), id=self._editable(variant_id).id)
        return replace(self, variants=tuple(edited if v.id == variant_id else v for v in self.variants))

    def without_variant(self, variant_id: str) -> Self:
        self._editable(variant_id)
        return replace(self, variants=tuple(v for v in self.variants if v.id != variant_id))

    def rewritten(self, card: SourceCard, position: int) -> "Knowledge":
        return replace(new_knowledge(self.deck_id, card, position), memory=self.memory)

    def _editable(self, variant_id: str) -> Variant:
        variant = self.variant(variant_id)
        if variant.is_original:
            raise OriginalIsReadOnly(variant_id)
        return variant


def new_knowledge(deck_id: str, card: SourceCard, position: int) -> Knowledge:
    original = Variant(id=ORIGINAL, question=card.question, answer=card.answer)
    return Knowledge(deck_id=deck_id, id=card.id, position=position, variants=(original,))
