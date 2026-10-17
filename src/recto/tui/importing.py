from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from recto.adapters.toml_deck_files import example_decks, read_deck_file
from recto.container import Container
from recto.domain.deck import DeckFile
from recto.domain.errors import InvalidDeck, ModelUnavailable


class ImportScreen(Screen[None]):
    BINDINGS: ClassVar[list[BindingType]] = [("escape", "back", "Back")]

    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container = container
        self._examples = {example.deck.id: example for example in example_decks()}
        self._importing = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Example decks")
        yield OptionList(
            *(Option(example.deck.name, id=deck_id) for deck_id, example in self._examples.items()),
            id="examples",
            markup=False,
        )
        yield Label("Or a file")
        yield Input(placeholder="~/decks/espagnol.toml", id="path")
        yield Static("", id="status", markup=False)
        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        return not (action == "back" and self._importing)

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id and not self._importing:
            self._start(self._examples[event.option.id])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._importing:
            return
        try:
            deck_file = read_deck_file(event.value)
        except InvalidDeck as error:
            self._show(str(error))
            return
        self._start(deck_file)

    def _start(self, deck_file: DeckFile) -> None:
        self._set_importing(True)
        self._import(deck_file)

    @work(thread=True, exclusive=True)
    def _import(self, deck_file: DeckFile) -> None:
        def progress(done: int, total: int) -> None:
            self.app.call_from_thread(self._show, f"Generating variants… {done}/{total}")

        self.app.call_from_thread(self._show, "Generating variants…")
        try:
            report = self._container.import_deck().execute(deck_file, on_progress=progress)
        except ModelUnavailable as error:
            self.app.call_from_thread(self._failed, f"Import failed: {error}")
            return
        message = (
            f"{deck_file.deck.name}: {report.added} added, {report.regenerated} regenerated, {report.removed} deleted"
        )
        self.app.call_from_thread(self._done, message)

    def _show(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _failed(self, message: str) -> None:
        self._set_importing(False)
        self._show(message)

    def _done(self, message: str) -> None:
        self.app.notify(message)
        self.app.pop_screen()

    def _set_importing(self, importing: bool) -> None:
        self._importing = importing
        self.refresh_bindings()
