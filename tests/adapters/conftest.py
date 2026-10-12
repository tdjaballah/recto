from collections.abc import Iterator

import pytest
from testcontainers.community.ollama import OllamaContainer

OLLAMA_IMAGE = "alpine/ollama:0.40.3"
OLLAMA_MODEL = "qwen2.5:0.5b"
MODEL_CACHE_VOLUME = "frigo-ollama-models"


@pytest.fixture(scope="session")
def ollama_url() -> Iterator[str]:
    with OllamaContainer(OLLAMA_IMAGE, ollama_home=MODEL_CACHE_VOLUME) as ollama:
        ollama.pull_model(OLLAMA_MODEL)
        yield ollama.get_endpoint()
