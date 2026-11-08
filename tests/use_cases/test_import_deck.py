from dataclasses import replace
from pathlib import Path

import pytest
from dependency_injector import providers

from recto.domain.deck import DeckFile, SourceCard
from recto.domain.errors import InvalidDeck, ModelUnavailable
from recto.ports.deck_repository import DeckRepository
from recto.use_cases.import_deck import CONCURRENT_GENERATIONS, ImportDeck, ImportReport
from tests.container import build_test_container
from tests.fakes.fake_image_store import FakeImageStore
from tests.fakes.fake_variant_generator import FakeVariantGenerator
from tests.object_mothers.deck_file import FRANCE, JAPAN, DeckFileMother
from tests.object_mothers.knowledge import KnowledgeMother

DECK_FOLDER = Path("/decks")


def setup(images: FakeImageStore | None = None) -> tuple[ImportDeck, DeckRepository, FakeVariantGenerator]:
    generator = FakeVariantGenerator()
    container = build_test_container(
        variant_generator=providers.Object(generator), image_store=providers.Object(images or FakeImageStore())
    )

    return container.import_deck(), container.deck_repository(), generator


def with_france_image(image: str | None, *cards: SourceCard) -> DeckFile:
    france = replace(FRANCE, image=image)
    return DeckFileMother.geography().in_directory(DECK_FOLDER).with_cards(france, *(cards or (JAPAN,))).build()


def image_of(repository: DeckRepository, knowledge_id: str) -> str | None:
    knowledge = repository.get_knowledge("geographie", knowledge_id)
    assert knowledge is not None
    return knowledge.image


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


def test_variants_are_generated_concurrently_up_to_a_limit() -> None:
    import_deck, repository, generator = setup()
    cards = [SourceCard(f"card-{n}", f"Question {n} ?", f"Réponse {n}") for n in range(CONCURRENT_GENERATIONS * 2)]

    import_deck.execute(DeckFileMother.geography().with_cards(*cards).build())

    assert generator.most_concurrent == CONCURRENT_GENERATIONS
    assert [item.id for item in repository.knowledge("geographie")] == [card.id for card in cards]


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


def test_card_images_are_stored_and_referenced() -> None:
    images = FakeImageStore()
    import_deck, repository, _ = setup(images)

    import_deck.execute(with_france_image("images/france.png"))

    assert images.requests == [(DECK_FOLDER, "images/france.png")]
    assert image_of(repository, "france") == "stored-images/france.png"
    assert image_of(repository, "japon") is None


def test_reimport_regenerates_a_card_whose_image_changed_and_keeps_its_progress() -> None:
    import_deck, repository, generator = setup()
    import_deck.execute(with_france_image("images/france.png"))
    france = repository.get_knowledge("geographie", "france")
    assert france is not None
    repository.save_knowledge(replace(france, memory=KnowledgeMother.due().build().memory))
    progressed = repository.get_knowledge("geographie", "france")
    assert progressed is not None

    for image, stored in (("images/france-2.png", "stored-images/france-2.png"), (None, None)):
        report = import_deck.execute(with_france_image(image))

        assert report == ImportReport(added=0, regenerated=1, removed=0)
        france = repository.get_knowledge("geographie", "france")
        assert france is not None
        assert (france.image, france.memory) == (stored, progressed.memory)
        assert generator.requests[-1][0].image == stored
    assert len(generator.requests) == 4


def test_unusable_image_saves_nothing_and_asks_no_model() -> None:
    images = FakeImageStore()
    import_deck, repository, generator = setup(images)
    import_deck.execute(with_france_image("images/france.png"))
    images.rejects("images/broken.png")

    with pytest.raises(InvalidDeck, match=r"Image images/broken\.png: not found"):
        import_deck.execute(with_france_image("images/france.png", SourceCard("japon", "Q", "A", "images/broken.png")))

    assert image_of(repository, "france") == "stored-images/france.png"
    assert image_of(repository, "japon") is None
    assert len(generator.requests) == 2


def test_failed_generation_keeps_the_previous_image() -> None:
    import_deck, repository, generator = setup()
    import_deck.execute(with_france_image("images/france.png"))
    generator.fails_after(len(generator.requests))

    with pytest.raises(ModelUnavailable):
        import_deck.execute(with_france_image("images/france-2.png", replace(JAPAN, question="Capitale nippone ?")))

    assert image_of(repository, "france") == "stored-images/france.png"


def test_image_needs_a_deck_folder() -> None:
    import_deck, repository, _ = setup()
    deck_file = DeckFileMother.geography().with_cards(replace(FRANCE, image="images/france.png")).build()

    with pytest.raises(InvalidDeck, match=r"Image images/france\.png: no deck folder to find it in"):
        import_deck.execute(deck_file)

    assert repository.decks() == []
