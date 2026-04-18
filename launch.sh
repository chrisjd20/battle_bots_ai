#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "Usage: $0 [--check] [path/to/project.kicad_pro]"
  echo
  echo "If no project path is provided, the script auto-detects *.kicad_pro files in this repo."
  echo "Use --check to validate resolution without launching KiCad."
}

CHECK_ONLY=0
PROJECT_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -n "$PROJECT_ARG" ]]; then
        echo "Only one project path argument is supported." >&2
        usage >&2
        exit 2
      fi
      PROJECT_ARG="$1"
      shift
      ;;
  esac
done

if ! command -v kicad >/dev/null 2>&1; then
  echo "KiCad executable not found in PATH. Install KiCad and retry." >&2
  exit 1
fi

PROJECT_FILE=""

if [[ -n "$PROJECT_ARG" ]]; then
  if [[ "$PROJECT_ARG" = /* ]]; then
    PROJECT_FILE="$PROJECT_ARG"
  else
    PROJECT_FILE="$SCRIPT_DIR/$PROJECT_ARG"
  fi
elif [[ -n "${KICAD_PROJECT:-}" ]]; then
  if [[ "${KICAD_PROJECT}" = /* ]]; then
    PROJECT_FILE="${KICAD_PROJECT}"
  else
    PROJECT_FILE="$SCRIPT_DIR/${KICAD_PROJECT}"
  fi
else
  shopt -s globstar nullglob
  projects=()
  for candidate in "$SCRIPT_DIR"/**/*.kicad_pro; do
    [[ "$candidate" == *"/.git/"* ]] && continue
    projects+=("$candidate")
  done
  shopt -u globstar nullglob

  if [[ ${#projects[@]} -eq 1 ]]; then
    PROJECT_FILE="${projects[0]}"
  elif [[ ${#projects[@]} -eq 0 ]]; then
    echo "No KiCad project (*.kicad_pro) found under: $SCRIPT_DIR" >&2
    echo "Pass a project path explicitly: $0 path/to/project.kicad_pro" >&2
    exit 2
  else
    echo "Multiple KiCad projects found. Pass one explicitly:" >&2
    for project in "${projects[@]}"; do
      echo "  - ${project#$SCRIPT_DIR/}" >&2
    done
    exit 2
  fi
fi

if [[ ! -f "$PROJECT_FILE" ]]; then
  echo "KiCad project not found: $PROJECT_FILE" >&2
  exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  echo "Launch check passed."
  echo "Resolved project: $PROJECT_FILE"
  exit 0
fi

# WSLg usually provides WAYLAND_DISPLAY. Older X11 setups often need DISPLAY=:0.
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  export DISPLAY=:0
fi

LOG_FILE="${KICAD_LAUNCH_LOG:-$(mktemp "/tmp/kicad-launch.XXXXXX.log")}"
nohup kicad "$PROJECT_FILE" >"$LOG_FILE" 2>&1 &
KICAD_PID=$!

echo "Launching KiCad for: $PROJECT_FILE"
echo "PID: $KICAD_PID"
echo "Log: $LOG_FILE"
