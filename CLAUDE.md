# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WriteScore is a writing quality scoring tool with AI pattern detection. It analyzes text documents (primarily Markdown) and scores them on multiple dimensions to identify AI-generated patterns and provide actionable feedback for improving writing quality.

## Build & Development Commands

```bash
# Install dependencies (creates/updates .venv automatically)
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/writescore --cov-report=html

# Run specific test file
uv run pytest tests/unit/dimensions/test_perplexity.py

# Run specific test
uv run pytest tests/unit/dimensions/test_perplexity.py::test_function_name -v

# Skip slow tests
uv run pytest -m "not slow"

# Run integration tests only
uv run pytest -m integration

# Lint with ruff
uv run ruff check src/

# CLI usage
uv run writescore analyze document.md
uv run writescore analyze document.md --mode full --detailed
uv run writescore analyze document.md --mode adaptive --show-scores
```

## Architecture

### Source Layout
Uses `src/` layout with package at `src/writescore/`.

### Core Components

- **`core/analyzer.py`** - Main `AIPatternAnalyzer` class that orchestrates all dimension analyzers
- **`core/dimension_registry.py`** - Thread-safe registry for self-registering dimensions
- **`core/dimension_loader.py`** - Lazy loading of dimensions based on profiles
- **`core/analysis_config.py`** - Configuration for analysis modes (FAST, ADAPTIVE, SAMPLING, FULL)

### Dimension System

Dimensions are self-registering analyzers that inherit from `DimensionStrategy` (in `dimensions/base_strategy.py`):

```python
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

class MyDimension(DimensionStrategy):
    @property
    def dimension_name(self) -> str:
        return "my_dimension"

    @property
    def weight(self) -> float:
        return 5.0  # percentage of total score

    @property
    def tier(self) -> DimensionTier:
        return DimensionTier.SUPPORTING  # ADVANCED, CORE, SUPPORTING, or STRUCTURAL

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        # Return metrics dict
        pass

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        # Return 0-100 score (100 = most human-like)
        pass
```

**Scoring Convention**: All dimensions use 0-100 scale where 100 = most human-like, 0 = most AI-like.

**Tier System**:
- ADVANCED: ML-based (transformers, GLTR) - 30-40% weight
- CORE: Proven AI signatures (burstiness, formatting, voice) - 35-45% weight
- SUPPORTING: Quality indicators (lexical, sentiment) - 15-25% weight
- STRUCTURAL: AST-based patterns - 5-10% weight

### Key Dimensions (in `dimensions/`)

| Dimension | File | Purpose |
|-----------|------|---------|
| perplexity | `perplexity.py` | AI vocabulary detection |
| burstiness | `burstiness.py` | Sentence/paragraph variation |
| formatting | `formatting.py` | Em-dash patterns (strongest AI signal) |
| predictability | `predictability.py` | GLTR/n-gram analysis |
| voice | `voice.py` | First-person, contractions, authenticity |
| syntactic | `syntactic.py` | Dependency tree complexity |
| lexical | `lexical.py` | Type-token ratio diversity |
| semantic_coherence | `semantic_coherence.py` | Cross-sentence coherence |

### CLI Structure

- **`cli/main.py`** - Click-based CLI with `analyze` and `recalibrate` commands
- **`cli/formatters.py`** - Output formatting (standard, detailed, dual-score reports)

### Scoring System

- **`scoring/dual_score.py`** - Dual scoring dataclasses and thresholds
- **`scoring/dual_score_calculator.py`** - Score calculation from dimension results

## Testing

Tests mirror source structure under `tests/`:
- `tests/unit/` - Unit tests per module
- `tests/integration/` - Cross-module integration tests
- `tests/accuracy/` - Accuracy validation tests
- `tests/performance/` - Performance benchmarks
- `tests/fixtures/` - Sample documents (AI, human, mixed, edge cases)

The `tests/conftest.py` provides shared fixtures including sample texts and auto-clearing of the `DimensionRegistry` between tests.

## Analysis Modes

| Mode | Speed | Use Case |
|------|-------|----------|
| FAST | Fastest | Quick checks, truncates to 2000 chars |
| ADAPTIVE | Balanced | Default, scales with document size |
| SAMPLING | Configurable | Large docs, samples N sections |
| FULL | Slowest | Complete analysis, most accurate |

## Configuration

Analysis can be configured via `AnalysisConfig`:

```python
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode

config = AnalysisConfig(
    mode=AnalysisMode.ADAPTIVE,
    sampling_sections=5,
    dimension_overrides={"predictability": {"max_chars": 5000}}
)
```

