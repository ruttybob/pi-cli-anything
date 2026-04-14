"""Calculator backend wrapper.

This module wraps the real calculator engine (calculator_engine.py) from the
GUI application. It handles finding the source code and importing the engine.

The calculator app is a required dependency — this CLI is useless without it.
"""

import os
import sys
import importlib
from typing import Optional


def find_calculator_source() -> str:
    """Find the calculator source directory.

    Checks:
    1. CALCULATOR_SOURCE_PATH environment variable
    2. Common locations

    Returns:
        Path to the calculator source directory.

    Raises:
        RuntimeError: If the calculator source cannot be found.
    """
    # Check environment variable
    env_path = os.environ.get("CALCULATOR_SOURCE_PATH", "")
    if env_path and os.path.isfile(os.path.join(env_path, "calculator_engine.py")):
        return env_path

    # Check common locations
    candidates = [
        os.path.expanduser("~/calculator"),
        "/home/ubuntu/calculator",
        os.path.join(os.getcwd(), "calculator"),
        os.getcwd(),
    ]

    for path in candidates:
        if os.path.isfile(os.path.join(path, "calculator_engine.py")):
            return path

    raise RuntimeError(
        "Calculator source not found. Set CALCULATOR_SOURCE_PATH to the directory "
        "containing calculator_engine.py, or run from the calculator source directory.\n"
        "Example: export CALCULATOR_SOURCE_PATH=/home/user/calculator"
    )


def get_engine_class():
    """Import and return the CalculatorEngine class from the real source.

    Returns:
        The CalculatorEngine class.

    Raises:
        RuntimeError: If the calculator source cannot be found.
        ImportError: If the engine module cannot be imported.
    """
    source_path = find_calculator_source()

    if source_path not in sys.path:
        sys.path.insert(0, source_path)

    # Force reimport if needed
    if "calculator_engine" in sys.modules:
        mod = sys.modules["calculator_engine"]
    else:
        mod = importlib.import_module("calculator_engine")

    return mod.CalculatorEngine


def create_engine():
    """Create a new CalculatorEngine instance.

    Returns:
        A new CalculatorEngine instance from the real source.
    """
    cls = get_engine_class()
    return cls()


def launch_gui() -> dict:
    """Launch the calculator GUI application.

    Returns:
        dict with launch status.
    """
    import subprocess

    source_path = find_calculator_source()
    gui_path = os.path.join(source_path, "calculator_gui.py")

    if not os.path.isfile(gui_path):
        return {"error": f"calculator_gui.py not found at {gui_path}"}

    proc = subprocess.Popen(
        [sys.executable, gui_path],
        cwd=source_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return {
        "status": "launched",
        "pid": proc.pid,
        "gui_path": gui_path,
    }
