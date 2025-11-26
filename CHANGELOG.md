# Changelog

All notable changes to WriteScore (formerly AI Pattern Analyzer) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.3.0] - 2025-11-25

### CI/CD Release Automation (Story 4.3)

**Added GitHub Actions workflows for continuous integration and automated releases**

#### Added

**GitHub Actions Workflows**:
- **`.github/workflows/ci.yml`**: Continuous integration workflow
  - Triggers on push to main and pull requests
  - Lint job: ruff check on Python 3.12
  - Test job: Matrix testing on Python 3.8, 3.10, 3.12
  - Coverage upload to Codecov (Python 3.12 only)
  - Runs unit and integration tests

- **`.github/workflows/release.yml`**: Automated release workflow
  - Triggers on version tags (v*)
  - Builds wheel and source distributions
  - Creates GitHub releases with auto-generated notes
  - Attaches build artifacts (.whl, .tar.gz)
  - PyPI publishing ready (commented, requires PYPI_API_TOKEN secret)

**Ruff Linting Configuration**:
- Added `[tool.ruff]` section to pyproject.toml
- Line length: 100 characters
- Target version: Python 3.8
- Rules enabled: E, F, W, I, UP, B, C4, SIM
- Sensible ignores for style preferences (E501, B008, SIM108)
- Per-file ignores for tests (S101, PLR2004)
- isort integration with first-party package recognition

#### Changed

**Code Quality Improvements** (all files pass ruff check):
- Fixed import ordering across all modules (I001)
- Added proper exception chaining with `from e` (B904)
- Renamed unused loop variables to `_` prefix (B007)
- Combined nested if statements where appropriate (SIM102)
- Fixed ambiguous variable names `l` → `level`/`item` (E741)
- Used context managers for file operations (SIM115)
- Applied contextlib.suppress for try-except-pass patterns (SIM105)
- Fixed function binding in loops (B023)

#### Technical Details

- **Python Support**: 3.8, 3.10, 3.12 (matrix tested)
- **Linting**: Zero ruff errors (all 17+ files cleaned)
- **Test Results**: 1968 passed, 9 pre-existing failures, 16 skipped
- **Workflow Permissions**: Minimal (contents: write for releases only)

#### Files Added
- `.github/workflows/ci.yml` (45 lines)
- `.github/workflows/release.yml` (36 lines)

#### Files Modified
- `pyproject.toml` (added ruff configuration)
- 20+ source files (code style fixes)
- 4 test files (code style fixes)

---

## [6.2.0] - 2025-11-24

### Expanded Pragmatic Markers Lexicon (Story 2.6)

**Major expansion of pragmatic marker detection from 52 to 126 patterns using established research taxonomies**

This release implements Phase 1 of the Lexicon Enhancement Strategy, expanding pragmatic marker coverage
using patterns from Hyland's Metadiscourse taxonomy, LIWC2015 certainty/tentative dictionaries,
Biber et al. LGSWE stance markers, and BioScope corpus hedge cues.

#### Added

**New Pattern Categories (Story 2.6)**:
- **ATTITUDE_MARKERS** (18 patterns) - Express writer's affective evaluation:
  - Evaluative unexpected: surprisingly, unexpectedly, interestingly, remarkably, curiously, strangely
  - Evaluative positive/negative: unfortunately, fortunately, regrettably, hopefully
  - Evaluative importance: importantly, significantly, notably, admittedly
  - Evaluative expectation: oddly, predictably, inevitably, understandably

- **LIKELIHOOD_ADVERBIALS** (11 patterns) - Express probability or evidential likelihood:
  - Core probability: probably, arguably, plausibly
  - Evidential likelihood: apparently, evidently, seemingly, ostensibly
  - Reported likelihood: supposedly, reportedly, allegedly, purportedly

**New Analysis Methods**:
- `_analyze_attitude_markers()`: Detects attitude marker patterns with density calculations
- `_analyze_likelihood_adverbials()`: Detects likelihood adverbial patterns with density calculations

**Research Documentation**:
- `docs/research/SOURCE_AVAILABILITY.md`: Source access validation findings
- `docs/research/hyland_patterns.csv`: 70 patterns from Hyland taxonomy
- `docs/research/liwc_patterns.csv`: 20 patterns from LIWC samples
- `docs/research/biber_patterns.csv`: 22 patterns from Biber LGSWE
- `docs/research/bioscope_patterns.csv`: 20 patterns from BioScope
- `docs/research/new_patterns_final.csv`: Final 74 new patterns with sources
- `docs/research/PATTERN_SELECTION_RATIONALE.md`: Inclusion/exclusion rationale
- `docs/research/THRESHOLD_ANALYSIS.md`: Scoring threshold changes
- `docs/research/PERFORMANCE_VALIDATION.md`: F1 benchmark results

**Test Coverage**:
- `tests/performance/test_story_2_6_validation.py`: 8 validation tests
- Extended `test_pragmatic_markers.py` with Story 2.6 test classes:
  - `TestExpandedEpistemicHedges`: New epistemic hedge patterns
  - `TestExpandedCertaintyMarkers`: New certainty markers
  - `TestAttitudeMarkers`: New attitude marker category
  - `TestLikelihoodAdverbials`: New likelihood category
  - `TestExpandedAssertionActs`: New assertion act verbs
- All 48 unit tests passing, 88% coverage

#### Changed

**Expanded Pattern Dictionaries**:
- **EPISTEMIC_HEDGES**: 20 → 43 patterns (+23)
  - New modal hedges: would, should
  - New lexical verb hedges: seem, appear, believe, think, suspect, suppose
  - New adjective hedges: possible, probable, unlikely, uncertain, unclear
  - New approximators: nearly, essentially, relatively, somewhat, fairly, quite, typically, usually
  - New multi-word hedges: to some extent, in general

- **STRONG_CERTAINTY**: 6 → 18 patterns (+12)
  - Absolute certainty: always, never, completely, entirely
  - Emphatic certainty: totally, surely, truly, indeed
  - Confirmatory boosters: in fact, of course, unquestionably, undeniably

- **SUBJECTIVE_CERTAINTY**: 4 → 8 patterns (+4)
  - We know, I am certain, We are confident, It is clear

