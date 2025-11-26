# GLTR Weight Review 2025

**Date**: 2025-11-12
**Context**: Following accuracy audit revealing GLTR achieves 80% F1-score (not 95%)
**Current Weight**: 20.0% (highest single dimension)
**Question**: Should we reduce GLTR weight from 20% to 12-15%?

---

## Current Weight Distribution (v5.0.0)

| Rank | Dimension | Weight | Tier | Justification |
|------|-----------|--------|------|---------------|
| 1 | **Predictability (GLTR)** | **20.0%** | ADVANCED | Token probability analysis, 80% F1-score |
| 2 | Sentiment | 17.0% | SUPPORTING | Emotional variation analysis |
| 3 | Advanced Lexical | 14.0% | ADVANCED | MTLD, MATTR, VocD metrics |
| 4 | Transition Marker | 10.0% | CORE | Formulaic AI phrases |
| 5 | Readability | 10.0% | CORE | Flesch, Coleman-Liau scores |
| 6 | Burstiness | 6.0% | CORE | Sentence/paragraph variation |
| 7 | Perplexity | 5.0% | CORE | AI vocabulary patterns |
| 8 | Voice | 5.0% | CORE | First-person, contractions |
| 9 | Formatting | 4.0% | CORE | Em-dash, bold/italic |
| 10 | Structure | 4.0% | CORE | Heading/section patterns |
| 11 | Lexical | 3.0% | SUPPORTING | Basic TTR diversity |
| 12 | Syntactic | 2.0% | ADVANCED | Dependency parsing |
| | **TOTAL** | **100.0%** | | |

### Tier Distribution
- **ADVANCED** (36.0%): Predictability (20%), Advanced Lexical (14%), Syntactic (2%)
- **CORE** (34.0%): Transition (10%), Readability (10%), Burstiness (6%), Perplexity (5%), Voice (5%), Formatting (4%), Structure (4%)
- **SUPPORTING** (20.0%): Sentiment (17%), Lexical (3%)

---

## Analysis: Should We Reduce GLTR Weight?

### Arguments FOR Reduction (20% → 12-15%)

#### 1. Accuracy-Based Adjustment
**Original justification**: "reflects GLTR's proven accuracy" (implied 95%)
**Reality**: 80% F1-score (validated 2025)

**Mathematical adjustment**:
```
Original weight: 20.0% (assumed 95% accuracy)
Adjusted weight: 20.0% × (80% / 95%) = 16.8%
Rounded: 15-17%
```

#### 2. Diminishing Returns on Modern Models
- GPT-4+ detection: 31-50% (catastrophic degradation)
- Expected on GPT-4.5+: ~50-65% (barely better than random)
- User primarily uses Claude 3.5+ for content generation

**Impact**: GLTR's value decreases as models improve.

#### 3. Single Dimension Dominance Risk
- GLTR = 20% of total score
- Next highest = Sentiment (17%)
- Gap = 3 percentage points

**Risk**: Over-reliance on single dimension reduces ensemble robustness.

#### 4. Processing Cost
- GLTR: 2-10s first analysis (model load)
- GLTR: ~0.1-0.5s subsequent analyses
- Other dimensions: <0.1s each

**Cost/benefit**: High computational cost for 80% accuracy.

---

### Arguments AGAINST Reduction (Keep 20%)

#### 1. Still Best Single Dimension
**80% F1-score** is still the highest validated accuracy of any individual dimension:
- Em-dash: "95%" (UNVALIDATED)
- Structure: "85%/78%" (citation unverified)
- Others: No validated accuracy claims

**Conclusion**: GLTR remains strongest dimension despite correction.

#### 2. Ensemble Architecture Philosophy
**Key insight**: No single dimension needs 95%+ accuracy for ensemble to work.

From DIMENSION-ENHANCEMENT-ANALYSIS-2025.md:
> "The ensemble approach is what matters. Multiple weak signals (even 60-75% individual accuracy) combine into a robust 70-85% ensemble."

**Implication**: 80% vs 95% doesn't fundamentally change GLTR's value in ensemble.

#### 3. Quality Feedback Value
**User's purpose**: "Help us use AI to write better human sounding content"

GLTR provides **actionable feedback**:
- "Token predictability at 72%, target <55%"
- "High concentration of predictable words"
- "Use more varied, unexpected vocabulary"

**Value**: Quality improvement coaching, not just detection score.

#### 4. Correlation Analysis Missing
**Unknown**: How much does GLTR correlate with other dimensions?

**Possibilities**:
- High correlation: GLTR redundant with others → reduce weight
- Low correlation: GLTR provides unique signal → keep weight

**Conclusion**: Can't make informed decision without correlation data.

#### 5. Weight Stability
Changing weights affects:
- User baselines (historical scores become incomparable)
- Dimension balance (need to redistribute 5-8%)
- Test expectations (baseline fixtures need updates)

**Cost**: High effort, moderate disruption.

---

## Weight Redistribution Scenarios

### Option A: Reduce to 15% (-5%)

**Redistribution** (+5% to distribute):
```
OLD                    NEW                    CHANGE
Predictability: 20% →  15%                   -5%
Sentiment:      17% →  17%                   --
Advanced Lexical:14% → 16%                   +2%
Transition:     10% →  11%                   +1%
Readability:    10% →  10%                   --
Burstiness:      6% →   7%                   +1%
Perplexity:      5% →   6%                   +1%
Voice:           5% →   5%                   --
Formatting:      4% →   4%                   --
Structure:       4% →   4%                   --
Lexical:         3% →   3%                   --
Syntactic:       2% →   2%                   --
TOTAL:         100% → 100%
```

