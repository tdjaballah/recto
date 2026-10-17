import sys

import pydantic_ai
from pydantic import ValidationError

from recto.container import Container
from recto.settings import Settings
from recto.tui.app import RectoApp


def main() -> None:
    pydantic_ai.BANNER_ENABLED = False  # ty: ignore[invalid-assignment]
    try:
        settings = Settings()
    except ValidationError as error:
        sys.exit("\n".join(f"recto: {e['loc'][0]}: {e['msg']}" for e in error.errors()))
    container = Container()
    container.config.from_pydantic(settings)
    RectoApp(container).run()
