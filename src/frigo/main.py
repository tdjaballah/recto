import sys
from pathlib import Path

from frigo.cli.commands import build_cli
from frigo.container import Container


def main() -> None:
    container = Container()
    container.config.db_path.from_env("FRIGO_DB", default=str(Path.home() / ".frigo.db"))
    container.config.chef.from_env("FRIGO_CHEF", default="ollama")
    container.config.ollama.url.from_env("FRIGO_OLLAMA_URL", default="http://localhost:11434")
    container.config.ollama.model.from_env("FRIGO_OLLAMA_MODEL", default="qwen2.5:1.5b")
    container.config.openai.api_key.from_env("OPENAI_API_KEY", default="missing")
    container.config.openai.model.from_env("FRIGO_OPENAI_MODEL", default="gpt-5.4-mini")
    if container.config.chef() not in container.chef.providers:
        sys.exit(f"FRIGO_CHEF must be one of: {', '.join(container.chef.providers)}")

    build_cli(container)()
