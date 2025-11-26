# Story 2.3.0: Semantic Coherence Dimension - Research Spike

**Status**: Done
**Parent Epic**: docs/stories/epic-2-enhanced-ai-detection.md
**Estimated Effort**: 1-2 days
**Dependencies**: sentence-transformers (optional dependency - to be validated)
**Priority**: Medium
**Target Version**: v5.2.0 (research phase)
**Story Type**: Research Spike

---

## Story

**As a** technical product owner evaluating new AI detection dimensions,
**I want** to validate the feasibility and effectiveness of semantic coherence analysis,
**so that** I can make an informed go/no-go decision before committing to full implementation.

---

## Acceptance Criteria

1. **Model Performance Validated**
   - Benchmark at least 3 embedding models (all-MiniLM-L6-v2, all-mpnet-base-v2, paraphrase-MiniLM-L3-v2)
   - Processing speed measured on 10k word documents
   - Memory usage measured for each model
   - Recommendation documented with justification

2. **Coherence Metrics Discrimination Validated**
   - Test 4 proposed metrics (paragraph cohesion, topic consistency, discourse flow, conceptual depth) on sample corpus
   - Minimum 20 human-written + 20 AI-generated documents tested
   - Statistical significance calculated (p-value < 0.05 required for GO)
   - Metrics ranked by discrimination power

3. **Performance Targets Confirmed**
   - Processing time verified < 0.5s per 10k words (with optimizations)
   - Memory usage verified < 200MB for recommended model
   - If targets not met, mitigation strategies identified

4. **False Positive Risk Assessed**
   - Test on domain-specific content (creative, academic, technical)
   - Identify if technical writing falsely flags as AI
   - Domain-aware threshold recommendations provided

5. **Correlation Analysis Completed**
   - Compare semantic coherence scores with existing dimensions
   - Correlation coefficient calculated for each existing dimension
   - Confirm low correlation (<0.7) with existing dimensions or justify unique value

6. **Go/No-Go Decision Documented**
   - Decision documented with supporting evidence
   - If GO: Implementation risks and mitigations identified
   - If NO-GO: Alternative approaches recommended (if any)

---

## Tasks / Subtasks

- [ ] **Environment Setup** (AC: All)
  - [ ] Install sentence-transformers library in test environment
  - [ ] Verify installation and model download process
  - [ ] Test compatibility with existing codebase

- [ ] **Prepare Test Corpus** (AC: 2, 4)
  - [ ] Gather 20+ human-written documents (mix of creative, academic, technical)
  - [ ] Gather 20+ AI-generated documents (same domain distribution)
  - [ ] Ensure documents are 1k-10k words each
  - [ ] Document corpus sources and characteristics

- [ ] **Model Benchmarking** (AC: 1, 3)
  - [ ] Create benchmark script for 3 embedding models
  - [ ] Test all-MiniLM-L6-v2 (RECOMMENDED candidate)
    - [ ] Measure processing speed on 10k word document (10 runs, average)
    - [ ] Measure memory usage during model loading and inference
    - [ ] Document model size and download requirements
  - [ ] Test all-mpnet-base-v2 (HIGH QUALITY candidate)
    - [ ] Measure processing speed on 10k word document (10 runs, average)
    - [ ] Measure memory usage during model loading and inference
    - [ ] Document model size and download requirements
  - [ ] Test paraphrase-MiniLM-L3-v2 (FAST candidate)
    - [ ] Measure processing speed on 10k word document (10 runs, average)
    - [ ] Measure memory usage during model loading and inference
    - [ ] Document model size and download requirements
  - [ ] Create comparison table with recommendation

- [ ] **Implement Prototype Metrics** (AC: 2)
  - [ ] Implement paragraph_cohesion_score() function
  - [ ] Implement topic_consistency_score() function
  - [ ] Implement discourse_flow_score() function
  - [ ] Implement conceptual_depth_score() function
  - [ ] Create utility functions (text splitting, sampling, etc.)

- [ ] **Metrics Validation Testing** (AC: 2, 4)
  - [ ] Run all 4 metrics on human-written corpus
  - [ ] Run all 4 metrics on AI-generated corpus
  - [ ] Calculate mean and standard deviation for each metric by corpus type
  - [ ] Perform t-test for statistical significance (p < 0.05)
  - [ ] Test on domain-specific subsets (creative, academic, technical)
  - [ ] Document false positive rates by domain

