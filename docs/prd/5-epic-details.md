# 5. Epic Details

## 5.1 Epic 1: Foundation & Dimension Architecture

**Goal:** Transform WriteScore from a monolithic analysis system into a plugin-based, self-registering architecture where dimensions declare their own metadata, weights, and scoring logic—enabling dynamic dimension discovery without core code modifications.

### Story 1.1: Enhanced Dimension Base Contract

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

### Story 1.2: Dimension Registry

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

### Story 1.3: Weight Validation Mediator

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

### Story 1.4: Refactor Existing Dimensions

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

### Story 1.4a: Split Multi-Concern Dimensions

**As a** maintainer,
**I want** multi-concern dimensions split into focused single-purpose dimensions,
**so that** scoring is more accurate and dimensions are easier to maintain.

**Acceptance Criteria:**
1. Perplexity dimension split into: ai_vocabulary, transition_marker, true_perplexity
2. Each new dimension follows DimensionStrategy contract
3. Combined weights equal original perplexity weight
4. All tests updated for new dimension structure

---

### Story 1.5: Evidence Extraction

**As a** user analyzing documents,
**I want** line-by-line evidence extraction,
**so that** I can see exactly which lines contain AI patterns.

**Acceptance Criteria:**
1. Evidence extraction returns line numbers with context
2. Each evidence item includes problem type and specific replacement suggestion
3. Evidence grouped by dimension
4. Works with --detailed CLI flag

---

### Story 1.16: Fix Dynamic Reporting Architecture

**As a** maintainer,
**I want** dynamic dimension loading to work correctly with reporting,
**so that** dimension profiles don't break output formatting.

**Acceptance Criteria:**
1. Report formatter handles variable dimension sets
2. Missing dimensions show as N/A rather than errors
3. Dimension order consistent across profiles

---

### Story 1.17: Rename to WriteScore

**As a** product owner,
**I want** the tool rebranded from "AI Pattern Analyzer" to "WriteScore",
**so that** the name reflects the scoring-focused value proposition.

**Acceptance Criteria:**
1. Package renamed to `writescore`
2. CLI command changed to `writescore`
3. All documentation updated
4. Backward compatibility alias for transition period

---

## 5.2 Epic 2: Advanced Dimensions & Scoring

**Goal:** Expand WriteScore's detection capabilities with sophisticated linguistic dimensions (figurative language, pragmatic markers, semantic coherence) while improving scoring accuracy through percentile-anchored calibration and research-validated thresholds.

### Story 2.1: Figurative Language Dimension

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

### Story 2.2: Pragmatic Markers Dimension

**As a** analyst,
**I want** to detect discourse markers and pragmatic signals,
**so that** I can identify AI text lacking natural conversational flow.

**Acceptance Criteria:**
1. Detects hedges, boosters, attitude markers, self-mentions
2. Uses 50+ pragmatic marker lexicon
3. Scores based on marker diversity and appropriateness
4. Handles domain-specific marker usage

---

### Story 2.3: Semantic Coherence Dimension

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

### Story 2.4: Dimension Scoring Optimization

**As a** maintainer,
**I want** scoring algorithms optimized across all dimensions,
**so that** scores are accurate and consistent.

**Acceptance Criteria:**
1. All dimension scoring uses consistent 0-100 scale
2. Score calculations validated against known test cases
3. Edge cases handled (empty text, very short text)

**Spike:** [SPIKE-002-story-2.4-scoring-strategy](../research/spikes/SPIKE-002-story-2.4-scoring-strategy/)

---

### Story 2.5: Percentile-Anchored Scoring

**As a** analyst,
**I want** scoring thresholds derived from validation datasets,
**so that** scores are calibrated against real human/AI distributions.

**Acceptance Criteria:**
1. Thresholds derived from 1000+ document corpus
2. Separate thresholds for human vs AI distributions
3. Recalibration command updates parameters
4. Version management for parameter changes

---

### Story 2.6: Expand Pragmatic Markers Lexicon

**As a** analyst,
**I want** expanded pragmatic marker detection,
**so that** detection is more comprehensive.

