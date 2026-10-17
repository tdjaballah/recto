from dependency_injector import providers
from textual.widgets import OptionList, Static

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.domain.deck import Deck
from recto.tui.app import RectoApp
from recto.tui.knowledge_list import KnowledgeListScreen
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
        assert prompt.endswith("1 to review ·  0 new")


async def test_enter_is_shown_as_the_key_to_review_a_deck() -> None:
    app, repository = setup()
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.new().build()])

    async with app.run_test():
        assert app.screen.active_bindings["enter"].binding.description == "Review"


async def test_long_descriptions_are_cut_so_the_counts_line_up() -> None:
    app, repository = setup()
    repository.save_deck(Deck("anglais", "Anglais", "Vocabulaire courant, faux amis et verbes irréguliers"), [])
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [])

    async with app.run_test():
        decks = app.screen.query_one("#decks", OptionList)
        prompts = [str(decks.get_option_at_index(index).prompt) for index in range(2)]
        assert prompts[0].index("to review") == prompts[1].index("to review")
        assert "…" in prompts[0]


async def test_cards_of_a_deck_are_shown_under_its_name() -> None:
    app, repository = setup()
    repository.save_deck(Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.new().build()])

    async with app.run_test() as pilot:
        await pilot.press("c")

        assert isinstance(app.screen, KnowledgeListScreen)
        assert app.screen.sub_title == "Géographie"


async def test_q_quits() -> None:
    app, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("q")

        assert app.return_code == 0
