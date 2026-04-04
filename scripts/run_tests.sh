#!/usr/bin/env bash
# Run all tests for pi-cli-anything
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "═══════════════════════════════════════════════════════"
echo "  pi-cli-anything — Test Suite"
echo "═══════════════════════════════════════════════════════"
echo ""

EXIT_CODE=0

# ── Python Tests ────────────────────────────────────────────────────────

echo "▸ Running Python tests (pytest)..."
echo ""
python3 -m pytest tests/test_skill_generator.py tests/test_repl_skin.py tests/test_skill_template.py -v || EXIT_CODE=$?
echo ""

# ── TypeScript Tests ────────────────────────────────────────────────────

echo "▸ Running TypeScript tests (vitest)..."
echo ""

# Install deps if needed
if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install --silent
fi

npx vitest run tests/ || EXIT_CODE=$?
echo ""

# ── Summary ─────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✓ All tests passed"
else
    echo "  ✗ Some tests failed (exit code: $EXIT_CODE)"
fi
echo "═══════════════════════════════════════════════════════"

exit $EXIT_CODE
