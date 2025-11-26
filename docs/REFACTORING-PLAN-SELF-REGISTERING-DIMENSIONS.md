# AI Pattern Analyzer: Self-Registering Dimension Architecture Refactoring Plan

**Document Version:** 1.0
**Date:** 2025-11-03
**Status:** Proposed
**Author:** Claude Code (with Sarah - PO)

---

## Executive Summary

Transform the AI Pattern Analyzer from a monolithic, manually-coupled architecture to a self-registering, self-balancing plugin-based system using Gang of Four design patterns. This refactoring will enable dimension isolation, automatic weight validation, and dynamic reporting without requiring core code modifications when adding new analysis dimensions.

---

## Current Architecture Analysis

### Problems Identified

1. ❌ **Manual Dimension Instantiation** - Core analyzer manually instantiates all 10 dimensions (analyzer.py:151-160)
2. ❌ **Hardcoded Scoring Logic** - 847 lines of coupled dimension-specific logic in dual_score_calculator.py
3. ❌ **No Self-Registration** - Dimensions don't announce their presence or capabilities
4. ❌ **Missing Metadata** - Dimensions don't provide weights, tiers, or recommendations
5. ❌ **No Weight Validation** - System could accept invalid weight configurations (>100% or <100%)
6. ❌ **Static Reporting** - Must modify core code to add dimensions to reports
7. ❌ **Centralized Scoring** - Scoring logic lives outside dimensions, creating tight coupling

### Current Code Structure

```
analyzer.py (1026 lines)
├── Manual dimension instantiation (lines 151-160)
├── Hardcoded dimension method calls (lines 274-285)
└── Static result building (lines 304-396)

dual_score_calculator.py (847 lines)
├── Hardcoded weight assignments per dimension
├── Hardcoded scoring thresholds
└── Manual dimension result extraction

dimensions/
├── base.py - Simple ABC with analyze() and score()
├── perplexity.py
├── burstiness.py
├── structure.py
├── formatting.py
├── voice.py
├── syntactic.py
├── lexical.py
├── stylometric.py
├── advanced.py
└── sentiment.py
```

---

## Proposed Architecture: Self-Registering Dimension System

### Design Patterns Applied

| Pattern | Purpose | Implementation |
|---------|---------|----------------|
| **Registry Pattern** | Central dimension registry with self-registration | `DimensionRegistry` singleton |
| **Strategy Pattern** | Each dimension is independent, pluggable strategy | `DimensionStrategy` base class |
| **Mediator Pattern** | Algorithm coordinates dimensions, validates weights | `WeightMediator` class |
| **Factory Pattern** | Optional dimension creation abstraction | `DimensionFactory` (future) |
| **Observer Pattern** | Dimensions notify registry of state changes | Registry notifications |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DynamicAnalysisEngine                     │
│  - Orchestrates analysis across registered dimensions        │
│  - Validates weights before execution                        │
│  - Aggregates results dynamically                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─────────────────┐
                  │                 │
        ┌─────────▼────────┐  ┌────▼──────────────┐
        │ DimensionRegistry │  │  WeightMediator   │
        │   (Singleton)     │  │  - Validates      │
        │ - register()      │  │  - Balances       │
        │ - get_all()       │  │  - Reports        │
        │ - get_by_tier()   │  └───────────────────┘
        └─────────┬─────────┘
                  │
     ┌────────────┴────────────┐
     │  Self-registering       │
     │  on instantiation       │
     │                         │
┌────▼─────┐  ┌──────────┐  ┌──────────┐
│Perplexity│  │Burstiness│  │Structure │  ... (10 dimensions)
│Dimension │  │Dimension │  │Dimension │
└──────────┘  └──────────┘  └──────────┘
     │             │              │
     └─────────────┴──────────────┘
              │
    ┌─────────▼──────────┐
    │ DimensionStrategy  │
    │  (Enhanced Base)   │
    │ - dimension_name   │
    │ - weight          │
    │ - tier            │
    │ - analyze()       │
    │ - calculate_score()│
    │ - get_recommendations()│
    │ - get_tiers()     │
    └────────────────────┘
```

---

## Research Foundation

### Perplexity Research Summary

The proposed architecture leverages multiple Gang of Four patterns:

1. **Strategy Pattern** - Each dimension represents a different analysis strategy that can be swapped dynamically, allowing independent algorithm encapsulation
2. **Observer Pattern** - Enables self-registration without brittle registries; core algorithm acts as observable subject
3. **Factory Method** - Handles dimension instantiation while allowing subclasses to determine concrete types
4. **Mediator Pattern** - Coordinates weight validation and communication between dimensions without direct references
5. **Registry Pattern** - While not strictly GoF, commonly used for plugin architectures with self-registration

**Key Benefits:**
- Loose coupling through abstraction
- Open-closed principle (open for extension, closed for modification)
- Single responsibility (dimensions own their logic)
- Dependency inversion (depend on abstractions, not concretions)

**Sources:** DigitalOcean GoF Tutorial, Cornell CS Patterns, Stanford GoF Studies

---

## Epic: Self-Registering, Self-Balancing AI Pattern Analyzer

**Goal:** Transform the analyzer into a plugin-based architecture where dimensions self-register, provide complete metadata, and the algorithm dynamically balances and validates itself.

**Business Value:**
- ✅ Add new dimensions without modifying core code
- ✅ Automatic weight validation prevents configuration errors
- ✅ Dimension isolation improves testing and maintenance
- ✅ Dynamic reporting generation
- ✅ Self-documenting system (dimensions declare capabilities)

**Total Story Points:** 73
**Estimated Timeline:** 4-6 sprints

---

## 📦 STORY 1: Create Enhanced Dimension Base Contract

**Priority:** P0 (Foundation)
**Story Points:** 3
**Dependencies:** None

### Description

**As a** dimension developer
**I want** dimensions to declare all metadata (weight, tiers, recommendations)
**So that** the algorithm can dynamically incorporate them

### Acceptance Criteria

1. New `DimensionStrategy` ABC created in `dimensions/base_strategy.py`
2. Must include all required abstract methods and properties
3. Full type hints on all methods
4. Comprehensive docstrings with examples
5. No breaking changes to existing dimensions yet

### Implementation Details

```python
# dimensions/base_strategy.py

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any

