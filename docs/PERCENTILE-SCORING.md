# Percentile-Based Scoring in WriteScore

This document explains how WriteScore's percentile-based scoring system works and how to interpret the results.

## Overview

WriteScore uses **percentile-anchored scoring** to evaluate text. Instead of arbitrary thresholds, scores are based on how your text compares to distributions of known human and AI-generated writing.

**Key concept**: A score of 75 means your text is at the 75th percentile of the reference distribution - it performs better than 75% of samples in that category.

## How Scoring Works

### Traditional vs Percentile-Based Scoring

**Traditional (Absolute) Scoring**:
```
if burstiness < 5:
    score = "low"
elif burstiness < 15:
    score = "good"
else:
    score = "high"
```
Problem: These thresholds become outdated when AI models evolve.

**Percentile-Based Scoring**:
```
burstiness_percentile = where(your_value) in human_distribution
if burstiness_percentile < 25:
    score = "below average"
elif burstiness_percentile < 75:
    score = "typical"
else:
    score = "above average"
```
Advantage: Automatically adapts as reference distributions are updated.

### Score Interpretation

When you run analysis with `--show-percentiles`, you see output like:

```
PERCENTILE-BASED SCORE INTERPRETATION
================================================================================

Overall Quality Percentile: 72.5
  → Your text is higher quality than 72.5% of analyzed documents

Overall Detection Risk: 25.0
  → Only 25% of AI-generated texts score this low (good sign!)

PER-DIMENSION ANALYSIS
--------------------------------------------------------------------------------

BURSTINESS
  Raw Value: 12.0
  Human Percentile: 50.0 (at median)
  AI Percentile: 85.0 (higher than most AI)
  Interpretation: Sentence length variation matches typical human writing

LEXICAL
  Raw Value: 0.68
  Human Percentile: 65.0 (above average)
  Interpretation: Vocabulary diversity is stronger than average
```

### Understanding Percentile Context

For each dimension, you see:

| Field | Meaning |
|-------|---------|
| Raw Value | The actual measured metric |
| Human Percentile | Where your value falls in human writing distribution |
| AI Percentile | Where your value falls in AI writing distribution |
| Interpretation | Plain-language explanation |

**Ideal scenario**: High human percentile, high AI percentile (your text looks more human-like than typical AI output).

## Dimension Percentiles Explained

### Burstiness (Sentence Length Variation)

- **What it measures**: How much sentence lengths vary
- **Human tendency**: High variation (percentile 40-80)
- **AI tendency**: Low variation (uniform sentence lengths)
- **Recommendation**: Aim for 40th-80th percentile of human distribution

```
Low burstiness (< 25th percentile):
  "Your sentences are too uniform. Add more variation."

High burstiness (> 90th percentile):
  "Extreme variation may seem chaotic. Balance short and long sentences."

Typical burstiness (25th-75th percentile):
  "Good sentence rhythm, typical of human writing."
```

### Lexical Diversity

- **What it measures**: Vocabulary richness (type-token ratio, hapax legomena)
- **Human tendency**: Moderate to high diversity
- **AI tendency**: Often moderate, sometimes repetitive
- **Recommendation**: Aim for 50th+ percentile of human distribution

### Sentiment Variation

- **What it measures**: Emotional tone shifts throughout text
- **Human tendency**: Natural emotional arcs
- **AI tendency**: Often flat or predictable sentiment
- **Recommendation**: Some variation is good, extreme swings may seem artificial

### Voice Markers

- **What it measures**: Active vs passive voice, first-person usage
- **Human tendency**: More active voice, natural mix
- **AI tendency**: Often more passive, formal
- **Recommendation**: Match your target audience expectations

### Transition Markers

- **What it measures**: Density of transition phrases
- **Human tendency**: Natural, contextual transitions
- **AI tendency**: Often overuses formulaic transitions
- **Recommendation**: Use transitions purposefully, not mechanically

## Using Percentile Reports

### Enable Percentile Display

```bash
writescore analyze document.md --show-percentiles
```

### Interpret the Recommendations

