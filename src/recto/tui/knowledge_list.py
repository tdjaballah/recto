from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList
from textual.widgets.option_list import Option

from recto.container import Container
from recto.domain.deck import Deck
from recto.tui.variants import VariantsScreen


class KnowledgeListScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "variants", "Variants", priority=True),
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, container: Container, deck: Deck) -> None:
        super().__init__()
        self._container = container
        self._deck = deck
        self.sub_title = deck.name

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(id="knowledge", markup=False)
        yield Footer()

    def on_screen_resume(self) -> None:
        knowledge = self._container.list_knowledge().execute(self._deck.id)
        options = self.query_one("#knowledge", OptionList)
        highlighted = options.highlighted or 0
        options.clear_options()
        options.add_options(
            [Option(f"{item.original.question}   ({len(item.variants)} variants)", id=item.id) for item in knowledge]
        )
        if knowledge:
            options.highlighted = min(highlighted, len(knowledge) - 1)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_variants()

    def action_variants(self) -> None:
        option = self.query_one("#knowledge", OptionList).highlighted_option
        if option and option.id:
            self.app.push_screen(VariantsScreen(self._container, self._deck.id, option.id))
