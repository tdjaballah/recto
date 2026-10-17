from dataclasses import dataclass
from datetime import datetime

from recto.domain.grading import Grade, Rating


@dataclass(frozen=True)
class Review:
    deck_id: str
    knowledge_id: str
    variant_id: str
    answer: str
    grade: Grade
    rating: Rating
    reviewed_at: datetime
