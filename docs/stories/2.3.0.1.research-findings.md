# Story 2.3.0 Research Findings Report

**Date**: 2025-11-20
**Researcher**: Sarah (Product Owner)
**Purpose**: Validate research claims and technical feasibility for Semantic Coherence Dimension

---

## Executive Summary

Comprehensive research using Perplexity (4 deep research queries, 3 reasoning queries, 4 search queries) reveals:

**✅ VALIDATED**: Core methodology is sound, semantic coherence analysis is a legitimate approach for AI detection
**⚠️ CRITICAL ISSUES**: Specific research citations and statistical thresholds in original Story 2.3 are UNVERIFIED
**✅ VALIDATED**: sentence-transformers models and performance optimization strategies are feasible
**⚠️ CONCERNS**: False positive risks in technical writing are REAL and significant

**Recommendation**: Proceed with research spike, but REPLACE hypothetical claims with empirical validation

---

## 1. Semantic Coherence Research: PARTIALLY VALIDATED

### What We Found in the Literature

**VALID CONCEPT**: AI-generated text DOES exhibit measurably different semantic coherence patterns than human text.

**REAL RESEARCH EVIDENCE**:
- Statistical Coherence Alignment (SCA) study documented coherence scores:
  - Baseline AI models: 0.72 coherence score
  - SCA-enhanced models: 0.85 coherence score
  - This shows a 0.13 improvement range, suggesting measurability

- Stylometric detection methods achieve 99.8% accuracy using:
  - Function word unigrams
  - Part-of-speech bigrams
  - Phrase patterns
  - Random forest classifiers on Japanese text

- DivEye framework (diversity-based detection) outperformed zero-shot detectors by 33.2% using higher-order statistical features

- Discourse relation analysis shows correlation with text coherence using Penn Discourse Treebank (PDTB) parsers

**CRITICAL ISSUE: UNVERIFIED CITATIONS**

The original Story 2.3 claimed:
```markdown
**Research Support**:
- Coherence Analysis (2023): AI text shows 23% lower paragraph cohesion scores
- Topic Modeling Study (2024): LLMs exhibit more topic drift in long-form generation
- Discourse Structure (2023): AI paragraphs show 0.68 avg cosine similarity vs 0.82 human
```

**FINDING**: These specific studies **DO NOT EXIST** in published research literature.
- No paper titled "Coherence Analysis (2023)" found
- No "Topic Modeling Study (2024)" with these specific claims found
- No "Discourse Structure (2023)" with 0.68 vs 0.82 statistics found

**IMPACT**: The specific threshold claims (0.68 vs 0.82, 23% lower cohesion) are UNSUPPORTED and must be treated as **hypotheses to be validated**, not established facts.

### What This Means

**The approach is valid**, but we CANNOT claim:
- Specific threshold ranges for human vs AI text
- Specific percentage differences (23% lower cohesion)
- Specific cosine similarity ranges (0.68 vs 0.82)

**We CAN claim**:
- Semantic coherence differs between human and AI text (supported by SCA study)
- Discourse structure analysis is effective (supported by PDTB research)
- Detection is feasible (supported by 99.8% accuracy in stylometric studies)

---

## 2. Sentence-Transformers Models: VALIDATED

### Model Specifications (CONFIRMED)

| Model | Size | Embedding Dims | Status |
|-------|------|----------------|--------|
| **all-MiniLM-L6-v2** | ~90 MB | 384 | ✅ VALIDATED |
| **all-mpnet-base-v2** | ~420 MB | 768 | ✅ VALIDATED |
| **paraphrase-MiniLM-L3-v2** | ~60 MB | 384 | ✅ VALIDATED |

### Processing Speed: PARTIAL DATA

**CLAIMED in Story 2.3**:
- all-MiniLM-L6-v2: ~0.3s per 10k words
- all-mpnet-base-v2: ~1.2s per 10k words
- paraphrase-MiniLM-L3-v2: ~0.2s per 10k words

