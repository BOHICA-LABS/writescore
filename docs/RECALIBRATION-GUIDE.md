# WriteScore Recalibration Guide

This guide explains how to recalibrate WriteScore's scoring parameters when new AI models emerge or when drift is detected in production scores.

## Table of Contents

1. [Overview](#overview)
2. [When to Recalibrate](#when-to-recalibrate)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Workflow](#step-by-step-workflow)
5. [Interpreting Reports](#interpreting-reports)
6. [Decision Criteria](#decision-criteria)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)
9. [CLI Reference](#cli-reference)

---

## Overview

WriteScore uses **percentile-anchored parameters** that adapt to empirical distributions from validation data. Instead of hardcoded thresholds like `target = 10.0`, parameters are derived from actual human and AI writing distributions:

- `target = p50_human` (50th percentile of human distribution)
- `width = σ_human` (standard deviation of human distribution)
- `threshold_low = p25_human`, `threshold_high = p75_human`

This approach provides:
- **Automatic adaptation** when AI models evolve
- **Reduced maintenance** (no manual parameter tuning)
- **Better interpretability** (scores map to percentile rankings)

---

## When to Recalibrate

### Trigger 1: New Major AI Model Release

**When**: Within 30 days of a new major AI model's public API availability (e.g., GPT-5, Claude 4, Gemini 2).

**Why**: New models may have different text characteristics that shift AI distributions.

**Action**:
1. Generate 200+ documents from the new model across all domains
2. Add to validation dataset
3. Run recalibration
4. Review shift report
5. Deploy if shifts are acceptable

### Trigger 2: Quarterly Drift Detection

**When**: Average detection scores shift > 5 points from baseline over a 3-month period.

**Monitoring**:
```bash
# Track quarterly score averages on production samples
# Compare against established baseline
```

**Action**:
1. Investigate: Are users submitting different content types?
2. Validate on fresh human/AI samples
3. Recalibrate if drift is confirmed

### Trigger 3: Performance Degradation

**When**: F1 score drops > 2 percentage points (e.g., 0.85 → 0.83) sustained for 3 months.

**Action**:
1. Analyze which dimensions show increased errors
2. Investigate AI model landscape changes
3. Recalibrate focusing on underperforming dimensions

### Trigger 4: Validation Dataset Expansion

**When**: Adding a new domain OR 25%+ increase in validation set size.

**Action**:
1. Run distribution analysis on new data only
2. Compare distributions (KS test)
3. Full recalibration if significant shift detected

### Trigger 5: Annual Preventive Maintenance

**When**: Every 12 months, regardless of drift metrics.

**Action**:
1. Refresh validation dataset (replace oldest 20%)
2. Run full recalibration
3. Compare parameters (expect < 10% change)

### When NOT to Recalibrate

- Minor model updates (GPT-4 → GPT-4-turbo): Monitor only
- Small dataset additions (< 10% increase): Update metadata only
- Score shifts < 2 points: Within normal variance
- Single-month F1 dip: Wait for 3-month trend

---

## Prerequisites

### 1. Validation Dataset

You need a labeled validation dataset in JSON Lines format:

```json
{"id": "doc_001", "text": "...", "label": "human", "domain": "academic"}
{"id": "doc_002", "text": "...", "label": "ai", "ai_model": "gpt-4", "domain": "business"}
```

**Minimum requirements**:
- 1000+ human documents
- 1000+ AI documents (200+ per model)
- Distribution: 40% academic, 30% social, 30% business

### 2. Current Parameters (Optional)

If you have existing parameters to compare against:
```
config/scoring_parameters.yaml
```

### 3. Installed WriteScore

```bash
pip install -e .
writescore --help
```

---

## Step-by-Step Workflow

### Step 1: Prepare Validation Dataset

Ensure your dataset is properly formatted and labeled:

```bash
# Verify dataset structure
head -5 validation_data/v2.0.jsonl

# Check label distribution
grep -c '"label": "human"' validation_data/v2.0.jsonl
grep -c '"label": "ai"' validation_data/v2.0.jsonl
```

### Step 2: Run Dry-Run Recalibration

Preview what recalibration would do without making changes:

```bash
writescore recalibrate validation_data/v2.0.jsonl --dry-run
```

This shows:
- Dataset statistics
- Dimensions to be analyzed
- Expected parameter changes

### Step 3: Run Full Recalibration

```bash
writescore recalibrate validation_data/v2.0.jsonl \
  --existing config/scoring_parameters.yaml \
  --output config/scoring_parameters_v2.yaml \
  --report reports/recalibration_$(date +%Y%m%d).json \
  --text-report reports/recalibration_$(date +%Y%m%d).txt
```

### Step 4: Review the Report

Check the text report for:
- Parameter changes per dimension
- Score shift analysis
- Warnings or errors

```bash
cat reports/recalibration_$(date +%Y%m%d).txt
```

### Step 5: Validate Parameters

Run the validation suite:

```bash
python -m pytest tests/integration/test_scoring_regression.py -v
```

### Step 6: Deploy (If Acceptable)

```bash
# Preview deployment checklist
writescore deploy config/scoring_parameters_v2.yaml --dry-run

# Deploy with confirmation
writescore deploy config/scoring_parameters_v2.yaml
```

### Step 7: Verify Deployment

```bash
# Check current version
writescore versions

# Run smoke test on sample document
writescore analyze sample_document.md --show-scores
```

---

## Interpreting Reports

### Recalibration Report Structure

```
================================================================================
RECALIBRATION SUMMARY
================================================================================
Dataset Version: v2.0
Total Documents: 2500
Dimensions Analyzed: 16
  - New: 0
  - Modified: 8

Parameter Changes:
  [MODIFIED] burstiness
    target: 10.2 → 11.5 (+12.7%)
    width: 2.3 → 2.1 (-8.7%)
  [MODIFIED] lexical
    threshold_low: 0.55 → 0.58 (+5.5%)
    threshold_high: 0.72 → 0.70 (-2.8%)
  [NO CHANGE] readability
  ...
```

### Understanding Parameter Changes

| Change Type | Meaning |
|-------------|---------|
| `[NEW]` | Dimension added (wasn't in previous params) |
| `[MODIFIED]` | Parameter values changed |
| `[NO CHANGE]` | Parameters unchanged |

### Score Shift Analysis

```
SCORE SHIFT ANALYSIS
================================================================================
Mean Total Shift: 3.2 points
Maximum Shift: 12.5 points
Documents with Warning Shift (>10 pts): 15
Documents with Error Shift (>15 pts): 2

Per-Dimension Mean Shifts:
  burstiness: +2.1 points
  lexical: -1.5 points
  sentiment: +0.8 points
```

**Interpretation**:
- Mean shift < 5 points: **Acceptable** - proceed with deployment
- Mean shift 5-10 points: **Warning** - review carefully
- Mean shift > 10 points: **Error** - investigate before deploying

---

## Decision Criteria

### Minimum Dataset Size

| Category | Minimum Documents |
|----------|-------------------|
| Human (total) | 1000+ |
| AI (total) | 1000+ |
| AI (per model) | 200+ |
| Per domain | 300+ |

### Acceptable Score Shifts

| Metric | Threshold | Action |
|--------|-----------|--------|
| Mean shift | < 5 points | Acceptable |
| Mean shift | 5-10 points | Review required |
| Mean shift | > 10 points | Investigate, consider rollback |
| Max shift | < 15 points | Acceptable |
| Max shift | > 15 points | Flag affected documents |

### Performance Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| F1 change | < 2% drop | Acceptable |
| F1 change | 2-5% drop | Review dimensions |
| F1 change | > 5% drop | Do not deploy |
| Detection accuracy | < 1% drop | Acceptable |

---

## Troubleshooting

### Problem: "Insufficient data for percentile estimation"

**Cause**: Not enough documents in validation set (< 50 per category).

**Solution**:
1. Add more documents to validation dataset
2. Or use `--use-fallback` to use literature-based defaults:
   ```bash
   writescore recalibrate dataset.jsonl --use-fallback
   ```

### Problem: "Extreme outliers affecting parameters"

**Cause**: Validation set contains documents with unusual characteristics.

**Solution**:
1. Review outliers in the distribution analysis
2. Consider removing or capping extreme values
3. Use IQR-based width (more robust than stdev)

### Problem: "Large score shifts detected"

**Cause**: AI model characteristics have changed significantly.

**Solution**:
1. Review which dimensions shifted most
2. Check if new AI model was added correctly
3. Consider gradual rollout (deploy to staging first)
4. If unacceptable, rollback:
   ```bash
   writescore rollback --version 1.0
   ```

### Problem: "Distribution assumption violations"

**Cause**: Data doesn't follow expected distribution (e.g., bimodal instead of normal).

**Solution**:
1. Check Q-Q plots in analysis output
2. Consider using different scoring type for dimension
3. Use IQR-based parameters instead of stdev-based

### Problem: "Parameter validation failed"

**Cause**: Derived parameters violate constraints (e.g., negative width, inverted thresholds).

**Solution**:
1. Check validation errors in log
2. Review dimension statistics for anomalies
3. May indicate data quality issue - review validation set

---

## Examples

### Example 1: Adding GPT-5 to Validation Dataset

1. **Generate GPT-5 samples**:
   ```bash
   python scripts/generate_ai_samples.py \
     --model gpt-5 \
     --count 200 \
     --domains academic,social,business \
     --output validation_data/ai_gpt5.jsonl
   ```

2. **Merge into validation dataset**:
   ```bash
   cat validation_data/v2.0.jsonl validation_data/ai_gpt5.jsonl > validation_data/v2.1.jsonl
   ```

3. **Run recalibration**:
   ```bash
   writescore recalibrate validation_data/v2.1.jsonl \
     --existing config/scoring_parameters.yaml \
     --output config/scoring_parameters_v2.1.yaml \
     --report reports/gpt5_recalibration.json
   ```

4. **Review and deploy**:
   ```bash
   writescore diff 2.0 2.1 --detailed
   writescore deploy config/scoring_parameters_v2.1.yaml
   ```

### Example 2: Recalibrating After Claude 4 Release

Similar to Example 1, but also consider:

1. **Compare Claude 3 vs Claude 4 distributions**:
   ```bash
   # Run analysis on Claude-4-only subset
   writescore recalibrate claude4_samples.jsonl --dry-run
   ```

2. **Check if Claude 4 differs significantly from Claude 3**:
   - If similar: Add to existing validation set
   - If different: May need higher weighting for newer model

### Example 3: Domain-Specific Recalibration

For specialized content (e.g., legal documents):

1. **Create domain-specific validation set**:
   ```bash
   # Filter validation data for legal domain
   grep '"domain": "legal"' validation_data/full.jsonl > validation_data/legal.jsonl
   ```

2. **Run domain-focused recalibration**:
   ```bash
   writescore recalibrate validation_data/legal.jsonl \
     --dimensions structure --dimensions lexical --dimensions voice \
     --output config/scoring_parameters_legal.yaml
   ```

3. **Use domain-specific parameters at runtime**:
   ```bash
   writescore analyze legal_document.md \
     --params config/scoring_parameters_legal.yaml
   ```

---

## CLI Reference

### recalibrate

```bash
writescore recalibrate DATASET [OPTIONS]

Arguments:
  DATASET  Path to validation dataset (JSONL format)

Options:
  -o, --output PATH      Output path for derived parameters
  -e, --existing PATH    Path to existing parameters for comparison
  -r, --report PATH      Path to save detailed report (JSON)
  --text-report PATH     Path to save human-readable report
  -d, --dimensions TEXT  Specific dimensions to recalibrate (repeatable)
  --no-backup            Do not backup existing parameters
  --dry-run              Preview without saving
  -v, --verbose          Enable verbose logging
```

### versions

```bash
writescore versions [OPTIONS]

Options:
  --params-dir PATH   Directory containing parameter files
  --archive-dir PATH  Directory for archived versions
  --json              Output in JSON format
```

### rollback

```bash
writescore rollback [OPTIONS]

Options:
  -v, --version TEXT  Version to rollback to [required]
  --dry-run           Show what would be rolled back
  -y, --yes           Skip confirmation prompt
```

### diff

```bash
writescore diff OLD_VERSION NEW_VERSION [OPTIONS]

Arguments:
  OLD_VERSION  First version to compare
  NEW_VERSION  Second version to compare

Options:
  --detailed  Show field-level changes
  --json      Output in JSON format
```

### deploy

```bash
writescore deploy PARAMS_FILE [OPTIONS]

Arguments:
  PARAMS_FILE  Parameter file to deploy

Options:
  --no-backup  Do not backup current parameters
  --dry-run    Show deployment checklist without deploying
  -y, --yes    Skip confirmation prompt
```

---

## Appendix: Parameter Types

### Gaussian Parameters

Used for dimensions with symmetric optima (burstiness, sentiment).

```yaml
burstiness:
  scoring_type: gaussian
  target:
    source: percentile
    percentile: p50_human
    value: 10.2
  width:
    source: stdev
    value: 2.3
```

### Monotonic Parameters

Used for "more is better" or "less is better" dimensions (lexical diversity).

```yaml
lexical:
  scoring_type: monotonic
  threshold_low:
    source: percentile
    percentile: p25_human
    value: 0.55
  threshold_high:
    source: percentile
    percentile: p75_human
    value: 0.72
  direction: increasing
```

### Threshold Parameters

Used for discrete categories (structure issues).

```yaml
structure:
  scoring_type: threshold
  thresholds:
    - source: percentile
      percentile: p75_human
      value: 2
    - source: percentile
      percentile: p50_combined
      value: 5
  labels: [excellent, good, concerning, poor]
  scores: [100, 75, 40, 10]
```