**Acceptance Criteria:**
1. Lexicon expanded from 50 to 200+ markers
2. Markers categorized by function
3. Context-aware matching to reduce false positives

---

### Story 2.9: Short Content Optimization

**As a** user analyzing short content,
**I want** accurate results for documents under 500 characters,
**so that** I can analyze tweets, bios, and short-form content.

**Acceptance Criteria:**
1. All dimensions handle content < 500 chars gracefully
2. Scoring adjusted for limited sample size
3. Clear indication when content is too short for reliable analysis

---

## 5.3 Epic 3: Content-Aware Analysis

**Goal:** Adapt WriteScore's analysis based on automatically-detected or user-specified content type (academic, technical, creative, blog, etc.), enabling genre-appropriate dimension weighting and scoring thresholds.

### Story 3.1: Content Type Detection

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

### Story 3.2: Content-Aware Dimension Weighting

**As a** user,
**I want** dimension weights adjusted based on content type,
**so that** technical writing isn't penalized for appropriate formality.

**Acceptance Criteria:**
1. Weight adjustment profiles defined for each content type
2. Weights applied transparently with clear documentation
3. Original weights available for comparison

---

### Story 3.3: Content-Aware Scoring Thresholds

**As a** user,
**I want** scoring thresholds adjusted for content type,
**so that** academic writing isn't flagged for appropriate passive voice usage.

**Acceptance Criteria:**
1. Genre-specific thresholds for key dimensions
2. Thresholds documented and configurable
3. Report shows applied content type

---

### Stories 3.4-3.8: Additional Dimensions

| Story | Title | Description |
|-------|-------|-------------|
| 3.4 | Register Consistency Dimension | Detect inconsistent register/formality shifts |
| 3.5 | Person Consistency Dimension | Detect inconsistent POV (1st/2nd/3rd person) |
| 3.6 | Lexical Inflation Dimension | Detect unnecessarily complex vocabulary |
| 3.7 | Content Function Word Ratio | Analyze content vs function word distribution |
| 3.8 | Formulaic Language Appropriateness | Assess formulaic language in context |

---

## 5.4 Epic 4: Repository Extraction

**Goal:** Extract WriteScore into a standalone GitHub repository with industry-standard Python project structure, CI/CD pipeline, and automated release management.

### Story 4.1: Repository Setup & Source Migration

**As a** maintainer,
**I want** WriteScore in a standalone repository,
**so that** it can be developed and versioned independently.

**Acceptance Criteria:**
1. New repository created at `/Users/jmagady/Dev/writescore`
2. src-layout per PEP 517/518
3. Single pyproject.toml with unified version
4. All source code migrated and functional

---

### Story 4.2: Test & Documentation Migration

**As a** maintainer,
**I want** tests and docs migrated to the new repository,
**so that** the full development environment is self-contained.

**Acceptance Criteria:**
1. All tests migrated and passing
2. Documentation migrated to docs/
3. pytest configuration in pyproject.toml

---

### Story 4.3: CI/CD & Release Automation

**As a** maintainer,
**I want** automated CI/CD pipeline,
**so that** releases are consistent and tested.

**Acceptance Criteria:**
1. GitHub Actions CI for test, lint, build
2. Automated release workflow on tag push
3. Changelog generation from commits

---

## 5.5 Epic 5: README Modernization

**Goal:** Transform README.md into a user-centric, 2025 best-practices document that accelerates user onboarding and establishes WriteScore as a credible project.

### Story 5.1: Modernize README 2025 Best Practices

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

## 5.6 Epic 6: Developer Experience & Security

**Goal:** Improve developer onboarding with streamlined setup options, enhance CI/CD with caching and comprehensive validation, and leverage GitHub Advanced Security features available free for public repositories.

### Story 6.1: Fix Installation Issues

**As a** user installing WriteScore via the Quick Start instructions,
**I want** complete dependency declarations and accurate documentation,
**so that** the package installs and runs correctly on first try.

