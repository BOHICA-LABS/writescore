"""
Integration tests for WeightMediator with dimension registry.

Tests validation and reporting with multi-tier dimension configurations.
"""

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.weight_mediator import WeightMediator, WeightValidationError
from writescore.dimensions.base_strategy import DimensionStrategy


class TestDimension(DimensionStrategy):
    """Test dimension for integration testing."""

    def __init__(self, name: str, weight: float, tier: str):
        """Initialize test dimension."""
        self._name = name
        self._weight = weight
        self._tier = tier
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
        return f"Test dimension {self._name}"

    def analyze(self, text, lines, **kwargs):
        """Analyze text (mock)."""
        return {}

    def calculate_score(self, metrics):
        """Calculate score (mock)."""
        return 50.0

    def get_recommendations(self, score, metrics):
        """Get recommendations (mock)."""
        return []

    def get_tiers(self):
        """Get tiers (mock)."""
        return {"excellent": (90, 100), "good": (70, 89), "poor": (0, 69)}


class TestWeightValidationIntegration:
    """Integration tests with dimension registry."""

    def setup_method(self):
        """Clear registry before each test."""
        DimensionRegistry.clear()

    def test_validation_with_multiple_dimensions_all_tiers(self):
        """Test validation with dimensions across all tiers."""
        # Create dimensions across all tiers
        TestDimension(name="advanced1", weight=15.0, tier="ADVANCED")
        TestDimension(name="advanced2", weight=20.0, tier="ADVANCED")
        TestDimension(name="core1", weight=20.0, tier="CORE")
        TestDimension(name="core2", weight=15.0, tier="CORE")
        TestDimension(name="supporting1", weight=15.0, tier="SUPPORTING")
        TestDimension(name="supporting2", weight=10.0, tier="SUPPORTING")
        TestDimension(name="structural1", weight=5.0, tier="STRUCTURAL")

        mediator = WeightMediator()

        # Should be valid (total = 100.0)
        assert mediator.validate_weights()
        assert mediator.is_valid
        assert len(mediator.validation_errors) == 0

        # Verify total weight
        assert mediator.get_total_weight() == 100.0

    def test_tier_based_weight_reporting(self):
        """Test tier-based weight breakdown with dimensions."""
        # Create dimensions with specific tier distribution
        TestDimension(name="adv1", weight=30.0, tier="ADVANCED")
        TestDimension(name="core1", weight=25.0, tier="CORE")
        TestDimension(name="core2", weight=20.0, tier="CORE")
        TestDimension(name="supporting1", weight=15.0, tier="SUPPORTING")
        TestDimension(name="structural1", weight=10.0, tier="STRUCTURAL")

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        tier_data = report["dimensions_by_tier"]

        # Verify tier totals
        assert tier_data["ADVANCED"]["total_weight"] == 30.0
        assert tier_data["ADVANCED"]["dimension_count"] == 1
        assert tier_data["CORE"]["total_weight"] == 45.0
        assert tier_data["CORE"]["dimension_count"] == 2
        assert tier_data["SUPPORTING"]["total_weight"] == 15.0
        assert tier_data["SUPPORTING"]["dimension_count"] == 1
        assert tier_data["STRUCTURAL"]["total_weight"] == 10.0
        assert tier_data["STRUCTURAL"]["dimension_count"] == 1

        # Verify dimension details in tiers
        assert len(tier_data["CORE"]["dimensions"]) == 2
        core_names = [d["name"] for d in tier_data["CORE"]["dimensions"]]
        assert "core1" in core_names
        assert "core2" in core_names

    def test_validation_report_with_real_registry(self):
        """Test comprehensive validation report with real registry."""
        # Create realistic dimension configuration
        TestDimension(name="perplexity", weight=18.0, tier="CORE")
        TestDimension(name="burstiness", weight=17.0, tier="CORE")
        TestDimension(name="advanced1", weight=35.0, tier="ADVANCED")
        TestDimension(name="supporting1", weight=20.0, tier="SUPPORTING")
        TestDimension(name="structural1", weight=10.0, tier="STRUCTURAL")

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        # Verify report structure
        assert report["is_valid"]
        assert report["dimension_count"] == 5
        assert report["total_weight"] == 100.0
        assert report["tolerance"] == 0.1
        assert len(report["errors"]) == 0
        assert len(report["warnings"]) == 0

        # Verify dimension weights in report
        assert report["dimension_weights"]["perplexity"] == 18.0
        assert report["dimension_weights"]["burstiness"] == 17.0

        # Should not have rebalancing suggestions when valid
        assert "suggested_rebalancing" not in report

    def test_require_valid_with_registry_integration(self):
        """Test require_valid() enforcement with real registry."""
        # Create valid configuration
        TestDimension(name="dim1", weight=50.0, tier="CORE")
        TestDimension(name="dim2", weight=50.0, tier="ADVANCED")

        mediator = WeightMediator()

        # Should not raise
        mediator.require_valid()

    def test_require_valid_raises_with_invalid_registry_config(self):
        """Test require_valid() raises exception with invalid configuration."""
        # Create invalid configuration
        TestDimension(name="dim1", weight=60.0, tier="CORE")
        TestDimension(name="dim2", weight=50.0, tier="ADVANCED")
        # Total: 110.0 (invalid)

        mediator = WeightMediator()

        with pytest.raises(WeightValidationError) as exc_info:
            mediator.require_valid()

        # Verify exception details
        e = exc_info.value
        assert e.total_weight == 110.0
        assert len(e.errors) > 0

        # Verify error message includes useful information
        error_str = str(e)
        assert "110.00%" in error_str
        assert "100.00%" in error_str

    def test_rebalancing_with_multi_tier_configuration(self):
        """Test rebalancing suggestions with multi-tier dimensions."""
        # Create imbalanced configuration
        TestDimension(name="advanced1", weight=40.0, tier="ADVANCED")
        TestDimension(name="core1", weight=30.0, tier="CORE")
        TestDimension(name="supporting1", weight=20.0, tier="SUPPORTING")
        TestDimension(name="structural1", weight=20.0, tier="STRUCTURAL")
        # Total: 110.0 (needs rebalancing)

        mediator = WeightMediator()
        suggestions = mediator.suggest_rebalancing()

        # Verify suggestions sum to 100.0
        assert sum(suggestions.values()) == 100.0

        # Verify proportional scaling preserved relationships
        # Original: 40, 30, 20, 20 -> Scale factor: 100/110 = 0.909...
        assert suggestions["advanced1"] == pytest.approx(36.36, rel=0.01)
        assert suggestions["core1"] == pytest.approx(27.27, rel=0.01)
        assert suggestions["supporting1"] == pytest.approx(18.18, rel=0.01)
        assert suggestions["structural1"] == pytest.approx(18.18, rel=0.01)

    def test_validation_report_includes_rebalancing_when_invalid(self):
        """Test validation report includes rebalancing for invalid config."""
        # Create invalid configuration
        TestDimension(name="dim1", weight=70.0, tier="CORE")
        TestDimension(name="dim2", weight=70.0, tier="ADVANCED")
        # Total: 140.0

        mediator = WeightMediator()
        report = mediator.get_validation_report()

        # Should be invalid
        assert not report["is_valid"]
        assert report["total_weight"] == 140.0

        # Should include rebalancing suggestions
        assert "suggested_rebalancing" in report
        assert report["suggested_rebalancing"]["dim1"] == 50.0
        assert report["suggested_rebalancing"]["dim2"] == 50.0

    def test_custom_tolerance_with_registry(self):
        """Test custom tolerance configuration with real registry."""
        # Create configuration at edge of default tolerance
        TestDimension(name="dim1", weight=49.5, tier="CORE")
        TestDimension(name="dim2", weight=49.5, tier="ADVANCED")
        # Total: 99.0 (1.0% off)

        # Should fail with default tolerance (0.1%)
        mediator_default = WeightMediator(tolerance=0.1)
        assert not mediator_default.validate_weights()

        # Should pass with custom tolerance (1.0%)
        mediator_custom = WeightMediator(tolerance=1.0)
        assert mediator_custom.validate_weights()

    def test_empty_registry_validation(self):
        """Test validation behavior with empty registry."""
        # Registry is empty (no dimensions registered)
        mediator = WeightMediator()

        # Should be invalid
        assert not mediator.validate_weights()

        # Should have no_dimensions error
        errors = [e for e in mediator.validation_errors if e.error_type == "no_dimensions"]
        assert len(errors) == 1

    def test_mediator_with_custom_registry_instance(self):
        """Test WeightMediator with custom registry instance."""
        # This tests the registry parameter in WeightMediator.__init__
        # For now, we test with None (uses class-level registry)
        TestDimension(name="dim1", weight=50.0, tier="CORE")
        TestDimension(name="dim2", weight=50.0, tier="ADVANCED")

        # Test with default (None) registry
        mediator = WeightMediator(registry=None)
        assert mediator.validate_weights()

    def test_validation_with_ten_dimensions(self):
        """Test validation with 10 dimensions (simulating full analyzer)."""
        # Create 10 dimensions with weights that sum to 100.0
        weights = [12.0, 11.0, 10.0, 10.0, 9.0, 9.0, 9.0, 10.0, 10.0, 10.0]
        tiers = [
            "ADVANCED",
            "ADVANCED",
            "CORE",
            "CORE",
            "CORE",
            "SUPPORTING",
            "SUPPORTING",
            "SUPPORTING",
            "STRUCTURAL",
            "STRUCTURAL",
        ]

        for i, (weight, tier) in enumerate(zip(weights, tiers), 1):
            TestDimension(name=f"dim{i}", weight=weight, tier=tier)

        mediator = WeightMediator()

        # Should be valid
        assert mediator.validate_weights()
        assert mediator.get_total_weight() == 100.0

        # Verify tier distribution
        report = mediator.get_validation_report()
        tier_data = report["dimensions_by_tier"]

        # ADVANCED: 12 + 11 = 23
        assert tier_data["ADVANCED"]["total_weight"] == 23.0
        # CORE: 10 + 10 + 9 = 29
        assert tier_data["CORE"]["total_weight"] == 29.0
        # SUPPORTING: 9 + 9 + 10 = 28
        assert tier_data["SUPPORTING"]["total_weight"] == 28.0
        # STRUCTURAL: 10 + 10 = 20
        assert tier_data["STRUCTURAL"]["total_weight"] == 20.0