## Dependencies

Required: marko, nltk, spacy, textstat, transformers, torch, scipy, textacy, numpy, click

Optional extras:
- `[dev]` - pytest, pytest-cov, ruff
- `[semantic]` - sentence-transformers
- `[ml]` - accelerate, datasets

## Git Commit Guidelines

When creating git commits, do NOT include:
- The "Generated with Claude Code" line
- The "Co-Authored-By: Claude" line
- Any other AI attribution in commit messages

### Conventional Commits Format

All commits MUST follow https://www.conventionalcommits.org/:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Required: Type

| Type     | Purpose                      |
|----------|------------------------------|
| feat     | New feature (MINOR version)  |
| fix      | Bug fix (PATCH version)      |
| docs     | Documentation only           |
| style    | Code style (no logic change) |
| refactor | Neither fix nor feature      |
| perf     | Performance improvement      |
| test     | Adding/fixing tests          |
| build    | Build system/dependencies    |
| ci       | CI configuration             |
| chore    | Other non-src/test changes   |

### Required: Description

- Use imperative, present tense ("add" not "added")
- Do NOT capitalize the first letter
- Do NOT end with a period

### Optional: Scope

Enclose in parentheses after type: `feat(api): add endpoint`

Common scopes: `cli`, `core`, `dimensions`, `scoring`, `docs`

### Optional: Body

- Separate from description with a blank line
- Explain motivation and contrast with previous behavior

### Optional: Footer

- `Refs: #123` - Issue references
- `Closes: #123` - Issues closed by commit
- `BREAKING CHANGE:` - Breaking change description

### Breaking Changes

Indicate with either:
1. `!` after type/scope: `feat(api)!: remove endpoint`
2. Footer: `BREAKING CHANGE: endpoint removed and replaced with accounts`

## Pre-commit Hooks

This project uses pre-commit hooks for code quality. Install them:

```bash
uv run pre-commit install && uv run pre-commit install --hook-type commit-msg
```

**Hooks installed:**
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **ggshield** - Secret scanning
- **nbstripout** - Notebook output stripping
- **conventional-pre-commit** - Commit message validation
- **pre-commit-hooks** - Trailing whitespace, YAML/JSON checks, large file checks
- **no-commit-to-branch** - Prevents direct commits to `main`

## Git Workflow (Git Flow)

This project uses **Git Flow** branching strategy. Follow these rules:

### Branch Structure

| Branch | Purpose | Create from |
|--------|---------|-------------|
| `main` | Production releases only | - |
| `develop` | Integration branch (default working branch) | `main` |
| `feature/*` | New features | `develop` |
| `fix/*` | Bug fixes | `develop` |
| `spike/*` | Research spikes | `develop` |
| `hotfix/*` | Emergency production fixes | `main` |
| `release/*` | Release preparation | `develop` |

### Rules

1. **NEVER commit directly to `main`** - blocked by pre-commit hook
2. **Always branch from `develop`** for new work
3. **Use conventional commits** - enforced by pre-commit hook

### Branch Naming

```
feature/story-X.X-short-description
fix/issue-123-short-description
spike/XXX-topic
hotfix/issue-456-critical-fix
release/vX.X.X
```

### Creating a Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/story-1.2-config-registry
```

### After Work is Complete

Create a PR to merge into `develop` (not `main`).

## Secret Scanning (ggshield)

The repo uses GitGuardian's ggshield for secret detection via pre-commit hook.

### Scan the Entire Repo

```bash
uvx ggshield secret scan repo .
```

### Configuration

- `.gitguardian.yaml` - ignore rules for false positives and docs
- Runs automatically on every commit via pre-commit hook

### Managing Incidents via API

The ggshield CLI cannot manage dashboard incidents. Use the API directly:

```bash
# Ignore an incident (mark as false positive)
curl -X POST "https://api.gitguardian.com/v1/incidents/secrets/{incident_id}/ignore" \
  -H "Authorization: Token ${GITGUARDIAN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"ignore_reason": "test_credential"}'

# Resolve an incident (secret was revoked)
curl -X POST "https://api.gitguardian.com/v1/incidents/secrets/{incident_id}/resolve" \
  -H "Authorization: Token ${GITGUARDIAN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"secret_revoked": true}'
```

Ignore reasons: `test_credential`, `false_positive`, `low_risk`

Requires API key with `incidents:read` and `incidents:write` scopes.
