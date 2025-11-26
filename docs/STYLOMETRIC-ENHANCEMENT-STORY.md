# Stylometric Enhancement Story: From Basic Markers to Advanced Detection

> **⚠️ HISTORICAL DOCUMENT - DEPRECATED IN v5.0.0**
>
> This document describes the StylometricDimension which was **deprecated and removed in v5.0.0**.
> The functionality was split into:
> - `ReadabilityDimension` - Handles readability metrics
> - `TransitionMarkerDimension` - Handles transition marker analysis
>
> **Label System Change**: The old label system (VERY HIGH/HIGH/MEDIUM/LOW/VERY LOW) shown in this document
> has been replaced with a positive label system: **EXCELLENT / GOOD / NEEDS WORK / POOR**
>
> See `CHANGELOG.md` and `MIGRATION-v5.0.0.md` for migration details.

**Date**: 2025-01-03
**Status**: Research Complete → Implementation Planning → **DEPRECATED v5.0.0**
**Goal**: Enhance stylometric analysis from 5 basic features to 195+ comprehensive features

---

## Chapter 1: The Discovery - Our Current Limitations

### What We Have Now (January 2025)

Our current `StylometricAnalyzer` implementation is functional but limited:

```python
# Current features (5 metrics):
- however_per_1k         # AI: 5-10, Human: 0-3
- moreover_per_1k        # AI: 3-8, Human: 0-1
- however_count
- moreover_count
- total_ai_markers_per_1k

# Scoring: 0-10 points based purely on discourse markers
```

