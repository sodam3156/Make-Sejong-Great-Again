# Sejong observed-constraint evidence package

This package records official geometry coverage, historical signal timing vectors, and explicit exclusions for public probe samples. It is deliberately separate from `synthetic-v0` and cannot activate simulator parameters.

Committed data are compact, non-sensitive derived evidence. The original large ZIP/XLSX files remain outside Git; exact filenames, byte sizes, and SHA-256 values are stored in the JSON manifests.

Validation:

```bash
python scripts/validate_sejong_observed_constraints.py
```

Runtime activation requires a separate reviewed PR after exact simulator-approach/lane-link mapping and the missing field inputs listed in `sejong_observed_input_gate_20260731.json` are resolved.
