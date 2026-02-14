# Skill: fix-lint

> Fix all code quality issues — linting, formatting, unused imports, and type checking.
> Run this skill **after every implementation task** before committing.

## When to Use

- After writing or modifying any Python code
- Before committing changes
- When CI lint/format checks fail
- When you see import warnings or unused variable errors

## Procedure

### Step 1: Run ruff lint with auto-fix

```bash
ruff check --fix .
```

This auto-fixes issues caught by the configured rules:
- **E** — pycodestyle errors (whitespace, indentation, line length)
- **F** — pyflakes (unused imports, undefined names, redefined-unused variables)
- **I** — isort (import ordering: stdlib > third-party > local)
- **N** — pep8-naming (PascalCase classes, snake_case functions)
- **W** — pycodestyle warnings
- **UP** — pyupgrade (modernize syntax to Python 3.13+: `list[]` not `List[]`, `X | None` not `Optional[X]`)

**If there are unfixable errors**, ruff will print them. Fix those manually:
- Unused variables: remove or prefix with `_`
- Naming violations: rename to match convention
- Undefined names: add missing imports

### Step 2: Run ruff format

```bash
ruff format .
```

Formats all Python files to line-length 88 (configured in `pyproject.toml`).

### Step 3: Run unit tests

```bash
uv run pytest tests/unit -v
```

Verify nothing broke. All 61+ unit tests must pass. **Do NOT run integration tests** — they require external services.

### Step 4: Run type checking (optional but recommended)

```bash
mypy src/
```

Strict mode is enabled in `pyproject.toml`. Fix any type errors:
- Add missing type annotations
- Fix incompatible return types
- Add `# type: ignore[<code>]` only as last resort with a comment explaining why

### Step 5: Re-run lint after manual fixes

If you made manual fixes in steps 1-4, re-run to confirm everything is clean:

```bash
ruff check . && ruff format --check .
```

Both commands must exit with code 0 (no issues found, no files reformatted).

## Quick One-Liner

For simple cases where you just need to clean up after an implementation:

```bash
ruff check --fix . && ruff format . && uv run pytest tests/unit -v
```

## Configuration Reference

All config lives in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.13"
strict = true
```

## Common Issues

| Symptom | Fix |
|---------|-----|
| `F401 imported but unused` | Remove the import, or add `# noqa: F401` if re-exported intentionally |
| `F841 local variable assigned but never used` | Remove the variable or prefix with `_` |
| `I001 import block unsorted` | Auto-fixed by `ruff check --fix` |
| `UP006 use list instead of List` | Auto-fixed by `ruff check --fix` |
| `UP007 use X \| Y instead of Optional[X]` | Auto-fixed by `ruff check --fix` |
| `N801 class name should use CapWords` | Rename the class to PascalCase |
| `E501 line too long` | Auto-fixed by `ruff format` |
