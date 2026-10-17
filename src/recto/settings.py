from pathlib import Path

from platformdirs import user_data_dir
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RECTO_")

    db: Path = Path(user_data_dir("recto")) / "recto.db"
    model: str = "gpt-5.4-mini"
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY")
