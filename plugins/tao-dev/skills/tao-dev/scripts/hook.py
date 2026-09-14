#!/usr/bin/env python3
"""Dependency-free hook entry; unconfigured projects remain untouched."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import hook_main

if __name__ == "__main__":
    raise SystemExit(hook_main())
