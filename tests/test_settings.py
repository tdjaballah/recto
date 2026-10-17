from pathlib import Path

import pytest

from recto.settings import Settings


def test_settings_are_read_from_the_recto_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECTO_DB", "/data/recto.db")
    monkeypatch.setenv("RECTO_MODEL", "openai:gpt-5.4")

    settings = Settings()

    assert settings.db == Path("/data/recto.db")
    assert settings.model == "openai:gpt-5.4"
