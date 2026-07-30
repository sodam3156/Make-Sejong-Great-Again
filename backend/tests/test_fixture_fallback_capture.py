"""Regression contract for the Day 3 fixture-fallback evidence path."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAPTURE_SCRIPT = ROOT / "scripts" / "capture_day3_evidence.py"


def test_fixture_capture_is_explicit_and_never_labelled_live():
    source = CAPTURE_SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)

    assert '"--mode"' in source
    assert 'choices=("live", "fixture")' in source
    assert '"counts_as_live_integration": not args.fixture_fallback' in source
    assert '"integration_path": (' in source
    assert '"fixture_fallback" if args.fixture_fallback else "live_api"' in source


def test_fixture_capture_forces_api_failure_and_audits_local_replay():
    source = CAPTURE_SCRIPT.read_text(encoding="utf-8")

    assert 'request.method == "POST"' in source
    assert 'parsed.path.rstrip("/") == "/api/simulations"' in source
    assert '"decision": "forced_fixture_fallback"' in source
    assert "status=503" in source
    assert '"fixture_fallback_http_503_observed"' in source
    assert '"fixture_result_source"' in source
    assert '"served_fixture_asset_matches_repo"' in source
    assert '"fixture_approval_sent_no_api_request"' in source
    assert '"fixture_recovery_panel_rendered"' in source
    assert '"all_seven_ui_states_captured"' in source
    assert '"minimum_three_minutes_elapsed"' in source
