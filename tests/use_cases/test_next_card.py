from datetime import timedelta

from recto.domain.deck import Deck
from recto.domain.knowledge import Variant
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.next_card import NextCard
from tests.container import build_test_container
from tests.object_mothers.knowledge import NOW, KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales")


def setup() -> tuple[NextCard, DeckRepository]:
    container = build_test_container()

    return container.next_card(), container.deck_repository()


def test_due_knowledge_is_asked_before_new_knowledge() -> None:
    next_card, repository = setup()
    repository.save_deck(
        GEOGRAPHY,
        [KnowledgeMother.new().with_id("new").build(), KnowledgeMother.due().with_id("due").at_position(1).build()],
    )

    question = next_card.execute("geographie")

    assert question is not None
    assert question.knowledge.id == "due"
    assert (question.to_review, question.learning, question.new) == (1, 0, 1)


def test_question_is_one_of_the_knowledge_variants() -> None:
    next_card, repository = setup()
    knowledge = KnowledgeMother.new().with_variants(Variant("r", "Capitale française ?", "Paris")).build()
    repository.save_deck(GEOGRAPHY, [knowledge])

    question = next_card.execute("geographie")

    assert question is not None
    assert question.variant in knowledge.variants


def test_nothing_is_asked_when_nothing_is_due() -> None:
    next_card, repository = setup()
    repository.save_deck(GEOGRAPHY, [KnowledgeMother.new().due_at(NOW + timedelta(days=1)).build()])

    assert next_card.execute("geographie") is None
