"""Computation module for calculator CLI harness.

Wraps the calculator engine to provide stateful computation through
the CLI. Supports direct calculations, chained operations, and
interaction with the calculator's memory system.
"""

import sys
import os

# Add calculator source to path so we can import the engine
_CALC_SOURCE = os.environ.get("CALCULATOR_SOURCE_PATH", "")
if _CALC_SOURCE and _CALC_SOURCE not in sys.path:
    sys.path.insert(0, _CALC_SOURCE)


def get_engine(project: dict):
    """Create a CalculatorEngine and load project state into it.

    Args:
        project: Project dict with 'state' key.

    Returns:
        CalculatorEngine instance with loaded state.
    """
    from calculator_engine import CalculatorEngine

    engine = CalculatorEngine()
    state = project.get("state", {})
    engine.load_state(state)
    return engine


def compute_expression(project: dict, a: float, op: str, b: float) -> dict:
    """Perform a calculation using the real calculator engine.

    This invokes the REAL calculator engine — not a reimplementation.

    Args:
        project: Project dict.
        a: First operand.
        op: Operator (+, -, *, /).
        b: Second operand.

    Returns:
        dict with result, updated project state.
    """
    engine = get_engine(project)
    result = engine.compute(a, op, b)

    if "error" in result:
        return result

    # Update project state
    project["state"] = engine.get_state()

    return {
        "result": result["result"],
        "expression": result["expression"],
        "display": result["display"],
        "history_count": len(engine.history),
    }


def chain_calculate(project: dict, value: float, op: str) -> dict:
    """Chain a calculation using the last result.

    Args:
        project: Project dict.
        value: The second operand.
        op: Operator to apply.

    Returns:
        dict with result.
    """
    engine = get_engine(project)
    last = engine.last_result
    if last is None:
        last = float(engine.display_value) if engine.display_value != "Error" else 0.0

    return compute_expression(project, last, op, value)


def memory_operation(project: dict, operation: str, value: float = None) -> dict:
    """Perform a memory operation on the calculator.

    Args:
        project: Project dict.
        operation: One of 'store', 'recall', 'add', 'subtract', 'clear'.
        value: Value for store/add/subtract (uses display if None).

    Returns:
        dict with memory state.
    """
    engine = get_engine(project)

    if operation == "store":
        if value is not None:
            engine.memory = value
        else:
            engine.memory = float(engine.display_value) if engine.display_value != "Error" else 0.0
    elif operation == "recall":
        engine.memory_recall()
    elif operation == "add":
        if value is not None:
            engine.memory += value
        else:
            engine.memory_add()
    elif operation == "subtract":
        if value is not None:
            engine.memory -= value
        else:
            engine.memory_subtract()
    elif operation == "clear":
        engine.memory_clear()
    else:
        return {"error": f"Unknown memory operation: {operation}"}

    project["state"] = engine.get_state()

    return {
        "operation": operation,
        "memory": engine.memory,
        "display": engine.display_value,
    }


def get_history(project: dict) -> list:
    """Get calculation history from project.

    Args:
        project: Project dict.

    Returns:
        List of history entries.
    """
    engine = get_engine(project)
    return engine.get_history()