**ACTUAL RESEARCH FINDINGS**:
- Speed benchmarks are reported as "queries per second" not "per 10k words"
- multi-qa-MiniLM-L6-cos-v1: 18,000 queries/sec (GPU), 750 queries/sec (CPU)
- Processing time DEPENDS on: batch size, hardware, sequence length
- For ~10k word documents split into chunks:
  - GPU processing: several milliseconds per batch (32-128 sentences)
  - CPU processing: 2-4× slower than GPU

**FINDING**: The specific "per 10k words" claims **REQUIRE EMPIRICAL BENCHMARKING**. Cannot be verified from published research.

### Memory Usage: ESTIMATED

**CLAIMED in Story 2.3**: <200MB memory usage

**ACTUAL RESEARCH FINDINGS**:
- GPU VRAM requirements:
  - all-MiniLM-L6-v2: ~1-2 GB VRAM (batch size 16, max length 128)
  - all-mpnet-base-v2: ~2-4 GB VRAM
  - paraphrase-MiniLM-L3-v2: ~1 GB VRAM

- CPU RAM requirements:
  - all-MiniLM-L6-v2: 2-4 GB RAM for loading + encoding
  - all-mpnet-base-v2: 4-8 GB RAM

**FINDING**: The <200MB claim is **LIKELY UNREALISTIC** for full model operation. This needs empirical validation.

### Installation and Dependencies: VALIDATED ✅

**Requirements**:
- Python 3.10+ (recommended for 2025)
- PyTorch 1.11.0+ (2.2.0+ recommended)
- Transformers v4.41.0+

**Optional Dependencies**:
```bash
pip install -U sentence-transformers  # Basic
pip install -U "sentence-transformers[onnx-gpu]"  # GPU acceleration
pip install -U "sentence-transformers[onnx]"  # CPU optimization
```

**Model Download Sizes** (to ~/.cache/torch/sentence_transformers):
- all-MiniLM-L6-v2: ~90 MB ✅
- all-mpnet-base-v2: ~420 MB ✅
- paraphrase-MiniLM-L3-v2: ~60 MB ✅

**FINDING**: Installation process is straightforward and well-documented.

---

## 3. Semantic Coherence Metrics: METHODOLOGY VALIDATED

### Proposed Metrics Assessment

#### A. Paragraph Cohesion Score
**METHOD**: Calculate pairwise cosine similarity between sentences within paragraphs

**VALIDATION STATUS**: ✅ METHODOLOGY VALID
- Cosine similarity for semantic measurement is standard practice
- Formula: sim(S₁, S₂) = (2|words(S₁) ∩ words(S₂)|) / total words
- LSA (Latent Semantic Analysis) widely used for coherence measurement
- Combined model (Egrid + Overlap + LSA + HStO + Lesk) achieved r=0.522 correlation with human judgments

**THRESHOLD CLAIMS**: ⚠️ UNVERIFIED
- Story claimed: Human 0.78-0.85, AI 0.65-0.72
- Research found: 0.72 (baseline AI) to 0.85 (enhanced) from SCA study
- **CONCLUSION**: Ranges overlap with research but are NOT specific to paragraph cohesion

#### B. Topic Consistency Score
**METHOD**: Measure similarity between adjacent sections, penalize drift

**VALIDATION STATUS**: ✅ METHODOLOGY VALID
- Topic modeling research supports this approach
- Discourse relation sequences show correlation with coherence (r > 0.5)
- BiLSTM classifiers on discourse relations outperformed raw text

**THRESHOLD CLAIMS**: ⚠️ UNVERIFIED
- Story claimed: Human 0.72-0.80, AI 0.58-0.68
- No research found supporting these specific ranges

#### C. Discourse Flow Score
**METHOD**: Measure if paragraph transitions fall in "ideal range" (0.6-0.75 similarity)

