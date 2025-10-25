from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/socket_chat"
    )
    jwt_secret: str = "dev-secret"
    jwt_alg: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未在 Settings 中声明的其他环境变量（如 API_BASE/WS_URL）
    )


settings = Settings()  # type: ignore[call-arg]
