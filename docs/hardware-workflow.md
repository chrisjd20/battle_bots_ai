# Hardware Workflow

This repo is configured as a reusable KiCad + AI workspace for multiple hardware projects.

For script-first mechanical CAD setup, see `docs/mechanical-workflow.md`.

## Current Status

- KiCad tooling is installed (`kicad`, `kicad-cli`, `pcbnew` import).
- Project-local MCP config exists at `.cursor/mcp.json`.
- `launch.sh` can auto-detect a single `*.kicad_pro` or accept an explicit project path.
- No `*.kicad_pro` file is currently tracked in this repo.

## Known Gaps

- Until a KiCad project file exists, ERC/DRC/export commands cannot run on this repo.
- Docker is referenced from Windows-side Docker Desktop but is not currently available inside this WSL distro.

## Intended Day-to-Day Flow

1. Create or open a KiCad project under `bots/<name>/...` or `accessories/<name>/...`.
2. Edit schematic, then run ERC.
3. Sync schematic to PCB.
4. Place components and route.
5. Run DRC.
6. Export fabrication outputs into `fab/<project>/`.

## Validation Commands

Use these from repo root after a project exists:

```bash
./launch.sh --check path/to/project.kicad_pro
./launch.sh path/to/project.kicad_pro
kicad-cli sch erc path/to/project.kicad_sch
kicad-cli pcb drc path/to/project.kicad_pcb
python3 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
```

MCP smoke check:

```bash
LOG_LEVEL=info KICAD_PYTHON=/usr/bin/python3 PYTHONPATH=/usr/lib/python3/dist-packages timeout 8s node /home/admin/github/lora-low-power-surveillance/tools/KiCAD-MCP-Server/dist/index.js
```
