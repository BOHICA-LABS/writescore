# WriteScore Product Requirements Document (PRD)

**Version:** 2.0
**Status:** Active
**Last Updated:** 2025-12-02
**Product Version:** 6.3.0

---

## 1. Goals and Background Context

### 1.1 Goals

- **Detect AI-generated writing patterns** across multiple linguistic dimensions with high accuracy
- **Provide actionable feedback** with specific line-by-line suggestions for improving writing authenticity
- **Score documents objectively** using a dual-score system that separates detection risk from writing quality
- **Support iterative improvement** by tracking score history across editing sessions
- **Scale to book-length documents** through intelligent sampling modes that balance speed vs. accuracy
- **Enable customization** via domain-specific terms, dimension profiles, and recalibrated parameters
- **Maintain scientific rigor** through percentile-anchored scoring derived from validated human/AI datasets

### 1.2 Background Context

As AI writing assistants (ChatGPT, Claude, etc.) have become ubiquitous, writers face a new challenge: their AI-assisted content often contains detectable patterns that undermine authenticity and trigger AI detection tools. These patterns include overuse of em-dashes, formulaic transitions ("Furthermore," "Moreover,"), uniform sentence lengths, and predictable vocabulary choices.

WriteScore addresses this by providing writers with detailed analysis of their text across 18 linguistic dimensions—far more comprehensive than simple AI detectors that only give a binary "AI/human" verdict. Rather than just flagging content as AI-generated, WriteScore shows *exactly which patterns* trigger detection and *how to fix them*, enabling writers to maintain their authentic voice while leveraging AI assistance.

**Target Users:** Individual writers improving their own content—technical writers, fiction authors, content creators, and anyone wanting to reduce AI-detectable patterns in their writing.

### 1.3 Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-02 | 2.0 | Restructured PRD to align with template; added full story AC | SM Agent |
| 2025-11-26 | 1.0 | Reverse-engineered PRD from existing codebase v6.3.0 | PM Agent |

---

## 2. Requirements

### 2.1 Functional Requirements

- **FR1:** The system shall analyze Markdown text documents and produce scores across multiple linguistic dimensions
- **FR2:** The system shall calculate a dual score: Detection Risk (0-100, lower=better) and Quality Score (0-100, higher=better)
- **FR3:** The system shall support four analysis modes: FAST (truncated), ADAPTIVE (smart sampling), SAMPLING (configurable), and FULL (complete)
- **FR4:** The system shall provide detailed line-by-line diagnostics with context, problem identification, and specific replacement suggestions
- **FR5:** The system shall detect AI vocabulary patterns including "delve," "robust," "leverage," "harness," and 30+ other AI-typical words
- **FR6:** The system shall detect formatting patterns including em-dash overuse (10x more common in AI text than human)
- **FR7:** The system shall measure sentence burstiness (variation in sentence length) as a key human-vs-AI discriminator
- **FR8:** The system shall track score history across multiple editing iterations for a single document
- **FR9:** The system shall support batch analysis of all .md files in a directory
- **FR10:** The system shall output results in text, JSON, or TSV formats
- **FR11:** The system shall allow recalibration of scoring parameters from validation datasets
- **FR12:** The system shall support parameter version management (deploy, rollback, diff, versions)
- **FR13:** The system shall provide dimension profiles (fast/balanced/full) to control which dimensions are loaded
- **FR14:** The system shall allow custom domain-specific terms to be configured for technical writing analysis
- **FR15:** The system shall strip HTML comments (metadata blocks) before analysis to avoid false positives

### 2.2 Non-Functional Requirements

