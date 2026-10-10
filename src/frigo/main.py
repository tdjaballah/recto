from pathlib import Path

from frigo.cli.commands import build_cli
from frigo.container import Container


def main() -> None:
    container = Container()
    container.config.db_path.from_env("FRIGO_DB", default=str(Path.home() / ".frigo.db"))
    container.config.ollama.url.from_env("FRIGO_OLLAMA_URL", default="http://localhost:11434")
    container.config.ollama.model.from_env("FRIGO_OLLAMA_MODEL", default="qwen2.5:1.5b")
    build_cli(container)()
