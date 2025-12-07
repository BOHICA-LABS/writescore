# 3. Technical Assumptions

## 3.1 Repository Structure: Monorepo

Single repository containing all WriteScore components:
- `src/writescore/` - Main package (src-layout per PEP 517/518)
- `tests/` - Test suite (unit, integration, accuracy, performance)
- `docs/` - Documentation and stories
- `config/` - Scoring parameters and configuration

## 3.2 Service Architecture

**Local CLI Tool (Monolith)**

WriteScore is a self-contained command-line application with no external service dependencies:
- Single Python package installed via pip
- File-based history storage (`.ai-analysis-history/`)
- No database or network infrastructure required
- Entry point: `writescore` CLI command

## 3.3 Testing Requirements

**Full Testing Pyramid:**
- **Unit tests:** Per-module coverage (target: 80%+)
- **Integration tests:** Cross-module functionality
- **Accuracy tests:** Validation against human/AI document corpus
- **Performance tests:** Benchmarking analysis modes

**Test Markers:** `slow`, `integration`, `accuracy`, `performance_local`
**Timeout:** 300s for individual tests
**Framework:** pytest with pytest-cov, pytest-timeout

## 3.4 Additional Technical Assumptions

- **Language:** Python 3.9+ (supports 3.9, 3.10, 3.11, 3.12)
- **CLI Framework:** Click 8.0+
- **NLP Libraries:** NLTK 3.8+, spaCy 3.7+, textstat 0.7.3+
- **ML/Transformers:** transformers 4.35+, torch 2.0+, sentence-transformers 2.0+
- **Linting:** ruff with E, F, W, I, UP, B, C4, SIM rules
- **Docstrings:** Google style with type hints
- **See:** `docs/technical-reference.md` for complete technical specifications

---
