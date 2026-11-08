from dataclasses import replace

from recto.domain.deck import SourceCard
from recto.domain.importing import plan_import
from recto.domain.knowledge import Variant
from tests.object_mothers.knowledge import KnowledgeMother

FRANCE = SourceCard("france", "Capitale de la France ?", "Paris")


def test_card_not_in_the_deck_yet_is_added() -> None:
    plan = plan_import("geographie", [], [FRANCE], {})

    assert [item.id for item in plan.added] == ["france"]


def test_unchanged_card_is_kept_as_is() -> None:
    known = KnowledgeMother.due().build()

    plan = plan_import("geographie", [known], [FRANCE], {})

    assert plan.kept == (known,)
    assert plan.added == plan.rewritten == plan.removed == ()


def test_card_with_a_new_wording_is_rewritten() -> None:
    known = KnowledgeMother.due().build()

    plan = plan_import(
        "geographie", [known], [SourceCard("france", "Quelle est la capitale de la France ?", "Paris")], {}
    )

    assert [item.original.question for item in plan.rewritten] == ["Quelle est la capitale de la France ?"]
    assert plan.rewritten[0].memory == known.memory


def test_card_gone_from_the_file_is_removed() -> None:
    known = KnowledgeMother.due().build()

    plan = plan_import("geographie", [known], [SourceCard("japon", "Capitale du Japon ?", "Tokyo")], {})

    assert plan.removed == (known,)


def test_positions_follow_the_file() -> None:
    known = KnowledgeMother.new().at_position(0).build()

    plan = plan_import("geographie", [known], [SourceCard("japon", "Capitale du Japon ?", "Tokyo"), FRANCE], {})

    assert plan.kept[0].position == 1
    assert plan.added[0].position == 0


def test_stored_image_is_given_to_the_knowledge() -> None:
    france = (
        KnowledgeMother.due().with_variants(Variant("r", "Capitale française ?", "Paris")).with_image("a.png").build()
    )
    japan = KnowledgeMother.due().with_id("japon").with_image("japon.png").build()
    cards = [
        FRANCE,
        SourceCard("japon", "Capitale du Japon ?", "Tokyo"),
        SourceCard("coree", "Capitale de la Corée ?", "Séoul"),
    ]

    plan = plan_import("geographie", [france, japan], cards, {"france": "b.png", "coree": "coree.png"})

    assert plan.kept == (replace(france, image="b.png"),)
    assert [(item.id, item.image, item.memory) for item in plan.rewritten] == [("japon", None, japan.memory)]
    assert [(item.id, item.image) for item in plan.added] == [("coree", "coree.png")]
