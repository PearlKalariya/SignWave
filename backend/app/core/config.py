from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "signwave_meeting"
    anthropic_api_key: str = ""
    secret_key: str = "dev-secret-change-in-prod"
    backend_port: int = 8010
    cors_origins: List[str] = ["http://localhost:3000"]
    whisper_model: str = "base"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
