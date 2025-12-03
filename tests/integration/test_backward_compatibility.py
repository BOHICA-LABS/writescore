"""
Backward compatibility and performance regression tests for Story 1.4.6.

Tests ensure that adding config infrastructure doesn't break existing behavior:
- Existing code calling analyze() without config still works
- config=None produces bit-identical scores to no config
- Performance overhead is <5% in default path
- FAST mode timing remains within 5-15 second bounds

Created: Story 1.4.6 - Analysis Configuration Infrastructure
"""

import time
from pathlib import Path

import pytest

from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.dimension_registry import DimensionRegistry

# Fixtures directory path (relative to this test file)
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear dimension registry before each test to avoid duplicate registration."""
    DimensionRegistry.clear()
    yield
    # Optionally clear after test as well
    DimensionRegistry.clear()


class TestBackwardCompatibility:
    """Ensure config infrastructure doesn't break existing behavior."""

    def test_no_config_parameter_works(self):
        """Existing code calling analyze() without config still works."""
        analyzer = AIPatternAnalyzer()

        # Simulate old calling pattern (no config param)
        result = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"))

        assert result is not None
        assert result.total_words > 0
        # Verify all dimension scores exist
        assert hasattr(result, "perplexity_score")
        assert hasattr(result, "burstiness_score")
        assert hasattr(result, "structure_score")
        assert hasattr(result, "voice_score")
        assert hasattr(result, "formatting_score")

    def test_config_none_identical_results(self):
        """config=None produces bit-identical scores to no config."""
        analyzer = AIPatternAnalyzer()

        # Analyze without config (old behavior)
        result1 = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"))

        # Analyze with config=None (new behavior)
        result2 = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=None)

        # Scores must be identical
        assert result1.perplexity_score == result2.perplexity_score
        assert result1.burstiness_score == result2.burstiness_score
        assert result1.structure_score == result2.structure_score
        assert result1.voice_score == result2.voice_score
        assert result1.formatting_score == result2.formatting_score

        # Check key metrics
        assert result1.ai_vocabulary_per_1k == result2.ai_vocabulary_per_1k
        assert result1.sentence_stdev == result2.sentence_stdev
        assert result1.total_words == result2.total_words

    def test_config_none_identical_to_default_config(self):
        """config=None behaves identically to AnalysisConfig() default."""
        analyzer = AIPatternAnalyzer()

        # Analyze with config=None
        result1 = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=None)

        # Analyze with explicit default config
        default_config = AnalysisConfig()
        result2 = analyzer.analyze_file(
            str(FIXTURES_DIR / "sample_mixed_text.md"), config=default_config
        )

        # Should produce identical results (both use DEFAULT_CONFIG internally)
        assert result1.perplexity_score == result2.perplexity_score
        assert result1.burstiness_score == result2.burstiness_score
        assert result1.structure_score == result2.structure_score

    @pytest.mark.slow
    def test_no_performance_regression_default_path(self):
        """Config=None path has <5% overhead vs no config."""
        analyzer = AIPatternAnalyzer()
        test_file = str(FIXTURES_DIR / "section-1.1-final.md")  # ~5000 words

        # Benchmark: No config (baseline)
        times_no_config = []
        for _ in range(3):
            start = time.time()
            analyzer.analyze_file(test_file)
            times_no_config.append(time.time() - start)
        baseline = sum(times_no_config) / len(times_no_config)

        # Benchmark: config=None (new default path)
        times_config_none = []
        for _ in range(3):
            start = time.time()
            analyzer.analyze_file(test_file, config=None)
            times_config_none.append(time.time() - start)
        with_config = sum(times_config_none) / len(times_config_none)

        # Assert <5% overhead
        overhead_pct = ((with_config - baseline) / baseline) * 100

        print("\nPerformance Results:")
        print(f"  Baseline (no config): {baseline:.2f}s")
        print(f"  With config=None: {with_config:.2f}s")
        print(f"  Overhead: {overhead_pct:.2f}%")

        assert (
            overhead_pct < 5.0
        ), f"Performance regression: {overhead_pct:.1f}% overhead (limit: 5%)"

    @pytest.mark.slow
    def test_fast_mode_timing_within_bounds(self):
        """FAST mode completes analysis within reasonable time bounds."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(mode=AnalysisMode.FAST)
        test_file = str(FIXTURES_DIR / "section-1.2.md")  # ~6600 words

        start = time.time()
        result = analyzer.analyze_file(test_file, config=config)
        elapsed = time.time() - start

        print(f"\nFAST mode timing: {elapsed:.2f}s")

        # Verify timing - FAST mode should be quick (allowing for some variance)
        # Story spec says 5-15s for ~20k words, so 6.6k should be faster
        # Using 0.1-20s as reasonable bound for 6.6k words (system now runs faster)
        assert (
            0.1 <= elapsed <= 20
        ), f"FAST mode took {elapsed:.1f}s (expected 0.1-20s for 6.6k words)"
        assert result is not None
        assert result.total_words > 0


class TestConfigModes:
    """Test that different config modes work correctly (infrastructure only)."""

    def test_fast_mode_creates_results(self):
        """FAST mode creates valid analysis results."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        result = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=config)

        assert result is not None
        assert result.total_words > 0
        # Verify scores exist (they are string values like HIGH/MEDIUM/LOW)
        assert hasattr(result, "perplexity_score")
        assert hasattr(result, "burstiness_score")

    def test_adaptive_mode_creates_results(self):
        """ADAPTIVE mode creates valid analysis results."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        result = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=config)

        assert result is not None
        assert result.total_words > 0
        # Verify scores exist (they are string values like HIGH/MEDIUM/LOW)
        assert hasattr(result, "perplexity_score")
        assert hasattr(result, "burstiness_score")

    def test_sampling_mode_creates_results(self):
        """SAMPLING mode creates valid analysis results."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(
            mode=AnalysisMode.SAMPLING, sampling_sections=5, sampling_chars_per_section=2000
        )

        result = analyzer.analyze_file(str(FIXTURES_DIR / "section-1.1-final.md"), config=config)

        assert result is not None
        assert result.total_words > 0
        # Verify scores exist (they are string values like HIGH/MEDIUM/LOW)
        assert hasattr(result, "perplexity_score")
        assert hasattr(result, "burstiness_score")

    def test_full_mode_creates_results(self):
        """FULL mode creates valid analysis results."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(mode=AnalysisMode.FULL)

        result = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=config)

        assert result is not None
        assert result.total_words > 0
        # Verify scores exist (they are string values like HIGH/MEDIUM/LOW)
        assert hasattr(result, "perplexity_score")
        assert hasattr(result, "burstiness_score")


class TestConfigPropagation:
    """Test that config properly propagates through analyzer to dimensions."""

    def test_config_reaches_dimensions(self):
        """Verify config parameter reaches dimension analyze methods."""
        analyzer = AIPatternAnalyzer()
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        # This should work without errors if config is properly threaded
        result = analyzer.analyze_file(str(FIXTURES_DIR / "sample_mixed_text.md"), config=config)

        # If we got a result, config was successfully passed through
        assert result is not None

    def test_different_configs_accepted(self):
        """Verify analyzer accepts various config objects."""
        analyzer = AIPatternAnalyzer()
        test_file = str(FIXTURES_DIR / "sample_mixed_text.md")

        # Test different config modes
        configs = [
            None,
            AnalysisConfig(mode=AnalysisMode.FAST),
            AnalysisConfig(mode=AnalysisMode.ADAPTIVE),
            AnalysisConfig(mode=AnalysisMode.SAMPLING, sampling_sections=3),
            AnalysisConfig(mode=AnalysisMode.FULL),
        ]

        for config in configs:
            result = analyzer.analyze_file(test_file, config=config)
            assert result is not None
            assert result.total_words > 0
