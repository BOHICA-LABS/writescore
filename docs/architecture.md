# WriteScore Architecture Document

**Version:** 1.0
**Status:** Baseline (Reverse-Engineered from Existing Codebase)
**Last Updated:** 2025-11-26
**Product Version:** 6.3.0

---

## Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial Architecture | 2025-11-26 | 1.0 | Reverse-engineered architecture from codebase v6.3.0 | Architect Agent |

---

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture of WriteScore, an AI writing pattern analysis and scoring tool. It serves as the authoritative reference for understanding the system's structure, components, and design decisions.

### 1.2 Scope

This architecture document covers:
- System overview and architectural patterns
- Technology stack and dependencies
- Component architecture and interactions
- Data models and persistence
- Source code organization
- Infrastructure and deployment
- Coding standards and testing

### 1.3 Existing Project Analysis

| Aspect | Current State |
|--------|---------------|
| **Primary Purpose** | AI writing pattern analysis and scoring tool |
| **Tech Stack** | Python 3.9+, Click CLI, NLTK, spaCy, transformers, torch |
| **Architecture Style** | Modular monolith with plugin-like dimension system |
| **Deployment** | Local CLI installation via pip |

### 1.4 Architectural Patterns Identified

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Registry Pattern** | `core/dimension_registry.py` | Thread-safe dimension registration |
| **Strategy Pattern** | `dimensions/base_strategy.py` | Pluggable dimension analyzers |
| **Factory/Loader** | `core/dimension_loader.py` | Config-driven dimension instantiation |
| **Dataclass Models** | `core/results.py`, `scoring/dual_score.py` | Immutable result objects |
| **Facade** | `core/analyzer.py` | Unified analysis interface |

### 1.5 Constraints

- **No database** - All persistence is file-based (JSON)
- **Local execution only** - No API server or web interface
- **Memory-bound for ML** - Transformer models require significant RAM
- **Python-only** - No multi-language components

### 1.6 Future Considerations

- Potential web service/API evolution
- **MCP (Model Context Protocol) Server** - Enable WriteScore as a tool for AI assistants
- Service layer extraction for API/MCP reuse

---

## 2. Technology Stack

### 2.1 Core Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | Python | 3.9+ | Core implementation |
| **CLI Framework** | Click | 8.0+ | Command-line interface |
| **Markdown Parsing** | marko | 2.0+ | AST-based Markdown analysis |
| **NLP - Tokenization** | NLTK | 3.8+ | Sentence/word tokenization |
| **NLP - Parsing** | spaCy | 3.7+ | Dependency parsing, POS tagging |
| **NLP - Readability** | textstat | 0.7.3+ | Readability metrics |
| **NLP - Advanced** | textacy | 0.13+ | Text statistics, MTLD |
| **ML - Transformers** | transformers | 4.35+ | GLTR, perplexity models |
| **ML - Backend** | torch | 2.0+ | PyTorch for model inference |
| **ML - Embeddings** | sentence-transformers | 2.0+ | Semantic coherence |
| **Math/Stats** | numpy, scipy | 1.24+, 1.11+ | Numerical operations |
| **Testing** | pytest | 7.4+ | Test framework |
| **Linting** | ruff | 0.1+ | Code quality |

### 2.2 Dependency Groups

**Core Dependencies:**
```
marko>=2.0.0
nltk>=3.8
spacy>=3.7.0
textstat>=0.7.3
transformers>=4.35.0
torch>=2.0.0
scipy>=1.11.0
textacy>=0.13.0
numpy>=1.24.0
click>=8.0.0
sentence-transformers>=2.0.0
```

