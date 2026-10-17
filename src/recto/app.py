from pathlib import Path

import pydantic_ai
from platformdirs import user_data_dir

from recto.container import Container
from recto.tui.app import RectoApp


def main() -> None:
    pydantic_ai.BANNER_ENABLED = False  # ty: ignore[invalid-assignment]
    container = Container()
    container.config.db_path.from_env("RECTO_DB", default=str(Path(user_data_dir("recto")) / "recto.db"))
    container.config.model.from_env("RECTO_MODEL", default="openai:gpt-5.4-mini")
    RectoApp(container).run()
