# AI Pattern Analyzer - Comprehensive Codebase Report

## Executive Summary

The AI Pattern Analyzer is a modular, registry-based system for detecting AI-generated text through 12 linguistic/stylometric dimensions. Version 5.0.0 removed deprecated dimensions (`advanced` and `stylometric`), completing a refactoring from v4.x. The system uses a DimensionStrategy pattern with self-registering dimensions, enabling zero-modification architecture for adding new patterns.

**Current Status**: 12 active dimensions across 4 tiers, ~7,770 lines of production code in dimensions alone

---

## SECTION 1: CURRENT DIMENSION INVENTORY (12 DIMENSIONS)

### Complete Dimension Breakdown

| Rank | Dimension | Weight | Tier | Lines | Key Features |
|------|-----------|--------|------|-------|--------------|
| 1 | **predictability** | 20.0% | ADVANCED | 616 | GLTR token analysis, 95% accuracy |
| 2 | **sentiment** | 17.0% | SUPPORTING | 363 | Emotional variation detection |
| 3 | **advanced_lexical** | 14.0% | ADVANCED | 485 | HDD, Yule's K, MATTR, RTTR, Maas |
| 4 | **perplexity** | 11.0% | CORE | 430 | AI vocabulary (27+ terms), formulaic transitions |
| 5 | **readability** | 10.0% | CORE | 322 | Flesch, Gunning Fog, ARI, syllable patterns |
| 6 | **transition_marker** | 10.0% | ADVANCED | 376 | "However"/"Moreover" overuse detection |
| 7 | **burstiness** | 6.0% | CORE | 516 | Sentence/paragraph length variation |
| 8 | **voice** | 5.0% | CORE | 385 | First-person, contractions, domain expertise |
| 9 | **structure** | 4.0% | CORE | 1640 | Heading depth, parallelism, list nesting |
| 10 | **formatting** | 4.0% | CORE | 763 | Em-dash (95% accuracy), bold/italic overuse |
| 11 | **lexical** | 3.0% | SUPPORTING | 361 | Type-Token Ratio, vocabulary richness |
| 12 | **syntactic** | 2.0% | ADVANCED | 525 | Dependency trees, subordination, POS diversity |

**Total Weight Sum**: 106.0% (weighted average calculation used in scoring)
**Total Production Code**: ~7,770 lines (dimensions only)

---

## SECTION 2: DETAILED DIMENSION ANALYSIS

### TIER 1: ADVANCED (51.0% weight - highest precision ML/GLTR-based)

#### 1. **Predictability Dimension** (20.0% weight)
- **What it analyzes**:
  - GLTR (Giant Language Model Test Room) token probability ranking
  - Token rank distribution: Top-10, Top-100, top-1000 percentages
  - High-predictability text segments (chunks with >70% top-10 tokens)
  - Model-based unpredictability metrics

- **Feature count**: ~4-5 metrics per analysis
- **Detection accuracy**: 95% (cited from GLTR research)
- **Key threshold**: AI signature when >70% tokens in top-10
- **Performance**:
  - First run: 2-10s (model loading)
  - Cached: 0.1-0.5s
  - Timeout: 120 seconds (prevents hanging)
  - Thread-safe with double-checked locking pattern

#### 2. **Advanced Lexical Dimension** (14.0% weight)
- **What it analyzes**:
  - HDD (Hypergeometric Distribution D) - most robust diversity metric
  - Yule's K - vocabulary richness via frequency distribution
  - MATTR (Moving Average Type-Token Ratio) - window-based diversity
  - RTTR (Root Type-Token Ratio) - length-independent measure
  - Maas - length-corrected TTR variant

