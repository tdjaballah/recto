from abc import ABC, abstractmethod
from pathlib import Path


class ImageStore(ABC):
    @abstractmethod
    def store(self, directory: Path, declared: str) -> str:
        """Copy the image a deck file declares, relative to its folder; the name of the copy, or InvalidDeck."""

    @abstractmethod
    def path(self, name: str) -> Path:
        """Where the copy stored under that name is."""
