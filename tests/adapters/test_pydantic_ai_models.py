from pathlib import Path
from typing import Any

import pytest
from pydantic_ai import BinaryContent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from recto.adapters.file_image_store import FileImageStore
from recto.adapters.pydantic_ai_models import (
    GENERATE,
    GENERATE_ONE,
    JUDGE,
    PydanticAIAnswerJudge,
    PydanticAIVariantGenerator,
)
from recto.domain.grading import Grade
from tests.object_mothers.knowledge import KnowledgeMother

PNG = b"\x89PNG\r\n\x1a\n" + b"a red square"
JPEG = b"\xff\xd8\xff\xe0" + b"a blue square"
CARD = "Deck instructions: Réponds en français.\nQuestion: Capitale de la France ?\nAnswer: Paris"
VARIANTS = {
    "reverse": {"question": "Paris est la capitale de quel pays ?", "answer": "La France"},
    "rephrasings": [{"question": f"Capitale française {n} ?", "answer": "Paris"} for n in range(1, 4)],
}
REPHRASINGS = ["Capitale française 1 ?", "Capitale française 2 ?", "Capitale française 3 ?"]


class RecordingModel:
    """Answers every request with the same output, through the output tool, and keeps what it was sent."""

    def __init__(self, output: dict[str, Any]) -> None:
        self.prompts: list[Any] = []
        self.instructions: list[str | None] = []
        self.model = FunctionModel(self._answer)
        self._output = output

    def _answer(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        request = messages[-1]
        assert isinstance(request, ModelRequest)
        self.prompts += [part.content for part in request.parts if isinstance(part, UserPromptPart)]
        self.instructions.append(info.instructions)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, self._output)])


def stored(tmp_path: Path, content: bytes = PNG) -> tuple[FileImageStore, str]:
    (tmp_path / "france.img").write_bytes(content)
    images = FileImageStore(tmp_path / "images")
    return images, images.store(tmp_path, "france.img")


async def test_text_only_card_is_sent_as_before(tmp_path: Path) -> None:
    model = RecordingModel(VARIANTS)
    generator = PydanticAIVariantGenerator(model.model, FileImageStore(tmp_path))

    variants = await generator.generate(KnowledgeMother.new().build(), "Réponds en français.")

    assert model.prompts == [CARD]
    assert model.instructions == [GENERATE]
    assert [variant.question for variant in variants] == ["Paris est la capitale de quel pays ?", *REPHRASINGS]


@pytest.mark.parametrize(("content", "media_type"), [(PNG, "image/png"), (JPEG, "image/jpeg")])
async def test_card_image_is_sent_with_its_media_type(tmp_path: Path, content: bytes, media_type: str) -> None:
    images, name = stored(tmp_path, content)
    model = RecordingModel(VARIANTS)
    generator = PydanticAIVariantGenerator(model.model, images)

    await generator.generate(KnowledgeMother.new().with_image(name).build(), "Réponds en français.")

    [(text, image)] = model.prompts
    assert text == CARD
    assert isinstance(image, BinaryContent)
    assert (image.data, image.media_type) == (content, media_type)
    [instructions] = model.instructions
    assert instructions is not None
    assert instructions.startswith(GENERATE)
    assert "image" in instructions.removeprefix(GENERATE)


async def test_card_with_an_image_gets_no_reverse_variant(tmp_path: Path) -> None:
    images, name = stored(tmp_path)
    generator = PydanticAIVariantGenerator(RecordingModel(VARIANTS).model, images)

    variants = await generator.generate(KnowledgeMother.new().with_image(name).build(), "")

    assert [variant.question for variant in variants] == REPHRASINGS


async def test_one_more_variant_is_written_with_the_image(tmp_path: Path) -> None:
    images, name = stored(tmp_path)
    model = RecordingModel({"question": "Capitale française ?", "answer": "Paris"})
    generator = PydanticAIVariantGenerator(model.model, images)

    variant = await generator.generate_one(KnowledgeMother.new().with_image(name).build(), "Réponds en français.")

    assert variant.question == "Capitale française ?"
    [(text, image)] = model.prompts
    assert text == f"{CARD}\nExisting variants:\n- Capitale de la France ? -> Paris"
    assert isinstance(image, BinaryContent)
    assert model.instructions[0] is not None
    assert model.instructions[0].startswith(GENERATE_ONE)


def test_text_only_answer_is_judged_as_before(tmp_path: Path) -> None:
    model = RecordingModel({"score": 1.0, "comment": "Exact."})
    judge = PydanticAIAnswerJudge(model.model, FileImageStore(tmp_path))
    variant = KnowledgeMother.new().build().original

    grade = judge.judge(variant, "paris", "Réponds en français.", None)

    assert grade == Grade(1.0, "Exact.")
    assert model.prompts == [
        "Deck instructions: Réponds en français.\n"
        "Question: Capitale de la France ?\n"
        "Reference answer: Paris\n"
        "Learner's answer: paris"
    ]
    assert model.instructions == [JUDGE]


def test_answer_is_judged_with_the_image(tmp_path: Path) -> None:
    images, name = stored(tmp_path)
    model = RecordingModel({"score": 1.0, "comment": "Exact."})
    judge = PydanticAIAnswerJudge(model.model, images)

    judge.judge(KnowledgeMother.new().build().original, "paris", "", name)

    [(_, image)] = model.prompts
    assert isinstance(image, BinaryContent)
    assert image.data == PNG
    assert model.instructions[0] is not None
    assert model.instructions[0].startswith(JUDGE)
    assert model.instructions[0] != JUDGE


async def test_missing_image_is_left_out(tmp_path: Path) -> None:
    model = RecordingModel(VARIANTS)
    generator = PydanticAIVariantGenerator(model.model, FileImageStore(tmp_path))

    variants = await generator.generate(KnowledgeMother.new().with_image("missing.png").build(), "Réponds en français.")

    assert model.prompts == [CARD]
    assert model.instructions == [GENERATE]
    assert [variant.question for variant in variants] == REPHRASINGS
