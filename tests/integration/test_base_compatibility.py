"""
Integration tests for backward compatibility between DimensionAnalyzer and DimensionStrategy.

Tests that both base classes can coexist during the transition period:
- Both can be imported without conflicts
- Legacy dimensions using DimensionAnalyzer still work
- New dimensions using DimensionStrategy work correctly
- No namespace conflicts between the two base classes
"""

import pytest
from abc import ABC
from typing import Dict, List, Tuple, Any
from writescore.dimensions.base import DimensionAnalyzer
from writescore.dimensions.base_strategy import (
    DimensionStrategy,
    DimensionTier
)


# ============================================================================
# Legacy Dimension (DimensionAnalyzer)
# ============================================================================

class LegacyDimension(DimensionAnalyzer):
    """Legacy dimension using old DimensionAnalyzer base class."""

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """Legacy analyze implementation."""
        return {
            'word_count': len(text.split()),
            'line_count': len(lines)
        }

    def score(self, analysis_results: Dict[str, Any]) -> Tuple[float, str]:
        """Legacy score implementation returning (value, label)."""
        word_count = analysis_results.get('word_count', 0)
        if word_count > 100:
            return (8.0, "HIGH")
        elif word_count > 50:
            return (5.0, "MEDIUM")
        else:
            return (3.0, "LOW")


# ============================================================================
# New Dimension (DimensionStrategy)
# ============================================================================

