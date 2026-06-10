import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cabinet_craft.db")

    # LLM Configuration
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000"]
    )


settings = Settings()
