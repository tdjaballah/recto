import hashlib
import re
from pathlib import Path

import pytest

from recto.adapters.file_image_store import MAX_IMAGE_SIZE, FileImageStore
from recto.domain.errors import InvalidDeck

PNG = b"\x89PNG\r\n\x1a\n" + b"a red square"
JPEG = b"\xff\xd8\xff\xe0" + b"a blue square"


def setup(tmp_path: Path) -> tuple[FileImageStore, Path, Path]:
    deck = tmp_path / "decks" / "geographie"
    (deck / "images").mkdir(parents=True)
    images = tmp_path / "data" / "images"
    return FileImageStore(images), deck, images


def stored(images: Path) -> list[str]:
    return sorted(path.name for path in images.glob("*"))


def test_png_is_stored_under_the_hash_of_its_content(tmp_path: Path) -> None:
    store, deck, images = setup(tmp_path)
    (deck / "images" / "france.png").write_bytes(PNG)

    name = store.store(deck, "images/france.png")

    assert name == hashlib.sha256(PNG).hexdigest() + ".png"
    assert (images / name).read_bytes() == PNG
    assert stored(images) == [name]


def test_jpeg_is_stored_as_jpg(tmp_path: Path) -> None:
    store, deck, _ = setup(tmp_path)
    (deck / "france.jpeg").write_bytes(JPEG)

    assert store.store(deck, "france.jpeg") == hashlib.sha256(JPEG).hexdigest() + ".jpg"


def test_format_comes_from_the_bytes_not_the_extension(tmp_path: Path) -> None:
    store, deck, _ = setup(tmp_path)
    (deck / "images" / "photo.JPEG").write_bytes(PNG)

    assert store.store(deck, "images/photo.JPEG").endswith(".png")


def test_storing_an_image_again_gives_the_same_name(tmp_path: Path) -> None:
    store, deck, images = setup(tmp_path)
    (deck / "images" / "france.png").write_bytes(PNG)
    (deck / "copy.png").write_bytes(PNG)

    names = {
        store.store(deck, "images/france.png"),
        store.store(deck, "images/france.png"),
        store.store(deck, "copy.png"),
    }

    assert len(names) == 1
    assert stored(images) == list(names)


def test_same_path_in_two_decks_does_not_collide(tmp_path: Path) -> None:
    store, geography, images = setup(tmp_path)
    wines = tmp_path / "decks" / "vins"
    (wines / "images").mkdir(parents=True)
    (geography / "images" / "a.png").write_bytes(PNG)
    (wines / "images" / "a.png").write_bytes(PNG + b" with a border")

    first = store.store(geography, "images/a.png")
    second = store.store(wines, "images/a.png")

    assert first != second
    assert (images / first).read_bytes() == PNG
    assert (images / second).read_bytes() == PNG + b" with a border"


@pytest.mark.parametrize(
    ("declared", "reason"),
    [
        ("images/missing.png", "not found"),
        ("images", "not found"),
        ("../outside.png", "outside the deck's folder"),
        ("{outside}", "outside the deck's folder"),
        ("images/link.png", "outside the deck's folder"),
        ("images/france.gif", "not a PNG or JPEG"),
        ("images/empty.png", "not a PNG or JPEG"),
        ("images/huge.png", "larger than 5 MB"),
        ("images/locked.png", "cannot be read"),
        ("images/a\0.png", "cannot be read"),
    ],
)
def test_unusable_image_is_rejected_with_the_reason(tmp_path: Path, declared: str, reason: str) -> None:
    store, deck, images = setup(tmp_path)
    outside = tmp_path / "decks" / "outside.png"
    outside.write_bytes(PNG)
    (deck / "images" / "link.png").symlink_to(outside)
    (deck / "images" / "france.gif").write_bytes(b"GIF89a")
    (deck / "images" / "empty.png").write_bytes(b"")
    with (deck / "images" / "huge.png").open("wb") as huge:
        huge.write(PNG)
        huge.truncate(MAX_IMAGE_SIZE + 1)
    (deck / "images" / "locked.png").write_bytes(PNG)
    (deck / "images" / "locked.png").chmod(0)
    declared = declared.format(outside=outside)

    with pytest.raises(InvalidDeck, match=f"^Image {re.escape(declared)}: {reason}$"):
        store.store(deck, declared)
    assert stored(images) == []
