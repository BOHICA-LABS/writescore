# 15. Design Principles

## 15.1 Backward Compatibility

The package maintains backward compatibility through package-level exports:

```python
# Old way (still works)
from analyze_ai_patterns import AIPatternAnalyzer

# New way (recommended)
from writescore.core.analyzer import AIPatternAnalyzer

# Or use package import
from writescore import AIPatternAnalyzer
```

## 15.2 Dimension Analyzer Interface

All dimension analyzers implement the `DimensionAnalyzer` base class:

```python
class DimensionAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """Analyze text for this dimension"""
        pass

    @abstractmethod
    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """Calculate score for this dimension"""
        pass
```

## 15.3 Separation of Concerns

- **Core**: Orchestration and coordination
- **Dimensions**: Individual analysis algorithms
- **Scoring**: Dual-score calculation and interpretation
- **History**: Score tracking over time
- **Utils**: Shared helper functions
- **CLI**: User interface layer
- **Config**: Configuration loading and validation

## 15.4 Configuration Over Code

Behavioral parameters are externalized to declarative YAML configuration files rather than embedded in application logic.

### Principles

1. **Single Source of Truth**: All configurable values live in YAML files, not scattered through code
2. **Type-Safe Access**: Pydantic schemas validate configuration at load time
3. **Layered Overrides**: base.yaml -> environment.yaml -> environment variables
4. **Graceful Degradation**: Fallback to defaults when ConfigRegistry not initialized

### What Should Be Configuration

- Scoring thresholds and category boundaries
- Dimension profiles and weights
- Content-type specific settings
- Analysis mode parameters
- Feature flags

### What Should Remain Code

- Core algorithms and business logic
- Type definitions and interfaces
- Error handling patterns
- Test fixtures

### Example Pattern

```python
# WRONG - Magic numbers in code
if score >= 75:
    return "human"

# RIGHT - Value from configuration
threshold = ConfigRegistry.get(ScoringConfig).categories.human.min_threshold
if score >= threshold:
    return "human"

# With backward-compatible fallback
def get_human_threshold() -> int:
    try:
        return ConfigRegistry.get(ScoringConfig).categories.human.min_threshold
    except RuntimeError:
        return 75  # Default when ConfigRegistry not initialized
```

See [18. Configuration System](./18-configuration-system.md) for implementation details.
