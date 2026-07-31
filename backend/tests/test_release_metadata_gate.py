"""Static gates for release commit/tag provenance in the Windows bundle."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts" / "build_windows.ps1"
RUNBOOK = ROOT / "docs" / "RUNBOOK.md"


def test_windows_build_records_and_checks_release_tag_commit():
    script = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert '[string]$ReleaseTag = ""' in script
    assert 'git rev-parse "$ReleaseTag^{commit}"' in script
    assert "$ReleaseTagCommit -ne $SourceCommit" in script
    assert '"RELEASE-METADATA.json"' in script
    assert "source_commit_sha = $SourceCommit" in script
    assert "release_tag_commit_sha = $ReleaseTagCommit" in script


def test_runbook_documents_release_metadata_and_tagged_build():
    runbook = RUNBOOK.read_text(encoding="utf-8")

    release_tags = re.findall(
        r"-ReleaseTag (v[0-9A-Za-z][0-9A-Za-z._-]+)",
        runbook,
    )
    assert len(release_tags) == 1
    assert f"git tag -a {release_tags[0]}" in runbook
    assert "`RELEASE-METADATA.json`" in runbook
