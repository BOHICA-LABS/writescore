# Analysis Configuration Guide

**Story 1.4.6**: Configuration infrastructure added - full implementation in Story 1.4.7.

## Overview

The AI Pattern Analyzer now supports configurable analysis modes to handle different document sizes efficiently.

## AnalysisConfig Class

### Analysis Modes

```python
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode

# Available modes
AnalysisMode.FAST       # Truncate to 2000 chars (current default behavior)
AnalysisMode.ADAPTIVE   # Adapt to document length (recommended)
AnalysisMode.SAMPLING   # Sample N sections, aggregate results
AnalysisMode.FULL       # Analyze entire document (use for small docs)
AnalysisMode.STREAMING  # Progressive analysis (future - Story 1.4.7+)
```

### Basic Usage

```python
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode

# Create analyzer
analyzer = AIPatternAnalyzer()

# Option 1: Use default (current behavior - FAST mode equivalent)
results = analyzer.analyze_file("document.md")

# Option 2: Use FAST mode explicitly
config = AnalysisConfig(mode=AnalysisMode.FAST)
results = analyzer.analyze_file("document.md", config=config)

# Option 3: Use ADAPTIVE mode (future default - Story 1.4.7)
config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)
results = analyzer.analyze_file("document.md", config=config)

# Option 4: Use SAMPLING mode for large documents
config = AnalysisConfig(
    mode=AnalysisMode.SAMPLING,
    sampling_sections=5,
    sampling_chars_per_section=2000,
    sampling_strategy="weighted"
)
results = analyzer.analyze_file("large_chapter.md", config=config)
```

### Configuration Options

```python
config = AnalysisConfig(
    mode=AnalysisMode.ADAPTIVE,                # Analysis mode
    sampling_sections=5,                       # Number of samples (SAMPLING mode)
    sampling_chars_per_section=2000,           # Chars per sample
    sampling_strategy="even",                  # "even", "weighted", "adaptive"
    max_text_length=None,                      # Optional hard limit
    max_analysis_time_seconds=300,             # Timeout (5 min default)
    dimension_overrides={                      # Dimension-specific overrides
        "predictability": {"max_chars": 5000}
    },
    enable_detailed_analysis=True              # Enable detailed metrics
)
```

## Mode Behaviors (Story 1.4.6 - Infrastructure Only)

### FAST Mode
- **Behavior**: Truncates to 2000 characters
- **Use Case**: Quick analysis, small snippets
- **Performance**: 5-15 seconds
- **Accuracy**: Good for short documents (<2000 chars)

### ADAPTIVE Mode (Recommended)
- **Behavior**:
  - Small docs (<5000 chars): Analyze fully
  - Medium docs (5000-50000 chars): Analyze first 10k chars
  - Large docs (>50000 chars): Use sampling (5 sections)
- **Use Case**: General purpose, handles any document size
- **Performance**: Scales with document size
- **Accuracy**: High for all document sizes

### SAMPLING Mode
- **Behavior**: Always samples N sections, aggregates metrics
- **Use Case**: Very large documents, consistent sampling
- **Performance**: Predictable (N × per-section cost)
- **Accuracy**: Representative of full document

### FULL Mode
- **Behavior**: Analyzes entire document without truncation
- **Use Case**: Small documents where full analysis is fast
- **Performance**: Scales linearly with document length
- **Accuracy**: Highest (analyzes everything)

## Sampling Strategies

### Even Sampling
Samples evenly spaced sections:
```python
config = AnalysisConfig(
    mode=AnalysisMode.SAMPLING,
    sampling_strategy="even"
)
```

### Weighted Sampling
Emphasizes beginning and end (intro/conclusion):
```python
config = AnalysisConfig(
    mode=AnalysisMode.SAMPLING,
    sampling_strategy="weighted"
)
```

### Adaptive Sampling
Detects section boundaries (markdown headings):
```python
config = AnalysisConfig(
    mode=AnalysisMode.SAMPLING,
    sampling_strategy="adaptive"
)
```

## Dimension-Specific Overrides

Override settings for specific dimensions:

```python
config = AnalysisConfig(
    mode=AnalysisMode.FAST,
    dimension_overrides={
        "predictability": {"max_chars": 5000},  # GLTR on 5k instead of 2k
        "syntactic": {"max_chars": 3000}
    }
)
```

## Backward Compatibility

All existing code continues to work without modification:

```python
# Old code (still works - uses DEFAULT_CONFIG internally)
analyzer = AIPatternAnalyzer()
results = analyzer.analyze_file("document.md")

# Equivalent new code
analyzer = AIPatternAnalyzer()
results = analyzer.analyze_file("document.md", config=None)
```

## Implementation Status

**Story 1.4.6 (Current)**: Infrastructure only
- ✅ AnalysisConfig class created
- ✅ Config parameter added to all 14 dimensions
- ✅ Config threaded through analyzer.py
- ⏳ Default behavior unchanged (FAST mode equivalent)
- ⏳ Full mode implementations pending (Story 1.4.7)

**Story 1.4.7 (Next)**: Full document analysis
- ⏳ Implement sampling in heavy dimensions (Predictability, AdvancedLexical, Syntactic)
- ⏳ Enable ADAPTIVE/SAMPLING/FULL modes
- ⏳ Test with book chapters (90 pages / 180k chars)

## Performance Expectations

| Mode | 10-page doc | 90-page doc | Notes |
|------|------------|------------|-------|
| FAST | 5-15s | 5-15s | Always truncates to 2k |
| ADAPTIVE | 5-15s | 20-40s | Samples large docs |
| SAMPLING | 15-30s | 15-30s | Consistent (5 sections) |
| FULL | 5-15s | 90-180s | Linear scaling |

*Note: Timings are estimates for Story 1.4.7 implementation. Current (1.4.6) behavior matches FAST mode.*

## References

- **Story 1.4.6**: Analysis Configuration Infrastructure (this release)
- **Story 1.4.7**: Enable Full Document GLTR Analysis
- **Story 1.4.8**: Optimize Other Heavy Dimensions
- **Story 1.4.9**: CLI Integration

## Support

For questions or issues, see: [GitHub Issues](https://github.com/jmagady/writescore/issues)
