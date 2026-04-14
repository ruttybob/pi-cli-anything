# TEST.md — cli-anything-calculator Test Plan & Results

## Test Inventory Plan

- `test_core.py`: ~15 unit tests planned
- `test_full_e2e.py`: ~10 E2E tests planned (including subprocess tests)

## Unit Test Plan (test_core.py)

### project.py
- `test_create_project` — Creates valid project structure
- `test_create_project_with_file` — Saves to disk
- `test_load_project` — Loads from disk
- `test_load_project_missing` — FileNotFoundError
- `test_project_info` — Returns correct summary
- `test_save_project` — Updates modified timestamp

### compute.py
- `test_compute_add` — Addition
- `test_compute_subtract` — Subtraction
- `test_compute_multiply` — Multiplication
- `test_compute_divide` — Division
- `test_compute_divide_by_zero` — Error handling
- `test_memory_operations` — Store, recall, add, subtract, clear

### session.py
- `test_session_undo_redo` — Undo/redo stack
- `test_session_save` — File locking save

### export.py
- `test_export_json` — JSON export
- `test_export_csv` — CSV export
- `test_export_txt` — Text export

## E2E Test Plan (test_full_e2e.py)

### Workflow: Multi-step Calculation
1. Create project
2. Perform 5 calculations
3. Verify history has 5 entries
4. Export to CSV
5. Verify CSV file structure

### Workflow: Memory Pipeline
1. Create project
2. Calculate 10 + 5
3. Store result in memory
4. Calculate 20 * 3
5. Recall memory
6. Verify memory value

### CLI Subprocess Tests
- `test_help` — `--help` returns 0
- `test_project_new_json` — Create project with `--json`
- `test_calc_add_json` — Add with `--json` output
- `test_full_workflow` — Create → calc → history → export

## Test Results

_(To be appended after test execution)_