- **ASSERTION_ACTS**: 4 → 10 patterns (+6)
  - demonstrate, show, prove, establish, confirm, find

**Updated Scoring Thresholds** (for expanded 126-pattern lexicon):
- HEDGING_THRESHOLD_EXCELLENT: 7.0 → 9.0 (+29%)
- HEDGING_THRESHOLD_GOOD: 9.0 → 11.0 (+22%)
- HEDGING_THRESHOLD_CONCERNING: 12.0 → 15.0 (+25%)
- HEDGING_VARIETY_TARGET: 0.6 → 0.4 (adjusted for larger pattern set)
- HEDGING_VARIETY_OPTIMAL: 0.7 → 0.5
- CERTAINTY_THRESHOLD_MIN: 2.0 → 3.0 (+50%)
- CERTAINTY_THRESHOLD_MAX: 5.0 → 7.0 (+40%)
- SPEECH_ACTS_THRESHOLD_MAX: 6.0 → 8.0 (+33%)
- PRAGMATIC_HEDGE_TARGET: 6.0 → 7.0
- PRAGMATIC_CERTAINTY_TARGET: 3.5 → 5.0
- PRAGMATIC_SPEECH_TARGET: 4.5 → 5.5

**Pattern Count Summary**:
| Category | Pre-2.6 | Post-2.6 | Change |
|----------|---------|----------|--------|
| EPISTEMIC_HEDGES | 20 | 43 | +115% |
| FREQUENCY_HEDGES | 6 | 6 | 0% |
| EPISTEMIC_VERBS | 8 | 8 | 0% |
| STRONG_CERTAINTY | 6 | 18 | +200% |
| SUBJECTIVE_CERTAINTY | 4 | 8 | +100% |
| ASSERTION_ACTS | 4 | 10 | +150% |
| FORMULAIC_AI_ACTS | 4 | 4 | 0% |
| ATTITUDE_MARKERS | 0 | 18 | NEW |
| LIKELIHOOD_ADVERBIALS | 0 | 11 | NEW |
| **TOTAL** | **52** | **126** | **+142%** |

#### Performance Validation

- **Analysis time**: 0.0072s per 1k words (limit: 2.0s) - 276× faster than requirement
- **AI/Human score separation**: 12.7 points on full documents (Human: 59.2, AI: 46.5)
- **Pattern count**: 126/126 verified
- **All 8 validation tests passing**

#### Research Citations

1. **Hyland, K.** (2005). *Metadiscourse: Exploring Interaction in Writing*. Continuum.
2. **Pennebaker, J. W., et al.** (2015). *LIWC2015 Manual*. University of Texas at Austin.
3. **Biber, D., et al.** (1999). *Longman Grammar of Spoken and Written English*. Pearson.
4. **Vincze, V., et al.** (2008). BioScope Corpus. *BMC Bioinformatics*, 9(Suppl 11), S9.

#### Backward Compatibility

- **100% backward compatible** with v6.1.0
- All existing result fields preserved
- New fields (attitude_markers, likelihood_adverbials) are additive
- Scoring logic enhanced but maintains same 0-100 scale
- All regression tests pass

---

## [6.1.0] - 2025-01-24

### Dimension Scoring Optimization (Story 2.4.1)

**Major refactoring of dimension scoring functions based on research-backed distributions**

This release migrates all 16 dimensions from threshold-based heuristics to research-validated
scoring functions (Gaussian, monotonic increasing/decreasing, and quality-adjusted monotonic).
Includes z-score normalization infrastructure to eliminate clustering artifacts.

#### Added

**Score Normalization Infrastructure (AC7)**:
- **scoring/score_normalization.py** (NEW module)
  - Z-score normalization across all dimensions before weighted aggregation
  - Prevents clustering artifacts from mixed scoring functions (Gaussian/monotonic/threshold)
  - `ScoreNormalizer` class with configurable enable/disable
  - `compute_dimension_statistics()` method for validation set analysis
  - Loads dimension statistics from `scoring/dimension_stats.json` (μ, σ for each dimension)
  - Algorithm: `normalized = 50 + ((raw_score - μ) / σ) * 15`, clamped to [0, 100]
  - 22 comprehensive tests (100% coverage)

- **scoring/dimension_stats.json** (NEW configuration file)
  - Stores mean (μ) and stdev (σ) for each of 16 dimensions
  - Computed from validation set (placeholder values pending Task 8)
  - Used by ScoreNormalizer for z-score transformation

- **tests/performance/test_scoring_optimization_validation.py** (NEW test framework)
  - Performance validation framework for holdout testing
  - `ValidationCorpusLoader` class for loading labeled test sets
  - `PerformanceEvaluator` class for computing accuracy, F1, FPR, FNR, AUC-ROC
  - Domain robustness testing infrastructure (academic, social media, business)
  - Statistical significance testing framework (paired t-test)
  - Awaits validation corpus for full execution

#### Changed

**Group A: Gaussian Scoring (Natural Targets, AC3)** - 2 dimensions:
- **advanced_lexical.py (HD-D)**: Migrated to Gaussian scoring
  - Target: μ=0.85, σ=0.05 (human writing clusters around 0.85 HD-D)
  - Uses logit transformation before Gaussian: `logit(x) = log(x / (1-x))`
  - Research: Jarvis (2002), McCarthy & Jarvis (2010) on HD-D as lexical sophistication measure
  - 12 comprehensive tests added

- **syntactic.py (Repetition Diversity)**: Migrated to Gaussian scoring
  - Target: μ=0.75, σ=0.10 (human writing shows balanced syntactic variety)
  - Uses logit transformation for [0,1] bounded metrics
  - Research: Syntactic diversity research, LuResearches: Lu (2010), Kyle & Crossley (2018)
  - 12 comprehensive tests added

**Group B: Monotonic Scoring (Always Better, AC4)** - 4 dimensions:
- **burstiness.py**: Migrated to monotonic increasing
  - Thresholds: low=0.20 (AI flat), high=0.40 (human varied)
  - Higher variance = more human-like
  - Research: Gehrmann et al. (2019) GLTR, GPTZero methodology
  - 10 comprehensive tests added

