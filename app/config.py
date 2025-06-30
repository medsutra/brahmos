import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    GOOGLE_GENAI_API_KEY: str = os.getenv("GOOGLE_GENAI_API_KEY", "")
    GOOGLE_GENAI_MODEL: str = "gemini-2.0-flash-001"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
