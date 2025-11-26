"""Unit tests for DimensionStrategy configuration helper methods.

Tests cover:
- _prepare_text() for each mode
- _aggregate_sampled_metrics() with various data types
- Config=None maintains current behavior
- Edge cases and error handling
"""

import pytest

from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

# ============================================================================
# Test Dimension Implementation
# ============================================================================

class TestDimension(DimensionStrategy):
    """Concrete test dimension for testing base class functionality."""

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

    def analyze(self, text: str, lines=None, config=None, **kwargs):
        return {"test_metric": 42}

    def calculate_score(self, metrics):
        return 85.0

    def get_recommendations(self, score, metrics):
        return ["Test recommendation"]

    def get_tiers(self):
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
def test_dimension():
    """Create test dimension instance."""
    return TestDimension()


@pytest.fixture
def short_text():
    """Short text < 2000 chars."""
    return "Test text. " * 100  # ~1100 chars


@pytest.fixture
def medium_text():
    """Medium text 5000-10000 chars."""
    return "Test paragraph. " * 400  # ~6800 chars


@pytest.fixture
def long_text():
    """Long text > 50000 chars."""
    return "Test chapter text. " * 3000  # ~57000 chars


# ============================================================================
# Test _prepare_text() - FAST Mode
# ============================================================================

def test_prepare_text_fast_mode_always_truncates(test_dimension, long_text):
    """Test FAST mode always truncates to 2000 chars regardless of text length."""
    config = AnalysisConfig(mode=AnalysisMode.FAST)

    result = test_dimension._prepare_text(long_text, config, "test_dimension")

    assert isinstance(result, str)
    assert len(result) == 2000


def test_prepare_text_fast_mode_short_text(test_dimension, short_text):
    """Test FAST mode with text already < 2000 chars."""
    config = AnalysisConfig(mode=AnalysisMode.FAST)

    result = test_dimension._prepare_text(short_text, config, "test_dimension")

    assert isinstance(result, str)
    # Text is shorter than 2000, so returns full text
    assert result == short_text


# ============================================================================
# Test _prepare_text() - ADAPTIVE Mode
# ============================================================================

def test_prepare_text_adaptive_small_text(test_dimension, short_text):
    """Test ADAPTIVE mode returns full text for small docs (<5000 chars)."""
    config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

    result = test_dimension._prepare_text(short_text, config, "test_dimension")

    assert isinstance(result, str)
    assert result == short_text  # Full text, no truncation


def test_prepare_text_adaptive_medium_text(test_dimension, medium_text):
    """Test ADAPTIVE mode truncates to 10000 for medium docs (5000-50000 chars)."""
    config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

    result = test_dimension._prepare_text(medium_text, config, "test_dimension")

    assert isinstance(result, str)
    assert len(result) == min(10000, len(medium_text))


def test_prepare_text_adaptive_large_text(test_dimension, long_text):
    """Test ADAPTIVE mode uses sampling for large docs (>50000 chars)."""
    config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

    result = test_dimension._prepare_text(long_text, config, "test_dimension")

    # Should return list of samples
    assert isinstance(result, list)
    assert len(result) == 5  # Default sampling_sections
    # Each item is a tuple of (position, text)
    for pos, text in result:
        assert isinstance(pos, int)
        assert isinstance(text, str)


# ============================================================================
# Test _prepare_text() - SAMPLING Mode
# ============================================================================

def test_prepare_text_sampling_mode_always_samples(test_dimension, medium_text):
    """Test SAMPLING mode always returns samples regardless of text length."""
    config = AnalysisConfig(mode=AnalysisMode.SAMPLING, sampling_sections=3)

    result = test_dimension._prepare_text(medium_text, config, "test_dimension")

    assert isinstance(result, list)
    assert len(result) == 3
    for pos, text in result:
        assert isinstance(pos, int)
        assert isinstance(text, str)


def test_prepare_text_sampling_mode_custom_sections(test_dimension, long_text):
    """Test SAMPLING mode with custom number of sections."""
    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_sections=7,
        sampling_chars_per_section=1500
    )

    result = test_dimension._prepare_text(long_text, config, "test_dimension")

    assert isinstance(result, list)
    assert len(result) == 7
    # Check sample sizes
    for _pos, text in result:
        assert len(text) <= 1500


# ============================================================================
# Test _prepare_text() - FULL Mode
# ============================================================================

