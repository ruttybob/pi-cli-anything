---
name: "cli-anything-calculator"
description: "Command-line interface for Calculator - CLI harness for the Simple Calculator GUI application, built using the [cli-anything](https://github..."
---

# cli-anything-calculator

CLI harness for the Simple Calculator GUI application, built using the [cli-anything](https://github.com/ruttybob/pi-cli-anything) methodology.

## Installation

This CLI is installed as part of the cli-anything-calculator package:

```bash
pip install cli-anything-calculator
```

**Prerequisites:**
- Python 3.10+
- Calculator must be installed on your system

## Usage

### Basic Commands

```bash
# Show help
cli-anything-calculator --help

# Start interactive REPL mode
cli-anything-calculator

# Create a new project
cli-anything-calculator project new -o project.json

# Run with JSON output (for agent consumption)
cli-anything-calculator --json project info -p project.json
```

## Command Groups

### General

General commands for the CLI.

| Command | Description |
|---------|-------------|
| `launch-gui` | Launch the calculator GUI application. |

## Examples

### Create a New Project

Create a new calculator project file.

```bash
cli-anything-calculator project new -o myproject.json
# Or with JSON output for programmatic use
cli-anything-calculator --json project new -o myproject.json
```

### Interactive REPL Session

Start an interactive session with undo/redo support.

```bash
cli-anything-calculator
# Enter commands interactively
# Use 'help' to see available commands
# Use 'undo' and 'redo' for history navigation
```

## For AI Agents

When using this CLI programmatically:

1. **Always use `--json` flag** for parseable output
2. **Check return codes** - 0 for success, non-zero for errors
3. **Parse stderr** for error messages on failure
4. **Use absolute paths** for all file operations
5. **Verify outputs exist** after export operations

## Version

1.0.0