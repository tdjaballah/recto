from collections.abc import Callable
from dataclasses import dataclass

from recto.domain.deck import DeckFile
from recto.domain.importing import plan_import
from recto.domain.knowledge import Knowledge
from recto.ports.deck_repository import DeckRepository
from recto.ports.variant_generator import VariantGenerator

type Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class ImportReport:
    added: int
    regenerated: int
    removed: int


def _ignore(done: int, total: int) -> None:
    pass


class ImportDeck:
    def __init__(self, repository: DeckRepository, generator: VariantGenerator) -> None:
        self._repository = repository
        self._generator = generator

    def execute(self, deck_file: DeckFile, on_progress: Progress = _ignore) -> ImportReport:
        deck = deck_file.deck
        plan = plan_import(deck.id, self._repository.knowledge(deck.id), deck_file.cards)

        to_generate = (*plan.added, *plan.rewritten)
        generated: list[Knowledge] = []
        for done, knowledge in enumerate(to_generate, start=1):
            generated.append(knowledge.with_variants(*self._generator.generate(knowledge, deck.instructions)))
            on_progress(done, len(to_generate))

        knowledge = sorted((*plan.kept, *generated), key=lambda item: item.position)
        self._repository.save_deck(deck, knowledge)
        return ImportReport(added=len(plan.added), regenerated=len(plan.rewritten), removed=len(plan.removed))
