# WriteScore Development Commands
# Run `just` to see available recipes, or `just <recipe>` to run one

# Default recipe - show available commands
default:
    @just --list

# === Setup ===

# Install project in development mode with all dependencies
install:
    uv pip install -e ".[dev,semantic]"

# Install pre-commit hooks
hooks:
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

# Full development setup
setup: install hooks
    @echo "Development environment ready!"

# === Testing ===

# Run fast tests (excludes slow ML tests)
test:
    uv run pytest -m "not slow" --tb=short

# Run all tests including slow ones
test-all:
    uv run pytest --tb=short

# Run tests with coverage report
test-cov:
    uv run pytest --cov=src/writescore --cov-report=html --cov-report=term
    @echo "Coverage report: htmlcov/index.html"

# Run specific test file
test-file FILE:
    uv run pytest {{FILE}} -v

# Run tests matching a pattern
test-match PATTERN:
    uv run pytest -k "{{PATTERN}}" -v

# === Linting & Formatting ===

# Run all linters
lint:
    uv run ruff check src/ tests/
    uv run ruff format --check src/ tests/

# Auto-fix linting issues
lint-fix:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Run type checking
typecheck:
    uv run mypy src/

# Run all checks (lint + typecheck)
check: lint typecheck

# === Pre-commit ===

# Run pre-commit on all files
pre-commit:
    uv run pre-commit run --all-files

# Update pre-commit hooks
pre-commit-update:
    uv run pre-commit autoupdate

# === CLI ===

# Analyze a file
analyze FILE:
    uv run writescore analyze {{FILE}}

# Analyze with full mode and detailed output
analyze-full FILE:
    uv run writescore analyze {{FILE}} --mode full --detailed

# Analyze with scores shown
analyze-scores FILE:
    uv run writescore analyze {{FILE}} --show-scores

# === Documentation ===

# Shard a document using md-tree
shard-doc DOC OUTPUT:
    md-tree explode {{DOC}} {{OUTPUT}}

# === Utilities ===

# Clean build artifacts and caches
clean:
    rm -rf build/ dist/ *.egg-info/
    rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/
    rm -rf htmlcov/ .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    @echo "Cleaned!"

# Show project stats
stats:
    @echo "=== Source Lines ==="
    @find src -name "*.py" | xargs wc -l | tail -1
    @echo "=== Test Lines ==="
    @find tests -name "*.py" | xargs wc -l | tail -1
    @echo "=== Dimensions ==="
    @ls src/writescore/dimensions/*.py | grep -v __init__ | grep -v base | wc -l | xargs echo "Count:"

# Show git status summary
status:
    @git status --short
    @echo "---"
    @git log --oneline -5

# === Release ===

# Build package
build: clean
    uv run python -m build

# Check package before upload
check-package: build
    uv run twine check dist/*
