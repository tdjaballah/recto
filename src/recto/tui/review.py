from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, LoadingIndicator, Static

from recto.container import Container
from recto.domain.errors import ModelUnavailable
from recto.domain.grading import Grade
from recto.tui.variants import VariantsScreen
from recto.use_cases.next_card import Question


class ReviewScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "next", "Next"),
        Binding("v", "variants", "Variants"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, container: Container, deck_id: str) -> None:
        super().__init__()
        self._container = container
        self._deck_id = deck_id
        self._question: Question | None = None
        self._graded = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="progress", markup=False)
        yield Static("", id="question", markup=False)
        yield Input(id="answer", select_on_focus=False)
        yield LoadingIndicator(id="judging")
        yield Static("", id="grade", markup=False)
        yield Static("", id="expected", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#judging").display = False
        self._ask()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in ("next", "variants"):
            return self._graded
        return True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._question is None:
            return
        event.input.disabled = True
        self.query_one("#judging").display = True
        self.query_one("#grade", Static).update("")
        self._judge(self._question, event.value)

    def action_next(self) -> None:
        self._ask()

    def action_variants(self) -> None:
        if self._question:
            self.app.push_screen(VariantsScreen(self._container, self._deck_id, self._question.knowledge.id))

    def _ask(self) -> None:
        question = self._container.next_card().execute(self._deck_id)
        if question is None:
            self.app.notify("Nothing to review")
            self.app.pop_screen()
            return
        self._question = question
        self._set_graded(False)
        self.query_one("#progress", Static).update(f"{question.remaining} left")
        self.query_one("#question", Static).update(question.variant.question)
        self.query_one("#grade", Static).update("")
        self.query_one("#expected", Static).update("")
        answer = self.query_one("#answer", Input)
        answer.value = ""
        answer.disabled = False
        answer.focus()

    @work(thread=True, exclusive=True)
    def _judge(self, question: Question, answer: str) -> None:
        try:
            grade = self._container.submit_answer().execute(
                self._deck_id, question.knowledge.id, question.variant.id, answer
            )
        except ModelUnavailable as error:
            self.app.call_from_thread(self._failed, str(error))
            return
        self.app.call_from_thread(self._show_grade, question, grade)

    def _show_grade(self, question: Question, grade: Grade) -> None:
        if not self.is_attached:
            return
        self.query_one("#judging").display = False
        mark = "✓" if grade.score == 1 else "✗"
        self.query_one("#grade", Static).update(f"{mark} {round(grade.score * 100)} %   {grade.comment}")
        self.query_one("#expected", Static).update(f"Answer: {question.variant.answer}")
        self._set_graded(True)
        self.set_focus(None)

    def _failed(self, message: str) -> None:
        if not self.is_attached:
            return
        self.query_one("#judging").display = False
        self.query_one("#grade", Static).update(f"Could not grade the answer: {message}")
        answer = self.query_one("#answer", Input)
        answer.disabled = False
        answer.focus()

    def _set_graded(self, graded: bool) -> None:
        self._graded = graded
        self.refresh_bindings()
