"""Export module for calculator CLI harness.

Exports calculator data (history, session state) to various formats.
Uses the real calculator engine for any computation needed during export.
"""

import csv
import json
import os
from typing import Optional


def export_history(project: dict, output_path: str, fmt: str = "json",
                   overwrite: bool = False) -> dict:
    """Export calculation history to a file.

    Args:
        project: Project dict.
        output_path: Path for the output file.
        fmt: Output format ('json', 'csv', 'txt').
        overwrite: Whether to overwrite existing files.

    Returns:
        dict with export metadata.
    """
    if os.path.exists(output_path) and not overwrite:
        return {"error": f"File exists: {output_path}. Use --overwrite to replace."}

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    history = project.get("state", {}).get("history", [])

    if fmt == "json":
        _export_json(history, output_path)
    elif fmt == "csv":
        _export_csv(history, output_path)
    elif fmt == "txt":
        _export_txt(history, output_path)
    else:
        return {"error": f"Unsupported format: {fmt}. Use json, csv, or txt."}

    size = os.path.getsize(output_path)
    return {
        "output": output_path,
        "format": fmt,
        "entries": len(history),
        "file_size": size,
    }


def export_session(project: dict, output_path: str, overwrite: bool = False) -> dict:
    """Export the full session state to JSON.

    Args:
        project: Project dict.
        output_path: Path for the output file.
        overwrite: Whether to overwrite existing files.

    Returns:
        dict with export metadata.
    """
    if os.path.exists(output_path) and not overwrite:
        return {"error": f"File exists: {output_path}. Use --overwrite to replace."}

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(project, f, indent=2)

    size = os.path.getsize(output_path)
    return {
        "output": output_path,
        "format": "json",
        "file_size": size,
    }


def _export_json(history: list, path: str):
    """Export history as JSON."""
    with open(path, "w") as f:
        json.dump({"history": history, "count": len(history)}, f, indent=2)


def _export_csv(history: list, path: str):
    """Export history as CSV."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Expression", "Result", "Operand1", "Operator", "Operand2"])
        for i, entry in enumerate(history, 1):
            writer.writerow([
                i,
                entry.get("expression", ""),
                entry.get("result", ""),
                entry.get("operand1", ""),
                entry.get("operator", ""),
                entry.get("operand2", ""),
            ])


def _export_txt(history: list, path: str):
    """Export history as plain text."""
    with open(path, "w") as f:
        f.write("Calculator History\n")
        f.write("=" * 40 + "\n\n")
        for i, entry in enumerate(history, 1):
            f.write(f"{i}. {entry.get('expression', '')} {entry.get('result', '')}\n")
        f.write(f"\nTotal calculations: {len(history)}\n")
