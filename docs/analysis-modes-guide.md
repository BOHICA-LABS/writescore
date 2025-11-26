# Analysis Modes Guide

## Quick Start

The AI Pattern Analyzer now supports four analysis modes that let you balance speed and accuracy:

```bash
# Fast mode - Quick analysis of document start (default)
python analyze_ai_patterns.py document.md

# Adaptive mode - Intelligent sampling based on document size
python analyze_ai_patterns.py document.md --mode adaptive

# Sampling mode - Custom sampling strategy
python analyze_ai_patterns.py document.md --mode sampling --samples 10 --sample-size 3000

# Full mode - Complete document analysis (most accurate)
python analyze_ai_patterns.py document.md --mode full
```

## Mode Comparison

| Mode | Speed | Accuracy | Best For | Coverage |
|------|-------|----------|----------|----------|
| **Fast** | ⚡⚡⚡ Fastest | ⭐⭐ Basic | Quick checks, early drafts | ~2000 chars/dimension |
| **Adaptive** | ⚡⚡ Fast | ⭐⭐⭐ Good | Most documents, standard workflow | Adjusts to size |
| **Sampling** | ⚡ Medium | ⭐⭐⭐⭐ High | Large documents, custom needs | User-defined |
| **Full** | 🐌 Slowest | ⭐⭐⭐⭐⭐ Best | Final review, critical content | 100% |

## Detailed Mode Descriptions

### Fast Mode (Default)

**When to Use:**
- Quick sanity checks during writing
- Early draft reviews
- Rapid iteration on small changes
- CI/CD pipeline checks

**How It Works:**
- Analyzes first ~2000 characters per dimension
- Skips heavy computations
- Provides directional feedback

**Example:**
```bash
python analyze_ai_patterns.py draft.md
# or explicitly:
python analyze_ai_patterns.py draft.md --mode fast
```

**Typical Speed:** 2-5 seconds for most documents

### Adaptive Mode

**When to Use:**
- Standard analysis workflow
- Medium to large documents (5k-100k words)
- When you want balanced speed and accuracy
- Most production use cases

**How It Works:**
- Documents < 5k chars: Full analysis
- Documents 5k-50k chars: 5 samples × 2000 chars
- Documents > 50k chars: 10 samples × 2000 chars
- Intelligently selects representative sections

**Example:**
```bash
python analyze_ai_patterns.py article.md --mode adaptive
```

**Typical Speed:** 5-15 seconds depending on document size

### Sampling Mode

**When to Use:**
- Very large documents (100k+ words)
- Custom sampling requirements
- Performance tuning
- Specific section analysis

**How It Works:**
- You control the number of samples and sample size
- Choose sampling strategy (uniform, weighted, start, end)
- Optimizes for your specific needs

**Example:**
```bash
# Sample 8 sections of 5000 chars each
python analyze_ai_patterns.py large-doc.md --mode sampling --samples 8 --sample-size 5000

# Weighted sampling (favors start/end)
python analyze_ai_patterns.py book.md --mode sampling --samples 15 --strategy weighted
```

**Sampling Strategies:**
- `uniform`: Even distribution across document
- `weighted`: More samples from start/end (default)
- `start`: Focus on beginning
- `end`: Focus on conclusion

**Typical Speed:** 10-30 seconds depending on parameters

### Full Mode

**When to Use:**
- Final manuscript review
- Critical content (academic, legal)
- Maximum accuracy requirements
- Benchmark/baseline analysis

**How It Works:**
- Analyzes entire document
- All dimensions at full depth
- Most comprehensive results
- No sampling or approximation

**Example:**
```bash
python analyze_ai_patterns.py final-manuscript.md --mode full
```

**Typical Speed:** 30-120+ seconds for large documents

## Decision Matrix

Use this matrix to choose the right mode:

| Situation | Recommended Mode | Why |
|-----------|------------------|-----|
| Writing first draft | Fast | Quick feedback loop |
| Reviewing edits | Adaptive | Balances speed and accuracy |
| Pre-submission check | Full | Maximum confidence |
| Large book chapter | Sampling | Efficient for large content |
| CI/CD pipeline | Fast or Adaptive | Speed matters |
| Academic paper | Full | Accuracy critical |
| Blog post | Fast or Adaptive | Sufficient for web content |
| Legal document | Full | Risk mitigation |

## Integration Examples

### Batch Analysis with Modes

```bash
# Analyze multiple files with adaptive mode
python analyze_ai_patterns.py chapter-*.md --mode adaptive --batch

# Custom sampling for large batch
python analyze_ai_patterns.py *.md --mode sampling --samples 5 --batch --output results.tsv
```

