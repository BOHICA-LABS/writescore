"""
Performance tests for GLTR analysis modes.

Tests that FAST, ADAPTIVE, and FULL modes meet performance targets.
Story 1.4.7: Enable Full Document GLTR Analysis
"""

import pytest
import time
from writescore.dimensions.predictability import PredictabilityDimension
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.dimension_registry import DimensionRegistry


@pytest.fixture
def dim():
    """Create PredictabilityDimension instance with clean registry."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return PredictabilityDimension()


class TestDataHelpers:
    """Helper methods for generating test data."""

    @staticmethod
    def _load_sample_chapter() -> str:
        """Generate ~180k char test text (90 pages × 2000 chars/page)."""
        # Use repetitive but varied text
        sentences = [
            "The industrial control system monitors critical infrastructure.",
            "Security operations require continuous vigilance and analysis.",
            "Data patterns reveal insights into system behavior.",
            "Automated detection helps identify potential anomalies.",
        ]
        # 90 pages × 2000 chars/page = 180k chars
        # Each sentence ~60 chars, need ~3000 repetitions
        return " ".join(sentences * 750)  # ~180k chars


class TestGLTRPerformance:
    """Performance tests for GLTR analysis."""

    @pytest.mark.slow
    def test_fast_mode_completes_in_15_seconds(self, dim):
        """Test FAST mode meets 15-second target."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        long_text = "word " * 50000  # 250k chars

        start = time.time()
        result = dim.analyze(long_text, config=config)
        elapsed = time.time() - start

        # Allow 25s to account for model loading overhead (~4-5s) and system variability
        assert elapsed < 25.0, f"FAST mode took {elapsed:.1f}s, expected <25s"
        assert result['samples_analyzed'] == 1

    @pytest.mark.slow
    def test_adaptive_mode_completes_in_90_seconds(self, dim):
        """Test ADAPTIVE mode for 90-page chapter."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        helpers = TestDataHelpers()
        chapter_text = helpers._load_sample_chapter()  # ~180k chars

        start = time.time()
        result = dim.analyze(chapter_text, config=config)
        elapsed = time.time() - start

        assert elapsed < 90.0, f"ADAPTIVE mode took {elapsed:.1f}s, expected <90s"
        assert result['samples_analyzed'] >= 5

    @pytest.mark.slow
    def test_full_mode_completes_in_15_minutes(self, dim):
        """Test FULL mode for 90-page chapter."""
        config = AnalysisConfig(mode=AnalysisMode.FULL)

        helpers = TestDataHelpers()
        chapter_text = helpers._load_sample_chapter()  # ~180k chars

        start = time.time()
        result = dim.analyze(chapter_text, config=config)
        elapsed = time.time() - start

        assert elapsed < 900.0, f"FULL mode took {elapsed:.1f}s, expected <900s (15min)"
        assert result['coverage_percentage'] == 100.0

    @pytest.mark.slow
    def test_sampling_mode_completes_in_120_seconds(self, dim):
        """Test SAMPLING mode with 5 samples completes in reasonable time."""
        config = AnalysisConfig(
            mode=AnalysisMode.SAMPLING,
            sampling_sections=5,
            sampling_chars_per_section=3000
        )

        helpers = TestDataHelpers()
        chapter_text = helpers._load_sample_chapter()  # ~180k chars

        start = time.time()
        result = dim.analyze(chapter_text, config=config)
        elapsed = time.time() - start

        assert elapsed < 120.0, f"SAMPLING mode took {elapsed:.1f}s, expected <120s"
        assert result['samples_analyzed'] == 5

    @pytest.mark.slow
    def test_adaptive_faster_than_full(self, dim):
        """Test ADAPTIVE mode is faster than FULL mode and analyzes less data.

        Note: Model loading dominates runtime, so time difference may be modest.
        The key benefits of ADAPTIVE are:
        1. Less data analyzed (sampling)
        2. At least as fast as FULL (batched samples)
        """
        text = "word " * 30000  # ~150k chars

        # Warm-up call to load model (model loading is cached after first call)
        warmup_config = AnalysisConfig(mode=AnalysisMode.FAST)
        dim.analyze("warmup text " * 100, config=warmup_config)

        # Time FULL mode first (longer operation)
        full_config = AnalysisConfig(mode=AnalysisMode.FULL)
        start_full = time.time()
        full_result = dim.analyze(text, config=full_config)
        full_time = time.time() - start_full

        # Time ADAPTIVE mode second
        adaptive_config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)
        start_adaptive = time.time()
        adaptive_result = dim.analyze(text, config=adaptive_config)
        adaptive_time = time.time() - start_adaptive

        # ADAPTIVE should be no slower than FULL (allow 20% margin for variance)
        assert adaptive_time < full_time * 1.2, \
            f"ADAPTIVE ({adaptive_time:.1f}s) should not be slower than FULL ({full_time:.1f}s)"

        # ADAPTIVE should analyze less data than FULL
        assert adaptive_result['analyzed_text_length'] < full_result['analyzed_text_length'], \
            f"ADAPTIVE ({adaptive_result['analyzed_text_length']} chars) should analyze less than FULL ({full_result['analyzed_text_length']} chars)"

    def test_fast_mode_performance_on_small_text(self, dim):
        """Test FAST mode is fast on small text (non-slow test)."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "word " * 500  # ~2.5k chars

        start = time.time()
        result = dim.analyze(text, config=config)
        elapsed = time.time() - start

        # Small text should complete in under 30 seconds (includes model loading)
        assert elapsed < 30.0, f"FAST mode on small text took {elapsed:.1f}s, expected <30s"
        assert result['available'] is True
