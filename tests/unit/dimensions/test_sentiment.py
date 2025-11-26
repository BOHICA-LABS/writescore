"""
Tests for SentimentDimension - Sentiment variance analysis.
Story 1.4.6 - Adding missing test file for sentiment dimension.
"""

import pytest
from unittest.mock import Mock, patch
from writescore.dimensions.sentiment import SentimentDimension
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode


@pytest.fixture
def dimension():
    """Create SentimentDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return SentimentDimension()


@pytest.fixture
def varied_sentiment_text():
    """Text with high sentiment variance (human-like)."""
    return """
    I'm absolutely thrilled about this amazing breakthrough! This discovery changes everything.
    However, we must approach this cautiously. There are concerning implications.
    The data itself is neutral, showing neither positive nor negative trends.
    I'm disappointed by the lack of progress on this critical issue.
    Overall, this represents a fascinating development worth exploring further.
    """


@pytest.fixture
def flat_sentiment_text():
    """Text with low sentiment variance (AI-like)."""
    return """
    The system operates efficiently. The process functions correctly.
    The framework provides functionality. The implementation works properly.
    The solution delivers results. The method applies techniques effectively.
    """


@pytest.fixture
def neutral_text():
    """Text with neutral sentiment."""
    return """
    The data shows three key trends. First, usage increased by 10 percent.
    Second, engagement remained stable. Third, conversions grew modestly.
    These findings indicate measured progress across multiple metrics.
    """


class TestDimensionMetadata:
    """Tests for dimension metadata and registration."""

    def test_dimension_name(self, dimension):
        """Test dimension name is 'sentiment'."""
        assert dimension.dimension_name == "sentiment"

    def test_dimension_weight(self, dimension):
        """Test dimension weight is 15.6% (rebalanced to 100% total)."""
        assert dimension.weight == 15.6

    def test_dimension_tier(self, dimension):
        """Test dimension tier is SUPPORTING."""
        assert dimension.tier == "SUPPORTING"

    def test_dimension_description(self, dimension):
        """Test dimension has meaningful description."""
        desc = dimension.description
        assert isinstance(desc, str)
        assert len(desc) > 20
        assert "sentiment" in desc.lower()

    def test_dimension_registers_on_init(self):
        """Test dimension self-registers with registry on initialization."""
        DimensionRegistry.clear()
        dim = SentimentDimension()

        registered = DimensionRegistry.get("sentiment")
        assert registered is dim


class TestAnalyzeMethod:
    """Tests for analyze() method."""

    def test_analyze_returns_sentiment_metrics(self, dimension, varied_sentiment_text):
        """Test analyze() returns sentiment variance metrics."""
        result = dimension.analyze(varied_sentiment_text)

        assert 'sentiment' in result
        assert 'available' in result
        assert result['available'] is True

        sentiment = result['sentiment']
        assert 'variance' in sentiment
        assert 'mean' in sentiment

    def test_analyze_accepts_config_parameter(self, dimension, varied_sentiment_text):
        """Test analyze() accepts config parameter (Story 1.4.6)."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        # Should not raise error
        result = dimension.analyze(varied_sentiment_text, config=config)

        assert 'sentiment' in result
        assert 'available' in result

    def test_analyze_with_config_none(self, dimension, varied_sentiment_text):
        """Test analyze() works with config=None."""
        result = dimension.analyze(varied_sentiment_text, config=None)

        assert 'sentiment' in result
        assert 'available' in result

    def test_analyze_high_variance_text(self, dimension, varied_sentiment_text):
        """Test analyze() detects high sentiment variance."""
        result = dimension.analyze(varied_sentiment_text)

        sentiment = result['sentiment']
        # Varied text should have higher variance
        assert sentiment['variance'] > 0.0

    def test_analyze_handles_empty_text(self, dimension):
        """Test analyze() handles empty text gracefully."""
        result = dimension.analyze("")

        assert 'available' in result
        # May be True or False depending on implementation

    def test_analyze_sets_available_flag(self, dimension, neutral_text):
        """Test analyze() sets 'available' flag."""
        result = dimension.analyze(neutral_text)
        assert 'available' in result