def test_prepare_text_full_mode_never_truncates(test_dimension, long_text):
    """Test FULL mode always returns complete text."""
    config = AnalysisConfig(mode=AnalysisMode.FULL)

    result = test_dimension._prepare_text(long_text, config, "test_dimension")

    assert isinstance(result, str)
    assert result == long_text  # Complete text, no truncation


# ============================================================================
# Test _prepare_text() - Config=None (Backward Compatibility)
# ============================================================================

def test_prepare_text_config_none_uses_default(test_dimension, long_text):
    """Test config=None uses DEFAULT_CONFIG (ADAPTIVE mode)."""
    result = test_dimension._prepare_text(long_text, config=None, dimension_name="test_dimension")

    # DEFAULT_CONFIG is ADAPTIVE, so large text should trigger sampling
    assert isinstance(result, list)


def test_prepare_text_no_dimension_name_uses_property(test_dimension, medium_text):
    """Test that dimension_name=None falls back to self.dimension_name."""
    config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

    result = test_dimension._prepare_text(medium_text, config, dimension_name=None)

    # Should work using self.dimension_name property
    assert isinstance(result, str)


# ============================================================================
# Test _prepare_text() - Dimension Overrides
# ============================================================================

def test_prepare_text_dimension_override(test_dimension, long_text):
    """Test dimension-specific override takes precedence."""
    config = AnalysisConfig(
        mode=AnalysisMode.FAST,  # Would normally use 2000
        dimension_overrides={
            "test_dimension": {"max_chars": 5000}
        }
    )

    result = test_dimension._prepare_text(long_text, config, "test_dimension")

    assert isinstance(result, str)
    assert len(result) == 5000  # Override value, not 2000


# ============================================================================
# Test _aggregate_sampled_metrics() - Numeric Values
# ============================================================================

