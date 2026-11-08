from pathlib import Path

from recto.domain.errors import InvalidDeck
from recto.ports.image_store import ImageStore


class FakeImageStore(ImageStore):
    def __init__(self) -> None:
        self.requests: list[tuple[Path, str]] = []
        self._rejected: set[str] = set()

    def rejects(self, declared: str) -> None:
        self._rejected.add(declared)

    def store(self, directory: Path, declared: str) -> str:
        self.requests.append((directory, declared))
        if declared in self._rejected:
            raise InvalidDeck(f"Image {declared}: not found")
        return f"stored-{declared}"