class DimensionStrategy(ABC):
    """
    Enhanced base contract for self-contained analysis dimensions.

    Each dimension must:
    1. Self-register with DimensionRegistry on instantiation
    2. Declare its weight contribution (0-100 total across all dimensions)
    3. Provide tier grouping for organization
    4. Implement analysis logic
    5. Own its scoring calculations
    6. Generate actionable recommendations
    7. Define score tier mappings

    Example:
        class MyCustomDimension(DimensionStrategy):
            def __init__(self):
                super().__init__()
                DimensionRegistry.register(self)

            @property
            def dimension_name(self) -> str:
                return "my_custom"

            @property
            def weight(self) -> float:
                return 8.0  # 8 points out of 200 total

            # ... implement other abstract methods
    """

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """
        Unique dimension identifier (lowercase, underscore-separated).

        Returns:
            Unique string identifier for this dimension
        """
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        """
        Contribution weight for overall scoring (0-100 scale).

        All dimension weights must sum to 100.0 (validated by WeightMediator).

        Returns:
            Float representing this dimension's weight (e.g., 10.0 = 10 points)
        """
        pass

    @property
    @abstractmethod
    def tier(self) -> str:
        """
        Grouping tier for organization and reporting.

        Valid tiers:
        - ADVANCED: Highest accuracy detection metrics (ML-based, GLTR, etc.)
        - CORE: Proven AI signatures (burstiness, perplexity, formatting)
        - SUPPORTING: Context and quality indicators
        - STRUCTURAL: AST-based structural patterns

        Returns:
            Tier string (must be one of the above)
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this dimension analyzes.

        Returns:
            Brief description (1-2 sentences)
        """
        pass

    @abstractmethod
    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """
        Perform dimension-specific analysis on text.

        Args:
            text: Full document text
            lines: Text split into lines
            **kwargs: Optional analysis parameters (word_count, etc.)

        Returns:
            Dict containing raw metrics specific to this dimension.
            Keys should be descriptive and unique.

        Example:
            {
                'ai_vocabulary_count': 15,
                'ai_vocabulary_per_1k': 3.2,
                'formulaic_transitions_count': 8,
                'specific_words': ['delve', 'leverage', ...]
            }
        """
        pass

    @abstractmethod
    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Convert raw metrics into a 0-100 score.

        This is dimension-owned scoring logic. The score should represent
        "human-likeness" where 100 = most human-like, 0 = most AI-like.

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        pass

    @abstractmethod
    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations based on analysis.

        Recommendations should:
        - Be specific and actionable
        - Explain how to improve the score
        - Include concrete examples when possible
        - Focus on increasing "human-likeness" or reducing "AI detection"

        Args:
            score: Current score from calculate_score()
            metrics: Raw metrics from analyze()

        Returns:
            List of recommendation strings, ordered by priority

        Example:
            [
                "Reduce AI vocabulary from 3.2 to <1.0 per 1k words",
                "Replace 'delve', 'leverage', 'robust' with simpler alternatives",
                "Add more domain-specific terminology"
            ]
        """
        pass

    @abstractmethod
    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """
        Define score tier ranges for interpretation.

        Tiers map score ranges to quality labels. Common tiers:
        - excellent: 90-100 (minimal AI signatures)
        - good: 75-89 (natural with minor tells)
        - acceptable: 50-74 (mixed signals)
        - poor: 0-49 (obvious AI patterns)

        Returns:
            Dict mapping tier name to (min_score, max_score) tuple

        Example:
            {
                'excellent': (90, 100),
                'good': (75, 89),
                'acceptable': (50, 74),
                'poor': (0, 49)
            }
        """
        pass

    def get_impact_level(self, score: float) -> str:
        """
        Calculate impact level based on gap from perfect score.

        Args:
            score: Current dimension score

        Returns:
            Impact level: HIGH, MEDIUM, LOW, or NONE
        """
        gap = 100.0 - score
        if gap < 5.0:
            return "NONE"
        elif gap < 15.0:
            return "LOW"
        elif gap < 30.0:
            return "MEDIUM"
        else:
            return "HIGH"
```

### Tasks

- [ ] Create `dimensions/base_strategy.py` with full implementation
- [ ] Add comprehensive docstrings with examples
- [ ] Include type hints on all methods/properties
- [ ] Add validation helpers (tier validation, score range validation)
- [ ] Write unit tests for base class methods
- [ ] Update `dimensions/__init__.py` to export new base class

### Verification

```python
# Test that base class is properly abstract
def test_cannot_instantiate_base():
    with pytest.raises(TypeError):
        DimensionStrategy()

# Test tier validation
def test_tier_validation():
    class TestDimension(DimensionStrategy):
        @property
        def tier(self):
            return "INVALID_TIER"

    # Should fail validation
    ...
```

---

## 📦 STORY 2: Implement Dimension Registry (Registry Pattern)

**Priority:** P0 (Foundation)
**Story Points:** 5
**Dependencies:** Story 1

### Description

**As a** system architect
**I want** a central registry where dimensions self-register
**So that** the core algorithm doesn't need modification when adding dimensions

### Acceptance Criteria

1. Thread-safe singleton implementation
2. Dimensions can self-register during `__init__`
3. Registry prevents duplicate registrations
4. Supports retrieval by tier, name, or all dimensions
5. Includes clear() method for testing
6. Comprehensive unit test coverage

### Implementation Details

```python
# core/dimension_registry.py

import threading
from typing import Dict, List, Optional
from writescore.dimensions.base_strategy import DimensionStrategy

class DimensionRegistry:
    """
    Thread-safe singleton registry for dimension self-registration.

    Dimensions register themselves during instantiation:

        class MyDimension(DimensionStrategy):
            def __init__(self):
                super().__init__()
                DimensionRegistry.register(self)

    The registry provides discovery and retrieval of registered dimensions.
    """

    _instance: Optional['DimensionRegistry'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._dimensions: Dict[str, DimensionStrategy] = {}
                    cls._instance._tiers: Dict[str, List[str]] = {
                        'ADVANCED': [],
                        'CORE': [],
                        'SUPPORTING': [],
                        'STRUCTURAL': []
                    }
        return cls._instance

    @classmethod
    def register(cls, dimension: DimensionStrategy) -> bool:
        """
        Register a dimension with the registry.

        Args:
            dimension: Instance of DimensionStrategy to register

        Returns:
            True if registered successfully, False if already registered

        Raises:
            ValueError: If dimension has invalid tier or missing required properties
        """
        instance = cls()

        # Validation
        name = dimension.dimension_name
        if not name:
            raise ValueError("Dimension must have a non-empty dimension_name")

        tier = dimension.tier
        if tier not in instance._tiers:
            raise ValueError(f"Invalid tier '{tier}'. Must be one of: {list(instance._tiers.keys())}")

        weight = dimension.weight
        if weight < 0 or weight > 100:
            raise ValueError(f"Weight must be 0-100, got {weight}")

        with cls._lock:
            # Check for duplicate
            if name in instance._dimensions:
                return False

            # Register
            instance._dimensions[name] = dimension
            instance._tiers[tier].append(name)

        return True

    @classmethod
    def get(cls, dimension_name: str) -> Optional[DimensionStrategy]:
        """
        Retrieve a dimension by name.

        Args:
            dimension_name: Name of the dimension to retrieve

        Returns:
            DimensionStrategy instance or None if not found
        """
        instance = cls()
        return instance._dimensions.get(dimension_name)

    @classmethod
    def get_all(cls) -> List[DimensionStrategy]:
        """
        Retrieve all registered dimensions.

        Returns:
            List of all registered DimensionStrategy instances
        """
        instance = cls()
        return list(instance._dimensions.values())

    @classmethod
    def get_by_tier(cls, tier: str) -> List[DimensionStrategy]:
        """
        Retrieve all dimensions in a specific tier.

        Args:
            tier: Tier name (ADVANCED, CORE, SUPPORTING, STRUCTURAL)

        Returns:
            List of DimensionStrategy instances in the specified tier
        """
        instance = cls()
        if tier not in instance._tiers:
            raise ValueError(f"Invalid tier '{tier}'")

        dimension_names = instance._tiers[tier]
        return [instance._dimensions[name] for name in dimension_names]

    @classmethod
    def get_count(cls) -> int:
        """
        Get the count of registered dimensions.

        Returns:
            Number of registered dimensions
        """
        instance = cls()
        return len(instance._dimensions)

    @classmethod
    def get_tiers_summary(cls) -> Dict[str, int]:
        """
        Get count of dimensions per tier.

        Returns:
            Dict mapping tier name to count of dimensions
        """
        instance = cls()
        return {tier: len(names) for tier, names in instance._tiers.items()}

    @classmethod
    def clear(cls):
        """
        Clear all registered dimensions.

        This is primarily for testing purposes. Use with caution.
        """
        instance = cls()
        with cls._lock:
            instance._dimensions.clear()
            for tier in instance._tiers:
                instance._tiers[tier].clear()
```

### Tasks

- [ ] Create `core/dimension_registry.py`
- [ ] Implement singleton pattern with thread safety
- [ ] Add registration with validation
- [ ] Add retrieval methods (get, get_all, get_by_tier)
- [ ] Add tier summary and count methods
- [ ] Implement clear() for testing
- [ ] Write comprehensive unit tests
- [ ] Add docstring examples
- [ ] Performance test with 100+ dimensions

### Verification

```python
# Test singleton behavior
def test_registry_is_singleton():
    r1 = DimensionRegistry()
    r2 = DimensionRegistry()
    assert r1 is r2

# Test registration
def test_dimension_registration():
    DimensionRegistry.clear()
    dim = MockDimension()
    assert DimensionRegistry.register(dim) == True
    assert DimensionRegistry.get_count() == 1

# Test duplicate prevention
def test_duplicate_registration():
    DimensionRegistry.clear()
    dim1 = MockDimension()
    dim2 = MockDimension()  # Same name
    assert DimensionRegistry.register(dim1) == True
    assert DimensionRegistry.register(dim2) == False

# Test tier retrieval
def test_get_by_tier():
    DimensionRegistry.clear()
    core_dim = MockDimension(tier='CORE')
    advanced_dim = MockDimension(tier='ADVANCED', name='advanced_mock')

    DimensionRegistry.register(core_dim)
    DimensionRegistry.register(advanced_dim)

    core_dims = DimensionRegistry.get_by_tier('CORE')
    assert len(core_dims) == 1
    assert core_dims[0].dimension_name == 'mock'
```

---

## 📦 STORY 3: Create Weight Validation Mediator

**Priority:** P0 (Foundation)
**Story Points:** 5
**Dependencies:** Story 1, Story 2

### Description

**As a** system operator
**I want** automatic weight validation
**So that** dimensions can't exceed 100% total weight

### Acceptance Criteria

1. Validates all dimension weights sum to 100.0 (±0.1% tolerance)
2. Detects negative weights
3. Detects individual weights > 100
4. Provides detailed error messages
5. Suggests auto-rebalancing when invalid
6. Returns comprehensive validation report

### Implementation Details

```python
# core/weight_mediator.py

from typing import Dict, List, Any, Optional
from writescore.core.dimension_registry import DimensionRegistry

class WeightValidationError(Exception):
    """Raised when dimension weights are invalid"""
    pass

class WeightMediator:
    """
    Validates and balances dimension weights.

    Ensures that all registered dimensions have valid weights that sum to 100.0.
    Provides detailed error reporting and rebalancing suggestions.
    """

    TOLERANCE = 0.1  # ±0.1% tolerance for floating point arithmetic

    def __init__(self, registry: Optional[DimensionRegistry] = None):
        """
        Initialize mediator.

        Args:
            registry: DimensionRegistry instance (uses singleton if None)
        """
        self.registry = registry or DimensionRegistry()
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

    def validate_weights(self) -> bool:
        """
        Ensure weights sum to 100% (within tolerance).

        Performs the following validations:
        1. Total weight sums to 100.0 (±0.1%)
        2. No dimension has negative weight
        3. No dimension has weight > 100
        4. At least one dimension is registered

        Returns:
            True if all validations pass, False otherwise
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()

        dimensions = self.registry.get_all()

        # Check 1: At least one dimension registered
        if not dimensions:
            self.validation_errors.append("No dimensions registered")
            return False

        # Check 2: Individual weight validation
        for dim in dimensions:
            weight = dim.weight

            if weight < 0:
                self.validation_errors.append(
                    f"Dimension '{dim.dimension_name}' has negative weight: {weight}"
                )

            if weight > 100:
                self.validation_errors.append(
                    f"Dimension '{dim.dimension_name}' has weight > 100: {weight}"
                )

            if weight == 0:
                self.validation_warnings.append(
                    f"Dimension '{dim.dimension_name}' has zero weight (will be ignored)"
                )

        # Check 3: Total weight validation
        total_weight = sum(d.weight for d in dimensions)
        difference = abs(total_weight - 100.0)

        if difference > self.TOLERANCE:
            self.validation_errors.append(
                f"Total weight is {total_weight:.2f}%, expected 100.0% "
                f"(difference: {total_weight - 100.0:+.2f}%)"
            )

        return len(self.validation_errors) == 0

    def get_total_weight(self) -> float:
        """
        Calculate total weight across all dimensions.

        Returns:
            Sum of all dimension weights
        """
        dimensions = self.registry.get_all()
        return sum(d.weight for d in dimensions)

    def suggest_rebalancing(self) -> Dict[str, float]:
        """
        Suggest weight adjustments to reach 100% total.

        Strategy: Proportionally scale all weights to sum to 100.0

        Returns:
            Dict mapping dimension name to suggested weight
        """
        dimensions = self.registry.get_all()

        if not dimensions:
            return {}

        total_weight = self.get_total_weight()

        if total_weight == 0:
            # Equal distribution if all weights are 0
            equal_weight = 100.0 / len(dimensions)
            return {d.dimension_name: equal_weight for d in dimensions}

        # Proportional scaling
        scale_factor = 100.0 / total_weight
        return {
            d.dimension_name: d.weight * scale_factor
            for d in dimensions
        }

    def get_validation_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive validation status report.

        Returns:
            Dict containing:
            - is_valid: bool
            - total_weight: float
            - expected_weight: float
            - difference: float
            - dimension_weights: Dict[str, float]
            - errors: List[str]
            - warnings: List[str]
            - suggested_rebalancing: Dict[str, float] (if invalid)
        """
        is_valid = self.validate_weights()
        total_weight = self.get_total_weight()
        dimensions = self.registry.get_all()

        report = {
            'is_valid': is_valid,
            'total_weight': round(total_weight, 2),
            'expected_weight': 100.0,
            'difference': round(total_weight - 100.0, 2),
            'tolerance': self.TOLERANCE,
            'dimension_count': len(dimensions),
            'dimension_weights': {
                d.dimension_name: d.weight
                for d in dimensions
            },
            'dimensions_by_tier': self._get_weights_by_tier(),
            'errors': self.validation_errors.copy(),
            'warnings': self.validation_warnings.copy()
        }

        if not is_valid:
            report['suggested_rebalancing'] = self.suggest_rebalancing()

        return report

    def _get_weights_by_tier(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate weight distribution by tier.

        Returns:
            Dict mapping tier to {total_weight, dimensions}
        """
        tiers = ['ADVANCED', 'CORE', 'SUPPORTING', 'STRUCTURAL']
        result = {}

        for tier in tiers:
            dimensions = self.registry.get_by_tier(tier)
            total = sum(d.weight for d in dimensions)
            result[tier] = {
                'total_weight': round(total, 2),
                'dimension_count': len(dimensions),
                'dimensions': [d.dimension_name for d in dimensions]
            }

        return result

    def require_valid(self):
        """
        Raise exception if weights are invalid.

        Raises:
            WeightValidationError: If validation fails
        """
        if not self.validate_weights():
            report = self.get_validation_report()
            error_msg = f"Weight validation failed:\n"
            error_msg += f"  Total: {report['total_weight']}% (expected 100.0%)\n"
            error_msg += f"  Errors:\n"
            for err in self.validation_errors:
                error_msg += f"    - {err}\n"

            raise WeightValidationError(error_msg)