**VALIDATION STATUS**: ✅ CONCEPT VALID, ⚠️ RANGES UNVERIFIED
- Discourse structure analysis is well-established
- Context overlap ratio and syntactic alignment are validated metrics
- BUT: The specific "ideal range" of 0.6-0.75 is NOT documented in research

**THRESHOLD CLAIMS**: ⚠️ UNVERIFIED
- Story claimed: Human 0.75-0.85, AI 0.55-0.70
- No research found supporting these specific ranges

#### D. Conceptual Depth Score
**METHOD**: Compare paragraphs to overall document embedding

**VALIDATION STATUS**: ✅ METHODOLOGY VALID
- Semantic similarity to document centroid is standard practice
- Transformer embeddings (768-1024 dimensions) capture semantic meaning
- Cosine distance effectively measures semantic relationships

**THRESHOLD CLAIMS**: ⚠️ UNVERIFIED
- Story claimed: Human 0.68-0.78, AI 0.52-0.65
- No research found supporting these specific ranges

### Summary: Metrics Assessment

**✅ ALL FOUR METRICS USE VALID METHODOLOGIES**
**⚠️ ALL THRESHOLD RANGES ARE UNVERIFIED HYPOTHESES**

**RECOMMENDATION**: Implement metrics, but conduct empirical research to establish actual threshold ranges.

---

## 4. False Positive Risk: VALIDATED CONCERN ⚠️

### Technical Writing Challenges

**FINDING**: Technical writing shows **SIGNIFICANTLY HIGHER false positive rates** in AI detection.

**RESEARCH EVIDENCE**:
- Technical writing exhibits:
  - Logical, sequential, systematic organization
  - Clear, objective language
  - Specialized vocabulary
  - Direct information delivery
  - Standardized syntax and templates
  - Limited sentence structure variation
  - Repetitive phrasing (installation steps, feature lists)

- These patterns **closely resemble AI-generated text**, leading to higher false positives

**DOMAIN-SPECIFIC PATTERNS**:

| Domain | False Positive Risk | Coherence Characteristics |
|--------|-------------------|--------------------------|
| **Creative Writing** | LOW | Imaginative, figurative, highly individualized |
| **Academic Writing** | MEDIUM | Formal but varied (argumentation, citations) |
| **Technical Writing** | **HIGH** | Formulaic, repetitive, objective |

**VALIDATION**: Research explicitly confirms that "structured technical documents (e.g., manuals, API docs, scientific reports) often contain highly formulaic, repetitive phrasing, boilerplate templates, and strict adherence to documentation standards."

### Domain-Aware Threshold Recommendations

**Story 2.3 Proposed**:
```python
COHERENCE_THRESHOLDS = {
    'creative': {'paragraph_cohesion': 0.75},
    'academic': {'paragraph_cohesion': 0.72},
    'technical': {'paragraph_cohesion': 0.65},
}
```

**FINDING**: The CONCEPT of domain-specific thresholds is ✅ VALID and NECESSARY.

**HOWEVER**: Specific threshold values are ⚠️ UNVERIFIED and need empirical validation.

### Weight Adjustment Strategy

**Story 2.3 Proposed**:
```python
weights = {
    'creative': 0.07,  # High signal
    'academic': 0.05,  # Moderate signal
    'technical': 0.03,  # Low signal, supplementary
}
```

**FINDING**: Weight reduction for technical domains is ✅ SOUND APPROACH to mitigate false positives.

**RECOMMENDATION**: Validate through empirical testing on domain-specific corpora.

---

## 5. Performance Optimization: VALIDATED ✅

### Optimization Strategies

#### Strategy 1: Sentence Sampling
**CLAIMED**: 70% speed improvement, <5% accuracy loss

**VALIDATION**: ✅ CONFIRMED as valid approach
- For documents >500 sentences, sample evenly distributed subset
- Research confirms sentence sampling reduces computation while maintaining accuracy
- Windowed chunking is standard practice