def test_aggregate_numeric_values(test_dimension):
    """Test aggregation of numeric (int/float) values calculates mean."""
    samples = [
        {'score': 85, 'count': 10},
        {'score': 90, 'count': 20},
        {'score': 88, 'count': 15}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Mean of [85, 90, 88] = 87.67
    assert result['score'] == pytest.approx(87.67, rel=0.01)
    # Mean of [10, 20, 15] = 15
    assert result['count'] == pytest.approx(15.0, rel=0.01)


def test_aggregate_mixed_numeric_types(test_dimension):
    """Test aggregation handles mixed int and float."""
    samples = [
        {'value': 10},
        {'value': 15.5},
        {'value': 12}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Mean of [10, 15.5, 12] = 12.5
    assert result['value'] == pytest.approx(12.5, rel=0.01)


# ============================================================================
# Test _aggregate_sampled_metrics() - Boolean Values
# ============================================================================

def test_aggregate_boolean_majority_true(test_dimension):
    """Test boolean aggregation with True majority."""
    samples = [
        {'has_issue': True},
        {'has_issue': True},
        {'has_issue': False}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # 2 True, 1 False -> True wins
    assert result['has_issue'] is True


def test_aggregate_boolean_majority_false(test_dimension):
    """Test boolean aggregation with False majority."""
    samples = [
        {'has_issue': True},
        {'has_issue': False},
        {'has_issue': False}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # 1 True, 2 False -> False wins
    assert result['has_issue'] is False


def test_aggregate_boolean_tie_goes_to_false(test_dimension):
    """Test boolean aggregation with 50/50 tie."""
    samples = [
        {'has_issue': True},
        {'has_issue': False}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Tie: not (true_count > len(values)/2) -> False
    assert result['has_issue'] is False


# ============================================================================
# Test _aggregate_sampled_metrics() - String Values
# ============================================================================

def test_aggregate_string_mode(test_dimension):
    """Test string aggregation uses most common value."""
    samples = [
        {'label': 'A'},
        {'label': 'B'},
        {'label': 'A'}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # 'A' appears twice, 'B' once -> 'A' wins
    assert result['label'] == 'A'


def test_aggregate_string_all_same(test_dimension):
    """Test string aggregation when all values identical."""
    samples = [
        {'label': 'SAME'},
        {'label': 'SAME'},
        {'label': 'SAME'}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    assert result['label'] == 'SAME'


# ============================================================================
# Test _aggregate_sampled_metrics() - List Values
# ============================================================================

def test_aggregate_list_concatenation(test_dimension):
    """Test list aggregation concatenates and deduplicates."""
    samples = [
        {'words': ['delve', 'robust']},
        {'words': ['leverage', 'delve']},  # 'delve' duplicate
        {'words': ['streamline']}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Should have all unique words in order
    assert 'delve' in result['words']
    assert 'robust' in result['words']
    assert 'leverage' in result['words']
    assert 'streamline' in result['words']
    # Check deduplication: 'delve' should appear only once
    assert result['words'].count('delve') == 1


def test_aggregate_empty_lists(test_dimension):
    """Test list aggregation with empty lists."""
    samples = [
        {'words': []},
        {'words': ['item']},
        {'words': []}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    assert result['words'] == ['item']


# ============================================================================
# Test _aggregate_sampled_metrics() - Dict Values
# ============================================================================

def test_aggregate_dict_merge(test_dimension):
    """Test dict aggregation merges with first-value-wins."""
    samples = [
        {'metadata': {'key1': 'value1', 'key2': 'value2'}},
        {'metadata': {'key2': 'different', 'key3': 'value3'}},  # key2 conflict
        {'metadata': {'key4': 'value4'}}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # First value wins for conflicts
    assert result['metadata']['key1'] == 'value1'
    assert result['metadata']['key2'] == 'value2'  # First value, not 'different'
    assert result['metadata']['key3'] == 'value3'
    assert result['metadata']['key4'] == 'value4'


# ============================================================================
# Test _aggregate_sampled_metrics() - None Values
# ============================================================================

def test_aggregate_with_none_values(test_dimension):
    """Test aggregation ignores None values."""
    samples = [
        {'score': 85, 'optional': None},
        {'score': 90, 'optional': 'value'},
        {'score': 88, 'optional': None}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Score should aggregate all 3
    assert result['score'] == pytest.approx(87.67, rel=0.01)
    # Optional should only use non-None value
    assert result['optional'] == 'value'


def test_aggregate_all_none_values(test_dimension):
    """Test aggregation when all values are None."""
    samples = [
        {'optional': None},
        {'optional': None},
        {'optional': None}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    assert result['optional'] is None


# ============================================================================
# Test _aggregate_sampled_metrics() - Mixed Types
# ============================================================================

def test_aggregate_mixed_metric_types(test_dimension):
    """Test aggregation handles multiple metric types simultaneously."""
    samples = [
        {
            'score': 85,
            'has_issue': True,
            'label': 'A',
            'words': ['word1', 'word2'],
            'metadata': {'key1': 'val1'}
        },
        {
            'score': 90,
            'has_issue': False,
            'label': 'B',
            'words': ['word2', 'word3'],
            'metadata': {'key2': 'val2'}
        },
        {
            'score': 88,
            'has_issue': False,
            'label': 'A',
            'words': ['word4'],
            'metadata': {'key3': 'val3'}
        }
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Numeric: mean
    assert result['score'] == pytest.approx(87.67, rel=0.01)
    # Boolean: majority (1 True, 2 False)
    assert result['has_issue'] is False
    # String: mode (A appears twice)
    assert result['label'] == 'A'
    # List: concatenated and deduplicated
    assert len(result['words']) == 4  # word1, word2, word3, word4
    assert 'word2' in result['words']
    # Dict: merged
    assert len(result['metadata']) == 3


# ============================================================================
# Test _aggregate_sampled_metrics() - Edge Cases
# ============================================================================

def test_aggregate_empty_list(test_dimension):
    """Test aggregation with empty sample list."""
    result = test_dimension._aggregate_sampled_metrics([])

    assert result == {}


def test_aggregate_single_sample(test_dimension):
    """Test aggregation with single sample returns that sample."""
    samples = [
        {'score': 85, 'label': 'test'}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    assert result['score'] == 85
    assert result['label'] == 'test'


def test_aggregate_missing_keys_in_some_samples(test_dimension):
    """Test aggregation when not all samples have all keys."""
    samples = [
        {'score': 85, 'optional': 'value1'},
        {'score': 90},  # Missing 'optional'
        {'score': 88, 'optional': 'value2'}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Score aggregates all 3
    assert result['score'] == pytest.approx(87.67, rel=0.01)
    # Optional uses most common from available values
    assert result['optional'] in ['value1', 'value2']


def test_aggregate_unknown_type_uses_first_value(test_dimension):
    """Test aggregation with unknown type uses first value."""
    # Use a custom class as unknown type
    class CustomType:
        def __init__(self, value):
            self.value = value

    obj1 = CustomType(1)
    obj2 = CustomType(2)

    samples = [
        {'custom': obj1},
        {'custom': obj2}
    ]

    result = test_dimension._aggregate_sampled_metrics(samples)

    # Should use first value for unknown types
    assert result['custom'] is obj1
