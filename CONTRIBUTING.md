# Contributing to WriteScore

Thank you for your interest in contributing to WriteScore!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/writescore.git`

### Option 1: Using Just (Recommended)

```bash
# Install Just (see README for OS-specific instructions)
just dev
```

### Option 2: Using Devcontainer

Open in VS Code and select "Reopen in Container" when prompted.

### Option 3: Manual Setup

```bash
uv sync --extra dev
uv run python -m spacy download en_core_web_sm
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

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

### Secret Scanning (ggshield)

This project uses [GitGuardian's ggshield](https://github.com/GitGuardian/ggshield) for secret detection via pre-commit hook. Setup is required before your first commit:

### Setup (One-time)

1. Create a free account at [gitguardian.com](https://www.gitguardian.com/)
2. Authenticate locally:
   ```bash
   ggshield auth login
   ```

### Skipping ggshield (Optional)

If you prefer not to use ggshield, you can skip it for individual commits:

```bash
SKIP=ggshield git commit -m "your message"
```

Or disable it entirely in your local environment:

```bash
git config --local hooks.ggshield false
```

Note: GitHub's built-in secret scanning is also enabled for this repository as a backup.

## Code Style

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

## Issue and PR Labels

We use a structured label system to categorize and track work. When creating issues or PRs, apply appropriate labels from each category.

### Type Labels (maps to conventional commits)

| Label | Description | Commit Prefix |
|-------|-------------|---------------|
| `type: bug` | Bug fix | `fix:` |
| `type: feature` | New feature | `feat:` |
| `type: docs` | Documentation | `docs:` |
| `type: refactor` | Code refactoring | `refactor:` |
| `type: test` | Test changes | `test:` |
| `type: perf` | Performance improvement | `perf:` |
| `type: build` | Build/CI changes | `build:` |

### Scope Labels (agile tracking)

| Label | Description |
|-------|-------------|
| `scope: epic` | Multi-story theme or initiative |
| `scope: story` | User story, usually multiple PRs |
| `scope: spike` | Time-boxed research or investigation |
| `scope: tech-debt` | Technical debt to address |

### Area Labels (architecture)

| Label | Description |
|-------|-------------|
| `area: cli` | CLI and command interface |
| `area: core` | Core analyzer and registry |
| `area: dimensions` | Dimension analyzers |
| `area: scoring` | Scoring system and calculation |

### Priority Labels

| Label | Description |
|-------|-------------|
| `priority: high` | Urgent - address soon |
| `priority: medium` | Normal priority |
| `priority: low` | Backlog - address when time permits |

### Label Guidelines

- **Each issue should have exactly one `type:` label** matching the intended commit prefix
- Apply `area:` labels to indicate which part of the codebase is affected
- Use `scope:` labels for planning and tracking larger initiatives
- Use `priority:` labels during triage to indicate urgency
- `good first issue` and `help wanted` are available for community contributions

## Adding New Dimensions

See [docs/architecture.md](docs/architecture.md) for the dimension system architecture. New dimensions should:

1. Inherit from `DimensionStrategy`
2. Implement `analyze()` and `calculate_score()` methods
3. Include comprehensive tests
4. Use 0-100 scoring (100 = most human-like)

## Questions?

Open an issue for questions or discussion.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
Please read it before participating.