```

### Tasks

- [ ] Create `core/weight_mediator.py`
- [ ] Implement weight validation logic
- [ ] Add error and warning collection
- [ ] Implement rebalancing suggestions
- [ ] Create comprehensive validation report
- [ ] Add require_valid() exception method
- [ ] Write unit tests for all validation scenarios
- [ ] Add integration tests with registry

### Verification

```python
# Test valid weights
def test_valid_weights():
    DimensionRegistry.clear()
    MockDimension(weight=50.0, name='dim1')
    MockDimension(weight=50.0, name='dim2')

    mediator = WeightMediator()
    assert mediator.validate_weights() == True

# Test invalid total
def test_invalid_total():
    DimensionRegistry.clear()
    MockDimension(weight=60.0, name='dim1')
    MockDimension(weight=50.0, name='dim2')

    mediator = WeightMediator()
    assert mediator.validate_weights() == False
    assert len(mediator.validation_errors) > 0

# Test rebalancing suggestion
def test_suggest_rebalancing():
    DimensionRegistry.clear()
    MockDimension(weight=60.0, name='dim1')
    MockDimension(weight=60.0, name='dim2')

    mediator = WeightMediator()
    suggestions = mediator.suggest_rebalancing()

    assert suggestions['dim1'] == 50.0
    assert suggestions['dim2'] == 50.0