**Development Dependencies:** `[dev]`
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-timeout>=2.2.0
psutil>=5.9.0
ruff>=0.1.0
```

**ML Extras:** `[ml]`
```
accelerate>=0.20.0
datasets>=2.14.0
```

### 2.3 Architectural Recommendations

| Observation | Recommendation | Priority |
|-------------|----------------|----------|
| Heavy ML deps always loaded | Lazy imports for CLI startup speed | Medium |
| No async support | Add async for future API/MCP server | High |
| No caching layer | Add optional result caching | Medium |

---

## 3. Component Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                               │
│                    (cli/main.py, formatters.py)                 │
├─────────────────────────────────────────────────────────────────┤
│                      Orchestration Layer                        │
│                    (core/analyzer.py)                           │
├──────────────────┬──────────────────┬───────────────────────────┤
│   Dimension      │    Scoring       │      History              │
│   System         │    System        │      System               │
│  (dimensions/)   │   (scoring/)     │    (history/)             │
├──────────────────┴──────────────────┴───────────────────────────┤
│                     Core Infrastructure                         │
│        (registry, loader, config, results, exceptions)          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Descriptions

#### CLI Layer (`cli/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| **CLI Entry Point** | `main.py` | Click commands, argument parsing |
| **Formatters** | `formatters.py` | Output formatting (text, JSON, TSV) |

#### Orchestration Layer (`core/analyzer.py`)

**AIPatternAnalyzer** - Facade orchestrating all analysis:

```python
class AIPatternAnalyzer:
    def analyze_file(file_path, config) -> AnalysisResults
    def analyze_text(text, config) -> AnalysisResults
    def analyze_file_detailed(file_path) -> DetailedAnalysis
    def calculate_dual_score(results, targets) -> DualScore
    def load_score_history(file_path) -> ScoreHistory
    def save_score_history(history) -> None
```

#### Dimension System (`dimensions/`)

| Component | Purpose |
|-----------|---------|
| **DimensionStrategy** | Abstract base class for all dimensions |
| **DimensionRegistry** | Thread-safe dimension registration |
| **DimensionLoader** | Config-driven lazy loading |
| **18 Dimensions** | Individual analysis implementations |

**DimensionStrategy Interface:**
```python
class DimensionStrategy(ABC):
    @property
    def dimension_name(self) -> str
    @property
    def weight(self) -> float
    @property
    def tier(self) -> DimensionTier  # ADVANCED, CORE, SUPPORTING, STRUCTURAL

    def analyze(text, lines, **kwargs) -> Dict[str, Any]
    def calculate_score(metrics) -> float  # 0-100, 100=most human-like
    def get_recommendations(score, metrics) -> List[str]
```

#### Scoring System (`scoring/`)

| Component | Purpose |
|-----------|---------|
| **DualScore** | Score dataclasses, categories |
| **DualScoreCalculator** | Registry-based score calculation |
| **ScoreNormalization** | Z-score normalization |

#### History System (`history/`)

| Component | Purpose |
|-----------|---------|
| **ScoreHistory** | Score tracking dataclass |
| **Trends** | Trend visualization, comparisons |

### 3.3 Component Interaction Diagram

```mermaid
graph TB
    subgraph CLI["CLI Layer"]
        MAIN[main.py]
        FMT[formatters.py]
    end

    subgraph ORCH["Orchestration"]
        APA[AIPatternAnalyzer]
    end

    subgraph DIM["Dimension System"]
        REG[DimensionRegistry]
        LOAD[DimensionLoader]
        D1[18 Dimensions]
    end

    subgraph SCORE["Scoring System"]
        CALC[DualScoreCalculator]
        DS[DualScore]
    end

    subgraph HIST["History System"]
        TRACK[ScoreHistory]
    end

    MAIN --> APA
    MAIN --> FMT
    APA --> REG
    APA --> LOAD
    APA --> CALC
    APA --> TRACK
    LOAD --> REG
    REG --> D1
    CALC --> REG
    CALC --> DS
    FMT --> DS
```

### 3.4 Dimension Inventory

