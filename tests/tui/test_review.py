from dependency_injector import providers
from textual.widgets import Input, Static

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.domain.deck import Deck
from recto.domain.grading import Grade
from recto.tui.app import RectoApp
from recto.tui.decks import DecksScreen
from recto.tui.review import ReviewScreen
from tests.container import build_test_container
from tests.fakes.fake_answer_judge import FakeAnswerJudge
from tests.object_mothers.knowledge import KnowledgeMother


def setup() -> tuple[RectoApp, InMemoryDeckRepository, FakeAnswerJudge]:
    repository = InMemoryDeckRepository()
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.new().build()])
    judge = FakeAnswerJudge()
    container = build_test_container(deck_repository=providers.Object(repository), answer_judge=providers.Object(judge))

    return RectoApp(container), repository, judge


def text(app: RectoApp, widget_id: str) -> str:
    return str(app.screen.query_one(widget_id, Static).content)


async def test_question_is_asked() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("enter")

        assert isinstance(app.screen, ReviewScreen)
        assert app.screen.sub_title == "Géographie"
        assert text(app, "#question") == "Capitale de la France ?"
        assert text(app, "#progress") == "0 to review · 1 new"


async def test_typed_answer_is_graded_and_the_reference_shown() -> None:
    app, repository, judge = setup()
    judge.will_grade(Grade(0.5, "Presque."))

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert text(app, "#grade") == "~ 50 %   Presque."
        assert text(app, "#expected") == "Answer: Paris"
        assert judge.requests[0][1] == "paris"
        assert len(repository.reviews("geographie", "france")) == 1


async def test_answer_that_cannot_be_graded_stays_in_the_input() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert text(app, "#grade").startswith("Could not grade the answer")
        assert app.screen.query_one("#answer", Input).value == "paris"
        assert repository.reviews("geographie", "france") == []


async def test_knowledge_seen_for_the_first_time_comes_back_in_the_same_session() -> None:
    app, _, judge = setup()
    judge.will_grade(Grade(1.0, "Exact."))

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("enter")

        assert isinstance(app.screen, ReviewScreen)
        assert text(app, "#question") == "Capitale de la France ?"


async def test_typing_after_a_grading_error_adds_to_the_answer() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("!")

        assert app.screen.query_one("#answer", Input).value == "paris!"


async def test_session_ends_when_nothing_is_left() -> None:
    app, repository, judge = setup()
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.due().build()])
    judge.will_grade(Grade(1.0, "Exact."))

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("enter")

        assert isinstance(app.screen, DecksScreen)


async def test_variants_cannot_be_opened_from_a_review() -> None:
    app, _, judge = setup()
    judge.will_grade(Grade(1.0, "Exact."))

    async with app.run_test() as pilot:
        await pilot.press("enter", *"paris", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("v")

        assert isinstance(app.screen, ReviewScreen)
