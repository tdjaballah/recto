from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from recto.container import Container
from recto.use_cases.list_decks import DeckSummary


class DecksScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container = container

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(id="decks", markup=False)
        yield Static("", id="empty", markup=False)
        yield Footer()

    def on_screen_resume(self) -> None:
        summaries = self._container.list_decks().execute()
        decks = self.query_one("#decks", OptionList)
        highlighted = decks.highlighted or 0
        decks.clear_options()
        decks.add_options([Option(_line(summary), id=summary.deck.id) for summary in summaries])
        if summaries:
            decks.highlighted = min(highlighted, len(summaries) - 1)
        self.query_one("#empty", Static).update("" if summaries else "No deck yet. Press i to import one.")


def _line(summary: DeckSummary) -> str:
    return f"{summary.deck.name:<14}{summary.deck.description:<40}{summary.to_review:>4} · {summary.new:>2} ✦"
