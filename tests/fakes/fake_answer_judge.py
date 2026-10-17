from recto.domain.errors import ModelUnavailable
from recto.domain.grading import Grade
from recto.domain.knowledge import Variant
from recto.ports.answer_judge import AnswerJudge


class FakeAnswerJudge(AnswerJudge):
    def __init__(self) -> None:
        self._grades: list[Grade] = []
        self.requests: list[tuple[Variant, str, str]] = []

    def will_grade(self, *grades: Grade) -> None:
        self._grades = list(grades)

    def judge(self, variant: Variant, answer: str, instructions: str) -> Grade:
        self.requests.append((variant, answer, instructions))
        if not self._grades:
            raise ModelUnavailable("the fake judge has no grade left")
        return self._grades.pop(0)
