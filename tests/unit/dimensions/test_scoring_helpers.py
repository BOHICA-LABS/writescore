"""
Comprehensive unit tests for scoring helper methods in DimensionStrategy base class.

Tests cover:
- _gaussian_score(): Gaussian (bell curve) scoring
- _monotonic_score(): Monotonic increasing/decreasing scoring
- _logit_transform(): Logit transformation for bounded [0,1] values
- _log_transform(): Natural log transformation for positive values

Coverage target: >= 95%
"""

import math

import pytest

from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

# ========================================================================
# MOCK DIMENSION FOR TESTING
# ========================================================================


class MockDimension(DimensionStrategy):
    """Minimal concrete implementation for testing helper methods."""

    @property
    def dimension_name(self) -> str:
        return "mock_dimension"

    @property
    def weight(self) -> float:
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        return DimensionTier.SUPPORTING

    @property
    def description(self) -> str:
        return "Mock dimension for testing scoring helpers"

    def analyze(self, text: str, lines: list = None, **kwargs) -> dict:
        return {}

    def calculate_score(self, metrics: dict) -> float:
        return 100.0

    def get_recommendations(self, score: float, metrics: dict) -> list:
        return []

    def get_tiers(self) -> dict:
        return {
            "excellent": (90.0, 100.0),
            "good": (75.0, 89.9),
            "acceptable": (50.0, 74.9),
            "poor": (0.0, 49.9),
        }


@pytest.fixture
def dimension():
    """Fixture providing a mock dimension instance for testing helpers."""
    return MockDimension()


# ========================================================================
# GAUSSIAN SCORE TESTS
# ========================================================================


class TestGaussianScore:
    """Test suite for _gaussian_score() helper method."""

    def test_perfect_match(self, dimension):
        """Score should be 100.0 when value equals target exactly."""
        score = dimension._gaussian_score(value=10.0, target=10.0, width=2.0)
        assert score == 100.0

    def test_one_sigma_away(self, dimension):
        """Score should be ~60.7 at one standard deviation from target."""
        score = dimension._gaussian_score(value=12.0, target=10.0, width=2.0)
        expected = 100.0 * math.exp(-0.5)  # exp(-1/(2*1)) = exp(-0.5) ≈ 0.6065
        assert abs(score - expected) < 0.01
        assert 60.0 < score < 61.5

    def test_two_sigma_away(self, dimension):
        """Score should be ~13.5 at two standard deviations from target."""
        score = dimension._gaussian_score(value=14.0, target=10.0, width=2.0)
        expected = 100.0 * math.exp(-2.0)  # exp(-4/(2*4)) = exp(-2) ≈ 0.135
        assert abs(score - expected) < 0.5
        assert 13.0 < score < 14.0

    def test_symmetric(self, dimension):
        """Score should be symmetric around target (value ± delta same score)."""
        score_plus = dimension._gaussian_score(value=12.0, target=10.0, width=2.0)
        score_minus = dimension._gaussian_score(value=8.0, target=10.0, width=2.0)
        assert abs(score_plus - score_minus) < 0.001

    def test_extreme_distance(self, dimension):
        """Score should approach 0 when very far from target."""
        score = dimension._gaussian_score(value=100.0, target=10.0, width=2.0)
        assert score < 1e-10  # Essentially 0

    def test_zero_width(self, dimension):
        """Zero width should be handled gracefully (minimum width used)."""
        score = dimension._gaussian_score(value=10.0, target=10.0, width=0.0)
        assert score == 100.0  # Should still work with minimum width

    def test_negative_values(self, dimension):
        """Should work correctly with negative targets and values."""
        score = dimension._gaussian_score(value=-10.0, target=-10.0, width=2.0)
        assert score == 100.0

        score_offset = dimension._gaussian_score(value=-8.0, target=-10.0, width=2.0)
        expected = 100.0 * math.exp(-0.5)
        assert abs(score_offset - expected) < 0.01

    def test_range(self, dimension):
        """Score should always be in range [0.0, 100.0]."""
        test_cases = [
            (10.0, 10.0, 2.0),  # Perfect match
            (0.0, 10.0, 2.0),  # Far below
            (100.0, 10.0, 2.0),  # Far above
            (-50.0, 10.0, 5.0),  # Very far negative
        ]

        for value, target, width in test_cases:
            score = dimension._gaussian_score(value, target, width)
            assert (
                0.0 <= score <= 100.0
            ), f"Score {score} out of range for {value}, {target}, {width}"


