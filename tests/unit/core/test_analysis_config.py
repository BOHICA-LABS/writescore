"""Unit tests for AnalysisConfig class.

Tests cover:
- Mode enum validation
- Config creation with defaults
- get_effective_limit() for each mode
- should_use_sampling() logic
- extract_samples() for even/weighted/adaptive strategies
- Dimension overrides
"""

import pytest
from writescore.core.analysis_config import (
    AnalysisMode,
    AnalysisConfig,
    DEFAULT_CONFIG
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_text_short():
    """Short text < 2000 chars for FAST mode testing."""
    return "Sample text. " * 100  # ~1300 chars


@pytest.fixture
def sample_text_medium():
    """Medium text 5000-10000 chars for ADAPTIVE mode testing."""
    return "Sample paragraph text. " * 300  # ~6900 chars


@pytest.fixture
def sample_text_long():
    """Long text simulating 90-page chapter (~180k chars)."""
    return "Sample chapter text with multiple sections. " * 4000  # ~180k chars


@pytest.fixture
def config_fast():
    """AnalysisConfig with FAST mode."""
    return AnalysisConfig(mode=AnalysisMode.FAST)


@pytest.fixture
def config_adaptive():
    """AnalysisConfig with ADAPTIVE mode."""
    return AnalysisConfig(mode=AnalysisMode.ADAPTIVE)


@pytest.fixture
def config_sampling():
    """AnalysisConfig with SAMPLING mode."""
    return AnalysisConfig(mode=AnalysisMode.SAMPLING, sampling_sections=5)


@pytest.fixture
def config_full():
    """AnalysisConfig with FULL mode."""
    return AnalysisConfig(mode=AnalysisMode.FULL)


# ============================================================================
# Test AnalysisMode Enum
# ============================================================================

def test_analysis_mode_enum_values():
    """Test that AnalysisMode enum has expected values."""
    assert AnalysisMode.FAST == "fast"
    assert AnalysisMode.ADAPTIVE == "adaptive"
    assert AnalysisMode.SAMPLING == "sampling"
    assert AnalysisMode.FULL == "full"
    assert AnalysisMode.STREAMING == "streaming"


def test_analysis_mode_enum_membership():
    """Test that all expected modes are in the enum."""
    modes = [m.value for m in AnalysisMode]
    assert "fast" in modes
    assert "adaptive" in modes
    assert "sampling" in modes
    assert "full" in modes
    assert "streaming" in modes


# ============================================================================
# Test AnalysisConfig Creation
# ============================================================================

def test_config_default_creation():
    """Test creating config with default values."""
    config = AnalysisConfig()
    assert config.mode == AnalysisMode.ADAPTIVE
    assert config.sampling_sections == 5
    assert config.sampling_chars_per_section == 2000
    assert config.sampling_strategy == "even"
    assert config.max_text_length is None
    assert config.max_analysis_time_seconds == 300
    assert config.dimension_overrides == {}
    assert config.enable_detailed_analysis is True


def test_config_custom_creation():
    """Test creating config with custom values."""
    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_sections=10,
        sampling_chars_per_section=3000,
        sampling_strategy="weighted",
        max_text_length=100000,
        dimension_overrides={"predictability": {"max_chars": 5000}}
    )
    assert config.mode == AnalysisMode.SAMPLING
    assert config.sampling_sections == 10
    assert config.sampling_chars_per_section == 3000
    assert config.sampling_strategy == "weighted"
    assert config.max_text_length == 100000
    assert "predictability" in config.dimension_overrides


def test_default_config_constant():
    """Test that DEFAULT_CONFIG is properly initialized."""
    assert DEFAULT_CONFIG.mode == AnalysisMode.ADAPTIVE
    assert isinstance(DEFAULT_CONFIG, AnalysisConfig)


# ============================================================================
# Test get_effective_limit()
# ============================================================================

def test_get_effective_limit_fast_mode_always_2000(config_fast):
    """Test FAST mode always returns 2000 char limit."""
    assert config_fast.get_effective_limit("test_dimension", 500) == 2000
    assert config_fast.get_effective_limit("test_dimension", 5000) == 2000
    assert config_fast.get_effective_limit("test_dimension", 100000) == 2000


def test_get_effective_limit_adaptive_small_text(config_adaptive):
    """Test ADAPTIVE mode returns None for small text (<5000 chars)."""
    assert config_adaptive.get_effective_limit("test_dimension", 1000) is None
    assert config_adaptive.get_effective_limit("test_dimension", 4999) is None


