from abc import ABC, abstractmethod

from recto.domain.grading import Grade
from recto.domain.knowledge import Variant


class AnswerJudge(ABC):
    @abstractmethod
    def judge(self, variant: Variant, answer: str, instructions: str) -> Grade: ...
