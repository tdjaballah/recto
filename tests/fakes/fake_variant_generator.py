import threading

from recto.domain.errors import ModelUnavailable
from recto.domain.knowledge import Knowledge, Variant
from recto.ports.variant_generator import VariantGenerator


class FakeVariantGenerator(VariantGenerator):
    def __init__(self) -> None:
        self.requests: list[tuple[Knowledge, str]] = []
        self._calls_before_failing: int | None = None
        self._running = threading.Event()
        self._running.set()

    def pause(self) -> None:
        self._running.clear()

    def release(self) -> None:
        self._running.set()

    def fails_after(self, calls: int) -> None:
        self._calls_before_failing = calls

    def generate(self, knowledge: Knowledge, instructions: str) -> list[Variant]:
        self._call(knowledge, instructions)
        question = knowledge.original.question
        return [
            Variant(id=f"{knowledge.id}-{n}", question=f"{question} ({n})", answer=knowledge.original.answer)
            for n in range(1, 4)
        ]

    def generate_one(self, knowledge: Knowledge, instructions: str) -> Variant:
        self._call(knowledge, instructions)
        n = len(knowledge.variants)
        return Variant(
            id=f"{knowledge.id}-extra-{n}",
            question=f"{knowledge.original.question} (extra {n})",
            answer=knowledge.original.answer,
        )

    def _call(self, knowledge: Knowledge, instructions: str) -> None:
        self._running.wait(timeout=5)
        if self._calls_before_failing is not None and len(self.requests) >= self._calls_before_failing:
            raise ModelUnavailable("the fake generator is down")
        self.requests.append((knowledge, instructions))
