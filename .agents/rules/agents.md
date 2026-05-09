---
trigger: always_on
---

# Repo

- **What**: Multiple Plastic Antweight / SPARC-oriented combat robots **and** accessories—software, firmware, PCBs, CAD, 3D prints, documentation.
- **PCB**: KiCad (`.kicad_pro`, schematics, layouts). Boards live per project under `bots/<name>/` or `accessories/<name>/`; reusable symbols, footprints, and 3D models under `shared/kicad-libraries/`.
- **Where to put work**: `bots/<robot-name>/` · `accessories/<project-name>/` · `shared/` (libraries, templates, cross-project tools) · `docs/` (reference / build notes). Pick the smallest folder that fits; avoid unrelated files at repo root except top-level specs or launch helpers.
- **Changes**: Keep structure consistent with the README; put reusable pieces in `shared/` instead of duplicating under every bot.

# KiCad

- **Paths**: Primary projects as `*.kicad_pro`, `*.kicad_sch`, `*.kicad_pcb` under `bots/<name>/` or `accessories/<name>/` (often `pcb/`). Shared symbols, footprints, 3D models → `shared/kicad-libraries/`. Launch KiCad UI via `launch.sh` (repo root). If no project exists yet, create it in the project folder before ERC / DRC / export workflows.
- **Source of truth**: `.kicad_pro`, `.kicad_sch`, `.kicad_pcb` are authoritative for electrical and board state. Fabrication and export outputs are derived unless documented otherwise. Imported archives, snapshots, vendor exports, and legacy sources are read-only reference unless the task explicitly requires converting or updating them.
- **Environment**: Prefer KiCad 9.x with `kicad`, `kicad-cli`, and Python `pcbnew`. Use project-local KiCad MCP from `.cursor/mcp.json`. On WSL/WSLg, prefer existing display variables for GUI; use `DISPLAY=:0` only as fallback. Freerouting (autoroute) may rely on Docker/Podman/Java—do not assume it is installed.
- **Default flow**: Schematic edits → ERC → sync schematic to board → placement and routing → DRC → fabrication/export outputs. If work on a task is import-first for this repo, document deviations before changing authoritative source files.
- **Guardrails**: Do not overwrite or regenerate authoritative KiCad sources unless requested. Temporary exports (`*.dsn`, `*.ses`, plots, cache) are not source-of-truth. Preserve naming, stackup, and constraint intent from project files or notes. Scope changes to the requested task; update docs when introducing new workflow steps. Do not modify unrelated bots or accessories while working on one project.

