"""
Integration tests for all dimensions with config support.

Verifies all 12 dimensions accept config parameter and return consistent metadata.
Story 1.4.8: Optimize Heavy Dimensions for Full Documents
"""

import pytest

from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension
from writescore.dimensions.burstiness import BurstinessDimension
from writescore.dimensions.formatting import FormattingDimension
from writescore.dimensions.lexical import LexicalDimension
from writescore.dimensions.perplexity import PerplexityDimension

# Import all dimensions
from writescore.dimensions.predictability import PredictabilityDimension
from writescore.dimensions.readability import ReadabilityDimension
from writescore.dimensions.sentiment import SentimentDimension
from writescore.dimensions.structure import StructureDimension
from writescore.dimensions.syntactic import SyntacticDimension
from writescore.dimensions.transition_marker import TransitionMarkerDimension
from writescore.dimensions.voice import VoiceDimension


@pytest.fixture
def all_dimensions():
    """Create instances of all 12 dimensions."""
    DimensionRegistry.clear()
    return [
        PredictabilityDimension(),
        SyntacticDimension(),
        AdvancedLexicalDimension(),
        ReadabilityDimension(),
        BurstinessDimension(),
        PerplexityDimension(),
        VoiceDimension(),
        LexicalDimension(),
        FormattingDimension(),
        StructureDimension(),
        SentimentDimension(),
        TransitionMarkerDimension()
    ]


class TestAllDimensionsConfig:
    """Test all dimensions accept config and return consistent metadata."""

    def test_all_dimensions_accept_fast_mode(self, all_dimensions):
        """Test all dimensions accept FAST mode config."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)
        text = "This is a test sentence. " * 100

        for dim in all_dimensions:
            result = dim.analyze(text, config=config)

            # Should not crash and should return a dict
            assert isinstance(result, dict), f"{dim.dimension_name} should return dict"
            assert 'analysis_mode' in result, f"{dim.dimension_name} missing analysis_mode"
            assert result['analysis_mode'] == 'fast', f"{dim.dimension_name} wrong mode"

    def test_all_dimensions_accept_adaptive_mode(self, all_dimensions):
        """Test all dimensions accept ADAPTIVE mode config."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)
        text = "This is a test sentence. " * 200

        for dim in all_dimensions:
            result = dim.analyze(text, config=config)

            assert isinstance(result, dict), f"{dim.dimension_name} should return dict"
            assert 'analysis_mode' in result, f"{dim.dimension_name} missing analysis_mode"
            assert result['analysis_mode'] == 'adaptive', f"{dim.dimension_name} wrong mode"

    def test_all_dimensions_return_consistent_metadata(self, all_dimensions):
        """Test all dimensions return required metadata fields.

        Note: Some dimensions (like perplexity) are document-level metrics and
        don't use sampling, so they may not have all sampling-related fields.
        """
        config = AnalysisConfig(mode=AnalysisMode.FAST)
        text = "The quick brown fox jumps over the lazy dog. " * 50

        # All dimensions must have analysis_mode
        required_fields = ['analysis_mode']

        # Sampling-aware dimensions have additional fields
        sampling_fields = [
            'samples_analyzed',
            'total_text_length',
            'analyzed_text_length',
            'coverage_percentage'
        ]

        # Dimensions that use sampling (most of them)
        sampling_dimensions = {
            'predictability', 'syntactic', 'advanced_lexical', 'readability',
            'burstiness', 'voice', 'lexical', 'formatting', 'structure',
            'sentiment', 'transition_marker'
        }

        for dim in all_dimensions:
            result = dim.analyze(text, config=config)

            # Check required fields present
            for field in required_fields:
                assert field in result, f"{dim.dimension_name} missing field: {field}"

            # Check sampling fields for sampling-aware dimensions
            if dim.dimension_name in sampling_dimensions:
                for field in sampling_fields:
                    assert field in result, f"{dim.dimension_name} missing field: {field}"

                # Verify types for sampling dimensions
                assert isinstance(result['samples_analyzed'], int)
                assert isinstance(result['total_text_length'], int)
                assert isinstance(result['analyzed_text_length'], int)
                assert isinstance(result['coverage_percentage'], (int, float))

                # Verify values are reasonable
                assert result['samples_analyzed'] >= 1
                assert result['total_text_length'] == len(text)
                assert 0 <= result['coverage_percentage'] <= 100

            # All dimensions must have analysis_mode as string
            assert isinstance(result['analysis_mode'], str)

    def test_all_dimensions_handle_none_config(self, all_dimensions):
        """Test all dimensions handle config=None gracefully (default to ADAPTIVE)."""
        text = "Test sentence. " * 50

        for dim in all_dimensions:
            result = dim.analyze(text, config=None)

            # Should default to ADAPTIVE mode
            assert 'analysis_mode' in result
            assert result['analysis_mode'] == 'adaptive'

    def test_heavy_dimensions_support_full_mode(self):
        """Test heavy dimensions support FULL mode (no limits)."""
        DimensionRegistry.clear()

        heavy_dims = [
            PredictabilityDimension(),
            SyntacticDimension(),
            AdvancedLexicalDimension()
        ]

        config = AnalysisConfig(mode=AnalysisMode.FULL)
        # Use moderate-length text for FULL mode test
        text = "The quick brown fox jumps over the lazy dog. " * 500  # ~22.5k chars

        for dim in heavy_dims:
            result = dim.analyze(text, config=config)

            assert result['analysis_mode'] == 'full'
            # FULL mode should analyze entire text (for moderate lengths)
            assert result['analyzed_text_length'] == len(text)
            assert result['coverage_percentage'] == 100.0

    def test_fast_dimensions_ignore_sampling(self):
        """Test fast dimensions always analyze full text regardless of mode.

        Note: Perplexity is excluded as it's a special document-level metric
        that doesn't follow the sampling pattern.
        """
        DimensionRegistry.clear()

        # Fast dimensions that support sampling metadata
        fast_dims = [
            ReadabilityDimension(),
            BurstinessDimension(),
            VoiceDimension(),
            LexicalDimension(),
            FormattingDimension(),
            StructureDimension(),
            SentimentDimension(),
            TransitionMarkerDimension()
        ]

        # Try different modes - all should analyze full text
        configs = [
            AnalysisConfig(mode=AnalysisMode.FAST),
            AnalysisConfig(mode=AnalysisMode.ADAPTIVE),
            AnalysisConfig(mode=AnalysisMode.FULL)
        ]

        text = "Test sentence. " * 100

        for dim in fast_dims:
            for config in configs:
                result = dim.analyze(text, config=config)

                # Fast dimensions always analyze 100%
                assert result['samples_analyzed'] == 1
                assert result['coverage_percentage'] == 100.0
                assert result['analyzed_text_length'] == len(text)

    def test_dimensions_handle_empty_text(self, all_dimensions):
        """Test all dimensions handle empty text gracefully."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        # Dimensions that return total_text_length
        sampling_dimensions = {
            'predictability', 'syntactic', 'advanced_lexical', 'readability',
            'burstiness', 'voice', 'lexical', 'formatting', 'structure',
            'sentiment', 'transition_marker'
        }

        for dim in all_dimensions:
            result = dim.analyze("", config=config)

            # Should not crash
            assert isinstance(result, dict)

            # Check total_text_length only for sampling-aware dimensions
            if dim.dimension_name in sampling_dimensions:
                assert result['total_text_length'] == 0
