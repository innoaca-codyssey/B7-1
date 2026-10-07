from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"
    default_token_limit: int = 100000
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 1440
    admin_username: str | None = None
    admin_password: SecretStr | None = None

    ai_base_url: str = "https://copa.codyssey.kr/v1"
    ai_api_key: SecretStr = SecretStr("")
    ai_timeout_seconds: float = 30
    context_window: int = 10

    @field_validator("admin_password")
    @classmethod
    def check_admin_password(cls, v: SecretStr | None) -> SecretStr | None:
        if v is not None:
            password = v.get_secret_value()
            if len(password) < 8 or len(password.encode()) > 72:
                raise ValueError("ADMIN_PASSWORD는 8자 이상 72바이트 이하여야 합니다")
        return v


settings = Settings()
