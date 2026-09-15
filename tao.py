#!/usr/bin/env python3
"""Run tao from a source checkout without installing Python packages first."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / 'plugins/tao-dev/skills/tao-dev/scripts'))
from runtime import main

if __name__ == '__main__':
    raise SystemExit(main())
