#!/usr/bin/env python3
"""Use the same isolated core runtime for standalone source validation."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import main

if __name__ == "__main__":
    raise SystemExit(main(entry="validate_documents.py"))