```

---

## 📦 STORY 4: Refactor Existing Dimensions to Self-Register

**Priority:** P1 (Enablement)
**Story Points:** 21
**Dependencies:** Stories 1-3

### Description

**As a** maintainer
**I want** all existing dimensions to adopt the new contract
**So that** the system uses the self-registration mechanism

### Dimensions to Refactor

1. PerplexityAnalyzer → PerplexityDimension
2. BurstinessAnalyzer → BurstinessDimension
3. StructureAnalyzer → StructureDimension
4. FormattingAnalyzer → FormattingDimension
5. VoiceAnalyzer → VoiceDimension
6. SyntacticAnalyzer → SyntacticDimension
7. LexicalAnalyzer → LexicalDimension
8. StylometricAnalyzer → StylometricDimension
9. AdvancedAnalyzer → AdvancedDimension
10. SentimentAnalyzer → SentimentDimension

### Weight Distribution (200 total points → normalized to 100)

Based on current `dual_score_calculator.py`:

| Tier | Dimension | Old Points | New Weight | Percentage |
|------|-----------|------------|------------|------------|
| **ADVANCED** | GLTR Token Ranking | 12 | 6.0 | 6% |
| ADVANCED | HDD/Yule's K | 8 | 4.0 | 4% |
| ADVANCED | MATTR | 12 | 6.0 | 6% |
| ADVANCED | RTTR | 8 | 4.0 | 4% |
| ADVANCED | AI Detection Ensemble | 10 | 5.0 | 5% |
| ADVANCED | Stylometric Markers | 10 | 5.0 | 5% |
| ADVANCED | Syntactic Complexity | 4 | 2.0 | 2% |
| ADVANCED | Multi-Model Perplexity | 6 | 3.0 | 3% |
| **CORE** | Burstiness | 12 | 6.0 | 6% |
| CORE | Perplexity | 10 | 5.0 | 5% |
| CORE | Formatting | 8 | 4.0 | 4% |
| CORE | Voice | 10 | 5.0 | 5% |
| CORE | Structure | 8 | 4.0 | 4% |
| CORE | Technical Depth | 6 | 3.0 | 3% |
| CORE | Bold/Italic | 6 | 3.0 | 3% |
| CORE | List Usage | 4 | 2.0 | 2% |
| CORE | Punctuation | 4 | 2.0 | 2% |
| CORE | Whitespace | 4 | 2.0 | 2% |
| CORE | Heading Hierarchy | 2 | 1.0 | 1% |
| **SUPPORTING** | Lexical Diversity | 6 | 3.0 | 3% |
| SUPPORTING | MTLD | 6 | 3.0 | 3% |
| SUPPORTING | Syntactic Repetition | 4 | 2.0 | 2% |
| SUPPORTING | Paragraph CV | 6 | 3.0 | 3% |
| SUPPORTING | Section Variance | 6 | 3.0 | 3% |
| SUPPORTING | List Depth | 4 | 2.0 | 2% |
| SUPPORTING | Subsection Asymmetry | 6 | 3.0 | 3% |
| SUPPORTING | Heading Length | 4 | 2.0 | 2% |
| SUPPORTING | Heading Depth Nav | 4 | 2.0 | 2% |
| **STRUCTURAL** | Blockquote | 3 | 1.5 | 1.5% |
| STRUCTURAL | Link Anchor | 2 | 1.0 | 1% |
| STRUCTURAL | Punctuation Spacing | 2 | 1.0 | 1% |
| STRUCTURAL | List AST | 2 | 1.0 | 1% |
| STRUCTURAL | Code AST | 1 | 0.5 | 0.5% |
| **TOTAL** | | **200** | **100.0** | **100%** |

### Example Refactored Dimension

```python
# dimensions/perplexity.py

from typing import Dict, List, Tuple, Any
from writescore.dimensions.base_strategy import DimensionStrategy
from writescore.core.dimension_registry import DimensionRegistry
import re