#### Strategy 2: Batch Processing
**CLAIMED**: 3-5× faster than sequential

**VALIDATION**: ✅ CONFIRMED
- Research documents: "5-10× throughput increase over naïve, single-sentence inference"
- Batch sizes of 32-128 for GPUs recommended
- Sorting sentences by length minimizes padding overhead

#### Strategy 3: Caching Embeddings
**CLAIMED**: Avoid recomputation on repeated analysis

**VALIDATION**: ✅ CONFIRMED as standard practice
- In-memory or persistent caches recommended
- Hash-based keys for sentence/document chunks
- Significant speedup for iterative manuscript editing

#### Strategy 4: FP16 Quantization
**CLAIMED**: 40% speed improvement, ~2% accuracy loss

**VALIDATION**: ✅ CONFIRMED
- Research documents: "up to 50% speed improvement with minimal accuracy loss"
- FP16 (half-precision) via `model.half()` or `torch_dtype="float16"`
- Int8 quantization can yield 3× speedup for short texts

### Performance Target Assessment

**CLAIMED TARGET**: <0.5s per 10k words (with optimizations)

**VALIDATION**: ⚠️ REQUIRES EMPIRICAL TESTING
- Research confirms optimizations work
- Specific timing depends on: hardware, batch size, document characteristics
- Must benchmark on target hardware with actual 10k word documents

**RECOMMENDATION**: Include performance benchmarking as core research spike task.

---

## 6. Test Corpus Requirements: VALIDATED ✅

### Minimum Corpus Size

**FINDING**: Research provides clear evidence-based guidelines.

**MINIMUM VIABLE**: 500 samples per class
- Datasets <300 samples systematically overestimate performance (overfitting)
- 500 samples per class = practical minimum for stable metrics
- Below this, high variance and unreliable cross-validation

**RECOMMENDED**: 750-1,500 samples per class
- Achieves performance convergence
- Diminishing returns beyond this range
- For binary classification: 1,000-3,000 total documents

**FOR STORY 2.3.0**: "Minimum 20 human + 20 AI documents" is **INSUFFICIENT**
- 40 documents total is far below minimum viable size
- **RECOMMENDATION**: Increase to minimum 50 human + 50 AI (100 total)
- **BETTER**: 100 human + 100 AI (200 total) for reliable validation

### Domain Distribution

**FINDING**: Research strongly recommends domain diversity.

**BEST PRACTICE**: 100-200 samples per domain for reliable estimation

**MAJOR BENCHMARKS**:
- MAGE: 447,674 documents across 10 domains, 27 LLMs
- RAID: 6+ million instances across 11 models, 8 domains, 11 adversarial attacks
- PrismAI: 537,588 documents across 7 domains, 2 languages
- HC3: 40,000 question-answer pairs

**FOR STORY 2.3.0**: AC2 requires "20 human + 20 AI documents"

**RECOMMENDATION**: Specify domain distribution:
- Creative writing: 20 documents (10 human, 10 AI)
- Academic writing: 20 documents (10 human, 10 AI)
- Technical writing: 20 documents (10 human, 10 AI)
- **TOTAL**: 60 documents minimum (30 human, 30 AI)

### Document Length Requirements

**FINDING**: Document length significantly affects detection performance.

**RESEARCH EVIDENCE**:
- Detection accuracy improves monotonically with document length
- Shorter documents (<100 words) present detection challenges
- Zero-shot methods become ineffective below 50-100 tokens

**RECOMMENDED DISTRIBUTION**:
- Short texts: 50-200 words (social media, reviews)
- Medium texts: 200-1,000 words (articles, essays)
- Long texts: 1,000-10,000 words (papers, reports)

**FOR STORY 2.3.0**: AC2 requires "documents are 1k-10k words each"

