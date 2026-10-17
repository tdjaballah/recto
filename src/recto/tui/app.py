from textual.app import App

from recto.container import Container
from recto.tui.decks import DecksScreen


class RectoApp(App[None]):
    TITLE = "Recto"

    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container = container

    def on_mount(self) -> None:
        self.push_screen(DecksScreen(self._container))
