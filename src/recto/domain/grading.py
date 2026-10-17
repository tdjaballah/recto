from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Grade:
    score: float
    comment: str


class Rating(Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"


NO_ANSWER = Grade(score=0.0, comment="No answer.")


def rating_for(score: float) -> Rating:
    if score < 0.5:
        return Rating.AGAIN
    if score < 1:
        return Rating.HARD
    return Rating.GOOD