**RECOMMENDATION**: ✅ This is appropriate for validating the dimension, but consider adding shorter documents (200-1k words) to test robustness.

### Statistical Significance

**FINDING**: Proper statistical testing is essential.

**REQUIREMENTS FOR p < 0.05**:
- Adequate sample size (500+ per class minimum)
- Appropriate statistical tests (t-test for continuous metrics)
- Multiple evaluation metrics (precision, recall, F1, ROC-AUC)
- Cross-validation to reduce variance

**FOR STORY 2.3.0**: AC2 requires "Statistical significance calculated (p-value < 0.05 required for GO)"

**RECOMMENDATION**: ✅ Correct requirement, but ensure adequate sample size (increase from 20+20 to 100+100 minimum).

---

## 7. Critical Findings Summary

### What Is VALIDATED ✅

1. **Methodology**: Semantic coherence analysis is a legitimate AI detection approach
2. **Metrics**: All four proposed metrics use valid methodologies
3. **Models**: sentence-transformers models are appropriate and available
4. **Optimization**: Performance optimization strategies are confirmed effective
5. **False Positives**: Technical writing false positive risk is real and documented
6. **Corpus Guidelines**: Research provides clear corpus construction best practices

### What Is UNVERIFIED ⚠️

1. **Research Citations**: The three specific studies cited DO NOT EXIST
2. **Threshold Ranges**: All claimed threshold values (0.68 vs 0.82, etc.) are unsupported
3. **Performance Claims**: Specific processing speeds (<0.5s per 10k words) need validation
4. **Memory Claims**: <200MB memory target is likely unrealistic
5. **Statistical Claims**: "23% lower paragraph cohesion" is unsubstantiated

### What REQUIRES CHANGE 🔧

1. **Remove fake citations** and replace with actual research references
2. **Relabel thresholds as "hypotheses to be validated"** not established facts
3. **Increase corpus size** from 20+20 to minimum 100+100 documents
4. **Add empirical benchmarking tasks** for processing speed and memory
5. **Add domain-specific corpus** requirements (creative, academic, technical)

---

## 8. Revised Go/No-Go Criteria

### Original Criteria (Story 2.3.0)

**GO IF**:
- ✅ Statistical significance confirmed (p < 0.05)
- ✅ Processing time < 0.5s per 10k words achieved
- ✅ Memory usage < 200MB achieved
- ✅ Low correlation (<0.7) with existing dimensions

**NO-GO IF**:
- ❌ No significant discrimination on validation corpus
- ❌ Processing time > 1s per 10k words
- ❌ Memory usage > 500MB
- ❌ High correlation (>0.8) with existing dimensions

### REVISED CRITERIA (Based on Research)

**GO IF**:
- ✅ Statistical significance confirmed (p < 0.05) on corpus of 100+ documents per class
- ✅ At least ONE metric shows significant discrimination (not necessarily all four)
- ✅ Processing time < 2s per 10k words achieved (realistic target)
- ✅ Memory usage < 5GB achieved (realistic for model + inference)
- ✅ Correlation with existing dimensions < 0.7 OR unique value demonstrated

**NO-GO IF**:
- ❌ NO metrics show significant discrimination (p > 0.05) on adequate corpus
- ❌ Processing time > 5s per 10k words (too slow for production)
- ❌ Memory usage > 10GB (impractical for deployment)
- ❌ High correlation (>0.8) with existing dimensions AND no unique insights
- ❌ Technical writing false positive rate > 50% (unacceptable for deployment)

**RATIONALE FOR CHANGES**:
- More realistic performance targets based on actual research
- Flexibility to proceed if SOME metrics work (not requiring all four)
- Explicit consideration of false positive rates
- Memory targets aligned with actual model requirements

---

## 9. Recommendations for Story 2.3.0 Revisions

### IMMEDIATE ACTIONS REQUIRED

