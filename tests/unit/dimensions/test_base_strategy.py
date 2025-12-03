"""
Tests for DimensionStrategy enhanced base class.

Covers:
- Abstract enforcement (cannot instantiate base class)
- Abstract method/property enforcement
- Tier validation with valid/invalid values
- Score validation (0-100 range)
- Weight validation (0-100 range)
- get_impact_level() logic with threshold boundaries
- _calculate_gap() static method
- AST helper methods
- Backward compatibility methods
- analyze_detailed() default implementation
- _map_score_to_tier() with various scores
"""

from typing import Any, Dict, List, Tuple

import pytest
from marko.block import FencedCode, Heading, Quote

from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

# ============================================================================
# Test Fixtures - Concrete Implementations
# ============================================================================


class CompleteDimension(DimensionStrategy):
    """Complete concrete implementation for testing."""

    @property
    def dimension_name(self) -> str:
        return "test_dimension"

    @property
    def weight(self) -> float:
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        return DimensionTier.SUPPORTING

    @property
    def description(self) -> str:
        return "Test dimension for unit testing"

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        return {"test_metric": len(text)}

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        score = 85.0
        self._validate_score(score)
        return score

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        if score < 75:
            return ["Improve test metric"]
        return []

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        return {
            "excellent": (90.0, 100.0),
            "good": (75.0, 89.9),
            "acceptable": (50.0, 74.9),
            "poor": (0.0, 49.9),
        }


class IncompleteDimension(DimensionStrategy):
    """Incomplete implementation missing required methods."""

    @property
    def dimension_name(self) -> str:
        return "incomplete"

    # Missing other required properties and methods


class InvalidTierDimension(DimensionStrategy):
    """Dimension with invalid tier value."""

    def __init__(self):
        super().__init__()
        self._invalid_tier = "INVALID_TIER"

    @property
    def dimension_name(self) -> str:
        return "invalid_tier"

    @property
    def weight(self) -> float:
        return 5.0

    @property
    def tier(self):
        return self._invalid_tier

    @property
    def description(self) -> str:
        return "Test dimension with invalid tier"

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        return {}

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        return 50.0

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        return []

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        return {"good": (0.0, 100.0)}


@pytest.fixture
def dimension():
    """Create complete test dimension instance."""
    return CompleteDimension()


@pytest.fixture
def markdown_text():
    """Sample markdown text for AST testing."""
    return """# Heading 1

This is a paragraph with some text.

## Heading 2

> This is a blockquote
> with multiple lines

- List item 1
- List item 2

```python
def hello():
    return "world"
```

More text here.
"""


# ============================================================================
# Abstract Base Class Tests
# ============================================================================


def test_cannot_instantiate_base():
    """Verify DimensionStrategy cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        DimensionStrategy()


def test_abstract_method_enforcement():
    """Verify incomplete subclass cannot be instantiated."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteDimension()


def test_complete_dimension_can_be_instantiated():
    """Verify complete implementation can be instantiated."""
    dim = CompleteDimension()
    assert dim is not None
    assert isinstance(dim, DimensionStrategy)


# ============================================================================
# Abstract Properties Tests
# ============================================================================


def test_dimension_name_property(dimension):
    """Test dimension_name property is accessible."""
    assert dimension.dimension_name == "test_dimension"
    assert isinstance(dimension.dimension_name, str)


def test_weight_property(dimension):
    """Test weight property is accessible."""
    assert dimension.weight == 5.0
    assert isinstance(dimension.weight, float)


def test_tier_property(dimension):
    """Test tier property is accessible."""
    assert dimension.tier == DimensionTier.SUPPORTING
    assert isinstance(dimension.tier, DimensionTier)


def test_description_property(dimension):
    """Test description property is accessible."""
    assert dimension.description == "Test dimension for unit testing"
    assert isinstance(dimension.description, str)


# ============================================================================
# Abstract Methods Tests
# ============================================================================


def test_analyze_method(dimension):
    """Test analyze method works correctly."""
    result = dimension.analyze("test text", ["test", "text"])
    assert isinstance(result, dict)
    assert "test_metric" in result


def test_calculate_score_method(dimension):
    """Test calculate_score method works correctly."""
    metrics = {"test_metric": 100}
    score = dimension.calculate_score(metrics)
    assert isinstance(score, float)
    assert score == 85.0


def test_get_recommendations_method(dimension):
    """Test get_recommendations method works correctly."""
    recommendations = dimension.get_recommendations(85.0, {})
    assert isinstance(recommendations, list)
    assert len(recommendations) == 0  # 85.0 > 75, so no recommendations

    recommendations = dimension.get_recommendations(50.0, {})
    assert len(recommendations) > 0  # 50.0 < 75, should have recommendations


