# Next Steps

This section provides handoff guidance for implementing new features and stories in WriteScore.

---

## 17.1 Story Manager Handoff

When creating new stories for WriteScore, provide this context:

### Required Reading

```
docs/architecture/index.md           # Architecture overview
docs/architecture/3-component-architecture.md  # Component structure
docs/architecture/9-coding-standards.md        # Code style requirements
docs/prd/index.md                    # Product requirements
```

### Key Integration Points

1. **New Dimensions**: Must implement `DimensionStrategy` interface and self-register
2. **CLI Changes**: Use Click framework, follow existing command patterns
3. **Scoring Changes**: Update `DualScoreCalculator` and weight mediator
4. **Output Changes**: Modify formatters in `cli/formatters.py`

### Story Checklist

For each story, verify:
- [ ] Follows existing architectural patterns
- [ ] Includes unit tests with >80% coverage
- [ ] Updates relevant documentation
- [ ] Passes all pre-commit hooks
- [ ] Does not break existing functionality (regression tests)

---

## 17.2 Developer Handoff

### Environment Setup

```bash
# Clone and setup
git clone <repo>
cd writescore

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Verify setup
uv run pytest -m "not slow"
```

### Development Workflow

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/story-X.X-description

# Make changes, run tests
uv run pytest tests/unit/
uv run ruff check src/

# Commit with conventional commits
git add .
git commit -m "feat(dimensions): add new dimension"

# Push and create PR to develop
git push -u origin feature/story-X.X-description
```

### Key Files to Know

| Purpose | Location |
|---------|----------|
| Main analyzer | `src/writescore/core/analyzer.py` |
| Dimension base | `src/writescore/dimensions/base_strategy.py` |
| Dimension registry | `src/writescore/core/dimension_registry.py` |
| Score calculation | `src/writescore/scoring/dual_score_calculator.py` |
| CLI entry | `src/writescore/cli/main.py` |
| Test fixtures | `tests/fixtures/` |

### Adding a New Dimension

1. Create `src/writescore/dimensions/my_dimension.py`
2. Implement `DimensionStrategy` interface
3. Add module-level instance for self-registration
4. Create `tests/unit/dimensions/test_my_dimension.py`
5. Update dimension profiles if needed

See `docs/architecture/3-component-architecture.md#35-dimension-self-registration-pattern` for full pattern.

---

## 17.3 QA Handoff

### Test Execution

```bash
# Full test suite (slow, ~5-10 min)
uv run pytest

# Fast tests only (~1 min)
uv run pytest -m "not slow"

# With coverage
uv run pytest --cov=src/writescore --cov-report=html

# Specific dimension
uv run pytest tests/unit/dimensions/test_perplexity.py -v
```

### Test Categories

| Marker | Purpose | Run Frequency |
|--------|---------|---------------|
| (none) | Standard unit tests | Every commit |
| `slow` | ML model tests | PR merge, nightly |
| `integration` | Cross-component tests | PR merge |
| `accuracy` | Validation corpus tests | Weekly |

### Validation Fixtures

Test fixtures in `tests/fixtures/`:
- `ai/` - Known AI-generated samples
- `human/` - Known human-written samples
- `mixed/` - Hybrid content
- `edge_cases/` - Short text, special characters, etc.

---

## 17.4 Current Priorities

Based on the PRD (see `docs/prd/5-epic-details.md`):

### Epic 1: Foundation (In Progress)
- Story 1.4: Refactor existing dimensions to DimensionStrategy
- Story 1.5: Evidence extraction for detailed output

### Epic 2: Advanced Dimensions (Next)
- Story 2.1: Figurative Language dimension
- Story 2.2: Pragmatic Markers expansion
- Story 2.3: Semantic Coherence optimization

### Epic 3: Content-Aware Analysis (Future)
- Story 3.1: Content type detection
- Story 3.2: Content-aware weighting

---

## 17.5 Related Documents

| Document | Purpose |
|----------|---------|
| `docs/prd/index.md` | Product requirements |
| `docs/architecture/index.md` | This architecture |
| `CLAUDE.md` | AI assistant guidelines |
| `docs/MIGRATION-v5.0.0.md` | Breaking changes from v4 |
| `docs/RECALIBRATION-GUIDE.md` | Score threshold tuning |
