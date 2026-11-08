from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.exceptions import AgentRunError, UserError
from pydantic_ai.messages import UserContent
from pydantic_ai.models import Model

from recto.domain.errors import ModelUnavailable
from recto.domain.grading import Grade
from recto.domain.knowledge import Knowledge, Variant, new_variant
from recto.ports.answer_judge import AnswerJudge
from recto.ports.image_store import ImageStore
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

GENERATE_WITH_IMAGE = """\
The card comes with an image that is shown with every variant: the reverse question is null, \
and each rephrasing stays about the image, without describing it or giving the answer away."""

GENERATE_ONE_WITH_IMAGE = """\
The card comes with an image that is shown with the variant: it stays about the image, \
without describing it or giving the answer away."""

JUDGE_WITH_IMAGE = "The question comes with an image, which the learner saw."


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
    def __init__(self, model: Model, images: ImageStore) -> None:
        self._variants = Agent(model, output_type=_Variants, instructions=GENERATE)
        self._one = Agent(model, output_type=_Pair, instructions=GENERATE_ONE)
        self._images = images

    async def generate(self, knowledge: Knowledge, instructions: str) -> list[Variant]:
        prompt = _with_image(self._images, _card(knowledge, instructions), knowledge.image)
        output = await _run(self._variants, prompt, GENERATE_WITH_IMAGE)
        # Shown with the card's image, the reverse question would give its answer away.
        reverse = None if knowledge.image else output.reverse
        pairs = [reverse, *output.rephrasings] if reverse else output.rephrasings
        return [new_variant(pair.question, pair.answer) for pair in pairs]

    async def generate_one(self, knowledge: Knowledge, instructions: str) -> Variant:
        existing = "\n".join(f"- {v.question} -> {v.answer}" for v in knowledge.variants)
        text = f"{_card(knowledge, instructions)}\nExisting variants:\n{existing}"
        pair = await _run(self._one, _with_image(self._images, text, knowledge.image), GENERATE_ONE_WITH_IMAGE)
        return new_variant(pair.question, pair.answer)


class PydanticAIAnswerJudge(AnswerJudge):
    def __init__(self, model: Model, images: ImageStore) -> None:
        self._agent = Agent(model, output_type=_Grade, instructions=JUDGE)
        self._images = images

    def judge(self, variant: Variant, answer: str, instructions: str, image: str | None) -> Grade:
        prompt = (
            f"Deck instructions: {instructions or 'none'}\n"
            f"Question: {variant.question}\n"
            f"Reference answer: {variant.answer}\n"
            f"Learner's answer: {answer}"
        )
        output = _run_sync(self._agent, _with_image(self._images, prompt, image), JUDGE_WITH_IMAGE)
        return Grade(score=output.score, comment=output.comment)


def _card(knowledge: Knowledge, instructions: str) -> str:
    return (
        f"Deck instructions: {instructions or 'none'}\n"
        f"Question: {knowledge.original.question}\n"
        f"Answer: {knowledge.original.answer}"
    )


def _with_image(images: ImageStore, text: str, image: str | None) -> str | list[UserContent]:
    """The text alone when there is no image or it cannot be read, so text-only cards are sent as they always were."""
    if image is None:
        return text
    try:
        return [text, BinaryContent.from_path(images.path(image))]
    except OSError:
        return text


def _about_image(prompt: str | list[UserContent], instructions: str) -> str | None:
    return instructions if isinstance(prompt, list) else None


async def _run[T](agent: Agent[None, T], prompt: str | list[UserContent], about_image: str) -> T:
    try:
        return (await agent.run(prompt, instructions=_about_image(prompt, about_image))).output
    except (AgentRunError, UserError) as error:
        raise ModelUnavailable(str(error)) from error


def _run_sync[T](agent: Agent[None, T], prompt: str | list[UserContent], about_image: str) -> T:
    try:
        return agent.run_sync(prompt, instructions=_about_image(prompt, about_image)).output
    except (AgentRunError, UserError) as error:
        raise ModelUnavailable(str(error)) from error
