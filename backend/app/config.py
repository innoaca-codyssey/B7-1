from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"
    default_token_limit: int = 100000
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 1440

    ai_base_url: str = "https://copa.codyssey.kr/v1"
    ai_api_key: SecretStr = SecretStr("")
    ai_timeout_seconds: float = 30
    context_window: int = 10


settings = Settings()
