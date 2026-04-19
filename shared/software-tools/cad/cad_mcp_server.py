#!/usr/bin/env python3
"""MCP server for local CAD automation tasks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP


def _repo_root() -> Path:
    value = os.environ.get("CAD_REPO_ROOT")
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[3]


def _cad_python() -> Path:
    value = os.environ.get("CAD_PYTHON")
    if value:
        return Path(value).resolve()
    return _repo_root() / ".venv-cad" / "bin" / "python"


def _resolve_inside_repo(path_str: str) -> Path:
    repo = _repo_root()
    path = Path(path_str)
    resolved = path.resolve() if path.is_absolute() else (repo / path).resolve()
    if repo not in resolved.parents and resolved != repo:
        raise ValueError(f"Path must be inside repo: {resolved}")
    return resolved


mcp = FastMCP("cad")


@mcp.tool()
def cad_environment() -> dict:
    """Return local CAD tool status and versions."""
    freecad = subprocess.run(
        ["freecad", "--version"], capture_output=True, text=True, check=False
    )
    py = subprocess.run(
        [_cad_python(), "--version"], capture_output=True, text=True, check=False
    )
    return {
        "repo_root": str(_repo_root()),
        "cad_python": str(_cad_python()),
        "cad_python_exists": _cad_python().exists(),
        "cad_python_version": py.stdout.strip() or py.stderr.strip(),
        "freecad_available": freecad.returncode == 0,
        "freecad_version": freecad.stdout.strip() or freecad.stderr.strip(),
    }


@mcp.tool()
def run_cad_script(script_path: str, args: list[str] | None = None) -> dict:
    """Run a Python CAD script inside the repo virtualenv."""
    script = _resolve_inside_repo(script_path)
    if not script.exists():
        raise ValueError(f"Script does not exist: {script}")

    cmd = [str(_cad_python()), str(script), *(args or [])]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