**Acceptance Criteria:**
1. `scikit-learn>=1.3.0` added to pyproject.toml dependencies
2. README Quick Start includes spaCy model download step
3. Fresh install via `uv sync` succeeds without errors
4. `writescore analyze` works with all dimensions enabled

---

### Story 6.2: Developer Environment Setup

**As a** user or contributor to WriteScore,
**I want** streamlined environment setup with choice of native or containerized development,
**so that** I can start using or contributing quickly.

**Acceptance Criteria:**
1. Justfile created with common development commands (install, dev, test, lint, format, coverage, clean)
2. `.devcontainer/devcontainer.json` created for VS Code/GitHub Codespaces
3. README includes "Getting Started" section with options table (Native Just, Native Manual, Devcontainer, Codespaces)
4. Brewfile updated to include `just` for macOS developers
5. Environment-aware tests created that skip based on detected environment

---

### Story 6.3: README Requirements and Troubleshooting

**As a** user evaluating or installing WriteScore,
**I want** clear system requirements and troubleshooting guidance,
**so that** I can verify my system is compatible and resolve common issues.

**Acceptance Criteria:**
1. README includes "Requirements" section (Python, RAM, disk space)
2. README includes "Troubleshooting" section with common issues
3. Diagnostic commands documented for "command not found" issues
4. Solutions documented for slow first run, out of memory, missing models

---

### Story 6.4: CI Pipeline Improvements

**As a** contributor to WriteScore,
**I want** faster CI builds with comprehensive security scanning,
**so that** I get quicker feedback and catch security issues early.

**Acceptance Criteria:**
1. CI caches pip packages and spaCy model for faster builds
2. Python 3.11 added to test matrix (alongside 3.9, 3.10, 3.12)
3. Pre-commit job added to CI to enforce all local hooks
4. CodeQL workflow created for Python security analysis
5. Dependency review action added to flag vulnerable dependencies in PRs

---

### Story 6.5: Dependabot and Security Settings

**As a** maintainer of WriteScore,
**I want** automated dependency updates and a clear security policy,
**so that** vulnerabilities are patched promptly and security researchers know how to report issues.

**Acceptance Criteria:**
1. `.github/dependabot.yml` created for pip (weekly) and GitHub Actions (monthly) updates
2. Dev dependencies grouped to reduce PR noise
3. `SECURITY.md` created with vulnerability reporting instructions
4. Dependabot alerts and security updates enabled
5. Secret scanning and push protection verified (default for public repos)

---

### Story 6.6: README Status Badges

**As a** potential user or contributor evaluating WriteScore,
**I want** to see at-a-glance status indicators in the README,
**so that** I can quickly assess project health, security posture, and maintenance activity.

**Acceptance Criteria:**
1. Badges organized into logical rows (CI/Build, Code Quality, Security, Project Info, Maintenance)
2. CI badges: GitHub Actions, CodeQL, pre-commit enabled
3. Quality badges: Codecov coverage, Ruff linter, mypy type-checked
4. Security badges: Security policy, Dependabot enabled
5. Maintenance badges: Last commit, open issues, PRs welcome
6. All badges link to relevant detail pages

---

### Story 6.7: Contributor Experience

**As a** potential contributor to WriteScore,
**I want** clear community guidelines and structured templates for issues and PRs,
**so that** I know how to participate appropriately and provide useful information.

**Acceptance Criteria:**
1. `CODE_OF_CONDUCT.md` created using Contributor Covenant v2.1
2. `.github/ISSUE_TEMPLATE/bug_report.yml` created with structured form
3. `.github/ISSUE_TEMPLATE/feature_request.yml` created with structured form
4. `.github/PULL_REQUEST_TEMPLATE.md` created with description, type, and checklist
5. `CONTRIBUTING.md` updated to reference Justfile, devcontainer, and Code of Conduct

---

### Story 6.8: Mypy Type Compliance

**As a** contributor to WriteScore,
**I want** the codebase to pass mypy type checking,
**so that** type errors are caught early and the pre-commit hook doesn't block commits.

