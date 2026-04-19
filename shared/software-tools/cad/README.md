# CAD Automation Tooling

This folder holds the local CAD automation stack used by this repo.

## Tool choices

- `FreeCAD`: local GUI inspection and manual checks
- `build123d` / `CadQuery`: source-of-truth parametric modeling in Python
- `MCP (optional)`: tool entrypoints to run CAD scripts from Cursor

## Bootstrap

From repo root:

```bash
./shared/software-tools/cad/bootstrap.sh
```

This creates `.venv-cad` and installs packages from
`shared/software-tools/cad/requirements.txt`.

## Run a CAD model script

```bash
.venv-cad/bin/python bots/flipping-cool/cad/src/baseline_layout.py
```

## MCP server

The CAD MCP server lives at:

- `shared/software-tools/cad/cad_mcp_server.py`

When configured in `.cursor/mcp.json`, it exposes:

- `cad_environment`
- `run_cad_script`

## Source-of-truth policy

- Python CAD scripts in `cad/src/` are authoritative.
- Generated `STEP` / `STL` files under `cad/generated/` are derived artifacts.
