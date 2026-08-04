"""Frozen RainFlow policy catalogue and deterministic metering rules."""
from __future__ import annotations

from typing import Final

POLICIES: Final[tuple[str, ...]] = (
    "no_action",
    "fixed_metering",
    "corridor_gating",
)

POLICY_LABELS: Final[dict[str, str]] = {
    "no_action": "무대응",
    "fixed_metering": "고정 미터링",
    "corridor_gating": "연속 게이팅",
}

POLICY_VERSION: Final[str] = "rainflow-policy-v1"


def metering_factors(
    policy_id: str,
    *,
    in_rain: bool,
    link_occupancy: dict[str, float],
    approaches: tuple[str, ...] | list[str],
) -> dict[str, float]:
    """Return deterministic per-approach discharge multipliers."""
    if policy_id not in POLICIES:
        raise ValueError(f"unknown policy_id: {policy_id}")

    meter = {approach: 1.0 for approach in approaches}
    if policy_id == "fixed_metering" and in_rain:
        # Educational fairness violation: fixed suppression burdens side entries.
        meter["R2_S"] = 0.45
        meter["R1_W"] = 0.45
    elif policy_id == "corridor_gating":
        # Gate all entries feeding the same constrained link proportionally.
        for link_id, upstreams in (
            ("L23", ("R2_N", "R2_S")),
            ("L12", ("R1_N", "R1_W")),
        ):
            occupancy = link_occupancy[link_id]
            if occupancy > 0.80:
                factor = max(0.35, 1.0 - (occupancy - 0.80) / 0.20 * 0.65)
                for approach in upstreams:
                    meter[approach] = min(meter[approach], factor)
    return meter

