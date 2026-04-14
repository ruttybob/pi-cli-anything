"""Project management for calculator CLI harness.

Handles creating, saving, loading, and inspecting calculator projects (sessions).
A "project" is a JSON file storing the calculator's state including display,
memory, history, and pending operations.
"""

import json
import os
from datetime import datetime
from typing import Optional


def create_project(name: str = "calculator", output_path: Optional[str] = None) -> dict:
    """Create a new calculator project.

    Args:
        name: Project name.
        output_path: Optional path to save the project file.

    Returns:
        dict with project metadata and initial state.
    """
    project = {
        "name": name,
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat(),
        "modified": datetime.utcnow().isoformat(),
        "state": {
            "display_value": "0",
            "first_operand": None,
            "operator": None,
            "waiting_for_operand": False,
            "memory": 0.0,
            "history": [],
            "last_result": None,
        },
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(project, f, indent=2)

    return project


def load_project(path: str) -> dict:
    """Load a calculator project from a JSON file.

    Args:
        path: Path to the project JSON file.

    Returns:
        Project dict.

    Raises:
        FileNotFoundError: If the project file doesn't exist.
        json.JSONDecodeError: If the file is invalid JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Project file not found: {path}")

    with open(path, "r") as f:
        project = json.load(f)

    return project


def save_project(project: dict, path: str) -> dict:
    """Save a calculator project to a JSON file.

    Args:
        project: Project dict to save.
        path: Output path.

    Returns:
        dict with save metadata.
    """
    project["modified"] = datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(project, f, indent=2)

    return {"saved": path, "size": os.path.getsize(path)}


def project_info(project: dict) -> dict:
    """Get summary info about a calculator project.

    Args:
        project: Project dict.

    Returns:
        dict with project summary info.
    """
    state = project.get("state", {})
    history = state.get("history", [])

    return {
        "name": project.get("name", "unknown"),
        "version": project.get("version", "unknown"),
        "created": project.get("created", "unknown"),
        "modified": project.get("modified", "unknown"),
        "display_value": state.get("display_value", "0"),
        "memory": state.get("memory", 0.0),
        "history_count": len(history),
        "has_pending_operation": state.get("operator") is not None,
    }
