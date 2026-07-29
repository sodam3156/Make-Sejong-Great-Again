"""End-to-end synchronization guard for the QA v2 demo freeze."""
from __future__ import annotations

import hashlib
import json
import subprocess

from fastapi.testclient import TestClient

from backend.app import main as backend_main
from backend.app.main import result_checksum
from backend.app.storage import RunStore
from scripts.generate_contract_artifacts import ROOT, SOURCE_FILES


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _policy(run: dict, policy_id: str) -> dict:
    return next(
        policy for policy in run["policies"]
        if policy["policy_id"] == policy_id
    )


def test_five_live_api_runs_match_frozen_run_checksum_and_values(
    tmp_path,
    monkeypatch,
):
    fixture = _load("backend/fixtures/demo_run.json")
    expected_checksum = fixture["reproducibility"]["result_checksum"]
    expected_policies = fixture["policies"]
    monkeypatch.setattr(backend_main, "STORE", RunStore(tmp_path / "logs"))
    backend_main.RUNS.clear()
    client = TestClient(backend_main.app)

    for _ in range(5):
        created = client.post(
            "/api/simulations",
            json={
                "scenario_id": "rain_spillback_a",
                "seed": 42,
                "force_source": "live_simulation",
            },
        )
        assert created.status_code == 200
        response = client.get(created.json()["url"])
        assert response.status_code == 200
        live = response.json()
        assert live["reproducibility"]["result_checksum"] == expected_checksum
        assert result_checksum(live) == expected_checksum
        assert [
            {
                "policy_id": policy["policy_id"],
                "candidate_hash": policy["candidate_hash"],
                "kpi": policy["kpi"],
                "extra": policy["extra"],
                "delta_vs_no_action": policy["delta_vs_no_action"],
            }
            for policy in live["policies"]
        ] == [
            {
                "policy_id": policy["policy_id"],
                "candidate_hash": policy["candidate_hash"],
                "kpi": policy["kpi"],
                "extra": policy["extra"],
                "delta_vs_no_action": policy["delta_vs_no_action"],
            }
            for policy in expected_policies
        ]


def test_fixture_script_screen_and_manifest_share_one_source_run():
    fixture = _load("backend/fixtures/demo_run.json")
    manifest = _load("docs/evidence/demo_freeze_20260729.json")
    script = (ROOT / "docs/16_DEMO_SCRIPT.md").read_text(encoding="utf-8")
    screen = (ROOT / "frontend/demo_run.js").read_text(encoding="utf-8")

    reproducibility = fixture["reproducibility"]
    assert manifest["source"]["run_id"] == reproducibility["source_live_run_id"]
    assert manifest["source"]["result_checksum"] == reproducibility["result_checksum"]
    assert reproducibility["result_checksum"] in script
    assert reproducibility["source_live_run_id"] in script
    assert screen == (
        "window.DEMO_RUN = "
        + json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True)
        + ";\n"
    )


def test_manifest_hashes_every_frozen_artifact():
    manifest = _load("docs/evidence/demo_freeze_20260729.json")

    for relative, expected in manifest["artifacts"].items():
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert hashlib.sha256(content.encode("utf-8")).hexdigest() == expected


def test_seed_matrix_covers_a_and_b_for_ten_seeds():
    matrix = _load("docs/evidence/demo_kpi_seed_matrix_20260729.json")

    assert matrix["dataset_id"] == "synthetic-v0"
    assert matrix["provisional"] is True
    assert "실제 세종 성과" in matrix["interpretation_limit"]
    assert set(matrix["scenarios"]) == {
        "rain_spillback_a",
        "rain_spillback_b",
    }
    for scenario in matrix["scenarios"].values():
        assert [run["seed"] for run in scenario["runs"]] == list(range(1, 11))
        assert scenario["guard_failure_seeds"] == []
        assert set(scenario["policy_distribution"]) == {
            "no_action",
            "fixed_metering",
            "corridor_gating",
        }
        for policy in scenario["policy_distribution"].values():
            assert set(policy["kpi_distribution"]) == {
                "spillback_time_sec",
                "recovery_time_sec",
                "total_travel_time_sec",
                "worst_approach_delay_sec",
            }
            assert policy["guard_failed_seed_count"] == len(
                policy["guard_failure_seeds"]
            )
            assert policy["recovery_unobserved_seed_count"] == len(
                policy["recovery_unobserved_seeds"]
            )


def test_presentation_paths_exclude_qa_banned_numbers_and_terms():
    paths = (
        "docs/16_DEMO_SCRIPT.md",
        "backend/README.md",
        "frontend/index.html",
        "frontend/demo_run.js",
        "backend/fixtures/demo_run.json",
        "backend/fixtures/cached_run.json",
    )
    text = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in paths
    )
    banned = (
        "1240초",
        "1,240초",
        "51840",
        "44900",
        "−71",
        "-71.0%",
        "−13.4",
        "-13.4%",
        "우회 전가 지체는 95초",
        "diversion_delay_sec 95",
        '"diversion_delay_sec": 95',
        "0.87",
        "SAFETY_TTC_DEGRADED",
    )

    assert all(value not in text for value in banned)


def test_frozen_git_sha_is_latest_commit_touching_source_files():
    meta = _load("backend/fixtures/demo_freeze_meta.json")
    current = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", *SOURCE_FILES],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert meta["git_commit_sha"] == current
