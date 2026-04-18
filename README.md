# battle_bots_ai

Monorepo for **Plastic Antweight** combat robots (about **1 lb / 454 g or less**) and related work aligned with **SPARC** (Standardized Procedures for the Advancement of Robotic Combat). It holds software, PCB design, mechanical/CAD, 3D-printed parts, and docs for **multiple** bots and battle-bot accessories—not a single project.

## PCB design

**KiCad** is used for all PCB work. Shared footprints/symbols can live under `shared/kicad-libraries/`; per-bot or per-accessory boards sit under `bots/<name>/` or `accessories/<name>/` (often in a `pcb/` subfolder as projects grow).

`launch.sh` can open a KiCad project when present (see script for the expected path).

## KiCad + AI setup

- MCP config: `.cursor/mcp.json` (server name `kicad`)
- Launcher: `./launch.sh` (auto-detects one project, or pass explicit `.kicad_pro`)
- Workflow guide: `docs/hardware-workflow.md`
- Fabrication output location: `fab/`

Quick commands (after a KiCad project exists):

```bash
./launch.sh --check path/to/project.kicad_pro
kicad-cli sch erc path/to/project.kicad_sch
kicad-cli pcb drc path/to/project.kicad_pcb
```

## Repo layout (starter)

| Path | Purpose |
|------|---------|
| `bots/` | One folder per robot |
| `accessories/` | Tools, jigs, side projects, non-robot-specific hardware |
| `shared/kicad-libraries/` | Reusable KiCad symbols, footprints, 3D models |
| `shared/cad-templates/` | Reusable CAD starter files or templates |
| `shared/software-tools/` | Shared scripts, utilities, or small tools |
| `docs/reference/` | Rules, datasheets summaries, reference notes |
| `docs/build-notes/` | Build logs, BOMs, assembly notes |

Individual projects may add subfolders such as `pcb/`, `firmware/`, `software/`, `cad/`, `prints/`, and `docs/` as needed.

## Other docs

- Design notes and concepts: keep them inside each bot's `docs/` folder (example: `bots/flipping-cool/docs/`).
