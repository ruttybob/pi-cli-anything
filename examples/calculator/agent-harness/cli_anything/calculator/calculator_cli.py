"""CLI entry point for cli-anything-calculator.

Click-based CLI with REPL support for controlling the Simple Calculator
GUI application from the command line.

Usage:
    cli-anything-calculator                          # Enter REPL mode
    cli-anything-calculator project new -o calc.json # Create project
    cli-anything-calculator --project calc.json calc add 5 3
    cli-anything-calculator --json --project calc.json calc history
"""

import json
import os
import sys

import click

# Ensure calculator source is on path
_CALC_SOURCE = os.environ.get("CALCULATOR_SOURCE_PATH", "")
if not _CALC_SOURCE:
    # Auto-detect
    for candidate in [
        os.path.expanduser("~/calculator"),
        "/home/ubuntu/calculator",
    ]:
        if os.path.isfile(os.path.join(candidate, "calculator_engine.py")):
            _CALC_SOURCE = candidate
            break

if _CALC_SOURCE and _CALC_SOURCE not in sys.path:
    sys.path.insert(0, _CALC_SOURCE)
    os.environ["CALCULATOR_SOURCE_PATH"] = _CALC_SOURCE


# ── Global state ────────────────────────────────────────────────────
_project = None
_session = None
_json_mode = False


def _output(data: dict):
    """Output result in JSON or human-readable format."""
    if _json_mode:
        click.echo(json.dumps(data, indent=2))
    else:
        for key, value in data.items():
            click.echo(f"  {key}: {value}")


def _error_output(msg: str):
    """Output an error."""
    if _json_mode:
        click.echo(json.dumps({"error": msg}), err=True)
    else:
        click.echo(f"Error: {msg}", err=True)


def _load_project_if_needed(ctx):
    """Load the project from --project flag if set."""
    global _project, _session
    project_path = ctx.obj.get("project_path") if ctx.obj else None
    if project_path and _project is None:
        from cli_anything.calculator.core.project import load_project
        from cli_anything.calculator.core.session import Session
        _project = load_project(project_path)
        _session = Session(_project, project_path)


# ── Main CLI group ──────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--project", "-p", "project_path", default=None,
              help="Path to a calculator project JSON file.")
@click.option("--json", "use_json", is_flag=True, default=False,
              help="Output in JSON format for programmatic use.")
@click.pass_context
def cli(ctx, project_path, use_json):
    """cli-anything-calculator: CLI harness for the Simple Calculator.

    Control the calculator from the command line with full undo/redo,
    memory, history, and export support.
    """
    global _json_mode, _project, _session
    _json_mode = use_json

    ctx.ensure_object(dict)
    ctx.obj["project_path"] = project_path
    ctx.obj["json_mode"] = use_json

    if project_path:
        _load_project_if_needed(ctx)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl, project_path=project_path)


# ── Project commands ────────────────────────────────────────────────

@cli.group()
@click.pass_context
def project(ctx):
    """Project management commands."""
    pass


@project.command("new")
@click.option("-o", "--output", "output_path", required=True,
              help="Output path for the project JSON file.")
@click.option("-n", "--name", default="calculator", help="Project name.")
@click.pass_context
def project_new(ctx, output_path, name):
    """Create a new calculator project."""
    from cli_anything.calculator.core.project import create_project
    result = create_project(name=name, output_path=output_path)
    _output({"status": "created", "path": output_path, "name": name})


@project.command("info")
@click.pass_context
def project_info_cmd(ctx):
    """Show info about the current project."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded. Use --project <path> to load one.")
        return
    from cli_anything.calculator.core.project import project_info
    info = project_info(_project)
    _output(info)


@project.command("save")
@click.option("-o", "--output", "output_path", default=None,
              help="Output path (defaults to the loaded project path).")
@click.pass_context
def project_save(ctx, output_path):
    """Save the current project."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.project import save_project
    path = output_path or ctx.obj.get("project_path")
    if not path:
        _error_output("No save path specified. Use -o <path>.")
        return
    result = save_project(_project, path)
    _output(result)


