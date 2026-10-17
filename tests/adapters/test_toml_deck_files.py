from pathlib import Path

import pytest

from recto.adapters.toml_deck_files import example_decks, parse_deck, read_deck_file
from recto.domain.deck import Deck, SourceCard
from recto.domain.errors import InvalidDeck

VALID = """
[deck]
name = "Géographie"
description = "Capitales"
instructions = "Réponds en français."

[[cards]]
id = "france"
question = "Capitale de la France ?"
answer = " Paris "
"""


def test_deck_file_is_read() -> None:
    deck_file = parse_deck("geographie", VALID)

    assert deck_file.deck == Deck("geographie", "Géographie", "Capitales", "Réponds en français.")
    assert deck_file.cards == (SourceCard("france", "Capitale de la France ?", "Paris"),)


def test_instructions_are_optional() -> None:
    deck_file = parse_deck("geographie", VALID.replace('instructions = "Réponds en français."', ""))

    assert deck_file.deck.instructions == ""


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("name = ", "Invalid TOML"),
        ('[[cards]]\nid = "a"\nquestion = "Q"\nanswer = "A"', "Missing [deck] table"),
        ('[deck]\nname = "N"\ndescription = "D"', "No [[cards]]"),
        (VALID.replace('name = "Géographie"', ""), "[deck]: name is missing"),
        (VALID.replace('answer = " Paris "', 'answer = "  "'), "card 1: answer is missing"),
        (VALID.replace('answer = " Paris "', "answer = 42"), "card 1: answer must be text"),
        (VALID + '\n[[cards]]\nid = "france"\nquestion = "Q"\nanswer = "A"', "Duplicate card id: france"),
    ],
)
def test_invalid_deck_file_is_rejected_with_the_reason(text: str, message: str) -> None:
    with pytest.raises(InvalidDeck, match=message.replace("[", r"\[").replace("]", r"\]")):
        parse_deck("geographie", text)


def test_deck_id_is_the_file_name(tmp_path: Path) -> None:
    (tmp_path / "espagnol.toml").write_text(VALID, encoding="utf-8")

    assert read_deck_file(f"  {tmp_path / 'espagnol.toml'} ").deck.id == "espagnol"


def test_missing_file_is_an_invalid_deck(tmp_path: Path) -> None:
    with pytest.raises(InvalidDeck, match="Cannot read"):
        read_deck_file(str(tmp_path / "nope.toml"))


@pytest.mark.parametrize("raw_path", ["~no-such-user-recto/deck.toml", "deck\0.toml"])
def test_unusable_path_is_an_invalid_deck(raw_path: str) -> None:
    with pytest.raises(InvalidDeck, match="Cannot read"):
        read_deck_file(raw_path)


def test_example_decks_hold_fifty_cards_each() -> None:
    decks = example_decks()

    assert [deck_file.deck.id for deck_file in decks] == ["anglais", "geographie", "vins", "maths"]
    assert all(len(deck_file.cards) == 50 for deck_file in decks)
