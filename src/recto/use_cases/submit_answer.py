from dataclasses import replace

from recto.domain.errors import DeckNotFound, KnowledgeNotFound
from recto.domain.grading import NO_ANSWER, Grade, rating_for
from recto.domain.memory import remember
from recto.domain.review import Review
from recto.ports.answer_judge import AnswerJudge
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository


class SubmitAnswer:
    def __init__(self, repository: DeckRepository, judge: AnswerJudge, clock: Clock) -> None:
        self._repository = repository
        self._judge = judge
        self._clock = clock

    def execute(self, deck_id: str, knowledge_id: str, variant_id: str, answer: str) -> Grade:
        deck = self._repository.deck(deck_id)
        if deck is None:
            raise DeckNotFound(deck_id)
        knowledge = self._repository.get_knowledge(deck_id, knowledge_id)
        if knowledge is None:
            raise KnowledgeNotFound(knowledge_id)
        variant = knowledge.variant(variant_id)

        answer = answer.strip()
        grade = self._judge.judge(variant, answer, deck.instructions) if answer else NO_ANSWER
        rating = rating_for(grade.score)
        now = self._clock.now()

        self._repository.save_knowledge(replace(knowledge, memory=remember(knowledge.memory, rating, now)))
        self._repository.add_review(
            Review(
                deck_id=deck_id,
                knowledge_id=knowledge_id,
                variant_id=variant_id,
                answer=answer,
                grade=grade,
                rating=rating,
                reviewed_at=now,
            )
        )
        return grade
