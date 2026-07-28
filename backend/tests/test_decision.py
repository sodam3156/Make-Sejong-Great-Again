"""Focused tests for the deterministic rule-based decision layer."""
import copy
import json
import unittest

from backend.app.decision import build_rule_based_decision


def _policy(
    policy_id,
    *,
    passed,
    spillback_delta=0.0,
    travel_time_delta=0.0,
    worst_delay_delta=0.0,
    violations=None,
):
    return {
        "policy_id": policy_id,
        "kpi": {
            "spillback_time_sec": 0,
            "recovery_time_sec": 0,
            "total_travel_time_sec": 0,
            "worst_approach_delay_sec": 0,
        },
        "delta_vs_no_action": {
            "spillback_time_pct": spillback_delta,
            "total_travel_time_pct": travel_time_delta,
            "worst_approach_delay_pct": worst_delay_delta,
        },
        "guard": {
            "passed": passed,
            "violations": violations or [],
        },
    }


class RuleBasedDecisionTests(unittest.TestCase):
    def test_recommends_best_guard_passing_policy(self):
        policies = [
            _policy("no_action", passed=True),
            _policy(
                "fixed_metering",
                passed=False,
                spillback_delta=-95.0,
                travel_time_delta=-90.0,
                violations=[
                    {
                        "code": "FAIRNESS_P95_EXCEEDED",
                        "detail": "One approach exceeds the fairness limit.",
                    }
                ],
            ),
            _policy(
                "corridor_gating",
                passed=True,
                spillback_delta=-71.0,
                travel_time_delta=-13.4,
                worst_delay_delta=-4.5,
            ),
        ]

        decision = build_rule_based_decision(policies)

        self.assertEqual(decision["scoring_version"], "rainflow-rule-v1")
        self.assertEqual(decision["explanation_mode"], "rule_based")
        self.assertEqual(decision["recommended_policy_id"], "corridor_gating")
        self.assertEqual(
            decision["ranked_policy_ids"],
            ["corridor_gating", "no_action", "fixed_metering"],
        )

        fixed = next(
            item
            for item in decision["policy_assessments"]
            if item["policy_id"] == "fixed_metering"
        )
        self.assertFalse(fixed["guard_passed"])
        self.assertIn(
            "FAIRNESS_P95_EXCEEDED",
            {risk["code"] for risk in fixed["risks"]},
        )
        self.assertEqual(fixed["reasons"][0]["code"], "EXCLUDED_BY_GUARD")

    def test_no_action_is_fallback_when_all_candidates_fail(self):
        policies = [
            _policy("no_action", passed=True),
            _policy(
                "fixed_metering",
                passed=False,
                spillback_delta=-80.0,
                violations=[{"code": "FAIRNESS_P95_EXCEEDED", "detail": "unsafe"}],
            ),
            _policy(
                "corridor_gating",
                passed=False,
                spillback_delta=-100.0,
                violations=[{"code": "SAFETY_TTC_DEGRADED", "detail": "unsafe"}],
            ),
        ]

        decision = build_rule_based_decision(policies)

        self.assertEqual(decision["recommended_policy_id"], "no_action")
        self.assertEqual(decision["ranked_policy_ids"][0], "no_action")
        baseline = decision["policy_assessments"][0]
        self.assertEqual(baseline["reasons"][0]["code"], "SAFE_FALLBACK")

    def test_no_action_beats_a_guard_passing_but_worse_policy(self):
        policies = [
            _policy("no_action", passed=True),
            _policy(
                "corridor_gating",
                passed=True,
                spillback_delta=5.0,
                travel_time_delta=2.0,
                worst_delay_delta=1.0,
            ),
        ]

        decision = build_rule_based_decision(policies)

        self.assertEqual(decision["recommended_policy_id"], "no_action")
        candidate = next(
            item
            for item in decision["policy_assessments"]
            if item["policy_id"] == "corridor_gating"
        )
        self.assertIn("METRIC_WORSENED", {risk["code"] for risk in candidate["risks"]})

    def test_output_is_byte_stable_and_input_order_independent(self):
        policies = [
            _policy("no_action", passed=True),
            _policy(
                "corridor_gating",
                passed=True,
                spillback_delta=-71.0,
                travel_time_delta=-13.4,
                worst_delay_delta=-4.5,
            ),
            _policy(
                "fixed_metering",
                passed=False,
                spillback_delta=-50.0,
                travel_time_delta=-8.6,
                worst_delay_delta=17.4,
                violations=[
                    {"detail": "fairness", "code": "FAIRNESS_P95_EXCEEDED"}
                ],
            ),
        ]
        before = copy.deepcopy(policies)

        first = build_rule_based_decision(policies)
        second = build_rule_based_decision(list(reversed(policies)))
        first_bytes = json.dumps(
            first, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        second_bytes = json.dumps(
            second, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")

        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(policies, before)

    def test_requires_a_guard_passing_no_action_fallback(self):
        with self.assertRaisesRegex(ValueError, "no_action policy is required"):
            build_rule_based_decision(
                [_policy("corridor_gating", passed=True, spillback_delta=-10.0)]
            )

        with self.assertRaisesRegex(ValueError, "no_action must be guard-passing"):
            build_rule_based_decision([_policy("no_action", passed=False)])


if __name__ == "__main__":
    unittest.main()
