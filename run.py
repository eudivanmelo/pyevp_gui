#!/usr/bin/env python3
"""Local entrypoint for the pyevp_gui test application."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pyevp_gui.app import main


if __name__ == "__main__":
    raise SystemExit(main())