- [ ] **Correlation Analysis** (AC: 5)
  - [ ] Run existing analyzer on test corpus
  - [ ] Extract existing dimension scores
  - [ ] Calculate correlation coefficients between semantic coherence and each dimension
  - [ ] Create correlation matrix visualization
  - [ ] Document findings and interpret results

- [ ] **Performance Optimization Testing** (AC: 3)
  - [ ] Test sentence sampling strategy (measure speed vs accuracy trade-off)
  - [ ] Test batch processing optimization (measure speedup)
  - [ ] Test caching strategy (measure speedup on repeated analysis)
  - [ ] Verify final processing time < 0.5s per 10k words
  - [ ] Document optimization recommendations

- [ ] **Risk Assessment** (AC: 4, 6)
  - [ ] Document false positive scenarios identified
  - [ ] Propose mitigation strategies (domain-aware thresholds, weight adjustments)
  - [ ] Identify implementation risks
  - [ ] Assess dependency management concerns (optional dependency pattern)

- [ ] **Generate Research Report** (AC: 6)
  - [ ] Document all benchmark results
  - [ ] Document all validation results
  - [ ] Document statistical analysis
  - [ ] Document correlation analysis
  - [ ] Make GO/NO-GO recommendation with justification
  - [ ] If GO: Provide implementation plan with validated parameters
  - [ ] If NO-GO: Explain reasoning and suggest alternatives

---

## Dev Notes

### Research Context

This research spike validates the technical feasibility of Story 2.3 (Semantic Coherence Dimension) before full implementation. The research addresses 4 critical unknowns:

1. **Model Selection**: Which embedding model provides best speed/accuracy trade-off?
2. **Metric Effectiveness**: Do the proposed coherence metrics actually discriminate AI from human text?
3. **Performance Feasibility**: Can we meet <0.5s processing time and <200MB memory targets?
4. **Unique Value**: Does this dimension add signal beyond existing dimensions?

### Hypothesis to Test

**Hypothesis**: AI-generated text exhibits measurably lower semantic coherence than human text, detectable via sentence embeddings and computable within performance constraints.

**Research Support** (to be verified):
- Coherence Analysis (2023): Claims 23% lower paragraph cohesion in AI text
- Topic Modeling Study (2024): Claims AI exhibits more topic drift
- Discourse Structure (2023): Claims 0.68 vs 0.82 cosine similarity (AI vs human)

**NOTE**: These claims are UNVERIFIED. This research spike will validate or refute them.

### Proposed Metrics

Four coherence metrics to validate:

1. **Paragraph Cohesion**: Mean cosine similarity between sentences within paragraphs
   - Hypothesis: Higher in human text (0.78-0.85) vs AI (0.65-0.72)

2. **Topic Consistency**: Similarity between adjacent sections, weighted by smoothness
   - Hypothesis: Higher in human text (0.72-0.80) vs AI (0.58-0.68)

3. **Discourse Flow**: Proportion of paragraph transitions in "ideal range" (0.6-0.75 similarity)
   - Hypothesis: Higher in human text (0.75-0.85) vs AI (0.55-0.70)

4. **Conceptual Depth**: Mean paragraph-to-document similarity
   - Hypothesis: Higher in human text (0.68-0.78) vs AI (0.52-0.65)

### Embedding Models to Test

Three sentence-transformers models to benchmark:

| Model | Size | Expected Speed | Quality | Use Case |
|-------|------|---------------|---------|----------|
| all-MiniLM-L6-v2 | 80MB | ~0.3s/10k words | 384 dims | **Recommended** - Production |
| all-mpnet-base-v2 | 420MB | ~1.2s/10k words | 768 dims | Research/Offline |
| paraphrase-MiniLM-L3-v2 | 60MB | ~0.2s/10k words | 384 dims | Real-time |

### Performance Targets

**MUST MEET for GO decision:**
- Processing time: < 0.5s per 10k words
- Memory usage: < 200MB
- Statistical significance: p < 0.05 on validation corpus
- Correlation with existing dimensions: < 0.7

**Optimization strategies to test:**
- Sentence sampling (for docs >500 sentences)
- Batch processing (GPU efficiency)
- Embedding caching (repeated analysis)
- Quantization (FP16 for speed)

### Go/No-Go Criteria

**GO IF:**
- ✅ Statistical significance confirmed (p < 0.05)
- ✅ Processing time < 0.5s per 10k words achieved
- ✅ Memory usage < 200MB achieved
- ✅ Low correlation (<0.7) with existing dimensions OR unique value justified

