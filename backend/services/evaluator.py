"""
Evidence evaluation service (RAG pipeline).

Compares a claim against retrieved evidence to produce a verdict,
explanation, and citations.

Will be implemented in Milestone 5.
"""


async def evaluate_claim(claim: str, evidence: list[dict]) -> dict:
    """
    Evaluate a claim against retrieved evidence.

    Args:
        claim: The normalized claim text.
        evidence: List of evidence items from the retrieval service.

    Returns:
        A dict with verdict, explanation, confidence, and citations.
    """
    # Stub: no evaluation yet
    return {
        "verdict": "insufficient_evidence",
        "explanation": "[STUB] Evidence evaluation not yet implemented.",
        "confidence": None,
        "citations": [],
    }