def test_get_effective_limit_adaptive_medium_text(config_adaptive):
    """Test ADAPTIVE mode returns 10000 for medium text (5000-50000 chars)."""
    assert config_adaptive.get_effective_limit("test_dimension", 5000) == 10000
    assert config_adaptive.get_effective_limit("test_dimension", 25000) == 10000
    assert config_adaptive.get_effective_limit("test_dimension", 49999) == 10000


def test_get_effective_limit_adaptive_large_text(config_adaptive):
    """Test ADAPTIVE mode returns None for large text (>50000 chars, triggers sampling)."""
    assert config_adaptive.get_effective_limit("test_dimension", 50001) is None
    assert config_adaptive.get_effective_limit("test_dimension", 180000) is None


def test_get_effective_limit_sampling_mode(config_sampling):
    """Test SAMPLING mode always returns None (triggers extract_samples)."""
    assert config_sampling.get_effective_limit("test_dimension", 1000) is None
    assert config_sampling.get_effective_limit("test_dimension", 50000) is None


def test_get_effective_limit_full_mode(config_full):
    """Test FULL mode always returns None (no limit)."""
    assert config_full.get_effective_limit("test_dimension", 1000) is None
    assert config_full.get_effective_limit("test_dimension", 180000) is None


def test_get_effective_limit_dimension_override():
    """Test dimension-specific override takes precedence."""
    config = AnalysisConfig(
        mode=AnalysisMode.FAST,
        dimension_overrides={
            "predictability": {"max_chars": 5000}
        }
    )
    # Override should take precedence over FAST mode's 2000
    assert config.get_effective_limit("predictability", 10000) == 5000
    # Non-overridden dimension should use mode default
    assert config.get_effective_limit("readability", 10000) == 2000


# ============================================================================
# Test should_use_sampling()
# ============================================================================

def test_should_use_sampling_fast_mode(config_fast):
    """Test FAST mode never samples."""
    assert config_fast.should_use_sampling(1000) is False
    assert config_fast.should_use_sampling(100000) is False


def test_should_use_sampling_adaptive_mode_small(config_adaptive):
    """Test ADAPTIVE mode doesn't sample for small/medium text."""
    assert config_adaptive.should_use_sampling(1000) is False
    assert config_adaptive.should_use_sampling(49999) is False


def test_should_use_sampling_adaptive_mode_large(config_adaptive):
    """Test ADAPTIVE mode samples for large text (>50k chars)."""
    assert config_adaptive.should_use_sampling(50001) is True
    assert config_adaptive.should_use_sampling(180000) is True


def test_should_use_sampling_sampling_mode(config_sampling):
    """Test SAMPLING mode always samples."""
    assert config_sampling.should_use_sampling(1000) is True
    assert config_sampling.should_use_sampling(100000) is True


def test_should_use_sampling_full_mode(config_full):
    """Test FULL mode never samples."""
    assert config_full.should_use_sampling(1000) is False
    assert config_full.should_use_sampling(180000) is False


# ============================================================================
# Test extract_samples() - Even Strategy
# ============================================================================

def test_extract_samples_even_strategy(config_sampling, sample_text_long):
    """Test even sampling strategy produces evenly spaced samples."""
    config_sampling.sampling_strategy = "even"
    config_sampling.sampling_sections = 5

    samples = config_sampling.extract_samples(sample_text_long)

    assert len(samples) == 5
    # Check that samples are tuples of (position, text)
    for pos, text in samples:
        assert isinstance(pos, int)
        assert isinstance(text, str)
        assert len(text) <= config_sampling.sampling_chars_per_section


def test_extract_samples_even_spacing(config_sampling):
    """Test that even samples are properly spaced."""
    text = "x" * 100000  # 100k chars
    config_sampling.sampling_strategy = "even"
    config_sampling.sampling_sections = 5

    samples = config_sampling.extract_samples(text)

    # With 100k chars and 5 sections, section_size = 20k
    # Samples should start at: 0, 20k, 40k, 60k, 80k
    expected_positions = [0, 20000, 40000, 60000, 80000]

    assert len(samples) == 5
    for i, (pos, _) in enumerate(samples):
        assert pos == expected_positions[i]


def test_extract_samples_text_smaller_than_one_sample(config_sampling):
    """Test that text smaller than one sample returns entire text."""
    short_text = "Short text"
    samples = config_sampling.extract_samples(short_text)

    assert len(samples) == 1
    assert samples[0] == (0, short_text)


# ============================================================================
# Test extract_samples() - Weighted Strategy
# ============================================================================

def test_extract_samples_weighted_strategy(config_sampling, sample_text_long):
    """Test weighted sampling strategy favors beginning/end."""
    config_sampling.sampling_strategy = "weighted"
    config_sampling.sampling_sections = 5

    samples = config_sampling.extract_samples(sample_text_long)

    assert len(samples) == 5
    # First sample should be at position 0 (beginning)
    assert samples[0][0] == 0
    # Last sample should be near the end
    text_length = len(sample_text_long)
    last_sample_pos = samples[-1][0]
    assert last_sample_pos >= text_length * 0.7  # Should be in last 30%


