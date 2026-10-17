import pytest
from dependency_injector import providers

from recto.domain.deck import SourceCard
from recto.domain.errors import ModelUnavailable
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.import_deck import ImportDeck, ImportReport
from tests.container import build_test_container
from tests.fakes.fake_variant_generator import FakeVariantGenerator
from tests.object_mothers.deck_file import FRANCE, JAPAN, DeckFileMother


def setup() -> tuple[ImportDeck, DeckRepository, FakeVariantGenerator]:
    generator = FakeVariantGenerator()
    container = build_test_container(variant_generator=providers.Object(generator))

    return container.import_deck(), container.deck_repository(), generator


def test_imported_knowledge_gets_generated_variants() -> None:
    import_deck, repository, generator = setup()

    report = import_deck.execute(DeckFileMother.geography().build())

    assert report == ImportReport(added=2, regenerated=0, removed=0)
    france = repository.get_knowledge("geographie", "france")
    assert france is not None
    assert [variant.id for variant in france.variants] == ["original", "france-1", "france-2", "france-3"]
    assert generator.requests[0][1] == "Réponds en français."


def test_progress_is_reported_after_each_generation() -> None:
    import_deck, _, _ = setup()
    progress: list[tuple[int, int]] = []

    import_deck.execute(
        DeckFileMother.geography().build(), on_progress=lambda done, total: progress.append((done, total))
    )

    assert progress == [(1, 2), (2, 2)]


def test_reimporting_an_unchanged_deck_generates_nothing() -> None:
    import_deck, _, generator = setup()
    import_deck.execute(DeckFileMother.geography().build())

    report = import_deck.execute(DeckFileMother.geography().build())

    assert report == ImportReport(added=0, regenerated=0, removed=0)
    assert len(generator.requests) == 2


def test_reimport_regenerates_changed_cards_and_drops_removed_ones() -> None:
    import_deck, repository, _ = setup()
    import_deck.execute(DeckFileMother.geography().build())
    reworded = SourceCard("france", "Quelle est la capitale de la France ?", "Paris")

    report = import_deck.execute(DeckFileMother.geography().with_cards(reworded).build())

    assert report == ImportReport(added=0, regenerated=1, removed=1)
    assert [item.id for item in repository.knowledge("geographie")] == ["france"]


def test_failed_generation_saves_nothing() -> None:
    import_deck, repository, generator = setup()
    generator.fails_after(1)

    with pytest.raises(ModelUnavailable):
        import_deck.execute(DeckFileMother.geography().with_cards(FRANCE, JAPAN).build())

    assert repository.decks() == []
