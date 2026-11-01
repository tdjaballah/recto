import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from recto.domain.deck import DeckFile
from recto.domain.importing import plan_import
from recto.domain.knowledge import Knowledge
from recto.ports.deck_repository import DeckRepository
from recto.ports.variant_generator import VariantGenerator

type Progress = Callable[[int, int], None]

CONCURRENT_GENERATIONS = 8


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

        generated = asyncio.run(self._generate((*plan.added, *plan.rewritten), deck.instructions, on_progress))

        knowledge = sorted((*plan.kept, *generated), key=lambda item: item.position)
        self._repository.save_deck(deck, knowledge)
        return ImportReport(added=len(plan.added), regenerated=len(plan.rewritten), removed=len(plan.removed))

    async def _generate(
        self, to_generate: Sequence[Knowledge], instructions: str, on_progress: Progress
    ) -> list[Knowledge]:
        slots = asyncio.Semaphore(CONCURRENT_GENERATIONS)
        done = 0

        async def generate(knowledge: Knowledge) -> Knowledge:
            nonlocal done
            async with slots:
                variants = await self._generator.generate(knowledge, instructions)
            done += 1
            on_progress(done, len(to_generate))
            return knowledge.with_variants(*variants)

        return await asyncio.gather(*(generate(knowledge) for knowledge in to_generate))
