from pathlib import Path

from frigo.cli.commands import build_cli
from frigo.container import Container


def main() -> None:
    container = Container()
    container.config.db_path.from_env("FRIGO_DB", default=str(Path.home() / ".frigo.db"))
    build_cli(container)()