1. **Remove Unverified Citations**
   ```markdown
   # REMOVE:
   **Research Support**:
   - Coherence Analysis (2023): AI text shows 23% lower paragraph cohesion scores
   - Topic Modeling Study (2024): LLMs exhibit more topic drift
   - Discourse Structure (2023): AI paragraphs show 0.68 avg cosine similarity vs 0.82 human

   # REPLACE WITH:
   **Research Hypothesis** (to be validated):
   AI-generated text is hypothesized to exhibit measurably different semantic coherence
   than human text. This research spike will validate whether:
   - Paragraph cohesion differs significantly between human and AI text
   - Topic consistency shows detectable patterns
   - Discourse flow exhibits discriminative characteristics

   **Supporting Literature**:
   - Statistical Coherence Alignment study: AI coherence scores 0.72 vs 0.85 (enhanced)
   - Stylometric detection achieves 99.8% accuracy using linguistic features
   - Discourse relation analysis shows correlation with text coherence
   ```

2. **Relabel All Thresholds as Hypotheses**
   ```markdown
   # In each metric description, change:
   Human average: 0.78-0.85  # REMOVE - unverified
   AI average: 0.65-0.72     # REMOVE - unverified

   # TO:
   Expected pattern: Higher scores for human text (to be validated)
   Threshold to be determined empirically during research spike
   ```

3. **Update Corpus Size Requirements**
   ```markdown
   # AC2: Change from:
   - Minimum 20 human-written + 20 AI-generated documents tested

   # TO:
   - Minimum 100 human-written + 100 AI-generated documents tested
   - Distributed across 3 domains: creative (33%), academic (33%), technical (34%)
   - Document length: 1k-10k words per document
   - Total corpus: 200 documents minimum
   ```

4. **Add Domain Distribution Task**
   ```markdown
   - [ ] **Prepare Domain-Stratified Test Corpus** (AC: 2, 4)
     - [ ] Gather 33+ human-written creative documents (novels, stories, creative essays)
     - [ ] Gather 33+ human-written academic documents (research papers, scholarly articles)
     - [ ] Gather 34+ human-written technical documents (manuals, API docs, technical reports)
     - [ ] Generate 33+ AI creative documents (same prompts/topics as human creative)
     - [ ] Generate 33+ AI academic documents (same prompts/topics as human academic)
     - [ ] Generate 34+ AI technical documents (same prompts/topics as human technical)
     - [ ] Ensure documents are 1k-10k words each
     - [ ] Document corpus sources, characteristics, and generation parameters
   ```

5. **Update Performance Targets**
   ```markdown
   # Change:
   **Target Performance**: <0.5s per 10k words (with optimizations)

   # TO:
   **Target Performance**:
   - Primary target: <2s per 10k words (with optimizations)
   - Stretch goal: <1s per 10k words (if achievable)
   - Memory usage: <5GB (model + inference overhead)
   ```

6. **Add Actual Research References**
   ```markdown
   ## References

   1. Statistical Coherence Alignment (SCA) for LLMs - arXiv 2502.09815v1
   2. Stylometric Detection Methods (99.8% accuracy) - PMC 12558491
   3. DivEye Framework (diversity-based detection) - arXiv 2509.18880v1
   4. Discourse Relation Analysis for Coherence - ACL 2025.acl-long.236
   5. MAGE Benchmark (447k documents, 10 domains) - arXiv 2305.13242v3
   6. RAID Benchmark (6M instances, adversarial robustness) - arXiv 2405.07940
   7. Sentence-Transformers Documentation - sbert.net
   8. Building AI Detection Test Corpora - Nature s42256-024-00878-8
   ```

7. **Add Research Validation Tasks**
   ```markdown
   - [ ] **Validate Coherence Thresholds** (AC: 2)
     - [ ] Calculate actual threshold ranges for each metric
     - [ ] Test if human vs AI differences are statistically significant
     - [ ] Document observed ranges (not assumed ranges)
     - [ ] Compare results to hypothesized ranges

   - [ ] **Measure Actual Performance** (AC: 3)
     - [ ] Benchmark processing time on actual 10k word documents
     - [ ] Measure memory usage during model loading and inference
     - [ ] Test on target hardware (document CPU/GPU specs)
     - [ ] Document actual vs target performance
   ```

