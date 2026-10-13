"""
Application configuration.

Loads settings from environment variables (via .env file).
All configurable values should be accessed through the `settings` singleton.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

        # CORS origins — comma-separated list
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        self.ALLOWED_ORIGINS: list[str] = [
            origin.strip()
            for origin in origins_str.split(",")
            if origin.strip()
        ]

        # API keys (used in later milestones)
        self.SEARCH_API_KEY: str | None = os.getenv("SEARCH_API_KEY")
        self.SEARCH_ENGINE_ID: str | None = os.getenv("SEARCH_ENGINE_ID")
        self.LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
        self.LLM_MODEL: str | None = os.getenv("LLM_MODEL")


settings = Settings()