class PerplexityDimension(DimensionStrategy):
    """
    Analyzes vocabulary predictability and AI-specific word patterns.

    Detects:
    - AI-typical vocabulary (delve, leverage, robust, harness, etc.)
    - Formulaic transitions (Furthermore, Moreover, Additionally, etc.)
    - Vocabulary predictability

    Higher scores = more human-like vocabulary
    Lower scores = AI-typical word choices
    """

    # AI vocabulary patterns
    AI_VOCAB_PATTERNS = {
        r'\bdelv(e|es|ing)\b': ['explore', 'examine', 'investigate'],
        r'\brobust(ness)?\b': ['reliable', 'powerful', 'solid'],
        r'\bleverag(e|es|ing)\b': ['use', 'apply', 'employ'],
        # ... (all patterns from original)
    }

    # Formulaic transitions
    FORMULAIC_TRANSITIONS = [
        r'\bFurthermore,\b',
        r'\bMoreover,\b',
        r'\bAdditionally,\b',
        # ... (all patterns from original)
    ]

    def __init__(self):
        """Initialize and self-register with registry."""
        super().__init__()

        # Compile patterns for performance
        self._vocab_compiled = {
            re.compile(pattern, re.IGNORECASE): replacements
            for pattern, replacements in self.AI_VOCAB_PATTERNS.items()
        }
        self._transition_compiled = [
            re.compile(pattern) for pattern in self.FORMULAIC_TRANSITIONS
        ]

        # Self-register
        DimensionRegistry.register(self)

    # ============= Metadata Properties =============

    @property
    def dimension_name(self) -> str:
        return "perplexity"

    @property
    def weight(self) -> float:
        return 5.0  # 5% of total score (was 10 points out of 200)

    @property
    def tier(self) -> str:
        return "CORE"

    @property
    def description(self) -> str:
        return "Analyzes vocabulary predictability and AI-typical word patterns"

    # ============= Analysis Methods =============

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """
        Analyze text for perplexity indicators.

        Returns:
            {
                'ai_vocabulary': {
                    'count': int,
                    'per_1k': float,
                    'words': List[str],
                    'instances': List[Dict]  # word, line_num, context
                },
                'formulaic_transitions': {
                    'count': int,
                    'per_1k': float,
                    'transitions': List[str],
                    'instances': List[Dict]  # phrase, line_num, context
                }
            }
        """
        word_count = kwargs.get('word_count', len(text.split()))

        # Detect AI vocabulary
        ai_vocab_instances = []
        for pattern, replacements in self._vocab_compiled.items():
            for match in pattern.finditer(text):
                ai_vocab_instances.append({
                    'word': match.group(),
                    'position': match.start(),
                    'suggestions': replacements
                })

        # Detect formulaic transitions
        transition_instances = []
        for pattern in self._transition_compiled:
            for match in pattern.finditer(text):
                transition_instances.append({
                    'phrase': match.group(),
                    'position': match.start()
                })

        # Calculate per-1k rates
        ai_vocab_count = len(ai_vocab_instances)
        transition_count = len(transition_instances)

        ai_vocab_per_1k = (ai_vocab_count / word_count * 1000) if word_count > 0 else 0
        transition_per_1k = (transition_count / word_count * 1000) if word_count > 0 else 0

        return {
            'ai_vocabulary': {
                'count': ai_vocab_count,
                'per_1k': ai_vocab_per_1k,
                'words': [inst['word'] for inst in ai_vocab_instances],
                'instances': ai_vocab_instances[:20]  # Limit for performance
            },
            'formulaic_transitions': {
                'count': transition_count,
                'per_1k': transition_per_1k,
                'transitions': [inst['phrase'] for inst in transition_instances],
                'instances': transition_instances[:15]
            }
        }

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on perplexity metrics.

        Scoring:
        - AI vocab < 1.0 per 1k: 100 (excellent)
        - AI vocab < 3.0 per 1k: 75 (good)
        - AI vocab < 5.0 per 1k: 50 (acceptable)
        - AI vocab >= 5.0 per 1k: 25 (poor)

        Formulaic transitions penalty: -5 points per transition
        """
        ai_vocab = metrics.get('ai_vocabulary', {})
        formulaic = metrics.get('formulaic_transitions', {})

        ai_vocab_per_1k = ai_vocab.get('per_1k', 0)
        transition_count = formulaic.get('count', 0)

        # Base score from vocabulary
        if ai_vocab_per_1k < 1.0:
            score = 100.0
        elif ai_vocab_per_1k < 3.0:
            score = 75.0
        elif ai_vocab_per_1k < 5.0:
            score = 50.0
        else:
            score = 25.0

        # Penalty for formulaic transitions
        transition_penalty = min(transition_count * 5, 50)  # Max -50
        score -= transition_penalty

        return max(0.0, min(100.0, score))

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        ai_vocab = metrics.get('ai_vocabulary', {})
        formulaic = metrics.get('formulaic_transitions', {})

        # AI vocabulary recommendations
        ai_vocab_per_1k = ai_vocab.get('per_1k', 0)
        if ai_vocab_per_1k > 1.0:
            recommendations.append(
                f"Reduce AI vocabulary from {ai_vocab_per_1k:.1f} to <1.0 per 1k words"
            )

            # Specific words to replace
            words = ai_vocab.get('words', [])
            if words:
                unique_words = list(set(words[:10]))
                recommendations.append(
                    f"Replace these AI words: {', '.join(unique_words)}"
                )

        # Transition recommendations
        transition_count = formulaic.get('count', 0)
        if transition_count > 0:
            recommendations.append(
                f"Replace {transition_count} formulaic transitions with natural connectors"
            )
            recommendations.append(
                "Use simpler transitions: 'Also', 'Plus', 'And', 'But', 'Still'"
            )

        return recommendations

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """Define score tiers."""
        return {
            'excellent': (90.0, 100.0),
            'good': (75.0, 89.9),
            'acceptable': (50.0, 74.9),
            'poor': (0.0, 49.9)
        }
```

### Tasks

For EACH dimension:
- [ ] Refactor to extend `DimensionStrategy`
- [ ] Add self-registration in `__init__`
- [ ] Implement all required properties (name, weight, tier, description)
- [ ] Move scoring logic from `dual_score_calculator.py` into `calculate_score()`
- [ ] Extract recommendation logic into `get_recommendations()`
- [ ] Define tier mappings in `get_tiers()`
- [ ] Update existing `analyze()` method to return Dict format
- [ ] Update unit tests to test new interface
- [ ] Maintain backward compatibility with old interface (optional)

Checklist:
- [ ] PerplexityDimension
- [ ] BurstinessDimension
- [ ] StructureDimension
- [ ] FormattingDimension
- [ ] VoiceDimension
- [ ] SyntacticDimension
- [ ] LexicalDimension
- [ ] StylometricDimension
- [ ] AdvancedDimension
- [ ] SentimentDimension

### Verification

After refactoring each dimension:
```python
# Test self-registration
def test_dimension_registers_on_init():
    DimensionRegistry.clear()
    dim = PerplexityDimension()
    assert DimensionRegistry.get_count() == 1
    assert DimensionRegistry.get('perplexity') is not None

# Test metadata
def test_dimension_metadata():
    dim = PerplexityDimension()
    assert dim.dimension_name == "perplexity"
    assert dim.weight == 5.0
    assert dim.tier == "CORE"
    assert dim.description != ""

# Test analysis
def test_dimension_analyze():
    dim = PerplexityDimension()
    text = "We should leverage robust solutions to delve into the problem."
    metrics = dim.analyze(text, text.splitlines(), word_count=10)

    assert 'ai_vocabulary' in metrics
    assert metrics['ai_vocabulary']['count'] > 0

# Test scoring
def test_dimension_calculate_score():
    dim = PerplexityDimension()
    metrics = {
        'ai_vocabulary': {'count': 0, 'per_1k': 0.0},
        'formulaic_transitions': {'count': 0}
    }
    score = dim.calculate_score(metrics)
    assert score == 100.0

# Test recommendations
def test_dimension_get_recommendations():
    dim = PerplexityDimension()
    metrics = {
        'ai_vocabulary': {'count': 15, 'per_1k': 5.2, 'words': ['delve', 'leverage']},
        'formulaic_transitions': {'count': 3}
    }
    score = dim.calculate_score(metrics)
    recommendations = dim.get_recommendations(score, metrics)

    assert len(recommendations) > 0
    assert any('AI vocabulary' in rec for rec in recommendations)
```

---

## 📦 STORY 5: Create Dynamic Analysis Engine

**Priority:** P1 (Core Functionality)
**Story Points:** 8
**Dependencies:** Stories 1-4

### Description

**As a** user
**I want** the analyzer to work with any registered dimensions
**So that** I can add custom dimensions without code changes

### Acceptance Criteria

1. Engine dynamically discovers all registered dimensions
2. Validates weights before executing analysis
3. Executes all dimensions in parallel (if possible)
4. Aggregates results into unified format
5. Calculates weighted overall score
6. Gracefully handles dimension failures (don't crash entire analysis)
7. Maintains backward compatibility with existing `AnalysisResults` format

### Implementation Overview

```python
# core/dynamic_engine.py

from typing import Dict, List, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.weight_mediator import WeightMediator, WeightValidationError
from writescore.core.results import AnalysisResults

class DynamicAnalysisEngine:
    """
    Orchestrates analysis across all registered dimensions dynamically.

    Features:
    - Auto-discovers registered dimensions
    - Validates weights before execution
    - Parallel dimension execution
    - Graceful error handling
    - Dynamic result aggregation
    """

    def __init__(self,
                 registry: Optional[DimensionRegistry] = None,
                 mediator: Optional[WeightMediator] = None,
                 parallel: bool = True):
        """
        Initialize engine.

        Args:
            registry: DimensionRegistry (uses singleton if None)
            mediator: WeightMediator (creates new if None)
            parallel: Execute dimensions in parallel if True
        """
        self.registry = registry or DimensionRegistry()
        self.mediator = mediator or WeightMediator(self.registry)
        self.parallel = parallel
        self.last_analysis_time: Optional[float] = None

    def analyze(self, file_path: str, **kwargs) -> AnalysisResults:
        """
        Execute analysis across all registered dimensions.

        Args:
            file_path: Path to file to analyze
            **kwargs: Additional parameters passed to dimensions

        Returns:
            AnalysisResults with comprehensive analysis

        Raises:
            WeightValidationError: If dimension weights are invalid
            FileNotFoundError: If file doesn't exist
        """
        start_time = time.time()

        # Validate weights first
        self.mediator.require_valid()

        # Load file
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Preprocess
        text = self._strip_html_comments(text)
        lines = text.splitlines()

        # Calculate word count for dimensions that need it
        word_count = self._count_words(text)
        kwargs['word_count'] = word_count

        # Execute dimensions
        dimension_results = self._execute_dimensions(text, lines, **kwargs)

        # Aggregate results
        results = self._aggregate_results(
            file_path=file_path,
            text=text,
            lines=lines,
            dimension_results=dimension_results,
            word_count=word_count
        )

        self.last_analysis_time = time.time() - start_time

        return results

    def _execute_dimensions(self, text: str, lines: List[str], **kwargs) -> Dict[str, Dict]:
        """
        Execute all registered dimensions.

        Returns:
            Dict mapping dimension name to results dict:
            {
                'dimension_name': {
                    'metrics': {...},
                    'score': float,
                    'recommendations': [...],
                    'tier_mapping': str,
                    'weight': float,
                    'error': Optional[str]
                }
            }
        """
        dimensions = self.registry.get_all()
        results = {}

        if self.parallel and len(dimensions) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=min(len(dimensions), 10)) as executor:
                futures = {
                    executor.submit(self._execute_single_dimension, dim, text, lines, **kwargs): dim
                    for dim in dimensions
                }

                for future in as_completed(futures):
                    dim = futures[future]
                    results[dim.dimension_name] = future.result()
        else:
            # Sequential execution
            for dim in dimensions:
                results[dim.dimension_name] = self._execute_single_dimension(dim, text, lines, **kwargs)

        return results

    def _execute_single_dimension(self, dimension, text: str, lines: List[str], **kwargs) -> Dict:
        """
        Execute a single dimension with error handling.

        Returns:
            Result dict with metrics, score, recommendations, or error
        """
        try:
            # Analyze
            metrics = dimension.analyze(text, lines, **kwargs)

            # Score
            score = dimension.calculate_score(metrics)

            # Recommendations
            recommendations = dimension.get_recommendations(score, metrics)

            # Tier mapping
            tiers = dimension.get_tiers()
            tier_mapping = self._map_to_tier(score, tiers)

            return {
                'metrics': metrics,
                'score': score,
                'recommendations': recommendations,
                'tier_mapping': tier_mapping,
                'weight': dimension.weight,
                'tier': dimension.tier,
                'error': None
            }

        except Exception as e:
            # Graceful degradation - don't crash entire analysis
            return {
                'metrics': {},
                'score': 50.0,  # Neutral score on error
                'recommendations': [],
                'tier_mapping': 'unknown',
                'weight': dimension.weight,
                'tier': dimension.tier,
                'error': str(e)
            }

    def _map_to_tier(self, score: float, tiers: Dict[str, Tuple[float, float]]) -> str:
        """Map score to tier name."""
        for tier_name, (min_val, max_val) in sorted(tiers.items(), key=lambda x: -x[1][0]):
            if min_val <= score <= max_val:
                return tier_name
        return 'unknown'

    def _aggregate_results(self, file_path: str, text: str, lines: List[str],
                          dimension_results: Dict[str, Dict], word_count: int) -> AnalysisResults:
        """
        Aggregate dimension results into AnalysisResults format.

        Maintains backward compatibility with existing result format.
        """
        # Calculate overall weighted score
        total_weighted_score = 0.0
        total_weight = 0.0

        for dim_name, dim_result in dimension_results.items():
            if dim_result['error'] is None:
                total_weighted_score += dim_result['score'] * dim_result['weight']
                total_weight += dim_result['weight']

        overall_score = (total_weighted_score / total_weight) if total_weight > 0 else 50.0

        # Map to qualitative assessment
        overall_assessment = self._assess_overall(overall_score)

        # Build AnalysisResults (backward compatible format)
        # Extract common metrics from dimension results
        results = AnalysisResults(
            file_path=file_path,
            total_words=word_count,
            total_sentences=self._extract_metric(dimension_results, 'total_sentences', 0),
            total_paragraphs=self._extract_metric(dimension_results, 'total_paragraphs', 0),

            # Store dimension results for new dynamic access
            dimension_results=dimension_results,

            # Overall scores
            overall_score=overall_score,
            overall_assessment=overall_assessment,

            # Legacy fields (extracted from dimension results)
            **self._extract_legacy_fields(dimension_results)
        )

        return results

    def _assess_overall(self, score: float) -> str:
        """Map overall score to qualitative assessment."""
        if score >= 85:
            return "HUMAN-LIKE"
        elif score >= 50:
            return "MIXED"
        else:
            return "AI-LIKELY"

    def _extract_metric(self, dimension_results: Dict, metric_name: str, default: Any) -> Any:
        """Extract a metric from any dimension result."""
        for dim_result in dimension_results.values():
            metrics = dim_result.get('metrics', {})
            # Search nested dicts
            if metric_name in metrics:
                return metrics[metric_name]
            for sub_dict in metrics.values():
                if isinstance(sub_dict, dict) and metric_name in sub_dict:
                    return sub_dict[metric_name]
        return default

    def _extract_legacy_fields(self, dimension_results: Dict) -> Dict:
        """
        Extract legacy field mappings for backward compatibility.

        Maps new dimension result format to old AnalysisResults fields.
        """
        legacy = {}

        # Extract from perplexity dimension
        perp = dimension_results.get('perplexity', {}).get('metrics', {})
        if perp:
            ai_vocab = perp.get('ai_vocabulary', {})
            legacy['ai_vocabulary_count'] = ai_vocab.get('count', 0)
            legacy['ai_vocabulary_per_1k'] = ai_vocab.get('per_1k', 0.0)
            legacy['ai_vocabulary_list'] = ai_vocab.get('words', [])

            formulaic = perp.get('formulaic_transitions', {})
            legacy['formulaic_transitions_count'] = formulaic.get('count', 0)
            legacy['formulaic_transitions_list'] = formulaic.get('transitions', [])

        # Extract from burstiness dimension
        burst = dimension_results.get('burstiness', {}).get('metrics', {})
        if burst:
            sent_burst = burst.get('sentence_burstiness', {})
            legacy['sentence_mean_length'] = sent_burst.get('mean', 0.0)
            legacy['sentence_stdev'] = sent_burst.get('stdev', 0.0)
            legacy['sentence_min'] = sent_burst.get('min', 0)
            legacy['sentence_max'] = sent_burst.get('max', 0)

        # ... (continue for all legacy fields)

        # Store dimension scores
        for dim_name, dim_result in dimension_results.items():
            score_val = dim_result.get('score', 50.0)
            tier_mapping = dim_result.get('tier_mapping', 'unknown')

            # Create score field name: dimension_name + '_score'
            legacy[f'{dim_name}_score'] = tier_mapping
            legacy[f'{dim_name}_score_value'] = score_val

        return legacy

    def _strip_html_comments(self, text: str) -> str:
        """Remove HTML comments from text."""
        import re
        return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    def _count_words(self, text: str) -> int:
        """Count words excluding code blocks."""
        import re
        text = re.sub(r'```[\s\S]*?```', '', text)
        words = re.findall(r"\b[\w'-]+\b", text)
        return len(words)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for last analysis.

        Returns:
            Dict with timing and dimension execution info
        """
        dimensions = self.registry.get_all()

        return {
            'last_analysis_time_seconds': self.last_analysis_time,
            'dimension_count': len(dimensions),
            'parallel_execution': self.parallel,
            'dimensions': [
                {
                    'name': d.dimension_name,
                    'tier': d.tier,
                    'weight': d.weight
                }
                for d in dimensions
            ]
        }