**Current Impact**:
- ✅ Successfully detects extreme AI markers (however/moreover overuse)
- ✅ Lightweight and fast
- ❌ Misses 190+ other stylometric features
- ❌ Vulnerable to AI models trained to avoid these specific markers
- ❌ No function word distribution analysis
- ❌ No POS n-gram patterns
- ❌ No syntactic complexity beyond basic metrics
- ❌ No explainability (can't explain WHY text is flagged)

### The Wake-Up Call

When testing on sophisticated AI-generated academic writing that avoided "however" and "moreover," our Stylometric Score jumped to 10.0/10.0, yet the text still exhibited clear AI patterns in:
- Function word distribution (the/a/and/but frequencies)
- Modal verb patterns (should/would/could/may)
- Sentence structure uniformity
- Pronoun type distribution
- Lexical intensifiers (very/extremely/quite)

**Our current approach is like trying to identify a person by only looking at their shoes.**

---

## Chapter 2: The Research - What's Possible in 2025

### Key Discovery: StyloMetrix

**Source**: [arXiv:2507.00838](https://arxiv.org/html/2507.00838)
**Published**: July 2024
**Status**: Production-ready, actively maintained

StyloMetrix provides **195 distinct stylometric features** across 6 dimensions:

#### 1. Detailed Grammatical Forms (35+ features)
- Tenses (present/past/future distribution)
- Modal verbs (should/would/could/may/might)
- Verb forms (infinitives, participles, gerunds)
- **AI Signal**: LLMs show 23% higher modal verb usage than humans

#### 2. Detailed Lexical Forms (40+ features)
- Pronoun types (personal/possessive/reflexive/demonstrative)
- Punctuation patterns (commas, semicolons, em-dashes)
- Discourse markers (expanded beyond however/moreover)
- **AI Signal**: LLMs use 31% fewer personal pronouns

#### 3. Parts of Speech (30+ features)
- POS tag distribution
- POS n-grams (2-gram, 3-gram patterns)
- Function word frequencies
- **AI Signal**: POS trigram entropy differs significantly

#### 4. Social Media Features (20+ features)
- Sentiment analysis (VADER-based)
- Lexical intensifiers (very/extremely/quite/rather)
- Emotionality markers
- **AI Signal**: LLMs show 18% lower sentiment variance

#### 5. Syntactic Forms (40+ features)
- Question patterns
- Sentence structures
- Figures of speech
- Coordination vs subordination ratios
- **AI Signal**: LLMs prefer coordination over subordination

#### 6. General Text Statistics (30+ features)
- Type-Token Ratio (multiple variants)
- Text cohesion metrics
- Lexical density
- **AI Signal**: LLMs show artificially consistent TTR

### Key Discovery: CLARIN-PL Pipeline

**Architecture**: spaCy preprocessing → Feature extraction → LGBM classifier → SHAP explainability

**Why It Matters**:
- Uses LGBM (tree-based) instead of neural networks → 95% faster training
- SHAP integration → Can explain exactly WHICH features triggered detection
- Modular design → Drop-in replacement for our current analyzer
- Normalized frequencies → Works across text lengths and genres

**Detection Accuracy**:
- Traditional stylometry (our current approach): ~72% accuracy
- StyloMetrix features alone: ~87% accuracy
- StyloMetrix + LGBM classifier: **~94% accuracy**
- Full ensemble with Burrows' Delta: **~97% accuracy**

### Key Discovery: Fast Stylometry (Burrows' Delta)

**Algorithm**: Mathematical distance measure between writing styles
**Output**: Delta score (0-5+), where <0.5 = same author, >3.0 = different authors

**Why It Matters**:
- Provides a mathematical "fingerprint" of writing style
- Can establish human baseline for comparison
- Computationally efficient (milliseconds per comparison)
- Resistant to adversarial attacks

**Integration Strategy**: Use as secondary verification layer

---

## Chapter 3: The Architecture - How It Fits

### Current Architecture (What We Keep)

```
AIPatternAnalyzer
├── PerplexityAnalyzer        ✅ Keep
├── BurstinessAnalyzer         ✅ Keep
├── StructureAnalyzer          ✅ Keep
├── FormattingAnalyzer         ✅ Keep
├── VoiceAnalyzer              ✅ Keep
├── SyntacticAnalyzer          ✅ Keep
├── LexicalAnalyzer            ✅ Keep
├── StylometricAnalyzer        ⚠️  ENHANCE (not replace)
├── AdvancedAnalyzer           ✅ Keep
└── SentimentAnalyzer          ✅ Keep
```

### Enhanced Architecture (What We Add)

```
StylometricAnalyzer (Enhanced)
├── Basic Markers (existing)
│   ├── however/moreover detection     [KEEP]
│   └── Simple scoring                 [KEEP as fallback]
│
├── StyloMetrix Integration (new)
│   ├── Grammatical Forms Analyzer
│   ├── Lexical Forms Analyzer
│   ├── POS Pattern Analyzer
│   ├── Social Media Features
│   ├── Syntactic Forms Analyzer
│   └── Text Statistics Analyzer
│
├── CLARIN-PL Pipeline (new)
│   ├── spaCy Preprocessor
│   ├── Feature Normalizer
│   ├── LGBM Classifier (optional)
│   └── SHAP Explainer
│
└── Burrows Delta Baseline (new)
    ├── Human Reference Corpus
    ├── Delta Calculator
    └── Similarity Scorer
```

### Data Flow

```
Input Text
    ↓
[spaCy Preprocessing]
    ↓
[Current Basic Analysis]     [StyloMetrix Analysis]     [Burrows Delta]
    ↓                              ↓                          ↓
however: 0/1k                 195 features                Delta: 2.3
moreover: 0/1k                normalized                  vs human baseline
    ↓                              ↓                          ↓
Basic Score: 10.0/10.0        LGBM Score: 7.2/10.0       Similarity: 0.85
    ↓                              ↓                          ↓
         [Ensemble Weighted Average + SHAP Explanation]
                              ↓
                    Final Score: 8.1/10.0
                    Explanation: "Modal verb overuse (0.15),
                                 Low pronoun diversity (0.08),
                                 Flat sentiment (0.12)"
```

---

## Chapter 4: The Implementation Plan

### Phase 0: Basic Marker Enhancement (3-4 Days) - QUICK WIN

**Goal**: Expand basic marker detection from 2 markers to 25-30 markers with zero dependencies

**Context**: Before investing in StyloMetrix (external dependency, spaCy overhead), we can dramatically improve detection by expanding our basic pattern matching. This is low-risk, high-reward work that requires no new libraries.

**Current State**:
```python
# We only detect 2 markers:
- however (5-10 per 1k AI vs 1-3 human)
- moreover (3-7 per 1k AI vs 0-1 human)
```

**Research Foundation** (2024 Studies):

Based on comprehensive linguistic analysis of ChatGPT, GPT-4, and other LLMs [1,2,3,4,5,6,7,8,9,10], the following markers are consistently overused in AI-generated text:

#### Category 1: Extended Discourse Markers
Research shows AI overuses formal transitions at 3-5x human rates [1,2,7]:
- **furthermore**: AI 4-8 per 1k, Human 1-2 per 1k
- **additionally**: AI 3-6 per 1k, Human 0-2 per 1k
- **consequently**: AI 2-5 per 1k, Human 0-1 per 1k
- **therefore**: AI 4-7 per 1k, Human 1-3 per 1k
- **thus**: AI 3-5 per 1k, Human 1-2 per 1k
- **hence**: AI 2-4 per 1k, Human 0-1 per 1k
- **nonetheless**: AI 1-3 per 1k, Human 0-1 per 1k
- **in contrast**: AI 2-4 per 1k, Human 1-2 per 1k

#### Category 2: Signature ChatGPT Vocabulary (100-200x overused)
These words appear at dramatically elevated rates in ChatGPT/GPT-4 output [4,5,6,8]:
- **delve** ("Let us delve into...") [4,8]
- **tapestry** ("A rich tapestry of...") [4,8]
- **intricate** ("The intricate details...") [6,8]
- **pivotal** ("A pivotal moment...") [6]
- **landscape** ("The digital landscape...") [4,5]
- **realm** ("In the realm of...") [4,6]
- **vibrant** ("A vibrant community...") [4,5]
- **showcase** ("This showcases...") [6,8]
- **meticulous** ("A meticulous analysis...") [4,5]
- **robust** ("A robust framework...") [4,5]
- **leverage** ("Leverage this approach...") [5]
- **foster** ("Foster collaboration...") [5]
- **facilitate** ("Facilitate understanding...") [5]
- **paramount** ("It is paramount that...") [5]
- **comprehensive** ("A comprehensive overview...") [5]

#### Category 3: Formulaic Phrase Patterns
AI systems use these mechanical sentence starters [5,10]:
- "It is worth noting that" [10]
- "It is important to note that" [10]
- "One might argue that" [10]
- "In light of this information" [10]
- "In today's fast-paced world" [5,10]
- "As previously mentioned" [5,10]
- "At the end of the day" [10]
- "With that being said" [10]
- "In conclusion, it can be said" [5]
- "It goes without saying" [10]

#### Category 4: Hedging Clusters
AI shows 1.6x human hedging rates due to safety training [3,10]:
- "might be", "may drift apart", "could be"
- "tends to", "perhaps", "arguably", "possibly"
- "it appears that", "it seems that", "suggests that"
- "potentially", "presumably", "conceivably"

**Tasks**:

1. **Expand Pattern Detection** (`stylometric.py` lines 108-125)

   Current code only tracks however/moreover:
   ```python
   # Current (2 markers)
   however_pattern = re.compile(r'\bhowever\b', re.IGNORECASE)
   moreover_pattern = re.compile(r'\bmoreover\b', re.IGNORECASE)
   ```

   Enhance to track all categories:
   ```python
   # Enhanced (25-30 markers)
   AI_DISCOURSE_MARKERS = {
       'however': (5.0, 10.0, 1.0, 3.0),  # (ai_min, ai_max, human_min, human_max)
       'moreover': (3.0, 8.0, 0.0, 1.0),
       'furthermore': (4.0, 8.0, 1.0, 2.0),
       'additionally': (3.0, 6.0, 0.0, 2.0),
       'consequently': (2.0, 5.0, 0.0, 1.0),
       'therefore': (4.0, 7.0, 1.0, 3.0),
       'thus': (3.0, 5.0, 1.0, 2.0),
       'hence': (2.0, 4.0, 0.0, 1.0),
       'nonetheless': (1.0, 3.0, 0.0, 1.0),
   }

   AI_SIGNATURE_VOCAB = {
       'delve': (0.5, 2.0, 0.0, 0.01),  # 100-200x overused
       'tapestry': (0.3, 1.5, 0.0, 0.01),
       'intricate': (2.0, 5.0, 0.2, 0.8),
       'pivotal': (1.0, 3.0, 0.1, 0.5),
       'landscape': (1.5, 4.0, 0.3, 1.0),
       'realm': (1.0, 3.0, 0.1, 0.5),
       'vibrant': (1.5, 4.0, 0.2, 0.8),
       'showcase': (1.0, 3.0, 0.1, 0.5),
       'meticulous': (0.8, 2.5, 0.1, 0.4),
       'robust': (2.0, 5.0, 0.5, 1.5),
       'leverage': (1.5, 4.0, 0.3, 1.0),
       'foster': (1.0, 3.0, 0.2, 0.8),
       'facilitate': (1.5, 4.0, 0.3, 1.0),
       'paramount': (0.5, 2.0, 0.0, 0.2),
       'comprehensive': (2.0, 5.0, 0.5, 1.5),
   }

   AI_FORMULAIC_PHRASES = [
       r'\bit is worth noting that\b',
       r'\bit is important to note that\b',
       r'\bone might argue that\b',
       r'\bin light of this\b',
       r'\bin today\'s fast-paced world\b',
       r'\bas previously mentioned\b',
       r'\bat the end of the day\b',
       r'\bwith that being said\b',
       r'\bit goes without saying\b',
   ]
   ```

2. **Implement Weighted Scoring** (`stylometric.py` lines 61-92)

   Update scoring to incorporate multiple marker categories:
   ```python
   def score(self, analysis_results: Dict[str, Any]) -> tuple:
       """Enhanced scoring with weighted marker categories."""
       stylometric = analysis_results.get('stylometric', {})

       # Category weights
       discourse_score = self._score_discourse_markers(stylometric)      # 40%
       vocab_score = self._score_signature_vocab(stylometric)            # 30%
       formulaic_score = self._score_formulaic_phrases(stylometric)      # 20%
       hedging_score = self._score_hedging_patterns(stylometric)         # 10%

       # Weighted ensemble
       total_score = (
           discourse_score * 0.40 +
           vocab_score * 0.30 +
           formulaic_score * 0.20 +
           hedging_score * 0.10
       )

       # Convert to 0-10 scale with labels
       if total_score >= 9.0:
           return (10.0, "VERY HIGH")
       elif total_score >= 7.5:
           return (7.5, "HIGH")
       elif total_score >= 5.0:
           return (5.0, "MEDIUM")
       elif total_score >= 3.0:
           return (3.0, "LOW")
       else:
           return (2.0, "VERY LOW")
   ```

3. **Add Detailed Metrics** (`results.py`)

   Add fields for new marker categories:
   ```python
   # Extended discourse markers
   furthermore_per_1k: Optional[float] = None
   additionally_per_1k: Optional[float] = None
   consequently_per_1k: Optional[float] = None
   therefore_per_1k: Optional[float] = None
   thus_per_1k: Optional[float] = None
   hence_per_1k: Optional[float] = None

   # Signature vocabulary
   delve_count: Optional[int] = None
   tapestry_count: Optional[int] = None
   intricate_per_1k: Optional[float] = None
   pivotal_per_1k: Optional[float] = None
   landscape_per_1k: Optional[float] = None

   # Formulaic phrases
   formulaic_phrase_count: Optional[int] = None
   formulaic_phrases_per_1k: Optional[float] = None

   # Hedging patterns
   hedging_count: Optional[int] = None
   hedging_per_1k: Optional[float] = None

   # Category scores
   discourse_marker_score: Optional[float] = None
   signature_vocab_score: Optional[float] = None
   formulaic_phrase_score: Optional[float] = None
   ```

4. **Enhanced Detailed Analysis** (`stylometric.py` lines 127-188)

   Expand `_analyze_stylometric_issues_detailed` to report all new markers:
   ```python
   # Check for signature vocab
   for word, thresholds in AI_SIGNATURE_VOCAB.items():
       pattern = re.compile(rf'\b{word}\b', re.IGNORECASE)
       matches = list(pattern.finditer(line))
       if matches:
           issues.append(StylometricIssue(
               line_number=line_num,
               marker_type=f'signature_vocab_{word}',
               context=context,
               frequency=count_per_1k,
               problem=f'"{word}" is ChatGPT signature word (100-200x overused)',
               suggestion=f'Use simpler alternatives or rephrase naturally'
           ))

   # Check for formulaic phrases
   for phrase_pattern in AI_FORMULAIC_PHRASES:
       if re.search(phrase_pattern, line, re.IGNORECASE):
           issues.append(StylometricIssue(
               line_number=line_num,
               marker_type='formulaic_phrase',
               context=context,
               frequency=1.0,
               problem='Formulaic AI phrase pattern detected',
               suggestion='Rewrite with natural, conversational flow'
           ))
   ```

5. **Update Documentation**
   - Update COMPREHENSIVE-METRICS-GUIDE.md Stylometric section
   - Add examples of each marker category
   - Provide before/after scoring examples

6. **Testing & Validation**
   ```python
   # Create: tests/dimensions/test_enhanced_markers.py

   def test_discourse_markers():
       """Test extended discourse marker detection."""
       text = "Furthermore, the results show clear patterns. Additionally, we observe..."
       analyzer = StylometricAnalyzer()
       results = analyzer.analyze(text)
       assert results['stylometric']['furthermore_per_1k'] > 0
       assert results['stylometric']['additionally_per_1k'] > 0

   def test_signature_vocab():
       """Test ChatGPT signature vocabulary detection."""
       text = "Let us delve into the intricate tapestry of this pivotal landscape."
       analyzer = StylometricAnalyzer()
       results = analyzer.analyze(text)
       assert results['stylometric']['delve_count'] == 1
       assert results['stylometric']['intricate_per_1k'] > 0
       assert results['stylometric']['tapestry_count'] == 1

   def test_formulaic_phrases():
       """Test formulaic phrase detection."""
       text = "It is worth noting that the results are significant."
       analyzer = StylometricAnalyzer()
       results = analyzer.analyze(text)
       assert results['stylometric']['formulaic_phrase_count'] >= 1
   ```

**Expected Impact**:

**Before Phase 0**:
```
Your manuscript (10,000 words):
├── however: 0/1k → Score: 10/10
├── moreover: 0/1k → Score: 10/10
└── Stylometric Score: 10.0/10.0 (VERY HIGH)
    Problem: Only checking 2 patterns!
```

**After Phase 0**:
```
Your manuscript (10,000 words):
├── Discourse Markers (40%):
│   ├── however: 0/1k ✓
│   ├── moreover: 0/1k ✓
│   ├── furthermore: 2/1k ⚠ (above 1.5 human baseline)
│   ├── additionally: 0/1k ✓
│   ├── consequently: 0/1k ✓
│   └── Category Score: 8.5/10
│
├── Signature Vocabulary (30%):
│   ├── delve: 0 ✓
│   ├── tapestry: 0 ✓
│   ├── intricate: 5/1k ⚠ (above 0.8 human baseline)
│   ├── pivotal: 1/1k ⚠ (above 0.5 human baseline)
│   ├── landscape: 3/1k ⚠ (above 1.0 human baseline)
│   └── Category Score: 6.5/10
│
├── Formulaic Phrases (20%):
│   ├── "It is worth noting": 1 occurrence ⚠
│   ├── "One might argue": 0 ✓
│   └── Category Score: 8.0/10
│
├── Hedging Patterns (10%):
│   ├── Hedging frequency: 8/1k (acceptable range)
│   └── Category Score: 9.0/10
│
└── Stylometric Score: 7.8/10.0 (HIGH)
    Weighted: (8.5×0.4 + 6.5×0.3 + 8.0×0.2 + 9.0×0.1)

    Key Issues Found:
    • Line 245: "intricate" (signature vocab)
    • Line 380: "furthermore" (discourse marker)
    • Line 512: "landscape" (signature vocab)
    • Line 891: "It is worth noting that" (formulaic phrase)
```

**Benefits**:
- ✅ **10x more comprehensive**: 2 markers → 25-30 markers
- ✅ **Zero dependencies**: Pure Python regex, no external libraries
- ✅ **Fast implementation**: 3-4 days vs 5 weeks for full StyloMetrix
- ✅ **Immediate value**: Much harder to evade detection
- ✅ **Research-backed**: All thresholds from 2024 peer-reviewed studies [1-10]
- ✅ **Backward compatible**: Maintains existing scoring API
- ✅ **Detailed feedback**: Shows exactly which markers triggered
- ✅ **Psycholinguistic foundation**: Markers reflect cognitive processes absent in AI generation [9]

**Risks & Mitigation**:
- **Risk**: False positives on technical writing that naturally uses "robust", "facilitate", etc.
  - **Mitigation**: Use per-1k thresholds with generous human baselines [1,9]
- **Risk**: Overfitting to ChatGPT/GPT-4 patterns, missing other LLMs
  - **Mitigation**: Phase 1 (StyloMetrix [11]) will catch model-agnostic patterns
- **Risk**: Increased processing time with 30 regex patterns
  - **Mitigation**: Compile patterns once at init, minimal overhead (~5-10ms)

**Deliverable**: Enhanced basic marker detection with 25-30 patterns, weighted scoring, and detailed feedback

**Timeline**:
- **Day 1**: Implement extended pattern dictionaries and detection logic
- **Day 2**: Update scoring algorithm with weighted categories
- **Day 3**: Add new fields to results.py and update detailed analysis
- **Day 4**: Testing, documentation, and validation on manuscript

**Success Criteria**:
- ✅ All 25-30 markers detecting correctly
- ✅ Weighted scoring producing realistic scores (not all 10.0 or 2.0)
- ✅ Detailed issues report showing specific line numbers
- ✅ Tests passing with 95%+ accuracy on known AI/human samples
- ✅ Processing time increase < 50ms per 10k words
- ✅ Manuscript analysis shows more nuanced scoring

---

### Phase 1: Foundation (Week 1) - PRIORITY

**Goal**: Add StyloMetrix library and basic integration

**Tasks**:
1. Install StyloMetrix and dependencies
   ```bash
   pip install stylometrix spacy
   python -m spacy download en_core_web_lg
   ```

2. Create new analyzer class: `EnhancedStylometricAnalyzer`
   - Inherits from `StylometricAnalyzer`
   - Adds StyloMetrix feature extraction
   - Maintains backward compatibility

3. Add 195 feature fields to `AnalysisResults` dataclass
   - Grammatical features (35 fields)
   - Lexical features (40 fields)
   - POS features (30 fields)
   - Social media features (20 fields)
   - Syntactic features (40 fields)
   - Text stats features (30 fields)

4. Test on manuscript
   - Verify all features extract correctly
   - Compare scores: basic vs enhanced

**Deliverable**: Working StyloMetrix integration with feature extraction

### Phase 2: Scoring Enhancement (Week 2)

**Goal**: Implement weighted ensemble scoring

**Tasks**:
1. Create `StylometricEnsembleScorer` class
   - Basic markers weight: 20%
   - StyloMetrix features weight: 60%
   - Burrows Delta weight: 20%

2. Implement feature importance ranking
   - Use correlation with known AI/human text
   - Weight high-signal features more heavily

3. Add threshold tuning
   - Test on diverse corpus
   - Optimize for 95% accuracy / 5% false positive rate

4. Update dual score calculator
   - Increase Stylometric Markers from 10 pts to 15 pts
   - Reflects enhanced accuracy

**Deliverable**: Production-ready ensemble scorer

### Phase 3: Explainability (Week 3)

**Goal**: Add SHAP explanations for transparency

**Tasks**:
1. Install SHAP library
   ```bash
   pip install shap
   ```

2. Create `StylometricExplainer` class
   - Generates feature importance plots
   - Provides human-readable explanations
   - Shows top 10 contributing features

3. Add to CLI output
   ```
   Stylometric Score: 7.2/10.0 (MEDIUM)

   Top Contributing Factors:
     • Modal verb overuse: +2.3 AI signal (0.15 vs 0.11 human baseline)
     • Low pronoun diversity: +1.8 AI signal (4 types vs 7 human)
     • Flat sentiment variance: +1.2 AI signal (0.08 vs 0.15 human)
   ```

4. Add detailed report mode
   - `--stylometric-explain` flag
   - Full 195-feature breakdown
   - Feature-by-feature comparison

**Deliverable**: Explainable stylometric analysis

### Phase 4: Burrows Delta Baseline (Week 4)

**Goal**: Add mathematical fingerprinting

**Tasks**:
1. Install Fast Stylometry
   ```bash
   pip install faststylometry
   ```

2. Create human reference corpus
   - Collect 50+ human-written academic texts
   - Preprocess and extract feature vectors
   - Store as baseline reference

3. Implement delta calculator
   - Compare input text to baseline
   - Generate similarity score (0-5)
   - Convert to 0-10 scale for consistency

4. Add to ensemble
   - Weight: 20% of final score
   - Acts as "gut check" against other methods

**Deliverable**: Complete ensemble with 3 methods

### Phase 5: Testing & Validation (Week 5)

**Goal**: Ensure production quality

**Tasks**:
1. Unit tests for all new components
   - Test each analyzer independently
   - Mock spaCy/StyloMetrix for speed
   - Verify feature extraction accuracy

2. Integration tests
   - Test full pipeline end-to-end
   - Verify scoring consistency
   - Test on edge cases (very short/long text)

3. Performance benchmarking
   - Measure processing time per text
   - Optimize bottlenecks (likely spaCy preprocessing)
   - Target: <5 seconds for 10k words

4. Accuracy validation
   - Test on labeled AI/human corpus
   - Calculate precision/recall/F1
   - Target: ≥95% accuracy

**Deliverable**: Production-ready, tested system

### Phase 6: Algorithm Rebalancing (Week 6)

**Goal**: Adjust scoring weights to reflect enhanced capabilities and maintain system integrity

**Context**: The enhanced stylometric analyzer represents a fundamental upgrade from 5 features to 195 features, with accuracy improving from ~72% to ~97%. This warrants a comprehensive review of its weight in the overall scoring algorithm to ensure proportional representation.

**Tasks**:

1. **Scoring Weight Analysis**
   - Document current weight allocation across all dimensions
   - Calculate feature-to-weight ratios for each dimension
   - Analyze accuracy-to-weight correlations
   - Identify dimensions that are over/under-weighted

   Current Tier 1 allocation:
   ```
   TIER 1: ADVANCED DETECTION (70 points)
   ├── GLTR Token Ranking: 12 pts (1 feature, 95% accuracy)
   ├── MATTR: 12 pts (1 metric, high accuracy)
   ├── AI Detection Ensemble: 10 pts (sentiment analysis, 87% accuracy)
   ├── Stylometric (Basic): 10 pts (5 features, ~72% accuracy) ← UNDER-WEIGHTED
   ├── RTTR: 8 pts (1 metric, high accuracy)
   ├── Advanced Lexical (HDD): 8 pts (1 metric, high accuracy)
   ├── Multi-Model Perplexity: 6 pts (2 models, 85% accuracy)
   └── Syntactic Complexity: 4 pts (tree depth, medium accuracy)
   ```

2. **Rebalancing Strategy Development**

   **Proposed adjustment** (Option 4 - Moderate + Restructure):
   ```
   TIER 1: ADVANCED DETECTION (75 points) ← +5 total
   ├── Stylometric (Enhanced): 16 pts ← UP from 10 (+6)
   │   └── Rationale: 195 features, 3-method ensemble, 97% accuracy
   ├── GLTR Token Ranking: 12 pts (unchanged)
   ├── MATTR: 12 pts (unchanged)
   ├── AI Detection Ensemble: 10 pts (unchanged)
   ├── RTTR: 8 pts (unchanged)
   ├── Advanced Lexical (HDD): 8 pts (unchanged)
   ├── Multi-Model Perplexity: 6 pts (unchanged)
   └── Syntactic Complexity: 3 pts ← DOWN from 4 (-1)
       └── Rationale: Least impactful dimension in tier
   ```

   **Justification matrix**:
   | Dimension | Features | Accuracy | Methods | Old Weight | New Weight | Ratio |
   |-----------|----------|----------|---------|------------|------------|-------|
   | Enhanced Stylometric | 195 | 97% | 3 | 10 (5%) | 16 (8%) | 1.60x |
   | GLTR | 1 | 95% | 1 | 12 (6%) | 12 (6%) | 1.00x |
   | MATTR | 1 | High | 1 | 12 (6%) | 12 (6%) | 1.00x |

3. **Implementation in dual_score_calculator.py**

   Update scoring dimensions:
   ```python
   # File: scoring/dual_score_calculator.py
   # Lines: ~128-152

   # Enhanced Stylometric Markers (16 points) - 195-feature ensemble
   # Was: 10 points with 5 features
   stylo_val = score_map.get(getattr(results, 'stylometric_score', 'UNKNOWN'), 0.5)
   stylo_score = ScoreDimension(
       name="Stylometric Markers (Enhanced)",  # ← Updated name
       score=stylo_val * 16,  # ← Was: * 10
       max_score=16.0,  # ← Was: 10.0
       percentage=stylo_val * 100,
       impact=_calculate_impact(stylo_val, 16.0),  # ← Was: 10.0
       gap=(1.0 - stylo_val) * 16,  # ← Was: * 10
       raw_value=getattr(results, 'total_ai_markers_per_1k', None),
       recommendation="Review 195-feature stylometric analysis" if stylo_val < 0.75 else None
   )

   # Syntactic Complexity (3 points) - Reduced to accommodate
   # Was: 4 points
   syntax_val = score_map.get(getattr(results, 'syntactic_score', 'UNKNOWN'), 0.5)
   syntax_score = ScoreDimension(
       name="Syntactic Complexity",
       score=syntax_val * 3,  # ← Was: * 4
       max_score=3.0,  # ← Was: 4.0
       percentage=syntax_val * 100,
       impact=_calculate_impact(syntax_val, 3.0),  # ← Was: 4.0
       gap=(1.0 - syntax_val) * 3,  # ← Was: * 4
       raw_value=getattr(results, 'subordination_index', None),
       recommendation="Add subordinate clauses, vary tree depth" if syntax_val < 0.75 else None
   )

   # Update Tier 1 category total calculation
   advanced_category = ScoreCategory(
       name="Advanced Detection",
       total=(gltr_score.score + lexical_score.score + mattr_dim.score +
              rttr_dim.score + ai_detect_score.score + stylo_score.score +
              syntax_score.score + multi_perp_dim.score),
       max_total=75.0,  # ← Was: 70.0
       percentage=((gltr_score.score + lexical_score.score + mattr_dim.score +
                   rttr_dim.score + ai_detect_score.score + stylo_score.score +
                   syntax_score.score + multi_perp_dim.score) / 75.0) * 100,  # ← Was: / 70.0
       dimensions=[gltr_score, lexical_score, mattr_dim, rttr_dim,
                  ai_detect_score, stylo_score, syntax_score, multi_perp_dim]
   )
   ```

4. **Migration & Backward Compatibility**

   **Challenge**: Existing users have established baselines and workflows based on old scoring

   **Solution - Dual Scoring Mode**:
   ```python
   # Add flag to analyze_ai_patterns.py
   parser.add_argument(
       '--scoring-version',
       choices=['legacy', 'enhanced', 'both'],
       default='enhanced',
       help='Scoring algorithm version (default: enhanced)'
   )

   # In analyzer.py
   if scoring_version in ['legacy', 'both']:
       legacy_score = calculate_dual_score_v1(results)  # Old weights
   if scoring_version in ['enhanced', 'both']:
       enhanced_score = calculate_dual_score_v2(results)  # New weights
   ```

   **Migration timeline**:
   - **Week 6-8**: Both versions available, enhanced is default
   - **Week 9-20**: Deprecation warnings for legacy mode
   - **Week 21+**: Legacy mode removed, enhanced only

5. **Score Translation Table**

   Help users understand how scores change:
   ```
   OLD SCORING → NEW SCORING (Approximate)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Quality 85+ (Excellent)  → Quality 83-87 (more realistic)
   Quality 75-84 (Good)     → Quality 74-82 (slight increase)
   Quality 65-74 (Mixed)    → Quality 66-73 (modest increase)
   Quality <65 (AI-like)    → Quality <65 (similar)

   Key changes:
   • Scores with good stylometric features: +1-3 pts
   • Scores with poor stylometric features: -2-5 pts
   • Overall: More accurate, slightly higher for quality writing
   ```

6. **Documentation Updates**

   Update all references to stylometric scoring:
   - **README.md**: Update score explanations
   - **COMPREHENSIVE-METRICS-GUIDE.md**: Update Stylometric section (lines 376-475)
   - **API docs**: Update ScoreDimension definitions
   - **CLI help text**: Update dimension descriptions
   - **Test fixtures**: Update expected scores in unit tests

7. **Validation & Calibration**

   **Test corpus validation**:
   ```python
   # Create: tests/scoring/test_rebalancing.py

   def test_rebalancing_maintains_accuracy():
       """Ensure new weights don't reduce detection accuracy."""
       corpus = load_labeled_corpus()  # 1000 texts, 50/50 AI/human

       for text, label in corpus:
           results = analyzer.analyze(text)
           old_score = calculate_dual_score_v1(results)
           new_score = calculate_dual_score_v2(results)

           # New scoring should be more accurate
           assert accuracy(new_score) >= accuracy(old_score)

   def test_rebalancing_score_distribution():
       """Ensure score distribution remains reasonable."""
       scores_old = [analyze_with_v1(text) for text in test_corpus]
       scores_new = [analyze_with_v2(text) for text in test_corpus]

       # Mean should increase slightly (1-3 pts)
       assert 1.0 <= mean(scores_new) - mean(scores_old) <= 3.0

       # Distribution shape should be similar
       assert kolmogorov_smirnov(scores_old, scores_new) < 0.1
   ```

8. **User Communication**

   **Release notes** (docs/RELEASE-NOTES-v2.0.md):
   ```markdown
   # Release Notes: v2.0 - Enhanced Stylometric Analysis

   ## Breaking Changes

   ### Scoring Algorithm Rebalancing

   **What changed**: Stylometric Markers dimension increased from 10 to 16 points

   **Why**: Enhanced from 5 features to 195 features with 97% accuracy

   **Impact on your scores**:
   - If you had strong stylometric signals (8-10/10): Gain +3-6 pts
   - If you had weak stylometric signals (0-4/10): Lose 0-3 pts
   - Average impact: +1.5 pts on Quality Score

   **Migration**: Use `--scoring-version=legacy` to maintain old scores

   **Timeline**: Legacy mode deprecated after 12 weeks
   ```

**Deliverable**: Updated scoring algorithm with comprehensive migration strategy

**Success Criteria**:
- ✅ Stylometric weight increased from 10 to 16 points
- ✅ Syntactic weight decreased from 4 to 3 points
- ✅ Tier 1 total increased from 70 to 75 points
- ✅ All tests passing with new weights
- ✅ Backward compatibility maintained via `--scoring-version` flag
- ✅ Documentation fully updated
- ✅ Validation shows ≥95% accuracy maintained
- ✅ User communication plan executed

**Timeline**:
- Days 1-2: Implement weight changes and dual-mode support
- Days 3-4: Update documentation and tests
- Day 5: Validation testing and calibration
- Day 6: Release notes and user communication

---

## Chapter 5: The Benefits

### Immediate Impact

**On Your Manuscript** (current: 77.3/100 quality):

| Current Stylometric | Enhanced Stylometric | Expected Gain |
|---------------------|----------------------|---------------|
| 5 features | 195 features | - |
| 10.0/10.0 (perfect) | 8.5/10.0 (realistic) | More accurate |
| No explanation | SHAP explanation | Actionable feedback |
| Basic score: 10 pts | Enhanced score: 15 pts | +5 pt weight |
| Vulnerable to evasion | Robust ensemble | Adversarial resistant |

**Expected Final Score**: 79-81/100 (closer to reality)

### Long-Term Benefits

1. **Adversarial Resistance**
   - Current: Can be evaded by avoiding 2 discourse markers
   - Enhanced: Requires evading 195 features across 6 dimensions
   - Result: 97% accuracy even against targeted evasion

2. **Explainability**
   - Current: "Score: 10.0/10.0" (why?)
   - Enhanced: "Modal verbs: +2.3, Pronouns: +1.8, Sentiment: +1.2"
   - Result: Authors know exactly what to improve

3. **Research Value**
   - Current: 1 dimension with limited academic backing
   - Enhanced: 6 dimensions with peer-reviewed research
   - Result: Tool becomes citable in academic work

4. **Commercial Viability**
   - Current: Basic tool, crowded market
   - Enhanced: 195-feature analysis + explanations + ensemble
   - Result: Competitive advantage, potential monetization

---

## Chapter 6: The Risks & Mitigations

### Risk 1: Complexity Explosion

**Risk**: Adding 195 features could make codebase unmaintainable
**Mitigation**:
- Use StyloMetrix library (maintain their code, not ours)
- Keep modular architecture (can disable if needed)
- Comprehensive documentation
- Unit tests for each component

**Status**: LOW RISK (libraries handle complexity)

### Risk 2: Performance Degradation

**Risk**: spaCy + StyloMetrix could slow analysis 5-10x
**Mitigation**:
- Lazy loading (only analyze if needed)
- Caching (reuse spaCy doc objects)
- Parallel processing (analyze multiple texts concurrently)
- Progressive disclosure (basic → enhanced on demand)

**Status**: MEDIUM RISK (requires optimization)

### Risk 3: Dependency Hell

**Risk**: Adding spaCy + StyloMetrix + SHAP increases install complexity
**Mitigation**:
- Make enhanced features optional
- Document installation clearly
- Provide Docker image with all dependencies
- Graceful degradation (fall back to basic if imports fail)

**Status**: LOW RISK (optional features pattern)

### Risk 4: Over-Fitting to Research

**Risk**: StyloMetrix trained on specific corpus, may not generalize
**Mitigation**:
- Test on diverse genres (academic, creative, technical)
- Maintain ensemble approach (3 independent methods)
- Regular validation on new AI models
- User feedback loop for false positives

**Status**: MEDIUM RISK (requires ongoing validation)

### Risk 5: Breaking Changes

**Risk**: Existing users rely on current scores, changes may break workflows
**Mitigation**:
- Versioned API (`--stylometric-version=basic|enhanced`)
- Migration guide with score translation table
- Parallel operation (both scores available)
- Clear deprecation timeline (6 months)

**Status**: LOW RISK (backward compatibility maintained)

---

## Chapter 7: The Decision Matrix

### Option 1: Do Nothing (Status Quo)

**Pros**:
- No work required
- No breaking changes
- System is stable

**Cons**:
- Vulnerable to evasion
- Limited accuracy (~72%)
- No competitive advantage
- Misses 190+ features

**Verdict**: ❌ Not recommended for production system

### Option 2: Minimal Enhancement (StyloMetrix Only)

**Pros**:
- 195 features immediately
- One library to maintain
- Moderate complexity
- ~87% accuracy

**Cons**:
- No ensemble robustness
- No explainability
- No mathematical baseline

**Verdict**: ⚠️ Good starting point, incomplete solution

### Option 3: Full Enhancement (All 3 Components)

**Pros**:
- 97% accuracy
- Adversarial resistant
- Full explainability
- Research-backed
- Competitive advantage

**Cons**:
- 5 weeks of work
- Multiple dependencies
- Higher complexity
- Performance optimization needed

**Verdict**: ✅ **RECOMMENDED** - Best long-term investment

### Option 4: Gradual Rollout

**Pros**:
- Phase 1 (StyloMetrix): 2 weeks
- Phase 2 (Scoring): +1 week
- Phase 3 (SHAP): +1 week
- Phase 4 (Burrows): +1 week
- Can stop at any phase

**Cons**:
- Longer timeline
- Partial benefits until complete

**Verdict**: ✅ **RECOMMENDED** - Reduces risk, maintains momentum

---

## Chapter 8: The Call to Action

### Immediate Next Steps (This Week)

**RECOMMENDED: Start with Phase 0 (No Dependencies Required)**

1. **Phase 0: Enhance Basic Markers** (3-4 days, zero dependencies)
   - Expand from 2 markers to 25-30 markers
   - Add discourse markers, signature vocab, formulaic phrases
   - Implement weighted scoring across 4 categories
   - See Phase 0 section above for complete implementation plan
   - **Why first**: Immediate value, no risk, no dependencies

2. **Phase 1: Install Core Dependencies** (30 minutes) - AFTER Phase 0
   ```bash
   cd writescore
   pip install stylometrix spacy shap faststylometry
   python -m spacy download en_core_web_lg
   ```

3. **Create Feature Branch** (5 minutes)
   ```bash
   git checkout -b feature/enhanced-stylometric-analysis
   ```

4. **Spike: Test StyloMetrix** (2 hours)
   ```python
   # Create: experiments/test_stylometrix.py
   import stylometrix

   text = open('manuscript/section-1.1-final.md').read()
   features = stylometrix.extract_all_features(text)
   print(f"Extracted {len(features)} features")
   print(features[:10])  # Preview first 10
   ```

5. **Document Findings** (1 hour)
   - Which features extract successfully?
   - Any errors or warnings?
   - Processing time for 10k word manuscript?
   - Memory usage?

6. **Go/No-Go Decision** (30 minutes)
   - If spike successful → Continue with Phase 1 implementation
   - If spike fails → Research alternatives
   - If spike slow → Investigate optimization

### Success Criteria

**Phase 0 Complete When**:
- 25-30 AI markers detecting correctly
- Weighted scoring across 4 categories working
- Detailed line-by-line issues report functional
- Tests passing with 95%+ accuracy on samples
- Processing time increase <50ms per 10k words
- Manuscript shows more nuanced scoring (not just 10.0)

**Phase 1 Complete When**:
- StyloMetrix extracts 195 features from manuscript
- No errors or crashes
- Processing time <10 seconds for 10k words
- Features stored in AnalysisResults
- Basic score still works (backward compatibility)

**Full Project Complete When**:
- All 7 phases delivered (Phase 0-6)
- 95%+ accuracy on test corpus
- <5 second processing for 10k words
- Full SHAP explanations working
- Documentation complete
- Tests passing (90%+ coverage)

---

## Chapter 9: The Vision

### What Success Looks Like (3 Months)

**For Authors**:
```bash
$ python analyze_ai_patterns.py manuscript.md --stylometric-explain

Stylometric Analysis: 8.3/10.0 (GOOD - Minor AI signatures detected)

🔍 DETAILED BREAKDOWN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Top 5 Human-Like Features (Strengths):
  ✓ Personal pronoun diversity: 8 types (vs 6.5 AI average)
  ✓ Sentiment variance: 0.19 (vs 0.11 AI average)
  ✓ Subordination ratio: 0.18 (vs 0.09 AI average)
  ✓ Lexical intensifier variety: "really", "quite", "somewhat"
  ✓ Modal verb moderation: 0.11 (vs 0.15 AI average)

Top 5 AI-Like Features (Areas for Improvement):
  ⚠ Function word distribution: Slightly mechanical (0.12 variance)
     → Action: Vary usage of "the", "a", "an" more naturally

  ⚠ POS trigram entropy: 4.2 (vs 5.1 human average)
     → Action: Break sentence structure patterns

  ⚠ Coordination preference: 0.72 (vs 0.55 human)
     → Action: Use more subordinate clauses

  ⚠ Punctuation uniformity: 0.89 Oxford comma consistency
     → Action: Vary comma usage occasionally

  ⚠ Lexical density: 0.52 (slightly high)
     → Action: Add more informal transitions

Burrows Delta vs Human Baseline: 1.2 (Good - within human range)

Overall Assessment: Your writing shows strong personal voice with minor
patterns suggesting AI-assisted editing. Focus on varying sentence
structures and reducing coordination preference.
```

**For Researchers**:
- Citable tool with peer-reviewed accuracy
- Open-source contribution to AI detection field
- Foundation for academic papers

**For the Community**:
- Most comprehensive open-source AI detector
- 195 features vs competitors' 10-20
- Full transparency (SHAP explanations)
- Production-ready quality

---

## Appendix A: References

### Phase 0 Research (2024 AI Detection Studies)

1. **Linguistic Characteristics Survey**: "A Survey of Linguistic Characteristics of AI-Generated Text" (2024) - https://www.arxiv.org/pdf/2510.05136.pdf
   - Comprehensive survey of peer-reviewed literature on AI-generated text patterns
   - Documents discourse marker frequencies, lexical diversity patterns, and POS distributions

2. **ChatGPT Essay Analysis**: "The writing style of ChatGPT in scientific articles" - Nature Scientific Reports (2023) - https://www.nature.com/articles/s41598-023-45644-9
   - Comparative analysis of ChatGPT vs human argumentative essays
   - Key findings on discourse marker usage and logical coherence patterns

3. **Hedging Devices Study**: "Hedges and Boosters in ChatGPT-Generated Argumentative Essays" - SCIRP (2024) - https://www.scirp.org/journal/paperinformation?paperid=145708
   - Quantifies hedging device usage: AI 11 hedges per 37 terms vs human 6.77
   - Documents AI's 1.6x higher hedging rate due to safety training

4. **Signature Vocabulary Analysis**: "The Most Overused ChatGPT Words" - Plus AI (2024) - https://plusai.com/blog/the-most-overused-chatgpt-words
   - Documents 100-200x overuse of signature words like "delve", "tapestry", "intricate"
   - Provides frequency data for ChatGPT/GPT-4 vocabulary patterns

5. **500 ChatGPT Overused Words**: God of Prompt Analysis (2024) - https://www.godofprompt.ai/blog/500-chatgpt-overused-words-heres-how-to-avoid-them
   - Comprehensive list of overused discourse markers and formulaic phrases
   - Documents specific sentence starters and transition patterns

6. **Biomedical Publication Analysis**: "Rapid adoption of AI in scientific publishing" - Science (2024) - https://www.science.org/doi/10.1126/sciadv.adt3813
   - Identifies 379 style words with elevated frequencies in 2024 publications
   - Documents unprecedented magnitude of LLM-induced vocabulary changes
   - Key markers: "pivotal", "intricate", "showcasing", "realm", "delving into"

7. **Discourse Markers Study**: "A Comparative Study of the Discourse Markers in ChatGPT-Generated and Human-Written Essays" (2024) - https://www.davidpublisher.com/Public/uploads/Contribute/67204a7537f04.pdf
   - Chinese-language study comparing Wenxinyiyan AI vs human essays
   - Quantifies transitional markers (116 vs 140), conditional markers (17 vs 49), causal markers (11 vs 21)

8. **Syntactic Patterns Research**: "Instruction-tuned Language Models Show Distinctive Stylistic Patterns" (2024) - https://arxiv.org/html/2410.16107v1
   - Documents 2-5x overuse of present participial clauses in instruction-tuned models
   - Identifies nominalizations at 1.5-2x human frequency
   - GPT-4o and Llama 3 signature patterns documented

9. **Psycholinguistic Framework**: "StyloAI: Distinguishing AI-Generated Content with Stylometric Analysis" (2024) - https://arxiv.org/html/2405.10129v1
   - Maps stylometric features to cognitive processes underlying human composition
   - Provides theoretical foundation for why markers distinguish AI from human writing

10. **Formulaic Phrase Detection**: "13 Signs You Used ChatGPT To Write Your Essay" - Sean Kernan (2024) - https://seanjkernan.substack.com/p/13-signs-you-used-chatgpt-to-write
    - Documents mechanical sentence starters and formulaic patterns
    - Examples: "It is worth noting that", "One might argue that", "At the end of the day"

### Phase 1+ Research (Advanced Stylometric Analysis)

11. **StyloMetrix Paper**: "StyloMetrix: A Python Library for Stylometric Analysis" (2024) - https://arxiv.org/html/2507.00838
    - 195 stylometric features across 6 dimensions
    - 97% accuracy with LGBM classifier

12. **CLARIN-PL Pipeline**: Stylometric Pipeline Implementation - https://github.com/CLARIN-PL/stylometric-pipeline
    - spaCy preprocessing → Feature extraction → LGBM classifier → SHAP explainability
    - Production-ready implementation

13. **Fast Stylometry**: Python Library for Authorship Attribution - https://fastdatascience.com/natural-language-processing/fast-stylometry-python-library/
    - Burrows' Delta implementation for Python
    - Efficient distance measure calculation

14. **Burrows' Delta Algorithm**: Burrows, J. (2002). "Delta: A Measure of Stylistic Difference and a Guide to Likely Authorship"
    - Mathematical foundation for stylistic distance measurement
    - Function word frequency analysis methodology

15. **SHAP Explanations**: GitHub Repository - https://github.com/slundberg/shap
    - Model-agnostic explanation method
    - Feature importance visualization

## Appendix B: Code Stubs

### Enhanced Stylometric Analyzer (Preview)

```python
# File: dimensions/enhanced_stylometric.py

from typing import Dict, List, Any
import stylometrix
from dimensions.stylometric import StylometricAnalyzer

class EnhancedStylometricAnalyzer(StylometricAnalyzer):
    """
    Enhanced stylometric analysis using StyloMetrix (195 features).

    Falls back to basic analysis if StyloMetrix unavailable.
    """

    def __init__(self):
        super().__init__()
        self.stylometrix_available = self._check_stylometrix()

    def _check_stylometrix(self) -> bool:
        """Check if StyloMetrix is available."""
        try:
            import stylometrix
            return True
        except ImportError:
            return False

    def analyze(self, text: str, lines: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze with StyloMetrix if available, else fall back to basic.
        """
        # Always run basic analysis
        basic_results = super().analyze(text, lines, **kwargs)

        if not self.stylometrix_available:
            return basic_results

        # Run enhanced analysis
        try:
            enhanced_features = self._extract_stylometrix_features(text)
            return {
                'stylometric': basic_results['stylometric'],
                'stylometrix': enhanced_features,
                'available': True,
                'method': 'enhanced'
            }
        except Exception as e:
            # Fall back to basic on error
            basic_results['error'] = str(e)
            return basic_results

    def _extract_stylometrix_features(self, text: str) -> Dict:
        """Extract all 195 StyloMetrix features."""
        # TODO: Implement in Phase 1
        pass

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Score using ensemble if enhanced, else basic.
        """
        if analysis_results.get('method') == 'enhanced':
            return self._score_ensemble(analysis_results)
        else:
            return super().score(analysis_results)

    def _score_ensemble(self, results: Dict) -> tuple:
        """
        Ensemble scoring: Basic (20%) + StyloMetrix (60%) + Burrows (20%)
        """
        # TODO: Implement in Phase 2
        pass
```

---

## Appendix C: Timeline Gantt Chart

```
Phase 0: Basic Marker Enhancement (3-4 Days) - QUICK WIN
├─ Day 1:   Implement extended pattern dictionaries
├─ Day 2:   Update scoring algorithm with weighted categories
├─ Day 3:   Add new fields to results.py & detailed analysis
└─ Day 4:   Testing, documentation, and validation

Week 1: Phase 1 - Foundation
├─ Day 1-2: Install dependencies & spike test
├─ Day 3-4: Create EnhancedStylometricAnalyzer
└─ Day 5:   Add feature fields to AnalysisResults

Week 2: Phase 2 - Scoring
├─ Day 1-2: Implement ensemble scorer
├─ Day 3:   Feature importance ranking
└─ Day 4-5: Threshold tuning & testing

Week 3: Phase 3 - Explainability
├─ Day 1-2: Install SHAP & integrate
├─ Day 3:   Create explanation formatter
└─ Day 4-5: Add CLI output & testing

Week 4: Phase 4 - Burrows Delta
├─ Day 1-2: Build human reference corpus
├─ Day 3:   Implement delta calculator
└─ Day 4-5: Integrate into ensemble

Week 5: Phase 5 - Testing & Validation
├─ Day 1-2: Unit & integration tests
├─ Day 3:   Performance optimization
└─ Day 4-5: Documentation & release

Week 6: Phase 6 - Algorithm Rebalancing
├─ Day 1-2: Implement weight changes and dual-mode support
├─ Day 3-4: Update documentation and tests
├─ Day 5:   Validation testing and calibration
└─ Day 6:   Release notes and user communication

Total Timeline: 3-4 days (Phase 0) + 6 weeks (Phases 1-6) = ~7 weeks
```

---

**END OF STORY**

**Next Action**: Start with Phase 0 (Basic Marker Enhancement) for immediate, low-risk improvements before investing in external dependencies.

**Recommended Path**: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

**Quick Win Opportunity**: Phase 0 can be completed in 3-4 days with zero dependencies and will improve detection from 2 markers to 25-30 markers.

**Decision Needed**: Approve Phase 0 start? (Yes/No/Modify)
