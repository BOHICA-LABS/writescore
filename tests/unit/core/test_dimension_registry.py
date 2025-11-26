"""
Comprehensive unit tests for DimensionRegistry.

Tests cover:
- Class-based (non-singleton) behavior
- Dimension registration success and validation
- Duplicate prevention
- Case-insensitive lookup
- Tier retrieval
- Exception handling
- Thread safety
- Performance with 100+ dimensions
"""

import pytest
import threading
import time
from writescore.core.dimension_registry import (
    DimensionRegistry,
    register_dimension,
    get_dimension,
    list_dimensions
)
from writescore.core.exceptions import (
    AIPatternAnalyzerError,
    DimensionNotFoundError,
    DuplicateDimensionError,
    InvalidTierError,
    InvalidWeightError
)


class MockDimension:
    """Mock dimension for testing."""

    def __init__(self, name='mock', weight=10.0, tier='CORE'):
        self.dimension_name = name
        self.weight = weight
        self.tier = tier


class TestDimensionRegistry:
    """Test suite for DimensionRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        DimensionRegistry.clear()

    def test_class_based_not_singleton(self):
        """Verify registry uses class-level storage, not singleton instances."""
        # No need to instantiate - all methods are classmethods
        assert DimensionRegistry.get_count() == 0

    def test_dimension_registration_success(self):
        """Test successful dimension registration."""
        dim = MockDimension()
        result = DimensionRegistry.register(dim)

        assert result is dim
        assert DimensionRegistry.get_count() == 1
        assert DimensionRegistry.has('mock')

    def test_duplicate_registration_raises_error(self):
        """Test duplicate registration raises DuplicateDimensionError."""
        dim1 = MockDimension()
        dim2 = MockDimension()  # Same name

        DimensionRegistry.register(dim1)

        with pytest.raises(DuplicateDimensionError) as exc_info:
            DimensionRegistry.register(dim2, allow_overwrite=False)

        assert exc_info.value.dimension_name == 'mock'

    def test_case_insensitive_lookup(self):
        """Test dimension names are case-insensitive."""
        dim = MockDimension(name='MyDimension')
        DimensionRegistry.register(dim)

        # All these should work
        assert DimensionRegistry.get('mydimension') is dim
        assert DimensionRegistry.get('MyDimension') is dim
        assert DimensionRegistry.get('MYDIMENSION') is dim
        assert DimensionRegistry.has('mydimension')
        assert DimensionRegistry.has('MYDIMENSION')

    def test_get_nonexistent_dimension_raises_error(self):
        """Test getting non-existent dimension raises DimensionNotFoundError."""
        with pytest.raises(DimensionNotFoundError) as exc_info:
            DimensionRegistry.get('nonexistent')

        # Error message should list registered dimensions
        assert 'nonexistent' in str(exc_info.value)
        assert exc_info.value.dimension_name == 'nonexistent'

    def test_tier_retrieval(self):
        """Test retrieving dimensions by tier."""
        core_dim = MockDimension(name='core1', tier='CORE')
        advanced_dim = MockDimension(name='advanced1', tier='ADVANCED')
        core_dim2 = MockDimension(name='core2', tier='CORE')

        DimensionRegistry.register(core_dim)
        DimensionRegistry.register(advanced_dim)
        DimensionRegistry.register(core_dim2)

        core_dims = DimensionRegistry.get_by_tier('CORE')
        assert len(core_dims) == 2
        assert core_dim in core_dims
        assert core_dim2 in core_dims

        advanced_dims = DimensionRegistry.get_by_tier('ADVANCED')
        assert len(advanced_dims) == 1
        assert advanced_dim in advanced_dims

    def test_invalid_tier_raises_error(self):
        """Test invalid tier raises InvalidTierError."""
        dim = MockDimension(tier='INVALID')

        with pytest.raises(InvalidTierError) as exc_info:
            DimensionRegistry.register(dim)

        assert exc_info.value.tier == 'INVALID'
        assert 'ADVANCED' in str(exc_info.value)  # Shows valid tiers

    def test_invalid_weight_raises_error(self):
        """Test invalid weight raises InvalidWeightError."""
        dim_negative = MockDimension(weight=-5.0)
        dim_too_high = MockDimension(name='high', weight=150.0)

        with pytest.raises(InvalidWeightError) as exc_info1:
            DimensionRegistry.register(dim_negative)
        assert exc_info1.value.weight == -5.0

        with pytest.raises(InvalidWeightError) as exc_info2:
            DimensionRegistry.register(dim_too_high)
        assert exc_info2.value.weight == 150.0

    def test_get_all_returns_list(self):
        """Test get_all() returns List[DimensionStrategy]."""
        dim1 = MockDimension(name='dim1')
        dim2 = MockDimension(name='dim2')

        DimensionRegistry.register(dim1)
        DimensionRegistry.register(dim2)

        all_dims = DimensionRegistry.get_all()

        assert isinstance(all_dims, list)
        assert len(all_dims) == 2
        assert dim1 in all_dims
        assert dim2 in all_dims

    def test_get_tiers_summary(self):
        """Test tiers summary includes counts and names."""
        DimensionRegistry.register(MockDimension(name='core1', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='core2', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='adv1', tier='ADVANCED'))

        summary = DimensionRegistry.get_tiers_summary()

        assert summary['CORE']['count'] == 2
        assert 'core1' in summary['CORE']['dimensions']
        assert 'core2' in summary['CORE']['dimensions']
        assert summary['ADVANCED']['count'] == 1
        assert summary['SUPPORTING']['count'] == 0

    def test_clear_removes_all_dimensions(self):
        """Test clear() removes all dimensions."""
        DimensionRegistry.register(MockDimension(name='dim1'))
        DimensionRegistry.register(MockDimension(name='dim2'))

        assert DimensionRegistry.get_count() == 2

        DimensionRegistry.clear()

        assert DimensionRegistry.get_count() == 0
        assert not DimensionRegistry.has('dim1')

    def test_repr_shows_useful_info(self):
        """Test __repr__ shows dimension count and tier breakdown."""
        DimensionRegistry.register(MockDimension(name='dim1', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='dim2', tier='ADVANCED'))

        repr_str = DimensionRegistry.__repr__()

        assert 'total=2' in repr_str
        assert 'CORE' in repr_str
        assert 'ADVANCED' in repr_str

    def test_thread_safety_concurrent_registration(self):
        """Test concurrent registrations are thread-safe."""
        num_threads = 10
        dims_per_thread = 10

        def register_dimensions(thread_id):
            for i in range(dims_per_thread):
                dim = MockDimension(name=f'dim_{thread_id}_{i}')
                DimensionRegistry.register(dim)

        threads = [
            threading.Thread(target=register_dimensions, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly num_threads * dims_per_thread dimensions
        assert DimensionRegistry.get_count() == num_threads * dims_per_thread

    def test_performance_with_100_dimensions(self):
        """Test registry performs well with 100+ dimensions."""
        # Register 100 dimensions
        for i in range(100):
            tier = ['CORE', 'ADVANCED', 'SUPPORTING', 'STRUCTURAL'][i % 4]
            DimensionRegistry.register(MockDimension(name=f'dim_{i}', tier=tier))

        # Test retrieval performance (should be O(1))
        start = time.time()
        for _ in range(1000):
            DimensionRegistry.get('dim_50')
        elapsed = time.time() - start

        # 1000 lookups should take < 10ms
        assert elapsed < 0.01

        # Test get_all performance
        start = time.time()
        all_dims = DimensionRegistry.get_all()
        elapsed = time.time() - start

        assert len(all_dims) == 100
        assert elapsed < 0.01  # Should be very fast

    def test_get_count(self):
        """Test get_count returns accurate count."""
        assert DimensionRegistry.get_count() == 0

        DimensionRegistry.register(MockDimension(name='dim1'))
        assert DimensionRegistry.get_count() == 1

        DimensionRegistry.register(MockDimension(name='dim2'))
        assert DimensionRegistry.get_count() == 2

    def test_has_method(self):
        """Test has method returns correct boolean."""
        assert not DimensionRegistry.has('test')

        DimensionRegistry.register(MockDimension(name='test'))
        assert DimensionRegistry.has('test')
        assert DimensionRegistry.has('TEST')  # Case insensitive

    def test_get_by_tier_empty(self):
        """Test get_by_tier returns empty list for tier with no dimensions."""
        supporting_dims = DimensionRegistry.get_by_tier('SUPPORTING')
        assert isinstance(supporting_dims, list)
        assert len(supporting_dims) == 0

    def test_get_by_tier_invalid_tier(self):
        """Test get_by_tier raises InvalidTierError for invalid tier."""
        with pytest.raises(InvalidTierError) as exc_info:
            DimensionRegistry.get_by_tier('INVALID_TIER')

        assert exc_info.value.tier == 'INVALID_TIER'
        assert exc_info.value.valid_tiers == DimensionRegistry.VALID_TIERS

    def test_empty_dimension_name(self):
        """Test registration with empty name raises ValueError."""
        dim = MockDimension(name='')

        with pytest.raises(ValueError) as exc_info:
            DimensionRegistry.register(dim)

        assert 'non-empty string' in str(exc_info.value)

    def test_edge_case_weight_boundaries(self):
        """Test weight validation at boundary values."""
        # Valid boundary values
        dim_zero = MockDimension(name='zero', weight=0.0)
        dim_hundred = MockDimension(name='hundred', weight=100.0)

        DimensionRegistry.register(dim_zero)
        DimensionRegistry.register(dim_hundred)

        assert DimensionRegistry.get_count() == 2

        # Invalid boundary values
        dim_negative = MockDimension(name='negative', weight=-0.1)
        dim_over = MockDimension(name='over', weight=100.1)

        with pytest.raises(InvalidWeightError):
            DimensionRegistry.register(dim_negative)

        with pytest.raises(InvalidWeightError):
            DimensionRegistry.register(dim_over)


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Test suite for module-level convenience functions."""

    def setup_method(self):
        """Clear registry before each test."""
        DimensionRegistry.clear()

    def test_register_dimension(self):
        """Test register_dimension convenience function."""
        dim = MockDimension(name='test')
        result = register_dimension(dim)

        assert result is dim
        assert DimensionRegistry.has('test')

    def test_get_dimension(self):
        """Test get_dimension convenience function."""
        dim = MockDimension(name='test')
        register_dimension(dim)

        retrieved = get_dimension('test')
        assert retrieved is dim

    def test_list_dimensions(self):
        """Test list_dimensions convenience function."""
        dim1 = MockDimension(name='dim1')
        dim2 = MockDimension(name='dim2')

        register_dimension(dim1)
        register_dimension(dim2)

        all_dims = list_dimensions()

        assert len(all_dims) == 2
        assert dim1 in all_dims
        assert dim2 in all_dims


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestRegistryExceptions:
    """Test suite for registry exception classes."""

    def test_dimension_not_found_error_attributes(self):
        """Test DimensionNotFoundError has dimension_name attribute."""
        error = DimensionNotFoundError(
            "Dimension 'foo' not found",
            dimension_name='foo'
        )

        assert error.dimension_name == 'foo'
        assert 'foo' in str(error)

    def test_duplicate_dimension_error_attributes(self):
        """Test DuplicateDimensionError has dimension_name attribute."""
        error = DuplicateDimensionError(
            "Dimension 'bar' already registered",
            dimension_name='bar'
        )

        assert error.dimension_name == 'bar'
        assert 'bar' in str(error)

    def test_invalid_tier_error_attributes(self):
        """Test InvalidTierError has tier and valid_tiers attributes."""
        valid_tiers = {'ADVANCED', 'CORE', 'SUPPORTING', 'STRUCTURAL'}
        error = InvalidTierError(
            "Invalid tier 'INVALID'",
            tier='INVALID',
            valid_tiers=valid_tiers
        )

        assert error.tier == 'INVALID'
        assert error.valid_tiers == valid_tiers
        assert 'INVALID' in str(error)

    def test_invalid_weight_error_attributes(self):
        """Test InvalidWeightError has weight and valid_range attributes."""
        error = InvalidWeightError(
            "Weight 150 out of range",
            weight=150,
            valid_range=(0, 100)
        )

        assert error.weight == 150
        assert error.valid_range == (0, 100)
        assert '150' in str(error)

    def test_exception_repr_methods(self):
        """Test all exceptions have proper __repr__ methods."""
        error1 = DimensionNotFoundError("msg", dimension_name='test')
        assert 'DimensionNotFoundError' in repr(error1)
        assert 'test' in repr(error1)

        error2 = DuplicateDimensionError("msg", dimension_name='dup')
        assert 'DuplicateDimensionError' in repr(error2)

        error3 = InvalidTierError("msg", tier='BAD')
        assert 'InvalidTierError' in repr(error3)

        error4 = InvalidWeightError("msg", weight=200)
        assert 'InvalidWeightError' in repr(error4)

    def test_exception_inheritance(self):
        """Test all registry exceptions inherit from AIPatternAnalyzerError."""
        assert issubclass(DimensionNotFoundError, AIPatternAnalyzerError)
        assert issubclass(DuplicateDimensionError, AIPatternAnalyzerError)
        assert issubclass(InvalidTierError, AIPatternAnalyzerError)
        assert issubclass(InvalidWeightError, AIPatternAnalyzerError)

        # All should also inherit from base Exception
        assert issubclass(AIPatternAnalyzerError, Exception)

    def test_base_exception_str_and_repr(self):
        """Test base AIPatternAnalyzerError str and repr."""
        error = AIPatternAnalyzerError("Test error message")

        assert str(error) == "Test error message"
        assert 'AIPatternAnalyzerError' in repr(error)
        assert 'Test error message' in repr(error)

    def test_invalid_weight_error_default_range(self):
        """Test InvalidWeightError uses default range when not provided."""
        error = InvalidWeightError("Weight out of range", weight=150)

        assert error.valid_range == (0, 100)
