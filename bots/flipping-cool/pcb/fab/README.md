# Flipping Cool Rev A Fab Package

Generated from `../flipping-cool.kicad_pcb` with KiCad CLI 9.0.7.

## Fabrication Files

- `gerbers/`: copper, mask, paste, silkscreen, edge cuts, and Gerber job file.
- `drill/`: separate PTH/NPTH Excellon drill files plus drill-map PDFs.
- `flipping-cool-pos.csv`: board pick-and-place position export.
- `flipping-cool-top.png` / `flipping-cool-bottom.png`: quick visual renders.
- `reports/`: ERC and DRC reports used for release verification.

## Verification

- ERC: `0` errors, `0` warnings.
- PCB DRC, error severity: `0` violations, `0` unconnected pads.
- PCB DRC, all severities: one non-blocking `silk_over_copper` warning from
  the official KiCad `J22` wire strain-relief footprint. Gerbers were exported
  with `--subtract-soldermask`, so that silkscreen is clipped cleanly.

The schematic-parity report is included for traceability. Its warnings are for
unplaced optional growth/test footprints and extra mechanical mounting holes;
they are not required for the base receiver-driven bot PCB.
