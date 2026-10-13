"""
Rule-based claim triage engine.

Determines whether a submitted claim is potentially verifiable
(factual assertion) or should be filtered out (opinion, question,
casual commentary).

Will be fully implemented in Milestone 2.
"""


def triage_claim(claim: str) -> dict:
    """
    Classify whether a claim is suitable for verification.

    Args:
        claim: The normalized claim text.

    Returns:
        A dict with:
            - is_verifiable (bool): True if the claim should proceed.
            - reason (str): Human-readable explanation.
    """
    # Stub: accept all claims for now
    return {
        "is_verifiable": True,
        "reason": "[STUB] Triage engine not yet implemented. All claims pass through.",
    }