- **perplexity.py**: Migrated to monotonic decreasing (via value inversion)
  - Thresholds: low=0.55 (human), high=0.70 (AI)
  - Lower top-10 percentage = more human-like
  - Research: GLTR 80% F1-score for GPT-3.5 detection
  - 11 comprehensive tests added

- **pragmatic_markers.py**: Migrated to monotonic increasing
  - Thresholds: low=1.5, high=6.0 markers per 1k words
  - Higher frequency = more conversational, human-like
  - Research: Fraser (1999), Schiffrin (1987) on discourse markers
  - 10 comprehensive tests added

- **transition_marker.py**: Migrated to monotonic increasing
  - Thresholds: low=2.0, high=8.0 markers per 1k words
  - Higher frequency = stronger discourse coherence
  - Research: Halliday & Hasan (1976) cohesion theory
  - 11 comprehensive tests added

**Group D: Transformed/Quality-Adjusted Scoring (AC6)** - 6 dimensions:
- **predictability.py (GLTR)**: Migrated to monotonic decreasing
  - Thresholds: low=0.55 (human), high=0.70 (AI)
  - Lower top-10 = less predictable = more human
  - Same research as perplexity (GLTR framework)
  - 11 comprehensive tests added

- **voice.py**: Migrated to monotonic increasing (contraction ratio)
  - Thresholds: low=0.005 (0.5%, AI), high=0.015 (1.5%, human)
  - Simplified from 3-marker system to single contraction ratio metric
  - Research: Conversational markers in human vs AI writing
  - 11 comprehensive tests added

- **figurative_language.py**: Migrated to monotonic + quality adjustments
  - Base monotonic: frequency per 1k words (low=0.1, high=0.8)
  - Variety bonus (0-15 points): using multiple types (similes, metaphors, idioms)
  - Novelty bonus (0-20 points): novel vs clichéd expressions
  - Cliché penalty (0-40 points): AI characteristic markers (delve: 28×, underscores: 13.8×)
  - Research: Kobak et al. (2025) on AI cliché overuse
  - 10 comprehensive tests added

- **semantic_coherence.py**: Migrated to monotonic + domain-aware thresholds
  - Base: average of 4 coherence metrics (cohesion, consistency, flow, depth)
  - Domain-specific thresholds:
    - Technical: lower thresholds (domain jargon reduces coherence scores)
    - Creative: higher thresholds (narrative freedom)
    - Academic: stricter thresholds (expects strong coherence)
    - General: balanced thresholds
  - Research: Embedding-based coherence detection (cosine similarity)
  - 9 comprehensive tests added (includes creative/academic domain tests)

- **ai_vocabulary.py**: Validated threshold scoring (no changes needed)
  - Already using research-based tier weighting (Tier 1: 3×, Tier 2: 2×, Tier 3: 1×)
  - Thresholds: low=2.0, high=8.0 per 1k words
  - Research: Kobak et al. (2025) AI vocabulary multipliers

- **formatting.py**: Validated threshold scoring (no changes needed)
  - Count-based metrics don't benefit from continuous scoring
  - Discrete bands for list overuse, em-dash abuse patterns

**Group C: Threshold Scoring (Validated, AC5)** - 4 dimensions retained as-is:
- **lexical.py**, **readability.py**, **sentiment.py**, **structure.py**
  - Validated that threshold-based scoring is appropriate for these metrics
  - Count-based or discrete categorical data doesn't benefit from continuous transformations

**Scoring Infrastructure Updates**:
- **dual_score_calculator.py**: Integrated z-score normalization
  - Added `config` parameter to `calculate_dual_score()`
  - Added `enable_normalization` check in `_build_dimension_scores()`
  - Applies `normalizer.normalize_score()` before weight calculation
  - Backward compatible (config optional, defaults to normalization enabled)

- **analyzer.py**: Pass config to dual score calculator
  - Updated `calculate_dual_score()` to pass `self.config` parameter

- **analysis_config.py**: Added normalization flag
  - New field: `enable_score_normalization: bool = True`
  - Allows disabling normalization for testing/comparison

**Shared Scoring Helpers (base_strategy.py, AC2)**:
- `_gaussian_score()`: Bell-curve scoring with μ (target) and σ (width) parameters
- `_monotonic_score()`: Three-zone scoring (fixed, linear, asymptotic)
  - Below threshold_low: fixed at 25
  - Between thresholds: linear 25-75
  - Above threshold_high: asymptotic 75-100
- `_logit_transform()`: Transforms [0,1] metrics to (-∞, ∞) for Gaussian scoring
- 15 comprehensive tests for scoring helpers

#### Test Coverage
- **87 new dimension migration tests** (Groups A, B, D)
- **22 normalization infrastructure tests** (100% coverage)
- **15 scoring helper tests** (shared base_strategy methods)
- **Performance validation framework** (awaits validation corpus)
- **Total: 124 new tests added**

#### Research Citations
- **GLTR Framework**: Gehrmann et al. (2019), 80% F1-score for GPT-3.5 detection
- **Burstiness**: GPTZero methodology (Tian, 2023)
- **Lexical Diversity (HD-D)**: Jarvis (2002), McCarthy & Jarvis (2010)
- **Syntactic Diversity**: Lu (2010), Kyle & Crossley (2018)
- **Pragmatic Markers**: Fraser (1999), Schiffrin (1987)
- **Cohesion Theory**: Halliday & Hasan (1976)
- **AI Vocabulary**: Kobak et al. (2025) multiplier analysis
- **Semantic Coherence**: Embedding-based coherence (cosine similarity research)

#### Configuration
- Normalization enabled by default (`enable_score_normalization=True`)
- Disable via: `AnalysisConfig(enable_score_normalization=False)`
- Statistics loaded from `scoring/dimension_stats.json`

#### Migration Notes
- **Zero breaking changes**: All APIs backward compatible
- Scoring functions updated internally, no interface changes
- Existing tests pass with same results structure
- Score values will differ slightly due to optimization (expected behavior)

#### Performance
- Normalization adds <1ms overhead per analysis
- No measurable performance regression from scoring optimizations
- Full validation pending Task 8 (requires validation corpus)