- **NFR1:** FAST mode shall complete analysis in 5-15 seconds for any document size
- **NFR2:** ADAPTIVE mode shall complete analysis in 30-240 seconds for book-chapter-length documents (~90 pages)
- **NFR3:** FULL mode may take 5-20 minutes for large documents but shall analyze 100% of content
- **NFR4:** The system shall support Python 3.9, 3.10, 3.11, and 3.12
- **NFR5:** The system shall be installable via `pip install -e .` with optional dependency groups (dev, ml)
- **NFR6:** The scoring convention shall use 0-100 scale where 100 = most human-like consistently across all dimensions
- **NFR7:** The system shall provide meaningful results for documents as short as 50 characters
- **NFR8:** The system shall handle documents up to 500,000+ characters (book-length) via sampling modes
- **NFR9:** Dimension analyzers shall self-register via the DimensionRegistry pattern for extensibility
- **NFR10:** The CLI shall provide interactive confirmation for FULL mode on large documents (>500k chars)
- **NFR11:** The system shall maintain backward compatibility with existing `.ai-analysis-history` files
- **NFR12:** The system shall support existing parameter file formats (JSON and YAML)
- **NFR13:** CLI command structure shall remain stable (`writescore analyze`, `writescore recalibrate`)

---

## 3. Technical Assumptions

### 3.1 Repository Structure: Monorepo

Single repository containing all WriteScore components:
- `src/writescore/` - Main package (src-layout per PEP 517/518)
- `tests/` - Test suite (unit, integration, accuracy, performance)
- `docs/` - Documentation and stories
- `config/` - Scoring parameters and configuration

### 3.2 Service Architecture

**Local CLI Tool (Monolith)**

WriteScore is a self-contained command-line application with no external service dependencies:
- Single Python package installed via pip
- File-based history storage (`.ai-analysis-history/`)
- No database or network infrastructure required
- Entry point: `writescore` CLI command

### 3.3 Testing Requirements

**Full Testing Pyramid:**
- **Unit tests:** Per-module coverage (target: 80%+)
- **Integration tests:** Cross-module functionality
- **Accuracy tests:** Validation against human/AI document corpus
- **Performance tests:** Benchmarking analysis modes

**Test Markers:** `slow`, `integration`, `accuracy`, `performance_local`
**Timeout:** 300s for individual tests
**Framework:** pytest with pytest-cov, pytest-timeout

### 3.4 Additional Technical Assumptions

- **Language:** Python 3.9+ (supports 3.9, 3.10, 3.11, 3.12)
- **CLI Framework:** Click 8.0+
- **NLP Libraries:** NLTK 3.8+, spaCy 3.7+, textstat 0.7.3+
- **ML/Transformers:** transformers 4.35+, torch 2.0+, sentence-transformers 2.0+
- **Linting:** ruff with E, F, W, I, UP, B, C4, SIM rules
- **Docstrings:** Google style with type hints
- **See:** `docs/technical-reference.md` for complete technical specifications

---

## 4. Epic List

| Epic | Title | Goal |
|------|-------|------|
| **1** | Foundation & Dimension Architecture | Transform WriteScore into a plugin-based architecture with self-registering dimensions |
| **2** | Advanced Dimensions & Scoring | Add sophisticated linguistic dimensions and percentile-anchored scoring accuracy |
| **3** | Content-Aware Analysis | Adapt analysis based on auto-detected content type for genre-appropriate scoring |
| **4** | Repository Extraction | Extract WriteScore into standalone GitHub repository with CI/CD |
| **5** | README Modernization | Revamp README to follow 2025 best practices for user-centric documentation |

---

## 5. Epic Details

### 5.1 Epic 1: Foundation & Dimension Architecture

**Goal:** Transform WriteScore from a monolithic analysis system into a plugin-based, self-registering architecture where dimensions declare their own metadata, weights, and scoring logic—enabling dynamic dimension discovery without core code modifications.

#### Story 1.1: Enhanced Dimension Base Contract

**As a** dimension developer,
**I want** dimensions to declare all metadata (weight, tiers, recommendations),
**so that** the algorithm can dynamically incorporate them without core code modifications.

**Acceptance Criteria:**
1. New `DimensionStrategy` ABC created in `dimensions/base_strategy.py`
2. Must include all required abstract methods and properties
3. Full type hints on all methods
4. Comprehensive docstrings with examples
5. No breaking changes to existing dimensions yet
6. Maintains backward compatibility with existing `DimensionAnalyzer` base class
7. Includes AST helper methods from existing base.py
8. Provides validation helpers for tier, weight, and score values

