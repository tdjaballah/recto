from abc import ABC, abstractmethod

from recto.domain.knowledge import Knowledge, Variant


class VariantGenerator(ABC):
    @abstractmethod
    def generate(self, knowledge: Knowledge, instructions: str) -> list[Variant]:
        """The reverse question when it makes sense, plus 3 rephrasings of the original."""

    @abstractmethod
    def generate_one(self, knowledge: Knowledge, instructions: str) -> Variant:
        """One more rephrasing, different from the knowledge's current variants."""
