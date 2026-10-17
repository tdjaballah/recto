import pydantic_ai

from recto.container import Container
from recto.settings import Settings
from recto.tui.app import RectoApp


def main() -> None:
    pydantic_ai.BANNER_ENABLED = False  # ty: ignore[invalid-assignment]
    container = Container()
    container.config.from_pydantic(Settings())
    RectoApp(container).run()