---

#### Story 1.2: Dimension Registry

**As a** system architect,
**I want** a central registry where dimensions self-register,
**so that** the core algorithm doesn't need modification when adding dimensions.

**Acceptance Criteria:**
1. Thread-safe class-based registry implementation (not singleton)
2. Dimensions can self-register during `__init__`
3. Registry prevents duplicate registrations with clear error messages
4. Supports retrieval by tier, name, or all dimensions
5. Includes clear() method for testing
6. Custom exceptions for registry errors (DimensionNotFoundError, DuplicateDimensionError)
7. Case-insensitive dimension name lookup with normalization
8. Comprehensive unit test coverage including thread safety tests
9. Provides __repr__ for debugging and module-level convenience functions

---

#### Story 1.3: Weight Validation Mediator

**As a** system architect,
**I want** weight distribution validated across all dimensions,
**so that** the total weights sum to 100% with proper tier distribution.

**Acceptance Criteria:**
1. WeightMediator class validates total weights sum to 100.0 (±0.1%)
2. Validates tier weight distribution matches expected ranges
3. Provides detailed validation report with per-tier breakdown
4. Integrates with DimensionRegistry for dimension discovery
5. Raises InvalidWeightError for weight violations

---

#### Story 1.4: Refactor Existing Dimensions

**As a** maintainer,
**I want** all existing dimensions to adopt the new DimensionStrategy contract,
**so that** the system uses the self-registration mechanism and dimensions own their scoring logic.

**Acceptance Criteria:**
1. All 10 dimensions refactored to extend DimensionStrategy
2. All dimensions self-register in __init__
3. All dimensions implement required properties (name, weight, tier, description)
4. Scoring logic moved from dual_score_calculator.py into calculate_score()
5. Recommendation logic extracted into get_recommendations()
6. Tier mappings defined in get_tiers()
7. All dimension unit tests updated and passing
8. Weight distribution normalized to 100-point scale
9. No breaking changes to existing analyze() method signatures

---

#### Story 1.4a: Split Multi-Concern Dimensions

**As a** maintainer,
**I want** multi-concern dimensions split into focused single-purpose dimensions,
**so that** scoring is more accurate and dimensions are easier to maintain.

**Acceptance Criteria:**
1. Perplexity dimension split into: ai_vocabulary, transition_marker, true_perplexity
2. Each new dimension follows DimensionStrategy contract
3. Combined weights equal original perplexity weight
4. All tests updated for new dimension structure

---

#### Story 1.5: Evidence Extraction

**As a** user analyzing documents,
**I want** line-by-line evidence extraction,
**so that** I can see exactly which lines contain AI patterns.

**Acceptance Criteria:**
1. Evidence extraction returns line numbers with context
2. Each evidence item includes problem type and specific replacement suggestion
3. Evidence grouped by dimension
4. Works with --detailed CLI flag

---

#### Story 1.16: Fix Dynamic Reporting Architecture

**As a** maintainer,
**I want** dynamic dimension loading to work correctly with reporting,
**so that** dimension profiles don't break output formatting.

**Acceptance Criteria:**
1. Report formatter handles variable dimension sets
2. Missing dimensions show as N/A rather than errors
3. Dimension order consistent across profiles

---

#### Story 1.17: Rename to WriteScore

**As a** product owner,
**I want** the tool rebranded from "AI Pattern Analyzer" to "WriteScore",
**so that** the name reflects the scoring-focused value proposition.

**Acceptance Criteria:**
1. Package renamed to `writescore`
2. CLI command changed to `writescore`
3. All documentation updated
4. Backward compatibility alias for transition period

---

### 5.2 Epic 2: Advanced Dimensions & Scoring

**Goal:** Expand WriteScore's detection capabilities with sophisticated linguistic dimensions (figurative language, pragmatic markers, semantic coherence) while improving scoring accuracy through percentile-anchored calibration and research-validated thresholds.

#### Story 2.1: Figurative Language Dimension