The report includes actionable recommendations based on percentile gaps:

```
RECOMMENDATIONS
================================================================================
1. Increase sentence length variation
   Current: 25th percentile | Target: 50th percentile
   Gap: 25 percentile points

2. Reduce transition marker density
   Current: 90th percentile | Target: 50th percentile
   Gap: -40 percentile points (reduce usage)
```

### Track Progress Over Time

Use history tracking to see percentile improvements:

```bash
# Analyze and track
writescore analyze document.md --show-scores --history-notes "Initial draft"

# After edits, analyze again
writescore analyze document.md --show-scores --history-notes "Reduced AI patterns"

# View progress
writescore analyze document.md --show-history-full
```

## Percentile Reference Ranges

### Quality Benchmarks

| Percentile Range | Quality Level | Description |
|------------------|---------------|-------------|
| 90-100 | Excellent | Top tier human-like writing |
| 75-89 | Good | Clearly human-like characteristics |
| 50-74 | Average | Typical writing, some room for improvement |
| 25-49 | Below Average | Notable AI-like patterns |
| 0-24 | Needs Work | Strong AI indicators |

### Detection Risk Interpretation

| Detection Risk | Meaning |
|----------------|---------|
| < 20 | Very low risk - strongly human-like |
| 20-40 | Low risk - mostly human-like |
| 40-60 | Moderate risk - mixed signals |
| 60-80 | High risk - notable AI patterns |
| > 80 | Very high risk - strong AI indicators |

## Technical Details

### How Percentiles Are Calculated

1. **Collect reference data**: Large corpus of verified human and AI text
2. **Analyze dimensions**: Run WriteScore on all reference documents
3. **Build distributions**: For each dimension, record human and AI value distributions
4. **Derive percentiles**: p10, p25, p50, p75, p90 from each distribution
5. **Map your score**: Your value is mapped to the nearest percentile using linear interpolation

### Linear Interpolation Example

```python
# Your burstiness value: 11.0
# Human distribution percentiles:
#   p25 = 8.0, p50 = 12.0, p75 = 16.0

# 11.0 is between p25 (8.0) and p50 (12.0)
# Interpolation: 25 + (50-25) * (11.0-8.0)/(12.0-8.0)
#              = 25 + 25 * 0.75 = 43.75

# Your human percentile for burstiness: 43.75
```

### Parameter Sources

Parameters come from:

| Source | Description |
|--------|-------------|
| `percentile` | Derived from validation dataset percentile (e.g., p50_human) |
| `stdev` | Derived from standard deviation of distribution |
| `iqr` | Derived from interquartile range (robust to outliers) |
| `literature` | Based on published research (fallback) |

## Customization

### Domain-Specific Percentiles

Different domains have different writing norms. WriteScore supports domain-specific calibration:

```bash
# Use academic-specific parameters
writescore analyze paper.md --domain academic

# Use business-specific parameters
writescore analyze report.md --domain business
```

### Target Percentile Adjustment

You can customize target percentiles for recommendations:

```bash
# Aim for 75th percentile instead of default 50th
writescore analyze document.md --quality-target 75
```

## FAQ

### Q: Why do my percentiles change after recalibration?

A: Percentiles are relative to reference distributions. When new AI models are added to the reference set, what constitutes "typical AI" may shift. Your absolute text quality hasn't changed, but its relative position has.

### Q: Can I achieve 100th percentile on all dimensions?

A: Not necessarily desirable. 100th percentile means you're an extreme outlier. Aim for 50th-80th percentile on most dimensions for natural-sounding text.

### Q: Why is high AI percentile good?

A: If your text scores at the 90th percentile of the AI distribution, it means 90% of AI-generated text scores lower than yours. This indicates your text is MORE different from typical AI than most AI output - a good sign for appearing human.

### Q: How often are reference distributions updated?

A: Distributions should be updated when:
- Major new AI models are released (GPT-5, Claude 4, etc.)
- Significant drift is detected in production scores
- Annually for preventive maintenance

See [RECALIBRATION-GUIDE.md](./RECALIBRATION-GUIDE.md) for details.