# ========================================================================
# MONOTONIC SCORE TESTS (INCREASING)
# ========================================================================


class TestMonotonicIncreasing:
    """Test suite for _monotonic_score() with increasing=True."""

    def test_below_low(self, dimension):
        """Value below threshold_low should return 25.0."""
        score = dimension._monotonic_score(
            value=50, threshold_low=60, threshold_high=100, increasing=True
        )
        assert score == 25.0

    def test_at_low(self, dimension):
        """Value at threshold_low should return 25.0."""
        score = dimension._monotonic_score(
            value=60, threshold_low=60, threshold_high=100, increasing=True
        )
        assert score == 25.0

    def test_midpoint(self, dimension):
        """Value at midpoint between thresholds should return 50.0."""
        score = dimension._monotonic_score(
            value=80, threshold_low=60, threshold_high=100, increasing=True
        )
        assert score == 50.0

    def test_at_high(self, dimension):
        """Value at threshold_high should return 75.0."""
        score = dimension._monotonic_score(
            value=100, threshold_low=60, threshold_high=100, increasing=True
        )
        assert score == 75.0

    def test_above_high(self, dimension):
        """Value above threshold_high should be between 75.0 and 100.0."""
        score = dimension._monotonic_score(
            value=120, threshold_low=60, threshold_high=100, increasing=True
        )
        assert 75.0 < score < 100.0

    def test_far_above(self, dimension):
        """Value far above threshold_high should approach 100.0."""
        score = dimension._monotonic_score(
            value=500, threshold_low=60, threshold_high=100, increasing=True
        )
        assert score > 99.0  # Should be very close to 100

    def test_linear_zone(self, dimension):
        """Verify linear interpolation in zone between thresholds."""
        # Test quarter point (should be 37.5)
        score_quarter = dimension._monotonic_score(
            value=70, threshold_low=60, threshold_high=100, increasing=True
        )
        assert abs(score_quarter - 37.5) < 0.01

        # Test three-quarter point (should be 62.5)
        score_three_quarter = dimension._monotonic_score(
            value=90, threshold_low=60, threshold_high=100, increasing=True
        )
        assert abs(score_three_quarter - 62.5) < 0.01


# ========================================================================
# MONOTONIC SCORE TESTS (DECREASING)
# ========================================================================


class TestMonotonicDecreasing:
    """Test suite for _monotonic_score() with increasing=False."""

    def test_below_low(self, dimension):
        """Value below threshold_low should return 75.0 for decreasing."""
        score = dimension._monotonic_score(
            value=50, threshold_low=60, threshold_high=100, increasing=False
        )
        assert score == 75.0

    def test_above_high(self, dimension):
        """Value above threshold_high should approach 0.0 for decreasing."""
        score = dimension._monotonic_score(
            value=120, threshold_low=60, threshold_high=100, increasing=False
        )
        assert 0.0 < score < 25.0

    def test_far_above(self, dimension):
        """Value far above threshold_high should approach 0.0."""
        score = dimension._monotonic_score(
            value=500, threshold_low=60, threshold_high=100, increasing=False
        )
        assert score < 1.0  # Should be very close to 0

    def test_midpoint(self, dimension):
        """Value at midpoint should return 50.0 for decreasing."""
        score = dimension._monotonic_score(
            value=80, threshold_low=60, threshold_high=100, increasing=False
        )
        assert score == 50.0

    def test_linear_zone_decreasing(self, dimension):
        """Verify linear interpolation for decreasing monotonic."""
        # Test quarter point (should be 62.5)
        score_quarter = dimension._monotonic_score(
            value=70, threshold_low=60, threshold_high=100, increasing=False
        )
        assert abs(score_quarter - 62.5) < 0.01

        # Test three-quarter point (should be 37.5)
        score_three_quarter = dimension._monotonic_score(
            value=90, threshold_low=60, threshold_high=100, increasing=False
        )
        assert abs(score_three_quarter - 37.5) < 0.01