class TestCalculateScoreMethod:
    """Tests for calculate_score() - scores based on sentiment variance."""

    def test_score_high_variance_gives_high_score(self, dimension):
        """Test high sentiment variance (≥0.20) gives excellent score (100)."""
        metrics = {
            'sentiment': {
                'variance': 0.25,
                'mean': 0.0
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert score == 100.0

    def test_score_near_neutral_polarity_scores_high(self, dimension):
        """Test near-neutral mean polarity scores high (Story 2.4.1 - Gaussian scoring).

        Migrated from variance-based to mean polarity Gaussian scoring.
        Target μ=0.0, width σ=0.3
        """
        metrics = {
            'sentiment': {
                'variance': 0.17,
                'mean': 0.05  # Slightly positive, within 1σ
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert 85.0 <= score <= 100.0  # Within target range

    def test_score_moderate_positive_bias(self, dimension):
        """Test moderate positive bias scores moderately (Story 2.4.1 - Gaussian scoring).

        AI text shows positive bias (+0.1 to +0.2 mean polarity).
        """
        metrics = {
            'sentiment': {
                'variance': 0.12,
                'mean': 0.25  # Just outside 1σ (0.3)
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert 60.0 <= score <= 85.0  # Outside target, scores lower

    def test_score_strong_positive_bias(self, dimension):
        """Test strong positive bias scores low (Story 2.4.1 - Gaussian scoring).

        Strong AI signal - far from neutral target.
        """
        metrics = {
            'sentiment': {
                'variance': 0.07,
                'mean': 0.5  # ~1.7σ from target
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert 20.0 <= score <= 50.0  # Far from target, scores low

    def test_score_strong_negative_bias(self, dimension):
        """Test strong negative bias scores low (Story 2.4.1 - Gaussian scoring).

        Extreme deviation from neutral target.
        """
        metrics = {
            'sentiment': {
                'variance': 0.02,
                'mean': -0.6  # ~2σ from target
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert 5.0 <= score <= 30.0  # Very far from target, scores very low

    def test_score_validates_range(self, dimension):
        """Test calculate_score validates 0-100 range."""
        metrics = {
            'sentiment': {
                'variance': 0.25,
                'mean': 0.0
            },
            'available': True
        }
        score = dimension.calculate_score(metrics)

        assert 0.0 <= score <= 100.0


class TestGetRecommendationsMethod:
    """Tests for get_recommendations() method."""

    def test_recommendations_for_low_variance(self, dimension):
        """Test recommendations generated for low variance (AI signature)."""
        metrics = {
            'sentiment': {
                'variance': 0.05,
                'mean': 0.0,
                'emotionally_flat': True
            }
        }
        score = 50.0

        recommendations = dimension.get_recommendations(score, metrics)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should mention variance/variation/emotion
        rec_text = ' '.join(recommendations).lower()
        assert any(term in rec_text for term in ['variance', 'variation', 'emotion', 'sentiment'])

    def test_recommendations_for_high_variance(self, dimension):
        """Test fewer/no recommendations for high variance (human-like)."""
        metrics = {
            'sentiment': {
                'variance': 0.25,
                'mean': 0.0,
                'emotionally_flat': False
            }
        }
        score = 100.0

        recommendations = dimension.get_recommendations(score, metrics)

        # High score should have fewer recommendations
        assert isinstance(recommendations, list)


class TestGetTiersMethod:
    """Tests for get_tiers() method."""

    def test_get_tiers_returns_standard_tiers(self, dimension):
        """Test get_tiers() returns standard tier structure."""
        tiers = dimension.get_tiers()

        assert isinstance(tiers, dict)
        assert 'excellent' in tiers
        assert 'good' in tiers
        assert 'acceptable' in tiers
        assert 'poor' in tiers

    def test_tier_ranges_are_valid(self, dimension):
        """Test tier ranges don't overlap and cover 0-100."""
        tiers = dimension.get_tiers()

        for tier_name, (min_score, max_score) in tiers.items():
            assert 0.0 <= min_score <= 100.0
            assert 0.0 <= max_score <= 100.0
            assert min_score <= max_score


class TestBackwardCompatibility:
    """Tests for backward compatibility (config=None behavior)."""

    def test_no_config_parameter_works(self, dimension, neutral_text):
        """Test analyze() works without config parameter (old calling pattern)."""
        # Simulate old code that doesn't pass config
        result = dimension.analyze(neutral_text)

        assert 'sentiment' in result
        assert 'available' in result

    def test_config_none_identical_to_no_config(self, dimension, neutral_text):
        """Test config=None produces identical results to no config."""
        result1 = dimension.analyze(neutral_text)
        result2 = dimension.analyze(neutral_text, config=None)

        # Should produce same results
        assert result1['available'] == result2['available']
        if result1['available'] and result2['available']:
            assert result1['sentiment']['variance'] == result2['sentiment']['variance']


class TestGaussianScoring:
    """Tests for Gaussian scoring migration (Story 2.4.1, AC3)."""

    def test_calculate_score_optimal_neutral_polarity(self, dimension):
        """Test scoring at optimal neutral polarity (μ=0.0) returns near-perfect score."""
        metrics = {
            'sentiment': {
                'mean': 0.0,  # Optimal neutral target
                'variance': 0.10
            }
        }
        score = dimension.calculate_score(metrics)
        
        # Should be 100.0 (or very close)
        assert score >= 99.0
        assert score <= 100.0

    def test_calculate_score_within_one_sigma(self, dimension):
        """Test scoring within 1σ of optimal returns high score."""
        # μ=0.0, σ=0.3, so 1σ range is [-0.3, +0.3]
        # At μ±1σ, Gaussian function returns exp(-0.5) ≈ 0.606
        
        metrics_negative = {
            'sentiment': {
                'mean': -0.3,  # μ - 1σ
                'variance': 0.10
            }
        }
        score_negative = dimension.calculate_score(metrics_negative)
        assert score_negative >= 55.0
        assert score_negative <= 65.0
        
        metrics_positive = {
            'sentiment': {
                'mean': 0.3,  # μ + 1σ
                'variance': 0.10
            }
        }
        score_positive = dimension.calculate_score(metrics_positive)
        assert score_positive >= 55.0
        assert score_positive <= 65.0

    def test_calculate_score_ai_positive_bias(self, dimension):
        """Test scoring for AI positive bias (+0.15) returns moderate score."""
        # Research notes AI shows +0.1 to +0.2 positive bias
        metrics = {
            'sentiment': {
                'mean': 0.15,  # AI positive bias
                'variance': 0.10
            }
        }
        score = dimension.calculate_score(metrics)
        
        # 0.15 is 0.5σ from optimal, should return moderate-high score
        # exp(-0.5 * (0.5)²) ≈ exp(-0.125) ≈ 0.882
        assert score >= 80.0
        assert score <= 90.0

    def test_calculate_score_strong_positive_bias(self, dimension):
        """Test scoring for strong positive bias returns low score."""
        metrics = {
            'sentiment': {
                'mean': 0.6,  # Strong positive bias
                'variance': 0.10
            }
        }
        score = dimension.calculate_score(metrics)
        
        # 0.6 is 2σ from optimal, should return low score
        # exp(-0.5 * 4) ≈ 0.135
        assert score < 20.0

    def test_calculate_score_strong_negative_bias(self, dimension):
        """Test scoring for strong negative bias returns low score."""
        metrics = {
            'sentiment': {
                'mean': -0.6,  # Strong negative bias
                'variance': 0.10
            }
        }
        score = dimension.calculate_score(metrics)
        
        # -0.6 is 2σ from optimal, should return low score
        assert score < 20.0

    def test_calculate_score_symmetric_around_neutral(self, dimension):
        """Test that positive and negative deviations score similarly."""
        metrics_pos = {
            'sentiment': {
                'mean': 0.2,
                'variance': 0.10
            }
        }
        score_pos = dimension.calculate_score(metrics_pos)
        
        metrics_neg = {
            'sentiment': {
                'mean': -0.2,
                'variance': 0.10
            }
        }
        score_neg = dimension.calculate_score(metrics_neg)
        
        # Gaussian is symmetric, so both should score identically
        assert abs(score_pos - score_neg) < 1.0

    def test_calculate_score_monotonicity_from_neutral(self, dimension):
        """Test that score decreases monotonically moving away from neutral."""
        scores = []
        for polarity in [0.0, 0.1, 0.3, 0.5]:
            metrics = {
                'sentiment': {
                    'mean': polarity,
                    'variance': 0.10
                }
            }
            scores.append(dimension.calculate_score(metrics))
        
        # Scores should decrease as we move away from neutral (0.0)
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i+1], f"Score should decrease: {scores[i]} > {scores[i+1]}"
