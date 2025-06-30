from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sql_app.db"  # Default for SQLite

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