class NewDimension(DimensionStrategy):
    """New dimension using enhanced DimensionStrategy base class."""

    @property
    def dimension_name(self) -> str:
        return "new_dimension"

    @property
    def weight(self) -> float:
        return 10.0

    @property
    def tier(self) -> DimensionTier:
        return DimensionTier.CORE

    @property
    def description(self) -> str:
        return "New dimension with enhanced metadata"

    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """New analyze implementation."""
        return {
            'word_count': len(text.split()),
            'line_count': len(lines),
            'char_count': len(text)
        }

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """New calculate_score implementation (0-100 scale)."""
        word_count = metrics.get('word_count', 0)

        if word_count > 100:
            score = 90.0
        elif word_count > 50:
            score = 70.0
        else:
            score = 50.0

        self._validate_score(score)
        return score

    def get_recommendations(
        self, score: float, metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on score."""
        recommendations = []

        if score < 75:
            word_count = metrics.get('word_count', 0)
            recommendations.append(f"Increase word count from {word_count} to >50")

        return recommendations

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """Define score tier ranges."""
        return {
            'excellent': (90.0, 100.0),
            'good': (75.0, 89.9),
            'acceptable': (50.0, 74.9),
            'poor': (0.0, 49.9)
        }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def legacy_dimension():
    """Create legacy dimension instance."""
    return LegacyDimension()


@pytest.fixture
def new_dimension():
    """Create new dimension instance."""
    return NewDimension()


@pytest.fixture
def sample_text():
    """Sample text for testing both dimension types."""
    return """This is a sample text for testing both legacy and new dimensions.
It has multiple lines to test line counting functionality.
The text is long enough to trigger different score thresholds
in both the legacy and new dimension implementations.
This ensures comprehensive testing of backward compatibility."""


# ============================================================================
# Import and Namespace Tests
# ============================================================================

def test_both_bases_can_be_imported():
    """Verify both DimensionAnalyzer and DimensionStrategy can be imported."""
    from writescore.dimensions.base import DimensionAnalyzer
    from writescore.dimensions.base_strategy import DimensionStrategy

    assert DimensionAnalyzer is not None
    assert DimensionStrategy is not None


def test_both_bases_are_abstract():
    """Verify both base classes are ABCs."""
    assert issubclass(DimensionAnalyzer, ABC)
    assert issubclass(DimensionStrategy, ABC)


def test_both_bases_cannot_be_instantiated():
    """Verify neither base class can be instantiated directly."""
    with pytest.raises(TypeError):
        DimensionAnalyzer()

    with pytest.raises(TypeError):
        DimensionStrategy()


def test_no_namespace_conflicts():
    """Verify no namespace conflicts between the two base classes."""
    # Import both from dimensions module
    from writescore.dimensions import (
        DimensionAnalyzer,
        DimensionStrategy,
        DimensionTier
    )

    assert DimensionAnalyzer is not None
    assert DimensionStrategy is not None
    assert DimensionTier is not None

    # Verify they are different classes
    assert DimensionAnalyzer is not DimensionStrategy


# ============================================================================
# Legacy Dimension Tests
# ============================================================================

def test_legacy_dimension_works(legacy_dimension, sample_text):
    """Verify legacy dimensions using DimensionAnalyzer still work."""
    lines = sample_text.split('\n')

    # Test analyze method
    results = legacy_dimension.analyze(sample_text, lines)
    assert 'word_count' in results
    assert 'line_count' in results

    # Test score method
    score_value, score_label = legacy_dimension.score(results)
    assert isinstance(score_value, float)
    assert isinstance(score_label, str)
    assert score_label in ["HIGH", "MEDIUM", "LOW"]


def test_legacy_dimension_get_max_score(legacy_dimension):
    """Verify legacy get_max_score method works."""
    max_score = legacy_dimension.get_max_score()
    assert isinstance(max_score, float)
    assert max_score == 10.0  # Default from base class


def test_legacy_dimension_get_dimension_name(legacy_dimension):
    """Verify legacy get_dimension_name method works."""
    name = legacy_dimension.get_dimension_name()
    assert isinstance(name, str)
    assert name == "LegacyDimension"  # Derived from class name (only strips "Analyzer")


def test_legacy_dimension_has_ast_helpers(legacy_dimension):
    """Verify legacy dimensions have AST helper methods."""
    assert hasattr(legacy_dimension, '_get_markdown_parser')
    assert hasattr(legacy_dimension, '_parse_to_ast')
    assert hasattr(legacy_dimension, '_walk_ast')
    assert hasattr(legacy_dimension, '_extract_text_from_node')


# ============================================================================
# New Dimension Tests
# ============================================================================

def test_new_dimension_works(new_dimension, sample_text):
    """Verify new dimensions using DimensionStrategy work correctly."""
    lines = sample_text.split('\n')

    # Test analyze method
    metrics = new_dimension.analyze(sample_text, lines)
    assert 'word_count' in metrics
    assert 'line_count' in metrics
    assert 'char_count' in metrics

    # Test calculate_score method
    score = new_dimension.calculate_score(metrics)
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0

    # Test get_recommendations method
    recommendations = new_dimension.get_recommendations(score, metrics)
    assert isinstance(recommendations, list)


def test_new_dimension_metadata_properties(new_dimension):
    """Verify new dimensions have metadata properties."""
    assert new_dimension.dimension_name == "new_dimension"
    assert new_dimension.weight == 10.0
    assert new_dimension.tier == DimensionTier.CORE
    assert new_dimension.description == "New dimension with enhanced metadata"


def test_new_dimension_get_tiers(new_dimension):
    """Verify new dimension has get_tiers method."""
    tiers = new_dimension.get_tiers()
    assert isinstance(tiers, dict)
    assert 'excellent' in tiers
    assert 'good' in tiers


def test_new_dimension_get_impact_level(new_dimension):
    """Verify new dimension has get_impact_level method."""
    impact = new_dimension.get_impact_level(85.0)
    assert impact in ["NONE", "LOW", "MEDIUM", "HIGH"]


def test_new_dimension_backward_compatible_score_method(new_dimension, sample_text):
    """Verify new dimension has backward compatible score() method."""
    lines = sample_text.split('\n')
    metrics = new_dimension.analyze(sample_text, lines)

    # New dimensions should also support legacy score() signature
    score_value, score_label = new_dimension.score(metrics)
    assert isinstance(score_value, float)
    assert isinstance(score_label, str)


def test_new_dimension_has_ast_helpers(new_dimension):
    """Verify new dimensions have AST helper methods."""
    assert hasattr(new_dimension, '_get_markdown_parser')
    assert hasattr(new_dimension, '_parse_to_ast')
    assert hasattr(new_dimension, '_walk_ast')
    assert hasattr(new_dimension, '_extract_text_from_node')


# ============================================================================
# Side-by-Side Comparison Tests
# ============================================================================

def test_both_dimensions_can_analyze_same_text(
    legacy_dimension, new_dimension, sample_text
):
    """Verify both dimension types can analyze the same text."""
    lines = sample_text.split('\n')

    # Legacy dimension
    legacy_results = legacy_dimension.analyze(sample_text, lines)
    legacy_score_value, legacy_score_label = legacy_dimension.score(legacy_results)

    # New dimension
    new_metrics = new_dimension.analyze(sample_text, lines)
    new_score_value = new_dimension.calculate_score(new_metrics)

    # Both should produce valid results
    assert isinstance(legacy_score_value, float)
    assert isinstance(new_score_value, float)
    assert 0.0 <= new_score_value <= 100.0


def test_both_dimensions_work_independently(
    legacy_dimension, new_dimension, sample_text
):
    """Verify both dimension types work independently without interference."""
    lines = sample_text.split('\n')

    # Run legacy dimension
    legacy_results = legacy_dimension.analyze(sample_text, lines)
    legacy_score = legacy_dimension.score(legacy_results)

    # Run new dimension
    new_metrics = new_dimension.analyze(sample_text, lines)
    new_score = new_dimension.calculate_score(new_metrics)

    # Both should complete successfully
    assert legacy_score is not None
    assert new_score is not None


def test_legacy_and_new_have_common_interface_elements():
    """Verify both base classes share some common interface elements."""
    # Both should have analyze method
    assert hasattr(LegacyDimension, 'analyze')
    assert hasattr(NewDimension, 'analyze')

    # Both should have AST helpers
    legacy = LegacyDimension()
    new = NewDimension()

    assert hasattr(legacy, '_get_markdown_parser')
    assert hasattr(new, '_get_markdown_parser')


# ============================================================================
# Coexistence Tests
# ============================================================================

def test_multiple_legacy_and_new_dimensions_coexist():
    """Verify multiple instances of both dimension types can coexist."""
    # Create multiple instances
    legacy1 = LegacyDimension()
    legacy2 = LegacyDimension()
    new1 = NewDimension()
    new2 = NewDimension()

    # All should be valid instances
    assert isinstance(legacy1, DimensionAnalyzer)
    assert isinstance(legacy2, DimensionAnalyzer)
    assert isinstance(new1, DimensionStrategy)
    assert isinstance(new2, DimensionStrategy)

    # Instances should be independent
    assert legacy1 is not legacy2
    assert new1 is not new2


def test_dimension_instances_do_not_share_state(sample_text):
    """Verify dimension instances maintain independent state."""
    lines = sample_text.split('\n')

    # Create two new dimensions
    dim1 = NewDimension()
    dim2 = NewDimension()

    # Parse AST with different cache keys
    ast1 = dim1._parse_to_ast(sample_text, cache_key='dim1')
    ast2 = dim2._parse_to_ast(sample_text, cache_key='dim2')

    # Each should have its own cache
    assert 'dim1' in dim1._ast_cache
    assert 'dim1' not in dim2._ast_cache
    assert 'dim2' in dim2._ast_cache
    assert 'dim2' not in dim1._ast_cache


# ============================================================================
# Migration Path Tests
# ============================================================================

def test_new_dimension_can_replace_legacy_interface():
    """Verify new dimensions can fulfill legacy interface requirements."""
    new = NewDimension()

    # New dimension should support legacy methods
    assert hasattr(new, 'score')  # Legacy signature
    assert hasattr(new, 'get_max_score')  # Legacy method
    assert hasattr(new, 'get_dimension_name')  # Legacy method

    # These methods should work
    assert new.get_max_score() == 100.0
    assert new.get_dimension_name() == "new_dimension"


def test_backward_compatible_score_signature(new_dimension):
    """Verify new dimension's score() method matches legacy signature."""
    metrics = {'word_count': 75}

    # Should return tuple of (float, str)
    result = new_dimension.score(metrics)

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], float)
    assert isinstance(result[1], str)