### Detailed Analysis with Modes

```bash
# Get detailed findings with full analysis
python analyze_ai_patterns.py manuscript.md --mode full --detailed

# Quick detailed check
python analyze_ai_patterns.py section.md --mode fast --detailed --output-format json
```

### Dual Score Reports with Modes

```bash
# Optimization report with adaptive mode
python analyze_ai_patterns.py article.md --mode adaptive --scores

# Full accuracy dual score
python analyze_ai_patterns.py critical-doc.md --mode full --scores
```

### History Tracking with Modes

History automatically tracks which mode was used:

```bash
# First iteration with full analysis
python analyze_ai_patterns.py draft.md --mode full --save-to-history

# Quick check with fast mode
python analyze_ai_patterns.py draft.md --mode fast --save-to-history

# View history with mode information
python analyze_ai_patterns.py draft.md --history-full
```

The history report shows mode and analysis time for each iteration:

```
ITERATION 1: Initial baseline
Timestamp:     2025-01-15
Mode:          FULL
Analysis Time: 45.3s
Quality:       72.0 / 100  (GOOD)
...
```

## Dry-Run Mode

Preview what the analyzer will do without running analysis:

```bash
# See what fast mode will analyze
python analyze_ai_patterns.py large-doc.md --mode fast --dry-run

# Preview sampling strategy
python analyze_ai_patterns.py book.md --mode sampling --samples 10 --dry-run
```

Output shows:
- Mode selected
- Coverage statistics
- Dimensions that will be analyzed
- Estimated analysis time

## Coverage Statistics

Display detailed coverage information:

```bash
python analyze_ai_patterns.py document.md --mode adaptive --show-coverage
```

Output shows:
- Document size
- Characters analyzed
- Coverage percentage
- Mode-specific details

## Performance Tuning Tips

### For Speed

1. **Use Fast Mode for iterations:**
   ```bash
   python analyze_ai_patterns.py draft.md --mode fast
   ```

2. **Reduce sample count:**
   ```bash
   python analyze_ai_patterns.py large.md --mode sampling --samples 3
   ```

3. **Use adaptive for automatic optimization:**
   ```bash
   python analyze_ai_patterns.py *.md --mode adaptive --batch
   ```

### For Accuracy

1. **Use Full Mode for final checks:**
   ```bash
   python analyze_ai_patterns.py final.md --mode full
   ```

2. **Increase sampling for large documents:**
   ```bash
   python analyze_ai_patterns.py book.md --mode sampling --samples 20 --sample-size 5000
   ```

3. **Use weighted sampling strategy:**
   ```bash
   python analyze_ai_patterns.py manuscript.md --mode sampling --strategy weighted
   ```

### For Large Documents

1. **Start with Sampling Mode:**
   ```bash
   python analyze_ai_patterns.py large-book.md --mode sampling --samples 15
   ```

2. **Adjust sample size based on document:**
   - Documents < 50k words: 5-10 samples
   - Documents 50k-100k words: 10-15 samples
   - Documents > 100k words: 15-25 samples

3. **Use adaptive if document size varies:**
   ```bash
   python analyze_ai_patterns.py *.md --mode adaptive --batch
   ```

## Mode Help

Get detailed information about modes:

```bash
python analyze_ai_patterns.py --help-modes
```

This displays:
- All four modes with descriptions
- Sampling strategies
- Usage examples
- Performance characteristics

## Troubleshooting

### "Analysis taking too long"

**Solution:** Switch to a faster mode
```bash
# Instead of:
python analyze_ai_patterns.py huge.md --mode full

# Try:
python analyze_ai_patterns.py huge.md --mode sampling --samples 10
```

### "Results seem inaccurate"

**Solution:** Use more thorough analysis
```bash
# Instead of:
python analyze_ai_patterns.py important.md --mode fast

# Try:
python analyze_ai_patterns.py important.md --mode full
```

### "Out of memory errors"

**Solution:** Reduce sample size or use fast mode
```bash
# Instead of:
python analyze_ai_patterns.py massive.md --mode full

# Try:
python analyze_ai_patterns.py massive.md --mode sampling --samples 10 --sample-size 2000
```

### "Invalid sample count"

**Error:** `Sample count must be between 1 and 50`

**Solution:** Adjust --samples parameter
```bash
# Valid:
python analyze_ai_patterns.py doc.md --mode sampling --samples 10

# Invalid (too high):
python analyze_ai_patterns.py doc.md --mode sampling --samples 100
```

### "Mode not working as expected"

**Solution:** Use --dry-run to verify configuration
```bash
python analyze_ai_patterns.py doc.md --mode sampling --samples 5 --dry-run
```

