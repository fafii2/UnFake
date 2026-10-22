"""
Application configuration.

Loads settings from environment variables (via .env file).
All configurable values should be accessed through the `settings` singleton.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


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
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or self.LLM_API_KEY
        self.LLM_MODEL = self.LLM_MODEL or "gemini-3.5-flash"
        self.SEARCH_API_KEY = os.getenv("TAVILY_API_KEY") or self.SEARCH_API_KEY
        self.ARCHIVE_PATH = Path(os.getenv("ARCHIVE_PATH", str(BASE_DIR / "data" / "archive.sqlite3")))
        self.ARCHIVE_SEED = BASE_DIR / "data" / "archive.json"
        self.EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini" if self.GEMINI_API_KEY else "none")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        self.LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.PROVIDER_TIMEOUT_SECONDS = float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "12"))
        self.VERIFY_TIMEOUT_SECONDS = float(os.getenv("VERIFY_TIMEOUT_SECONDS", "25"))
        self.CALIBRATION_PATH = Path(os.getenv("CALIBRATION_PATH", str(BASE_DIR / "data" / "calibration.json")))
        self.MAX_EVIDENCE = 8
        self.SEARCH_DOMAINS = [
            "verafiles.org", "tsek.ph", "rappler.com", "gmanetwork.com", "inquirer.net",
            "philstar.com", "pna.gov.ph", "gov.ph", "factcheck.afp.com",
        ]


settings = Settings()
