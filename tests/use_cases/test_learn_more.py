from datetime import timedelta

from dependency_injector import providers

from recto.container import Container
from recto.domain.deck import Deck
from recto.domain.today import NEW_PER_DAY
from recto.use_cases.next_card import Question
from tests.container import build_test_container
from tests.fakes.fixed_clock import FixedClock
from tests.object_mothers.knowledge import NOW, KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales")


def setup() -> tuple[Container, FixedClock]:
    clock = FixedClock(NOW)
    container = build_test_container(clock=providers.Object(clock))
    introduced = [
        KnowledgeMother.new().with_id(f"seen{n}").introduced_at(NOW).due_at(NOW + timedelta(days=3)).build()
        for n in range(NEW_PER_DAY)
    ]
    new = [KnowledgeMother.new().with_id(f"k{n}").at_position(n).build() for n in range(15)]
    container.deck_repository().save_deck(GEOGRAPHY, [*introduced, *new])

    return container, clock


def test_learning_more_brings_new_knowledge_once_the_day_is_done() -> None:
    container, _ = setup()

    container.learn_more().execute("geographie")

    question = container.next_card().execute("geographie")
    assert isinstance(question, Question)
    assert question.knowledge.id.startswith("k")
    assert question.new == NEW_PER_DAY


def test_learning_more_is_capped_by_the_knowledge_left_unseen() -> None:
    container, _ = setup()

    container.learn_more().execute("geographie")
    container.learn_more().execute("geographie")

    question = container.next_card().execute("geographie")
    assert isinstance(question, Question)
    assert question.new == 15


def test_extra_new_knowledge_is_for_today_only() -> None:
    container, clock = setup()
    container.learn_more().execute("geographie")

    clock.advance(timedelta(days=1))

    question = container.next_card().execute("geographie")
    assert isinstance(question, Question)
    assert question.new == NEW_PER_DAY
