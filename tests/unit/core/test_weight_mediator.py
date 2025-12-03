"""
Unit tests for WeightMediator class.

Tests weight validation, rebalancing suggestions, error collection,
and comprehensive validation reporting.
"""

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.weight_mediator import (
    ValidationErrorDetail,
    WeightMediator,
    WeightValidationError,
)
from writescore.dimensions.base_strategy import DimensionStrategy


class MockDimension(DimensionStrategy):
    """Mock dimension for testing."""

    def __init__(self, name: str, weight: float, tier: str = "CORE", skip_validation: bool = False):
        """
        Initialize mock dimension.

        Args:
            name: Dimension name
            weight: Dimension weight
            tier: Dimension tier
            skip_validation: If True, bypass registry validation (for testing invalid weights)
        """
        self._name = name
        self._weight = weight
        self._tier = tier

        if skip_validation:
            # Directly add to registry without validation
            normalized_name = name.lower()
            DimensionRegistry._dimensions[normalized_name] = self
            DimensionRegistry._name_map[normalized_name] = name
            if tier in DimensionRegistry._tiers:
                DimensionRegistry._tiers[tier].append(normalized_name)
        else:
            DimensionRegistry.register(self)

    @property
    def dimension_name(self) -> str:
        """Get dimension name."""
        return self._name

    @property
    def weight(self) -> float:
        """Get dimension weight."""
        return self._weight

    @property
    def tier(self) -> str:
        """Get dimension tier."""
        return self._tier

    @property
    def description(self) -> str:
        """Get dimension description."""
        return f"Mock dimension {self._name}"

    def analyze(self, text, lines, **kwargs):
        """Mock analyze method."""
        return {}

    def calculate_score(self, metrics):
        """Mock calculate_score method."""
        return 50.0

    def get_recommendations(self, score, metrics):
        """Mock get_recommendations method."""
        return []

    def get_tiers(self):
        """Mock get_tiers method."""
        return {"excellent": (90, 100), "good": (70, 89), "poor": (0, 69)}


