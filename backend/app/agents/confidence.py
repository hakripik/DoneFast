"""Combines Phase 3-5 signals (retrieval similarity, verifier outcome, retry flag)
into a single 0-100 confidence score with a human-readable breakdown.

No LLM call here — this is a deterministic scoring formula, kept simple on purpose
so the result can always be explained in one sentence:

confidence = up to 50 points for retrieval strength (top similarity score, plus a
small bonus if it clearly beats the rest) + up to 40 points for the verifier's
outcome (reduced per flagged issue, more so if marked unsupported) - 10 points if
a retry was needed - capped at 30 overall if the top retrieval match is weak,
regardless of how the verifier judged the answer - and 0 outright if the answer
cited no evidence at all (an honest "I don't know" isn't a claim to be confident
about, even when the verifier correctly marks it as "supported").
"""

# Below this similarity, retrieved chunks likely don't really address the question
# (observed empirically: on-topic queries scored ~0.7-0.85, vague/off-topic ~0.5-0.56).
WEAK_RETRIEVAL_THRESHOLD = 0.55
STRONG_RETRIEVAL_THRESHOLD = 0.65
WEAK_MATCH_CAP = 30
RETRY_PENALTY = 10


def compute_confidence(
    retrieval_scores: list[float],
    verification: dict,
    retried: bool,
    has_citations: bool = True,
) -> dict:
    """Combine retrieval strength, verifier outcome, and retry flag into a score.

    `has_citations` should reflect whether the solver's answer actually cited any
    retrieved chunk (Phase 4's `used_chunk_ids`). Without it, a verifier correctly
    marking an honest "I don't know" as supported would score the same as a
    verified, well-grounded answer — there's no way to tell "nothing to answer
    with" apart from "answered and checked out" using verifier output alone.

    Returns {"confidence": int, "breakdown": list[str]}.
    """
    if not retrieval_scores:
        return {
            "confidence": 0,
            "breakdown": ["No retrieved evidence to assess — confidence not applicable."],
        }

    if not has_citations:
        return {
            "confidence": 0,
            "breakdown": [
                "The answer didn't cite any retrieved evidence — there's no substantive "
                "claim here to be confident about."
            ],
        }

    breakdown: list[str] = []

    top = max(retrieval_scores)
    rest = [s for s in retrieval_scores if s != top] or [top]
    avg_rest = sum(rest) / len(rest)
    gap = top - avg_rest

    retrieval_points = round(min(max(top, 0.0), 1.0) * 45)
    gap_bonus = round(min(max(gap / 0.25, 0.0), 1.0) * 5)
    retrieval_points = min(50, retrieval_points + gap_bonus)

    if top >= STRONG_RETRIEVAL_THRESHOLD:
        breakdown.append(f"Strong retrieval match (top score {top:.2f})")
    elif top >= WEAK_RETRIEVAL_THRESHOLD:
        breakdown.append(f"Moderate retrieval match (top score {top:.2f})")
    else:
        breakdown.append(
            f"Weak retrieval match (top score {top:.2f}) — retrieved material may not "
            "really address the question"
        )

    if len(retrieval_scores) > 1:
        if gap >= 0.1:
            breakdown.append(f"Top result clearly stood out from the rest (gap {gap:.2f})")
        else:
            breakdown.append("No single chunk stood out — retrieved results were all similarly related")

    issues = verification.get("issues") or []
    supported = bool(verification.get("supported"))

    if supported:
        verifier_points = max(15, 40 - 8 * len(issues))
        if issues:
            breakdown.append(f"Verifier marked it supported but flagged {len(issues)} issue(s): {issues[0]}")
        else:
            breakdown.append("Verifier found the answer fully supported with no issues")
    else:
        verifier_points = max(0, 12 - 5 * len(issues))
        if issues:
            breakdown.append(f"Verifier flagged {len(issues)} issue(s): {issues[0]}")
        else:
            breakdown.append("Verifier marked the answer as not supported")

    penalty = 0
    if retried:
        penalty = RETRY_PENALTY
        breakdown.append("Required a retry to reach this answer, indicating the first retrieval pass was weak")

    total = retrieval_points + verifier_points - penalty

    if top < WEAK_RETRIEVAL_THRESHOLD and total > WEAK_MATCH_CAP:
        total = WEAK_MATCH_CAP
        breakdown.append(
            "Retrieval match is too weak for a confident answer, so the score is capped "
            "regardless of the verifier's outcome"
        )

    total = max(0, min(100, total))

    return {"confidence": total, "breakdown": breakdown}
