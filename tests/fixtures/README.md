# Test Fixtures

This directory contains test fixtures for the AI Pattern Analyzer test suite.

## Regression Testing Fixtures

### regression_corpus.json

**Purpose**: Test corpus for scoring regression validation.

**Structure**:
- 25 diverse text samples categorized as:
  - 10 AI-generated samples (high AI probability markers)
  - 10 human-written samples (natural voice, varied structure)
  - 3 mixed samples (combination of AI and human styles)
  - 2 edge case samples (unicode, long sentences, etc.)

**Sample Format**:
```json
{
  "id": "unique_sample_id",
  "text": "Sample text content...",
  "category": "ai_generated|human_written|mixed|edge_case",
  "expected_ai_probability": "high|medium|low",
  "notes": "Description of AI/human markers"
}
```

**Usage**:
- Loaded by regression tests to validate dimension scoring consistency
- Can be extended with additional samples as needed

**Adding New Samples**:
1. Add sample to `regression_corpus.json` following the structure above
2. Re-run baseline capture: `python tests/utils/capture_baselines.py`
3. Verify regression tests still pass: `pytest tests/integration/test_scoring_regression.py -v`

### baseline_scores.json

**Purpose**: Known-good baseline scores for regression testing.

**Structure**:
- Baseline scores for all 25 corpus samples across all 12 dimensions
- Metadata: version, capture timestamp, model versions

**Sample Format**:
```json
{
  "version": "1.0",
  "captured": "2025-11-06T21:35:00Z",
  "model_versions": {
    "writescore": "4.0.0",
    "python": "3.11.7"
  },
  "baselines": {
    "sample_id": {
      "predictability": 75.0,
      "advanced_lexical": 50.0,
      "readability": 25.0,
      ...
    }
  }
}
```

**Usage**:
- Loaded by regression tests to compare current scores against baselines
- Tests assert ≤5% variance between baseline and current scores

**When to Update Baselines**:

Baselines should be updated when:
1. **Intentional dimension logic changes**: You've deliberately modified scoring algorithms
2. **Dependency updates**: Major version updates to NLP libraries (spacy, transformers, etc.)
3. **New features**: Added new metrics that affect scoring

Baselines should NOT be updated when:
1. **Refactoring**: Code restructuring without logic changes (tests should pass with 0% variance)
2. **Bug fixes**: Fixing incorrect behavior (consider if baselines were capturing bugs)
3. **Tests failing**: Investigate root cause before updating baselines

**How to Update Baselines**:

1. **Verify the change is intentional**:
   ```bash
   # Run regression tests to see which dimensions have variance
   pytest tests/integration/test_scoring_regression.py -v
   ```

2. **Review the variance report**:
   - Check which dimensions exceed 5% variance
   - Verify the variance is expected based on your changes
   - If unexpected, investigate before updating

3. **Capture new baselines**:
   ```bash
   # Re-capture baseline scores with current dimension logic
   python tests/utils/capture_baselines.py
   ```

4. **Verify new baselines**:
   ```bash
   # Regression tests should now pass with 0% variance
   pytest tests/integration/test_scoring_regression.py -v
   ```

5. **Document the change**:
   - Update `baseline_scores.json` metadata if needed
   - Document reason for baseline update in git commit

**Example Workflow**:

```bash
# Scenario: You've updated the PredictabilityDimension scoring logic

# 1. Check current variance
pytest tests/integration/test_scoring_regression.py::TestScoringRegression::test_predictability_scoring_regression -v

# Output might show:
# AssertionError: Sample ai_sample_01: Predictability variance 8.5% exceeds 5%

# 2. Verify this is expected (you changed the logic)

# 3. Re-capture baselines
python tests/utils/capture_baselines.py

# 4. Verify tests pass
pytest tests/integration/test_scoring_regression.py -v

# 5. Commit with clear message
git add tests/fixtures/baseline_scores.json
git commit -m "chore: update baselines after PredictabilityDimension scoring improvements"
```

## Other Fixtures

### sample_ai_text.md

Sample AI-generated text with typical AI writing patterns (furthermore, moreover, comprehensive, etc.)

### sample_human_text.md

Sample human-written text with natural voice, contractions, varied sentence structure.

### sample_mixed_text.md

Sample text mixing AI-style formal sections with human-style informal sections.

### sample_edge_cases.md

Edge cases for testing: unicode, long sentences, code blocks, malformed markdown, etc.

### section-1.1-final.md, section-1.2.md

Real manuscript sections used for integration testing with actual book content.

---

## Maintenance

### Regular Maintenance

- Review corpus relevance quarterly
- Update baselines when dependencies are upgraded
- Add new samples as new AI patterns emerge

### Quality Checks

- Ensure corpus represents diverse writing styles
- Verify baselines reflect current dimension logic
- Monitor regression test performance (should complete in <60s)

### Troubleshooting

**Regression tests failing after refactoring**:
- Should NOT happen if refactoring is correct
- Investigate scoring drift before updating baselines
- Refactoring should have 0% variance

**Regression tests failing after dependency updates**:
- Expected for major version updates
- Review variance report to understand changes
- Update baselines if changes are acceptable

**High variance on specific dimensions**:
- Check dimension implementation for bugs
- Verify corpus samples are appropriate
- Consider if 5% threshold needs adjustment

---

*Last Updated: 2025-11-06*
*Story: 1.4.13 - Add Scoring Regression Test Suite*
