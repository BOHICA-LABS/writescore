"""
Unit tests for SyntacticDimension analysis modes.

Tests FAST, ADAPTIVE, SAMPLING, and FULL modes for syntactic analysis.
Story 1.4.8: Optimize Heavy Dimensions for Full Documents
"""

import pytest

from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.syntactic import SyntacticDimension


@pytest.fixture
def dim():
    """Create SyntacticDimension instance with clean registry."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return SyntacticDimension()


class TestSyntacticModes:
    """Test SyntacticDimension with different analysis modes."""

    def test_fast_mode_truncates_to_100k(self, dim):
        """Test FAST mode maintains 100k-char limit (backward compatible)."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        long_text = "word " * 50000  # 250k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'fast'
        assert result['samples_analyzed'] == 1
        assert result['analyzed_text_length'] <= 100000

    def test_adaptive_mode_samples_long_documents(self, dim):
        """Test ADAPTIVE mode samples 90-page chapters."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        chapter_text = "word " * 36000  # ~180k chars (90 pages)
        result = dim.analyze(chapter_text, config=config)

        assert result['analysis_mode'] == 'adaptive'
        assert result['samples_analyzed'] >= 5  # Should sample 5-7 sections
        assert result['total_text_length'] == len(chapter_text)
        assert result['coverage_percentage'] > 5.0  # >5% analyzed

    def test_full_mode_analyzes_entire_document(self, dim):
        """Test FULL mode processes entire text (no 100k limit)."""
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

    def test_aggregate_syntactic_metrics_calculates_correctly(self, dim):
        """Test syntactic aggregation uses appropriate strategies."""
        # Create sample metrics with known values
        samples = [
            {
                'available': True,
                'syntactic_repetition_score': 0.3,
                'pos_diversity': 0.5,
                'avg_dependency_depth': 4.0,
                'subordination_index': 0.2,
                'passive_constructions': 5,
                'morphological_richness': 100
            },
            {
                'available': True,
                'syntactic_repetition_score': 0.5,
                'pos_diversity': 0.6,
                'avg_dependency_depth': 5.0,
                'subordination_index': 0.3,
                'passive_constructions': 8,
                'morphological_richness': 120
            },
            {
                'available': True,
                'syntactic_repetition_score': 0.4,
                'pos_diversity': 0.55,
                'avg_dependency_depth': 4.5,
                'subordination_index': 0.25,
                'passive_constructions': 6,
                'morphological_richness': 110
            }
        ]

        result = dim._aggregate_syntactic_metrics(samples)

        # Means
        assert result['syntactic_repetition_score'] == pytest.approx(0.4, abs=0.01)
        assert result['pos_diversity'] == pytest.approx(0.55, abs=0.01)
        assert result['avg_dependency_depth'] == pytest.approx(4.5, abs=0.1)
        assert result['subordination_index'] == pytest.approx(0.25, abs=0.01)

        # Sums
        assert result['passive_constructions'] == 19
        assert result['morphological_richness'] == 330

    def test_metadata_included_in_results(self, dim):
        """Test analysis metadata is included in results."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "This is a test sentence with varied structure. " * 100
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

    def test_backward_compatibility_structure(self, dim):
        """Test result structure maintains backward compatibility."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "The quick brown fox jumps over the lazy dog. " * 500
        result = dim.analyze(text, config=config)

        # Old code expects 'syntactic' key
        assert 'syntactic' in result
        assert result['syntactic']['available']

        # But also flattened fields for new code
        assert 'syntactic_repetition_score' in result
        assert 'pos_diversity' in result
        assert 'avg_dependency_depth' in result

    def test_syntactic_metrics_present(self, dim):
        """Test all syntactic metrics are present in results."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "The cat sat on the mat. The dog ran through the park. " * 200
        result = dim.analyze(text, config=config)

        # Verify all expected syntactic metrics
        assert 'syntactic_repetition_score' in result
        assert 'pos_diversity' in result
        assert 'avg_dependency_depth' in result
        assert 'avg_tree_depth' in result  # Alias
        assert 'subordination_index' in result
        assert 'passive_constructions' in result
        assert 'morphological_richness' in result

    def test_100k_limit_removed_in_full_mode(self, dim):
        """Test FULL mode can analyze texts >100k chars."""
        config = AnalysisConfig(mode=AnalysisMode.FULL)

        # Create text >100k chars
        long_text = "The quick brown fox jumps over the lazy dog. " * 2500  # ~112k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'full'
        assert result['analyzed_text_length'] > 100000
        assert result['coverage_percentage'] == 100.0
        assert result['available']
