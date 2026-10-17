from dataclasses import replace
from pathlib import Path

from recto.adapters.sqlite_deck_repository import SqliteDeckRepository
from recto.domain.deck import Deck
from recto.domain.grading import Grade, Rating
from recto.domain.knowledge import Variant
from recto.domain.review import Review
from tests.object_mothers.knowledge import NOW, KnowledgeMother

GEOGRAPHY = Deck("geographie", "Géographie", "Capitales", "Réponds en français.")
REPHRASED = Variant("rephrased", "Quelle ville est la capitale française ?", "Paris")


def setup(tmp_path: Path) -> SqliteDeckRepository:
    return SqliteDeckRepository(tmp_path / "data" / "recto.db")


def review_of(knowledge_id: str) -> Review:
    return Review("geographie", knowledge_id, "original", "Paris", Grade(1.0, "Exact."), Rating.GOOD, NOW)


def test_saved_deck_is_found_with_its_knowledge(tmp_path: Path) -> None:
    repository = setup(tmp_path)
    france = KnowledgeMother.due().with_variants(REPHRASED).build()
    japan = KnowledgeMother.new().with_id("japon").at_position(1).build()

    repository.save_deck(GEOGRAPHY, [france, japan])

    assert repository.decks() == [GEOGRAPHY]
    assert repository.deck("geographie") == GEOGRAPHY
    assert repository.knowledge("geographie") == [france, japan]
    assert repository.get_knowledge("geographie", "japon") == japan


def test_unknown_deck_and_knowledge_are_not_found(tmp_path: Path) -> None:
    repository = setup(tmp_path)

    assert repository.deck("geographie") is None
    assert repository.get_knowledge("geographie", "france") is None
    assert repository.knowledge("geographie") == []


def test_saved_knowledge_replaces_its_variants_and_memory(tmp_path: Path) -> None:
    repository = setup(tmp_path)
    france = KnowledgeMother.new().with_variants(REPHRASED).build()
    repository.save_deck(GEOGRAPHY, [france])
    changed = replace(KnowledgeMother.due().build(), variants=(france.original,))

    repository.save_knowledge(changed)

    assert repository.get_knowledge("geographie", "france") == changed


def test_saving_the_deck_again_keeps_the_reviews_of_the_knowledge_it_keeps(tmp_path: Path) -> None:
    repository = setup(tmp_path)
    france = KnowledgeMother.due().build()
    repository.save_deck(GEOGRAPHY, [france])
    repository.add_review(review_of("france"))

    repository.save_deck(GEOGRAPHY, [replace(france, variants=(france.original, REPHRASED))])

    assert repository.reviews("geographie", "france") == [review_of("france")]


def test_knowledge_left_out_of_the_deck_is_deleted_with_its_reviews(tmp_path: Path) -> None:
    repository = setup(tmp_path)
    france = KnowledgeMother.due().build()
    japan = KnowledgeMother.new().with_id("japon").at_position(1).build()
    repository.save_deck(GEOGRAPHY, [france, japan])
    repository.add_review(review_of("france"))

    repository.save_deck(replace(GEOGRAPHY, name="Géo"), [japan])

    assert repository.knowledge("geographie") == [japan]
    assert repository.reviews("geographie", "france") == []
    assert repository.decks()[0].name == "Géo"


def test_decks_are_sorted_by_name(tmp_path: Path) -> None:
    repository = setup(tmp_path)
    wines = Deck("vins", "Vins", "Cépages")

    repository.save_deck(wines, [])
    repository.save_deck(GEOGRAPHY, [])

    assert [deck.id for deck in repository.decks()] == ["geographie", "vins"]
