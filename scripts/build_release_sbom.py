#!/usr/bin/env python3
"""Build and validate a reproducible SBOM from the locked wheel runtime."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_NAME = "human-formation-benchmark"
FORBIDDEN = {
    "cyclonedx-bom",
    "mkdocs",
    "mypy",
    "pytest",
    "ruff",
}


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("dist/sbom.json"))
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    output = args.output.resolve()
    if not wheel.is_file():
        raise SystemExit(f"wheel does not exist: {wheel}")
    uv = shutil.which("uv")
    cyclonedx = shutil.which("cyclonedx-py")
    if not uv or not cyclonedx:
        raise SystemExit("uv and cyclonedx-py must be available")

    with tempfile.TemporaryDirectory(prefix="hfb-sbom-") as temporary:
        root = Path(temporary)
        requirements = root / "runtime-requirements.txt"
        environment = root / "runtime"
        _run(
            uv,
            "--quiet",
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--output-file",
            str(requirements),
        )
        _run(uv, "--quiet", "venv", "--python", sys.executable, str(environment))
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        _run(uv, "--quiet", "pip", "sync", "--python", str(python), str(requirements))
        _run(
            uv,
            "--quiet",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            str(wheel),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        _run(
            cyclonedx,
            "environment",
            "--pyproject",
            "pyproject.toml",
            "--mc-type",
            "library",
            "--output-reproducible",
            "--validate",
            "--output-file",
            str(output),
            str(python),
        )

    payload = json.loads(output.read_text(encoding="utf-8"))
    component_names = [
        str(component.get("name", "")).casefold() for component in payload.get("components", [])
    ]
    unexpected = sorted(FORBIDDEN.intersection(component_names))
    if unexpected:
        raise SystemExit(f"development-only components found in release SBOM: {unexpected}")
    root = payload.get("metadata", {}).get("component", {})
    if str(root.get("name", "")).casefold() != PROJECT_NAME:
        raise SystemExit("release SBOM root component is not the project")
    duplicate_roots = sum(name == PROJECT_NAME for name in component_names)
    if duplicate_roots:
        raise SystemExit("release SBOM duplicates the project root in components")
    if payload.get("serialNumber") or payload.get("metadata", {}).get("timestamp"):
        raise SystemExit("release SBOM contains non-reproducible serial/timestamp fields")
    print(f"validated production-only SBOM with {len(component_names)} runtime components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
