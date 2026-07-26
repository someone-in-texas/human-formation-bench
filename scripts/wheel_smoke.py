#!/usr/bin/env python3
"""Install a built wheel into a clean environment and run the no-cost path."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise SystemExit(f"wheel not found: {wheel}")
    with tempfile.TemporaryDirectory(prefix="hfb-wheel-smoke-") as directory:
        root = Path(directory)
        subprocess.run(["python3", "-m", "venv", root / "venv"], check=True)
        python = root / "venv/bin/python"
        hfb = root / "venv/bin/hfb"
        subprocess.run([python, "-m", "pip", "install", str(wheel)], check=True)
        subprocess.run([hfb, "doctor"], check=True, cwd=root)
        subprocess.run([hfb, "validate"], check=True, cwd=root)
        subprocess.run(
            [
                hfb,
                "run",
                "--profile",
                "micro",
                "--model",
                "fake/formation-v1",
                "--max-samples",
                "1",
                "--output-root",
                root / "runs",
                "--hard-stop",
            ],
            check=True,
            cwd=root,
        )


if __name__ == "__main__":
    main()
