from dataclasses import dataclass


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


@dataclass(frozen=True)
class DeckFile:
    deck: Deck
    cards: tuple[SourceCard, ...]
