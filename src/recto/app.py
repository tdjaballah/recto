import os
from pathlib import Path

from platformdirs import user_data_dir

from recto.container import Container
from recto.tui.app import RectoApp


def main() -> None:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    container = Container()
    container.config.db_path.from_env("RECTO_DB", default=str(Path(user_data_dir("recto")) / "recto.db"))
    container.config.model.from_env("RECTO_MODEL", default="openai:gpt-5.4-mini")
    RectoApp(container).run()