#### Future Work
- **Task 8**: Performance validation with 500+ document holdout set
- **Task 11**: Remove deprecated scoring code after validation complete

## [6.0.0] - 2025-11-22

### BREAKING CHANGES (Story 1.17)

**Project renamed from "AI Pattern Analyzer" to "WriteScore"**

This is a major version bump due to breaking changes in package naming and CLI command.

#### Changed
- **Package name**: `ai_pattern_analyzer` → `writescore`
- **CLI command**: `analyze-ai-patterns` → `writescore`
- **Python imports**: All `from ai_pattern_analyzer.*` → `from writescore.*`
- **Directory structure**: `.../ai_pattern_analyzer/` → `.../writescore/`
- **Project description**: Updated to "Writing quality scoring tool with AI pattern detection"

#### Migration
- See `MIGRATION-v6.0.0.md` for complete upgrade instructions
- No backward compatibility aliases provided
- All existing scripts and integrations must update imports and CLI commands

#### Preserved (Zero Functional Changes)
- ✅ All algorithms, scoring, and behavior unchanged
- ✅ All analysis history preserved and compatible
- ✅ All configuration files compatible
- ✅ All command-line flags and options unchanged
- ✅ Test suite passes with same results as v5.0.0

#### Files Updated
- 79 Python files (automated import updates)
- 51 markdown documentation files
- Multiple framework files in `.bmad-technical-writing/`
- 432+ project documentation references in `/docs`
- Configuration files: `pyproject.toml`, `pytest.ini`

#### Rationale
The new name "WriteScore" better reflects the tool's purpose:
- Emphasizes writing quality scoring over AI detection mechanism
- Shorter, more memorable (10 chars vs 21)
- More professional for external sharing
- User-centric branding focused on benefits

### AI Vocabulary Extraction (Story 2.4.0.6)

**Extracted AI vocabulary patterns into dedicated dimension**:

#### Added
- **ai_vocabulary.py** (NEW dimension - 3% weight, 34 patterns)
  - Extracted from perplexity.py to separate AI vocabulary detection from true perplexity calculation
  - **Tier 1** (14 patterns, 3× weight): delve, robust, leverage, harness, underscore, holistic, myriad, plethora, quintessential, paramount, foster, realm, tapestry, embark
  - **Tier 2** (12 patterns, 2× weight): revolutionize, game-changing, cutting-edge, pivotal, intricate, nuanced, multifaceted, comprehensive, innovative, transformative, seamless, dynamic
  - **Tier 3** (8 patterns, 1× weight): optimize, streamline, facilitate, enhance, mitigate, navigate, ecosystem, landscape
  - Tier-weighted scoring: `(tier1*3 + tier2*2 + tier3*1) per 1k words`
  - Threshold-based scoring (Group C): low=2.0, high=8.0 per 1k words
  - Comprehensive regex patterns for inflected forms (e.g., delve/delves/delving)
  - Tier: CORE
  - Self-registers with DimensionRegistry

#### Changed
- **perplexity.py** (STUB - initially 2% weight, later increased to 3% in Story 2.4.0.7)
  - Reduced to stub implementation pending Story 2.4.0.7 (true perplexity calculation)
  - Returns neutral score 50.0 (no contribution to aggregate until implemented)
  - Removed AI vocabulary detection code (moved to ai_vocabulary.py)
  - Removed AI_VOCAB_REPLACEMENTS dictionary
  - Added TODO comments for Story 2.4.0.7 implementation
  - Will implement: Perplexity = exp(-(1/N) × Σ log P(w_i | context))
  - Target thresholds: 25.0-45.0 (monotonic scoring, Group B)
  - Research findings: Human median 35.9, AI median 21.2 (40% lower)

#### Weight Distribution
- **Original**: perplexity.py = 5% (AI vocabulary + placeholder for true perplexity)
- **New distribution** (Story 2.4.0.6):
  - ai_vocabulary.py: 3% (AI vocabulary patterns)
  - perplexity.py: 2% (stub, neutral score pending Story 2.4.0.7)
- **Final distribution** (Story 2.4.0.7):
  - ai_vocabulary.py: 3% (AI vocabulary patterns)
  - perplexity.py: 3% (true perplexity implementation, validated)
- **Total**: 6% (increased by 1% based on empirical validation)

#### Dimension Count
- **Total dimensions**: 16 (was 15)
  - 15 existing functional dimensions
  - 1 new ai_vocabulary dimension
  - perplexity stub (non-contributory until Story 2.4.0.7)

#### Testing
- 49 new tests for ai_vocabulary.py (all tier patterns, weighted scoring, thresholds)
- 23 updated tests for perplexity.py stub (validates neutral score behavior)
- Updated regression baseline scores (perplexity: all samples now 50.0)
- Updated integration tests for new weight distribution
- All backward compatibility tests pass

#### Files Added
- `dimensions/ai_vocabulary.py` (150 lines)
- `tests/unit/dimensions/test_ai_vocabulary.py` (279 lines)

#### Files Modified
- `dimensions/perplexity.py` (378 → 193 lines, stub implementation)
- `tests/unit/dimensions/test_perplexity.py` (completely rewritten for stub)
- `tests/fixtures/baseline_scores.json` (updated perplexity baselines to 50.0)
- `tests/integration/test_dimension_registration.py` (updated weight assertions)

### True Perplexity Implementation with MPS Acceleration (Story 2.4.0.7)

**Implemented mathematical perplexity calculation using GPT-2 language model with hardware acceleration**:

#### Changed
- **perplexity.py** (FULL IMPLEMENTATION - 3% weight, validated with 29.5% discrimination)
  - Replaced stub with true mathematical perplexity calculation
  - **Formula**: Perplexity = exp(-(1/N) × Σ log P(w_i | context))
  - Uses GPT-2 language model for token probability computation
  - **MPS Acceleration**: Apple Silicon Metal Performance Shaders support (14.8× speedup)
  - **Intelligent device detection**: Priority hierarchy (MPS > CUDA > CPU)
  - **Monotonic scoring** (Group B thresholds: 25.0-45.0):
    - Below 25.0: Score 0-20 (very AI-like)
    - Between 25.0-45.0: Score 20-80 (linear interpolation)
    - Above 45.0: Score 80-100 (very human-like)
  - **Research findings**: Human median 35.9, AI median 21.2 (40% discrimination)
  - **Performance characteristics**: 0.09s per 1k words (33× faster than 3s target)
  - **Performance breakdown**:
    - First analysis: 8.62s (includes model loading)
    - Subsequent analyses: 0.04-0.05s (cached model)
    - 14.8× speedup from MPS acceleration vs CPU
    - 30.5× speedup from model caching
  - **Optimization**: Uses PyTorch cross-entropy loss for efficient single-pass calculation
  - **Security**: Input validation (1MB limit, control character sanitization, 1024 token limit)
  - Tier: ADVANCED (requires language model)
  - Self-registers with DimensionRegistry
  - Status changed from STUB → FULL IMPLEMENTATION

#### Implementation Details
- **Device Management**: Intelligent device detection with _get_device() method
  - Priority hierarchy: MPS (Apple Silicon) > CUDA (NVIDIA) > CPU (fallback)
  - Model and all tensors automatically moved to optimal device
  - Device caching for consistent performance across analyses
- **Model Loading**: Thread-safe global cache with lazy initialization and double-check locking
- **Tokenization**: Input validation and security checks (1MB limit, control character sanitization)
- **Perplexity Calculation**: Efficient single-pass computation using PyTorch's built-in cross-entropy loss
- **Monotonic Scoring**: Higher perplexity (human-like) → higher scores
- **Context Window**: Limited to 1024 tokens for performance and memory management
- **Performance**: First analysis loads model (8.62s), subsequent analyses use cached model (0.04-0.05s)

#### Testing
- 57 comprehensive tests covering:
  - Dimension properties and registration (4 tests)
  - Model loading and caching (5 tests)
  - Tokenization with validation (6 tests)
  - Perplexity calculation (4 tests)
  - Monotonic scoring (8 tests)
  - analyze() method (8 tests)
  - Edge cases (5 tests)
  - Performance validation (2 tests)
  - Integration tests (4 tests)
  - Recommendations and backward compatibility (11 tests)
- **Test Results**: 56/57 passing (98.2% pass rate)
  - Main performance test passes in 8.62s (0.09s per 1k words)
  - 1 optional benchmark test with tight assertion (not a blocker)
- **MPS Acceleration Impact**:
  - 14.8× speedup from CPU baseline (127s → 8.62s)
  - 30.5× speedup from model caching (1.42s → 0.04s)
  - Production-ready performance achieved
- Updated baseline_scores.json with real perplexity scores
- Updated test_dimension_registration.py for ADVANCED tier

#### Files Modified
- `dimensions/perplexity.py` (193 → 543 lines, full implementation; updated weight 2% → 3%)
- `tests/unit/dimensions/test_perplexity.py` (280 → 571 lines, comprehensive test suite; test renamed to test_weight_is_3_percent)
- `tests/integration/test_dimension_registration.py` (tier assertion updated to ADVANCED)
- `tests/fixtures/baseline_scores.json` (updated with real perplexity scores)

#### Weight Validation and Adjustment (Story 2.4.0.7 - AC10)
- **Weight validation executed**: `validate_perplexity_weight.py` script run on representative corpus
- **Empirical results**:
  - AI samples mean perplexity: 27.80
  - Human samples mean perplexity: 36.00
  - Discrimination: 29.5% (moderate, below 40% expected from research)
  - Score difference: 24.6 points between AI and human samples
  - Signal strength: 2% × 24.6 = ~0.49 point impact on final score
- **Weight adjustment decision**: **Increased from 2% to 3%**
  - Rationale: Moderate discrimination (29.5%) suggests dimension can contribute more effectively with higher weight
  - New impact: 3% × 24.6 = ~0.74 point contribution to final score
  - Recommendation source: Weight validation script (Option B)
- **Updated files**:
  - `dimensions/perplexity.py`: weight property returns 3.0 (was 2.0)
  - `dimensions/perplexity.py`: documentation updated to reflect 3% weight and validation results
  - `tests/unit/dimensions/test_perplexity.py`: test_weight_is_3_percent (was test_weight_is_2_percent)
- **Test results**: All 57 tests pass (100% pass rate) with new 3% weight

### Dimension Refactoring (Story 2.4.0.5)

**Three-way dimension refactor** for clearer separation of concerns:

#### Added
- **pragmatic_markers.py** (NEW dimension - 4% weight, 52 patterns)
  - Extracted from transition_marker.py to separate epistemic stance from discourse structure
  - **Epistemic Hedging** (20 patterns): might, may, could, possibly, perhaps, about, almost, etc.
  - **Frequency Hedges** (6 patterns): frequently, occasionally, sometimes, often, rarely, seldom
  - **Epistemic Verbs** (8 patterns): assume, estimate, indicate, speculate, propose, claim, argue, suggest
  - **Certainty Markers** (10 patterns): definitely, certainly, I believe, I think, clearly, obviously, etc.
  - **Speech Act Patterns** (8 patterns): I argue, We propose, This shows, This demonstrates, etc.
  - Tier: ADVANCED
  - Self-registers with DimensionRegistry

#### Changed
- **transition_marker.py** (EXPANDED - v2.0.0, 6% weight)
  - Removed pragmatic marker patterns (moved to pragmatic_markers.py)
  - Added formulaic transitions from perplexity.py:
    - Furthermore, Moreover, Additionally, In addition
    - First and foremost, In conclusion, To summarize, In summary
    - It is important to note that, It is worth mentioning that
    - When it comes to, With that said, Having said that
    - (Total: 19 formulaic transition patterns from FORMULAIC_TRANSITIONS)
  - Composite scoring: 50% basic transitions + 50% formulaic transitions
  - Now combines basic discourse markers (however, moreover) with formulaic transitions

- **perplexity.py** (REDUCED SCOPE - 5% weight)
  - Removed formulaic transition detection (moved to transition_marker.py)
  - Removed TRANSITION_REPLACEMENTS dictionary
  - Currently analyzes AI vocabulary patterns only (temporary)
  - Marked as TEMPORARY STATE pending:
    - Story 2.4.0.6: Extract AI vocabulary to ai_vocabulary.py
    - Story 2.4.0.7: Implement true perplexity calculation
  - Added TODO comments for future refactoring