# ── Calculation commands ────────────────────────────────────────────

@cli.group("calc")
@click.pass_context
def calc(ctx):
    """Calculation commands."""
    _load_project_if_needed(ctx)


@calc.command("add")
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.pass_context
def calc_add(ctx, a, b):
    """Add two numbers: a + b."""
    _do_calc(ctx, a, "+", b)


@calc.command("subtract")
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.pass_context
def calc_subtract(ctx, a, b):
    """Subtract two numbers: a - b."""
    _do_calc(ctx, a, "-", b)


@calc.command("multiply")
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.pass_context
def calc_multiply(ctx, a, b):
    """Multiply two numbers: a * b."""
    _do_calc(ctx, a, "*", b)


@calc.command("divide")
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.pass_context
def calc_divide(ctx, a, b):
    """Divide two numbers: a / b."""
    _do_calc(ctx, a, "/", b)


@calc.command("eval")
@click.argument("a", type=float)
@click.argument("op", type=click.Choice(["+", "-", "*", "/"]))
@click.argument("b", type=float)
@click.pass_context
def calc_eval(ctx, a, op, b):
    """Evaluate an expression: a op b."""
    _do_calc(ctx, a, op, b)


def _do_calc(ctx, a, op, b):
    """Perform a calculation and output the result."""
    global _project, _session
    if _project is None:
        # Create a temporary in-memory project
        from cli_anything.calculator.core.project import create_project
        _project = create_project()
        _session = None

    if _session:
        _session.snapshot()

    from cli_anything.calculator.core.compute import compute_expression
    result = compute_expression(_project, a, op, b)

    if "error" in result:
        _error_output(result["error"])
        return

    # Auto-save if project path is set
    if _session and _session.project_path:
        _session.save()

    _output(result)


@calc.command("history")
@click.option("--last", "-n", default=None, type=int,
              help="Show only the last N entries.")
@click.pass_context
def calc_history(ctx, last):
    """Show calculation history."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return

    from cli_anything.calculator.core.compute import get_history
    history = get_history(_project)

    if last:
        history = history[-last:]

    if _json_mode:
        click.echo(json.dumps({"history": history, "count": len(history)}, indent=2))
    else:
        if not history:
            click.echo("  No calculations in history.")
        else:
            for i, entry in enumerate(history, 1):
                click.echo(f"  {i}. {entry.get('expression', '')} {entry.get('result', '')}")


# ── Memory commands ─────────────────────────────────────────────────

@cli.group("memory")
@click.pass_context
def memory(ctx):
    """Memory operations."""
    _load_project_if_needed(ctx)


@memory.command("store")
@click.argument("value", type=float)
@click.pass_context
def memory_store(ctx, value):
    """Store a value in memory."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.compute import memory_operation
    result = memory_operation(_project, "store", value)
    _output(result)


@memory.command("recall")
@click.pass_context
def memory_recall(ctx):
    """Recall the value stored in memory."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.compute import memory_operation
    result = memory_operation(_project, "recall")
    _output(result)


@memory.command("add")
@click.argument("value", type=float)
@click.pass_context
def memory_add(ctx, value):
    """Add a value to memory."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.compute import memory_operation
    result = memory_operation(_project, "add", value)
    _output(result)


@memory.command("subtract")
@click.argument("value", type=float)
@click.pass_context
def memory_subtract(ctx, value):
    """Subtract a value from memory."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.compute import memory_operation
    result = memory_operation(_project, "subtract", value)
    _output(result)


@memory.command("clear")
@click.pass_context
def memory_clear(ctx):
    """Clear memory."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.compute import memory_operation
    result = memory_operation(_project, "clear")
    _output(result)


# ── Session commands ────────────────────────────────────────────────

@cli.group("session")
@click.pass_context
def session(ctx):
    """Session management commands."""
    _load_project_if_needed(ctx)


