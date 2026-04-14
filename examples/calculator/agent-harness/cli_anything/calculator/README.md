# cli-anything-calculator

CLI harness for the Simple Calculator GUI application, built using the
[cli-anything](https://github.com/ruttybob/pi-cli-anything) methodology.

## Prerequisites

- Python 3.10+
- The Simple Calculator app source code (contains `calculator_engine.py`)

## Installation

```bash
# From the agent-harness directory:
pip install -e .

# Set the calculator source path:
export CALCULATOR_SOURCE_PATH=/path/to/calculator
```

## Usage

### Interactive REPL

```bash
cli-anything-calculator
```

### One-shot Commands

```bash
# Create a new project
cli-anything-calculator project new -o calc.json

# Perform calculations
cli-anything-calculator --project calc.json calc add 10 5
cli-anything-calculator --project calc.json calc multiply 3 7
cli-anything-calculator --project calc.json calc divide 100 4

# View history
cli-anything-calculator --project calc.json calc history

# Memory operations
cli-anything-calculator --project calc.json memory store 42
cli-anything-calculator --project calc.json memory recall

# Export history
cli-anything-calculator --project calc.json export history results.csv -f csv

# JSON output for programmatic use
cli-anything-calculator --json --project calc.json calc add 5 3
```

### Session Management

```bash
# Check session status
cli-anything-calculator --project calc.json session status

# Undo/redo
cli-anything-calculator --project calc.json session undo
cli-anything-calculator --project calc.json session redo
```

### Launch GUI

```bash
cli-anything-calculator launch
```

## Running Tests

```bash
cd agent-harness
python3 -m pytest cli_anything/calculator/tests/ -v -s
```

## Architecture

The CLI wraps the real `calculator_engine.py` from the GUI application.
All calculations are performed by the actual engine — the CLI does NOT
reimplement arithmetic. This ensures parity between GUI and CLI results.