def test_both_dimensions_support_kwargs(legacy_dimension, new_dimension):
    """Verify both dimension types support **kwargs in analyze."""
    text = "Test text"
    lines = ["Test text"]

    # Both should accept additional kwargs
    legacy_result = legacy_dimension.analyze(
        text, lines, word_count=2, domain="GENERAL"
    )
    new_result = new_dimension.analyze(
        text, lines, word_count=2, domain="GENERAL"
    )

    # Both should complete successfully
    assert isinstance(legacy_result, dict)
    assert isinstance(new_result, dict)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_legacy_and_new_dimensions_handle_errors_independently():
    """Verify errors in one dimension type don't affect the other."""
    # Create valid instances
    legacy = LegacyDimension()
    new = NewDimension()

    # Both should work normally
    text = "test"
    lines = ["test"]

    legacy_result = legacy.analyze(text, lines)
    new_result = new.analyze(text, lines)

    assert legacy_result is not None
    assert new_result is not None


def test_dimension_tier_enum_only_in_new_base():
    """Verify DimensionTier enum is specific to new base class."""
    # New dimension should use DimensionTier
    new = NewDimension()
    assert isinstance(new.tier, DimensionTier)

    # Legacy dimension shouldn't have tier property
    legacy = LegacyDimension()
    assert not hasattr(legacy, 'tier')


# ============================================================================
# Documentation and Metadata Tests
# ============================================================================

def test_both_bases_have_docstrings():
    """Verify both base classes have documentation."""
    assert DimensionAnalyzer.__doc__ is not None
    assert DimensionStrategy.__doc__ is not None
    assert len(DimensionAnalyzer.__doc__) > 0
    assert len(DimensionStrategy.__doc__) > 0


def test_new_dimension_has_richer_metadata():
    """Verify new dimension has richer metadata than legacy."""
    legacy = LegacyDimension()
    new = NewDimension()

    # New has metadata properties that legacy doesn't
    assert hasattr(new, 'weight')
    assert hasattr(new, 'tier')
    assert hasattr(new, 'description')

    # Legacy doesn't have these properties
    assert not hasattr(legacy, 'weight')
    assert not hasattr(legacy, 'tier')
    assert not hasattr(legacy, 'description')
