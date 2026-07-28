"""Keep every consumer on the same verified fixture and OpenAPI contract."""
import json
from pathlib import Path

import jsonschema

from scripts.generate_contract_artifacts import ROOT, render_artifacts


def test_generated_contract_artifacts_are_in_sync():
    for path, expected in render_artifacts().items():
        assert path.read_text(encoding="utf-8") == expected, path.relative_to(ROOT)


def test_cached_run_matches_frozen_result_schema():
    schema = json.loads(
        (ROOT / "contracts" / "rainflow.schema.json").read_text(encoding="utf-8")
    )
    cached = json.loads(
        (ROOT / "backend" / "fixtures" / "cached_run.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(cached, schema)