| Dimension | Tier | Purpose |
|-----------|------|---------|
| `perplexity` | CORE | AI vocabulary detection |
| `burstiness` | CORE | Sentence variation |
| `formatting` | CORE | Em-dash patterns |
| `voice` | CORE | Authenticity markers |
| `ai_vocabulary` | CORE | AI word patterns |
| `transition_marker` | CORE | Formulaic transitions |
| `predictability` | ADVANCED | GLTR/n-gram analysis |
| `semantic_coherence` | ADVANCED | Cross-sentence coherence |
| `syntactic` | SUPPORTING | Dependency complexity |
| `lexical` | SUPPORTING | Type-token ratio |
| `advanced_lexical` | SUPPORTING | MTLD diversity |
| `figurative_language` | SUPPORTING | Similes, metaphors |
| `sentiment` | SUPPORTING | Emotional variance |
| `readability` | SUPPORTING | Flesch-Kincaid |
| `pragmatic_markers` | SUPPORTING | Discourse markers |
| `structure` | STRUCTURAL | Heading hierarchy, lists |

---

## 4. Data Models

### 4.1 Core Data Models

#### AnalysisResults

Primary output from `AIPatternAnalyzer.analyze_file()`:

```python
@dataclass
class AnalysisResults:
    file_path: str
    total_words: int
    total_sentences: int
    total_paragraphs: int
    dimension_results: Dict[str, DimensionResult]
    metadata: Dict[str, Any]
```

#### DualScore

Output from `calculate_dual_score()`:

```python
@dataclass
class DualScore:
    detection_risk: float      # 0-100 (lower = better)
    quality_score: float       # 0-100 (higher = better)
    detection_interpretation: str
    quality_interpretation: str
    categories: List[ScoreCategory]
    improvements: List[ImprovementAction]
    path_to_target: List[ImprovementAction]
    estimated_effort: str
```

#### Supporting Models

```python
@dataclass
class ScoreDimension:
    name: str
    score: float
    max_score: float
    percentage: float
    impact: str  # 'NONE', 'LOW', 'MEDIUM', 'HIGH'

@dataclass
class ImprovementAction:
    priority: int
    dimension: str
    potential_gain: float
    action: str
    effort_level: str  # 'LOW', 'MEDIUM', 'HIGH'
```

### 4.2 Persistence Model

**No database** - File-based JSON persistence:

| Data Type | Location | Format |
|-----------|----------|--------|
| Score History | `.ai-analysis-history/{file}.history.json` | JSON |
| Parameters | `config/scoring_parameters.yaml` | YAML |
| Parameter Archive | `config/parameters/archive/` | YAML |

---

## 5. Source Code Organization

### 5.1 Project Structure

```
writescore/
├── .github/workflows/       # CI/CD workflows
├── docs/                    # Documentation
│   └── stories/             # Epic and story definitions
├── src/writescore/          # Main package
│   ├── cli/                 # Command Line Interface
│   ├── core/                # Core Analysis Engine
│   ├── dimensions/          # Dimension Analyzers (18)
│   ├── scoring/             # Scoring System
│   ├── history/             # Score History Tracking
│   ├── evidence/            # Evidence Extraction
│   ├── utils/               # Utilities
│   └── data/                # Static Data Files
├── tests/                   # Test Suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── accuracy/            # Accuracy validation
│   ├── performance/         # Performance benchmarks
│   └── fixtures/            # Sample documents
├── pyproject.toml           # Package configuration
└── README.md                # Project overview
```

### 5.2 Naming Conventions

| Category | Convention | Example |
|----------|------------|---------|
| Modules | `snake_case.py` | `dual_score_calculator.py` |
| Classes | `PascalCase` | `AIPatternAnalyzer` |
| Functions | `snake_case` | `calculate_dual_score()` |
| Constants | `UPPER_SNAKE_CASE` | `AI_VOCAB_REPLACEMENTS` |
| Tests | `test_*.py` | `test_perplexity.py` |

### 5.3 Future Structure for MCP/API

```
src/writescore/
├── ...existing...
├── services/                # NEW: Business Logic Layer
│   ├── analysis_service.py
│   └── history_service.py
└── mcp/                     # NEW: MCP Server
    ├── server.py
    ├── tools.py
    └── resources.py
```

---

## 6. Infrastructure & Deployment

### 6.1 Deployment Model