- **Feature count**: 5 sophisticated lexical metrics
- **Dependencies**: scipy, textacy, spacy NLP
- **Accuracy boost**: +8% improvement over basic TTR/MTLD
- **Detection**: Low lexical diversity (HDD <0.7, Yule's K >50)

#### 3. **Transition Marker Dimension** (10.0% weight)
- **What it analyzes**:
  - "However" overuse: Human 0-3/1k, AI 5-10+/1k
  - "Moreover" overuse: Human 0-1/1k, AI 3-8+/1k
  - Marker clustering (multiple in proximity)
  - Formulaic phrase detection

- **Feature count**: ~3-4 transition metrics
- **Key signals**: Formal transition marker density
- **Reliability**: Highly specific AI signature

#### 4. **Syntactic Dimension** (2.0% weight)
- **What it analyzes**:
  - Dependency tree depth: AI 2-3 levels, Human 4-6 levels
  - Subordination index: AI <0.1, Human >0.15
  - Passive voice constructions
  - POS (Part-of-Speech) diversity patterns
  - Syntactic repetition detection

- **Feature count**: ~5 syntactic metrics
- **Dependencies**: spacy NLP with en_core_web_sm model
- **Accuracy improvement**: +10% vs. non-syntactic baselines
- **Detection**: Mechanical sentence structure, shallow trees

---

### TIER 2: CORE (35.0% weight - proven signatures >85% accuracy)

#### 5. **Perplexity Dimension** (11.0% weight)
- **What it analyzes**:
  - AI vocabulary (27+ terms identified in patterns):
    - Tier 1: delve, robust, leverage, harness, underscore, facilitate, pivotal, holistic
    - Tier 2: seamless, comprehensive, optimize, streamline, paramount, quintessential, myriad, plethora
    - Tier 3: innovative, cutting-edge, revolutionary, game-changing, transformative
    - Idioms: "dive deep", "deep dive", "paradigm shift", "ecosystem", "landscape"
  - Formulaic transitions (18 patterns): Furthermore, Moreover, Additionally, etc.

- **Feature count**: 27+ vocabulary terms + 18 transition phrases
- **Per-document metrics**: Vocabulary density/1k words, transition clustering
- **Detection baseline**: >10 per 1k words = strong AI marker
- **Strength**: Most intuitive signal for readers

#### 6. **Readability Dimension** (10.0% weight) [SPLIT FROM STYLOMETRIC v4.x]
- **What it analyzes**:
  - Flesch Reading Ease (primary scoring metric)
  - Flesch-Kincaid Grade Level
  - Automated Readability Index (ARI)
  - Average word length
  - Average sentence length
  - Syllable distribution patterns

- **Feature count**: 5-6 readability metrics
- **Dependencies**: textstat, nltk
- **AI signature**: Extreme values (<30 or >90 = mechanical)
- **Common AI range**: 60-70 Flesch (neutral, not diagnostic alone)

#### 7. **Burstiness Dimension** (6.0% weight)
- **What it analyzes**:
  - Sentence length variation (standard deviation)
  - Paragraph length uniformity detection
  - Short sentence ratio (<15 words)
  - Long sentence ratio (>30 words)
  - Length distribution variance

- **Feature count**: 4-5 burstiness metrics
- **Threshold**: Stdev < 3.0 = AI signature, >10.0 = human-like
- **Basis**: GPTZero research methodology
- **Signal strength**: Core AI detection metric

#### 8. **Voice Dimension** (5.0% weight)
- **What it analyzes**:
  - First-person pronouns (I, me, my, we, us, our)
  - Direct address (you, your, yours)
  - Contractions (can't, don't, it's, won't, etc.)
  - Technical domain expertise (via domain_terms regex)
  - Personal authenticity markers

- **Feature count**: 4 voice metrics
- **Customizable**: domain_terms list (default: cybersecurity terms)
- **Detection**: AI avoids personal voice and contractions
- **Strength**: High human authenticity when present

#### 9. **Formatting Dimension** (4.0% weight) [SPLIT FROM STYLOMETRIC v4.x]
- **What it analyzes**:
  - Em-dash frequency and clustering: ChatGPT 10x more than humans
  - Bold/italic overuse: AI 10-50/1k, human 1-5/1k
  - Quotation patterns
  - Formatting mechanical consistency (0.7+ = AI-like)
  - Distribution across document

- **Feature count**: 4-5 formatting metrics
- **Detection accuracy**: 95% (em-dash strongest single signal)
- **Research basis**: ChatGPT formatting analysis
- **Thresholds**: >3 em-dashes/page = medium concern, >2 = acceptable

#### 10. **Structure Dimension** (4.0% weight) - LARGEST FILE (1640 lines)
- **What it analyzes**:
  - Heading depth analysis (max depth, variance)
  - Heading parallelism detection (mechanical similarity >0.7)
  - Heading verbosity (>30% verbose headings)
  - Section length uniformity (variance detection)
  - List nesting depth and symmetry
  - Uniform cluster detection (suspicious regularity)
  - Domain-aware thresholds (technical vs. narrative)

- **Feature count**: 8-10 structural metrics
- **Dependencies**: marko markdown parser, domain_thresholds module
- **Complexity**: AST-based analysis with heading phrase matching
- **Detection**: Perfect parallelism, excessive depth = AI signatures
- **Domain adaptation**: Different thresholds for tech/narrative documents

---

### TIER 3: SUPPORTING (20.0% weight - contextual quality indicators)

#### 11. **Sentiment Dimension** (17.0% weight)
- **What it analyzes**:
  - Sentiment variation across text chunks (variance metric)
  - Emotional flatness detection: AI variance <0.10, human >0.15
  - Average sentiment intensity
  - Sentiment distribution patterns
  - Monotonous emotional tone detection

- **Feature count**: 3-4 sentiment metrics
- **Model**: DistilBERT-base finetuned on SST-2 (lazy-loaded)
- **Dependencies**: transformers, torch (CPU mode)
- **Signal strength**: Low emotional variation = AI signature
- **Performance**: Lazy-loaded, ~50-100ms per chunk

#### 12. **Lexical Dimension** (3.0% weight)
- **What it analyzes**:
  - Type-Token Ratio (TTR) - basic vocabulary richness
  - Word frequency distribution
  - Stemmed diversity (catches word variants)
  - Vocabulary richness patterns

- **Feature count**: 2-3 lexical metrics
- **Dependencies**: nltk Porter Stemmer
- **Detection**: Repetitive vocabulary (low TTR) = AI signature
- **Relationship**: Basic version of advanced_lexical dimension
- **Note**: advanced_lexical provides HDD, MATTR alternatives

---

## SECTION 3: ARCHITECTURAL UNDERSTANDING

### 3.1: Dimension Strategy Pattern

All dimensions implement `DimensionStrategy` base class with required contract:

```python
class DimensionStrategy(ABC):
    @property
    def dimension_name(self) -> str: ...      # Unique identifier

    @property
    def weight(self) -> float: ...            # 0-100% contribution

    @property
    def tier(self) -> str: ...                # ADVANCED|CORE|SUPPORTING|STRUCTURAL

    @property
    def description(self) -> str: ...         # Human-readable purpose

    def analyze(
        self,
        text: str,
        lines: List[str],
        config: AnalysisConfig
    ) -> Dict[str, Any]: ...                  # Return metrics dict

    def calculate_score(
        self,
        metrics: Dict[str, Any]
    ) -> float: ...                           # Return 0-100 score

    def analyze_detailed(
        self,
        lines: List[str],
        html_comment_checker
    ) -> List[Issue]: ...                     # Optional: detailed findings
```

### 3.2: Self-Registering Architecture

Each dimension self-registers on instantiation:

```python
class MyDimension(DimensionStrategy):
    def __init__(self):
        super().__init__()
        DimensionRegistry.register(self)  # Self-register
```

**Benefits**:
- Zero modifications to core analyzer when adding dimensions
- No configuration file needed
- Python module system handles discovery
- Thread-safe with internal locking
- Allows dimension hot-loading in future

### 3.3: Registry System

`DimensionRegistry` provides class-based dimension management:

```python
DimensionRegistry.register(dimension)      # Register (idempotent)
DimensionRegistry.get('perplexity')        # Get by name
DimensionRegistry.get_all()                # Get all dimensions
DimensionRegistry.get_by_tier('CORE')      # Filter by tier
DimensionRegistry.clear()                  # Testing support
```

**Thread Safety**: All operations protected by `threading.Lock()`

### 3.4: Configuration-Driven Loading

`AnalysisConfig` + `DimensionLoader` enable selective dimension loading:

```python
class AnalysisConfig:
    dimension_profile: str                  # "fast"|"balanced"|"full"
    analysis_mode: AnalysisMode             # FAST|ADAPTIVE|SAMPLING|FULL
    explicit_dimensions: List[str]          # Override profile
    custom_profiles: Dict[str, List[str]]  # User-defined profiles
```

**Profiles**:
- **fast** (4 dims): Perplexity, Burstiness, Structure, Formatting
- **balanced** (8 dims): + Voice, Lexical, Readability, Sentiment
- **full** (12 dims): All dimensions

### 3.5: Scoring System

Dual-score approach via `DualScoreCalculator`:

```python
DualScore(
    risk_score: float,          # 0-100, lower is better (AI-like)
    quality_score: float,       # 0-100, higher is better (human-like)
    category: ScoreCategory,    # EXCELLENT|GOOD|NEEDS_WORK|POOR
    improvement_actions: List[ImprovementAction]
)
```

**Score Mapping** (v5.0.0 positive labels):
- EXCELLENT: 85-100 (minimal AI patterns)
- GOOD: 70-84 (some patterns, mostly human)
- NEEDS WORK: 50-69 (noticeable patterns)
- POOR: 0-49 (strong AI patterns)

---

## SECTION 4: FEATURE COVERAGE ANALYSIS

### 4.1: Currently Covered Linguistic/Stylometric Features

#### Lexical/Vocabulary Features
- [x] AI vocabulary detection (27+ terms, 3 tiers)
- [x] Formulaic transition phrases (18 patterns)
- [x] Type-Token Ratio (basic)
- [x] HDD, Yule's K, MATTR, RTTR, Maas (advanced)
- [x] Word frequency distribution
- [x] Vocabulary richness patterns
- [x] Domain-specific technical terms (customizable)

#### Syntactic/Grammar Features
- [x] Dependency tree depth analysis (spacy)
- [x] Subordination index calculation
- [x] Passive voice constructions
- [x] Part-of-Speech (POS) diversity
- [x] Syntactic repetition patterns

#### Readability Features
- [x] Flesch Reading Ease score
- [x] Flesch-Kincaid Grade Level
- [x] Automated Readability Index (ARI)
- [x] Average sentence length
- [x] Average word length
- [x] Syllable patterns

#### Stylistic Features
- [x] Sentence length variation (burstiness)
- [x] Paragraph length uniformity
- [x] Em-dash overuse (95% accuracy)
- [x] Bold/italic overuse (ChatGPT pattern)
- [x] Quotation patterns
- [x] Heading depth and parallelism
- [x] Section length variance
- [x] List nesting patterns

#### Semantic/Pragmatic Features
- [x] First-person pronouns (voice authenticity)
- [x] Direct address pronouns (you, your)
- [x] Contractions (conversational markers)
- [x] Sentiment variation across text
- [x] Emotional flatness detection
- [x] Transition marker overuse (however, moreover)
- [x] Formulaic phrase clustering

#### ML/Model-Based Features
- [x] GLTR token predictability (95% accuracy)
- [x] Token rank distribution (top-10, top-100, top-1000)
- [x] Sentiment analysis (DistilBERT-SST-2)

### 4.2: Feature Count Summary

| Feature Category | Count | Covered | Examples |
|-----------------|-------|---------|----------|
| Vocabulary patterns | 27+ | 100% | delve, robust, leverage, ecosystem, paradigm shift |
| Formulaic transitions | 18 | 100% | Furthermore, Moreover, Additionally, In conclusion |
| Readability metrics | 5-6 | 100% | Flesch, Gunning Fog, ARI, word/sentence length |
| Syntactic metrics | 5 | 100% | Tree depth, subordination, passive voice, POS diversity |
| Lexical diversity metrics | 8 | 100% | TTR, HDD, Yule's K, MATTR, RTTR, Maas, stemmed diversity |
| Formatting patterns | 4-5 | 100% | Em-dash, bold, italic, quotations, mechanical consistency |
| Structural patterns | 8-10 | 100% | Headings, sections, lists, nesting, parallelism, uniformity |
| Voice/authenticity | 4 | 100% | First-person, direct address, contractions, domain terms |
| Semantic patterns | 5 | 100% | Sentiment variance, emotional flatness, marker clustering |
| ML-based metrics | 3-4 | 100% | GLTR (4 metrics), DistilBERT sentiment |
| **TOTAL** | **~70+** | **100%** | Comprehensive stylometric coverage |

---

## SECTION 5: WHAT'S NOT CURRENTLY ANALYZED (COVERAGE GAPS)

### 5.1: Linguistic Features NOT Covered

#### Phonetic/Morphological
- [ ] Phoneme patterns
- [ ] Alliteration and assonance detection
- [ ] Morphological complexity beyond POS
- [ ] Lemma diversity (distinct word roots)

#### Advanced Semantic
- [ ] Named Entity Recognition (NER) patterns
- [ ] Coreference resolution patterns
- [ ] Semantic coherence metrics
- [ ] Topic consistency across paragraphs
- [ ] Discourse markers (beyond transitions)

#### Pragmatic Features
- [ ] Speech act analysis
- [ ] Politeness/formality levels
- [ ] Sarcasm/irony detection
- [ ] Figurative language (metaphor, simile)
- [ ] Rhetorical structure analysis

#### Contextual/Domain Features
- [ ] Citation patterns (academic documents)
- [ ] Code block analysis (technical docs)
- [ ] Mathematical notation patterns
- [ ] URL/link distribution
- [ ] Table/data structure patterns

#### Cross-Paragraph Features
- [ ] Coherence metrics between sentences
- [ ] Theme consistency across sections
- [ ] Topical diversity
- [ ] Argument structure analysis
- [ ] Anaphora/epistrophe patterns

#### Discourse-Level
- [ ] Document-level topical flow
- [ ] Paragraph role classification (intro, body, conclusion)
- [ ] Question-answer patterns
- [ ] Narrative structure
- [ ] Information density per section

#### Model Ensemble
- [ ] Multiple LLM comparisons (GPT-3.5, GPT-4, Claude, Gemini)
- [ ] Ensemble scoring from multiple models
- [ ] Model-specific fingerprints
- [ ] Fine-tuned model detection

### 5.2: Temporal/Statistical
- [ ] Time-series sentiment tracking
- [ ] Vocabulary evolution through document
- [ ] Writing pattern consistency
- [ ] Statistical significance testing
- [ ] Bayesian probability scoring

### 5.3: Language-Specific
- [ ] Multi-language support (currently English-focused)
- [ ] Language-specific readability metrics
- [ ] Non-English syntactic patterns
- [ ] Character n-gram analysis

### 5.4: Document-Specific
- [ ] Metadata extraction (author, date, source)
- [ ] Document type classification
- [ ] Genre-specific baselines
- [ ] Watermark detection (text steganography)
- [ ] Style transfer detection

---

## SECTION 6: PERFORMANCE CHARACTERISTICS

### 6.1: Bottlenecks

| Component | Bottleneck | Impact | Mitigation |
|-----------|-----------|--------|-----------|
| **Predictability** | Model loading (2-10s first run) | 120s timeout enforced | Lazy-load with cache, thread-safe |
| **Sentiment** | DistilBERT inference per chunk | 50-100ms per chunk | Lazy-load, batch processing available |
| **Advanced Lexical** | scipy.hypergeom calculations | O(vocab_size) operations | Textacy/spacy optimized |
| **Syntactic** | spacy NLP pipeline | ~100-500ms full pipeline | Already optimized, single pass |
| **Structure** | AST parsing via marko | ~50-100ms | Cached parse, reused AST |

### 6.2: Performance by Mode

| Mode | Typical Time | Coverage | Best For |
|------|-------------|----------|----------|
| **FAST** | 2-5 seconds | ~2000 chars/dimension | Quick feedback |
| **ADAPTIVE** | 5-15 seconds | Size-scaled sampling | Default, recommended |
| **SAMPLING** | 10-30 seconds | User-defined coverage | Large documents |
| **FULL** | 30-120+ seconds | 100% document | Final review |

### 6.3: Model Caching

**Predictability (GLTR)**:
- First analysis: 2-10 seconds (DistilGPT-2 load)
- Cached runs: 0.1-0.5 seconds
- Cache location: Module-level global with thread-safe lock
- Clear method: `PredictabilityDimension.clear_model_cache()`

**Sentiment**:
- First analysis: 2-5 seconds (DistilBERT load)
- Cached runs: 50-100ms per chunk
- Lazy-loaded on first use
- Module-level global `_sentiment_pipeline`

### 6.4: Threading Safety

- **Predictability**: Double-checked locking pattern (`_model_lock`)
- **Sentiment**: Global lazy-loaded, safe for concurrent reads
- **DimensionRegistry**: All operations protected by `threading.Lock()`
- **Overall**: Thread-safe for concurrent document analysis

### 6.5: Memory Usage

| Component | Memory Usage | Note |
|-----------|-------------|------|
| DistilGPT-2 (GLTR) | ~350-500 MB | Loaded once, shared across instances |
| DistilBERT (sentiment) | ~250-350 MB | Loaded once, shared across instances |
| spacy en_core_web_sm | ~40-50 MB | Pre-loaded for syntactic analysis |
| NLTK data | ~50-100 MB | Tokenizers, stemmers |
| MarKo parser | <10 MB | AST parser instance |
| **Total** | ~700-1000 MB | Typical for full profile |
| **Fast Profile** | ~100-150 MB | Excludes GLTR, sentiment, advanced lexical |

---

## SECTION 7: RECENT CHANGES (v5.0.0 vs v4.x)

### 7.1: What Was Removed (Story 2.0)

#### Deprecated Dimensions (v4.x → Removed v5.0.0)

1. **AdvancedDimension** (655 lines removed)
   - Split in v4.x Story 1.4.5 into:
     - `PredictabilityDimension` (GLTR analysis)
     - `AdvancedLexicalDimension` (HDD, Yule's K, MATTR)
   - Complete removal in v5.0.0 (no backward compatibility)

2. **StylometricDimension** (378 lines removed)
   - Split in v4.x Story 1.4.5 into:
     - `ReadabilityDimension` (Flesch, Gunning Fog, etc.)
     - `TransitionMarkerDimension` (however, moreover patterns)
   - Complete removal in v5.0.0

#### Backward Compatibility Code Removed

- `StylometricIssue` dataclass (replaced by `TransitionInstance`)
  - Field changes: `marker_type` → `transition`, `suggestion` → `suggestions` (list)
- `gltr_score` property (use `predictability_score` directly)
- `stylometric_score` field (use `readability_score` + `transition_marker_score`)
- `stylometric_issues` field (use `transition_instances`)
- CLI output section for stylometric markers (48 lines)

### 7.2: Breaking Changes

| Change | v4.x | v5.0.0 | Migration |
|--------|------|--------|-----------|
| Dimension count | 14 | 12 | Update assertions, dimension_count field |
| `advanced` dimension | Exists | `None` | Split to `predictability` + `advanced_lexical` |
| `stylometric` dimension | Exists | `None` | Split to `readability` + `transition_marker` |
| `gltr_score` property | Works | AttributeError | Use `predictability_score` field |
| `stylometric_score` field | Works | AttributeError | Use `readability_score` + `transition_marker_score` |
| Label system | HIGH/MEDIUM/LOW/VERY LOW | EXCELLENT/GOOD/NEEDS WORK/POOR | Intuitive positive labels |
| `StylometricIssue` import | Works | ImportError | Use `TransitionInstance` |
| Test files | 4 removed | - | `test_advanced.py`, `test_stylometric.py` |

### 7.3: Positive Label System (NEW in v5.0.0)

Replaced confusing impact-style labels with intuitive quality labels:

```
OLD (v4.x)             NEW (v5.0.0)
HIGH (0-24)      →     EXCELLENT (85-100)   ✓ Human-like
MEDIUM (25-49)   →     GOOD (70-84)         ✓ Mostly human
LOW (50-74)      →     NEEDS WORK (50-69)   ⚠ Some AI patterns
VERY LOW (75+)   →     POOR (0-49)          ✗ Strong AI patterns
```

**Rationale**: Old system was backwards (LOW sounded bad but meant low problems).
New system is intuitive: higher scores = better human-like writing.

### 7.4: Total Changes

- **Lines removed**: 1,033 (deprecated code + tests)
- **Tests deleted**: 6 (test_advanced.py, test_stylometric.py, 4 analyzer tests)
- **New validation**: `validate_no_deprecated()` method in DimensionRegistry
- **Backward compatibility**: 0% - This is a breaking change release

---

## SECTION 8: ARCHITECTURE COMPATIBILITY FOR ADDING NEW DIMENSIONS

### 8.1: Adding a New Dimension - Zero-Modification Pattern

To add a new dimension, follow this pattern (no core code changes required):

**Step 1**: Create new file `dimensions/my_dimension.py`:

```python
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.core.dimension_registry import DimensionRegistry
from typing import Dict, List, Any, Optional

class MyDimension(DimensionStrategy):
    def __init__(self):
        super().__init__()
        DimensionRegistry.register(self)  # Self-register

    @property
    def dimension_name(self) -> str:
        return "my_dimension"

    @property
    def weight(self) -> float:
        return 5.0  # 5% of total score

    @property
    def tier(self) -> str:
        return DimensionTier.SUPPORTING  # or CORE, ADVANCED

    @property
    def description(self) -> str:
        return "Analyzes my specific pattern"

    def analyze(
        self,
        text: str,
        lines: List[str],
        config: Optional[AnalysisConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # Perform analysis
        metrics = {
            'metric1': value1,
            'metric2': value2,
        }
        return metrics

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        # Return 0-100 score
        score = 100.0 - metrics['metric1']
        self._validate_score(score)
        return score

    def analyze_detailed(
        self,
        lines: List[str],
        html_comment_checker=None
    ) -> List[Any]:  # Return custom Issue dataclass
        # Optional: Return detailed findings
        issues = []
        return issues
```

**Step 2**: Import in `dimensions/__init__.py`:

```python
from writescore.dimensions.my_dimension import MyDimension

# Auto-register on import
_my_dimension = MyDimension()
```

**Step 3**: Analyzer automatically discovers it:

```python
analyzer = AIPatternAnalyzer()
my_dim = analyzer.dimensions.get('my_dimension')
results = analyzer.analyze(text)  # Automatically includes new dimension
```

### 8.2: Base Strategy Requirements

All dimensions must implement:

```python
class DimensionStrategy(ABC):
    # REQUIRED PROPERTIES
    @property
    @abstractmethod
    def dimension_name(self) -> str: pass

    @property
    @abstractmethod
    def weight(self) -> float: pass  # 0-100

    @property
    @abstractmethod
    def tier(self) -> str: pass  # ADVANCED|CORE|SUPPORTING|STRUCTURAL

    @property
    @abstractmethod
    def description(self) -> str: pass

    # REQUIRED METHODS
    @abstractmethod
    def analyze(
        self,
        text: str,
        lines: List[str],
        **kwargs
    ) -> Dict[str, Any]: pass

    @abstractmethod
    def calculate_score(
        self,
        metrics: Dict[str, Any]
    ) -> float: pass  # Must return 0-100 score
```

### 8.3: Available Helper Methods

Base class provides utilities:

```python
# Text preparation (handles mode-specific sampling)
prepared = self._prepare_text(text, config, self.dimension_name)

# Score validation (ensures 0-100 range)
self._validate_score(score)

# Threshold lookup (per dimension overrides from THRESHOLDS)
threshold = self._get_threshold('AI_VOCAB_LOW_THRESHOLD', dimension_name)

# Registry access
dim = DimensionRegistry.get('perplexity')
```

### 8.4: Optional Methods

Implement for enhanced CLI reporting:

```python
def analyze_detailed(
    self,
    lines: List[str],
    html_comment_checker=None
) -> List[CustomIssue]:
    """Return detailed findings (optional)."""
    # Return list of issues with:
    # - line_number
    # - context
    # - suggestions (list of strings)
    # - severity
```

### 8.5: Configuration Support

Dimensions receive `AnalysisConfig` with:

```python
class AnalysisConfig:
    dimension_profile: str          # "fast"|"balanced"|"full"
    analysis_mode: AnalysisMode     # FAST|ADAPTIVE|SAMPLING|FULL
    samples: int                    # Number of samples for SAMPLING mode
    sample_size: int                # Chars per sample
    sampling_strategy: str          # uniform|weighted|start|end
```

Dimensions can optimize based on mode:

```python
def analyze(self, text, lines, config=None, **kwargs):
    config = config or DEFAULT_CONFIG

    if config.analysis_mode == AnalysisMode.FAST:
        # Fast path: analyze first 2000 chars
        analyzed_text = self._prepare_text(text, config, self.dimension_name)
    elif config.analysis_mode == AnalysisMode.FULL:
        # Full path: analyze everything
        analyzed_text = text
```

---

## SECTION 9: STYLOMETRIC FEATURES SUMMARY FOR STYLOMETRX

### What StyloMetrix Should Know About Current Coverage

#### Already Handled (Don't Duplicate)
1. **Readability** (10% weight, CORE tier)
   - Flesch Reading Ease, Gunning Fog, ARI
   - StyloMetrix: Avoid duplicate readability scoring

2. **Lexical Diversity** (3% weight, dual coverage)
   - Basic: Type-Token Ratio (lexical.py)
   - Advanced: HDD, Yule's K, MATTR, RTTR, Maas (advanced_lexical.py)
   - StyloMetrix: Provide alternative metrics or deeper analysis

3. **Sentiment** (17% weight, SUPPORTING tier)
   - DistilBERT-based sentiment variation detection
   - StyloMetrix: Could enhance with aspect-based sentiment, emotion taxonomy

4. **Formatting** (4% weight, CORE tier)
   - Em-dash (95% accuracy), bold/italic, quotations
   - StyloMetrix: Could add ellipsis patterns, capitalization, line breaks

5. **Syntactic** (2% weight, ADVANCED tier)
   - spacy-based dependency trees, subordination, passive voice
   - StyloMetrix: Could add clause analysis, sentence type distribution

### Opportunities for StyloMetrix Differentiation

1. **Pragmatic Markers** (not currently covered)
   - Speech acts, hedging language, certainty markers
   - Authority claims vs. hedged statements

2. **Figurative Language** (not currently covered)
   - Metaphor detection, simile patterns, idiom usage
   - Could identify AI's tendency to avoid complex metaphors

3. **Author Fingerprinting** (not currently covered)
   - Unique stylistic quirks, writing habits
   - Biometric-style author signature matching

4. **Cross-Document Coherence** (not currently covered)
   - Consistency across multiple documents
   - Topic drift detection

5. **Language Model Ensemble** (not currently covered)
   - Compare multiple models (GPT-3.5, GPT-4, Claude, Gemini)
   - Model-specific fingerprints

6. **Linguistic Complexity Beyond Current**
   - Information density per section
   - Argument structure analysis
   - Rheme/theme progression patterns

### Integration Points

StyloMetrix should:
1. **Implement `DimensionStrategy`** for seamless integration
2. **Target low-weight positions** (avoid conflicting with high-weight predictability)
3. **Use lazy loading** for heavy models
4. **Thread-safe caching** if using model-based features
5. **Provide detailed findings** via `analyze_detailed()` method

---

## SECTION 10: SUMMARY TABLE

### Quick Reference

| Aspect | Details |
|--------|---------|
| **Total Dimensions** | 12 (removed 2 deprecated from v4.x) |
| **Total Feature Count** | ~70+ stylometric/linguistic features |
| **Largest Dimension** | Structure (1640 lines, 4% weight) |
| **Highest Weight** | Predictability (20%, GLTR-based) |
| **Architecture Pattern** | Self-registering DimensionStrategy |
| **Registry System** | Class-based, thread-safe |
| **Configuration** | Mode-driven (FAST/ADAPTIVE/SAMPLING/FULL) |
| **Performance** | 2-5s fast, 30-120s full analysis |
| **ML Models** | GLTR (DistilGPT-2), Sentiment (DistilBERT) |
| **Dependencies** | 9 core (marko, nltk, spacy, textstat, transformers, torch, scipy, textacy, click) |
| **Test Coverage** | 12+ integration tests, full regression suite |
| **Version** | 5.0.0 (breaking changes, no backward compat) |
| **Lines of Code** | ~7,770 lines (dimensions only) |

---

## SECTION 11: KEY INSIGHTS FOR STYLOMETRX DEVELOPMENT

### What This Codebase Does Well

1. **Modular Architecture**: Each dimension is completely independent, enabling easy addition
2. **Self-Registration**: Zero core modifications needed to add new dimensions
3. **Dual Scoring**: Provides both risk and quality perspectives
4. **Performance Tiers**: Three profiles (fast/balanced/full) for different use cases
5. **Type Safety**: Full type hints throughout codebase
6. **Evidence Extraction**: Detailed findings for each dimension (optional)
7. **Thread Safety**: All global state protected with locks
8. **Configuration Driven**: Dimension profiles and analysis modes

### What Could Be Improved (Opportunities for StyloMetrix)

1. **Coverage Gaps**:
   - No NLP-based semantic coherence
   - No cross-document consistency
   - No author fingerprinting
   - No pragmatic/figurative language analysis

2. **Model Diversity**:
   - Only compares single model (DistilGPT-2 for GLTR)
   - Could detect model-specific fingerprints

3. **Deep Semantic Analysis**:
   - Named entity patterns not analyzed
   - Topic modeling not included
   - Coreference resolution not detected

4. **Linguistic Depth**:
   - Advanced clause analysis missing
   - Argument structure not analyzed
   - Information density not calculated

### StyloMetrix Positioning

StyloMetrix should target **pragmatic/semantic layers** not covered:
- Figurative language patterns
- Speech act analysis
- Information density and distribution
- Author fingerprinting
- Multi-model comparative analysis

This would complement the existing **lexical/syntactic/readability** coverage without duplication.