**Acceptance Criteria:**
1. All implicit Optional errors fixed (parameters with `= None` but no `Optional` type)
2. All missing type annotations added to untyped variables
3. All method override signature mismatches fixed in dimension subclasses
4. Mypy passes with `--ignore-missing-imports` flag
5. Pre-commit hook no longer requires `SKIP=mypy` to commit
6. Mypy configuration added to `pyproject.toml`

---

## 5.7 Epic 7: MCP Server & API Layer

**Goal:** Expose WriteScore functionality via Model Context Protocol (MCP) for seamless IDE integration, enabling AI assistants to analyze writing quality directly within development environments.

### Story 7.1: MCP Server Foundation

**As a** developer using an AI-powered IDE,
**I want** WriteScore exposed as an MCP server,
**so that** I can analyze document quality without leaving my development environment.

**Acceptance Criteria:**
1. MCP server implementation in `src/writescore/mcp/`
2. `analyze` tool exposed via MCP protocol
3. Server starts via `writescore mcp serve` command
4. Compatible with Claude Code and other MCP clients
5. Returns structured analysis results

---

### Story 7.2: MCP Resources & Prompts

**As a** developer,
**I want** MCP resources and prompts for common analysis workflows,
**so that** I can quickly access WriteScore capabilities.

**Acceptance Criteria:**
1. Resource exposing available dimension profiles
2. Resource exposing current configuration
3. Prompt templates for common analysis tasks
4. Documentation for MCP integration

---

## 5.8 Epic 8: Configuration & Extensibility

**Goal:** Externalize all tunable WriteScore parameters to declarative YAML configuration files, enabling dimension weights, scoring thresholds, analysis profiles, and model selections to be modified without code changes—supporting environment-specific behavior, operator tuning, and A/B testing of detection strategies.

### Story 8.1: Configuration Over Code

**As a** WriteScore developer or operator,
**I want** to externalize all tunable parameters into declarative YAML configuration files,
**so that** I can modify dimension weights, scoring thresholds, analysis profiles, and model selections without code changes, enabling easier tuning, environment-specific behavior, and non-developer adjustment of detection parameters.

**Acceptance Criteria:**
1. Config directory structure with `base.yaml` and environment-specific overrides
2. Pydantic schemas for all config sections with validation
3. Config loader with layered override support (base → environment → env vars)
4. ConfigRegistry singleton for centralized access
5. Dimension config externalized (weights, tiers, profiles)
6. Scoring thresholds externalized
7. Analysis mode parameters externalized
8. Model selections externalized
9. Environment-specific YAML files with layered merging
10. Secret handling via `${ENV_VAR}` pattern
11. Validation at load time with clear errors
12. Backward compatibility with fallback to hardcoded defaults
13. CLI integration with `--config-dir` flag
14. Testing support with `ConfigRegistry.reset()`
15. Documentation for config structure and customization
16. Content-type list defined in config (foundation for Epic 3.1)
17. Content-type dimension weights externalized (foundation for Epic 3.2)
18. Content-type scoring thresholds externalized (foundation for Epic 3.3)
19. Pydantic schemas for content-type configuration with validation

---

### Story 8.2: Custom Dimension Profiles

**As a** WriteScore operator,
**I want** to define custom dimension profiles in configuration,
**so that** I can create specialized analysis profiles for different use cases.

**Acceptance Criteria:**
1. Custom profiles defined in YAML under `dimensions.profiles`
2. Profiles can include any subset of available dimensions
3. CLI accepts custom profile names via `--profile`
4. Invalid dimension names in profiles raise clear errors
5. Documentation for creating custom profiles

---

### Story 8.3: Runtime Configuration Reload

**As a** WriteScore operator running long-lived processes,
**I want** to reload configuration without restarting,
**so that** I can adjust parameters in production without downtime.

**Acceptance Criteria:**
1. `ConfigRegistry.reload()` method for hot reload
2. Signal handler (SIGHUP) triggers reload in MCP server
3. Reload validates new config before applying
4. Failed reload keeps previous config with warning
5. Reload event logged with config diff summary

---
