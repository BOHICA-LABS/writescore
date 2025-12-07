"""
Integration test for dimension self-registration.

Tests that dimensions can self-register with the DimensionRegistry
and that weights are correctly assigned.
"""

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.burstiness import BurstinessDimension
from writescore.dimensions.perplexity import PerplexityDimension


class TestDimensionRegistration:
    """Test dimension self-registration functionality."""

    def test_perplexity_registration(self):
        """Test that PerplexityDimension registers correctly."""
        DimensionRegistry.clear()
        dim = PerplexityDimension()

        # get_all() returns a list of dimensions
        all_dims = DimensionRegistry.get_all()
        assert len(all_dims) == 1

        # get() returns the dimension by name
        registered = DimensionRegistry.get("perplexity")

        assert registered.dimension_name == "perplexity"
        assert registered.weight == 2.8  # Weight after rebalancing to 100%
        assert registered.tier == "ADVANCED"  # ADVANCED tier (requires language model)
        assert dim is registered  # Same instance

    def test_burstiness_registration(self):
        """Test that BurstinessDimension registers correctly."""
        DimensionRegistry.clear()
        dim = BurstinessDimension()

        # get_all() returns a list of dimensions
        all_dims = DimensionRegistry.get_all()
        assert len(all_dims) == 1

        # get() returns the dimension by name
        registered = DimensionRegistry.get("burstiness")

        assert registered.dimension_name == "burstiness"
        assert registered.weight == 5.5  # Weight after rebalancing to 100%
        assert registered.tier == "CORE"
        assert dim is registered  # Same instance

    def test_multiple_dimension_registration(self):
        """Test that multiple dimensions can register together."""
        DimensionRegistry.clear()
        perp = PerplexityDimension()
        burst = BurstinessDimension()

        # get_all() returns a list
        all_dims = DimensionRegistry.get_all()
        assert len(all_dims) == 2

        # Verify both dimensions are registered
        assert DimensionRegistry.get("perplexity") is perp
        assert DimensionRegistry.get("burstiness") is burst

        # Verify total weight
        total_weight = sum(d.weight for d in all_dims)
        assert total_weight == 8.3  # 2.8 (perplexity) + 5.5 (burstiness)

    def test_duplicate_registration_prevention(self):
        """Test that duplicate registration is idempotent (registry stores only one)."""
        DimensionRegistry.clear()
        dim1 = PerplexityDimension()

        # Creating a second instance is allowed (different Python objects)
        dim2 = PerplexityDimension()
        assert dim1 is not dim2, "Different Python objects are created"

        # But registry is idempotent - only one dimension is stored
        all_dims = DimensionRegistry.get_all()
        assert (
            len(all_dims) == 1
        ), "Registry should store only one dimension despite multiple instantiations"

    def test_backward_compatibility_alias(self):
        """Test that backward compatibility aliases work."""
        from writescore.dimensions.burstiness import BurstinessAnalyzer
        from writescore.dimensions.perplexity import PerplexityAnalyzer

        # Aliases should point to the same class (check name and module)
        # Using name/module comparison instead of 'is' to avoid test isolation issues
        assert PerplexityAnalyzer.__name__ == PerplexityDimension.__name__
        assert PerplexityAnalyzer.__module__ == PerplexityDimension.__module__
        assert BurstinessAnalyzer.__name__ == BurstinessDimension.__name__
        assert BurstinessAnalyzer.__module__ == BurstinessDimension.__module__

        # Verify aliases are actually usable (can instantiate and work the same)
        DimensionRegistry.clear()
        alias_instance = PerplexityAnalyzer()
        assert alias_instance.dimension_name == "perplexity"
        assert alias_instance.weight == 2.8  # Weight after rebalancing to 100%
