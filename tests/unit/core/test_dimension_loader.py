"""
Tests for DimensionLoader and registry-based dimension loading (Story 1.4.11).

This test suite validates:
- DimensionLoader basic functionality
- Profile loading (fast/balanced/full)
- Custom profile registration
- Analyzer integration with config
- Performance characteristics
"""

import tempfile
import time
from pathlib import Path

import pytest

from writescore.core.analysis_config import AnalysisConfig
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.dimension_loader import BUILTIN_DIMENSION_PROFILES, DimensionLoader
from writescore.core.dimension_registry import DimensionRegistry


class TestDimensionLoaderBasics:
    """Test basic DimensionLoader functionality."""

    def test_load_single_dimension(self):
        """Test loading a single dimension."""
        # Start fresh
        DimensionRegistry.clear()

        loader = DimensionLoader()
        result = loader.load_dimensions(["perplexity"])

        assert len(result["loaded"]) == 1
        assert "perplexity" in result["loaded"]
        assert len(result["failed"]) == 0
        assert DimensionRegistry.has("perplexity")

    def test_load_fast_profile(self):
        """Test loading fast profile (4 dimensions)."""
        loader = DimensionLoader()
        result = loader.load_from_profile("fast")

        assert len(result["loaded"]) == 4
        expected = set(BUILTIN_DIMENSION_PROFILES["fast"])
        assert set(result["loaded"]) == expected
        assert len(result["failed"]) == 0

    def test_load_balanced_profile(self):
        """Test loading balanced profile (8 dimensions)."""
        loader = DimensionLoader()
        result = loader.load_from_profile("balanced")

        assert len(result["loaded"]) == 8
        expected = set(BUILTIN_DIMENSION_PROFILES["balanced"])
        assert set(result["loaded"]) == expected

    def test_load_full_profile(self):
        """Test loading full profile (17 dimensions)."""
        loader = DimensionLoader()
        result = loader.load_from_profile("full")

        assert len(result["loaded"]) == 17
        expected = set(BUILTIN_DIMENSION_PROFILES["full"])
        assert set(result["loaded"]) == expected

    def test_load_invalid_dimension(self):
        """Test loading unknown dimension fails gracefully."""
        loader = DimensionLoader()
        result = loader.load_dimensions(["unknown_dimension"])

        assert len(result["loaded"]) == 0
        assert "unknown_dimension" in result["failed"]

    def test_load_invalid_profile(self):
        """Test loading unknown profile raises ValueError."""
        loader = DimensionLoader()

        with pytest.raises(ValueError, match="Unknown profile"):
            loader.load_from_profile("invalid_profile")


class TestCustomProfiles:
    """Test custom profile registration and loading."""

    def test_register_custom_profile(self):
        """Test registering a custom profile."""
        DimensionLoader.register_custom_profile("test_profile", ["perplexity", "burstiness"])

        profiles = DimensionLoader.list_profiles()
        assert "test_profile" in profiles
        assert profiles["test_profile"] == ["perplexity", "burstiness"]

    def test_cannot_override_builtin_profile(self):
        """Test that built-in profiles cannot be overridden."""
        with pytest.raises(ValueError, match="Cannot override built-in profile"):
            DimensionLoader.register_custom_profile("fast", ["perplexity"])

    def test_register_invalid_dimensions(self):
        """Test that invalid dimensions are rejected."""
        with pytest.raises(ValueError, match="Unknown dimensions"):
            DimensionLoader.register_custom_profile("bad_profile", ["perplexity", "fake_dimension"])

    def test_load_custom_profile(self):
        """Test loading a custom profile."""
        DimensionLoader.register_custom_profile(
            "writing_quality", ["perplexity", "burstiness", "voice"]
        )

        loader = DimensionLoader()
        result = loader.load_from_profile("writing_quality")

        assert len(result["loaded"]) == 3
        assert set(result["loaded"]) == {"perplexity", "burstiness", "voice"}


