from collections.abc import Callable
from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from recto.container import Container
from recto.domain.errors import EmptyVariant, ModelUnavailable
from recto.domain.knowledge import Knowledge, Variant


class VariantsScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("n", "new", "New"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("g", "generate", "Generate"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, container: Container, deck_id: str, knowledge_id: str) -> None:
        super().__init__()
        self._container = container
        self._deck_id = deck_id
        self._knowledge_id = knowledge_id
        self._variants: tuple[Variant, ...] = ()
        self._generating = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._knowledge_id, id="title", markup=False)
        yield OptionList(id="variants", markup=False)
        yield Static("", id="status", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self._show(self._container.get_knowledge().execute(self._deck_id, self._knowledge_id))

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if self._generating and action in ("new", "edit", "delete", "generate"):
            return False
        if action in ("edit", "delete"):
            variant = self._highlighted()
            return variant is not None and not variant.is_original
        return True

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self.refresh_bindings()

    def action_new(self) -> None:
        def add(result: tuple[str, str] | None) -> None:
            if result:
                self._change(lambda: self._container.add_variant().execute(self._deck_id, self._knowledge_id, *result))

        self.app.push_screen(VariantForm(), add)

    def action_edit(self) -> None:
        variant = self._highlighted()
        if variant is None or variant.is_original:
            return

        def edit(result: tuple[str, str] | None) -> None:
            if result:
                self._change(
                    lambda: self._container.edit_variant().execute(
                        self._deck_id, self._knowledge_id, variant.id, *result
                    )
                )

        self.app.push_screen(VariantForm(variant.question, variant.answer), edit)

    def action_delete(self) -> None:
        variant = self._highlighted()
        if variant is None or variant.is_original:
            return

        def delete(confirmed: bool | None) -> None:
            if confirmed:
                self._change(
                    lambda: self._container.delete_variant().execute(self._deck_id, self._knowledge_id, variant.id)
                )

        self.app.push_screen(Confirm("Delete this variant? (y/n)"), delete)

    def action_generate(self) -> None:
        self._generating = True
        self.refresh_bindings()
        self.query_one("#status", Static).update("Generating a variant…")
        self._generate()

    @work(thread=True, exclusive=True)
    def _generate(self) -> None:
        try:
            knowledge = self._container.generate_variant().execute(self._deck_id, self._knowledge_id)
        except ModelUnavailable as error:
            self.app.call_from_thread(self._generated, None, f"Generation failed: {error}")
            return
        self.app.call_from_thread(self._generated, knowledge, "")

    def _generated(self, knowledge: Knowledge | None, message: str) -> None:
        if not self.is_attached:
            return
        self._generating = False
        if knowledge:
            self._show(knowledge)
        self.query_one("#status", Static).update(message)
        self.refresh_bindings()

    def _change(self, change: Callable[[], Knowledge]) -> None:
        try:
            knowledge = change()
        except EmptyVariant:
            self.query_one("#status", Static).update("A variant needs a question and an answer.")
            return
        self._show(knowledge)

    def _show(self, knowledge: Knowledge) -> None:
        self._variants = knowledge.variants
        options = self.query_one("#variants", OptionList)
        highlighted = options.highlighted or 0
        options.clear_options()
        options.add_options([Option(_line(variant), id=variant.id) for variant in knowledge.variants])
        options.highlighted = min(highlighted, len(knowledge.variants) - 1)
        self.query_one("#status", Static).update("")
        self.refresh_bindings()

    def _highlighted(self) -> Variant | None:
        option = self.query_one("#variants", OptionList).highlighted_option
        return next((variant for variant in self._variants if option and variant.id == option.id), None)


class VariantForm(ModalScreen[tuple[str, str] | None]):
    BINDINGS: ClassVar[list[BindingType]] = [("escape", "cancel", "Cancel")]

    def __init__(self, question: str = "", answer: str = "") -> None:
        super().__init__()
        self._question = question
        self._answer = answer

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Question")
            yield Input(self._question, id="question", select_on_focus=False)
            yield Label("Answer")
            yield Input(self._answer, id="answer", select_on_focus=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "question":
            self.query_one("#answer", Input).focus()
            return
        self.dismiss((self.query_one("#question", Input).value, event.value))

    def action_cancel(self) -> None:
        self.dismiss(None)


class Confirm(ModalScreen[bool]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("y", "answer(True)", "Yes"),
        ("n,escape", "answer(False)", "No"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        yield Static(self._message, markup=False)

    def action_answer(self, yes: bool) -> None:
        self.dismiss(yes)


def _line(variant: Variant) -> str:
    marker = "● " if variant.is_original else "  "
    suffix = "   (original)" if variant.is_original else ""
    return f"{marker}{variant.question} → {variant.answer}{suffix}"