def test_get_tiers_method(dimension):
    """Test get_tiers method works correctly."""
    tiers = dimension.get_tiers()
    assert isinstance(tiers, dict)
    assert "excellent" in tiers
    assert "good" in tiers
    assert "acceptable" in tiers
    assert "poor" in tiers


# ============================================================================
# Tier Validation Tests
# ============================================================================


def test_tier_validation_with_valid_values(dimension):
    """Verify valid tier values are accepted."""
    # Should not raise any exception
    dimension._validate_tier()


def test_tier_validation_with_all_valid_tier_types():
    """Test all DimensionTier enum values are valid."""

    def make_dim_class(tier_val):
        class TestDim(CompleteDimension):
            @property
            def tier(self):
                return tier_val

        return TestDim

    for tier_value in DimensionTier:
        TestDim = make_dim_class(tier_value)
        dim = TestDim()
        dim._validate_tier()  # Should not raise


def test_tier_validation_with_invalid_value():
    """Verify invalid tier values raise ValueError."""
    dim = InvalidTierDimension()
    with pytest.raises(ValueError, match="tier must be one of"):
        dim._validate_tier()


def test_dimension_tier_enum_values():
    """Test DimensionTier enum has all expected values."""
    assert DimensionTier.ADVANCED == "ADVANCED"
    assert DimensionTier.CORE == "CORE"
    assert DimensionTier.SUPPORTING == "SUPPORTING"
    assert DimensionTier.STRUCTURAL == "STRUCTURAL"


def test_dimension_tier_is_string_enum():
    """Test DimensionTier enum values are strings."""
    for tier in DimensionTier:
        assert isinstance(tier.value, str)


# ============================================================================
# Score Validation Tests
# ============================================================================


def test_score_validation_valid_scores(dimension):
    """Verify valid scores are accepted."""
    # Valid scores - should not raise
    dimension._validate_score(0.0)
    dimension._validate_score(50.0)
    dimension._validate_score(100.0)
    dimension._validate_score(0.1)
    dimension._validate_score(99.9)


def test_score_validation_invalid_negative(dimension):
    """Verify negative scores raise ValueError."""
    with pytest.raises(ValueError, match="score must be between 0.0 and 100.0"):
        dimension._validate_score(-1.0)

    with pytest.raises(ValueError, match="score must be between 0.0 and 100.0"):
        dimension._validate_score(-0.1)


def test_score_validation_invalid_above_100(dimension):
    """Verify scores above 100 raise ValueError."""
    with pytest.raises(ValueError, match="score must be between 0.0 and 100.0"):
        dimension._validate_score(101.0)

    with pytest.raises(ValueError, match="score must be between 0.0 and 100.0"):
        dimension._validate_score(100.1)


# ============================================================================
# Weight Validation Tests
# ============================================================================


def test_weight_validation_valid_weights(dimension):
    """Verify valid weights are accepted."""
    # Valid weights - should not raise
    dimension._validate_weight(0.0)
    dimension._validate_weight(50.0)
    dimension._validate_weight(100.0)
    dimension._validate_weight(0.1)
    dimension._validate_weight(99.9)


def test_weight_validation_invalid_negative(dimension):
    """Verify negative weights raise ValueError."""
    with pytest.raises(ValueError, match="weight must be between 0.0 and 100.0"):
        dimension._validate_weight(-5.0)

    with pytest.raises(ValueError, match="weight must be between 0.0 and 100.0"):
        dimension._validate_weight(-0.1)


def test_weight_validation_invalid_above_100(dimension):
    """Verify weights above 100 raise ValueError."""
    with pytest.raises(ValueError, match="weight must be between 0.0 and 100.0"):
        dimension._validate_weight(150.0)

    with pytest.raises(ValueError, match="weight must be between 0.0 and 100.0"):
        dimension._validate_weight(100.1)


# ============================================================================
# get_impact_level() Tests
# ============================================================================


def test_impact_level_none(dimension):
    """Test get_impact_level returns NONE for gap < 5."""
    assert dimension.get_impact_level(100.0) == "NONE"  # gap = 0
    assert dimension.get_impact_level(96.0) == "NONE"  # gap = 4
    assert dimension.get_impact_level(95.1) == "NONE"  # gap = 4.9


def test_impact_level_low(dimension):
    """Test get_impact_level returns LOW for 5 <= gap < 15."""
    assert dimension.get_impact_level(95.0) == "LOW"  # gap = 5
    assert dimension.get_impact_level(92.0) == "LOW"  # gap = 8
    assert dimension.get_impact_level(85.1) == "LOW"  # gap = 14.9


def test_impact_level_medium(dimension):
    """Test get_impact_level returns MEDIUM for 15 <= gap < 30."""
    assert dimension.get_impact_level(85.0) == "MEDIUM"  # gap = 15
    assert dimension.get_impact_level(84.0) == "MEDIUM"  # gap = 16
    assert dimension.get_impact_level(75.0) == "MEDIUM"  # gap = 25
    assert dimension.get_impact_level(70.1) == "MEDIUM"  # gap = 29.9


