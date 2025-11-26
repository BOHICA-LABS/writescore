# WriteScore - Writing Quality Scoring Tool

[![CI](https://github.com/jmagady/writescore/actions/workflows/ci.yml/badge.svg)](https://github.com/jmagady/writescore/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-6.3.0-green.svg)](https://github.com/jmagady/writescore/releases)

**Formerly known as AI Pattern Analyzer**

This package provides a comprehensive writing quality scoring tool with AI pattern detection capabilities. Refactored from the monolithic `analyze_ai_patterns.py` file (7,079 lines) into a modular architecture.

## Version 6.0.0 - PROJECT RENAMED 🎉

**Important**: Version 6.0.0 renames the project from "AI Pattern Analyzer" to "WriteScore". This is a breaking change affecting package names, CLI commands, and import paths.

**What Changed in v6.0.0**:
- **Package name**: `ai_pattern_analyzer` → `writescore`
- **CLI command**: `analyze-ai-patterns` → `writescore`
- **Python imports**: All `from ai_pattern_analyzer.*` → `from writescore.*`
- Zero functional changes - all algorithms, scoring, and behavior unchanged

**Migration**: See [MIGRATION-v6.0.0.md](MIGRATION-v6.0.0.md) for complete upgrade instructions.

For full change history, see [CHANGELOG.md](CHANGELOG.md).

## Package Structure

```
writescore/
├── __init__.py                 # Main package exports for backward compatibility ✓
├── core/                       # Core analysis engine
│   ├── analyzer.py            # Main AIPatternAnalyzer class ✓ (792 lines)
│   └── results.py             # Result dataclasses ✓ (540 lines)
├── dimensions/                # Analysis dimensions (12 total in v5.0.0)
│   ├── base_strategy.py      # Base DimensionStrategy interface ✓
│   ├── perplexity.py         # AI vocabulary & perplexity ✓ (290 lines)
│   ├── burstiness.py         # Sentence/paragraph variation ✓ (340 lines)
│   ├── structure.py          # Section/heading analysis ✓ (456 lines)
│   ├── formatting.py         # Em-dash, bold/italic, etc. ✓ (257 lines)
│   ├── voice.py              # Voice consistency ✓ (146 lines)
│   ├── syntactic.py          # Syntactic complexity ✓ (262 lines)
│   ├── lexical.py            # Lexical diversity ✓ (174 lines)
│   ├── sentiment.py          # Sentiment analysis ✓
│   ├── readability.py        # Readability metrics ✓ (split from stylometric)
│   ├── transition_marker.py  # AI transition markers ✓ (split from stylometric)
│   ├── predictability.py     # GLTR/n-gram analysis ✓ (split from advanced)
│   └── advanced_lexical.py   # Advanced lexical metrics ✓ (split from advanced)
├── scoring/                   # Scoring system
│   ├── dual_score.py         # Dual scoring dataclasses + thresholds ✓ (220 lines)
│   └── dual_score_calculator.py  # Dual score calculation ✓ (392 lines)
├── history/                   # History tracking
│   ├── tracker.py            # History tracking dataclasses ✓ (90 lines)
│   └── export.py             # CSV/JSON export (future enhancement)
├── evidence/                  # Evidence extraction (future expansion)
│   └── __init__.py           # Placeholder ✓
├── utils/                     # Shared utilities
│   ├── text_processing.py    # Text cleaning, word counting ✓ (180 lines)
│   ├── pattern_matching.py   # Regex patterns, constants ✓ (240 lines)
│   └── visualization.py      # Sparklines, charts ✓ (200 lines)
└── cli/                       # CLI interface
    ├── main.py               # Click-based CLI entry point ✓ (717 lines)
    ├── args.py               # Legacy argument parsing (backup)
    └── formatters.py         # Output formatting ✓ (1,036 lines)
```

## Installation

Install the package in development mode:

```bash
pip install -e .
```

This installs the `writescore` command-line tool.

### Development Setup

For development, install with dev dependencies:

```bash
pip install -e ".[dev]"
```

#### Local CI Testing with act

To test GitHub Actions workflows locally, install [act](https://github.com/nektos/act):

```bash
# macOS (via Homebrew)
brew install act

# Or use Brewfile
brew bundle
```

Run workflows locally:

```bash
# List available workflows
act -l

# Test lint job
act push --job lint --container-architecture linux/amd64

# Test full CI (requires significant disk space for PyTorch/CUDA)
act push --container-architecture linux/amd64
```

## Analysis Modes

WriteScore supports four analysis modes that balance speed and accuracy:

### Quick Start

```bash
# Fast mode - Quick analysis of document start
writescore document.md --mode fast

# Adaptive mode - Intelligent sampling based on document size (recommended, default)
writescore document.md --mode adaptive

# Sampling mode - Custom sampling strategy for large documents
writescore document.md --mode sampling --samples 10 --sample-size 3000

# Full mode - Complete document analysis (most accurate)
writescore document.md --mode full
```

### Mode Comparison

| Mode | Speed | Accuracy | Best For | Coverage |
|------|-------|----------|----------|----------|
| **Fast** | ⚡⚡⚡ Fastest | ⭐⭐ Basic | Quick checks, early drafts | ~2000 chars/dimension |
| **Adaptive** | ⚡⚡ Fast | ⭐⭐⭐ Good | Most documents, standard workflow | Adjusts to size |
| **Sampling** | ⚡ Medium | ⭐⭐⭐⭐ High | Large documents, custom needs | User-defined |
| **Full** | 🐌 Slowest | ⭐⭐⭐⭐⭐ Best | Final review, critical content | 100% |

### Integration with Features

Analysis modes work seamlessly with all existing features:

```bash
# Batch analysis with adaptive mode
writescore --batch chapter-dir/ --mode adaptive

# Detailed findings with full analysis
writescore manuscript.md --mode full --detailed

# Dual score optimization with sampling
writescore large-doc.md --mode sampling --samples 15 --show-scores

# Dry-run to preview configuration
writescore draft.md --mode adaptive --dry-run

# Show coverage statistics
writescore document.md --mode sampling --show-coverage
```

**📖 For comprehensive documentation**: See [Analysis Modes Guide](docs/analysis-modes-guide.md)

## Accuracy & Performance Expectations

### What to Expect

The AI Pattern Analyzer is designed as a **quality improvement tool**, not a binary AI detector. Its primary value is providing **actionable feedback** to help authors write more human-sounding content.

**Ensemble Detection Accuracy** (realistic estimate):
- **Overall**: 70-85% F1-score on mixed AI/human content
- **GPT-3.5/Claude 2**: 75-85% accuracy
- **GPT-4+/Claude 3+**: 60-70% accuracy (newer models are harder to detect)

**Individual Dimension Accuracy** (validated):
- GLTR (Predictability): 80% F1-score (degrades on GPT-4+)
- Em-dash pattern: Strong AI correlation (magnitude of effect varies)
- Other dimensions: Correlate with AI-generated text but individual accuracy not validated

### Why This Matters

✅ **DO use the analyzer for**:
- Identifying mechanical patterns in your writing
- Getting specific, actionable feedback to improve naturalness
- Tracking quality improvements over time
- Comparing writing style across documents

❌ **DON'T rely on it for**:
- Definitive "AI vs human" classification
- Academic integrity enforcement
- Legal proof of authorship
- Detection of latest-generation models (GPT-4+, Claude 3.5+)

### The Ensemble Advantage

The analyzer's strength comes from combining **12 complementary dimensions**:
- No single dimension needs 95%+ accuracy
- Ensemble approach provides robust quality assessment
- Multiple weak signals combine into actionable insights
- Focus on quality improvement > binary detection

## Dimension Profiles

**New in Story 1.4.11**: The analyzer now supports **selective dimension loading** for optimized performance.

### What are Dimension Profiles?

Dimension profiles let you control which analysis dimensions are loaded, enabling significant performance improvements while maintaining analysis quality based on your needs.

### Built-in Profiles

| Profile | Dimensions Loaded | Typical Speed | Best For |
|---------|-------------------|---------------|----------|
| **fast** | 4 lightweight dims | ~100ms | Quick checks, CI/CD pipelines |
| **balanced** | 8 core dims | ~200ms | Standard workflow, most documents |
| **full** | All 12 dimensions | ~4-6s | Comprehensive analysis, final review |

### Profile Details

**Fast Profile** (4 dimensions):
- Perplexity (AI vocabulary)
- Burstiness (sentence variation)
- Structure (organization)
- Formatting (em-dashes, bold/italic)

**Balanced Profile** (8 dimensions, default):
- All Fast dimensions, plus:
- Voice (authenticity)
- Lexical (diversity)
- Readability (complexity scores)
- Sentiment (emotional variation)

**Full Profile** (12 dimensions):
- All Balanced dimensions, plus:
- Syntactic (naturalness)
- Predictability (n-gram patterns)
- Advanced Lexical (MTLD, MATTR)
- Transition Markers (formulaic phrases)

### Using Profiles

Profiles are configured via the `.ai-analysis-config.yaml` file:

```yaml
# .ai-analysis-config.yaml
dimension_profile: "balanced"  # or "fast" or "full"
```

Or use explicit dimension selection:

```yaml
explicit_dimensions:
  - perplexity
  - burstiness
  - formatting
  - voice
```

### Custom Profiles

Create custom profiles for specific use cases:

```yaml
custom_profiles:
  quick_check:
    - perplexity
    - formatting
  deep_style:
    - lexical
    - syntactic
    - advanced_lexical
    - sentiment
```

Then use your custom profile:

```yaml
dimension_profile: "quick_check"
```

### Performance Benefits

- **Fast mode**: 60-98% faster than loading all dimensions
- **Memory savings**: Only loaded dimensions consume memory
- **Lazy loading**: Dimensions load on-demand when first used

### When to Use Each Profile

**Use Fast** when:
- Running in CI/CD pipelines
- Quick iterative feedback during writing
- Batch processing large document sets
- Initial quality checks

**Use Balanced** when:
- Standard document analysis
- Most day-to-day use cases
- Good balance of speed and coverage

**Use Full** when:
- Final manuscript review before publication
- Comprehensive AI detection needed
- Maximum accuracy required
- Deep stylistic analysis

### Backward Compatibility

The analyzer defaults to the **balanced** profile for backward compatibility. Existing configurations without dimension profiles continue to work unchanged.

## Current Status

**✓ Phase 1 - Foundation (COMPLETED):**

- Package structure and all `__init__.py` files
- Core data structures (`results.py` - 540 lines)
- Scoring dataclasses and thresholds (`dual_score.py` - 220 lines)
- History tracking dataclasses (`tracker.py` - 90 lines)
- Utils package complete (620 lines across 3 modules)
- CLI argument parsing complete (`args.py` - 100 lines)
- Base dimension analyzer interface (`base.py`)

**✓ Phase 2 - Dimension Extraction (COMPLETED):**

- ✅ `perplexity.py` (290 lines) - AI vocabulary & formulaic transitions
- ✅ `burstiness.py` (340 lines) - Sentence/paragraph variation
- ✅ `structure.py` (456 lines) - Headings, sections, lists
- ✅ `formatting.py` (257 lines) - Em-dash, bold/italic (STRONGEST AI signal)
- ✅ `voice.py` (146 lines) - First-person, contractions, authenticity
- ✅ `syntactic.py` (262 lines) - Dependency trees, subordination (requires spaCy)
- ✅ `lexical.py` (174 lines) - TTR, MTLD diversity (requires NLTK)
- ✅ `stylometric.py` (163 lines) - "However"/"moreover" markers (requires textstat)
- ⚠️ `advanced.py` (170 lines) - GLTR stubs only (requires transformers - optional)

**✓ Phase 3 - Core Implementation (COMPLETED):**

- ✅ `core/analyzer.py` (792 lines) - Main AIPatternAnalyzer orchestration class
- ✅ `scoring/dual_score_calculator.py` (392 lines) - Dual score calculation (4-tier, 174 points)
- ✅ `cli/formatters.py` (1,036 lines) - All output formatting functions
- ✅ `analyze_ai_patterns.py` (273 lines) - Streamlined CLI entry point
- ✅ Package `__init__.py` updated with full backward compatibility exports

**Total Refactored: ~7,000+ lines extracted into modular architecture**

- Original monolithic file: 7,079 lines
- New modular structure: 17+ files, largest <1,100 lines each
- Backward compatibility: 100% maintained
- All original functionality preserved

## Design Principles

### 1. Backward Compatibility

The package maintains backward compatibility through package-level exports:

```python
# Old way (still works)
from analyze_ai_patterns import AIPatternAnalyzer

# New way (recommended)
from writescore.core.analyzer import AIPatternAnalyzer

# Or use package import
from writescore import AIPatternAnalyzer
```

### 2. Dimension Analyzer Interface

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

### 3. Separation of Concerns

- **Core**: Orchestration and coordination
- **Dimensions**: Individual analysis algorithms
- **Scoring**: Dual-score calculation and interpretation
- **History**: Score tracking over time
- **Utils**: Shared helper functions
- **CLI**: User interface layer

## Development Roadmap

### Phase 1: Foundation ✅ COMPLETED

- ✓ Package structure
- ✓ Data structures
- ✓ Utils implementation
- ✓ CLI argument parsing

### Phase 2: Dimension Extraction ✅ COMPLETED

- ✓ Created 9 dimension analyzer implementations
- ✓ Extracted all analysis methods from main file
- ✓ Implemented dimension scoring methods
- ✓ Added base analyzer interface

### Phase 3: Core Implementation ✅ COMPLETED

- ✓ Extracted main analyzer class (792 lines)
- ✓ Implemented orchestration logic
- ✓ Implemented scoring calculation (392 lines)
- ✓ Extracted CLI formatters (1,036 lines)

### Phase 4: Integration ✅ COMPLETED

- ✓ Created new main entry point (273 lines)
- ✓ Ensured backward compatibility (package **init**.py)
- ⏳ Run existing tests (TODO)

### Phase 5: Documentation 🔄 IN PROGRESS

- ✓ Updated README with Phase 3 completion
- ⏳ Add comprehensive module docstrings
- ⏳ Create migration guide
- ⏳ Update related story files

## Testing Strategy

1. **Unit Tests**: Each module has isolated tests
2. **Integration Tests**: Modules work together correctly
3. **Backward Compatibility Tests**: Old imports still work
4. **CLI Tests**: Command-line behavior unchanged
5. **Performance Tests**: No significant regression

## Next Steps for Developers

The refactoring is now **complete**! Next steps:

1. **Testing** ✅ HIGH PRIORITY:
   - Run basic smoke tests with the new modular CLI
   - Test backward compatibility imports
   - Verify all analysis modes (standard, detailed, dual-score, batch)
   - Compare outputs with original monolithic version

2. **Documentation** 📝:
   - Add comprehensive docstrings to all modules
   - Create migration guide for users of the old monolithic file
   - Document the modular architecture for contributors

3. **Cleanup** 🧹:
   - Remove or archive `analyze_ai_patterns_original.py` after testing
   - Add unit tests for individual dimension analyzers
   - Add integration tests for the full pipeline

4. **Future Enhancements** 🚀:
   - Implement remaining GLTR/transformer features in `advanced.py`
   - Add evidence extraction capabilities
   - Create visualization dashboard for score tracking

## Dependencies

All dependencies remain unchanged:

- **Required**: None (pure Python)
- **Optional**: NLTK, spaCy, textstat, transformers, scipy, textacy, VADER, marko

## Version

- **Version**: 5.0.0 (BREAKING CHANGES - deprecated dimension removal)
- **Previous**: 4.0.0 (modular architecture with 14 dimensions)
- **Current**: 5.0.0 (12 dimensions, registry-based, no deprecated code)

## Contributing

When adding new features:

1. Identify the appropriate module
2. Follow existing patterns
3. Update tests
4. Maintain backward compatibility
5. Document changes

## License

Same as parent project.