**NO-GO IF:**
- ❌ No significant discrimination between human/AI corpus
- ❌ Processing time > 1s per 10k words (unoptimized)
- ❌ Memory usage > 500MB
- ❌ High correlation (>0.8) with existing dimensions AND no unique insights

### Project Structure Context

**Test Script Location:**
```
.bmad-technical-writing/data/tools/writescore/
├── research/
│   └── semantic_coherence_spike/
│       ├── benchmark_models.py          # Model benchmarking script
│       ├── validate_metrics.py          # Metrics validation script
│       ├── correlation_analysis.py      # Correlation with existing dimensions
│       └── research_report.md           # Final go/no-go report
├── tests/
│   └── research/
│       └── test_semantic_coherence_spike.py  # Research validation tests
└── corpus/
    ├── human/                            # Human-written samples
    └── ai/                               # AI-generated samples
```

**Existing Dimension Reference:**
- Review existing dimensions in `writescore/dimensions/` for patterns
- Reference DIMENSION-DEVELOPMENT-GUIDE.md for standards
- Follow self-registration pattern used by other dimensions

**Dependencies:**
- sentence-transformers: Optional dependency (to be validated)
- numpy: Already available
- scipy: For statistical tests

### Research Artifacts

**Required Outputs:**
1. Model benchmark results table
2. Metrics validation results (with statistical tests)
3. Correlation matrix with existing dimensions
4. Performance optimization report
5. Go/No-Go decision document

**Decision Document Must Include:**
- Recommended model (if GO)
- Validated threshold ranges (if GO)
- Validated weight assignment (if GO)
- Implementation risks and mitigations (if GO)
- Alternative approaches (if NO-GO)

### Testing

**Testing Approach:**
- Create isolated research environment
- Use pytest for validation tests
- Document all assumptions and findings
- Preserve research artifacts for future reference

**Test Data Requirements:**
- Minimum 40 documents (20 human, 20 AI)
- Document length: 1k-10k words each
- Domain distribution: 33% creative, 33% academic, 34% technical
- Sources must be documented and verifiable

**Validation Criteria:**
- All benchmarks must complete successfully
- All statistical tests must be documented
- Null hypothesis: No difference between human/AI coherence
- Alternative hypothesis: Significant difference (p < 0.05)

**Performance Testing:**
- Use consistent hardware for all benchmarks
- Document system specs (CPU, RAM, GPU availability)
- Run multiple iterations (min 10) for timing
- Report mean, std dev, min, max

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-20 | 1.0 | Initial research spike story created | Sarah (PO) |

---

## Dev Agent Record

### Agent Model Used
_To be populated by research agent_

### Debug Log References
_To be populated by research agent_

### Completion Notes List
_To be populated by research agent_

### File List
_To be populated by research agent_

---

## QA Results

_To be populated by QA agent after research completion_

---

## Appendix: Research Questions from Original Proposal

The following research questions from the original Story 2.3 proposal should be answered:

### 1. Semantic Embeddings
**Question**: Which embedding model provides best trade-off between accuracy and speed?
**Addressed by**: AC 1, Model Benchmarking tasks

### 2. Coherence Metrics
**Question**: Which semantic coherence metrics are most discriminative?
**Addressed by**: AC 2, Metrics Validation Testing tasks

### 3. Performance Optimization
**Question**: How to minimize processing time while maintaining accuracy?
**Addressed by**: AC 3, Performance Optimization Testing tasks

### 4. False Positive Risk
**Question**: Does technical writing naturally have lower coherence scores?
**Addressed by**: AC 4, Risk Assessment tasks

### 5. Correlation with Existing Dimensions
**Question**: Does this add unique signal or overlap with existing dimensions?
**Addressed by**: AC 5, Correlation Analysis tasks

---

## Next Steps After Research Spike

**If GO Decision:**
1. Update Story 2.3 with validated parameters
2. Reformat Story 2.3 as implementation story (using story template)
3. Add validated thresholds, model selection, and performance targets to Dev Notes
4. Create actionable implementation tasks based on research findings
5. Re-validate Story 2.3 before dev agent handoff

**If NO-GO Decision:**
1. Document decision rationale
2. Archive Story 2.3 (move to archived proposals)
3. Consider alternative approaches if identified in research
4. Update Epic 2 to remove Story 2.3 or replace with alternative
