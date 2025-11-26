# Source Availability Analysis - Story 2.6

**Date**: 2025-11-24
**Research Method**: Perplexity AI Deep Research
**Decision**: ✅ GO - Proceed with implementation

---

## Executive Summary

Research confirms sufficient source availability to expand pragmatic markers from 52 to 100-120 patterns. While LIWC2015 requires a commercial license, alternative sources provide comprehensive coverage.

---

## Source Analysis

### 1. Hyland's Taxonomy (2005)

**Availability**: ✅ Fully accessible via academic literature
**License**: Open academic use (published research)
**Source**: Hyland, K. (2005). *Metadiscourse: Exploring Interaction in Writing*. Continuum.

**Pattern Categories Available**:
- Hedges: might, may, could, possibly, perhaps, seem, appear, suggest, indicate, tend to
- Boosters: clearly, obviously, definitely, certainly, undoubtedly, demonstrate, show
- Attitude markers: surprisingly, unfortunately, hopefully, interestingly, remarkably
- Self-mention markers: I, we, my, our (in epistemic contexts)

**Estimated Yield**: 25-30 new patterns

---

### 2. LIWC2015 Dictionaries

**Availability**: ⚠️ Requires commercial/academic license
**License**: Proprietary (Pennebaker Conglomerates, Inc.)
**Cost**: Academic license required for full word lists

**Accessible Information**:
- Sample certainty words: always, never, definitely, clearly, certainly, obviously
- Sample tentative words: maybe, perhaps, guess, probably, likely, possibly

**Alternative Sources Identified**:
- CAT Scanner: Free, open-source dictionary-based tool
- Harvard General Inquirer: Free positive/negative sentiment lexicon
- NRC Emotion Lexicon: Free, covers 91 languages

**Estimated Yield**: 15-20 patterns (from documented samples + alternatives)

---

### 3. BioScope Corpus

**Availability**: ✅ Freely available for research
**License**: Free for academic/research purposes
**Access Points**:
- Official: http://www.inf.u-szeged.hu/rgai/bioscope
- Kaggle: "Bioscope Corpus - Negation Annotated"
- GitHub: https://rgai.inf.u-szeged.hu/node/105

**Corpus Statistics**:
- 20,000+ annotated sentences
- Token-level hedge cue annotations
- Scope annotations included
- Three subcorpora: clinical, abstracts, full papers

**Hedge Cues Documented**:
- Modal hedges: may, might, could, would
- Lexical hedges: suggest, indicate, appear, seem
- Approximators: about, around, roughly, approximately

**Estimated Yield**: 10-15 domain-general patterns

---

### 4. Biber et al. LGSWE (1999)

**Availability**: ✅ Academic literature documented
**License**: Open academic use (published research)
**Source**: Biber et al. (1999). *Longman Grammar of Spoken and Written English*. Chapter 10 (Stance).

**Pattern Categories**:
- Epistemic stance adverbials: probably, possibly, certainly, surely, apparently
- Likelihood modal verbs: may, might, could, must, should
- Attitudinal stance: surprisingly, regrettably, fortunately, thankfully

**Estimated Yield**: 10-15 patterns

---

### 5. Open-Source GitHub Resources

**words/hedges Package**:
- **Availability**: ✅ npm package (wooorm/words)
- **License**: Open source
- **Content**: ~162 English hedge words
- **URL**: https://github.com/words/hedges

**Sample Patterns**:
- "a bit", "about", "actually", "allege", "alleged", "almost"
- "almost never", "always", "and all that", "appear", "appear to"
- "approximately", "argue", "around", "assume", "basically"

**Estimated Yield**: 30-40 patterns (after deduplication with current 52)

---

## Coverage Summary

| Source | Status | License | New Patterns |
|--------|--------|---------|--------------|
| Hyland's Taxonomy | ✅ GO | Academic | 25-30 |
| LIWC2015 | ⚠️ Limited | Proprietary | 15-20 |
| BioScope Corpus | ✅ GO | Free research | 10-15 |
| Biber LGSWE | ✅ GO | Academic | 10-15 |
| words/hedges (GitHub) | ✅ GO | Open source | 30-40 |
| **Total (pre-dedup)** | | | **90-120** |
| **After Deduplication** | | | **50-70** |

---

## GO/NO-GO Decision

### Criteria Assessment

- ✅ **GO Criteria Met**: ≥2 major sources accessible
  - Hyland's Taxonomy: Fully documented
  - BioScope Corpus: Freely available
  - words/hedges GitHub: Open source
  - Biber LGSWE: Well documented

- ⚠️ **Adjustment**: LIWC full lists unavailable
  - Use documented sample words
  - Supplement with open-source alternatives
  - Reduce LIWC-specific target from 15-20 to 10-15

### Final Decision: ✅ PROCEED

**Revised Target**: 100-120 patterns (original target maintained)

---

## Implementation Approach

### Phase A Adjustments

1. **Task 1 (Hyland)**: Extract from academic literature - no change
2. **Task 2 (LIWC)**: Use documented samples + words/hedges supplement
3. **Task 3 (Biber)**: Extract from academic literature - no change
4. **Task 4 (BioScope)**: Download from Kaggle, extract domain-general cues

### New Pattern Categories Confirmed

Based on research, the following new categories are well-supported:

1. **ATTITUDE_MARKERS** (15-20 patterns)
   - surprisingly, unfortunately, hopefully, interestingly
   - fortunately, regrettably, curiously, oddly, strangely
   - remarkably, importantly, significantly

2. **LIKELIHOOD_ADVERBIALS** (10-15 patterns)
   - probably, possibly, conceivably, presumably, arguably
   - apparently, seemingly, ostensibly, evidently

---

## Citations

1. Hyland, K. (2005). *Metadiscourse: Exploring Interaction in Writing*. Continuum.
2. Pennebaker, J. W., et al. (2015). *LIWC2015 Manual*. University of Texas at Austin.
3. Biber, D., et al. (1999). *Longman Grammar of Spoken and Written English*. Pearson.
4. Vincze, V., et al. (2008). The BioScope Corpus. *BMC Bioinformatics*, 9(Suppl 11), S9.
5. wooorm/words. (2024). hedges - npm package. GitHub.
