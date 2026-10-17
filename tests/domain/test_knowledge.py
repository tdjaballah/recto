import pytest

from recto.domain.deck import SourceCard
from recto.domain.errors import EmptyVariant, OriginalIsReadOnly, VariantNotFound
from recto.domain.knowledge import ORIGINAL, Variant, new_knowledge, new_variant
from tests.object_mothers.knowledge import KnowledgeMother

REPHRASED = Variant(id="rephrased", question="Quelle ville est la capitale française ?", answer="Paris")


def test_new_knowledge_has_only_its_original_variant() -> None:
    knowledge = new_knowledge("geographie", SourceCard("france", "Capitale de la France ?", "Paris"), 0)

    assert knowledge.variants == (Variant(id=ORIGINAL, question="Capitale de la France ?", answer="Paris"),)
    assert knowledge.memory is None


def test_new_variant_is_trimmed_and_gets_its_own_id() -> None:
    first = new_variant("  Capitale ?  ", " Paris ")
    second = new_variant("Capitale ?", "Paris")

    assert (first.question, first.answer) == ("Capitale ?", "Paris")
    assert first.id != second.id


@pytest.mark.parametrize(("question", "answer"), [("", "Paris"), ("Capitale ?", "   ")])
def test_variant_needs_a_question_and_an_answer(question: str, answer: str) -> None:
    with pytest.raises(EmptyVariant):
        new_variant(question, answer)


def test_variant_is_edited_in_place() -> None:
    knowledge = KnowledgeMother.new().with_variants(REPHRASED).build()

    edited = knowledge.with_edited_variant("rephrased", "Capitale française ?", "Paris")

    assert edited.variant("rephrased").question == "Capitale française ?"
    assert len(edited.variants) == 2


def test_variant_is_deleted() -> None:
    knowledge = KnowledgeMother.new().with_variants(REPHRASED).build()

    assert knowledge.without_variant("rephrased").variants == (knowledge.original,)


def test_original_variant_cannot_be_edited_or_deleted() -> None:
    knowledge = KnowledgeMother.new().build()

    with pytest.raises(OriginalIsReadOnly):
        knowledge.with_edited_variant(ORIGINAL, "Autre ?", "Autre")
    with pytest.raises(OriginalIsReadOnly):
        knowledge.without_variant(ORIGINAL)


def test_unknown_variant_is_not_found() -> None:
    with pytest.raises(VariantNotFound):
        KnowledgeMother.new().build().without_variant("nope")


def test_rewritten_knowledge_keeps_its_memory_and_drops_its_variants() -> None:
    knowledge = KnowledgeMother.due().with_variants(REPHRASED).build()

    rewritten = knowledge.rewritten(SourceCard("france", "Capitale de la France ?", "Paris (Île-de-France)"), 3)

    assert rewritten.memory == knowledge.memory
    assert rewritten.variants == (Variant(ORIGINAL, "Capitale de la France ?", "Paris (Île-de-France)"),)
    assert rewritten.position == 3