class TestWeightMediator:
    """Test suite for WeightMediator."""

    def setup_method(self):
        """Clear registry before each test."""
        DimensionRegistry.clear()

    # ===== Valid Weights Tests =====

    def test_valid_weights_exactly_100(self):
        """Test valid weights that sum to exactly 100.0."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()
        assert mediator.validate_weights()
        assert len(mediator.validation_errors) == 0
        assert mediator.is_valid

    def test_valid_weights_within_tolerance_high(self):
        """Test valid weights at upper tolerance boundary (100.1)."""
        MockDimension(name="dim1", weight=50.05)
        MockDimension(name="dim2", weight=50.05)
        # Total: 100.1 (within default tolerance 0.1)

        mediator = WeightMediator()
        assert mediator.validate_weights()

    def test_valid_weights_within_tolerance_low(self):
        """Test valid weights at lower tolerance boundary (99.9)."""
        MockDimension(name="dim1", weight=49.95)
        MockDimension(name="dim2", weight=49.95)
        # Total: 99.9 (within default tolerance 0.1)

        mediator = WeightMediator()
        assert mediator.validate_weights()

    def test_tolerance_boundary_invalid_low(self):
        """Test invalid weights below tolerance (99.89)."""
        MockDimension(name="dim1", weight=49.945)
        MockDimension(name="dim2", weight=49.945)
        # Total: 99.89 (outside tolerance)

        mediator = WeightMediator()
        assert not mediator.validate_weights()
        assert any(e.error_type == "invalid_total" for e in mediator.validation_errors)

    def test_tolerance_boundary_invalid_high(self):
        """Test invalid weights above tolerance (100.11)."""
        MockDimension(name="dim1", weight=50.055)
        MockDimension(name="dim2", weight=50.055)
        # Total: 100.11 (outside tolerance)

        mediator = WeightMediator()
        assert not mediator.validate_weights()
        assert any(e.error_type == "invalid_total" for e in mediator.validation_errors)

    # ===== Custom Tolerance Tests =====

    def test_custom_tolerance_configuration(self):
        """Test custom tolerance configuration."""
        MockDimension(name="dim1", weight=49.5)
        MockDimension(name="dim2", weight=49.5)
        # Total: 99.0 (invalid with tolerance=0.1, valid with tolerance=1.0)

        # Should fail with default tolerance
        mediator_default = WeightMediator(tolerance=0.1)
        assert not mediator_default.validate_weights()

        # Should pass with custom tolerance
        mediator_custom = WeightMediator(tolerance=1.0)
        assert mediator_custom.validate_weights()

    def test_tolerance_validation(self):
        """Test tolerance parameter validation."""
        # Valid tolerances
        WeightMediator(tolerance=0.0)  # Should not raise
        WeightMediator(tolerance=10.0)  # Should not raise

        # Invalid tolerances
        with pytest.raises(ValueError, match="Tolerance must be between 0 and 10.0"):
            WeightMediator(tolerance=-0.1)

        with pytest.raises(ValueError, match="Tolerance must be between 0 and 10.0"):
            WeightMediator(tolerance=10.1)

    # ===== Invalid Weights Tests =====

    def test_invalid_total_too_high(self):
        """Test detection of total weight too high."""
        MockDimension(name="dim1", weight=60.0)
        MockDimension(name="dim2", weight=50.0)
        # Total: 110.0

        mediator = WeightMediator()
        assert not mediator.validate_weights()

        # Check structured error
        errors = [e for e in mediator.validation_errors if e.error_type == "invalid_total"]
        assert len(errors) == 1
        assert errors[0].current_value == 110.0
        assert errors[0].expected_value == 100.0
        assert "110.00%" in errors[0].message

    def test_invalid_total_too_low(self):
        """Test detection of total weight too low."""
        MockDimension(name="dim1", weight=40.0)
        MockDimension(name="dim2", weight=40.0)
        # Total: 80.0

        mediator = WeightMediator()
        assert not mediator.validate_weights()

        errors = [e for e in mediator.validation_errors if e.error_type == "invalid_total"]
        assert len(errors) == 1
        assert errors[0].current_value == 80.0

    def test_negative_weight_detection(self):
        """Test detection of negative weights."""
        MockDimension(name="dim1", weight=-5.0, skip_validation=True)
        MockDimension(name="dim2", weight=105.0, skip_validation=True)

        mediator = WeightMediator()
        assert not mediator.validate_weights()

        # Check structured error
        errors = [e for e in mediator.validation_errors if e.error_type == "negative_weight"]
        assert len(errors) == 1
        assert errors[0].dimension_name == "dim1"
        assert errors[0].current_value == -5.0
        assert errors[0].expected_value == ">= 0"

    def test_excessive_weight_detection(self):
        """Test detection of weights > 100."""
        MockDimension(name="dim1", weight=150.0, skip_validation=True)

        mediator = WeightMediator()
        assert not mediator.validate_weights()

        errors = [e for e in mediator.validation_errors if e.error_type == "excessive_weight"]
        assert len(errors) == 1
        assert errors[0].dimension_name == "dim1"
        assert errors[0].current_value == 150.0
        assert errors[0].expected_value == "<= 100"

    def test_zero_weight_warning(self):
        """Test zero weight generates warning and error."""
        MockDimension(name="dim1", weight=0.0)
        MockDimension(name="dim2", weight=100.0)

        mediator = WeightMediator()
        # Should fail due to zero weight error
        assert not mediator.validate_weights()

        # Check error
        errors = [e for e in mediator.validation_errors if e.error_type == "zero_weight"]
        assert len(errors) == 1
        assert errors[0].dimension_name == "dim1"

        # Check warning
        assert len(mediator.validation_warnings) == 1
        assert "dim1" in mediator.validation_warnings[0]

    def test_no_dimensions_registered(self):
        """Test error when no dimensions registered."""
        # Registry is empty
        mediator = WeightMediator()
        assert not mediator.validate_weights()

        errors = [e for e in mediator.validation_errors if e.error_type == "no_dimensions"]
        assert len(errors) == 1
        assert errors[0].dimension_name == "<registry>"
        assert errors[0].current_value == 0

    # ===== Rebalancing Tests =====

    def test_rebalancing_normal_case(self):
        """Test rebalancing with normal proportional scaling."""
        MockDimension(name="dim1", weight=60.0)
        MockDimension(name="dim2", weight=60.0)
        # Total: 120.0

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Should scale proportionally to 100.0
        assert suggestions["dim1"] == 50.0
        assert suggestions["dim2"] == 50.0
        assert sum(suggestions.values()) == 100.0

    def test_rebalancing_single_dimension(self):
        """Test rebalancing with single dimension (edge case)."""
        MockDimension(name="only_dim", weight=75.0)

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Single dimension should be set to 100.0
        assert suggestions["only_dim"] == 100.0

    def test_rebalancing_all_zero_weights(self):
        """Test rebalancing when all weights are zero (edge case)."""
        MockDimension(name="dim1", weight=0.0)
        MockDimension(name="dim2", weight=0.0)
        MockDimension(name="dim3", weight=0.0)

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Should use equal distribution
        assert suggestions["dim1"] == pytest.approx(33.33, rel=0.01)
        assert suggestions["dim2"] == pytest.approx(33.33, rel=0.01)
        assert suggestions["dim3"] == pytest.approx(33.33, rel=0.01)
        assert sum(suggestions.values()) == pytest.approx(100.0, abs=0.01)

    def test_rebalancing_with_negative_weights(self):
        """Test rebalancing with negative weights (edge case)."""
        MockDimension(name="dim1", weight=-10.0, skip_validation=True)
        MockDimension(name="dim2", weight=60.0)
        MockDimension(name="dim3", weight=40.0)
        # Total positive: 100.0

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Negative dimension should be set to 0.0
        assert suggestions["dim1"] == 0.0

        # Positive dimensions rebalanced
        assert suggestions["dim2"] == 60.0
        assert suggestions["dim3"] == 40.0
        assert sum(suggestions.values()) == 100.0

    def test_rebalancing_rounding_adjustment(self):
        """Test rebalancing adjusts rounding to ensure exact 100.0."""
        MockDimension(name="dim1", weight=33.33)
        MockDimension(name="dim2", weight=33.33)
        MockDimension(name="dim3", weight=33.33)
        # Total: 99.99

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Should sum to exactly 100.0
        assert sum(suggestions.values()) == 100.0

    # ===== Validation Report Tests =====

    def test_validation_report_structure(self):
        """Test comprehensive validation report structure."""
        MockDimension(name="dim1", weight=50.0, tier="CORE")
        MockDimension(name="dim2", weight=50.0, tier="ADVANCED")

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        # Check all required fields
        assert "is_valid" in report
        assert "total_weight" in report
        assert "expected_weight" in report
        assert "difference" in report
        assert "tolerance" in report
        assert "dimension_count" in report
        assert "dimension_weights" in report
        assert "dimensions_by_tier" in report
        assert "errors" in report
        assert "warnings" in report

        # Check values
        assert report["is_valid"]
        assert report["total_weight"] == 100.0
        assert report["dimension_count"] == 2
        assert len(report["dimension_weights"]) == 2

    def test_validation_report_includes_rebalancing_when_invalid(self):
        """Test validation report includes rebalancing suggestions when invalid."""
        MockDimension(name="dim1", weight=60.0)
        MockDimension(name="dim2", weight=60.0)

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        assert not report["is_valid"]
        assert "suggested_rebalancing" in report
        assert report["suggested_rebalancing"]["dim1"] == 50.0
        assert report["suggested_rebalancing"]["dim2"] == 50.0

    def test_validation_report_tier_breakdown(self):
        """Test tier breakdown in validation report."""
        MockDimension(name="core1", weight=30.0, tier="CORE")
        MockDimension(name="core2", weight=20.0, tier="CORE")
        MockDimension(name="adv1", weight=50.0, tier="ADVANCED")

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        tier_data = report["dimensions_by_tier"]

        # Check CORE tier
        assert tier_data["CORE"]["total_weight"] == 50.0
        assert tier_data["CORE"]["dimension_count"] == 2
        assert len(tier_data["CORE"]["dimensions"]) == 2

        # Check ADVANCED tier
        assert tier_data["ADVANCED"]["total_weight"] == 50.0
        assert tier_data["ADVANCED"]["dimension_count"] == 1

    # ===== require_valid() Tests =====

    def test_require_valid_passes_when_valid(self):
        """Test require_valid() does not raise when weights are valid."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()
        mediator.require_valid()  # Should not raise

    def test_require_valid_raises_when_invalid(self):
        """Test require_valid() raises WeightValidationError when invalid."""
        MockDimension(name="dim1", weight=60.0)
        MockDimension(name="dim2", weight=60.0)

        mediator = WeightMediator()

        with pytest.raises(WeightValidationError) as exc_info:
            mediator.require_valid()

        # Check exception attributes
        e = exc_info.value
        assert len(e.errors) > 0
        assert e.total_weight == 120.0
        assert e.expected_weight == 100.0
        assert e.tolerance == 0.1

    def test_require_valid_exception_message(self):
        """Test WeightValidationError message formatting."""
        MockDimension(name="dim1", weight=110.0, skip_validation=True)

        mediator = WeightMediator()

        with pytest.raises(WeightValidationError) as exc_info:
            mediator.require_valid()

        error_str = str(exc_info.value)

        # Check message contains key information
        assert "Dimension weight validation failed" in error_str
        assert "Total weight: 110.00%" in error_str
        assert "Expected: 100.00%" in error_str
        assert "Difference: +10.00%" in error_str

    # ===== __repr__ and __str__ Tests =====

    def test_weight_mediator_repr(self):
        """Test __repr__ method."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()
        repr_str = repr(mediator)

        assert "WeightMediator" in repr_str
        assert "dimensions=2" in repr_str
        assert "total_weight=100.00" in repr_str
        assert "tolerance=0.1" in repr_str
        assert "is_valid=True" in repr_str

    def test_weight_mediator_str(self):
        """Test __str__ method."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()
        str_repr = str(mediator)

        assert "WeightMediator" in str_repr
        assert "2 dimensions" in str_repr
        assert "100.00%" in str_repr
        assert "VALID" in str_repr

    def test_validation_error_detail_repr(self):
        """Test ValidationErrorDetail __repr__ method."""
        error = ValidationErrorDetail(
            dimension_name="test_dim",
            error_type="negative_weight",
            current_value=-5.0,
            expected_value=">= 0",
            message="Test error",
        )

        repr_str = repr(error)
        assert "ValidationErrorDetail" in repr_str
        assert "test_dim" in repr_str
        assert "negative_weight" in repr_str

    # ===== Helper Method Tests =====

    def test_get_total_weight(self):
        """Test get_total_weight() helper method."""
        MockDimension(name="dim1", weight=30.0)
        MockDimension(name="dim2", weight=40.0)
        MockDimension(name="dim3", weight=20.0)

        mediator = WeightMediator()
        assert mediator.get_total_weight() == 90.0

    def test_format_percentage(self):
        """Test _format_percentage() helper method."""
        mediator = WeightMediator()

        # Without sign
        assert mediator._format_percentage(105.5) == "105.50%"
        assert mediator._format_percentage(99.9) == "99.90%"

        # With sign
        assert mediator._format_percentage(5.5, show_sign=True) == "+5.50%"
        assert mediator._format_percentage(-3.2, show_sign=True) == "-3.20%"

    # ===== Edge Case Tests =====

    def test_rebalancing_with_mixed_weights(self):
        """Test rebalancing with mixed positive/negative/zero (comprehensive edge case)."""
        MockDimension(name="negative", weight=-5.0, skip_validation=True)
        MockDimension(name="zero", weight=0.0)
        MockDimension(name="positive1", weight=30.0)
        MockDimension(name="positive2", weight=20.0)

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Negative and zero should be 0.0
        assert suggestions["negative"] == 0.0
        assert suggestions["zero"] == 0.0

        # Positives should be rebalanced proportionally
        assert suggestions["positive1"] == 60.0
        assert suggestions["positive2"] == 40.0
        assert sum(suggestions.values()) == 100.0

    def test_validation_error_detail_to_dict(self):
        """Test ValidationErrorDetail.to_dict() method."""
        error = ValidationErrorDetail(
            dimension_name="test_dim",
            error_type="negative_weight",
            current_value=-5.0,
            expected_value=">= 0",
            message="Test error message",
        )

        error_dict = error.to_dict()

        assert error_dict["dimension_name"] == "test_dim"
        assert error_dict["error_type"] == "negative_weight"
        assert error_dict["current_value"] == -5.0
        assert error_dict["expected_value"] == ">= 0"
        assert error_dict["message"] == "Test error message"

    def test_weight_validation_error_to_dict(self):
        """Test WeightValidationError.to_dict() method."""
        error_detail = ValidationErrorDetail(
            dimension_name="test",
            error_type="invalid_total",
            current_value=110.0,
            expected_value=100.0,
            message="Test",
        )

        exc = WeightValidationError(
            message="Test error",
            errors=[error_detail],
            total_weight=110.0,
            expected_weight=100.0,
            tolerance=0.5,
        )

        exc_dict = exc.to_dict()

        assert exc_dict["message"] == "Test error"
        assert exc_dict["total_weight"] == 110.0
        assert exc_dict["expected_weight"] == 100.0
        assert exc_dict["tolerance"] == 0.5
        assert exc_dict["error_count"] == 1
        assert len(exc_dict["errors"]) == 1

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are collected."""
        MockDimension(name="negative", weight=-5.0, skip_validation=True)
        MockDimension(name="excessive", weight=150.0, skip_validation=True)
        MockDimension(name="zero", weight=0.0)

        mediator = WeightMediator()
        assert not mediator.validate_weights()

        # Should have at least 4 errors: negative, excessive, zero, invalid_total
        assert len(mediator.validation_errors) >= 4

        error_types = {e.error_type for e in mediator.validation_errors}
        assert "negative_weight" in error_types
        assert "excessive_weight" in error_types
        assert "zero_weight" in error_types
        assert "invalid_total" in error_types

    def test_empty_registry_rebalancing(self):
        """Test rebalancing with empty registry returns empty dict."""
        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        assert suggestions == {}

    def test_get_validation_report_json_format(self):
        """Test validation report with JSON format."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()
        report_json = mediator.get_validation_report(format="json")

        # Should be a JSON string
        assert isinstance(report_json, str)
        assert '"is_valid": true' in report_json or '"is_valid":true' in report_json

    def test_is_valid_property(self):
        """Test is_valid property behaves correctly."""
        MockDimension(name="dim1", weight=50.0)
        MockDimension(name="dim2", weight=50.0)

        mediator = WeightMediator()

        # Should be valid
        assert mediator.is_valid

        # Clear registry and add invalid weights
        DimensionRegistry.clear()
        MockDimension(name="dim1", weight=60.0)
        MockDimension(name="dim2", weight=60.0)

        mediator2 = WeightMediator()
        assert not mediator2.is_valid
