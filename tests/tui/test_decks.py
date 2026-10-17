from dependency_injector import providers
from textual.widgets import OptionList, Static

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.domain.deck import Deck
from recto.tui.app import RectoApp
from tests.container import build_test_container
from tests.object_mothers.knowledge import KnowledgeMother


def setup() -> tuple[RectoApp, InMemoryDeckRepository]:
    repository = InMemoryDeckRepository()
    container = build_test_container(deck_repository=providers.Object(repository))

    return RectoApp(container), repository


async def test_the_app_is_called_recto() -> None:
    app, _ = setup()

    async with app.run_test():
        assert app.title == "Recto"


async def test_without_decks_the_screen_points_to_import() -> None:
    app, _ = setup()

    async with app.run_test():
        assert "Press i to import" in str(app.screen.query_one("#empty", Static).content)


async def test_decks_show_what_is_left_today() -> None:
    app, repository = setup()
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.due().build()])

    async with app.run_test():
        prompt = str(app.screen.query_one("#decks", OptionList).get_option_at_index(0).prompt)
        assert prompt.startswith("Géographie")
        assert prompt.endswith("1 ·  0 ✦")


async def test_q_quits() -> None:
    app, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("q")

        assert app.return_code == 0