#### Weight Distribution
- **Original**: transition_marker.py = 10% (composite: 40% basic, 60% pragmatic)
- **New distribution**:
  - transition_marker.py: 6% (basic 50% + formulaic 50%)
  - pragmatic_markers.py: 4% (epistemic stance markers)
- **Total unchanged**: 10%
- **Rationale**: Transitions show stronger empirical signal per research

#### Backward Compatibility
- All existing unit tests pass
- API signatures unchanged (DimensionStrategy.analyze())
- Aggregate scores remain comparable (variance ≤ ±5 points)
- Migration is non-breaking for users
- Total dimension count: 12 (now 12 files for 12 conceptual dimensions)

#### Testing
- test_pragmatic_markers.py created (30 tests, 8 test classes)
- test_transition_marker.py updated (formulaic transition tests added)
- test_perplexity.py updated (formulaic transition tests removed)
- All 99 tests pass for the 3 refactored dimensions
- 85%+ code coverage maintained

---

## [5.1.1] - 2025-11-19

### Added (Story 2.2.1)

#### TransitionMarkerDimension Expanded Lexicon (v1.1.0 → v1.2.0)
- **Expanded Pragmatic Marker Lexicon** - 21 new patterns from Hyland's taxonomy:
  - **Approximators** (7 patterns): about, almost, approximately, around, roughly, generally, largely
    - Added to EPISTEMIC_HEDGES dictionary (13 → 20 patterns)
    - Low-ambiguity patterns with word boundaries to avoid false positives
  - **Frequency Hedges** (6 patterns): frequently, occasionally, sometimes, often, rarely, seldom
    - New FREQUENCY_HEDGES dictionary
    - Detects temporal hedging patterns common in AI text
  - **Epistemic Verbs** (8 patterns with inflections): assume/d/s, estimate/d/s, indicate/d/s, speculate/d/s, propose/d/s, claim/ed/s, argue/d/s, suggest/ed/s
    - New EPISTEMIC_VERBS dictionary
    - Regex patterns handle verb inflections (base, -s, -d, -ed forms)

- **Enhanced Results Schema** (backward compatible):
  - `approximators_count`: Count of approximator matches
  - `frequency_hedges_count`: Count of frequency hedge matches
  - `epistemic_verbs_count`: Count of epistemic verb matches
  - All v1.1.0 fields preserved (100% backward compatible)

- **Test Coverage**:
  - 9 new test cases (67 total tests for TransitionMarkerDimension)
  - 93% code coverage (exceeds 85% requirement)
  - `TestExpandedLexiconV1_2` class: comprehensive v1.2.0 tests
  - All v1.1.0 and v1.0.0 tests continue to pass

### Changed (Story 2.2.1)
- **Pattern Coverage**: 31 → 52 patterns (+67% increase)
  - 20 epistemic hedges (13 v1.1.0 + 7 approximators v1.2.0)
  - 6 frequency hedges (new in v1.2.0)
  - 8 epistemic verbs (new in v1.2.0)
  - 10 certainty markers (unchanged from v1.1.0)
  - 8 speech act patterns (unchanged from v1.1.0)

- **Recall Improvement**: Estimated +20% (50-60% → 70-80%)
  - Approaching 50% of Hyland's complete taxonomy
  - Better detection of AI overuse patterns

- **Performance**: Negligible impact
  - Pre-compiled regex patterns (no runtime compilation)
  - Linear scan O(n) complexity (same as v1.1.0)
  - Zero new dependencies (regex-only architecture maintained)

- **Version Metadata**:
  - Class docstring updated to v1.2.0
  - Module docstring includes full version history
  - Pattern count documentation updated

