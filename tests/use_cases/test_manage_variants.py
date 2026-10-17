import pytest
from dependency_injector import providers

from recto.container import Container
from recto.domain.deck import Deck
from recto.domain.errors import EmptyVariant, KnowledgeNotFound, ModelUnavailable, OriginalIsReadOnly
from recto.domain.knowledge import ORIGINAL, Variant
from recto.ports.deck_repository import DeckRepository
from tests.container import build_test_container
from tests.fakes.fake_variant_generator import FakeVariantGenerator
from tests.object_mothers.knowledge import KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales", "Réponds en français.")
REPHRASED = Variant("rephrased", "Quelle ville est la capitale française ?", "Paris")


def setup() -> tuple[Container, DeckRepository, FakeVariantGenerator]:
    generator = FakeVariantGenerator()
    container = build_test_container(variant_generator=providers.Object(generator))
    repository = container.deck_repository()
    repository.save_deck(GEOGRAPHY, [KnowledgeMother.new().with_variants(REPHRASED).build()])

    return container, repository, generator


def saved_variant_ids(repository: DeckRepository) -> list[str]:
    knowledge = repository.get_knowledge("geographie", "france")
    assert knowledge is not None
    return [variant.id for variant in knowledge.variants]


def test_knowledge_of_a_deck_is_listed() -> None:
    container, _, _ = setup()

    assert [item.id for item in container.list_knowledge().execute("geographie")] == ["france"]


def test_unknown_knowledge_is_not_found() -> None:
    container, _, _ = setup()

    with pytest.raises(KnowledgeNotFound):
        container.get_knowledge().execute("geographie", "japon")


def test_added_variant_is_saved() -> None:
    container, repository, _ = setup()

    knowledge = container.add_variant().execute("geographie", "france", "La France a pour capitale ?", "Paris")

    assert knowledge.variants[-1].question == "La France a pour capitale ?"
    assert len(saved_variant_ids(repository)) == 3


def test_blank_variant_is_refused() -> None:
    container, repository, _ = setup()

    with pytest.raises(EmptyVariant):
        container.add_variant().execute("geographie", "france", "  ", "Paris")

    assert saved_variant_ids(repository) == [ORIGINAL, "rephrased"]


def test_edited_variant_is_saved() -> None:
    container, repository, _ = setup()

    container.edit_variant().execute("geographie", "france", "rephrased", "Capitale française ?", "Paris")

    knowledge = repository.get_knowledge("geographie", "france")
    assert knowledge is not None
    assert knowledge.variant("rephrased").question == "Capitale française ?"


def test_deleted_variant_is_gone() -> None:
    container, repository, _ = setup()

    container.delete_variant().execute("geographie", "france", "rephrased")

    assert saved_variant_ids(repository) == [ORIGINAL]


def test_original_variant_stays_untouched() -> None:
    container, repository, _ = setup()

    with pytest.raises(OriginalIsReadOnly):
        container.delete_variant().execute("geographie", "france", ORIGINAL)

    assert saved_variant_ids(repository) == [ORIGINAL, "rephrased"]


def test_generated_variant_is_added_with_the_deck_instructions() -> None:
    container, repository, generator = setup()

    container.generate_variant().execute("geographie", "france")

    assert saved_variant_ids(repository) == [ORIGINAL, "rephrased", "france-extra-2"]
    assert generator.requests[0][1] == "Réponds en français."


def test_failed_generation_changes_nothing() -> None:
    container, repository, generator = setup()
    generator.fails_after(0)

    with pytest.raises(ModelUnavailable):
        container.generate_variant().execute("geographie", "france")

    assert saved_variant_ids(repository) == [ORIGINAL, "rephrased"]
