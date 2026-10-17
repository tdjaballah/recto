import pytest
from dependency_injector import providers

from recto.domain.deck import Deck
from recto.domain.errors import ModelUnavailable
from recto.domain.grading import Grade, Rating
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.submit_answer import SubmitAnswer
from tests.container import build_test_container
from tests.fakes.fake_answer_judge import FakeAnswerJudge
from tests.object_mothers.knowledge import NOW, KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales", "Réponds en français.")


def setup() -> tuple[SubmitAnswer, DeckRepository, FakeAnswerJudge]:
    judge = FakeAnswerJudge()
    container = build_test_container(answer_judge=providers.Object(judge))
    repository = container.deck_repository()
    repository.save_deck(GEOGRAPHY, [KnowledgeMother.new().build()])

    return container.submit_answer(), repository, judge


def test_answer_is_judged_against_the_variant_asked() -> None:
    submit_answer, _, judge = setup()
    judge.will_grade(Grade(1.0, "Exact."))

    grade = submit_answer.execute("geographie", "france", "original", " paris ")

    assert grade == Grade(1.0, "Exact.")
    variant, answer, instructions = judge.requests[0]
    assert (variant.answer, answer, instructions) == ("Paris", "paris", "Réponds en français.")


def test_judged_answer_schedules_the_knowledge_and_is_logged() -> None:
    submit_answer, repository, judge = setup()
    judge.will_grade(Grade(0.25, "Il manque la région."))

    submit_answer.execute("geographie", "france", "original", "Paris ?")

    knowledge = repository.get_knowledge("geographie", "france")
    assert knowledge is not None
    assert knowledge.memory is not None
    assert knowledge.memory.introduced_at == NOW
    [review] = repository.reviews("geographie", "france")
    assert (review.rating, review.grade.score, review.reviewed_at) == (Rating.AGAIN, 0.25, NOW)


def test_blank_answer_scores_zero_without_asking_the_model() -> None:
    submit_answer, _, judge = setup()

    grade = submit_answer.execute("geographie", "france", "original", "   ")

    assert grade.score == 0
    assert judge.requests == []


def test_answer_that_cannot_be_judged_changes_nothing() -> None:
    submit_answer, repository, _ = setup()

    with pytest.raises(ModelUnavailable):
        submit_answer.execute("geographie", "france", "original", "Paris")

    assert repository.get_knowledge("geographie", "france") == KnowledgeMother.new().build()
    assert repository.reviews("geographie", "france") == []