**As a** data analyst using the AI pattern analyzer,
**I want** to detect figurative language patterns (metaphors, similes, idioms) in text,
**so that** I can identify AI-generated content which systematically underuses figurative expressions.

**Acceptance Criteria:**
1. New `FigurativeLanguageDimension` class implements `DimensionStrategy` interface
2. Detects 3 types: similes (regex), idioms (lexicon), metaphors (embeddings)
3. Returns 0-100 score where higher = more human-like
4. Implements domain exception lists for technical literals
5. Processes 10k words in < 15 seconds
6. Auto-registers with `DimensionRegistry`
7. Unit tests achieve > 80% code coverage

---

#### Story 2.2: Pragmatic Markers Dimension

**As a** analyst,
**I want** to detect discourse markers and pragmatic signals,
**so that** I can identify AI text lacking natural conversational flow.

**Acceptance Criteria:**
1. Detects hedges, boosters, attitude markers, self-mentions
2. Uses 50+ pragmatic marker lexicon
3. Scores based on marker diversity and appropriateness
4. Handles domain-specific marker usage

---

#### Story 2.3: Semantic Coherence Dimension

**As a** developer implementing AI detection,
**I want** a semantic coherence dimension measuring topic consistency,
**so that** the analyzer can detect AI patterns related to semantic drift.

**Acceptance Criteria:**
1. Implements 4 coherence metrics: paragraph cohesion, topic consistency, discourse flow, conceptual depth
2. Uses sentence-transformers for embedding-based analysis
3. Falls back to lexical coherence when embeddings unavailable
4. Processing time < 2s per 10k words
5. Memory usage < 5GB

**Spike:** [SPIKE-001-story-2.3-semantic-coherence](../research/spikes/SPIKE-001-story-2.3-semantic-coherence/)

---

#### Story 2.4: Dimension Scoring Optimization

**As a** maintainer,
**I want** scoring algorithms optimized across all dimensions,
**so that** scores are accurate and consistent.

**Acceptance Criteria:**
1. All dimension scoring uses consistent 0-100 scale
2. Score calculations validated against known test cases
3. Edge cases handled (empty text, very short text)

**Spike:** [SPIKE-002-story-2.4-scoring-strategy](../research/spikes/SPIKE-002-story-2.4-scoring-strategy/)

---

#### Story 2.5: Percentile-Anchored Scoring

**As a** analyst,
**I want** scoring thresholds derived from validation datasets,
**so that** scores are calibrated against real human/AI distributions.

**Acceptance Criteria:**
1. Thresholds derived from 1000+ document corpus
2. Separate thresholds for human vs AI distributions
3. Recalibration command updates parameters
4. Version management for parameter changes

---

#### Story 2.6: Expand Pragmatic Markers Lexicon

**As a** analyst,
**I want** expanded pragmatic marker detection,
**so that** detection is more comprehensive.

**Acceptance Criteria:**
1. Lexicon expanded from 50 to 200+ markers
2. Markers categorized by function
3. Context-aware matching to reduce false positives

---

#### Story 2.9: Short Content Optimization

**As a** user analyzing short content,
**I want** accurate results for documents under 500 characters,
**so that** I can analyze tweets, bios, and short-form content.

**Acceptance Criteria:**
1. All dimensions handle content < 500 chars gracefully
2. Scoring adjusted for limited sample size
3. Clear indication when content is too short for reliable analysis

---

### 5.3 Epic 3: Content-Aware Analysis

**Goal:** Adapt WriteScore's analysis based on automatically-detected or user-specified content type (academic, technical, creative, blog, etc.), enabling genre-appropriate dimension weighting and scoring thresholds.

#### Story 3.1: Content Type Detection

**As a** technical writer analyzing documents,
**I want** the analyzer to detect or accept content type,
**so that** dimension weights can be adjusted appropriately for the genre.

**Acceptance Criteria:**
1. CLI `--content-type <type>` flag accepts: academic, professional_bio, personal_statement, blog, technical_docs, technical_book, business, creative, news
2. Auto-detection uses multi-feature voting ensemble
3. Confidence threshold ≥ 0.70 for auto-classification
4. Detection completes in < 0.05s for typical documents
5. AnalysisConfig and AnalysisResults include content_type fields

