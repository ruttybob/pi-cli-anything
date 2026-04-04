# pi-cli-anything

This project is inspired by HKUDS/CLI-Anything, and it's simply an attempt to create something meaningful.

## Running Tests

### All Tests

```bash
./scripts/run_tests.sh
```

Or via npm:

```bash
npm run test:all
```

### Python Tests (pytest)

```bash
python3 -m pytest tests/test_skill_generator.py tests/test_repl_skin.py tests/test_skill_template.py -v
```

### TypeScript Tests (vitest)

```bash
npx vitest run tests/
```

## Project Structure

```
├── index.ts              # Pi extension — registers 5 slash commands
├── scripts/
│   ├── skill_generator.py  # SKILL.md generator from CLI harnesses
│   ├── repl_skin.py        # Unified REPL terminal interface
│   └── run_tests.sh        # Test runner script
├── templates/
│   └── SKILL.md.template   # Jinja2 template for SKILL.md generation
├── commands/              # Command specification markdown files
├── guides/                # Development guides
├── tests/
│   ├── test_skill_generator.py  # pytest — skill_generator.py tests
│   ├── test_repl_skin.py        # pytest — repl_skin.py tests
│   ├── test_skill_template.py   # pytest — Jinja2 template rendering tests
│   └── test_extension.test.ts   # vitest — index.ts extension tests
└── HARNESS.md             # Methodology SOP for CLI harness building
```
