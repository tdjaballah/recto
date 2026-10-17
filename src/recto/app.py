from pathlib import Path

from platformdirs import user_data_dir

from recto.container import Container
from recto.tui.app import RectoApp


def main() -> None:
    container = Container()
    container.config.db_path.from_env("RECTO_DB", default=str(Path(user_data_dir("recto")) / "recto.db"))
    RectoApp(container).run()
