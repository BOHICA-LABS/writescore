"""
Tests for PerplexityDimension - true perplexity calculation (Story 2.4.0.7).

Tests mathematical perplexity calculation using GPT-2 language model.
"""

import time

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.perplexity import PerplexityDimension


@pytest.fixture
def dimension():
    """Create PerplexityDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    # Clear model cache to ensure clean state
    PerplexityDimension.clear_model_cache()
    return PerplexityDimension()


@pytest.fixture
def sample_text():
    """Sample text for testing perplexity calculation."""
    return """The quick brown fox jumps over the lazy dog. This is a test sentence
    with various words to analyze perplexity patterns. Natural language contains
    unpredictable elements that make it interesting."""


@pytest.fixture
def ai_like_text():
    """Text that should have low perplexity (AI-like)."""
    # Very predictable, common phrases
    return """The cat sat on the mat. The dog ran in the park. The sun is shining.
    It is a nice day. The weather is good."""


@pytest.fixture
def human_like_text():
    """Text that should have higher perplexity (human-like)."""
    # More varied, less predictable
    return """Serendipitous encounters beneath azure skies evoke contemplative musings.
    Ephemeral moments crystallize into cherished memories, defying temporal constraints."""


class TestDimensionProperties:
    """Tests for dimension metadata properties."""

    def test_dimension_name(self, dimension):
        """Test dimension name is correct."""
        assert dimension.dimension_name == "perplexity"

    def test_weight_is_3_percent(self, dimension):
        """Test dimension weight is 2.8% (rebalanced to 100% total)."""
        assert dimension.weight == 3.0

    def test_tier_is_advanced(self, dimension):
        """Test dimension tier is ADVANCED."""
        assert dimension.tier == "ADVANCED"

    def test_description_mentions_perplexity(self, dimension):
        """Test dimension description mentions perplexity."""
        description = dimension.description
        assert "perplexity" in description.lower()
        assert "language model" in description.lower()


class TestModelLoadingAndCaching:
    """Tests for model loading and caching."""

    def test_model_loads_successfully(self, dimension):
        """Test GPT-2 model loads without errors."""
        model = dimension._get_model()
        assert model is not None

    def test_tokenizer_loads_successfully(self, dimension):
        """Test GPT-2 tokenizer loads without errors."""
        tokenizer = dimension._get_tokenizer()
        assert tokenizer is not None

    def test_model_caching_reuses_instance(self, dimension):
        """Test that model is cached and reused."""
        model1 = dimension._get_model()
        model2 = dimension._get_model()
        assert model1 is model2  # Same cached instance

    def test_tokenizer_caching_reuses_instance(self, dimension):
        """Test that tokenizer is cached and reused."""
        tokenizer1 = dimension._get_tokenizer()
        tokenizer2 = dimension._get_tokenizer()
        assert tokenizer1 is tokenizer2  # Same cached instance

    def test_clear_model_cache_resets_model(self, dimension):
        """Test that clearing cache resets model."""
        model1 = dimension._get_model()
        PerplexityDimension.clear_model_cache()
        model2 = dimension._get_model()
        assert model1 is not model2  # Different instances after clear


class TestTokenization:
    """Tests for tokenization with input validation."""

    def test_tokenize_valid_text(self, dimension, sample_text):
        """Test tokenization of valid text."""
        tokens = dimension._tokenize(sample_text)
        assert tokens is not None
        assert tokens.shape[0] == 1  # Batch size 1
        assert tokens.shape[1] > 0  # Has tokens

    def test_tokenize_rejects_empty_text(self, dimension):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            dimension._tokenize("")

    def test_tokenize_rejects_whitespace_only(self, dimension):
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="printable characters"):
            dimension._tokenize("   \n\t   ")

    def test_tokenize_rejects_too_long_text(self, dimension):
        """Test that text over 1MB raises ValueError."""
        huge_text = "word " * 250_000  # Over 1MB
        with pytest.raises(ValueError, match="1MB"):
            dimension._tokenize(huge_text)

    def test_tokenize_handles_unicode(self, dimension):
        """Test tokenization handles Unicode characters."""
        unicode_text = "Hello 世界 Привет مرحبا"
        tokens = dimension._tokenize(unicode_text)
        assert tokens.shape[1] > 0

    def test_tokenize_sanitizes_control_characters(self, dimension):
        """Test that control characters are removed."""
        text_with_control = "Hello\x00World\x01Test"
        tokens = dimension._tokenize(text_with_control)
        assert tokens.shape[1] > 0  # Should still tokenize after sanitization


class TestPerplexityCalculation:
    """Tests for core perplexity calculation."""

    def test_calculate_perplexity_returns_valid_values(self, dimension, sample_text):
        """Test that perplexity calculation returns valid values."""
        perplexity, avg_log_prob, token_count = dimension._calculate_perplexity(sample_text)

        assert perplexity > 0, "Perplexity must be positive"
        assert avg_log_prob < 0, "Average log probability should be negative"
        assert token_count > 0, "Token count must be positive"

    def test_calculate_perplexity_formula_correctness(self, dimension):
        """Test perplexity formula: PP = exp(-avg_log_prob)."""
        text = "The cat sat on the mat"
        perplexity, avg_log_prob, _ = dimension._calculate_perplexity(text)

        # Verify formula: perplexity = exp(-avg_log_prob)
        import math

        expected_perplexity = math.exp(-avg_log_prob)
        assert abs(perplexity - expected_perplexity) < 0.01

    def test_get_token_log_prob_returns_negative(self, dimension):
        """Test that token log probabilities are negative."""
        text = "Hello world"
        tokens = dimension._tokenize(text)

        # Get log prob for second token given first
        context = tokens[:, :1]
        target = tokens[:, 1:2]
        log_prob = dimension._get_token_log_prob(context, target)

        assert log_prob < 0, "Log probability must be negative"
        assert log_prob > -20, "Log probability should be reasonable (not -inf)"

    def test_perplexity_consistent_across_calls(self, dimension, sample_text):
        """Test that perplexity calculation is deterministic."""
        pp1, _, _ = dimension._calculate_perplexity(sample_text)
        pp2, _, _ = dimension._calculate_perplexity(sample_text)

        assert abs(pp1 - pp2) < 0.01, "Perplexity should be consistent"


class TestMonotonicScoring:
    """Tests for monotonic scoring function."""

    def test_score_perplexity_below_threshold_low(self, dimension):
        """Test scoring for perplexity below 25.0 (AI-like)."""
        score = dimension._score_perplexity(21.2)  # AI median
        assert 0.0 <= score <= 20.0, "Score should be 0-20 for very low perplexity"
        assert score > 0.0, "Score should be > 0 for non-zero perplexity"

    def test_score_perplexity_at_threshold_low(self, dimension):
        """Test scoring at threshold low (25.0)."""
        score = dimension._score_perplexity(25.0)
        assert 15.0 <= score <= 25.0, "Score should be around 20 at threshold low"

    def test_score_perplexity_mid_range(self, dimension):
        """Test scoring in mid-range (25.0-45.0)."""
        score = dimension._score_perplexity(35.0)  # Between thresholds
        assert 40.0 <= score <= 60.0, "Score should be 40-60 for mid-range perplexity"

    def test_score_perplexity_at_threshold_high(self, dimension):
        """Test scoring at threshold high (45.0)."""
        score = dimension._score_perplexity(45.0)
        assert 75.0 <= score <= 85.0, "Score should be around 80 at threshold high"

    def test_score_perplexity_above_threshold_high(self, dimension):
        """Test scoring for perplexity above 45.0 (human-like)."""
        score = dimension._score_perplexity(50.0)
        assert 80.0 <= score <= 100.0, "Score should be 80-100 for high perplexity"

    def test_monotonic_increasing(self, dimension):
        """Test that scoring is monotonic increasing."""
        score_low = dimension._score_perplexity(21.2)  # AI median
        score_med = dimension._score_perplexity(35.9)  # Human median
        score_high = dimension._score_perplexity(50.0)  # Very human

        assert score_low < score_med < score_high, "Scoring must be monotonic increasing"

    def test_score_threshold_boundaries(self, dimension):
        """Test scoring at exact threshold boundaries."""
        score_25 = dimension._score_perplexity(25.0)
        score_45 = dimension._score_perplexity(45.0)

        # At 25.0, should be around 20
        assert 18.0 <= score_25 <= 22.0

        # At 45.0, should be around 80
        assert 78.0 <= score_45 <= 82.0

    def test_score_range_valid(self, dimension):
        """Test that all scores are in valid 0-100 range."""
        test_perplexities = [10.0, 21.2, 25.0, 35.9, 45.0, 50.0, 100.0]

        for pp in test_perplexities:
            score = dimension._score_perplexity(pp)
            assert 0.0 <= score <= 100.0, f"Score {score} for PP={pp} out of range"


class TestAnalyzeMethod:
    """Tests for analyze() method."""

    def test_analyze_returns_expected_structure(self, dimension, sample_text):
        """Test that analyze() returns correct structure."""
        result = dimension.analyze(sample_text)

        # Check required fields
        assert "score" in result
        assert "raw_value" in result
        assert "perplexity" in result
        assert "token_count" in result
        assert "avg_log_prob" in result
        assert "threshold_low" in result
        assert "threshold_high" in result
        assert "interpretation" in result
        assert "available" in result

    def test_analyze_perplexity_equals_raw_value(self, dimension, sample_text):
        """Test that perplexity equals raw_value."""
        result = dimension.analyze(sample_text)
        assert result["perplexity"] == result["raw_value"]

    def test_analyze_thresholds_correct(self, dimension, sample_text):
        """Test that thresholds are set correctly."""
        result = dimension.analyze(sample_text)
        assert result["threshold_low"] == 25.0
        assert result["threshold_high"] == 45.0

    def test_analyze_available_true_on_success(self, dimension, sample_text):
        """Test that available=True on successful analysis."""
        result = dimension.analyze(sample_text)
        assert result["available"] is True

    def test_analyze_handles_empty_text(self, dimension):
        """Test that empty text returns neutral values."""
        result = dimension.analyze("")

        assert result["available"] is False
        assert result["score"] == 50.0  # Neutral
        assert result["perplexity"] == 0.0
        assert result["token_count"] == 0

    def test_analyze_handles_whitespace_only(self, dimension):
        """Test that whitespace-only text returns neutral values."""
        result = dimension.analyze("   \n\t   ")

        assert result["available"] is False
        assert result["score"] == 50.0

    def test_analyze_short_text(self, dimension):
        """Test analysis of short text."""
        result = dimension.analyze("Hello world")

        assert result["available"] is True
        assert result["perplexity"] > 0
        assert result["token_count"] >= 2

    def test_analyze_includes_interpretation(self, dimension, sample_text):
        """Test that interpretation is included."""
        result = dimension.analyze(sample_text)
        assert isinstance(result["interpretation"], str)
        assert len(result["interpretation"]) > 0


class TestCalculateScore:
    """Tests for calculate_score() method (Story 2.4.1 monotonic migration)."""

    def test_calculate_score_uses_monotonic_helper(self, dimension):
        """Test that calculate_score uses _monotonic_score() helper."""
        # Provide metrics directly (not from analyze())
        metrics = {
            "available": True,
            "perplexity": 35.0,  # Human median
        }
        score = dimension.calculate_score(metrics)

        # Score should match what _monotonic_score would return
        # 35.0 is midway between 25.0 and 45.0, so score should be around 50
        assert 45.0 <= score <= 55.0

    def test_calculate_score_at_threshold_low(self, dimension):
        """Test scoring at threshold low (perplexity=25.0)."""
        metrics = {"available": True, "perplexity": 25.0}
        score = dimension.calculate_score(metrics)

        # At threshold_low=25.0, monotonic scoring returns 25.0
        assert score == 25.0

    def test_calculate_score_below_threshold_low(self, dimension):
        """Test scoring below threshold low (perplexity<25.0, AI-like)."""
        metrics = {
            "available": True,
            "perplexity": 21.2,  # AI median
        }
        score = dimension.calculate_score(metrics)

        # Below 25.0: should be fixed at 25.0
        assert score == 25.0

    def test_calculate_score_mid_range(self, dimension):
        """Test scoring in mid-range (perplexity between 25-45)."""
        metrics = {
            "available": True,
            "perplexity": 35.0,  # Between thresholds
        }
        score = dimension.calculate_score(metrics)

        # Between 25-45: should be 25-75 (linear)
        # 35 is midpoint, so score around 50
        assert 45.0 <= score <= 55.0

    def test_calculate_score_at_threshold_high(self, dimension):
        """Test scoring at threshold high (perplexity=45.0)."""
        metrics = {"available": True, "perplexity": 45.0}
        score = dimension.calculate_score(metrics)

        # At threshold_high=45.0, monotonic scoring returns 75.0
        assert score == 75.0

    def test_calculate_score_above_threshold_high(self, dimension):
        """Test scoring above threshold high (perplexity>45.0, human-like)."""
        metrics = {"available": True, "perplexity": 50.0}
        score = dimension.calculate_score(metrics)

        # Above 45.0: should be 75-100 (asymptotic)
        assert 75.0 <= score <= 100.0

    def test_calculate_score_monotonic_increasing(self, dimension):
        """Test that scoring is monotonic increasing with perplexity."""
        perplexity_values = [21.2, 25.0, 35.9, 45.0, 50.0]
        scores = []

        for pp in perplexity_values:
            metrics = {"available": True, "perplexity": pp}
            scores.append(dimension.calculate_score(metrics))

        # Scores should increase monotonically (or stay same for values below threshold)
        # Below threshold_low (25): all get 25.0
        # Then increases from 25 to 45 (25.0 to 75.0)
        # Then increases from 45+ (75.0 to 100.0 asymptotic)
        for i in range(len(scores) - 1):
            assert (
                scores[i] <= scores[i + 1]
            ), f"Score should increase or stay same: {scores[i]} <= {scores[i+1]} (PP {perplexity_values[i]} vs {perplexity_values[i+1]})"

    def test_calculate_score_handles_unavailable(self, dimension):
        """Test that calculate_score handles unavailable data gracefully."""
        metrics = {"available": False, "perplexity": 0.0}
        score = dimension.calculate_score(metrics)

        # Should return neutral score
        assert score == 50.0

    def test_calculate_score_validates_range(self, dimension, sample_text):
        """Test that calculate_score validates score is in 0-100 range."""
        result = dimension.analyze(sample_text)
        score = dimension.calculate_score(result)

        assert 0.0 <= score <= 100.0

    def test_calculate_score_all_values_in_range(self, dimension):
        """Test that all perplexity values produce valid scores."""
        test_perplexities = [10.0, 21.2, 25.0, 35.9, 45.0, 50.0, 100.0]

        for pp in test_perplexities:
            metrics = {"available": True, "perplexity": pp}
            score = dimension.calculate_score(metrics)
            assert 0.0 <= score <= 100.0, f"Score {score} for PP={pp} out of range"


class TestGetRecommendations:
    """Tests for get_recommendations() method."""

    def test_recommendations_for_low_perplexity(self, dimension):
        """Test recommendations for low perplexity (<25.0)."""
        metrics = {"available": True, "perplexity": 20.0, "score": 16.0}
        recommendations = dimension.get_recommendations(16.0, metrics)

        assert len(recommendations) > 0
        assert any("AI signature" in rec or "predictable" in rec for rec in recommendations)

    def test_recommendations_for_moderate_perplexity(self, dimension):
        """Test recommendations for moderate perplexity (25-35)."""
        metrics = {"available": True, "perplexity": 30.0, "score": 35.0}
        recommendations = dimension.get_recommendations(35.0, metrics)

        assert len(recommendations) > 0

    def test_recommendations_for_high_perplexity(self, dimension):
        """Test recommendations for high perplexity (>45.0)."""
        metrics = {"available": True, "perplexity": 50.0, "score": 85.0}
        recommendations = dimension.get_recommendations(85.0, metrics)

        assert len(recommendations) > 0
        assert any("human-like" in rec.lower() or "good" in rec.lower() for rec in recommendations)

    def test_recommendations_when_unavailable(self, dimension):
        """Test recommendations when analysis unavailable."""
        metrics = {"available": False, "perplexity": 0.0}
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any("unavailable" in rec.lower() for rec in recommendations)


class TestFormatDisplay:
    """Tests for format_display() method."""

    def test_format_display_shows_perplexity(self, dimension, sample_text):
        """Test that format_display shows perplexity value."""
        result = dimension.analyze(sample_text)
        display = dimension.format_display(result)

        assert isinstance(display, str)
        assert "perplexity" in display.lower() or str(result["perplexity"])[:3] in display

    def test_format_display_unavailable(self, dimension):
        """Test format_display when unavailable."""
        metrics = {"available": False}
        display = dimension.format_display(metrics)

        assert "unavailable" in display.lower()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_short_text(self, dimension):
        """Test with very short text (5 words)."""
        result = dimension.analyze("Hello world from test suite")

        assert result["available"] is True
        assert result["perplexity"] > 0

    def test_single_word_text(self, dimension):
        """Test with single word (should fail gracefully)."""
        result = dimension.analyze("Hello")

        # Single word may fail tokenization (needs 2+ tokens)
        # Should return neutral score if fails
        assert "score" in result

    def test_text_with_numbers(self, dimension):
        """Test text with numbers."""
        result = dimension.analyze("The year 2024 has 365 days and 12 months")

        assert result["available"] is True
        assert result["perplexity"] > 0

    def test_text_with_punctuation(self, dimension):
        """Test text with various punctuation."""
        text = "Hello! How are you? I'm fine, thanks. What about you?"
        result = dimension.analyze(text)

        assert result["available"] is True
        assert result["perplexity"] > 0

    def test_text_with_special_characters(self, dimension):
        """Test text with special characters."""
        text = "Email: test@example.com, Price: $99.99, Code: #ABC123"
        result = dimension.analyze(text)

        assert result["available"] is True
        assert result["perplexity"] > 0


class TestPerformance:
    """Tests for performance."""

    def test_performance_1k_words(self, dimension):
        """Test performance on ~1k words."""
        text = "This is a test sentence with various words. " * 100  # ~500 words

        start = time.time()
        result = dimension.analyze(text)
        elapsed = time.time() - start

        assert result["available"] is True
        # Should complete in reasonable time (may be slow on first run due to model load)
        # We're generous with timing since model loading is one-time
        assert elapsed < 30.0, f"Analysis took {elapsed:.2f}s (expected <30s including model load)"

    def test_model_caching_improves_performance(self, dimension):
        """Test that model caching improves performance."""
        text = "Test sentence for caching performance measurement."

        # First call (may load model)
        start1 = time.time()
        dimension.analyze(text)
        elapsed1 = time.time() - start1

        # Second call (should use cached model)
        start2 = time.time()
        dimension.analyze(text)
        elapsed2 = time.time() - start2

        # Second call should be faster or comparable (model already loaded)
        # We don't assert strict inequality due to system variability
        assert elapsed2 <= elapsed1 * 2, "Second call should benefit from cached model"


class TestIntegration:
    """Integration tests."""

    def test_dimension_self_registers(self):
        """Test that dimension self-registers."""
        DimensionRegistry.clear()
        PerplexityDimension()

        registered = DimensionRegistry.get("perplexity")
        assert registered is not None
        assert registered.dimension_name == "perplexity"

    def test_full_pipeline(self, dimension, sample_text):
        """Test complete analysis pipeline."""
        # Analyze
        result = dimension.analyze(sample_text)
        assert result["available"] is True
        assert result["perplexity"] > 0

        # Calculate score
        score = dimension.calculate_score(result)
        assert 0.0 <= score <= 100.0

        # Get recommendations
        recommendations = dimension.get_recommendations(score, result)
        assert isinstance(recommendations, list)

        # Format display
        display = dimension.format_display(result)
        assert isinstance(display, str)

    def test_backward_compatibility_structure(self, dimension, sample_text):
        """Test that dimension maintains backward compatible structure."""
        result = dimension.analyze(sample_text)

        # Should have required fields
        assert "available" in result
        assert "analysis_mode" in result

        # Score should be calculable
        score = dimension.calculate_score(result)
        assert isinstance(score, float)

    def test_legacy_score_method(self, dimension, sample_text):
        """Test legacy score() method."""
        result = dimension.analyze(sample_text)
        score, label = dimension.score(result)

        assert isinstance(score, float)
        assert isinstance(label, str)
        assert 0.0 <= score <= 10.0  # Legacy 10-point scale
        assert label in ["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR"]


class TestAnalyzeDetailed:
    """Tests for analyze_detailed() method."""

    def test_analyze_detailed_returns_note(self, dimension):
        """Test that analyze_detailed indicates perplexity is document-level."""
        lines = ["Sample line 1", "Sample line 2"]
        result = dimension.analyze_detailed(lines)

        assert "note" in result
        assert "document-level" in result["note"]


class TestAIvsHumanDiscrimination:
    """Tests for AI vs human discrimination."""

    def test_ai_text_has_lower_perplexity(self, dimension, ai_like_text, human_like_text):
        """Test that AI-like text has lower perplexity than human-like text."""
        ai_result = dimension.analyze(ai_like_text)
        human_result = dimension.analyze(human_like_text)

        # This may not always hold for all text samples, but should trend this way
        # We check scores instead of raw perplexity as scoring is more stable
        assert (
            ai_result["score"] < human_result["score"]
        ), f"AI-like score ({ai_result['score']}) should be lower than human-like ({human_result['score']})"


# Performance benchmarks (can be slow)
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests (marked as slow)."""

    def test_benchmark_various_lengths(self, dimension):
        """Benchmark analysis on various text lengths."""
        test_cases = [
            (
                "Short",
                "Hello world test",
                2.0,
            ),  # Includes model loading overhead (~1.4s first call)
            ("Medium", "Test sentence " * 50, 10.0),
            ("Long", "Test sentence " * 200, 30.0),
        ]

        for name, text, max_time in test_cases:
            start = time.time()
            result = dimension.analyze(text)
            elapsed = time.time() - start

            assert result["available"] is True, f"{name} analysis failed"
            # Be generous with timing for different hardware
            assert elapsed < max_time, f"{name} took {elapsed:.2f}s (expected <{max_time}s)"
