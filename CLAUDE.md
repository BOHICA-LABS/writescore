# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WriteScore is a writing quality scoring tool with AI pattern detection. It analyzes text documents (primarily Markdown) and scores them on multiple dimensions to identify AI-generated patterns and provide actionable feedback for improving writing quality.

## Build & Development Commands

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/writescore --cov-report=html

# Run specific test file
pytest tests/unit/dimensions/test_perplexity.py

# Run specific test
pytest tests/unit/dimensions/test_perplexity.py::test_function_name -v

# Skip slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration

# Lint with ruff
ruff check src/

# CLI usage
writescore analyze document.md
writescore analyze document.md --mode full --detailed
writescore analyze document.md --mode adaptive --show-scores
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
