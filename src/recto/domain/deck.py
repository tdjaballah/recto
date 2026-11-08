from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Deck:
    id: str
    name: str
    description: str
    instructions: str = ""


@dataclass(frozen=True)
class SourceCard:
    id: str
    question: str
    answer: str
    image: str | None = None  # the path written in the deck file, relative to it


@dataclass(frozen=True)
class DeckFile:
    deck: Deck
    cards: tuple[SourceCard, ...]
    directory: Path | None = None  # where the card images are looked for
