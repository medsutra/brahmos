import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    GOOGLE_GENAI_API_KEY: str = os.getenv("GOOGLE_GENAI_API_KEY", "")
    GOOGLE_GENAI_MODEL: str = os.getenv("GOOGLE_GENAI_MODEL", "")
    COLLECTION_NAME: str = os.getenv("GOOGLE_GENAI_MODEL", "")
    GOOGLE_GENAI_EMBEDDING_MODEL: str = os.getenv("GOOGLE_GENAI_EMBEDDING_MODEL", "")
    VECTOR_STORAGE_URL: str = os.getenv("VECTOR_STORAGE_URL", "")
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", 768))
    VECTOR_STORAGE_API_KEY: str = os.getenv("VECTOR_STORAGE_API_KEY", "")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
