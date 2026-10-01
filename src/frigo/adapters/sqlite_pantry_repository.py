import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path

from frigo.domain.ingredient import Ingredient
from frigo.ports.pantry_repository import PantryRepository

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingredients (
    name TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    expires_on TEXT
)
"""


class SqlitePantryRepository(PantryRepository):
    def __init__(self, path: Path) -> None:
        self._path = path
        with self._connection() as conn:
            conn.execute(SCHEMA)

    def get(self, name: str) -> Ingredient | None:
        with self._connection() as conn:
            row = conn.execute("SELECT name, quantity, expires_on FROM ingredients WHERE name = ?", (name,)).fetchone()
        return _to_ingredient(row) if row else None

    def save(self, ingredient: Ingredient) -> None:
        expires_on = ingredient.expires_on.isoformat() if ingredient.expires_on else None
        with self._connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ingredients VALUES (?, ?, ?)",
                (ingredient.name, ingredient.quantity, expires_on),
            )

    def remove(self, name: str) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM ingredients WHERE name = ?", (name,))

    def list(self) -> list[Ingredient]:
        with self._connection() as conn:
            rows = conn.execute("SELECT name, quantity, expires_on FROM ingredients").fetchall()
        return [_to_ingredient(row) for row in rows]

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as conn, conn:
            yield conn


def _to_ingredient(row: tuple[str, int, str | None]) -> Ingredient:
    name, quantity, expires_on = row
    return Ingredient(name=name, quantity=quantity, expires_on=date.fromisoformat(expires_on) if expires_on else None)
