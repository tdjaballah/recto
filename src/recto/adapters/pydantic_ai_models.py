from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, UserError

from recto.domain.errors import ModelUnavailable
from recto.domain.grading import Grade
from recto.domain.knowledge import Knowledge, Variant, new_variant
from recto.ports.answer_judge import AnswerJudge
from recto.ports.variant_generator import VariantGenerator

GENERATE = """\
You write variants of a flashcard so that a learner memorizes the knowledge, not one wording.
Give the reverse question, asking for what the original question was about given its answer, \
only when it has a single clear answer; otherwise null.
Give exactly 3 rephrasings of the original question that expect the same answer, each worded differently.
Keep the language of the card and follow the deck instructions."""

GENERATE_ONE = """\
You write one new variant of a flashcard so that a learner memorizes the knowledge, not one wording.
Rephrase the original question so that it expects the same answer, worded differently from every existing variant.
Keep the language of the card and follow the deck instructions."""

JUDGE = """\
You grade a learner's typed answer to a flashcard against the reference answer.
Judge the meaning, not the wording: spelling mistakes, synonyms and equivalent notations are fine.
When the reference answer holds several notions, the score is the share the learner got right \
(1 notion out of 4 is 0.25). Score 1 only when nothing is missing or wrong.
The comment is one or two short sentences, in the language of the question, \
saying what was missing or wrong, or confirming the answer.
Follow the deck instructions."""


class _Pair(BaseModel):
    question: str = Field(pattern=r"\S")
    answer: str = Field(pattern=r"\S")


class _Variants(BaseModel):
    reverse: _Pair | None
    rephrasings: list[_Pair] = Field(min_length=3, max_length=3)


class _Grade(BaseModel):
    score: float = Field(ge=0, le=1)
    comment: str


class PydanticAIVariantGenerator(VariantGenerator):
    def __init__(self, model: str) -> None:
        self._variants = Agent(model, output_type=_Variants, instructions=GENERATE, defer_model_check=True)
        self._one = Agent(model, output_type=_Pair, instructions=GENERATE_ONE, defer_model_check=True)

    def generate(self, knowledge: Knowledge, instructions: str) -> list[Variant]:
        output = _run(self._variants, _card(knowledge, instructions))
        pairs = [output.reverse, *output.rephrasings] if output.reverse else output.rephrasings
        return [new_variant(pair.question, pair.answer) for pair in pairs]

    def generate_one(self, knowledge: Knowledge, instructions: str) -> Variant:
        existing = "\n".join(f"- {v.question} -> {v.answer}" for v in knowledge.variants)
        pair = _run(self._one, f"{_card(knowledge, instructions)}\nExisting variants:\n{existing}")
        return new_variant(pair.question, pair.answer)


class PydanticAIAnswerJudge(AnswerJudge):
    def __init__(self, model: str) -> None:
        self._agent = Agent(model, output_type=_Grade, instructions=JUDGE, defer_model_check=True)

    def judge(self, variant: Variant, answer: str, instructions: str) -> Grade:
        prompt = (
            f"Deck instructions: {instructions or 'none'}\n"
            f"Question: {variant.question}\n"
            f"Reference answer: {variant.answer}\n"
            f"Learner's answer: {answer}"
        )
        output = _run(self._agent, prompt)
        return Grade(score=output.score, comment=output.comment)


def _card(knowledge: Knowledge, instructions: str) -> str:
    return (
        f"Deck instructions: {instructions or 'none'}\n"
        f"Question: {knowledge.original.question}\n"
        f"Answer: {knowledge.original.answer}"
    )


def _run[T](agent: Agent[None, T], prompt: str) -> T:
    try:
        return agent.run_sync(prompt).output
    except (AgentRunError, UserError) as error:
        raise ModelUnavailable(str(error)) from error
