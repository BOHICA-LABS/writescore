# Migration Guide: v4.x → v5.0.0

**BREAKING CHANGES** - This is a major version release that removes deprecated dimensions and backward compatibility code from v4.x.

## Overview

Version 5.0.0 removes the deprecated `advanced` and `stylometric` dimensions that were split into focused dimensions in v4.x Story 1.4.5. This cleanup removes ~1,033 lines of deprecated code and backward compatibility shims.

**Key Changes**:
- Removed deprecated dimensions: `advanced`, `stylometric`
- Updated from 14 to 12 dimensions
- Removed backward compatibility dataclasses and properties
- All scoring regression tests passing (baselines unchanged)

## Breaking Changes

### 1. Dimension Count Change

**What Changed**: The analyzer now reports 12 dimensions instead of 14.

**Impact**: Code checking dimension count will need updates.

**Before (v4.x)**:
```python
analyzer = AIPatternAnalyzer()
assert len(analyzer.dimensions) == 14  # ❌ FAILS in v5.0.0
```

**After (v5.0.0)**:
```python
analyzer = AIPatternAnalyzer()
assert len(analyzer.dimensions) == 12  # ✅ CORRECT

# Or use the dimension_count field from analysis results
results = analyzer.analyze(text)
assert results.dimension_count == 12
```

### 2. Removed Dimensions

#### Deprecated: `advanced` dimension

**Reason**: Split into `predictability` and `advanced_lexical` in Story 1.4.5 for single responsibility.

**Before (v4.x)**:
```python
# OLD - AdvancedDimension handled both GLTR and advanced lexical
advanced_dim = analyzer.dimensions.get('advanced')
results = advanced_dim.analyze(text)

# GLTR score
gltr_score = results['gltr_score']

# Advanced lexical metrics
mtld_score = results['mtld_score']
mattr_score = results['mattr_score']
```

**After (v5.0.0)**:
```python
# NEW - Use split dimensions
predictability_dim = analyzer.dimensions.get('predictability')
advanced_lexical_dim = analyzer.dimensions.get('advanced_lexical')

# GLTR analysis (now in PredictabilityDimension)
pred_results = predictability_dim.analyze(text)
gltr_score = pred_results.get('gltr_rank_1_proportion', 0.0)

# Advanced lexical metrics (now in AdvancedLexicalDimension)
lex_results = advanced_lexical_dim.analyze(text)
mtld_score = lex_results.get('mtld_score', 0.0)
mattr_score = lex_results.get('mattr_score', 0.0)
```

#### Deprecated: `stylometric` dimension

**Reason**: Split into `readability` and `transition_marker` in Story 1.4.5 for single responsibility.

**Before (v4.x)**:
```python
# OLD - StylometricDimension handled both readability and transition markers
stylometric_dim = analyzer.dimensions.get('stylometric')
results = stylometric_dim.analyze(text)

# Readability metrics
flesch_score = results['flesch_reading_ease']
gunning_fog = results['gunning_fog']

# Transition markers
however_count = results['however_count']
moreover_count = results['moreover_count']
```

**After (v5.0.0)**:
```python
# NEW - Use split dimensions
readability_dim = analyzer.dimensions.get('readability')
transition_dim = analyzer.dimensions.get('transition_marker')

# Readability metrics (now in ReadabilityDimension)
read_results = readability_dim.analyze(text)
flesch_score = read_results.get('flesch_reading_ease', 0.0)
gunning_fog = read_results.get('gunning_fog', 0.0)

# Transition markers (now in TransitionMarkerDimension)
trans_results = transition_dim.analyze(text)
however_count = trans_results.get('however_count', 0)
moreover_count = trans_results.get('moreover_count', 0)
```

### 3. Removed Backward Compatibility Properties

#### Removed: `gltr_score` property from `AnalysisResults`

**Reason**: Backward compatibility shim from Story 1.4.5 split.

**Before (v4.x)**:
```python
results = analyzer.analyze(text)

# Property redirect (backward compatibility)
gltr_score = results.gltr_score  # ❌ REMOVED in v5.0.0
```

**After (v5.0.0)**:
```python
results = analyzer.analyze(text)

# Use direct field
predictability_score = results.predictability_score  # ✅ CORRECT
```

#### Removed: `stylometric_score` field from `AnalysisResults`

**Reason**: Dimension split into `readability` and `transition_marker`.

**Before (v4.x)**:
```python
results = analyzer.analyze(text)
stylometric_score = results.stylometric_score  # ❌ REMOVED in v5.0.0
```

**After (v5.0.0)**:
```python
results = analyzer.analyze(text)

# Use split scores
readability_score = results.readability_score  # ✅ CORRECT
transition_marker_score = results.transition_marker_score  # ✅ CORRECT
```

### 4. Removed Dataclasses

#### Removed: `StylometricIssue` dataclass

**Reason**: Replaced by `TransitionInstance` with updated field names.

**Before (v4.x)**:
```python
from writescore.core.results import StylometricIssue

# OLD dataclass
issue = StylometricIssue(
    line_number=42,
    marker_type='however',  # ❌ Field renamed
    context='However, this is...',
    suggestion='Replace with: "But"'  # ❌ Now a list
)

# Field access
print(issue.marker_type)  # ❌ REMOVED in v5.0.0
```

**After (v5.0.0)**:
```python
from writescore.core.results import TransitionInstance

# NEW dataclass with updated fields
issue = TransitionInstance(
    line_number=42,
    transition='however',  # ✅ Renamed from marker_type
    context='However, this is...',
    suggestions=['Replace with: "But"', 'Use natural flow']  # ✅ Now a list
)

# Field access
print(issue.transition)  # ✅ CORRECT
print(issue.suggestions)  # ✅ Returns list
```

