from dataclasses import replace
from typing import Self

from recto.domain.deck import Deck, DeckFile, SourceCard

FRANCE = SourceCard("france", "Capitale de la France ?", "Paris")
JAPAN = SourceCard("japon", "Capitale du Japon ?", "Tokyo")


class DeckFileMother:
    _deck_file: DeckFile

    def __init__(self) -> None:
        raise TypeError("Use a named factory such as DeckFileMother.geography()")

    @classmethod
    def _of(cls, deck_file: DeckFile) -> Self:
        mother = cls.__new__(cls)
        mother._deck_file = deck_file
        return mother

    @classmethod
    def geography(cls) -> Self:
        deck = Deck("geographie", "Géographie", "Capitales et pays", "Réponds en français.")
        return cls._of(DeckFile(deck=deck, cards=(FRANCE, JAPAN)))

    def with_cards(self, *cards: SourceCard) -> Self:
        self._deck_file = replace(self._deck_file, cards=cards)
        return self

    def build(self) -> DeckFile:
        return replace(self._deck_file)