def test_impact_level_high(dimension):
    """Test get_impact_level returns HIGH for gap >= 30."""
    assert dimension.get_impact_level(70.0) == "HIGH"  # gap = 30
    assert dimension.get_impact_level(69.0) == "HIGH"  # gap = 31
    assert dimension.get_impact_level(50.0) == "HIGH"  # gap = 50
    assert dimension.get_impact_level(0.0) == "HIGH"  # gap = 100


def test_impact_level_all_thresholds(dimension):
    """Test all threshold boundaries for impact level."""
    # Exact boundary tests
    assert dimension.get_impact_level(100.0) == "NONE"
    assert dimension.get_impact_level(95.0) == "LOW"
    assert dimension.get_impact_level(85.0) == "MEDIUM"
    assert dimension.get_impact_level(70.0) == "HIGH"


# ============================================================================
# _calculate_gap() Tests
# ============================================================================


def test_calculate_gap_static_method():
    """Test _calculate_gap static method."""
    assert DimensionStrategy._calculate_gap(100.0) == 0.0
    assert DimensionStrategy._calculate_gap(75.0) == 25.0
    assert DimensionStrategy._calculate_gap(50.0) == 50.0
    assert DimensionStrategy._calculate_gap(0.0) == 100.0
    assert DimensionStrategy._calculate_gap(85.5) == 14.5


def test_calculate_gap_instance_method(dimension):
    """Test _calculate_gap can be called from instance."""
    assert dimension._calculate_gap(100.0) == 0.0
    assert dimension._calculate_gap(75.0) == 25.0


# ============================================================================
# AST Helper Methods Tests
# ============================================================================


def test_get_markdown_parser(dimension):
    """Test _get_markdown_parser lazy loading."""
    parser1 = dimension._get_markdown_parser()
    parser2 = dimension._get_markdown_parser()

    assert parser1 is not None
    assert parser1 is parser2  # Should be singleton


def test_parse_to_ast(dimension, markdown_text):
    """Test _parse_to_ast parsing."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test")
    assert ast is not None


def test_parse_to_ast_caching(dimension, markdown_text):
    """Test _parse_to_ast caching works."""
    ast1 = dimension._parse_to_ast(markdown_text, cache_key="test_cache")
    ast2 = dimension._parse_to_ast(markdown_text, cache_key="test_cache")

    assert ast1 is ast2  # Should return cached version


def test_parse_to_ast_different_cache_keys(dimension, markdown_text):
    """Test different cache keys store separately."""
    ast1 = dimension._parse_to_ast(markdown_text, cache_key="key1")
    ast2 = dimension._parse_to_ast(markdown_text, cache_key="key2")

    # Different cache keys, so different objects (re-parsed)
    assert ast1 is not ast2


def test_parse_to_ast_no_cache_key(dimension, markdown_text):
    """Test parsing without cache key."""
    ast1 = dimension._parse_to_ast(markdown_text)
    ast2 = dimension._parse_to_ast(markdown_text)

    # No caching, so different objects
    assert ast1 is not ast2


def test_walk_ast_find_headings(dimension, markdown_text):
    """Test _walk_ast finds headings."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test_headings")
    headings = dimension._walk_ast(ast, Heading)

    assert len(headings) >= 2  # Should find at least 2 headings


def test_walk_ast_find_quotes(dimension, markdown_text):
    """Test _walk_ast finds blockquotes."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test_quotes")
    quotes = dimension._walk_ast(ast, Quote)

    assert len(quotes) >= 1  # Should find at least 1 blockquote


def test_walk_ast_find_code_blocks(dimension, markdown_text):
    """Test _walk_ast finds code blocks."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test_code")
    code_blocks = dimension._walk_ast(ast, FencedCode)

    assert len(code_blocks) >= 1  # Should find at least 1 code block