| Aspect | Current State |
|--------|---------------|
| **Deployment Type** | Local pip installation |
| **Server Infrastructure** | None |
| **Database** | None (file-based JSON) |
| **Container Support** | None (could be added) |

### 6.2 CI/CD Pipeline

#### CI Workflow (`.github/workflows/ci.yml`)

| Job | Trigger | Steps |
|-----|---------|-------|
| **lint** | Push/PR to main | ruff check |
| **test** | Push/PR to main | pytest (Python 3.9, 3.10, 3.12) |

#### Release Workflow (`.github/workflows/release.yml`)

| Trigger | Steps |
|---------|-------|
| Tag `v*` | Build → GitHub Release |

### 6.3 Environment Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.9, 3.10, 3.11, or 3.12 |
| spaCy model | `en_core_web_sm` (manual download) |
| NLTK data | `punkt`, `punkt_tab` (auto-download) |

### 6.4 Installation

```bash
# Development install
pip install -e ".[dev]"
python -m spacy download en_core_web_sm

# CLI usage
writescore analyze document.md
```

---

## 7. Coding Standards

### 7.1 Code Style

**Enforced via ruff:**
- Line length: 100 characters
- Target: Python 3.9
- Rules: E, F, W, I, UP, B, C4, SIM

### 7.2 Documentation

**Google-style docstrings:**
```python
def calculate_score(metrics: Dict[str, Any]) -> float:
    """
    Calculate dimension score from raw metrics.

    Args:
        metrics: Dictionary containing raw analysis metrics

    Returns:
        Score from 0-100 where 100 = most human-like
    """
```

### 7.3 Type Hints

Required for all public function signatures:
```python
def analyze(
    text: str,
    lines: List[str],
    config: Optional[AnalysisConfig] = None
) -> Dict[str, Any]:
```

---

## 8. Testing Strategy

### 8.1 Test Organization

| Directory | Purpose | Marker |
|-----------|---------|--------|
| `tests/unit/` | Isolated unit tests | (default) |
| `tests/integration/` | Cross-module tests | `@pytest.mark.integration` |
| `tests/accuracy/` | Detection accuracy | `@pytest.mark.accuracy` |
| `tests/performance/` | Benchmarks | `@pytest.mark.slow` |

### 8.2 Test Patterns

**Dimension Testing:**
```python
def test_burstiness_high_variance_returns_high_score():
    """High variance (human-like) should score well."""
    dim = BurstinessDimension()
    score = dim.calculate_score({'variance': 25.0})
    assert score >= 80.0
```

**Registry Auto-Clear:**
```python
@pytest.fixture(autouse=True)
def clear_dimension_registry():
    DimensionRegistry.clear()
    yield
    DimensionRegistry.clear()
```

### 8.3 Coverage Targets

| Metric | Target |
|--------|--------|
| Line Coverage | 80%+ |
| Branch Coverage | Enabled |

---

## 9. Architectural Recommendations

### 9.1 For MCP Server Evolution

| Gap | Recommendation | Priority |
|-----|----------------|----------|
| No async support | Add async wrappers for analysis | High |
| No service layer | Extract business logic from CLI | High |
| No caching | Add result caching for repeated queries | Medium |
| Tight CLI coupling | Decouple for API/MCP reuse | High |

### 9.2 Proposed MCP Architecture

```
┌─────────────────────────────────────────────────┐
│              MCP Client (Claude)                │
└─────────────────────┬───────────────────────────┘
                      │ JSON-RPC over stdio/HTTP
┌─────────────────────▼───────────────────────────┐
│              MCP Server Layer                   │
│  ┌─────────────┐  ┌──────────────┐              │
│  │   Tools     │  │  Resources   │              │
│  │ - analyze   │  │ - config     │              │
│  │ - score     │  │ - dimensions │              │
│  └─────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────┤
│              Service Layer (NEW)                │
├─────────────────────────────────────────────────┤
│              Existing Core                      │
│    AIPatternAnalyzer, Dimensions, Scoring       │
└─────────────────────────────────────────────────┘
```

---

## 10. Appendix

