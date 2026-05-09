# Flipping Cool CAD

This folder contains the mechanical source files for `flipping-cool`.

## Source of truth

- `src/*.py` parametric scripts are authoritative.
- `generated/*` exports are derived outputs for inspection, sharing, and print
  prep.

## Current scripts

- `src/baseline_layout.py`: first-pass packaging envelopes from the BOM.
- `src/rev_a_layout.py`: Rev A assembly (motors, battery, servos, shafts).

## Generate outputs

From repo root:

```bash
.venv-cad/bin/python bots/flipping-cool/cad/src/baseline_layout.py
.venv-cad/bin/python bots/flipping-cool/cad/src/rev_a_layout.py
```

Generated files land in `bots/flipping-cool/cad/generated/`.

## View in FreeCAD

If you start FreeCAD from the application menu you get an **empty** "Unnamed"
document. You must **open the STEP file** or launch via the helper script.

From repo root:

```bash
./bots/flipping-cool/cad/view.sh
```

This runs `freecad` on `open_in_freecad.py`, which **imports the STEP with
`Part.read`** inside FreeCAD. Passing a `.step` path on the command line often
opens an empty document in the GUI, which is why the helper script exists.

If you still see a blank 3D view, check the **document tab** at the bottom:
select **`RevA_Layout`** (an older empty `Unnamed` tab may still be open).

**If the window is still blank:** use **File → Open** and choose:

`bots/flipping-cool/cad/generated/rev_a_assembly.step`

Then **View → Standard views → Fit all** (or press `V` then `B` in many
layouts).

**Windows FreeCAD + repo in WSL:** open the file via UNC path, for example
`\\wsl$\<distro>\home\...\battle_bots_ai\bots\flipping-cool\cad\generated\rev_a_assembly.step`
(substitute your distro name from `wsl -l -v`).
