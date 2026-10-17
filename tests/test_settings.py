from pathlib import Path

import pytest

from recto.settings import Settings


def test_settings_are_read_from_the_recto_variables_and_the_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECTO_DB", "/data/recto.db")
    monkeypatch.setenv("RECTO_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = Settings()

    assert settings.db == Path("/data/recto.db")
    assert settings.model == "gpt-5.4"
    assert settings.openai_api_key == "sk-test"
