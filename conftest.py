"""
Shared pytest configuration and fixtures for pi-cli-anything tests.

Centralizes sys.path setup so individual test files don't need to
manipulate the import path.
"""

import sys
from pathlib import Path

# Make scripts/ importable for all test modules
# (skill_generator.py, repl_skin.py, etc.)
SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
