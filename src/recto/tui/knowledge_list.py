from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList
from textual.widgets.option_list import Option

from recto.container import Container
from recto.tui.variants import VariantsScreen


class KnowledgeListScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [("escape", "app.pop_screen", "Back")]

    def __init__(self, container: Container, deck_id: str) -> None:
        super().__init__()
        self._container = container
        self._deck_id = deck_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(id="knowledge", markup=False)
        yield Footer()

    def on_screen_resume(self) -> None:
        knowledge = self._container.list_knowledge().execute(self._deck_id)
        options = self.query_one("#knowledge", OptionList)
        highlighted = options.highlighted or 0
        options.clear_options()
        options.add_options(
            [Option(f"{item.original.question}   ({len(item.variants)} variants)", id=item.id) for item in knowledge]
        )
        if knowledge:
            options.highlighted = min(highlighted, len(knowledge) - 1)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.app.push_screen(VariantsScreen(self._container, self._deck_id, event.option.id))
