from dependency_injector import providers
from textual.widgets import Footer, OptionList, Static

from recto.adapters.in_memory_deck_repository import InMemoryDeckRepository
from recto.domain.deck import Deck
from recto.domain.knowledge import ORIGINAL, Variant
from recto.tui.app import RectoApp
from recto.tui.variants import VariantsScreen
from tests.container import build_test_container
from tests.fakes.fake_variant_generator import FakeVariantGenerator
from tests.object_mothers.knowledge import KnowledgeMother

REPHRASED = Variant("rephrased", "Quelle ville est la capitale française ?", "Paris")


def setup() -> tuple[RectoApp, InMemoryDeckRepository, FakeVariantGenerator]:
    repository = InMemoryDeckRepository()
    repository.save_deck(
        Deck("geographie", "Géographie", "Capitales"), [KnowledgeMother.new().with_variants(REPHRASED).build()]
    )
    generator = FakeVariantGenerator()
    container = build_test_container(
        deck_repository=providers.Object(repository), variant_generator=providers.Object(generator)
    )

    return RectoApp(container), repository, generator


def variant_ids(repository: InMemoryDeckRepository) -> list[str]:
    knowledge = repository.get_knowledge("geographie", "france")
    assert knowledge is not None
    return [variant.id for variant in knowledge.variants]


async def test_variants_of_a_knowledge_are_listed() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter")

        assert isinstance(app.screen, VariantsScreen)
        assert app.screen.sub_title == "Capitale de la France ?"
        options = app.screen.query_one("#variants", OptionList)
        assert options.option_count == 2
        assert str(options.get_option_at_index(0).prompt).endswith("(original)")


async def test_enter_is_shown_as_the_key_to_the_variants_of_a_card() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c")

        assert app.screen.active_bindings["enter"].binding.description == "Variants"


async def test_edit_and_delete_are_greyed_out_on_the_original() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter")

        bindings = app.screen.active_bindings
        assert not bindings["e"].enabled
        assert not bindings["d"].enabled


async def test_variant_is_deleted_after_confirmation() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "down", "d", "y")

        assert variant_ids(repository) == [ORIGINAL]


async def test_deletion_can_be_cancelled() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "down", "d", "n")

        assert variant_ids(repository) == [ORIGINAL, "rephrased"]


async def test_original_cannot_be_deleted() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "d", "y")

        assert variant_ids(repository) == [ORIGINAL, "rephrased"]


async def test_new_variant_is_written_in_a_form() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "n", *"Capitale ?", "enter", *"Paris", "enter")

        knowledge = repository.get_knowledge("geographie", "france")
        assert knowledge is not None
        assert (knowledge.variants[-1].question, knowledge.variants[-1].answer) == ("Capitale ?", "Paris")


async def test_variant_is_edited_in_a_form() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "down", "e", "enter", *" (75)", "enter")

        knowledge = repository.get_knowledge("geographie", "france")
        assert knowledge is not None
        assert knowledge.variant("rephrased").answer == "Paris (75)"


async def test_enter_edits_the_highlighted_variant() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "down", "enter", "enter", *" (75)", "enter")

        knowledge = repository.get_knowledge("geographie", "france")
        assert knowledge is not None
        assert knowledge.variant("rephrased").answer == "Paris (75)"


async def test_forms_are_titled_after_what_they_do() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "n")
        new_title = app.screen.query_one("#dialog").border_title
        await pilot.press("escape", "down", "e")
        edit_title = app.screen.query_one("#dialog").border_title

        assert (new_title, edit_title) == ("New variant", "Edit variant")


async def test_form_shows_how_to_save_and_cancel() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "n")

        bindings = app.screen.active_bindings
        assert (bindings["enter"].binding.description, bindings["escape"].binding.description) == ("Save", "Cancel")
        assert len(app.screen.query(Footer)) == 1


async def test_confirmation_names_the_variant_and_shows_its_keys() -> None:
    app, _, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "down", "d")

        assert REPHRASED.question in str(app.screen.query_one("#message", Static).content)
        assert len(app.screen.query(Footer)) == 1


async def test_blank_variant_is_refused() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "n", "enter", "enter")

        assert "needs a question and an answer" in str(app.screen.query_one("#status", Static).content)
        assert variant_ids(repository) == [ORIGINAL, "rephrased"]


async def test_variant_is_generated() -> None:
    app, repository, _ = setup()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "g")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert variant_ids(repository) == [ORIGINAL, "rephrased", "france-extra-2"]
        assert app.screen.query_one("#variants", OptionList).option_count == 3


async def test_failed_generation_is_reported() -> None:
    app, repository, generator = setup()
    generator.fails_after(0)

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "g")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert "Generation failed" in str(app.screen.query_one("#status", Static).content)
        assert variant_ids(repository) == [ORIGINAL, "rephrased"]


async def test_variants_cannot_change_while_one_is_generated() -> None:
    app, repository, generator = setup()
    generator.pause()

    async with app.run_test() as pilot:
        await pilot.press("c", "enter", "g", "n")

        assert isinstance(app.screen, VariantsScreen)
        assert not app.screen.active_bindings["n"].enabled

        generator.release()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert variant_ids(repository) == [ORIGINAL, "rephrased", "france-extra-2"]
