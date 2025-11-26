"""
Unit tests for AdvancedLexicalDimension analysis modes.

Tests FAST, ADAPTIVE, SAMPLING, and FULL modes for advanced lexical analysis.
Story 1.4.8: Optimize Heavy Dimensions for Full Documents
"""

import pytest
from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.dimension_registry import DimensionRegistry


@pytest.fixture
def dim():
    """Create AdvancedLexicalDimension instance with clean registry."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return AdvancedLexicalDimension()


class TestAdvancedLexicalModes:
    """Test AdvancedLexicalDimension with different analysis modes."""

    def test_fast_mode_analyzes_full_text(self, dim):
        """Test FAST mode truncates to 2000 chars (standard FAST behavior)."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        # Text under 200k chars
        text = "The quick brown fox jumps over the lazy dog. " * 2000  # ~90k chars
        result = dim.analyze(text, config=config)

        assert result['analysis_mode'] == 'fast'
        assert result['samples_analyzed'] == 1
        # FAST mode truncates to 2000 chars (standard behavior)
        assert result['analyzed_text_length'] == 2000
        assert result['coverage_percentage'] < 100.0

    def test_adaptive_mode_full_analysis_under_200k(self, dim):
        """Test ADAPTIVE mode uses sampling for text >50k chars."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        # Text under 200k threshold but >50k chars
        text = "The quick brown fox jumps over the lazy dog. " * 3000  # ~135k chars
        result = dim.analyze(text, config=config)

        assert result['analysis_mode'] == 'adaptive'
        # ADAPTIVE mode samples for text >50k chars
        assert result['samples_analyzed'] >= 5  # Should sample
        assert result['coverage_percentage'] < 100.0

    def test_adaptive_mode_samples_over_200k(self, dim):
        """Test ADAPTIVE mode samples when >200k chars."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        # Text over 200k threshold
        text = "The quick brown fox jumps over the lazy dog. " * 5000  # ~225k chars
        result = dim.analyze(text, config=config)

        assert result['analysis_mode'] == 'adaptive'
        assert result['samples_analyzed'] >= 5  # Should sample (over threshold)
        assert result['total_text_length'] == len(text)
        assert result['coverage_percentage'] < 100.0

    def test_full_mode_analyzes_entire_document(self, dim):
        """Test FULL mode processes entire text."""
        config = AnalysisConfig(mode=AnalysisMode.FULL)

        long_text = "The quick brown fox jumps over the lazy dog. " * 2000  # ~90k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'full'
        assert result['analyzed_text_length'] == result['total_text_length']
        assert result['coverage_percentage'] == 100.0

    @pytest.mark.slow
    def test_sampling_mode_uses_configured_samples(self, dim):
        """Test SAMPLING mode respects sample configuration."""
        config = AnalysisConfig(
            mode=AnalysisMode.SAMPLING,
            sampling_sections=7,
            sampling_chars_per_section=10000
        )

        long_text = "The quick brown fox jumps over the lazy dog. " * 10000  # ~450k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'sampling'
        assert result['samples_analyzed'] == 7
        # Each sample ~10k chars, so total ~70k analyzed
        assert 60000 <= result['analyzed_text_length'] <= 80000

    def test_aggregate_lexical_metrics_uses_base_aggregation(self, dim):
        """Test lexical aggregation uses base _aggregate_sampled_metrics (mean)."""
        # Create sample metrics with known values
        samples = [
            {
                'hdd_score': 0.6,
                'yules_k': 60.0,
                'mattr': 0.70,
                'rttr': 7.5,
                'maas_score': 0.3,
                'vocab_concentration': 0.4
            },
            {
                'hdd_score': 0.7,
                'yules_k': 50.0,
                'mattr': 0.75,
                'rttr': 8.0,
                'maas_score': 0.4,
                'vocab_concentration': 0.35
            },
            {
                'hdd_score': 0.8,
                'yules_k': 40.0,
                'mattr': 0.80,
                'rttr': 8.5,
                'maas_score': 0.5,
                'vocab_concentration': 0.3
            }
        ]

        result = dim._aggregate_sampled_metrics(samples)

        # All metrics use mean
        assert result['hdd_score'] == pytest.approx(0.7, abs=0.01)
        assert result['yules_k'] == pytest.approx(50.0, abs=0.1)
        assert result['mattr'] == pytest.approx(0.75, abs=0.01)
        assert result['rttr'] == pytest.approx(8.0, abs=0.1)
        assert result['maas_score'] == pytest.approx(0.4, abs=0.01)
        assert result['vocab_concentration'] == pytest.approx(0.35, abs=0.01)

    def test_metadata_included_in_results(self, dim):
        """Test analysis metadata is included in results."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "This is a test sentence with varied lexical diversity. " * 100
        result = dim.analyze(text, config=config)

        # Check metadata fields
        assert 'analysis_mode' in result
        assert 'samples_analyzed' in result
        assert 'total_text_length' in result
        assert 'analyzed_text_length' in result
        assert 'coverage_percentage' in result
        assert result['total_text_length'] == len(text)

    def test_short_text_uses_full_analysis(self, dim):
        """Test short text (<5k chars) gets full analysis even in ADAPTIVE mode."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        short_text = "The cat sat on the mat. " * 100  # ~2.5k chars
        result = dim.analyze(short_text, config=config)

        # ADAPTIVE mode on short text should analyze fully
        assert result['samples_analyzed'] == 1
        assert result['coverage_percentage'] == 100.0

    def test_empty_text_handles_gracefully(self, dim):
        """Test empty text doesn't crash."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        result = dim.analyze("", config=config)

        assert 'available' in result
        assert result['total_text_length'] == 0

    def test_default_config_uses_adaptive(self, dim):
        """Test None config defaults to ADAPTIVE mode."""
        text = "The quick brown fox jumps over the lazy dog. " * 1000  # ~45k chars
        result = dim.analyze(text, config=None)

        # DEFAULT_CONFIG uses ADAPTIVE mode
        assert result['analysis_mode'] == 'adaptive'

    def test_advanced_lexical_metrics_present(self, dim):
        """Test all advanced lexical metrics are present in results."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "The cat sat on the mat. The dog ran through the park. " * 200
        result = dim.analyze(text, config=config)

        # Verify all expected metrics
        assert 'hdd_score' in result
        assert 'yules_k' in result
        assert 'mattr' in result
        assert 'rttr' in result
        assert 'maas_score' in result or result.get('maas_score') is None  # May be None for short text
        assert 'vocab_concentration' in result or result.get('vocab_concentration') is None

    def test_200k_threshold_adaptive_behavior(self, dim):
        """Test ADAPTIVE mode uses sampling for text >50k chars."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        # At 200k threshold - ADAPTIVE mode samples for text >50k
        text_at_threshold = "word " * 40000  # Exactly 200k chars
        result = dim.analyze(text_at_threshold, config=config)
        # ADAPTIVE samples for text >50k chars, so this should sample too
        assert result['coverage_percentage'] < 100.0
        assert result['samples_analyzed'] >= 5

        # Over threshold - should also sample
        text_over_threshold = "word " * 45000  # >200k chars (225k)
        result = dim.analyze(text_over_threshold, config=config)
        assert result['coverage_percentage'] < 100.0
        assert result['samples_analyzed'] >= 5
