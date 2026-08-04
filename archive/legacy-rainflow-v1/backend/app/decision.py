"""Deterministic policy ranking and operator-facing decision evidence.

The decision layer consumes the serialized policy dictionaries already produced
by ``backend.app.main.build_run``.  It never calculates traffic KPI values or
overrides the deterministic safety guard.
"""
from __future__ import annotations


SCORING_VERSION = "rainflow-rule-v1"
EXPLANATION_MODE = "rule_based"

# A reduction is represented by a negative delta, so the weighted sum is
# negated to make larger scores better.  The order is also the evidence order.
_METRIC_WEIGHTS = (
    ("spillback_time_pct", 0.50),
    ("total_travel_time_pct", 0.35),
    ("worst_approach_delay_pct", 0.15),
)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def score_policy_delta(delta: dict) -> float:
    """Return the versioned weighted score used by operator and game modes."""

    weighted_delta = 0.0
    for metric, weight in _METRIC_WEIGHTS:
        value = _number(delta.get(metric))
        if value is not None:
            weighted_delta += value * weight
    score = round(-weighted_delta, 3)
    return 0.0 if score == 0 else score


def _score(delta: dict) -> float:
    """Backward-compatible private alias for the frozen decision workflow."""

    return score_policy_delta(delta)


def _guard_risks(guard: dict) -> list[dict]:
    if guard.get("passed") is True:
        return []

    risks = []
    violations = guard.get("violations")
    if isinstance(violations, list):
        normalized = []
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            normalized.append(
                {
                    "code": str(violation.get("code", "GUARD_REJECTED")),
                    "detail": str(violation.get("detail", "Safety guard rejected the policy.")),
                }
            )
        risks.extend(sorted(normalized, key=lambda item: (item["code"], item["detail"])))

    if not risks:
        risks.append(
            {
                "code": "GUARD_REJECTED",
                "detail": "Safety guard rejected the policy without a violation code.",
            }
        )
    return risks


def _metric_evidence(delta: dict) -> tuple[list[dict], list[dict]]:
    evidence = []
    risks = []
    for metric, weight in _METRIC_WEIGHTS:
        value = _number(delta.get(metric))
        if value is None:
            evidence.append(
                {
                    "metric": metric,
                    "available": False,
                    "weight": weight,
                }
            )
            continue

        assessment = "improved" if value < 0 else ("worsened" if value > 0 else "unchanged")
        evidence.append(
            {
                "metric": metric,
                "available": True,
                "delta_pct": value,
                "assessment": assessment,
                "weight": weight,
            }
        )
        if value > 0:
            risks.append(
                {
                    "code": "METRIC_WORSENED",
                    "metric": metric,
                    "delta_pct": value,
                }
            )
    return evidence, risks


def build_rule_based_decision(policy_results: list[dict]) -> dict:
    """Rank serialized policy results without an LLM.

    ``policy_results`` entries must contain ``policy_id``, ``kpi``,
    ``delta_vs_no_action``, and ``guard``.  A guard-failing policy is always
    ranked after guard-passing policies and can never be recommended.
    ``no_action`` is required as the safe fallback and must itself be marked as
    guard-passing.
    """
    if not isinstance(policy_results, list) or not policy_results:
        raise ValueError("policy_results must be a non-empty list")

    by_id: dict[str, dict] = {}
    for policy in policy_results:
        if not isinstance(policy, dict):
            raise ValueError("each policy result must be a dictionary")

        policy_id = policy.get("policy_id")
        if not isinstance(policy_id, str) or not policy_id:
            raise ValueError("each policy result must have a non-empty policy_id")
        if policy_id in by_id:
            raise ValueError(f"duplicate policy_id: {policy_id}")

        for field in ("kpi", "delta_vs_no_action", "guard"):
            if not isinstance(policy.get(field), dict):
                raise ValueError(f"{policy_id}.{field} must be a dictionary")
        by_id[policy_id] = policy

    if "no_action" not in by_id:
        raise ValueError("no_action policy is required as the safe fallback")
    if by_id["no_action"]["guard"].get("passed") is not True:
        raise ValueError("no_action must be guard-passing to serve as the safe fallback")

    assessments_by_id = {}
    for policy_id in sorted(by_id):
        policy = by_id[policy_id]
        guard = policy["guard"]
        delta = policy["delta_vs_no_action"]
        metric_evidence, metric_risks = _metric_evidence(delta)
        guard_passed = guard.get("passed") is True

        assessments_by_id[policy_id] = {
            "policy_id": policy_id,
            "guard_passed": guard_passed,
            "score": _score(delta),
            "evidence": [
                {
                    "code": "GUARD_PASSED" if guard_passed else "GUARD_FAILED",
                    "value": guard_passed,
                },
                *metric_evidence,
            ],
            "risks": [*_guard_risks(guard), *metric_risks],
            "reasons": [],
        }

    ranked_policy_ids = sorted(
        assessments_by_id,
        key=lambda policy_id: (
            not assessments_by_id[policy_id]["guard_passed"],
            -assessments_by_id[policy_id]["score"],
            policy_id != "no_action",
            policy_id,
        ),
    )
    recommended_policy_id = ranked_policy_ids[0]

    for rank, policy_id in enumerate(ranked_policy_ids, start=1):
        assessment = assessments_by_id[policy_id]
        assessment["rank"] = rank
        if not assessment["guard_passed"]:
            reason = {
                "code": "EXCLUDED_BY_GUARD",
                "detail": "A guard-failing policy cannot be recommended.",
            }
        elif policy_id == recommended_policy_id and policy_id == "no_action":
            reason = {
                "code": "SAFE_FALLBACK",
                "detail": "No guard-passing policy scored above the no_action baseline.",
            }
        elif policy_id == recommended_policy_id:
            reason = {
                "code": "BEST_SAFE_SCORE",
                "detail": "Highest score among guard-passing policies.",
            }
        elif policy_id == "no_action":
            reason = {
                "code": "SAFE_BASELINE",
                "detail": "Retained as the fallback if the recommended policy cannot be applied.",
            }
        else:
            reason = {
                "code": "LOWER_SAFE_SCORE",
                "detail": "Guard-passing, but scored below the recommended policy.",
            }
        assessment["reasons"].append(reason)

    return {
        "scoring_version": SCORING_VERSION,
        "explanation_mode": EXPLANATION_MODE,
        "recommended_policy_id": recommended_policy_id,
        "ranked_policy_ids": ranked_policy_ids,
        "policy_assessments": [
            assessments_by_id[policy_id] for policy_id in ranked_policy_ids
        ],
    }
