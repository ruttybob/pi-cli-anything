"""Calculator Engine - Core computation logic for the calculator app.

This module contains the pure calculation logic, separated from the GUI.
It supports:
- Basic arithmetic: add, subtract, multiply, divide
- Memory operations: store, recall, add to memory, subtract from memory
- Percentage calculation
- Calculation history
- State management (current value, pending operation, etc.)

This is the "backend engine" that CLI harnesses can wrap.
"""

import json
import os
from typing import Optional


class CalculatorEngine:
    """Core calculator engine with state management."""

    def __init__(self):
        self.display_value: str = "0"
        self.first_operand: Optional[float] = None
        self.operator: Optional[str] = None
        self.waiting_for_operand: bool = False
        self.memory: float = 0.0
        self.history: list[dict] = []
        self.last_result: Optional[float] = None
        self._expression: str = ""

    def _state(self) -> dict:
        """Return current display state."""
        return {
            "display": self.display_value,
            "expression": self._expression,
            "memory": self.memory,
            "history_count": len(self.history),
        }

    def input_digit(self, digit: str) -> dict:
        """Input a digit (0-9)."""
        if self.waiting_for_operand:
            self.display_value = digit
            self.waiting_for_operand = False
        else:
            if self.display_value == "0":
                self.display_value = digit
            else:
                self.display_value += digit
        return self._state()

    def input_decimal(self) -> dict:
        """Input a decimal point."""
        if self.waiting_for_operand:
            self.display_value = "0."
            self.waiting_for_operand = False
        elif "." not in self.display_value:
            self.display_value += "."
        return self._state()

    def input_operator(self, op: str) -> dict:
        """Input an operator (+, -, *, /)."""
        current = float(self.display_value)

        if self.first_operand is not None and not self.waiting_for_operand:
            result = self._compute(self.first_operand, current, self.operator)
            self.display_value = self._format_number(result)
            self.first_operand = result
        else:
            self.first_operand = current

        self.operator = op
        self.waiting_for_operand = True

        op_symbols = {"+": "+", "-": "-", "*": "\u00d7", "/": "\u00f7"}
        self._expression = f"{self._format_number(self.first_operand)} {op_symbols.get(op, op)}"

        return self._state()

    def calculate(self) -> dict:
        """Perform the pending calculation (equals)."""
        if self.operator is None or self.first_operand is None:
            return self._state()

        current = float(self.display_value)

        try:
            result = self._compute(self.first_operand, current, self.operator)
        except ZeroDivisionError:
            self._expression = "Error: Division by zero"
            self.display_value = "Error"
            self.first_operand = None
            self.operator = None
            self.waiting_for_operand = True
            return self._state()

        op_symbols = {"+": "+", "-": "-", "*": "\u00d7", "/": "\u00f7"}
        expr = f"{self._format_number(self.first_operand)} {op_symbols.get(self.operator, self.operator)} {self._format_number(current)} ="

        self.history.append({
            "expression": expr,
            "result": result,
            "operand1": self.first_operand,
            "operator": self.operator,
            "operand2": current,
        })

        self.display_value = self._format_number(result)
        self._expression = expr
        self.last_result = result
        self.first_operand = None
        self.operator = None
        self.waiting_for_operand = True

        return self._state()

    def clear(self) -> dict:
        """Clear all state (C button)."""
        self.display_value = "0"
        self.first_operand = None
        self.operator = None
        self.waiting_for_operand = False
        self._expression = ""
        return self._state()

    def clear_entry(self) -> dict:
        """Clear current entry only (CE button)."""
        self.display_value = "0"
        return self._state()

    def backspace(self) -> dict:
        """Remove the last digit."""
        if len(self.display_value) > 1:
            self.display_value = self.display_value[:-1]
        else:
            self.display_value = "0"
        return self._state()

    def percentage(self) -> dict:
        """Calculate percentage of first operand."""
        current = float(self.display_value)
        if self.first_operand is not None:
            result = self.first_operand * (current / 100.0)
        else:
            result = current / 100.0
        self.display_value = self._format_number(result)
        return self._state()

    def memory_clear(self) -> dict:
        """Clear memory (MC)."""
        self.memory = 0.0
        return self._state()

    def memory_recall(self) -> dict:
        """Recall memory value (MR)."""
        self.display_value = self._format_number(self.memory)
        self.waiting_for_operand = True
        return self._state()

    def memory_add(self) -> dict:
        """Add display value to memory (M+)."""
        self.memory += float(self.display_value)
        self.waiting_for_operand = True
        return self._state()

    def memory_subtract(self) -> dict:
        """Subtract display value from memory (M-)."""
        self.memory -= float(self.display_value)
        self.waiting_for_operand = True
        return self._state()

    def get_history(self) -> list[dict]:
        """Get calculation history."""
        return list(self.history)

    def get_state(self) -> dict:
        """Get full engine state for serialization."""
        return {
            "display_value": self.display_value,
            "first_operand": self.first_operand,
            "operator": self.operator,
            "waiting_for_operand": self.waiting_for_operand,
            "memory": self.memory,
            "history": self.history,
            "last_result": self.last_result,
        }

    def load_state(self, state: dict) -> dict:
        """Load engine state from dict."""
        self.display_value = state.get("display_value", "0")
        self.first_operand = state.get("first_operand")
        self.operator = state.get("operator")
        self.waiting_for_operand = state.get("waiting_for_operand", False)
        self.memory = state.get("memory", 0.0)
        self.history = state.get("history", [])
        self.last_result = state.get("last_result")
        return self._state()

    def save_session(self, path: str) -> dict:
        """Save current session to a JSON file."""
        state = self.get_state()
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
        return {"saved": path, "state": state}

    def load_session(self, path: str) -> dict:
        """Load a session from a JSON file."""
        with open(path, "r") as f:
            state = json.load(f)
        self.load_state(state)
        return self._state()

    # --- Direct calculation API (for CLI use) ---

    def compute(self, a: float, op: str, b: float) -> dict:
        """Perform a direct calculation and record in history."""
        try:
            result = self._compute(a, b, op)
        except ZeroDivisionError:
            return {"error": "Division by zero", "expression": f"{a} {op} {b}"}

        op_symbols = {"+": "+", "-": "-", "*": "\u00d7", "/": "\u00f7"}
        expr = f"{self._format_number(a)} {op_symbols.get(op, op)} {self._format_number(b)} ="

        self.history.append({
            "expression": expr,
            "result": result,
            "operand1": a,
            "operator": op,
            "operand2": b,
        })

        self.display_value = self._format_number(result)
        self.last_result = result
        self._expression = expr

        return {
            "result": result,
            "expression": expr,
            "display": self.display_value,
        }

    @staticmethod
    def _compute(a: float, b: float, op: str) -> float:
        """Perform arithmetic operation."""
        if op == "+":
            return a + b
        elif op == "-":
            return a - b
        elif op == "*":
            return a * b
        elif op == "/":
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operator: {op}")

    @staticmethod
    def _format_number(value: float) -> str:
        """Format a number for display."""
        if value == int(value):
            return str(int(value))
        # Limit decimal places to avoid floating point noise
        formatted = f"{value:.10g}"
        return formatted