def test_walk_ast_no_type_filter(dimension, markdown_text):
    """Test _walk_ast without type filter returns all nodes."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test_all")
    all_nodes = dimension._walk_ast(ast, node_type=None)

    assert len(all_nodes) > 0  # Should return many nodes


def test_extract_text_from_node(dimension, markdown_text):
    """Test _extract_text_from_node extracts text."""
    ast = dimension._parse_to_ast(markdown_text, cache_key="test_extract")
    headings = dimension._walk_ast(ast, Heading)

    assert len(headings) > 0
    text = dimension._extract_text_from_node(headings[0])

    assert isinstance(text, str)
    assert len(text) > 0
    assert "Heading" in text


def test_extract_text_handles_string_node(dimension):
    """Test _extract_text_from_node handles string nodes."""
    text = dimension._extract_text_from_node("simple string")
    assert text == "simple string"


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


def test_score_method_backward_compatibility(dimension):
    """Verify score() method wraps calculate_score() correctly."""
    score_value, score_label = dimension.score({"test": "data"})

    assert score_value == 85.0
    assert isinstance(score_label, str)
    assert score_label == "GOOD"  # 85.0 falls in 'good' tier (75.0-89.9)


def test_get_max_score_deprecated(dimension):
    """Verify get_max_score returns 100.0."""
    assert dimension.get_max_score() == 100.0


def test_get_dimension_name_deprecated(dimension):
    """Verify get_dimension_name returns dimension_name property."""
    assert dimension.get_dimension_name() == "test_dimension"
    assert dimension.get_dimension_name() == dimension.dimension_name


# ============================================================================
# analyze_detailed() Tests
# ============================================================================


def test_analyze_detailed_default_implementation(dimension):
    """Verify analyze_detailed returns empty list by default."""
    result = dimension.analyze_detailed(["line 1", "line 2"])

    assert result == []
    assert isinstance(result, list)


def test_analyze_detailed_with_html_comment_checker(dimension):
    """Verify analyze_detailed accepts html_comment_checker parameter."""
    result = dimension.analyze_detailed(["line 1", "line 2"], html_comment_checker=lambda x: False)

    assert result == []


# ============================================================================
# _map_score_to_tier() Tests
# ============================================================================


def test_map_score_to_tier_excellent(dimension):
    """Test _map_score_to_tier maps to EXCELLENT tier."""
    assert dimension._map_score_to_tier(100.0) == "EXCELLENT"
    assert dimension._map_score_to_tier(95.0) == "EXCELLENT"
    assert dimension._map_score_to_tier(90.0) == "EXCELLENT"


def test_map_score_to_tier_good(dimension):
    """Test _map_score_to_tier maps to GOOD tier."""
    assert dimension._map_score_to_tier(89.9) == "GOOD"
    assert dimension._map_score_to_tier(80.0) == "GOOD"
    assert dimension._map_score_to_tier(75.0) == "GOOD"


def test_map_score_to_tier_acceptable(dimension):
    """Test _map_score_to_tier maps to ACCEPTABLE tier."""
    assert dimension._map_score_to_tier(74.9) == "ACCEPTABLE"
    assert dimension._map_score_to_tier(60.0) == "ACCEPTABLE"
    assert dimension._map_score_to_tier(50.0) == "ACCEPTABLE"


def test_map_score_to_tier_poor(dimension):
    """Test _map_score_to_tier maps to POOR tier."""
    assert dimension._map_score_to_tier(49.9) == "POOR"
    assert dimension._map_score_to_tier(25.0) == "POOR"
    assert dimension._map_score_to_tier(0.0) == "POOR"


def test_map_score_to_tier_boundary_values(dimension):
    """Test tier boundary values are mapped correctly."""
    # Test exact boundaries
    assert dimension._map_score_to_tier(90.0) == "EXCELLENT"
    assert dimension._map_score_to_tier(89.9) == "GOOD"
    assert dimension._map_score_to_tier(75.0) == "GOOD"
    assert dimension._map_score_to_tier(74.9) == "ACCEPTABLE"
    assert dimension._map_score_to_tier(50.0) == "ACCEPTABLE"
    assert dimension._map_score_to_tier(49.9) == "POOR"


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_analysis_workflow(dimension):
    """Test complete analysis workflow."""
    # 1. Analyze
    text = "This is test text for analysis"
    lines = text.split("\n")
    metrics = dimension.analyze(text, lines, word_count=6)

    assert "test_metric" in metrics

    # 2. Calculate score
    score = dimension.calculate_score(metrics)
    assert 0.0 <= score <= 100.0

    # 3. Get recommendations
    recommendations = dimension.get_recommendations(score, metrics)
    assert isinstance(recommendations, list)

    # 4. Get impact level
    impact = dimension.get_impact_level(score)
    assert impact in ["NONE", "LOW", "MEDIUM", "HIGH"]


def test_dimension_metadata_accessible():
    """Test all metadata properties are accessible."""
    dim = CompleteDimension()

    # All properties should be accessible
    assert dim.dimension_name is not None
    assert dim.weight is not None
    assert dim.tier is not None
    assert dim.description is not None


def test_ast_cache_persists_across_calls(dimension, markdown_text):
    """Test AST cache persists across multiple calls."""
    # First parse
    ast1 = dimension._parse_to_ast(markdown_text, cache_key="persist_test")

    # Second parse with same cache key
    ast2 = dimension._parse_to_ast(markdown_text, cache_key="persist_test")

    # Should be the exact same object from cache
    assert ast1 is ast2

    # Verify cache was actually used (check internal state)
    assert "persist_test" in dimension._ast_cache
