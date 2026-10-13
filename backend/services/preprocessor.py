"""
Text preprocessing service.

Normalizes and cleans user-submitted claim text before verification.
Preserves the original claim for reference.

Will be fully implemented in Milestone 2.
"""


def normalize_claim(raw_text: str) -> str:
    """
    Normalize whitespace and clean a raw claim string.

    - Strips leading/trailing whitespace
    - Collapses multiple spaces/newlines into single spaces
    - Preserves the semantic content of the claim

    Args:
        raw_text: The raw text as submitted by the user.

    Returns:
        A cleaned, single-line version of the claim.
    """
    # Strip and collapse whitespace
    cleaned = " ".join(raw_text.split())
    return cleaned
