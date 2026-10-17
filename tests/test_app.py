import pytest

from recto.app import main


def test_recto_stops_with_a_short_message_when_the_openai_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SystemExit, match=r"^recto: OPENAI_API_KEY: Field required$"):
        main()
