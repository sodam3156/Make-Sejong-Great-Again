"""Static regression gates for the dependency-free live frontend adapter."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_HTML = ROOT / "frontend" / "index.html"


def test_live_approval_refetches_applied_run_before_recovery_render():
    html = FRONTEND_HTML.read_text(encoding="utf-8")

    assert "function refreshLiveRun()" in html
    assert "'/api/simulations/' + DATA.run_id" in html
    assert "DATA = synthesizeDecisionSteps(updatedRun);" in html
    assert "return refreshLiveRun().then(function ()" in html
    assert "render();" in html


def test_live_mode_footer_does_not_claim_fixture_replay():
    html = FRONTEND_HTML.read_text(encoding="utf-8")

    assert 'id="run-mode-note"' in html
    assert "로컬 백엔드가 방금 계산하고 저장한 결과" in html
    assert "mode === 'live'" in html