### 5. Removed CLI Output Section

**What Changed**: The stylometric markers section in detailed reports has been removed.

**Before (v4.x)**:
```bash
$ writescore document.md --detailed

# Output included section:
=== Stylometric Analysis ===
- However usage: 5 instances
- Moreover usage: 2 instances
# ... (48 lines of output)
```

**After (v5.0.0)**:
```bash
$ writescore document.md --detailed

# Transition marker information now reported through standard dimension output:
=== Transition Marker Analysis ===
Score: 75.0/100
Recommendations:
- Reduce AI transition markers (7.2 per 1k words, target ≤2.0)
# ... (standard dimension output format)
```

## Migration Checklist

Use this checklist to ensure your code is v5.0.0 compatible:

- [ ] **Update dimension count checks**: Change `14` → `12`
- [ ] **Replace `advanced` dimension references**: Use `predictability` and `advanced_lexical`
- [ ] **Replace `stylometric` dimension references**: Use `readability` and `transition_marker`
- [ ] **Update field access**: Replace `gltr_score` property with `predictability_score` field
- [ ] **Update field access**: Replace `stylometric_score` with `readability_score` + `transition_marker_score`
- [ ] **Update imports**: Replace `StylometricIssue` with `TransitionInstance`
- [ ] **Update field names**: Change `marker_type` → `transition`, `suggestion` → `suggestions` (list)
- [ ] **Test your integration**: Run your test suite against v5.0.0
- [ ] **Verify scoring behavior**: Ensure dual scores and baselines match v4.x output

## Current Dimension List (v5.0.0)

The 12 dimensions in v5.0.0 are:

1. **perplexity** - AI vocabulary detection
2. **burstiness** - Sentence variation patterns
3. **structure** - Document organization
4. **formatting** - Em-dashes, emphasis markers
5. **voice** - Authenticity and first-person usage
6. **readability** - Flesch, Gunning Fog, etc. (split from stylometric)
7. **lexical** - Basic lexical diversity (TTR)
8. **sentiment** - Sentiment variation analysis
9. **syntactic** - Syntactic complexity and naturalness
10. **predictability** - GLTR/n-gram patterns (split from advanced)
11. **advanced_lexical** - MTLD, MATTR metrics (split from advanced)
12. **transition_marker** - AI transition markers (split from stylometric)

## Backward Compatibility Notes

### What Still Works

- **Package imports**: All existing import paths still work
- **Main API**: `AIPatternAnalyzer` interface unchanged
- **Scoring system**: Dual scores and thresholds unchanged
- **History tracking**: History files from v4.x load correctly
- **CLI commands**: All CLI flags and options work unchanged

### What No Longer Works

- **Direct dimension access**: `dimensions.get('advanced')` → returns `None`
- **Deprecated properties**: `results.gltr_score` → raises `AttributeError`
- **Old dataclasses**: `StylometricIssue` → import fails with `ImportError`
- **Dimension count checks**: Code expecting 14 dimensions will fail assertions

## Testing Your Migration

### 1. Run Your Test Suite

```bash
# Activate your environment
source nlp-env/bin/activate

# Run your tests
pytest tests/ -v
```

### 2. Verify Dimension Access

```python
from writescore import AIPatternAnalyzer

analyzer = AIPatternAnalyzer()

# Verify dimension count
assert analyzer.get_count() == 12, "Expected 12 dimensions in v5.0.0"

# Verify new dimensions exist
assert analyzer.has('predictability'), "PredictabilityDimension missing"
assert analyzer.has('advanced_lexical'), "AdvancedLexicalDimension missing"
assert analyzer.has('readability'), "ReadabilityDimension missing"
assert analyzer.has('transition_marker'), "TransitionMarkerDimension missing"

# Verify old dimensions removed
assert not analyzer.has('advanced'), "AdvancedDimension should be removed"
assert not analyzer.has('stylometric'), "StylometricDimension should be removed"

print("✅ All dimension checks passed!")
```

### 3. Verify Analysis Results

```python
from writescore import AIPatternAnalyzer

analyzer = AIPatternAnalyzer()
text = "Your test document text here..."

results = analyzer.analyze(text)

# Verify field access
assert hasattr(results, 'predictability_score'), "predictability_score missing"
assert hasattr(results, 'advanced_lexical_score'), "advanced_lexical_score missing"
assert hasattr(results, 'readability_score'), "readability_score missing"
assert hasattr(results, 'transition_marker_score'), "transition_marker_score missing"

# Verify old fields removed
assert not hasattr(results, 'gltr_score'), "gltr_score should be removed"
assert not hasattr(results, 'stylometric_score'), "stylometric_score should be removed"

print("✅ All field checks passed!")
```

## Getting Help

If you encounter issues migrating to v5.0.0:

1. **Review the CHANGELOG**: See [CHANGELOG.md](../CHANGELOG.md) for complete v5.0.0 details
2. **Check test examples**: See `tests/integration/test_backward_compatibility.py` for migration patterns
3. **Open an issue**: Report migration problems with code examples

## Summary

Version 5.0.0 completes the dimension refactoring started in v4.x Story 1.4.5 by removing deprecated code. The migration is straightforward:

- **Update dimension references**: Use split dimensions (`predictability`, `advanced_lexical`, `readability`, `transition_marker`)
- **Update field access**: Use direct fields instead of backward compatibility properties
- **Update dataclass imports**: Use `TransitionInstance` instead of `StylometricIssue`
- **Update dimension count checks**: Change `14` → `12`

All scoring behavior remains unchanged - only the internal organization has been cleaned up.
