#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP="$(readlink -f "${DIR}/generated/rev_a_assembly.step")"
PY="$(readlink -f "${DIR}/open_in_freecad.py")"

if [ ! -f "${STEP}" ]; then
    echo "Missing STEP: ${STEP}"
    echo "Generate:"
    echo "  .venv-cad/bin/python bots/flipping-cool/cad/src/rev_a_layout.py"
    exit 1
fi

if [ ! -f "${PY}" ]; then
    echo "Missing: ${PY}"
    exit 1
fi

echo "STEP: ${STEP}"
echo "Opening with FreeCAD startup script (CLI STEP open is unreliable in GUI):"
echo "  ${PY}"
echo ""

if command -v freecad >/dev/null 2>&1; then
    exec freecad "${PY}"
fi
if command -v FreeCAD >/dev/null 2>&1; then
    exec FreeCAD "${PY}"
fi

echo "Neither 'freecad' nor 'FreeCAD' found in PATH."
exit 1
