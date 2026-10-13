"""
Evidence retrieval service.

Coordinates retrieval from the local fact-check archive (SQLite + vector search)
and live web search providers.

Will be implemented in Milestone 4.
"""


async def retrieve_evidence(claim: str) -> list[dict]:
    """
    Retrieve relevant evidence for a given claim.

    Args:
        claim: The normalized claim text.

    Returns:
        A list of evidence dictionaries with source metadata.
    """
    # Stub: no evidence retrieval yet
    return []
