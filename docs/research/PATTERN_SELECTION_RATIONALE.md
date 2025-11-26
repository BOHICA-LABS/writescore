# Pattern Selection Rationale - Story 2.6

**Date**: 2025-11-24
**Total New Patterns Selected**: 70
**Target Total**: 122 patterns (52 existing + 70 new)

---

## Selection Criteria

### Inclusion Criteria

1. **Multi-source validation**: Patterns appearing in 2+ taxonomies prioritized
2. **Domain generality**: Excluded domain-specific jargon (medical, legal)
3. **Frequency in academic writing**: Based on corpus studies
4. **Distinctiveness**: No semantic overlap with existing 52 patterns
5. **Regex implementability**: Must be detectable via word boundary patterns

### Exclusion Criteria

1. **Already implemented**: 52 patterns in current pragmatic_markers.py
2. **Domain-specific**: Medical terms (putative, pathological hedges)
3. **Ambiguous function**: Words with primary non-epistemic uses
4. **Low frequency**: Rarely used in general academic writing
5. **Complex scope**: Patterns requiring syntactic parsing (excluded for Phase 1)

---

## Pattern Distribution by Target Dictionary

### EPISTEMIC_HEDGES (Current: 20 → Target: 43)
**New patterns: 23**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| would | High | Common modal hedge in hypotheticals |
| should | Medium | Epistemic use common but deontic ambiguity |
| seem/seems | High | Core lexical verb hedge |
| appear/appears | High | Core lexical verb hedge |
| believe/believes | High | Personal epistemic stance |
| think/thinks | High | Personal epistemic stance |
| suspect/suspects | Medium | Uncertainty verb |
| suppose/supposes | Medium | Hypothesis verb |
| possible | High | Core adjective hedge |
| probable | High | Probability adjective |
| unlikely | High | Negative probability |
| uncertain | High | Explicit uncertainty |
| unclear | High | Explicit uncertainty |
| nearly | Medium | Approximator |
| essentially | Medium | Degree hedge |
| relatively | Medium | Comparison hedge |
| somewhat | High | Common degree hedge |
| fairly | Medium | Degree hedge |
| quite | Medium | Degree hedge (UK) |
| typically | High | Frequency hedge |
| usually | High | Frequency hedge |
| to some extent | Medium | Multi-word hedge |
| in general | Medium | Multi-word hedge |

### STRONG_CERTAINTY (Current: 6 → Target: 18)
**New patterns: 12**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| always | High | Absolute certainty (LIWC validated) |
| never | High | Absolute certainty (LIWC validated) |
| completely | Medium | Emphatic certainty |
| totally | Medium | Emphatic (informal register) |
| entirely | Medium | Emphatic certainty |
| surely | High | Epistemic certainty adverb |
| truly | Medium | Emphatic certainty |
| indeed | High | Confirmatory booster |
| in fact | High | Confirmatory booster |
| of course | Medium | Presuppositional |
| unquestionably | Medium | Strong certainty |
| undeniably | Medium | Strong certainty |

### SUBJECTIVE_CERTAINTY (Current: 4 → Target: 8)
**New patterns: 4**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| We know | High | First-person certainty |
| I am certain | Medium | Personal certainty |
| We are confident | Medium | Personal certainty |
| It is clear | High | Impersonal certainty |

### ASSERTION_ACTS (Current: 4 → Target: 10)
**New patterns: 6**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| demonstrate/s | High | Strong assertion |
| show/s | High | Evidence assertion |
| prove/s | Medium | Strong assertion |
| establish/es | Medium | Formal assertion |
| confirm/s | High | Verification assertion |
| find/s | High | Discovery assertion |

### ATTITUDE_MARKERS (New category)
**New patterns: 18**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| surprisingly | High | Core evaluative - unexpected |
| unfortunately | High | Core evaluative - negative |
| fortunately | High | Core evaluative - positive |
| hopefully | High | Desiderative attitude |
| interestingly | High | Notable finding marker |
| importantly | High | Significance marker |
| remarkably | Medium | Notable finding |
| significantly | High | Importance marker |
| unexpectedly | Medium | Surprise marker |
| curiously | Low | Puzzlement marker |
| strangely | Low | Oddness marker |
| oddly | Low | Oddness marker |
| regrettably | Medium | Negative evaluation |
| admittedly | Medium | Concessive marker |
| notably | Medium | Salience marker |
| predictably | Medium | Expected outcome |
| inevitably | Medium | Necessity marker |
| understandably | Medium | Comprehension marker |

### LIKELIHOOD_ADVERBIALS (New category)
**New patterns: 11**

| Pattern | Priority | Rationale |
|---------|----------|-----------|
| probably | High | Core likelihood (multi-source) |
| conceivably | Medium | Possibility adverb |
| arguably | High | Debatable likelihood |
| apparently | High | Evidential likelihood |
| evidently | Medium | Evidential likelihood |
| seemingly | High | Appearance-based |
| ostensibly | Low | Surface appearance |
| supposedly | Medium | Reported likelihood |
| reportedly | Medium | Evidential - reported |
| allegedly | Medium | Evidential - claimed |
| plausibly | Medium | Reasonableness |

---

## Excluded Patterns with Rationale

| Pattern | Source | Exclusion Reason |
|---------|--------|------------------|
| if | BioScope | Too common, not primarily epistemic |
| or | BioScope | Disjunction, not epistemic marker |
| either | BioScope | Disjunction, not epistemic marker |
| putative | BioScope | Medical/scientific domain-specific |
| can | BioScope | Primary ability sense, not epistemic |
| whether | BioScope | Interrogative, not stance marker |
| really | LIWC | Primary emphatic, not certainty |
| actually | LIWC | Primary contrast, not certainty |
| guess | LIWC | Informal register only |
| questionable | LIWC | Evaluative, not epistemic |
| doubtful | LIWC | Evaluative, not epistemic |
| tentatively | LIWC | Rare in corpora |
| wisely | Biber | Evaluative, not epistemic |
| rightly | Biber | Evaluative, not epistemic |
| happily | Biber | Emotion, not stance |
| sadly | Biber | Emotion, not stance |
| thankfully | Biber | Emotion, not stance |
| according to | Biber | Requires NP, complex pattern |

---

## Summary Statistics

| Category | Current | New | Total |
|----------|---------|-----|-------|
| EPISTEMIC_HEDGES | 20 | 23 | 43 |
| FREQUENCY_HEDGES | 6 | 0 | 6 |
| EPISTEMIC_VERBS | 8 | 0 | 8 |
| STRONG_CERTAINTY | 6 | 12 | 18 |
| SUBJECTIVE_CERTAINTY | 4 | 4 | 8 |
| ASSERTION_ACTS | 4 | 6 | 10 |
| FORMULAIC_AI_ACTS | 4 | 0 | 4 |
| ATTITUDE_MARKERS | 0 | 18 | 18 |
| LIKELIHOOD_ADVERBIALS | 0 | 11 | 11 |
| **TOTAL** | **52** | **74** | **126** |

*Note: Final count is 126, exceeding target of 100-120. Consider trimming low-priority patterns if needed.*

---

## Citations

1. Hyland, K. (2005). *Metadiscourse*. Continuum. Chapters 3-4.
2. Pennebaker et al. (2015). *LIWC2015 Manual*. University of Texas.
3. Biber et al. (1999). *LGSWE*. Pearson. Chapter 10.
4. Vincze et al. (2008). BioScope Corpus. *BMC Bioinformatics*.
