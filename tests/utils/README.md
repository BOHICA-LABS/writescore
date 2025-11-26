# Test Utilities

This directory contains utility scripts for test infrastructure.

## capture_baselines.py

**Purpose**: Capture baseline scores for regression testing.

**Description**:
Analyzes all samples in the regression test corpus (`tests/fixtures/regression_corpus.json`) with all 12 dimensions and saves baseline scores to `tests/fixtures/baseline_scores.json`.

**Usage**:
```bash
python tests/utils/capture_baselines.py
```

**Output**:
- `tests/fixtures/baseline_scores.json` - Baseline scores for all samples

**When to Run**:
1. Initial baseline creation
2. After intentional dimension logic changes
3. After major dependency updates
4. When adding new samples to corpus

**Example Output**:
```
================================================================================
BASELINE SCORE CAPTURE
================================================================================

Loading corpus from: tests/fixtures/regression_corpus.json
Loaded 25 samples

Initializing 12 dimensions...
Initialized: predictability, advanced_lexical, readability, ...

================================================================================
ANALYZING SAMPLES
================================================================================

[1/25] Analyzing ai_sample_01 (ai_generated)...
  ✓ predictability        75.0
  ✓ advanced_lexical      50.0
  ...

✅ Baselines saved to: tests/fixtures/baseline_scores.json
   Total samples: 25
   Dimensions per sample: 12
   Total baseline scores: 300
```

**Implementation Details**:
- Initializes all 12 dimensions
- Analyzes each corpus sample
- Rounds scores to 1 decimal place
- Captures metadata (version, timestamp, dependencies)
- Error handling for dimension failures

**Dependencies**:
- All 12 dimension classes
- JSON for corpus/baseline I/O
- Python 3.8+

---

*Last Updated: 2025-11-06*
*Story: 1.4.13 - Add Scoring Regression Test Suite*
