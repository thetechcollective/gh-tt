# gh-tt justfile — project commands
# https://just.systems

@_default:
    just --list --unsorted



# Run all checks
[group('check')]
check: check-test check-format check-lint check-types check-spelling check-actionlint check-zizmor

# Check unit tests
[group('check')]
check-test *args:
    uv run --frozen -- pytest -m 'not end_to_end and not legacy' --cov=src/ --cov-config=pyproject.toml --tb=no -q --no-header --numprocesses=auto {{ args }}

# Check ruff formatting
[group('check')]
check-format:
    uv run --frozen -- ruff format --check --output-format=concise

# Check ruff linting
[group('check')]
check-lint:
    uv run --frozen -- ruff check --output-format=concise

# Check ty types
[group('check')]
check-types:
    uv run --frozen -- ty check --output-format=concise

# Check cspell spelling
[group('check')]
check-spelling:
    cspell lint --no-progress

# Check GitHub Actions with actionlint
[group('check')]
check-actionlint:
    actionlint -oneline

# Check GitHub Actions with zizmor
[group('check')]
check-zizmor:
    zizmor ./.github/ --pedantic --offline

# Fix all auto-fixable issues
[group('fix')]
fix: format lint

# Run ruff formatter
[group('fix')]
format:
    uv run --frozen -- ruff format

# Run ruff linter with auto-fix
[group('fix')]
lint:
    uv run --frozen -- ruff check --fix

[group('fix')]
lint-actions:
    zizmor ./.github/ --pedantic --offline --fix=safe

# Run unit tests with coverage
[group('test')]
test *args:
    uv run --frozen -- pytest --cov=src/ --cov-config=pyproject.toml -m 'not end_to_end and not legacy' {{ args }} --numprocesses=auto

# Run end-to-end tests (installs local gh-tt first)
[group('test')]
test-e2e *args:
    uv run --frozen -- python scripts/install_local_gh_tt.py
    uv run --frozen -- pytest --numprocesses=auto -m end_to_end {{ args }}

# Run the extension locally (e.g. just run deliver)
[group('dev')]
run *args:
    ./gh-tt {{ args }}

# Sync the project's locked dependencies
[group('dev')]
install:
    uv sync