```

### Tasks

- [ ] Create `core/dynamic_engine.py`
- [ ] Implement weight validation gate
- [ ] Implement parallel dimension execution
- [ ] Add error handling per dimension
- [ ] Implement result aggregation
- [ ] Map to legacy `AnalysisResults` format
- [ ] Add performance timing
- [ ] Write unit tests
- [ ] Write integration tests with real dimensions
- [ ] Performance benchmark vs old implementation

### Verification

```python
# Test basic analysis
def test_dynamic_analysis():
    # Setup dimensions
    DimensionRegistry.clear()
    PerplexityDimension()
    BurstinessDimension()

    engine = DynamicAnalysisEngine()
    results = engine.analyze('test_file.md')

    assert results.overall_score > 0
    assert results.dimension_results is not None
    assert len(results.dimension_results) == 2

# Test weight validation enforcement
def test_invalid_weights_rejected():
    DimensionRegistry.clear()
    MockDimension(weight=110.0)  # Invalid

    engine = DynamicAnalysisEngine()
    with pytest.raises(WeightValidationError):
        engine.analyze('test_file.md')

# Test dimension failure graceful handling
def test_dimension_failure_graceful():
    DimensionRegistry.clear()

    class FailingDimension(DimensionStrategy):
        def analyze(self, *args, **kwargs):
            raise RuntimeError("Dimension failed!")
        # ... other methods

    FailingDimension()
    PerplexityDimension()  # One good dimension

    engine = DynamicAnalysisEngine()
    results = engine.analyze('test_file.md')

    # Should still complete with failing dimension
    assert results is not None
    assert results.dimension_results['failing']['error'] is not None
