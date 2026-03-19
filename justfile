# gh-tt justfile — project commands
# https://just.systems

@_default:
    just --list --unsorted

# Format, lint, and type check (run after making changes)
[group('qa')]
check: format lint typecheck

# Run ruff formatter
[group('qa')]
format:
    uv run --frozen -- ruff format

# Run ruff linter with auto-fix
[group('qa')]
lint:
    uv run --frozen -- ruff check --fix

# Run ty type checker
[group('qa')]
typecheck:
    uv run --frozen -- ty check

# Run unit tests with coverage
[group('test')]
test *args:
    uv run --frozen -- pytest --cov=. --cov-config=pyproject.toml -m 'not gh_actions' {{ args }}

# Run end-to-end tests (installs local gh-tt first)
[group('test')]
test-e2e *args:
    uv run --frozen -- python scripts/install_local_gh_tt.py
    uv run --frozen -- pytest -m gh_actions {{ args }}

# Run the extension locally (e.g. just run deliver)
[group('dev')]
run *args:
    ./gh-tt {{ args }}

# Sync the project's locked dependencies
[group('dev')]
install:
    uv sync