---

#### Story 3.2: Content-Aware Dimension Weighting

**As a** user,
**I want** dimension weights adjusted based on content type,
**so that** technical writing isn't penalized for appropriate formality.

**Acceptance Criteria:**
1. Weight adjustment profiles defined for each content type
2. Weights applied transparently with clear documentation
3. Original weights available for comparison

---

#### Story 3.3: Content-Aware Scoring Thresholds

**As a** user,
**I want** scoring thresholds adjusted for content type,
**so that** academic writing isn't flagged for appropriate passive voice usage.

**Acceptance Criteria:**
1. Genre-specific thresholds for key dimensions
2. Thresholds documented and configurable
3. Report shows applied content type

---

#### Stories 3.4-3.8: Additional Dimensions

| Story | Title | Description |
|-------|-------|-------------|
| 3.4 | Register Consistency Dimension | Detect inconsistent register/formality shifts |
| 3.5 | Person Consistency Dimension | Detect inconsistent POV (1st/2nd/3rd person) |
| 3.6 | Lexical Inflation Dimension | Detect unnecessarily complex vocabulary |
| 3.7 | Content Function Word Ratio | Analyze content vs function word distribution |
| 3.8 | Formulaic Language Appropriateness | Assess formulaic language in context |

---

### 5.4 Epic 4: Repository Extraction

**Goal:** Extract WriteScore into a standalone GitHub repository with industry-standard Python project structure, CI/CD pipeline, and automated release management.

#### Story 4.1: Repository Setup & Source Migration

**As a** maintainer,
**I want** WriteScore in a standalone repository,
**so that** it can be developed and versioned independently.

**Acceptance Criteria:**
1. New repository created at `/Users/jmagady/Dev/writescore`
2. src-layout per PEP 517/518
3. Single pyproject.toml with unified version
4. All source code migrated and functional

---

#### Story 4.2: Test & Documentation Migration

**As a** maintainer,
**I want** tests and docs migrated to the new repository,
**so that** the full development environment is self-contained.

**Acceptance Criteria:**
1. All tests migrated and passing
2. Documentation migrated to docs/
3. pytest configuration in pyproject.toml

---

#### Story 4.3: CI/CD & Release Automation

**As a** maintainer,
**I want** automated CI/CD pipeline,
**so that** releases are consistent and tested.

**Acceptance Criteria:**
1. GitHub Actions CI for test, lint, build
2. Automated release workflow on tag push
3. Changelog generation from commits

---

### 5.5 Epic 5: README Modernization

**Goal:** Transform README.md into a user-centric, 2025 best-practices document that accelerates user onboarding and establishes WriteScore as a credible project.

#### Story 5.1: Modernize README 2025 Best Practices

**As a** potential user landing on the repository,
**I want** a clear, scannable README,
**so that** I can understand the value and start using WriteScore in 30 seconds.

**Acceptance Criteria:**
1. README under 200 lines (core content)
2. Clear problem/solution statement in first paragraph
3. Quick-start section enables 30-second first use
4. Visual demo (GIF) showing CLI in action
5. Enhanced badge suite (version, Python, license, CI status)
6. Development history moved to separate document
7. Mobile-readable formatting
8. All links verified working

---

## 6. Checklist Results Report

*To be populated after PM checklist execution.*

---

## 7. Next Steps

### 7.1 Architect Prompt

> Review the WriteScore PRD and `docs/technical-reference.md`. Design the architecture for Epic 3 (Content-Aware Analysis), focusing on: (1) ContentTypeDetector module design with feature extractors, (2) Weight/threshold adjustment mechanism integrated with existing DimensionRegistry, (3) CLI integration with AnalysisConfig. Produce architecture document with component diagrams and interface specifications.

### 7.2 Developer Prompt

> Implement Story 3.1 (Content Type Detection) following the architecture document. Create `core/content_type_detector.py` with multi-feature voting ensemble. Add CLI `--content-type` flag. Ensure 85%+ test coverage.