**Rationale**: Boost other ADVANCED/CORE dimensions slightly.

### Option B: Reduce to 12% (-8%)

**Redistribution** (+8% to distribute):
```
OLD                    NEW                    CHANGE
Predictability: 20% →  12%                   -8%
Sentiment:      17% →  17%                   --
Advanced Lexical:14% → 16%                   +2%
Transition:     10% →  12%                   +2%
Readability:    10% →  11%                   +1%
Burstiness:      6% →   7%                   +1%
Perplexity:      5% →   7%                   +2%
Voice:           5% →   5%                   --
Formatting:      4% →   4%                   --
Structure:       4% →   4%                   --
Lexical:         3% →   3%                   --
Syntactic:       2% →   2%                   --
TOTAL:         100% → 100%
```

**Rationale**: Distribute to multiple CORE dimensions (Transition, Readability, Perplexity).

### Option C: Keep 20% (No Change)

**Redistribution**: None

**Rationale**:
- 80% F1-score still best validated accuracy
- Quality feedback value unchanged
- Ensemble approach makes absolute accuracy less critical
- Avoid disruption without correlation data

---

## Correlation Analysis (Required for Informed Decision)

### Hypothesis 1: High Correlation
If GLTR correlates highly (r > 0.7) with:
- Advanced Lexical (both measure lexical sophistication)
- Perplexity (both measure AI vocabulary)

**Implication**: GLTR provides redundant signal → reduce weight.

### Hypothesis 2: Low Correlation
If GLTR correlates weakly (r < 0.5) with most dimensions:

**Implication**: GLTR provides unique signal → keep weight.

### How to Test
```python
# Analyze 100 documents with all dimensions
results = [analyze(doc) for doc in corpus]

# Extract dimension scores
gltr_scores = [r.predictability_score for r in results]
advanced_lex_scores = [r.advanced_lexical_score for r in results]
# ... etc for all dimensions

# Calculate Pearson correlation
from scipy.stats import pearsonr
corr_gltr_advlex = pearsonr(gltr_scores, advanced_lex_scores)
# ... for all pairs
```

**Effort**: 4-8 hours (corpus analysis + correlation matrix)

---

## Recommendation

### Option C: Keep 20% Weight ✅ RECOMMENDED

**Justification**:

1. **Still best validated dimension**: 80% F1-score > all others
2. **Quality feedback unchanged**: Actionable insights for improvement
3. **Ensemble philosophy**: Absolute accuracy less critical in ensemble
4. **Insufficient data**: Correlation analysis not yet performed
5. **Avoid disruption**: Don't change weights without compelling reason

### Required Before Any Reduction

1. **Correlation analysis** (4-8 hours):
   - Analyze 100+ documents
   - Calculate dimension correlation matrix
   - Identify redundant vs. unique signals

2. **Ensemble accuracy testing** (8-12 hours):
   - Test ensemble with 20% GLTR weight
   - Test ensemble with 15% GLTR weight
   - Test ensemble with 12% GLTR weight
   - Compare accuracy on validation corpus

3. **User impact assessment** (2-4 hours):
   - How much do scores change?
   - Are changes meaningful or noise?
   - Do recommendations improve?

**Total Effort**: 14-24 hours before informed decision.

---

## Alternative: Dynamic Weighting (Future Enhancement)

### Concept
Adjust GLTR weight based on detected model:

```python
# Pseudo-code
if detected_model in ['GPT-2', 'GPT-3', 'GPT-3.5']:
    gltr_weight = 20.0  # Strong performance
elif detected_model in ['GPT-4', 'GPT-4-Turbo']:
    gltr_weight = 12.0  # Degraded performance
elif detected_model in ['GPT-4.5+', 'Claude-3.5+']:
    gltr_weight = 8.0   # Minimal value
else:
    gltr_weight = 15.0  # Unknown model
```

**Benefits**:
- Adapts to model capabilities
- Maintains accuracy on older models
- Reduces over-reliance on newer models

**Challenges**:
- Model detection is unreliable
- Adds complexity
- Not aligned with "quality improvement" purpose

**Status**: Interesting, but **NOT RECOMMENDED** for current use case.

---

## Action Items

### Immediate (Completed ✅)
- [x] Document GLTR weight review analysis
- [x] Provide recommendation: KEEP 20%

### Short-term (Optional, 2-3 days)
- [ ] **Correlation analysis**: Calculate dimension correlation matrix
- [ ] **Ensemble testing**: Test accuracy at different weight distributions
- [ ] **User impact study**: Analyze score changes on sample corpus

### Long-term (Future consideration)
- [ ] Periodic weight rebalancing (annually)
- [ ] Model-aware weighting (if model detection improves)
- [ ] User-configurable weights (advanced users)

---

## Conclusion

**Decision**: **KEEP GLTR at 20%** weight for now.

**Rationale**:
- 80% F1-score is still best validated accuracy
- Quality feedback value unchanged
- Ensemble strength more important than individual accuracy
- Insufficient correlation data to justify change

**Next Steps**:
- Correlation analysis (optional, if time permits)
- Monitor ensemble accuracy as models evolve
- Revisit weight allocation in v5.1.0 or v6.0.0

**Review Date**: 2026-01-01 (or when correlation analysis completed)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: RECOMMENDATION - NO CHANGE TO GLTR WEIGHT