@session.command("status")
@click.pass_context
def session_status(ctx):
    """Show current session status."""
    _load_project_if_needed(ctx)
    if _session is None:
        _error_output("No active session. Load a project first.")
        return
    result = _session.status()
    _output(result)


@session.command("undo")
@click.pass_context
def session_undo(ctx):
    """Undo the last operation."""
    _load_project_if_needed(ctx)
    if _session is None:
        _error_output("No active session.")
        return
    result = _session.undo()
    _output(result)


@session.command("redo")
@click.pass_context
def session_redo(ctx):
    """Redo the last undone operation."""
    _load_project_if_needed(ctx)
    if _session is None:
        _error_output("No active session.")
        return
    result = _session.redo()
    _output(result)


# ── Export commands ──────────────────────────────────────────────────

@cli.group("export")
@click.pass_context
def export(ctx):
    """Export commands."""
    _load_project_if_needed(ctx)


@export.command("history")
@click.argument("output_path")
@click.option("-f", "--format", "fmt", default="json",
              type=click.Choice(["json", "csv", "txt"]),
              help="Output format.")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing files.")
@click.pass_context
def export_history(ctx, output_path, fmt, overwrite):
    """Export calculation history to a file."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.export import export_history as _export
    result = _export(_project, output_path, fmt=fmt, overwrite=overwrite)
    if "error" in result:
        _error_output(result["error"])
        return
    _output(result)


@export.command("session")
@click.argument("output_path")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing files.")
@click.pass_context
def export_session(ctx, output_path, overwrite):
    """Export the full session state to JSON."""
    _load_project_if_needed(ctx)
    if _project is None:
        _error_output("No project loaded.")
        return
    from cli_anything.calculator.core.export import export_session as _export_session
    result = _export_session(_project, output_path, overwrite=overwrite)
    if "error" in result:
        _error_output(result["error"])
        return
    _output(result)


# ── GUI launch command ──────────────────────────────────────────────

@cli.command("launch")
def launch_gui():
    """Launch the calculator GUI application."""
    from cli_anything.calculator.utils.calculator_backend import launch_gui as _launch
    result = _launch()
    _output(result)


# ── REPL command ────────────────────────────────────────────────────

@cli.command("repl", hidden=True)
@click.option("--project-path", default=None, help="Project path for REPL session.")
@click.pass_context
def repl(ctx, project_path):
    """Enter interactive REPL mode."""
    global _project, _session, _json_mode

    from cli_anything.calculator.utils.repl_skin import ReplSkin
    from cli_anything.calculator.core.project import create_project, load_project, save_project
    from cli_anything.calculator.core.session import Session
    from cli_anything.calculator.core.compute import compute_expression, memory_operation, get_history

    skin = ReplSkin("calculator", version="1.0.0")
    skin.print_banner()

    # Load or create project
    pp = project_path or (ctx.obj.get("project_path") if ctx.obj else None)
    if pp and os.path.exists(pp):
        _project = load_project(pp)
        skin.success(f"Loaded project: {pp}")
    elif pp:
        _project = create_project(output_path=pp)
        skin.success(f"Created new project: {pp}")
    else:
        _project = create_project()
        skin.info("Working with in-memory project (use 'save <path>' to persist)")

    _session = Session(_project, pp)

    commands = {
        "help": "Show this help message",
        "calc <a> <op> <b>": "Calculate expression (e.g., calc 5 + 3)",
        "history": "Show calculation history",
        "memory store <val>": "Store value in memory",
        "memory recall": "Recall memory value",
        "memory clear": "Clear memory",
        "undo": "Undo last operation",
        "redo": "Redo last undone operation",
        "status": "Show session status",
        "save [path]": "Save project",
        "export <path> [format]": "Export history (json/csv/txt)",
        "launch": "Launch the calculator GUI",
        "quit/exit": "Exit REPL",
    }

    try:
        pt_session = skin.create_prompt_session()
    except Exception:
        pt_session = None

    while True:
        try:
            project_name = _project.get("name", "calculator")
            modified = _session.modified if _session else False

            if pt_session:
                try:
                    from prompt_toolkit.formatted_text import FormattedText
                    tokens = skin.prompt_tokens(project_name=project_name, modified=modified)
                    line = pt_session.prompt(FormattedText(tokens), style=skin.get_prompt_style())
                except (EOFError, KeyboardInterrupt):
                    break
            else:
                prompt_str = skin.prompt(project_name=project_name, modified=modified)
                try:
                    line = input(prompt_str)
                except (EOFError, KeyboardInterrupt):
                    break

            line = line.strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ("quit", "exit", "q"):
                skin.print_goodbye()
                break

            elif cmd == "help":
                skin.help(commands)

            elif cmd == "calc":
                if len(parts) < 4:
                    skin.error("Usage: calc <a> <op> <b>  (e.g., calc 5 + 3)")
                    continue
                try:
                    a = float(parts[1])
                    op = parts[2]
                    b = float(parts[3])
                except ValueError:
                    skin.error("Invalid numbers. Usage: calc <a> <op> <b>")
                    continue

                if op not in ("+", "-", "*", "/"):
                    skin.error(f"Invalid operator '{op}'. Use +, -, *, /")
                    continue

                _session.snapshot()
                result = compute_expression(_project, a, op, b)
                if "error" in result:
                    skin.error(result["error"])
                else:
                    skin.success(f"{result['expression']} {result['result']}")

            elif cmd == "history":
                history = get_history(_project)
                if not history:
                    skin.info("No calculations in history.")
                else:
                    headers = ["#", "Expression", "Result"]
                    rows = [[str(i), e.get("expression", ""), str(e.get("result", ""))]
                            for i, e in enumerate(history, 1)]
                    skin.table(headers, rows)

            elif cmd == "memory":
                if len(parts) < 2:
                    skin.error("Usage: memory <store|recall|add|subtract|clear> [value]")
                    continue
                op = parts[1].lower()
                val = float(parts[2]) if len(parts) > 2 else None
                _session.snapshot()
                result = memory_operation(_project, op, val)
                if "error" in result:
                    skin.error(result["error"])
                else:
                    skin.success(f"Memory {op}: {result['memory']}")

            elif cmd == "undo":
                result = _session.undo()
                skin.info(f"Undo: {result['status']} (display: {result['display']})")

            elif cmd == "redo":
                result = _session.redo()
                skin.info(f"Redo: {result['status']} (display: {result['display']})")

            elif cmd == "status":
                status = _session.status()
                skin.status_block(
                    {k: str(v) for k, v in status.items()},
                    title="Session Status"
                )

            elif cmd == "save":
                path = parts[1] if len(parts) > 1 else pp
                if not path:
                    skin.error("No save path. Usage: save <path>")
                    continue
                result = save_project(_project, path)
                _session.project_path = path
                _session.modified = False
                skin.success(f"Saved to {result['saved']} ({result['size']} bytes)")

            elif cmd == "export":
                if len(parts) < 2:
                    skin.error("Usage: export <path> [json|csv|txt]")
                    continue
                from cli_anything.calculator.core.export import export_history as _exp_hist
                exp_path = parts[1]
                fmt = parts[2] if len(parts) > 2 else "json"
                result = _exp_hist(_project, exp_path, fmt=fmt, overwrite=True)
                if "error" in result:
                    skin.error(result["error"])
                else:
                    skin.success(f"Exported {result['entries']} entries to {result['output']} ({result['format']})")

            elif cmd == "launch":
                from cli_anything.calculator.utils.calculator_backend import launch_gui as _launch
                result = _launch()
                if "error" in result:
                    skin.error(result["error"])
                else:
                    skin.success(f"Calculator GUI launched (PID: {result['pid']})")

            else:
                skin.warning(f"Unknown command: {cmd}. Type 'help' for available commands.")

        except Exception as e:
            skin.error(f"Error: {e}")


if __name__ == "__main__":
    cli()
