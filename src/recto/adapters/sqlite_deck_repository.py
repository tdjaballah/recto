import json
import sqlite3
from collections.abc import Generator, Sequence
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from recto.domain.deck import Deck
from recto.domain.grading import Grade, Rating
from recto.domain.knowledge import Knowledge, Variant
from recto.domain.memory import Memory
from recto.domain.review import Review
from recto.ports.deck_repository import DeckRepository

SCHEMA = """
CREATE TABLE IF NOT EXISTS decks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    instructions TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge (
    deck_id TEXT NOT NULL REFERENCES decks (id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    position INTEGER NOT NULL,
    due TEXT,
    introduced_at TEXT,
    fsrs_card TEXT,
    PRIMARY KEY (deck_id, id)
);
CREATE TABLE IF NOT EXISTS variants (
    deck_id TEXT NOT NULL,
    knowledge_id TEXT NOT NULL,
    id TEXT NOT NULL,
    position INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    PRIMARY KEY (deck_id, knowledge_id, id),
    FOREIGN KEY (deck_id, knowledge_id) REFERENCES knowledge (deck_id, id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reviews (
    deck_id TEXT NOT NULL,
    knowledge_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    answer TEXT NOT NULL,
    score REAL NOT NULL,
    comment TEXT NOT NULL,
    rating TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY (deck_id, knowledge_id) REFERENCES knowledge (deck_id, id) ON DELETE CASCADE
);
"""

type KnowledgeRow = tuple[str, str, int, str | None, str | None, str | None]


class SqliteDeckRepository(DeckRepository):
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connection() as conn:
            conn.executescript(SCHEMA)

    def save_deck(self, deck: Deck, knowledge: Sequence[Knowledge]) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO decks VALUES (?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET "
                "name = excluded.name, description = excluded.description, instructions = excluded.instructions",
                (deck.id, deck.name, deck.description, deck.instructions),
            )
            conn.execute(
                "DELETE FROM knowledge WHERE deck_id = ? AND id NOT IN (SELECT value FROM json_each(?))",
                (deck.id, json.dumps([item.id for item in knowledge])),
            )
            for item in knowledge:
                _write_knowledge(conn, item)

    def decks(self) -> list[Deck]:
        with self._connection() as conn:
            rows = conn.execute("SELECT id, name, description, instructions FROM decks ORDER BY name").fetchall()
        return [Deck(*row) for row in rows]

    def deck(self, deck_id: str) -> Deck | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, name, description, instructions FROM decks WHERE id = ?", (deck_id,)
            ).fetchone()
        return Deck(*row) if row else None

    def knowledge(self, deck_id: str) -> list[Knowledge]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT deck_id, id, position, due, introduced_at, fsrs_card FROM knowledge "
                "WHERE deck_id = ? ORDER BY position",
                (deck_id,),
            ).fetchall()
            return [_to_knowledge(conn, row) for row in rows]

    def get_knowledge(self, deck_id: str, knowledge_id: str) -> Knowledge | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT deck_id, id, position, due, introduced_at, fsrs_card FROM knowledge "
                "WHERE deck_id = ? AND id = ?",
                (deck_id, knowledge_id),
            ).fetchone()
            return _to_knowledge(conn, row) if row else None

    def save_knowledge(self, knowledge: Knowledge) -> None:
        with self._connection() as conn:
            _write_knowledge(conn, knowledge)

    def add_review(self, review: Review) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    review.deck_id,
                    review.knowledge_id,
                    review.variant_id,
                    review.answer,
                    review.grade.score,
                    review.grade.comment,
                    review.rating.value,
                    review.reviewed_at.isoformat(),
                ),
            )

    def reviews(self, deck_id: str, knowledge_id: str) -> list[Review]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT deck_id, knowledge_id, variant_id, answer, score, comment, rating, reviewed_at FROM reviews "
                "WHERE deck_id = ? AND knowledge_id = ? ORDER BY reviewed_at",
                (deck_id, knowledge_id),
            ).fetchall()
        return [
            Review(
                deck_id=deck,
                knowledge_id=knowledge,
                variant_id=variant,
                answer=answer,
                grade=Grade(score=score, comment=comment),
                rating=Rating(rating),
                reviewed_at=datetime.fromisoformat(reviewed_at),
            )
            for deck, knowledge, variant, answer, score, comment, rating, reviewed_at in rows
        ]

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            with conn:
                yield conn


def _write_knowledge(conn: sqlite3.Connection, knowledge: Knowledge) -> None:
    memory = knowledge.memory
    conn.execute(
        "INSERT INTO knowledge VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (deck_id, id) DO UPDATE SET "
        "position = excluded.position, due = excluded.due, introduced_at = excluded.introduced_at, "
        "fsrs_card = excluded.fsrs_card",
        (
            knowledge.deck_id,
            knowledge.id,
            knowledge.position,
            memory.due.isoformat() if memory else None,
            memory.introduced_at.isoformat() if memory else None,
            memory.fsrs_card if memory else None,
        ),
    )
    conn.execute("DELETE FROM variants WHERE deck_id = ? AND knowledge_id = ?", (knowledge.deck_id, knowledge.id))
    conn.executemany(
        "INSERT INTO variants VALUES (?, ?, ?, ?, ?, ?)",
        [
            (knowledge.deck_id, knowledge.id, variant.id, position, variant.question, variant.answer)
            for position, variant in enumerate(knowledge.variants)
        ],
    )


def _to_knowledge(conn: sqlite3.Connection, row: KnowledgeRow) -> Knowledge:
    deck_id, knowledge_id, position, due, introduced_at, fsrs_card = row
    variants = conn.execute(
        "SELECT id, question, answer FROM variants WHERE deck_id = ? AND knowledge_id = ? ORDER BY position",
        (deck_id, knowledge_id),
    ).fetchall()
    memory = None
    if due and introduced_at and fsrs_card:
        memory = Memory(
            due=datetime.fromisoformat(due), introduced_at=datetime.fromisoformat(introduced_at), fsrs_card=fsrs_card
        )
    return Knowledge(
        deck_id=deck_id,
        id=knowledge_id,
        position=position,
        variants=tuple(Variant(*variant) for variant in variants),
        memory=memory,
    )
