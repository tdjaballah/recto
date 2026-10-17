from datetime import timedelta

import pytest

from recto.domain.grading import Rating, rating_for
from recto.domain.memory import remember
from tests.object_mothers.knowledge import NOW


@pytest.mark.parametrize(
    ("score", "rating"),
    [(0.0, Rating.AGAIN), (0.49, Rating.AGAIN), (0.5, Rating.HARD), (0.75, Rating.HARD), (1.0, Rating.GOOD)],
)
def test_score_becomes_a_rating(score: float, rating: Rating) -> None:
    assert rating_for(score) == rating


def test_forgotten_knowledge_comes_back_within_minutes() -> None:
    memory = remember(None, Rating.AGAIN, NOW)

    assert memory.due - NOW < timedelta(minutes=20)


def test_knowledge_known_twice_comes_back_days_later() -> None:
    first = remember(None, Rating.GOOD, NOW)

    second = remember(first, Rating.GOOD, first.due)

    assert second.due - first.due >= timedelta(days=1)


def test_first_review_is_when_the_knowledge_was_introduced() -> None:
    first = remember(None, Rating.GOOD, NOW)

    later = remember(first, Rating.GOOD, NOW + timedelta(days=3))

    assert later.introduced_at == NOW
