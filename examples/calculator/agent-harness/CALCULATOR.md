# CALCULATOR.md — Software-Specific SOP

## Software Overview

The Simple Calculator is a Python tkinter GUI application providing:
- Standard arithmetic operations (+, -, *, /)
- Memory functions (M+, M-, MR, MC)
- Calculation history
- Percentage and backspace

## Backend Engine

- **Engine file:** `calculator_engine.py`
- **Class:** `CalculatorEngine`
- **No external CLI tool** — the engine is a Python class, not a subprocess
- **State model:** JSON-serializable dict with display, operands, memory, history

## GUI-to-CLI Mapping

| GUI Action | Engine Method | CLI Command |
|-----------|---------------|-------------|
| Click digit | `input_digit()` | (via REPL direct input) |
| Click operator | `input_operator()` | `calc eval <a> <op> <b>` |
| Click = | `calculate()` | `calc eval <a> <op> <b>` |
| Click C | `clear()` | (implicit in new project) |
| Click MC | `memory_clear()` | `memory clear` |
| Click MR | `memory_recall()` | `memory recall` |
| Click M+ | `memory_add()` | `memory add <value>` |
| Click M- | `memory_subtract()` | `memory subtract <value>` |

## CLI Architecture

### Command Groups

1. **project** — Create, load, save, info
2. **calc** — add, subtract, multiply, divide, eval, history
3. **memory** — store, recall, add, subtract, clear
4. **session** — status, undo, redo
5. **export** — history (json/csv/txt), session

### State Model

- Project state stored as JSON file
- Session tracks undo/redo stacks in memory
- Memory value persists in project state
- History appends on each calculation

### Output Format

- Human-readable by default (key: value pairs)
- `--json` flag for machine-readable JSON output