def test_extract_samples_weighted_positions():
    """Test weighted strategy uses correct position weightings."""
    text = "x" * 100000  # 100k chars
    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_strategy="weighted",
        sampling_sections=5,
        sampling_chars_per_section=2000
    )

    samples = config.extract_samples(text)

    # Expected positions: 0, 10%, 40%, 70%, end
    expected_positions = [
        0,
        10000,   # 10% of 100k
        40000,   # 40% of 100k
        70000,   # 70% of 100k
        98000    # 100k - 2000
    ]

    assert len(samples) == 5
    for i, (pos, _) in enumerate(samples):
        assert pos == expected_positions[i]


# ============================================================================
# Test extract_samples() - Adaptive Strategy
# ============================================================================

def test_extract_samples_adaptive_with_headings():
    """Test adaptive strategy detects markdown headings."""
    text = """# Chapter 1
Content of chapter 1 here with lots of text to analyze.

## Section 1.1
More content in section 1.1 with detailed information.

# Chapter 2
Content of chapter 2 continues the story.

## Section 2.1
Final section with concluding thoughts."""

    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_strategy="adaptive",
        sampling_sections=4,
        sampling_chars_per_section=50
    )

    samples = config.extract_samples(text)

    # Should detect headings and sample from each section
    assert len(samples) >= 2  # At least some sections detected
    # First sample should start at beginning
    assert samples[0][0] == 0


def test_extract_samples_adaptive_fallback_to_even():
    """Test adaptive strategy falls back to even if no headings."""
    text = "No headings in this text. " * 1000  # ~26k chars, no markdown headers

    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_strategy="adaptive",
        sampling_sections=5,
        sampling_chars_per_section=2000
    )

    samples = config.extract_samples(text)

    # Should fall back to even sampling
    assert len(samples) == 5
    # Check even spacing (similar to even strategy test)
    text_length = len(text)
    section_size = text_length // 5
    for i, (pos, _) in enumerate(samples):
        assert pos == i * section_size


# ============================================================================
# Test extract_samples() - Unknown Strategy
# ============================================================================

def test_extract_samples_unknown_strategy_defaults_to_even(config_sampling):
    """Test unknown strategy falls back to even sampling."""
    config_sampling.sampling_strategy = "unknown_strategy"
    text = "x" * 50000

    samples = config_sampling.extract_samples(text)

    # Should default to even sampling
    assert len(samples) == 5
    # Check even spacing
    section_size = 50000 // 5
    for i, (pos, _) in enumerate(samples):
        assert pos == i * section_size


# ============================================================================
# Test Integration Scenarios
# ============================================================================

def test_fast_mode_workflow():
    """Test complete workflow for FAST mode."""
    config = AnalysisConfig(mode=AnalysisMode.FAST)
    text = "x" * 100000

    # FAST mode should truncate
    limit = config.get_effective_limit("test_dim", len(text))
    assert limit == 2000

    # FAST mode should not sample
    assert config.should_use_sampling(len(text)) is False


def test_adaptive_mode_workflow_large_doc():
    """Test complete workflow for ADAPTIVE mode with large document."""
    config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)
    text = "x" * 180000  # 90-page chapter

    # ADAPTIVE mode should trigger sampling for large docs
    limit = config.get_effective_limit("test_dim", len(text))
    assert limit is None

    # Should use sampling
    assert config.should_use_sampling(len(text)) is True

    # Extract samples
    samples = config.extract_samples(text)
    assert len(samples) == 5


def test_sampling_mode_workflow():
    """Test complete workflow for SAMPLING mode."""
    config = AnalysisConfig(
        mode=AnalysisMode.SAMPLING,
        sampling_sections=3,
        sampling_strategy="weighted"
    )
    text = "x" * 50000

    # SAMPLING mode should return None (triggers sampling)
    limit = config.get_effective_limit("test_dim", len(text))
    assert limit is None

    # Should always sample
    assert config.should_use_sampling(len(text)) is True

    # Extract samples
    samples = config.extract_samples(text)
    assert len(samples) == 3


def test_full_mode_workflow():
    """Test complete workflow for FULL mode."""
    config = AnalysisConfig(mode=AnalysisMode.FULL)
    text = "x" * 180000

    # FULL mode should not limit
    limit = config.get_effective_limit("test_dim", len(text))
    assert limit is None

    # FULL mode should not sample
    assert config.should_use_sampling(len(text)) is False
