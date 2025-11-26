# AI Pattern Analyzer - Quick Summary

## Current System (v5.0.0)

### 12 Dimensions Across 4 Tiers

**ADVANCED Tier (51% weight)** - ML-based, highest accuracy:
1. **Predictability** (20%) - GLTR token analysis, 95% accuracy
2. **Advanced Lexical** (14%) - HDD, Yule's K, MATTR, RTTR, Maas
3. **Transition Marker** (10%) - "However"/"Moreover" overuse
4. **Syntactic** (2%) - Dependency trees, subordination, POS

**CORE Tier (35% weight)** - Proven signatures >85% accuracy:
5. **Perplexity** (11%) - 27+ AI vocabulary terms + formulaic transitions
6. **Readability** (10%) - Flesch, Gunning Fog, ARI, word length
7. **Burstiness** (6%) - Sentence/paragraph length variation
8. **Voice** (5%) - First-person, contractions, domain expertise
9. **Formatting** (4%) - Em-dash (95% accuracy), bold/italic, quotations
10. **Structure** (4%) - Heading depth, parallelism, section uniformity

**SUPPORTING Tier (20% weight)** - Contextual quality indicators:
11. **Sentiment** (17%) - Emotional variation, flatness detection
12. **Lexical** (3%) - Type-Token Ratio, vocabulary richness

---

## Feature Coverage (~70+ Features)

### What's Analyzed
- 27+ AI vocabulary terms (delve, robust, leverage, ecosystem, paradigm shift, etc.)
- 18 formulaic transition phrases (Furthermore, Moreover, Additionally, etc.)
- 5-6 readability metrics (Flesch, Gunning Fog, ARI, etc.)
- 5 syntactic metrics (tree depth, subordination, passive voice, POS diversity)
- 8 lexical diversity metrics (TTR, HDD, Yule's K, MATTR, RTTR, Maas)
- 4-5 formatting patterns (em-dashes, bold/italic, quotations, consistency)
- 8-10 structural patterns (headings, sections, lists, nesting, parallelism)
- 4 voice markers (first-person, direct address, contractions, domain terms)
- 5 semantic patterns (sentiment variance, flatness, marker clustering)
- 3-4 ML metrics (GLTR token ranks, DistilBERT sentiment)

### What's NOT Analyzed
- Named Entity Recognition (NER) patterns
- Figurative language (metaphor, simile, irony)
- Semantic coherence between sentences
- Author fingerprinting
- Multi-model LLM comparison
- Pragmatic markers (speech acts, hedging)
- Cross-document consistency
- Information density
- Argument structure

---

## Architecture Excellence

### Zero-Modification Design
- New dimensions added without modifying core analyzer
- Self-registering via `DimensionStrategy` base class
- `DimensionRegistry` handles auto-discovery
- Thread-safe, testable, scalable

### Flexibility
- **Dimension Profiles**: fast (4), balanced (8), full (12)
- **Analysis Modes**: FAST (2-5s), ADAPTIVE (5-15s), SAMPLING (10-30s), FULL (30-120s)
- **Configuration-driven** via `AnalysisConfig`

### Performance
- GLTR model caching: 2-10s first run, 0.1-0.5s cached
- Sentiment lazy-loaded: 50-100ms per chunk
- Total memory: 700-1000MB (full), 100-150MB (fast)
- Thread-safe for concurrent analysis

---

## Version History

### v5.0.0 (Current) - Breaking Changes
- Removed deprecated `advanced` dimension (655 lines)
- Removed deprecated `stylometric` dimension (378 lines)
- Removed backward compatibility properties/dataclasses
- New intuitive labels: EXCELLENT/GOOD/NEEDS WORK/POOR (was HIGH/MEDIUM/LOW/VERY LOW)
- Total: 1,033 lines removed

### v4.x (Previous)
- 14 dimensions (had `advanced` + `stylometric`)
- Confusing inverse labels
- Backward compatibility shims

---

## For StyloMetrix Integration

### Already Covered (Don't Duplicate)
- Readability metrics (Flesch, Gunning Fog, ARI)
- Lexical diversity (TTR, HDD, Yule's K, MATTR, RTTR, Maas)
- Sentiment analysis (emotional variation)
- Formatting patterns (em-dashes, bold/italic)
- Syntactic features (tree depth, subordination)

### Opportunities for Differentiation
1. **Figurative Language** - Metaphor/simile detection
2. **Pragmatic Markers** - Speech acts, hedging, certainty
3. **Author Fingerprinting** - Unique stylistic signatures
4. **Multi-Model Ensemble** - Compare GPT-3.5, GPT-4, Claude, Gemini
5. **Information Structure** - Density, progression, argument flow
6. **Cross-Document Analysis** - Consistency across documents

### Integration Path
1. Implement `DimensionStrategy` base class
2. Register with `DimensionRegistry`
3. Set appropriate weight (avoid conflicting with predictability's 20%)
4. Use lazy-loading for ML models
5. Thread-safe global state management

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Production Code | ~7,770 lines (dimensions only) |
| Total Features | 70+ stylometric/linguistic |
| Architecture | Self-registering, zero-modification |
| Python Version | 3.8+ required |
| Key Dependencies | marko, nltk, spacy, textstat, transformers, torch, scipy, textacy |
| Test Coverage | Comprehensive regression suite |
| Threading | Fully thread-safe |
| Documentation | Excellent (migration guide, analysis modes guide) |

---

## Full Report Location

Comprehensive 900-line analysis available at:
`/Users/jmagady/Dev/B31590/.bmad-technical-writing/data/tools/writescore/docs/CODEBASE-ANALYSIS.md`

Includes:
- Detailed feature breakdown per dimension
- Performance bottleneck analysis
- How to add new dimensions (step-by-step)
- Coverage gap analysis
- StyloMetrix positioning recommendations