## Best Practices

### Development Workflow

1. **During Writing:** Use Fast mode for immediate feedback
   ```bash
   python analyze_ai_patterns.py draft.md --mode fast
   ```

2. **After Major Changes:** Use Adaptive mode for balanced review
   ```bash
   python analyze_ai_patterns.py draft.md --mode adaptive
   ```

3. **Before Submission:** Use Full mode for final validation
   ```bash
   python analyze_ai_patterns.py final.md --mode full --scores
   ```

### Team Workflow

1. **CI/CD Pipeline:** Fast or Adaptive for speed
   ```bash
   python analyze_ai_patterns.py *.md --mode adaptive --batch --output results.tsv
   ```

2. **Code Review:** Adaptive mode with history
   ```bash
   python analyze_ai_patterns.py changed-files.md --mode adaptive --save-to-history
   ```

3. **Release Validation:** Full mode for critical content
   ```bash
   python analyze_ai_patterns.py release-notes.md --mode full --detailed
   ```

### Content Type Guidelines

| Content Type | Recommended Mode | Frequency |
|--------------|------------------|-----------|
| Blog posts | Fast or Adaptive | Per save |
| Technical docs | Adaptive | Per major change |
| Marketing copy | Adaptive or Sampling | Daily |
| Academic papers | Full | Before submission |
| Books/ebooks | Sampling (10-15 samples) | Per chapter |
| Legal documents | Full | Before finalization |
| Social media | Fast | Per post |
| Email campaigns | Adaptive | Before send |

## Advanced Usage

### Custom Sampling Strategy

```bash
# Analyze start and end heavily
python analyze_ai_patterns.py novel.md --mode sampling --samples 20 --strategy weighted

# Uniform sampling across entire document
python analyze_ai_patterns.py article.md --mode sampling --samples 8 --strategy uniform

# Focus on beginning (intro analysis)
python analyze_ai_patterns.py report.md --mode sampling --samples 5 --strategy start

# Focus on end (conclusion analysis)
python analyze_ai_patterns.py thesis.md --mode sampling --samples 5 --strategy end
```

### Combining with Other Flags

```bash
# Full analysis with all reports
python analyze_ai_patterns.py manuscript.md --mode full --detailed --scores --save-to-history

# Fast batch with JSON output
python analyze_ai_patterns.py *.md --mode fast --batch --output-format json --output results.json

# Sampling with coverage display
python analyze_ai_patterns.py large.md --mode sampling --samples 10 --show-coverage

# Adaptive with dry-run first
python analyze_ai_patterns.py doc.md --mode adaptive --dry-run
python analyze_ai_patterns.py doc.md --mode adaptive
```

## Mode Selection Algorithm

The tool uses this logic when mode is not specified:

1. **Check --mode flag:** If specified, use that mode
2. **Default to Fast:** Most common use case
3. **Adaptive recommended:** For production workflows
4. **Full for critical:** When accuracy is paramount

## Migration from Previous Versions

If you've been using the analyzer without modes:

**Old command:**
```bash
python analyze_ai_patterns.py document.md
```

**New equivalent (same behavior):**
```bash
python analyze_ai_patterns.py document.md --mode fast
```

**Recommended upgrade:**
```bash
python analyze_ai_patterns.py document.md --mode adaptive
```

All existing commands work without changes. Modes are purely additive.

## FAQ

**Q: Which mode should I use most often?**
A: Adaptive mode for most work, Fast for quick checks, Full for final reviews.

**Q: Do different modes give different scores?**
A: Scores may vary slightly due to sampling, but trends and insights are consistent.

**Q: Can I change modes between iterations in history?**
A: Yes! History tracks which mode was used for each iteration.

**Q: Does batch mode work with all analysis modes?**
A: Yes, all modes work with --batch flag.

**Q: Will modes affect my existing scripts?**
A: No, existing commands work identically. Default is Fast mode (previous behavior).

**Q: How do I know which mode was used?**
A: Check the output header, history report, or use --show-coverage.

**Q: Can I use modes with --detailed flag?**
A: Yes, modes work with all existing flags (--detailed, --scores, --batch, etc.).

**Q: What if I run out of memory with Full mode?**
A: Use Sampling mode with fewer samples or smaller sample size.

## Summary

- **Fast:** Quick checks (default)
- **Adaptive:** Smart balance (recommended)
- **Sampling:** Large documents
- **Full:** Maximum accuracy

Start with Adaptive, adjust based on your needs. Use --dry-run to preview, --show-coverage to understand, and --help-modes for detailed reference.
