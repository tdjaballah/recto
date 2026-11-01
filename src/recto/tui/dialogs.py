from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Static


class Dialog[T](ModalScreen[T]):
    DEFAULT_CSS = """
    Dialog {
        align: center middle;
    }
    Dialog > #dialog {
        width: 80%;
        height: auto;
        padding: 1 2;
        border: round $primary;
        background: $surface;
    }
    """

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = self._title


class Confirm(Dialog[bool]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("y", "answer(True)", "Yes"),
        ("n,escape", "answer(False)", "No"),
    ]

    def __init__(self, title: str, message: str) -> None:
        super().__init__(title)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._message, id="message", markup=False)
        yield Footer()

    def action_answer(self, yes: bool) -> None:
        self.dismiss(yes)
