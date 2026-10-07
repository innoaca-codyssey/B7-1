from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"
    default_token_limit: int = 100000
    jwt_secret: str
    jwt_expire_minutes: int = 1440
    admin_username: str | None = None
    admin_password: str | None = None


settings = Settings()