```

---

## 📦 STORY 6: Build Dynamic Reporting System

**Priority:** P1 (User-Facing)
**Story Points:** 8
**Dependencies:** Story 5

### Description

**As a** user
**I want** reports to automatically include all registered dimensions
**So that** custom dimensions appear without report modifications

### Acceptance Criteria

1. Reports dynamically generated from registered dimensions
2. Dimensions grouped by tier in reports
3. Recommendations aggregated and prioritized
4. Weight distribution visualization data
5. Supports multiple output formats (JSON, text, markdown)
6. Maintains backward compatibility with existing CLI output

### Implementation Summary

```python
# core/dynamic_reporter.py

from typing import Dict, List, Any, Optional
from writescore.core.results import AnalysisResults, DualScore
from writescore.core.dimension_registry import DimensionRegistry

class DynamicReporter:
    """Generate reports dynamically based on registered dimensions."""

    def generate_comprehensive_report(self, results: AnalysisResults) -> Dict[str, Any]:
        """Create full report with all dimensions."""

    def generate_tier_summary(self, results: AnalysisResults) -> Dict[str, List[Dict]]:
        """Group dimensions by tier with scores."""

    def generate_prioritized_recommendations(self, results: AnalysisResults) -> List[Dict]:
        """Aggregate and prioritize recommendations from all dimensions."""

    def generate_weight_distribution(self) -> Dict[str, Any]:
        """Show how dimensions contribute to overall score."""

    def format_as_markdown(self, results: AnalysisResults) -> str:
        """Format report as markdown."""

    def format_as_json(self, results: AnalysisResults) -> str:
        """Format report as JSON."""
