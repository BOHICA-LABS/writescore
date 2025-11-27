# Contributing to WriteScore

Thank you for your interest in contributing to WriteScore!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/writescore.git`
3. Install development dependencies: `pip install -e ".[dev]"`
4. Download required models: `python -m spacy download en_core_web_sm`

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/writescore --cov-report=html

# Skip slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/unit/dimensions/test_perplexity.py -v
```

### Code Style

We use [ruff](https://github.com/astral-sh/ruff) for linting:

```bash
ruff check src/
```

**Style Guidelines:**
- Line length: 100 characters
- Target: Python 3.9+
- Use type hints for all public function signatures
- Follow Google-style docstrings

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests and linting: `pytest && ruff check src/`
4. Commit with a clear message
5. Push and create a Pull Request

## Bug Reports

When reporting bugs, please include:

- Python version (`python --version`)
- WriteScore version (`writescore --version`)
- Operating system
- Minimal reproduction steps
- Full error message/traceback

## Pull Requests

- Keep PRs focused on a single change
- Update tests for new functionality
- Ensure all tests pass
- Update documentation if needed

## Adding New Dimensions

See [docs/architecture.md](docs/architecture.md) for the dimension system architecture. New dimensions should:

1. Inherit from `DimensionStrategy`
2. Implement `analyze()` and `calculate_score()` methods
3. Include comprehensive tests
4. Use 0-100 scoring (100 = most human-like)

## Questions?

Open an issue for questions or discussion.