# ========================================================================
# MONOTONIC SCORE EDGE CASES
# ========================================================================


class TestMonotonicEdgeCases:
    """Test edge cases for _monotonic_score()."""

    def test_equal_thresholds_raises_error(self, dimension):
        """Equal thresholds should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            dimension._monotonic_score(
                value=50, threshold_low=60, threshold_high=60, increasing=True
            )
        assert "threshold_high" in str(exc_info.value)
        assert "must be >" in str(exc_info.value)

    def test_inverted_thresholds_raises_error(self, dimension):
        """Inverted thresholds (low > high) should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            dimension._monotonic_score(
                value=50, threshold_low=100, threshold_high=60, increasing=True
            )
        assert "threshold_high" in str(exc_info.value)

    def test_range_increasing(self, dimension):
        """All increasing scores should be in [0.0, 100.0]."""
        test_values = [0, 50, 60, 80, 100, 150, 1000]
        for value in test_values:
            score = dimension._monotonic_score(
                value=value, threshold_low=60, threshold_high=100, increasing=True
            )
            assert 0.0 <= score <= 100.0

    def test_range_decreasing(self, dimension):
        """All decreasing scores should be in [0.0, 100.0]."""
        test_values = [0, 50, 60, 80, 100, 150, 1000]
        for value in test_values:
            score = dimension._monotonic_score(
                value=value, threshold_low=60, threshold_high=100, increasing=False
            )
            assert 0.0 <= score <= 100.0


# ========================================================================
# LOGIT TRANSFORM TESTS
# ========================================================================


class TestLogitTransform:
    """Test suite for _logit_transform() helper method."""

    def test_midpoint(self, dimension):
        """Logit of 0.5 should be 0.0 (midpoint)."""
        result = dimension._logit_transform(0.5)
        assert abs(result - 0.0) < 1e-10

    def test_above_mid(self, dimension):
        """Logit of value > 0.5 should be positive."""
        result = dimension._logit_transform(0.7)
        assert result > 0
        # Approximately log(0.7/0.3) ≈ 0.847
        expected = math.log(0.7 / 0.3)
        assert abs(result - expected) < 0.001

    def test_below_mid(self, dimension):
        """Logit of value < 0.5 should be negative."""
        result = dimension._logit_transform(0.3)
        assert result < 0
        # Approximately log(0.3/0.7) ≈ -0.847
        expected = math.log(0.3 / 0.7)
        assert abs(result - expected) < 0.001

    def test_boundary_zero(self, dimension):
        """Logit of 0.0 should use epsilon boundary (no crash)."""
        result = dimension._logit_transform(0.0)
        # Should be large negative but not infinite
        assert result < -20  # log(1e-10 / (1 - 1e-10)) ≈ -23.03
        assert math.isfinite(result)

    def test_boundary_one(self, dimension):
        """Logit of 1.0 should use epsilon boundary (no crash)."""
        result = dimension._logit_transform(1.0)
        # Should be large positive but not infinite
        assert result > 20  # log((1-1e-10) / 1e-10) ≈ 23.03
        assert math.isfinite(result)

    def test_symmetric(self, dimension):
        """Logit should be symmetric: logit(p) = -logit(1-p)."""
        p = 0.7
        logit_p = dimension._logit_transform(p)
        logit_1_minus_p = dimension._logit_transform(1 - p)
        assert abs(logit_p + logit_1_minus_p) < 1e-10

    def test_high_value(self, dimension):
        """Logit of high value (0.9) should map to large positive."""
        result = dimension._logit_transform(0.9)
        expected = math.log(0.9 / 0.1)  # log(9) ≈ 2.197
        assert abs(result - expected) < 0.001

    def test_custom_epsilon(self, dimension):
        """Custom epsilon should be respected."""
        result = dimension._logit_transform(0.0, epsilon=1e-5)
        # Should use 1e-5 instead of default 1e-10
        expected = math.log(1e-5 / (1 - 1e-5))
        assert abs(result - expected) < 0.001