```

---

## 📦 STORY 7: Refactor Dual Score Calculator to Use Registry

**Priority:** P2 (Cleanup)
**Story Points:** 13
**Dependencies:** Stories 4-6

### Description

**As a** maintainer
**I want** the dual score calculator to use registered dimensions
**So that** scoring logic is DRY and dimension-owned

### Key Changes

- Remove 847 lines of hardcoded dimension logic
- Use `dimension.calculate_score()` for each dimension
- Use `dimension.weight` for score aggregation
- Use `dimension.get_recommendations()` for improvement actions
- Maintain exact backward compatibility with `DualScore` output

---

## 📦 STORY 8: Add Dimension Discovery/Auto-loading

**Priority:** P3 (Convenience)
**Story Points:** 5
**Dependencies:** Story 4

### Description

**As a** developer
**I want** dimensions to auto-register when imported
**So that** I don't need to manually instantiate them

### Implementation

```python
# dimensions/__init__.py

import importlib
import pkgutil
from pathlib import Path

# Auto-discover all dimension modules
package_dir = Path(__file__).parent
for (_, module_name, _) in pkgutil.iter_modules([str(package_dir)]):
    if module_name not in ['base', 'base_strategy', '__init__']:
        importlib.import_module(f'writescore.dimensions.{module_name}')

# At this point, all dimensions have self-registered
```

---

## 📦 STORY 9: Create Dimension Development Guide

**Priority:** P3 (Adoption)
**Story Points:** 5
**Dependencies:** Stories 1-8

### Description

**As a** new contributor
**I want** clear documentation on creating dimensions
**So that** I can add custom analysis dimensions

### Deliverables

- `docs/DIMENSION-DEVELOPMENT-GUIDE.md`
- Example custom dimension implementation
- Weight assignment best practices
- Testing guidelines
- Performance optimization tips

---

## Epic Summary & Timeline

**Total Story Points:** 73
**Estimated Timeline:** 4-6 sprints (8-12 weeks)

### Sprint Breakdown

**Sprint 1: Foundation (13 points)**
- Story 1: Enhanced Dimension Base Contract (3 pts)
- Story 2: Dimension Registry (5 pts)
- Story 3: Weight Validation Mediator (5 pts)

**Sprint 2-3: Refactoring (21 points)**
- Story 4: Refactor All Dimensions (21 pts)

**Sprint 4: Core Functionality (16 points)**
- Story 5: Dynamic Analysis Engine (8 pts)
- Story 6: Dynamic Reporting System (8 pts)

**Sprint 5: Cleanup & Polish (18 points)**
- Story 7: Refactor Dual Score Calculator (13 pts)
- Story 8: Auto-loading (5 pts)

**Sprint 6: Documentation (5 points)**
- Story 9: Development Guide (5 pts)

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code Reduction | -40% in core analyzer | Line count before/after |
| Test Coverage | ≥90% | pytest-cov |
| Performance | <5% regression | Benchmark suite |
| Weight Validation | 100% coverage | Unit tests |
| Dimension Isolation | 0 cross-dependencies | Static analysis |

### Functional Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Add Dimension | 0 core file changes | Manual test |
| Weight Auto-validation | 100% invalid configs caught | Unit tests |
| Dynamic Reporting | All dimensions auto-included | Integration test |
| Backward Compatibility | 100% existing tests pass | Regression suite |

---

## Migration Strategy

### Phase 1: Parallel Implementation (Weeks 1-4)
- Build new system alongside existing
- No breaking changes
- Existing code continues to work

### Phase 2: Gradual Migration (Weeks 5-8)
- Refactor dimensions one-by-one
- Run dual implementation (old + new)
- Compare results for parity
- Fix discrepancies

### Phase 3: Core Replacement (Weeks 9-10)
- Switch analyzer to use registry
- Remove old implementation
- Update all tests
- Performance validation

### Phase 4: Polish & Document (Weeks 11-12)
- Add auto-loading
- Write documentation
- Final performance optimization
- Release notes

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance regression | Medium | High | Benchmark at each phase, optimize hot paths |
| Breaking backward compatibility | Low | High | Extensive regression testing, parallel implementation |
| Weight conflicts | Medium | Medium | Comprehensive validation, clear error messages |
| Complex testing | High | Medium | Mocking framework for dimensions, clear test patterns |
| Dimension coupling | Medium | Medium | Regular code reviews, enforce interface contracts |

---

## Open Questions

1. **Weight Distribution**: Maintain 200-point system or normalize to 100?
   - **Recommendation**: Normalize to 100 for simplicity

2. **Backward Compatibility**: Must JSON outputs remain identical?
   - **Recommendation**: Yes, add new fields but maintain existing ones

3. **Runtime Configuration**: Should dimension weights be configurable?
   - **Recommendation**: Phase 2 feature, start with compile-time

4. **Performance Overhead**: Acceptable overhead for registry pattern?
   - **Recommendation**: Target <5% regression, optimize if needed

5. **External Plugins**: Support dimensions from separate packages?
   - **Recommendation**: Phase 2 feature, design for extensibility now

---

## Appendix: Pattern Research Details

### Strategy Pattern Benefits
- Each dimension encapsulates its algorithm independently
- Dimensions are interchangeable at runtime
- New dimensions added without modifying existing code
- Follows Open-Closed Principle

### Registry Pattern Benefits
- Decouples dimension creation from usage
- Central discovery point
- Enables plugin architecture
- Auto-discovery of available dimensions

### Mediator Pattern Benefits
- Reduces coupling between dimensions
- Centralizes validation logic
- Coordinates interactions without dependencies
- Easy to extend validation rules

### Observer Pattern Benefits
- Loose coupling through notifications
- Dimensions don't need to know about registry details
- Easy to add new observers (e.g., logging, monitoring)
- Event-driven architecture

---

## Approval & Sign-off

**Prepared By:** Claude Code (AI Assistant) & Sarah (Product Owner Agent)
**Date:** 2025-11-03
**Status:** Awaiting Approval

**Approvers:**

- [ ] Product Owner: __________________ Date: __________
- [ ] Tech Lead: __________________ Date: __________
- [ ] Engineering Manager: __________________ Date: __________

**Questions/Concerns:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

**End of Refactoring Plan**