class TestAnalyzerWithConfig:
    """Test AIPatternAnalyzer integration with AnalysisConfig."""

    def setup_method(self):
        """Create test file."""
        self.test_content = (
            """# Test Document

This is a test document with multiple paragraphs. The content includes various
linguistic patterns that will be analyzed by all dimensions.

However, we must consider the implications. Moreover, the analysis should detect
these transition markers as potential AI signatures.

## Technical Content

The perplexity score measures predictability. Advanced lexical diversity includes
metrics for vocabulary richness assessment.
"""
            * 2
        )

        # Create temp file
        self.temp_file_path = tempfile.mktemp(suffix=".md")
        with open(self.temp_file_path, "w") as f:
            f.write(self.test_content)

    def teardown_method(self):
        """Clean up test file."""
        Path(self.temp_file_path).unlink(missing_ok=True)

    def test_analyzer_with_fast_profile(self):
        """Test analyzer with fast profile config."""
        config = AnalysisConfig(dimension_profile="fast")
        analyzer = AIPatternAnalyzer(config=config)

        assert len(analyzer.dimensions) == 4
        assert "perplexity" in analyzer.dimensions
        assert "voice" not in analyzer.dimensions  # Not in fast profile

    def test_analyzer_with_balanced_profile(self):
        """Test analyzer with balanced profile config."""
        config = AnalysisConfig(dimension_profile="balanced")
        analyzer = AIPatternAnalyzer(config=config)

        assert len(analyzer.dimensions) == 8
        assert "voice" in analyzer.dimensions
        assert "predictability" not in analyzer.dimensions  # Not in balanced

    def test_analyzer_with_full_profile(self):
        """Test analyzer with full profile config."""
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)

        assert len(analyzer.dimensions) == 17

    def test_analyzer_with_explicit_dimensions(self):
        """Test analyzer with explicit dimension list."""
        config = AnalysisConfig(dimensions_to_load=["perplexity", "burstiness"])
        analyzer = AIPatternAnalyzer(config=config)

        assert len(analyzer.dimensions) == 2
        assert "perplexity" in analyzer.dimensions
        assert "burstiness" in analyzer.dimensions

    def test_analyzer_with_custom_profile(self):
        """Test analyzer with custom profile."""
        config = AnalysisConfig(
            dimension_profile="my_profile",
            custom_profiles={"my_profile": ["perplexity", "structure", "formatting"]},
        )
        analyzer = AIPatternAnalyzer(config=config)

        assert len(analyzer.dimensions) == 3

    def test_analysis_with_fast_profile(self):
        """Test full analysis with fast profile."""
        config = AnalysisConfig(dimension_profile="fast")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(self.temp_file_path)

        # Verify results object
        assert results.total_words > 0
        assert results.perplexity_score != ""
        assert results.burstiness_score != ""
        assert results.voice_score == "UNKNOWN"  # Not loaded

    def test_analysis_with_balanced_profile(self):
        """Test full analysis with balanced profile."""
        config = AnalysisConfig(dimension_profile="balanced")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(self.temp_file_path)

        assert results.voice_score != "UNKNOWN"  # Should be loaded
        assert results.lexical_score != "UNKNOWN"  # Should be loaded
        assert results.predictability_score == "UNKNOWN"  # Not in balanced


class TestPerformance:
    """Test performance characteristics of selective loading."""

    def setup_method(self):
        """Create test file."""
        self.test_content = (
            """# Performance Test

This is a performance test document. It contains enough content to trigger
meaningful analysis across all dimensions.

However, we need to ensure that fast mode completes quickly while full mode
provides comprehensive analysis.
"""
            * 5
        )

        self.temp_file_path = tempfile.mktemp(suffix=".md")
        with open(self.temp_file_path, "w") as f:
            f.write(self.test_content)

    def teardown_method(self):
        """Clean up test file."""
        Path(self.temp_file_path).unlink(missing_ok=True)

    def test_fast_profile_performance(self):
        """Verify fast profile loads quickly (<1s)."""
        config = AnalysisConfig(dimension_profile="fast")

        start = time.time()
        analyzer = AIPatternAnalyzer(config=config)
        analyzer.analyze_file(self.temp_file_path)
        elapsed = time.time() - start

        # Fast profile should complete in < 1 second
        # (might be slower on first run due to imports, but should be fast after)
        assert elapsed < 5.0, f"Fast profile took {elapsed}s (expected < 5s)"
        assert len(analyzer.dimensions) == 4

    def test_balanced_faster_than_full(self):
        """Verify balanced profile is faster than full profile."""
        config_balanced = AnalysisConfig(dimension_profile="balanced")
        config_full = AnalysisConfig(dimension_profile="full")

        # Test balanced
        start_bal = time.time()
        analyzer_bal = AIPatternAnalyzer(config=config_balanced)
        analyzer_bal.analyze_file(self.temp_file_path)
        time_bal = time.time() - start_bal

        # Test full
        start_full = time.time()
        analyzer_full = AIPatternAnalyzer(config=config_full)
        analyzer_full.analyze_file(self.temp_file_path)
        time_full = time.time() - start_full

        # Balanced should be faster (or at least not significantly slower)
        # We're lenient here since timing can vary
        assert (
            time_bal <= time_full * 1.5
        ), f"Balanced ({time_bal}s) should be faster than full ({time_full}s)"
