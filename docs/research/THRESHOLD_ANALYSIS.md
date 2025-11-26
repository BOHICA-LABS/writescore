# Threshold Analysis - Story 2.6

**Date**: 2025-11-24
**Analysis Type**: Theoretical adjustment based on pattern expansion
**Status**: Pending validation on corpus

---

## Summary

Scoring thresholds adjusted proportionally for expanded 126-pattern lexicon (from 52 patterns).

---

## Threshold Changes

### Hedging Thresholds

| Threshold | Pre-Story 2.6 | Post-Story 2.6 | Rationale |
|-----------|---------------|----------------|-----------|
| HEDGING_THRESHOLD_EXCELLENT | 7.0 | 9.0 | +29% for ~140% more patterns |
| HEDGING_THRESHOLD_GOOD | 9.0 | 11.0 | +22% adjustment |
| HEDGING_THRESHOLD_CONCERNING | 12.0 | 15.0 | +25% adjustment |
| HEDGING_VARIETY_TARGET | 0.6 | 0.4 | Lower target for larger set |
| HEDGING_VARIETY_OPTIMAL | 0.7 | 0.5 | Lower target for larger set |

**Research Baseline**:
- Pre-expansion: Human 4-7/1k, AI 10-15/1k
- Post-expansion estimate: Human 5-9/1k, AI 12-18/1k

### Certainty Thresholds

| Threshold | Pre-Story 2.6 | Post-Story 2.6 | Rationale |
|-----------|---------------|----------------|-----------|
| CERTAINTY_THRESHOLD_MIN | 2.0 | 3.0 | +50% for 160% more patterns |
| CERTAINTY_THRESHOLD_MAX | 5.0 | 7.0 | +40% adjustment |
| CERTAINTY_THRESHOLD_GOOD | 7.0 | 9.0 | +29% adjustment |
| CERTAINTY_THRESHOLD_CONCERNING | 10.0 | 12.0 | +20% adjustment |

**Pattern Expansion**: 10 → 26 patterns (160% increase)

### Speech Acts Thresholds

| Threshold | Pre-Story 2.6 | Post-Story 2.6 | Rationale |
|-----------|---------------|----------------|-----------|
| SPEECH_ACTS_THRESHOLD_MAX | 6.0 | 8.0 | +33% for 75% more patterns |

**Pattern Expansion**: 8 → 14 patterns (75% increase)

### Pragmatic Balance Targets

| Target | Pre-Story 2.6 | Post-Story 2.6 | Rationale |
|--------|---------------|----------------|-----------|
| PRAGMATIC_HEDGE_TARGET | 6.0 | 7.0 | Midpoint of new human range |
| PRAGMATIC_CERTAINTY_TARGET | 3.5 | 5.0 | Midpoint of new human range |
| PRAGMATIC_SPEECH_TARGET | 4.5 | 5.5 | Midpoint of new human range |

---

## Validation Requirements

### AC3 Criteria (from Story)

Thresholds should be adjusted ONLY IF:
1. Human mean shifts by >1.0 per 1k words
2. AI/Human ratio changes by >0.2

### Current Status

- **Theoretical adjustment**: Complete
- **Corpus validation**: Pending (requires 500+ document validation corpus)
- **Regression testing**: Pending

### Validation Plan

1. Run analysis on existing test fixtures
2. Compare score distributions before/after
3. Verify AI/Human separation maintained
4. Adjust thresholds if validation shows issues

---

## Pattern Count Summary

| Category | Pre-Story 2.6 | Post-Story 2.6 | Change |
|----------|---------------|----------------|--------|
| EPISTEMIC_HEDGES | 20 | 43 | +115% |
| FREQUENCY_HEDGES | 6 | 6 | 0% |
| EPISTEMIC_VERBS | 8 | 8 | 0% |
| STRONG_CERTAINTY | 6 | 18 | +200% |
| SUBJECTIVE_CERTAINTY | 4 | 8 | +100% |
| ASSERTION_ACTS | 4 | 10 | +150% |
| FORMULAIC_AI_ACTS | 4 | 4 | 0% |
| ATTITUDE_MARKERS | 0 | 18 | NEW |
| LIKELIHOOD_ADVERBIALS | 0 | 11 | NEW |
| **TOTAL** | **52** | **126** | **+142%** |

---

## Risk Assessment

### Low Risk
- Variety score adjustments (mathematical consequence of larger set)
- Proportional threshold increases

### Medium Risk
- Certainty threshold changes (larger % increase)
- New categories may shift balance calculations

### Mitigation
- Regression tests will catch major scoring shifts
- Performance validation on known AI/human documents
- Thresholds can be fine-tuned post-validation
