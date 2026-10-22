"""Validated archive interchange format. One record represents one checked assertion."""
import hashlib
import re
from datetime import date
from pydantic import BaseModel, Field, HttpUrl
from api.schemas import Verdict
from services.preprocessor import normalize_claim


def claim_key(text: str) -> str:
    # Preserve numbers and negation; fuzzy similarity is not proof of stance.
    return re.sub(r"[^\w%₱$]+", " ", normalize_claim(text).casefold()).strip()


def source_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


class EvidenceRecord(BaseModel):
    claim_text: str = Field(min_length=4, max_length=5000)
    verdict: Verdict
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    source_url: HttpUrl
    published_date: date
    retrieved_date: date
    snippet: str = Field(min_length=1, max_length=5000)
    aliases: list[str] = Field(default_factory=list)
    original_rating: str
    provenance_url: HttpUrl | None = None
