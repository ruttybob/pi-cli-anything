"""E2E tests for cli-anything-calculator.

Tests the full pipeline including real calculator engine invocation
and CLI subprocess tests.
"""

import json
import os
import subprocess
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


# ── E2E: Real Engine Tests ──────────────────────────────────────────

class TestRealEngineE2E:
    """Tests that invoke the real calculator engine."""

    def test_multi_step_calculation(self, tmp_dir):
        """Workflow: Create project, perform 5 calculations, verify history, export CSV."""
        from cli_anything.calculator.core.project import create_project, save_project
        from cli_anything.calculator.core.compute import compute_expression, get_history
        from cli_anything.calculator.core.export import export_history

        # Create project
        proj_path = os.path.join(tmp_dir, "calc.json")
        proj = create_project(name="e2e-test", output_path=proj_path)

        # Perform 5 calculations
        compute_expression(proj, 10, "+", 5)     # 15
        compute_expression(proj, 3, "*", 7)      # 21
        compute_expression(proj, 100, "/", 4)    # 25
        compute_expression(proj, 50, "-", 18)    # 32
        compute_expression(proj, 2, "*", 2)      # 4

        # Verify history
        history = get_history(proj)
        assert len(history) == 5
        assert history[0]["result"] == 15
        assert history[1]["result"] == 21
        assert history[4]["result"] == 4

        # Export to CSV
        csv_path = os.path.join(tmp_dir, "history.csv")
        result = export_history(proj, csv_path, fmt="csv", overwrite=True)
        assert os.path.exists(csv_path)
        assert result["entries"] == 5
        assert result["file_size"] > 0

        # Verify CSV structure
        with open(csv_path) as f:
            lines = f.readlines()
        assert len(lines) == 6  # header + 5 rows
        assert "Expression" in lines[0]

        print(f"\n  CSV: {csv_path} ({result['file_size']} bytes)")

    def test_memory_pipeline(self, tmp_dir):
        """Workflow: Calculate, store in memory, verify."""
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.compute import compute_expression, memory_operation

        proj = create_project()

        # Calculate 10 + 5 = 15
        result = compute_expression(proj, 10, "+", 5)
        assert result["result"] == 15

        # Store result in memory
        memory_operation(proj, "store", 15.0)
        assert proj["state"]["memory"] == 15.0

        # Calculate 20 * 3 = 60
        result = compute_expression(proj, 20, "*", 3)
        assert result["result"] == 60

        # Recall memory — should still be 15
        recall = memory_operation(proj, "recall")
        assert recall["memory"] == 15.0

    def test_session_undo_redo_workflow(self, tmp_dir):
        """Workflow: Calculate, undo, redo, verify state consistency."""
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.session import Session
        from cli_anything.calculator.core.compute import compute_expression

        proj = create_project()
        session = Session(proj)

        # Calculate 5 + 3 = 8
        session.snapshot()
        compute_expression(proj, 5, "+", 3)
        assert proj["state"]["display_value"] == "8"

        # Calculate 10 * 2 = 20
        session.snapshot()
        compute_expression(proj, 10, "*", 2)
        assert proj["state"]["display_value"] == "20"

        # Undo to 8
        result = session.undo()
        assert result["display"] == "8"

        # Undo to 0
        result = session.undo()
        assert result["display"] == "0"

        # Redo to 8
        result = session.redo()
        assert result["display"] == "8"

    def test_export_all_formats(self, tmp_dir):
        """Verify export works for all supported formats."""
        from cli_anything.calculator.core.project import create_project
        from cli_anything.calculator.core.compute import compute_expression
        from cli_anything.calculator.core.export import export_history

        proj = create_project()
        compute_expression(proj, 42, "+", 0)

        for fmt in ("json", "csv", "txt"):
            path = os.path.join(tmp_dir, f"export.{fmt}")
            result = export_history(proj, path, fmt=fmt, overwrite=True)
            assert os.path.exists(path), f"Export file not created for {fmt}"
            assert result["file_size"] > 0, f"Export file empty for {fmt}"
            print(f"\n  {fmt.upper()}: {path} ({result['file_size']} bytes)")


# ── CLI Subprocess Tests ────────────────────────────────────────────

def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    import shutil

    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = name.replace("cli-anything-", "cli_anything.") + "." + name.split("-")[-1] + "_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


class TestCLISubprocess:
    """Test the installed CLI command via subprocess."""

    CLI_BASE = _resolve_cli("cli-anything-calculator")

    def _run(self, args, check=True):
        env = os.environ.copy()
        env["CALCULATOR_SOURCE_PATH"] = _CALC_SOURCE
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "calculator" in result.stdout.lower()

    def test_project_new_json(self, tmp_dir):
        out = os.path.join(tmp_dir, "test.json")
        result = self._run(["--json", "project", "new", "-o", out])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "created"
        assert os.path.exists(out)

    def test_calc_add_json(self, tmp_dir):
        proj = os.path.join(tmp_dir, "calc.json")
        self._run(["project", "new", "-o", proj])
        result = self._run(["--json", "--project", proj, "calc", "add", "10", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["result"] == 15

    def test_calc_multiply_json(self, tmp_dir):
        proj = os.path.join(tmp_dir, "calc.json")
        self._run(["project", "new", "-o", proj])
        result = self._run(["--json", "--project", proj, "calc", "multiply", "6", "7"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["result"] == 42

    def test_full_workflow(self, tmp_dir):
        """Full E2E: create project → calculate → export → verify."""
        proj = os.path.join(tmp_dir, "workflow.json")
        csv_out = os.path.join(tmp_dir, "history.csv")

        # Create project
        self._run(["project", "new", "-o", proj])
        assert os.path.exists(proj)

        # Calculate
        self._run(["--project", proj, "calc", "add", "10", "5"])
        self._run(["--project", proj, "calc", "multiply", "3", "7"])
        self._run(["--project", proj, "calc", "divide", "100", "4"])

        # Export history
        self._run(["--project", proj, "export", "history", csv_out, "-f", "csv", "--overwrite"])
        assert os.path.exists(csv_out)

        # Verify CSV
        with open(csv_out) as f:
            lines = f.readlines()
        assert len(lines) >= 2  # header + at least 1 row
        print(f"\n  Workflow CSV: {csv_out}")
