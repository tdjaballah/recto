from pathlib import Path

from dependency_injector import providers
from textual.widgets import Static

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.tui.app import RectoApp
from recto.tui.decks import DecksScreen
from recto.tui.importing import ImportScreen
from tests.container import build_test_container
from tests.fakes.fake_variant_generator import FakeVariantGenerator


def setup() -> tuple[RectoApp, InMemoryDeckRepository, FakeVariantGenerator]:
    repository = InMemoryDeckRepository()
    generator = FakeVariantGenerator()
    container = build_test_container(
        deck_repository=providers.Object(repository), variant_generator=providers.Object(generator)
    )

    return RectoApp(container), repository, generator


async def test_example_deck_is_imported_and_listed() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("i", "down", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, DecksScreen)
        assert [deck.id for deck in repository.decks()] == ["geographie"]
        assert len(repository.knowledge("geographie")) == 50


async def test_deck_file_is_imported_from_its_path(tmp_path: Path) -> None:
    app, repository, _ = setup()
    deck = tmp_path / "espagnol.toml"
    deck.write_text(
        '[deck]\nname = "Espagnol"\ndescription = "Mots"\n\n[[cards]]\nid = "a"\nquestion = "Q"\nanswer = "A"\n'
    )

    async with app.run_test() as pilot:
        await pilot.press("i", "tab", *str(deck), "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert [deck.id for deck in repository.decks()] == ["espagnol"]


async def test_unreadable_file_is_reported() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("i", "tab", *"/nope/deck.toml", "enter")

        assert isinstance(app.screen, ImportScreen)
        assert "Cannot read" in str(app.screen.query_one("#status", Static).content)
        assert repository.decks() == []


async def test_failed_generation_is_reported_and_saves_nothing() -> None:
    app, repository, generator = setup()
    generator.fails_after(3)

    async with app.run_test() as pilot:
        await pilot.press("i", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, ImportScreen)
        assert "Import failed" in str(app.screen.query_one("#status", Static).content)
        assert repository.decks() == []


async def test_a_second_import_is_ignored_while_one_runs() -> None:
    app, _, generator = setup()
    generator.pause()

    async with app.run_test() as pilot:
        await pilot.press("i", "enter", "enter")
        generator.release()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(generator.requests) == 50


async def test_import_cannot_be_left_halfway() -> None:
    app, repository, generator = setup()
    generator.pause()

    async with app.run_test() as pilot:
        await pilot.press("i", "enter", "escape")

        assert isinstance(app.screen, ImportScreen)

        generator.release()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, DecksScreen)
        assert [deck.id for deck in repository.decks()] == ["anglais"]