---

## 10. Final Recommendation

**PROCEED WITH RESEARCH SPIKE** with the following critical changes:

### Must-Fix Issues (BLOCKING)

1. ✅ **Remove fake research citations** - replace with actual research or label as hypotheses
2. ✅ **Increase corpus size** - from 40 to 200 minimum documents
3. ✅ **Add domain stratification** - explicit creative/academic/technical splits
4. ✅ **Realistic performance targets** - based on actual research findings
5. ✅ **Empirical threshold validation** - don't assume threshold ranges

### Should-Fix Issues (Important)

6. ✅ **Add actual research references** - cite real papers found in this research
7. ✅ **Update go/no-go criteria** - more realistic thresholds
8. ✅ **Document false positive mitigation** - especially for technical writing
9. ✅ **Add correlation analysis** - with existing dimensions (weight, sentiment, etc.)

### Nice-to-Have Improvements

10. ✅ **Consider shorter documents** - add 200-1k word range for robustness
11. ✅ **Multilingual consideration** - note limitations of English-only validation
12. ✅ **Adversarial robustness** - consider paraphrasing attacks in future work

---

## Appendix A: Actual Research Citations

### Semantic Coherence and AI Detection

1. **Statistical Coherence Alignment (SCA)**
   - Source: arXiv:2502.09815v1
   - Finding: Coherence scores improved from 0.72 (baseline) to 0.85 (SCA-enhanced)
   - Relevance: Demonstrates measurability of coherence in AI text

2. **Stylometric Detection Methods**
   - Source: PMC 12558491, PLOS ONE
   - Finding: 99.8% accuracy using function word unigrams, POS bigrams, phrase patterns
   - Relevance: Validates that linguistic features can discriminate AI from human text

3. **DivEye Framework (Diversity Metrics)**
   - Source: arXiv:2509.18880v1
   - Finding: 33.2% improvement over zero-shot detectors using diversity metrics
   - Relevance: Shows statistical diversity is a powerful detection signal

4. **Discourse Relation Analysis**
   - Source: ACL Anthology 2025.acl-long.236
   - Finding: Discourse relation sequences correlate with text coherence
   - Relevance: Validates discourse-based coherence measurement

### Sentence-Transformers Performance

5. **Sentence-Transformers Documentation**
   - Source: sbert.net/docs
   - Models: all-MiniLM-L6-v2 (90MB), all-mpnet-base-v2 (420MB), paraphrase-MiniLM-L3-v2 (60MB)
   - Performance: 18,000 queries/sec GPU, 750 queries/sec CPU (for MiniLM variants)

6. **Optimization Strategies**
   - Source: sbert.net/docs/sentence_transformer/usage/efficiency.html
   - Finding: Batch processing yields 5-10× throughput vs sequential
   - Finding: FP16 quantization achieves ~50% speedup with minimal accuracy loss

### Corpus Construction Best Practices

7. **MAGE Benchmark**
   - Source: arXiv:2305.13242v3
   - Scale: 447,674 documents, 10 domains, 27 LLMs
   - Finding: In-domain detection 90%+, out-of-domain drops to 68%

8. **RAID Benchmark**
   - Source: arXiv:2405.07940
   - Scale: 6+ million instances, 11 models, 8 domains, 11 adversarial attacks
   - Finding: Adversarial attacks reduce detection by 60%+

9. **Minimum Sample Sizes for ML**
   - Source: PMC 11655521
   - Finding: <300 samples = systematic overfitting
   - Recommendation: 500+ samples per class minimum, 750-1,500 optimal

