# AI Pattern Analyzer - Codebase Analysis Index

This directory contains comprehensive analysis of the AI Pattern Analyzer codebase.

## Documents

### 1. CODEBASE-ANALYSIS.md (900 lines)
**Comprehensive deep-dive analysis**

Covers:
- Complete 12-dimension inventory with feature counts
- Detailed tier analysis (ADVANCED/CORE/SUPPORTING)
- Architectural understanding (DimensionStrategy, Registry, Configuration)
- 70+ feature coverage breakdown
- Coverage gaps (what's NOT analyzed)
- Performance characteristics and bottlenecks
- v5.0.0 breaking changes from v4.x
- Step-by-step guide to adding new dimensions
- StyloMetrix integration opportunities

Use this when you need: Complete technical reference, architecture details, migration information

### 2. QUICK-REFERENCE.md (100 lines)
**Executive summary for quick lookup**

Contains:
- Current system at a glance (12 dimensions, 4 tiers)
- Feature coverage summary
- Architecture highlights
- Version history
- StyloMetrix differentiation opportunities
- Key metrics

Use this when you need: Quick overview, integration planning, feature comparison

### 3. DIMENSION-INVENTORY.txt (250 lines)
**Visual reference with ASCII diagrams**

Shows:
- Tier distribution by weight
- Bar-chart dimension rankings
- Feature coverage checklist
- Not covered opportunities
- Architecture pattern visualization
- Integration requirements
- Key statistics

Use this when you need: Visual reference, dimension weights, quick lookup

## Key Findings

### Current Status (v5.0.0)
- **12 active dimensions** across 4 tiers
- **70+ stylometric/linguistic features** analyzed
- **~7,770 lines** of production code (dimensions only)
- **106.0% total weight** (weighted average scoring)
- **Zero-modification architecture** for adding new dimensions

### Tier Breakdown
- **ADVANCED** (51%): Predictability, Advanced Lexical, Transition Marker, Syntactic
- **CORE** (35%): Perplexity, Readability, Burstiness, Voice, Formatting, Structure
- **SUPPORTING** (20%): Sentiment, Lexical

### What's Fully Covered
1. Lexical/Vocabulary (27+ AI terms, 18 transitions, word frequency)
2. Syntactic/Grammar (dependency trees, subordination, passive voice, POS)
3. Readability (Flesch, Gunning Fog, ARI, word/sentence length)
4. Stylistic (em-dashes, bold/italic, heading analysis, section uniformity)
5. Semantic/Pragmatic (sentiment, first-person, contractions, transitions)
6. ML-Based (GLTR 95% accuracy, DistilBERT sentiment)

### What's NOT Covered (StyloMetrix Opportunities)
1. Figurative language (metaphor, simile, irony)
2. Pragmatic markers (speech acts, hedging, certainty)
3. Author fingerprinting
4. Multi-model ensemble (GPT-3.5, GPT-4, Claude, Gemini)
5. Semantic coherence between sentences
6. Information density and structure

## Architecture Highlights

### Self-Registering Pattern
- New dimensions added with ZERO core modifications
- Dimensions auto-discover via registry
- No configuration files needed
- Thread-safe, testable, scalable

### Configuration Flexibility
- **Profiles**: fast (4), balanced (8), full (12) dimensions
- **Modes**: FAST (2-5s), ADAPTIVE (5-15s), SAMPLING (10-30s), FULL (30-120s)
- Mode-specific optimization per dimension
- Configuration-driven via AnalysisConfig

### Performance
- GLTR model caching: 2-10s first run, 0.1-0.5s cached
- Sentiment lazy-loaded: 50-100ms per chunk
- Memory: 700-1000MB (full), 100-150MB (fast)
- Thread-safe for concurrent analysis
- 120-second timeout on heavy operations

## Version History

### v5.0.0 (Current - Breaking Changes)
- Removed deprecated `advanced` dimension (655 lines)
- Removed deprecated `stylometric` dimension (378 lines)
- New intuitive labels: EXCELLENT/GOOD/NEEDS WORK/POOR
- Total cleanup: 1,033 lines removed
- Complete code quality improvement

### v4.x (Previous)
- 14 dimensions
- Confusing inverse labels
- Backward compatibility shims

## For StyloMetrix Development

### Already Covered (Avoid Duplication)
- Readability metrics
- Lexical diversity (8 different metrics)
- Sentiment analysis
- Formatting patterns
- Syntactic features

### Recommended Integration Areas
1. **Figurative Language**: Metaphor, simile, personification patterns
2. **Pragmatic Analysis**: Speech acts, hedging, certainty markers
3. **Author Fingerprinting**: Unique stylistic signatures
4. **Multi-Model Comparison**: Model-specific fingerprints
5. **Information Structure**: Density, progression, argument flow
6. **Cross-Document Analysis**: Consistency and topic drift

### Integration Path
1. Implement `DimensionStrategy` base class
2. Self-register with `DimensionRegistry`
3. Set appropriate weight (5-10%, avoid predictability's 20%)
4. Use lazy-loading for ML models
5. Thread-safe global state
6. Optional: `analyze_detailed()` for CLI findings

## Reading Guide

**For quick overview**: Start with QUICK-REFERENCE.md, then DIMENSION-INVENTORY.txt

**For integration planning**: Read QUICK-REFERENCE.md section "For StyloMetrix Integration", then CODEBASE-ANALYSIS.md Section 9

**For architecture deep-dive**: CODEBASE-ANALYSIS.md Sections 3-8

**For feature comparison**: CODEBASE-ANALYSIS.md Sections 4-5

**For adding dimensions**: CODEBASE-ANALYSIS.md Section 8 (step-by-step guide)

**For performance analysis**: CODEBASE-ANALYSIS.md Section 6

## Key Files in Codebase

### Core Architecture
- `/dimensions/base_strategy.py` - DimensionStrategy base class (830 lines)
- `/core/dimension_registry.py` - Registry pattern implementation
- `/core/analyzer.py` - Main orchestration (792 lines)
- `/dimensions/__init__.py` - Auto-registration hub

### Dimensions (12 total)
- `predictability.py` (616) - GLTR, highest accuracy
- `advanced_lexical.py` (485) - HDD, Yule's K, MATTR
- `structure.py` (1640) - Largest, heading/section analysis
- `formatting.py` (763) - Em-dash (95% accuracy)
- `burstiness.py` (516) - Sentence/paragraph variation
- `perplexity.py` (430) - 27+ AI vocabulary terms
- `voice.py` (385) - Personal authenticity
- `readability.py` (322) - Flesch, Gunning Fog
- `sentiment.py` (363) - DistilBERT emotional analysis
- `syntactic.py` (525) - spacy dependency trees
- `lexical.py` (361) - Type-Token Ratio
- `transition_marker.py` (376) - However/Moreover detection

### Supporting
- `/core/results.py` (540) - Result dataclasses
- `/scoring/dual_score.py` (220) - Scoring system
- `/scoring/dual_score_calculator.py` (392) - Score calculation
- `/utils/pattern_matching.py` (240) - Regex patterns, constants
- `/utils/text_processing.py` (180) - Text utilities

## Questions?

For technical details, see the corresponding sections in CODEBASE-ANALYSIS.md:
- Questions about dimensions? → Section 2
- Questions about architecture? → Section 3
- Questions about features? → Sections 4-5
- Questions about performance? → Section 6
- Questions about v5.0.0 changes? → Section 7
- Questions about adding dimensions? → Section 8
- Questions about StyloMetrix? → Section 9

---

Generated: 2025-11-11
Analysis Level: Very Thorough (Complete codebase review)
Total Analysis: 900+ lines of documentation