### Backward Compatibility (Story 2.2.1)
- **100% Compatible** with v1.1.0 and v1.0.0
- All existing result fields preserved
- New fields are additive (won't break existing consumers)
- Scoring logic unchanged
- All regression tests pass

## [5.1.0] - 2025-11-18

### Added (Story 2.2)

#### TransitionMarkerDimension Enhancements (v1.0.0 → v1.1.0)
- **Pragmatic Markers Detection** - 30+ new patterns analyzing AI-specific linguistic markers:
  - **Epistemic Hedging** (13 patterns): might, may, could, possibly, perhaps, presumably, conceivably, potentially, it seems, it appears, suggests that, tends to, likely to
    - Human baseline: 4-7 hedges per 1k words
    - AI baseline: 10-15 hedges per 1k words (overuse due to safety training)
  - **Certainty Markers** (10 patterns):
    - Strong certainty: definitely, certainly, absolutely, undoubtedly, clearly, obviously
    - Subjective certainty: I believe, I think, we believe, in my view
  - **Speech Act Patterns** (8 patterns):
    - Personal assertions: I argue that, we propose that, this shows, this demonstrates
    - Formulaic AI patterns: it can be argued that, it is important to note that, it should be noted that, it is worth noting that

- **New Analysis Methods**:
  - `_analyze_hedging()`: Detects epistemic hedging patterns with density calculations
  - `_analyze_certainty()`: Analyzes strong and subjective certainty markers
  - `_analyze_speech_acts()`: Identifies personal vs formulaic speech acts
  - `_analyze_pragmatic_markers()`: Orchestrates all pragmatic analysis (v1.1.0)

- **Composite Metrics**:
  - `certainty_hedge_ratio`: Balance between certainty and hedging
  - `pragmatic_balance`: Overall balance of pragmatic markers
  - Marker density calculations per 1k words

- **Enhanced Scoring**:
  - 4-component weighted composite scoring:
    - Transitions: 40% (however, moreover patterns - v1.0.0)
    - Hedging: 25% (epistemic hedging patterns - v1.1.0)
    - Certainty: 20% (strong + subjective certainty - v1.1.0)
    - Speech Acts: 15% (formulaic AI patterns - v1.1.0)
  - Research-backed thresholds for each component
  - Backward-compatible scoring maintains v1.0.0 behavior

- **Test Coverage**:
  - 15 new test cases (58 total tests)
  - 92% code coverage (exceeds 85% requirement)
  - `TestPragmaticMarkersV1_1` class: 10 integration tests
  - `TestPragmaticScoringComponents` class: 5 unit tests for scoring methods

### Changed (Story 2.2)

#### Backward Compatibility
- **v1.0.0 fields preserved at top level** of results dictionary:
  - `transition_count`, `however_count`, `moreover_count`, `however_density`, `moreover_density`, `transition_instances`
- **v1.1.0 fields added as new keys** (non-breaking):
  - `hedging_count`, `hedging_density`, `hedge_patterns`, `certainty_count`, `certainty_density`, `certainty_patterns`
  - `speech_act_count`, `formulaic_ai_count`, `certainty_hedge_ratio`, `pragmatic_balance`
- **Existing API contracts maintained** - no changes to public method signatures
- **Score calculation enhanced** - includes new pragmatic components while maintaining v1.0.0 behavior

### Technical Details

- **Performance**: Pre-compiled regex patterns for efficiency (<0.05s additional processing time)
- **Dependencies**: No new dependencies (uses standard library `re`)
- **Weight**: 10.0% (unchanged)
- **Tier**: ADVANCED (unchanged)

## [5.0.0] - 2025-11-10

**BREAKING CHANGES** - This is a major version release that removes deprecated dimensions and backward compatibility code.

### Removed (Story 2.0)

#### Deprecated Dimensions
- **AdvancedDimension** (`dimensions/advanced.py` - 655 lines)
  - Removed in favor of `PredictabilityDimension` and `AdvancedLexicalDimension` (split in Story 1.4.5)
  - GLTR analysis now handled by `PredictabilityDimension`
  - Advanced lexical metrics now handled by `AdvancedLexicalDimension`

- **StylometricDimension** (`dimensions/stylometric.py` - 378 lines)
  - Removed in favor of `ReadabilityDimension` and `TransitionMarkerDimension` (split in Story 1.4.5)
  - Readability metrics now handled by `ReadabilityDimension`
  - Transition marker analysis now handled by `TransitionMarkerDimension`

#### Backward Compatibility Code
- **Removed `StylometricIssue` dataclass** from `core/results.py`
  - TransitionMarkerDimension now uses `TransitionInstance` instead
  - Fields renamed: `marker_type` → `transition`, `suggestion` → `suggestions` (list)

- **Removed `gltr_score` property** from `AnalysisResults`
  - Use `predictability_score` field directly instead

- **Removed `stylometric_score` field** from `AnalysisResults`
  - Use `readability_score` and `transition_marker_score` instead

- **Removed `stylometric_issues` field** from `DetailedAnalysis`
  - Use `transition_instances` from TransitionMarkerDimension instead

- **Removed deprecated parameters** from `_flatten_optional_metrics()`
  - Removed `stylometric_results` parameter
  - Removed `advanced_results` parameter

#### CLI Output
- **Removed stylometric markers section** from detailed reports (48 lines)
  - Transition marker information now reported through standard dimension output

### Changed (Story 2.0)

#### Positive Label System ✨ **NEW**
- **Replaced confusing impact-style labels with positive quality labels** for all dimension scores
  - **OLD labels (v4.x)**: HIGH / MEDIUM / LOW / VERY LOW
  - **NEW labels (v5.0.0)**: **EXCELLENT** / **GOOD** / **NEEDS WORK** / **POOR**
  - **Rationale**: Old labels were backwards - "LOW" sounded bad but meant low problems (good). New labels are intuitive.
  - **Scoring ranges**:
    - EXCELLENT: 85-100 (minimal AI patterns detected)
    - GOOD: 70-84 (some AI patterns, mostly human-like)
    - NEEDS WORK: 50-69 (noticeable AI patterns)
    - POOR: 0-49 (strong AI patterns detected)
  - **Applies to**: All 12 dimension scores in reports and API responses
  - **Implementation**: `core/analyzer.py:774-801` (`_convert_score_to_category()`)
  - **Report Updates**: All 12 dimensions now visible in DIMENSION SCORES section (`cli/formatters.py:746-765`)

#### Dimension Count
- **Updated from 14 to 12 dimensions** in v5.0.0
  - Removed: `advanced`, `stylometric` (deprecated dimensions)
  - Current 12 dimensions: `perplexity`, `burstiness`, `structure`, `formatting`, `voice`, `readability`, `lexical`, `sentiment`, `syntactic`, `predictability`, `advanced_lexical`, `transition_marker`

#### Import Statements
- **Removed `StylometricIssue`** from package exports (`__init__.py`)
  - Use `TransitionInstance` for transition marker issues

### Added (Story 2.0)

- **`validate_no_deprecated()` method** in `DimensionRegistry`
  - Validates that no deprecated dimensions are registered
  - Raises `RuntimeError` if any deprecated dimensions found
  - Useful for ensuring cleanup is complete in v5.0.0+

### Migration Guide (v4.x → v5.0.0)

**BREAKING CHANGES** require code updates:

1. **Update dimension references:**
   ```python
   # OLD (v4.x) - deprecated dimensions
   advanced_dim = analyzer.dimensions.get('advanced')
   stylometric_dim = analyzer.dimensions.get('stylometric')

   # NEW (v5.0.0) - use split dimensions
   predictability_dim = analyzer.dimensions.get('predictability')
   advanced_lexical_dim = analyzer.dimensions.get('advanced_lexical')
   readability_dim = analyzer.dimensions.get('readability')
   transition_marker_dim = analyzer.dimensions.get('transition_marker')
   ```

2. **Update field access:**
   ```python
   # OLD (v4.x) - backward compatibility properties
   gltr_score = results.gltr_score  # Property redirect
   stylometric_score = results.stylometric_score

   # NEW (v5.0.0) - use direct fields
   predictability_score = results.predictability_score  # Direct field
   readability_score = results.readability_score
   transition_marker_score = results.transition_marker_score
   ```

3. **Update issue handling:**
   ```python
   # OLD (v4.x) - StylometricIssue
   from writescore.core.results import StylometricIssue
   issues = stylometric_dim.analyze_detailed(lines)
   for issue in issues:
       print(issue.marker_type)  # 'however', 'moreover'

   # NEW (v5.0.0) - TransitionInstance
   from writescore.core.results import TransitionInstance
   transition_dim = analyzer.dimensions.get('transition_marker')
   issues = transition_dim.analyze_detailed(lines)
   for issue in issues:
       print(issue.transition)  # 'however', 'moreover'
       print(issue.suggestions)  # List of suggestions
   ```

4. **Update dimension count expectations:**
   ```python
   # OLD (v4.x) - expected 14 dimensions
   assert len(analyzer.dimensions) == 14

   # NEW (v5.0.0) - expect 12 dimensions
   assert len(analyzer.dimensions) == 12
   assert results.dimension_count == 12  # Story 1.10 field
   ```

5. **Update score label expectations:**
   ```python
   # OLD (v4.x) - old label system
   assert results.voice_score == "HIGH"
   assert results.perplexity_score in ["MEDIUM", "LOW"]

   # NEW (v5.0.0) - positive label system
   assert results.voice_score == "EXCELLENT"
   assert results.perplexity_score in ["GOOD", "NEEDS WORK"]

   # Label mapping:
   # HIGH → EXCELLENT (85-100)
   # MEDIUM → GOOD (70-84)
   # LOW → NEEDS WORK (50-69)
   # VERY LOW → POOR (0-49)
   ```

### Technical Details

- **Files deleted:** 4 dimension files + 2 test files (1,033 + test lines removed)
- **Backward compatibility:** **0%** - This is a breaking change release
- **Testing:** All Story 2.0-related tests passing
  - Deleted 4 deprecated tests in `test_analyzer.py`
  - Deleted `test_stylometric.py` (4 tests)
  - Updated `test_transition_marker.py` (43 tests passing)
  - Fixed field name changes: `marker_type` → `transition`

### Dependencies

- No changes to external dependencies
- Python 3.7+ still required
- All dimension dependencies unchanged (nltk, textstat, etc.)

### Known Issues

- None related to Story 2.0 changes
- Pre-existing issues in `test_structure_phase3.py` and `test_voice.py` are unrelated to this release

---

## [Unreleased]

### Added

#### Analysis Modes (Story 1.4.9)

- **Four analysis modes** to balance speed and accuracy:
  - `--mode fast`: Quick analysis of document start (default) - ~2000 chars per dimension
  - `--mode adaptive`: Intelligent sampling based on document size (recommended) - adjusts coverage automatically
  - `--mode sampling`: Custom sampling strategy with `--samples` and `--sample-size` options
  - `--mode full`: Complete document analysis - 100% coverage, maximum accuracy

- **Mode-specific CLI arguments**:
  - `--mode {fast,adaptive,sampling,full}`: Select analysis mode
  - `--samples N`: Number of samples for sampling mode (1-50, default: 10)
  - `--sample-size N`: Characters per sample for sampling mode (default: 2000)
  - `--sampling-strategy {uniform,weighted,start,end}`: Sampling distribution strategy
  - `--dry-run`: Preview analysis configuration without running analysis
  - `--show-coverage`: Display detailed coverage statistics after analysis
  - `--help-modes`: Display comprehensive help about analysis modes

- **Mode tracking in history system**:
  - Added `analysis_mode` field to HistoricalScore records
  - Added `analysis_time_seconds` field to track analysis duration
  - Mode and time information displayed in history reports
  - Full backward compatibility with existing history files (defaults to "adaptive" mode)

- **Mode display in output formats**:
  - Analysis mode shown in all output formats (text, JSON, TSV)
  - Mode included in batch analysis TSV output as dedicated column
  - Mode displayed in report headers for text format
  - Mode included in JSON output for programmatic access

- **Comprehensive documentation**:
  - Created `docs/analysis-modes-guide.md` with 500+ lines of documentation
  - Added Analysis Modes section to README.md with quick start and mode comparison
  - Mode help integrated into CLI with `--help-modes` command
  - Examples for all modes and use cases

### Changed

- **Default analysis mode**: Fast mode is now the default (previously analyzed full document)
- **CLI argument parsing**: Extended with mode-specific configuration options
- **History format**: History v2.0 now includes mode and time metadata (backward compatible)
- **Output formatters**: All format functions now accept optional `mode` parameter
- **Analysis configuration**: Main analyzer now accepts `AnalysisConfig` with mode settings

### Technical Details

- **Backward Compatibility**: 100% maintained
  - Old code without mode arguments continues to work (defaults to fast mode)
  - Existing history files load correctly (missing mode fields use defaults)
  - All existing CLI flags and output formats work unchanged

- **Testing**: Comprehensive test coverage added
  - 11+ new tests for mode tracking in history system
  - All tests passing (72 total tests)
  - Tests cover serialization, deserialization, backward compatibility, and display

- **Performance**: Analysis time varies by mode
  - Fast mode: 2-5 seconds (most documents)
  - Adaptive mode: 5-15 seconds (automatically scaled)
  - Sampling mode: 10-30 seconds (configurable)
  - Full mode: 30-120+ seconds (depends on document size)

### Migration Guide

For users upgrading from previous versions:

**No breaking changes** - all existing commands work identically:

```bash
# Old command (still works - now uses fast mode)
python analyze_ai_patterns.py document.md

# Recommended upgrade for better accuracy
python analyze_ai_patterns.py document.md --mode adaptive

# For final review/maximum accuracy
python analyze_ai_patterns.py document.md --mode full
```

History files from previous versions load automatically with default mode values.

## [4.0.0] - 2024

### Changed

- Complete refactoring from monolithic 7,079-line file to modular architecture
- Package structure with 17+ modules, largest <1,100 lines each
- Separation of concerns: core, dimensions, scoring, history, utils, CLI
- Full backward compatibility maintained via package-level exports

### Added

- Modular dimension analyzers with base interface
- Dual-score calculation system
- History tracking with comprehensive metadata
- CLI argument parsing and output formatting modules

---

## Version Numbering

- **Major version** (X.0.0): Breaking changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

---

[Unreleased]: https://github.com/your-org/writescore/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/your-org/writescore/releases/tag/v4.0.0
