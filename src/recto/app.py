from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header


class RectoApp(App):
    TITLE = "Recto"
    BINDINGS: ClassVar[list[BindingType]] = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


def main() -> None:
    RectoApp().run()