# ========================================================================
# LOG TRANSFORM TESTS
# ========================================================================


class TestLogTransform:
    """Test suite for _log_transform() helper method."""

    def test_positive(self, dimension):
        """Log of positive values should work correctly."""
        result = dimension._log_transform(10.0)
        expected = math.log(10.0)  # ≈ 2.303
        assert abs(result - expected) < 0.001

    def test_one(self, dimension):
        """Log of 1.0 should be 0.0."""
        result = dimension._log_transform(1.0)
        assert abs(result - 0.0) < 1e-10

    def test_e(self, dimension):
        """Log of e should be 1.0."""
        result = dimension._log_transform(math.e)
        assert abs(result - 1.0) < 1e-10

    def test_zero(self, dimension):
        """Log of 0 should use epsilon (no crash)."""
        result = dimension._log_transform(0.0)
        expected = math.log(1e-10)  # ≈ -23.03
        assert abs(result - expected) < 0.001
        assert math.isfinite(result)

    def test_negative(self, dimension):
        """Negative values should be treated as epsilon."""
        result = dimension._log_transform(-5.0)
        expected = math.log(1e-10)  # Treated as epsilon
        assert abs(result - expected) < 0.001

    def test_large_value(self, dimension):
        """Log of large values should work correctly."""
        result = dimension._log_transform(100.0)
        expected = math.log(100.0)  # ≈ 4.605
        assert abs(result - expected) < 0.001

    def test_custom_epsilon(self, dimension):
        """Custom epsilon should be respected."""
        result = dimension._log_transform(0.0, epsilon=1e-5)
        expected = math.log(1e-5)
        assert abs(result - expected) < 0.001

    def test_very_small_positive(self, dimension):
        """Very small positive values should work."""
        result = dimension._log_transform(1e-8)
        expected = math.log(1e-8)
        assert abs(result - expected) < 0.001


# ========================================================================
# INTEGRATION TESTS
# ========================================================================


class TestScoringHelpersIntegration:
    """Integration tests verifying helpers work together correctly."""

    def test_logit_then_gaussian(self, dimension):
        """Logit transform followed by Gaussian scoring should work."""
        # Transform bounded value to unbounded
        bounded_value = 0.7
        unbounded = dimension._logit_transform(bounded_value)

        # Apply Gaussian scoring on unbounded value
        score = dimension._gaussian_score(unbounded, target=0.0, width=1.0)

        # Score should be reasonable (< 100 since not at target)
        assert 0.0 <= score <= 100.0
        assert score < 100.0  # Not perfect since unbounded ≠ 0

    def test_log_then_gaussian(self, dimension):
        """Log transform followed by Gaussian scoring should work."""
        # Transform right-skewed value
        value = 10.0
        log_value = dimension._log_transform(value)

        # Apply Gaussian scoring
        score = dimension._gaussian_score(log_value, target=math.log(10.0), width=0.5)

        # Should be perfect score since log(10) matches target
        assert abs(score - 100.0) < 0.01

    def test_all_helpers_accessible(self, dimension):
        """All helper methods should be accessible from dimension instance."""
        assert hasattr(dimension, "_gaussian_score")
        assert callable(dimension._gaussian_score)

        assert hasattr(dimension, "_monotonic_score")
        assert callable(dimension._monotonic_score)

        assert hasattr(dimension, "_logit_transform")
        assert callable(dimension._logit_transform)

        assert hasattr(dimension, "_log_transform")
        assert callable(dimension._log_transform)
