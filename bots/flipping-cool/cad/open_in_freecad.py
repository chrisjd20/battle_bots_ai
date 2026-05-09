#!/usr/bin/env python3
"""
Run inside FreeCAD GUI — do not run with system python.

  freecad /path/to/bots/flipping-cool/cad/open_in_freecad.py

Loads generated/rev_a_assembly.step explicitly (CLI file open is unreliable).
"""

from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_STEP = os.path.join(_HERE, "generated", "rev_a_assembly.step")


def _fit_view() -> None:
    import FreeCADGui as Gui

    v = Gui.ActiveDocument.ActiveView if Gui.ActiveDocument else None
    if v is None:
        return
    v.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")


def main() -> None:
    import FreeCAD as App
    import Part

    if not os.path.isfile(_STEP):
        raise SystemExit(f"STEP not found. Generate first:\n  {_STEP}")

    # Prefer GUI path; freecadcmd has no Gui
    if not App.GuiUp:
        shape = Part.read(_STEP)
        print("STEP OK (no GUI). Volume:", shape.Volume)
        return

    import FreeCADGui as Gui
    import threading

    doc = App.newDocument("RevA_Layout")
    shape = Part.read(_STEP)
    obj = doc.addObject("Part::Feature", "RevA_Assembly")
    obj.Shape = shape
    doc.recompute()
    Gui.activeDocument().activeView().viewIsometric()
    # View is not always ready on first tick; stdlib only (no PySide coupling)
    threading.Timer(0.2, _fit_view).start()


# FreeCAD may execute this file without setting __name__ == "__main__"; always run.
main()
