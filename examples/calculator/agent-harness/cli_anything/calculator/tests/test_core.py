"""Unit tests for cli-anything-calculator core modules.

Tests use synthetic data — no external dependencies required.
"""

import json
import os
import sys
import tempfile

import pytest

# Ensure calculator source is on path
_CALC_SOURCE = os.environ.get("CALCULATOR_SOURCE_PATH", "/home/ubuntu/calculator")
if _CALC_SOURCE not in sys.path:
    sys.path.insert(0, _CALC_SOURCE)
os.environ["CALCULATOR_SOURCE_PATH"] = _CALC_SOURCE

# Ensure agent-harness is on path
_HARNESS = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _HARNESS not in sys.path:
    sys.path.insert(0, os.path.abspath(_HARNESS))


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


# ── project.py tests ────────────────────────────────────────────────

class TestProject:
    def test_create_project(self):
        from cli_anything.calculator.core.project import create_project
        proj = create_project(name="test-calc")
        assert proj["name"] == "test-calc"
        assert proj["version"] == "1.0.0"
        assert "state" in proj
        assert proj["state"]["display_value"] == "0"
        assert proj["state"]["memory"] == 0.0
        assert proj["state"]["history"] == []

    def test_create_project_with_file(self, tmp_dir):
        from cli_anything.calculator.core.project import create_project
        path = os.path.join(tmp_dir, "calc.json")
        proj = create_project(name="saved-calc", output_path=path)
        assert os.path.exists(path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["name"] == "saved-calc"

    def test_load_project(self, tmp_dir):
        from cli_anything.calculator.core.project import create_project, load_project
        path = os.path.join(tmp_dir, "calc.json")
        create_project(name="load-test", output_path=path)
        loaded = load_project(path)
        assert loaded["name"] == "load-test"

    def test_load_project_missing(self):
        from cli_anything.calculator.core.project import load_project
        with pytest.raises(FileNotFoundError):
            load_project("/nonexistent/path.json")

    def test_project_info(self):
        from cli_anything.calculator.core.project import create_project, project_info
        proj = create_project(name="info-test")
        info = project_info(proj)
        assert info["name"] == "info-test"
        assert info["history_count"] == 0
        assert info["memory"] == 0.0
        assert info["has_pending_operation"] is False

    def test_save_project(self, tmp_dir):
        from cli_anything.calculator.core.project import create_project, save_project
        proj = create_project(name="save-test")
        path = os.path.join(tmp_dir, "saved.json")
        result = save_project(proj, path)
        assert os.path.exists(path)
        assert result["saved"] == path
        assert result["size"] > 0


# ── compute.py tests ────────────────────────────────────────────────

class TestCompute:
    def _make_project(self):
        from cli_anything.calculator.core.project import create_project
        return create_project()

    def test_compute_add(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        result = compute_expression(proj, 10, "+", 5)
        assert result["result"] == 15
        assert "error" not in result

    def test_compute_subtract(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        result = compute_expression(proj, 10, "-", 3)
        assert result["result"] == 7

    def test_compute_multiply(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        result = compute_expression(proj, 6, "*", 7)
        assert result["result"] == 42

    def test_compute_divide(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        result = compute_expression(proj, 100, "/", 4)
        assert result["result"] == 25

    def test_compute_divide_by_zero(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        result = compute_expression(proj, 10, "/", 0)
        assert "error" in result

    def test_compute_updates_history(self):
        from cli_anything.calculator.core.compute import compute_expression
        proj = self._make_project()
        compute_expression(proj, 1, "+", 2)
        compute_expression(proj, 3, "*", 4)
        assert len(proj["state"]["history"]) == 2

    def test_memory_store_recall(self):
        from cli_anything.calculator.core.compute import memory_operation
        proj = self._make_project()
        memory_operation(proj, "store", 42.0)
        assert proj["state"]["memory"] == 42.0
        result = memory_operation(proj, "recall")
        assert result["memory"] == 42.0

    def test_memory_add_subtract(self):
        from cli_anything.calculator.core.compute import memory_operation
        proj = self._make_project()
        memory_operation(proj, "store", 10.0)
        memory_operation(proj, "add", 5.0)
        assert proj["state"]["memory"] == 15.0
        memory_operation(proj, "subtract", 3.0)
        assert proj["state"]["memory"] == 12.0

    def test_memory_clear(self):
        from cli_anything.calculator.core.compute import memory_operation
        proj = self._make_project()
        memory_operation(proj, "store", 99.0)
        memory_operation(proj, "clear")
        assert proj["state"]["memory"] == 0.0

    def test_get_history(self):
        from cli_anything.calculator.core.compute import compute_expression, get_history
        proj = self._make_project()
        compute_expression(proj, 2, "+", 3)
        history = get_history(proj)
        assert len(history) == 1
        assert history[0]["result"] == 5


# ── session.py tests ────────────────────────────────────────────────

class TestSession:
    def test_undo_redo(self):
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.session import Session
        from cli_anything.calculator.core.compute import compute_expression

        proj = create_project()
        session = Session(proj)

        # Perform calculation
        session.snapshot()
        compute_expression(proj, 5, "+", 3)
        assert proj["state"]["display_value"] == "8"

        # Undo
        result = session.undo()
        assert result["status"] == "undone"
        assert result["display"] == "0"

        # Redo
        result = session.redo()
        assert result["status"] == "redone"
        assert result["display"] == "8"

    def test_session_save(self, tmp_dir):
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.session import Session

        proj = create_project()
        path = os.path.join(tmp_dir, "session.json")
        session = Session(proj, path)
        result = session.save()
        assert os.path.exists(path)
        assert result["saved"] == path


# ── export.py tests ─────────────────────────────────────────────────

class TestExport:
    def _make_project_with_history(self):
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.compute import compute_expression
        proj = create_project()
        compute_expression(proj, 10, "+", 5)
        compute_expression(proj, 3, "*", 7)
        compute_expression(proj, 100, "/", 4)
        return proj

    def test_export_json(self, tmp_dir):
        from cli_anything.calculator.core.export import export_history
        proj = self._make_project_with_history()
        path = os.path.join(tmp_dir, "history.json")
        result = export_history(proj, path, fmt="json", overwrite=True)
        assert result["format"] == "json"
        assert result["entries"] == 3
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert len(data["history"]) == 3

    def test_export_csv(self, tmp_dir):
        from cli_anything.calculator.core.export import export_history
        proj = self._make_project_with_history()
        path = os.path.join(tmp_dir, "history.csv")
        result = export_history(proj, path, fmt="csv", overwrite=True)
        assert result["format"] == "csv"
        assert os.path.exists(path)
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 4  # header + 3 rows

    def test_export_txt(self, tmp_dir):
        from cli_anything.calculator.core.export import export_history
        proj = self._make_project_with_history()
        path = os.path.join(tmp_dir, "history.txt")
        result = export_history(proj, path, fmt="txt", overwrite=True)
        assert result["format"] == "txt"
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "Calculator History" in content

    def test_export_no_overwrite(self, tmp_dir):
        from cli_anything.calculator.core.export import export_history
        proj = self._make_project_with_history()
        path = os.path.join(tmp_dir, "existing.json")
        # Create existing file
        with open(path, "w") as f:
            f.write("{}")
        result = export_history(proj, path, fmt="json", overwrite=False)
        assert "error" in result
