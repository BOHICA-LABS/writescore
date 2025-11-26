# WriteScore Scripts

This directory contains utility scripts for WriteScore corpus generation and analysis.

## Validation Corpus Generation

### `generate_validation_corpus.py`

Generates a validation corpus for computing dimension statistics and performance benchmarking (Story 2.4.1, Task 8).

**Purpose:**
- Create 500+ document validation set (250 human, 250 AI)
- Support dimension statistics computation for score normalization
- Enable performance validation and benchmarking

**Usage:**

```bash
# Generate mock corpus for testing the generation pipeline
python scripts/generate_validation_corpus.py --mock --output validation_corpus/

# Generate real corpus (requires content sources - see Future Work below)
python scripts/generate_validation_corpus.py --output validation_corpus/
```

**Output Structure:**
```
validation_corpus/
  human/
    academic/        (50 docs: research papers, essays)
    social/          (50 docs: blog posts, social media)
    business/        (50 docs: reports, emails)
    technical/       (50 docs: documentation, tutorials)
    creative/        (50 docs: articles, narratives)
  ai/
    academic/        (50 docs: ChatGPT, Claude, etc.)
    social/          (50 docs)
    business/        (50 docs)
    technical/       (50 docs)
    creative/        (50 docs)
  metadata.json      (corpus statistics and provenance)
```

**Future Work:**

The script currently supports mock generation only. To collect a real validation corpus:

1. **Human Content Sources:**
   - Wikipedia articles (CC-BY-SA license)
   - Project Gutenberg books (public domain)
   - ArXiv papers (open access)
   - Stack Overflow posts (CC-BY-SA license)
   - News articles via APIs (check licensing)

2. **AI Content Generation:**
   - Implement API clients for OpenAI GPT-4
   - Implement API clients for Anthropic Claude
   - Use local models if available
   - Ensure diverse prompting strategies per domain

3. **Corpus Analysis:**
   - Run WriteScore analyzer on all 500 documents
   - Collect dimension scores for each document
   - Compute statistics (mean, stdev) per dimension
   - Update `scoring/dimension_stats.json` with real values
   - Validate normalization behavior

**Related Files:**
- `scoring/score_normalization.py` - Z-score normalization implementation
- `scoring/dimension_stats.json` - Dimension statistics (currently placeholder values)
- Story: `docs/stories/2.4.1.dimension-scoring-optimization.md`
- Quality Gate: `docs/qa/gates/2.4.1-dimension-scoring-optimization.yml`

**Estimated Effort:** 1-2 weeks (corpus collection + analysis)
