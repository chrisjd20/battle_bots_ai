#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
board_path="${1:-"$script_dir/flipping-cool.kicad_pcb"}"

if [[ ! -f "$board_path" ]]; then
  echo "PCB file not found: $board_path" >&2
  echo "Usage: $0 [path/to/board.kicad_pcb]" >&2
  exit 1
fi

board_path="$(realpath "$board_path")"

# If neither Wayland nor X11 is configured, try a common WSL2 X11 fallback.
if [[ -z "${WAYLAND_DISPLAY:-}" && -z "${DISPLAY:-}" ]]; then
  if [[ -f /etc/resolv.conf ]]; then
    xhost_ip="$(awk '/^nameserver / { print $2; exit }' /etc/resolv.conf)"
    if [[ -n "${xhost_ip:-}" ]]; then
      export DISPLAY="${xhost_ip}:0"
    fi
  fi
fi

if [[ -z "${WAYLAND_DISPLAY:-}" && -z "${DISPLAY:-}" ]]; then
  cat >&2 <<'EOF'
No GUI display detected in this Linux session.
For WSLg: run on Windows 11 with WSLg enabled.
For X11/VNC: start your X server/VNC server and set DISPLAY first.
EOF
  exit 1
fi

if command -v pcbnew >/dev/null 2>&1; then
  gui_cmd="pcbnew"
elif command -v kicad >/dev/null 2>&1; then
  gui_cmd="kicad"
else
  echo "KiCad GUI is not installed in this Linux environment." >&2
  echo "Install package(s) such as: sudo apt install kicad" >&2
  exit 1
fi

nohup "${gui_cmd}" "${board_path}" >/tmp/open_pcb_in_wsl_gui.log 2>&1 &
disown || true

echo "Launched Linux KiCad GUI (${gui_cmd}) for:"
echo "  ${board_path}"
echo "Log: /tmp/open_pcb_in_wsl_gui.log"
