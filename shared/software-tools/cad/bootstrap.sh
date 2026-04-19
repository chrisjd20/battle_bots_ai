#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-cad"
REQ_FILE="${ROOT_DIR}/shared/software-tools/cad/requirements.txt"

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${REQ_FILE}"

echo "CAD environment ready:"
echo "  Venv: ${VENV_DIR}"
echo "  Python: $("${VENV_DIR}/bin/python" --version)"
