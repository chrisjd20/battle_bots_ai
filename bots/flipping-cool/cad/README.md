# Flipping Cool CAD

This folder contains the mechanical source files for `flipping-cool`.

## Source of truth

- `src/*.py` parametric scripts are authoritative.
- `generated/*` exports are derived outputs for inspection, sharing, and print
  prep.

## Current script

- `src/baseline_layout.py`: generates first-pass packaging envelopes from the
  locked baseline BOM.

## Generate outputs

From repo root:

```bash
.venv-cad/bin/python bots/flipping-cool/cad/src/baseline_layout.py
```

Generated files land in `bots/flipping-cool/cad/generated/`.