### A. Quick Reference

**Installation:**
```bash
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

**CLI Commands:**
```bash
writescore analyze document.md
writescore analyze document.md --detailed
writescore analyze document.md --show-scores
writescore analyze --batch directory/
writescore recalibrate dataset.jsonl
```

**Scoring Convention:**
- 0-100 scale where **100 = most human-like**
- Detection Risk: Lower is better (target: <30)
- Quality Score: Higher is better (target: >85)

### B. Tier Weights

| Tier | Weight Range | Examples |
|------|--------------|----------|
| ADVANCED | 30-40% | predictability, semantic_coherence |
| CORE | 35-45% | burstiness, formatting, voice |
| SUPPORTING | 15-25% | lexical, sentiment, readability |
| STRUCTURAL | 5-10% | structure |

### C. Related Documents

- [Product Requirements Document](prd.md)
- [CLAUDE.md](../CLAUDE.md) - AI assistant instructions
- [CHANGELOG.md](../CHANGELOG.md) - Version history

---

*This architecture document was reverse-engineered from the WriteScore v6.3.0 codebase to establish a baseline architectural reference.*

---

## 11. Package Structure (Detailed)

This section provides a comprehensive view of the package structure with module descriptions.

```
writescore/
├── __init__.py                 # Main package exports for backward compatibility
├── core/                       # Core analysis engine
│   ├── analyzer.py            # Main AIPatternAnalyzer class
│   └── results.py             # Result dataclasses
├── dimensions/                # Analysis dimensions (12 total in v5.0.0)
│   ├── base_strategy.py      # Base DimensionStrategy interface
│   ├── perplexity.py         # AI vocabulary & perplexity
│   ├── burstiness.py         # Sentence/paragraph variation
│   ├── structure.py          # Section/heading analysis
│   ├── formatting.py         # Em-dash, bold/italic, etc.
│   ├── voice.py              # Voice consistency
│   ├── syntactic.py          # Syntactic complexity
│   ├── lexical.py            # Lexical diversity
│   ├── sentiment.py          # Sentiment analysis
│   ├── readability.py        # Readability metrics
│   ├── transition_marker.py  # AI transition markers
│   ├── predictability.py     # GLTR/n-gram analysis
│   └── advanced_lexical.py   # Advanced lexical metrics
├── scoring/                   # Scoring system
│   ├── dual_score.py         # Dual scoring dataclasses + thresholds
│   └── dual_score_calculator.py  # Dual score calculation
├── history/                   # History tracking
│   ├── tracker.py            # History tracking dataclasses
│   └── export.py             # CSV/JSON export (future enhancement)
├── evidence/                  # Evidence extraction (future expansion)
│   └── __init__.py           # Placeholder
├── utils/                     # Shared utilities
│   ├── text_processing.py    # Text cleaning, word counting
│   ├── pattern_matching.py   # Regex patterns, constants
│   └── visualization.py      # Sparklines, charts
└── cli/                       # CLI interface
    ├── main.py               # Click-based CLI entry point
    ├── args.py               # Legacy argument parsing (backup)
    └── formatters.py         # Output formatting
```

---

## 12. Design Principles

### 12.1 Backward Compatibility

The package maintains backward compatibility through package-level exports:

```python
# Old way (still works)
from analyze_ai_patterns import AIPatternAnalyzer

# New way (recommended)
from writescore.core.analyzer import AIPatternAnalyzer

# Or use package import
from writescore import AIPatternAnalyzer
```

### 12.2 Dimension Analyzer Interface

All dimension analyzers implement the `DimensionAnalyzer` base class:

```python
class DimensionAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """Analyze text for this dimension"""
        pass

    @abstractmethod
    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """Calculate score for this dimension"""
        pass
```

### 12.3 Separation of Concerns

- **Core**: Orchestration and coordination
- **Dimensions**: Individual analysis algorithms
- **Scoring**: Dual-score calculation and interpretation
- **History**: Score tracking over time
- **Utils**: Shared helper functions
- **CLI**: User interface layer
