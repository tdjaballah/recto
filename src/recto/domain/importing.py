from collections.abc import Sequence
from dataclasses import dataclass, replace

from recto.domain.deck import SourceCard
from recto.domain.knowledge import Knowledge, new_knowledge


@dataclass(frozen=True)
class ImportPlan:
    kept: tuple[Knowledge, ...]
    added: tuple[Knowledge, ...]
    rewritten: tuple[Knowledge, ...]
    removed: tuple[Knowledge, ...]


def plan_import(deck_id: str, existing: Sequence[Knowledge], cards: Sequence[SourceCard]) -> ImportPlan:
    current = {item.id: item for item in existing}
    kept: list[Knowledge] = []
    added: list[Knowledge] = []
    rewritten: list[Knowledge] = []
    for position, card in enumerate(cards):
        item = current.get(card.id)
        if item is None:
            added.append(new_knowledge(deck_id, card, position))
        elif item.matches(card):
            kept.append(replace(item, position=position))
        else:
            rewritten.append(item.rewritten(card, position))

    card_ids = {card.id for card in cards}
    removed = tuple(item for item in existing if item.id not in card_ids)
    return ImportPlan(kept=tuple(kept), added=tuple(added), rewritten=tuple(rewritten), removed=removed)
