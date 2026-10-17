import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

from recto.domain.deck import Deck, DeckFile, SourceCard
from recto.domain.errors import InvalidDeck

EXAMPLES = ("anglais", "geographie", "vins", "maths")


def example_decks() -> list[DeckFile]:
    return [parse_deck(name, (files("recto.decks") / f"{name}.toml").read_text(encoding="utf-8")) for name in EXAMPLES]


def read_deck_file(raw_path: str) -> DeckFile:
    try:
        path = Path(raw_path.strip()).expanduser()
        text = path.read_text(encoding="utf-8")
    except (OSError, RuntimeError, ValueError) as error:
        raise InvalidDeck(f"Cannot read {raw_path.strip()}") from error
    return parse_deck(path.stem, text)


def parse_deck(deck_id: str, text: str) -> DeckFile:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise InvalidDeck(f"Invalid TOML: {error}") from error

    header = data.get("deck")
    if not isinstance(header, dict):
        raise InvalidDeck("Missing [deck] table")
    deck = Deck(
        id=deck_id,
        name=_text(header, "name", "[deck]"),
        description=_text(header, "description", "[deck]"),
        instructions=_text(header, "instructions", "[deck]", required=False),
    )

    raw_cards = data.get("cards")
    if not isinstance(raw_cards, list) or not raw_cards:
        raise InvalidDeck("No [[cards]]")
    cards: list[SourceCard] = []
    for number, raw in enumerate(raw_cards, start=1):
        where = f"card {number}"
        if not isinstance(raw, dict):
            raise InvalidDeck(f"{where} is not a table")
        card = SourceCard(
            id=_text(raw, "id", where), question=_text(raw, "question", where), answer=_text(raw, "answer", where)
        )
        if any(card.id == other.id for other in cards):
            raise InvalidDeck(f"Duplicate card id: {card.id}")
        cards.append(card)

    return DeckFile(deck=deck, cards=tuple(cards))


def _text(table: dict[str, Any], key: str, where: str, required: bool = True) -> str:
    value = table.get(key, "")
    if not isinstance(value, str):
        raise InvalidDeck(f"{where}: {key} must be text")
    if required and not value.strip():
        raise InvalidDeck(f"{where}: {key} is missing")
    return value.strip()