10. **Cross-Dataset Evaluation Challenges**
    - Source: Nature s42256-024-00878-8
    - Finding: Models trained on one domain often fail on others
    - Recommendation: Multi-domain corpora with 100-200 samples per domain

### False Positive Risks

11. **Technical Writing AI Detection Challenges**
    - Source: GeeksforGeeks, ClickHelp, CCU blogs
    - Finding: Technical writing's formulaic patterns resemble AI output
    - Impact: Higher false positive rates in technical documentation
    - Recommendation: Domain-specific thresholds required

---

## Appendix B: Comparison Table - Claimed vs Validated

| Claim in Story 2.3 | Validation Status | Actual Finding |
|-------------------|------------------|----------------|
| Coherence Analysis (2023) study | ❌ DOES NOT EXIST | No such paper found |
| Topic Modeling Study (2024) | ❌ DOES NOT EXIST | No such paper found |
| Discourse Structure (2023) | ❌ DOES NOT EXIST | No such paper found |
| 23% lower paragraph cohesion | ❌ UNVERIFIED | No supporting data |
| 0.68 vs 0.82 cosine similarity | ❌ UNVERIFIED | No supporting data |
| Human cohesion: 0.78-0.85 | ❌ UNVERIFIED | Needs empirical validation |
| AI cohesion: 0.65-0.72 | ❌ UNVERIFIED | Needs empirical validation |
| all-MiniLM-L6-v2: 80MB | ✅ VALIDATED | Confirmed ~90MB |
| all-mpnet-base-v2: 420MB | ✅ VALIDATED | Confirmed ~420MB |
| paraphrase-MiniLM-L3-v2: 60MB | ✅ VALIDATED | Confirmed ~60MB |
| <0.5s per 10k words | ⚠️ NEEDS TESTING | No direct benchmark data |
| <200MB memory usage | ❌ UNREALISTIC | Actual: 2-8GB RAM needed |
| 3-5× batch speedup | ✅ VALIDATED | Research shows 5-10× speedup |
| 40% FP16 speedup | ✅ VALIDATED | Research shows ~50% speedup |
| Technical writing false positives | ✅ VALIDATED | Explicitly confirmed in research |
| Domain-specific thresholds | ✅ VALIDATED CONCEPT | Concept valid, values unverified |
| Minimum 20+20 documents | ❌ INSUFFICIENT | Research requires 500+ per class |

---

## Appendix C: Updated Research Spike Roadmap

### Phase 1: Corpus Construction (2-3 days)
- Gather 100 human documents across 3 domains
- Generate 100 AI documents (matched to human topics/domains)
- Validate corpus quality and document sources
- **Deliverable**: 200-document corpus with metadata

### Phase 2: Model Benchmarking (1 day)
- Install and test all 3 sentence-transformers models
- Benchmark processing speed on actual 10k word documents
- Measure memory usage on target hardware
- **Deliverable**: Performance comparison table

### Phase 3: Metrics Implementation (2 days)
- Implement all 4 coherence metrics
- Run on full corpus (human vs AI)
- Calculate actual threshold ranges
- Perform statistical significance testing
- **Deliverable**: Metrics validation report with empirical thresholds

### Phase 4: Analysis and Decision (1 day)
- Correlation analysis with existing dimensions
- False positive analysis by domain
- Domain-specific threshold recommendations
- Final go/no-go recommendation
- **Deliverable**: Research report with decision

**TOTAL ESTIMATED EFFORT**: 6-7 days (revised from 1-2 days)

**RATIONALE**: Original 1-2 day estimate was based on 40-document corpus. Increasing to 200 documents and adding proper benchmarking requires additional time.

---

**Report Compiled by**: Sarah (Product Owner)
**Based on**: 11 Perplexity research queries across deep research, reasoning, and search modes
**Total Research Sources**: 60+ academic papers, benchmarks, and technical documentation
**Date**: 2025-11-20
