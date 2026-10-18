from textwrap import shorten
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from recto.container import Container
from recto.domain.deck import Deck
from recto.tui.importing import ImportScreen
from recto.tui.knowledge_list import KnowledgeListScreen
from recto.tui.review import ReviewScreen
from recto.use_cases.list_decks import DeckSummary


class DecksScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "review", "Review", priority=True),
        ("c", "cards", "Cards"),
        ("i", "import", "Import"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container = container
        self._decks: dict[str, Deck] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(id="decks", markup=False)
        yield Static("", id="empty", markup=False)
        yield Footer()

    def on_screen_resume(self) -> None:
        summaries = self._container.list_decks().execute()
        self._decks = {summary.deck.id: summary.deck for summary in summaries}
        decks = self.query_one("#decks", OptionList)
        highlighted = decks.highlighted or 0
        decks.clear_options()
        decks.add_options([Option(_line(summary), id=summary.deck.id) for summary in summaries])
        if summaries:
            decks.highlighted = min(highlighted, len(summaries) - 1)
        self.query_one("#empty", Static).update("" if summaries else "No deck yet. Press i to import one.")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_review()

    def action_review(self) -> None:
        if deck := self._highlighted():
            self.app.push_screen(ReviewScreen(self._container, deck))

    def action_cards(self) -> None:
        if deck := self._highlighted():
            self.app.push_screen(KnowledgeListScreen(self._container, deck))

    def action_import(self) -> None:
        self.app.push_screen(ImportScreen(self._container))

    def _highlighted(self) -> Deck | None:
        option = self.query_one("#decks", OptionList).highlighted_option
        return self._decks.get(option.id) if option and option.id else None


def _line(summary: DeckSummary) -> str:
    description = shorten(summary.deck.description, 23, placeholder="…")
    counts = f"{summary.to_review:>4} to review · {summary.learning:>2} learning · {summary.new:>2} new"
    return f"{summary.deck.name:<14}{description:<25}{counts}"
