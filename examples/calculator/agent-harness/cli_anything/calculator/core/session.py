"""Session management for calculator CLI harness.

Provides undo/redo support by maintaining a stack of project states.
Uses file locking for safe concurrent access to session files.
"""

import copy
import json
import os
import fcntl
from typing import Optional


class Session:
    """Stateful session with undo/redo support."""

    def __init__(self, project: dict, project_path: Optional[str] = None):
        self.project = project
        self.project_path = project_path
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self.modified: bool = False

    def snapshot(self):
        """Save current state to undo stack before a mutation."""
        self.undo_stack.append(copy.deepcopy(self.project["state"]))
        self.redo_stack.clear()
        self.modified = True

    def undo(self) -> dict:
        """Undo the last operation.

        Returns:
            dict with status and current state.
        """
        if not self.undo_stack:
            return {"status": "nothing_to_undo", "display": self.project["state"].get("display_value", "0")}

        self.redo_stack.append(copy.deepcopy(self.project["state"]))
        self.project["state"] = self.undo_stack.pop()
        self.modified = True

        return {
            "status": "undone",
            "display": self.project["state"].get("display_value", "0"),
            "undo_remaining": len(self.undo_stack),
            "redo_remaining": len(self.redo_stack),
        }

    def redo(self) -> dict:
        """Redo the last undone operation.

        Returns:
            dict with status and current state.
        """
        if not self.redo_stack:
            return {"status": "nothing_to_redo", "display": self.project["state"].get("display_value", "0")}

        self.undo_stack.append(copy.deepcopy(self.project["state"]))
        self.project["state"] = self.redo_stack.pop()
        self.modified = True

        return {
            "status": "redone",
            "display": self.project["state"].get("display_value", "0"),
            "undo_remaining": len(self.undo_stack),
            "redo_remaining": len(self.redo_stack),
        }

    def save(self, path: Optional[str] = None) -> dict:
        """Save session to file with locking.

        Args:
            path: Optional path override. Uses project_path if not specified.

        Returns:
            dict with save status.
        """
        path = path or self.project_path
        if not path:
            return {"error": "No save path specified"}

        return _locked_save_json(path, self.project)

    def status(self) -> dict:
        """Get current session status.

        Returns:
            dict with session info.
        """
        state = self.project.get("state", {})
        return {
            "project_name": self.project.get("name", "unknown"),
            "project_path": self.project_path,
            "display": state.get("display_value", "0"),
            "memory": state.get("memory", 0.0),
            "history_count": len(state.get("history", [])),
            "modified": self.modified,
            "undo_available": len(self.undo_stack),
            "redo_available": len(self.redo_stack),
        }


def _locked_save_json(path: str, data: dict) -> dict:
    """Save JSON with exclusive file locking.

    Uses the pattern from guides/session-locking.md:
    open "r+", lock, then truncate inside the lock.

    Args:
        path: File path to save to.
        data: Dict to serialize as JSON.

    Returns:
        dict with save status.
    """
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    # Create the file if it doesn't exist
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return {"saved": path, "size": os.path.getsize(path), "locked": True}

    # Open for read+write, lock, truncate, write
    with open(path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return {"saved": path, "size": os.path.getsize(path), "locked": True}
