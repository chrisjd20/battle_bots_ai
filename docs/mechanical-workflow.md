# Mechanical CAD Workflow

This repo uses a local, script-first CAD workflow for automation:

- `FreeCAD` for manual inspection and occasional direct edits
- `build123d` / `CadQuery` Python scripts as source of truth

## Current Status

- `freecad` installed via apt
- repo-local CAD virtualenv at `.venv-cad`
- CAD MCP server configured in `.cursor/mcp.json` as `cad`

## Source-of-truth policy

- Authoritative CAD source: `bots/<name>/cad/src/*.py`
- Derived artifacts: `bots/<name>/cad/generated/*.step`, `*.stl`

## Day-to-day flow

1. Update parametric script in `cad/src/`.
2. Generate outputs into `cad/generated/`.
3. Inspect geometry in FreeCAD.
4. Iterate dimensions and regenerate outputs.
5. Use stable geometry to finalize BOM, clearances, and then electrical layout.

## Validation commands

From repo root:

```bash
./shared/software-tools/cad/bootstrap.sh
.venv-cad/bin/python bots/flipping-cool/cad/src/baseline_layout.py
freecad --version
```
