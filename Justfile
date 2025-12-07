# WriteScore development commands
# Run `just` to see available commands

# Default: list available recipes
default:
    @just --list

# Install for usage
install:
    pip install -e .
    python -m spacy download en_core_web_sm

# Install for development (full setup)
dev:
    pip install -e ".[dev]"
    python -m spacy download en_core_web_sm
    pre-commit install
    pre-commit install --hook-type commit-msg

# Run unit and integration tests
test:
    pytest tests/unit tests/integration

# Run all tests including slow
test-all:
    pytest

# Run fast tests only (skip slow markers)
test-fast:
    pytest -m "not slow"

# Lint code with ruff
lint:
    ruff check src/ tests/

# Format code with ruff
format:
    ruff format src/ tests/
    ruff check --fix src/ tests/

# Generate HTML coverage report
coverage:
    pytest --cov=src/writescore --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

# Clean build artifacts and caches
clean:
    rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
