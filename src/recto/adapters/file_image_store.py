import hashlib
import os
import tempfile
from pathlib import Path

from recto.domain.errors import InvalidDeck
from recto.ports.image_store import ImageStore

MAX_IMAGE_SIZE = 5 * 1024 * 1024
_EXTENSIONS = {b"\x89PNG\r\n\x1a\n": ".png", b"\xff\xd8\xff": ".jpg"}


class FileImageStore(ImageStore):
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def store(self, directory: Path, declared: str) -> str:
        data = _read(directory, declared)
        extension = next((ext for signature, ext in _EXTENSIONS.items() if data.startswith(signature)), None)
        if extension is None:
            raise InvalidDeck(f"Image {declared}: not a PNG or JPEG")

        name = hashlib.sha256(data).hexdigest() + extension
        target = self._directory / name
        if not target.exists():
            self._directory.mkdir(parents=True, exist_ok=True)
            handle, partial = tempfile.mkstemp(dir=self._directory, suffix=".part")
            with os.fdopen(handle, "wb") as file:
                file.write(data)
            os.replace(partial, target)
        return name

    def path(self, name: str) -> Path:
        return self._directory / name


def _read(directory: Path, declared: str) -> bytes:
    try:
        path = (directory / declared).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise InvalidDeck(f"Image {declared}: outside the deck's folder")
        if not path.is_file():
            raise InvalidDeck(f"Image {declared}: not found")
        if path.stat().st_size > MAX_IMAGE_SIZE:
            raise InvalidDeck(f"Image {declared}: larger than {MAX_IMAGE_SIZE // 2**20} MB")
        return path.read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise InvalidDeck(f"Image {declared}: cannot be read") from error
