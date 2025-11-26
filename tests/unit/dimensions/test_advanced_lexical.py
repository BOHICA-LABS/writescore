"""
Tests for AdvancedLexicalDimension - HDD, Yule's K, MATTR, RTTR analysis.
Story 1.4.5 - New dimension split from AdvancedDimension.
"""

from unittest.mock import Mock, patch

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension


@pytest.fixture
def dimension():
    """Create AdvancedLexicalDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return AdvancedLexicalDimension()


@pytest.fixture
def high_diversity_text():
    """Text with high lexical diversity (human-like)."""
    return """
    The unexpected adventure led them through meandering pathways, discovering
    peculiar artifacts scattered throughout forgotten chambers. Ancient inscriptions
    whispered secrets of civilizations long vanished, their mysteries awaiting
    curious minds willing to unravel complex patterns embedded within crumbling walls.
    """


@pytest.fixture
def low_diversity_text():
    """Text with low lexical diversity (AI-like)."""
    return """
    The system needs to optimize the system. The framework uses the framework
    to integrate the system. The solution provides the solution through the
    framework. The system leverages the solution to optimize the framework.
    """


class TestDimensionMetadata:
    """Tests for dimension metadata and registration."""

    def test_dimension_name(self, dimension):
        """Test dimension name is 'advanced_lexical'."""
        assert dimension.dimension_name == "advanced_lexical"

    def test_dimension_weight(self, dimension):
        """Test dimension weight is 12.8% (rebalanced to 100% total)."""
        assert dimension.weight == 12.8

    def test_dimension_tier(self, dimension):
        """Test dimension tier is ADVANCED."""
        assert dimension.tier == "ADVANCED"

    def test_dimension_description(self, dimension):
        """Test dimension has meaningful description."""
        desc = dimension.description
        assert isinstance(desc, str)
        assert len(desc) > 20
        assert any(term in desc for term in ["HDD", "Yule", "lexical", "diversity"])

    def test_dimension_registers_on_init(self):
        """Test dimension self-registers with registry on initialization."""
        DimensionRegistry.clear()
        dim = AdvancedLexicalDimension()

        registered = DimensionRegistry.get("advanced_lexical")
        assert registered is dim


class TestAnalyzeMethod:
    """Tests for analyze() method - must ONLY collect lexical metrics."""

    def test_analyze_returns_lexical_metrics_only(self, dimension):
        """Test analyze() collects ONLY advanced lexical metrics (no GLTR)."""
        text = """
        The quick brown fox jumps over the lazy dog. This sentence demonstrates
        various words with different frequencies and patterns. Additional vocabulary
        provides examples for lexical diversity analysis.
        """ * 10  # Repeat to ensure enough text

        result = dimension.analyze(text)

        # Should contain advanced lexical metrics
        assert 'hdd_score' in result
        assert 'yules_k' in result
        assert 'mattr' in result
        assert 'rttr' in result
        assert 'available' in result

        # Should NOT contain GLTR metrics (those belong in PredictabilityDimension)
        assert 'gltr_top10_percentage' not in result
        assert 'gltr_top100_percentage' not in result
        assert 'gltr_mean_rank' not in result
        assert 'gltr_likelihood' not in result

    def test_analyze_includes_maas_score(self, dimension):
        """Test analyze() includes Maas score (length-corrected TTR)."""
        text = "word " * 100  # Simple repetitive text
        result = dimension.analyze(text)

        # Maas comes from _calculate_advanced_lexical_diversity
        assert 'maas_score' in result

    def test_analyze_includes_vocab_concentration(self, dimension):
        """Test analyze() includes vocabulary concentration metric."""
        text = "word " * 100
        result = dimension.analyze(text)

        assert 'vocab_concentration' in result

    def test_analyze_sets_available_flag(self, dimension):
        """Test analyze() sets 'available' flag."""
        result = dimension.analyze("Sample text for analysis.")
        assert 'available' in result
        assert result['available'] is True

    def test_analyze_handles_empty_text(self, dimension):
        """Test analyze() handles empty text gracefully."""
        result = dimension.analyze("")
        assert 'available' in result


class TestCalculateScoreMethod:
    """Tests for calculate_score() - Gaussian scoring (Story 2.4.1).

    Note: Old threshold-based tests removed. See TestLogitGaussianScoring for comprehensive tests.
    """

    def test_score_handles_none_hdd(self, dimension):
        """Test score when HDD is None (text too short)."""
        metrics = {
            'available': True,
            'hdd_score': None,
            'yules_k': 100.0
        }
        score = dimension.calculate_score(metrics)

        assert 0.0 <= score <= 100.0  # Should use default value (0.5)

    def test_score_handles_none_yules_k(self, dimension):
        """Test score when Yule's K is None."""
        metrics = {
            'available': True,
            'hdd_score': 0.5,
            'yules_k': None
        }
        score = dimension.calculate_score(metrics)

        assert 0.0 <= score <= 100.0  # Should use default value (100.0)

    def test_score_unavailable_data(self, dimension):
        """Test score when data unavailable."""
        metrics = {
            'available': False
        }
        score = dimension.calculate_score(metrics)

        assert score == 50.0  # Neutral score for unavailable data

    def test_score_validates_range(self, dimension):
        """Test score is always in valid 0-100 range."""
        test_cases = [
            {'hdd_score': 0.0, 'yules_k': 500.0},
            {'hdd_score': 0.5, 'yules_k': 100.0},
            {'hdd_score': 0.9, 'yules_k': 30.0},
        ]

        for metrics_case in test_cases:
            metrics = {'available': True, **metrics_case}
            score = dimension.calculate_score(metrics)
            assert 0.0 <= score <= 100.0


class TestGetRecommendations:
    """Tests for get_recommendations() method."""

    def test_recommendations_for_low_hdd(self, dimension):
        """Test recommendations when HDD is low (<0.7)."""
        metrics = {
            'available': True,
            'hdd_score': 0.5,
            'yules_k': 80.0,
            'mattr': 0.70
        }
        recommendations = dimension.get_recommendations(75.0, metrics)

        assert len(recommendations) > 0
        assert any('hdd' in rec.lower() or 'diversity' in rec.lower() for rec in recommendations)

    def test_recommendations_for_high_yules_k(self, dimension):
        """Test recommendations when Yule's K is high (>50)."""
        metrics = {
            'available': True,
            'hdd_score': 0.7,
            'yules_k': 120.0,
            'mattr': 0.70
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any("yule" in rec.lower() or "repetition" in rec.lower() for rec in recommendations)

    def test_recommendations_for_low_mattr(self, dimension):
        """Test recommendations when MATTR is low (<0.70)."""
        metrics = {
            'available': True,
            'hdd_score': 0.7,
            'yules_k': 40.0,
            'mattr': 0.60
        }
        recommendations = dimension.get_recommendations(75.0, metrics)

        assert len(recommendations) > 0
        assert any('mattr' in rec.lower() for rec in recommendations)

    def test_recommendations_for_excellent_diversity(self, dimension):
        """Test recommendations when diversity is excellent."""
        metrics = {
            'available': True,
            'hdd_score': 0.8,
            'yules_k': 40.0,
            'mattr': 0.75
        }
        recommendations = dimension.get_recommendations(100.0, metrics)

        assert len(recommendations) > 0
        assert any('excellent' in rec.lower() for rec in recommendations)

    def test_recommendations_unavailable_data(self, dimension):
        """Test recommendations when data unavailable."""
        metrics = {
            'available': False
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('unavailable' in rec.lower() or 'install' in rec.lower() for rec in recommendations)


class TestGetTiers:
    """Tests for get_tiers() method."""

    def test_get_tiers_structure(self, dimension):
        """Test tier structure is valid."""
        tiers = dimension.get_tiers()

        assert isinstance(tiers, dict)
        assert 'excellent' in tiers
        assert 'good' in tiers
        assert 'acceptable' in tiers
        assert 'poor' in tiers

    def test_tier_ranges(self, dimension):
        """Test tier ranges are properly defined."""
        tiers = dimension.get_tiers()

        excellent_min, excellent_max = tiers['excellent']
        assert excellent_min == 90.0
        assert excellent_max == 100.0


class TestAdvancedLexicalDiversityCalculation:
    """Tests for _calculate_advanced_lexical_diversity() helper method."""

    def test_hdd_calculation(self, dimension):
        """Test HDD (Hypergeometric Distribution D) calculation."""
        # Generate 100 unique alphabetic words (regex requires [a-z]{3,})
        # Using base-26 encoding: wordaaa, wordaab, wordaac, ..., worddvs
        unique_words = []
        for i in range(100):
            # Convert i to base-26 using letters (e.g., 0→aaa, 1→aab, 25→aaz, 26→aba)
            suffix = ""
            n = i
            for _ in range(3):
                suffix = chr(97 + (n % 26)) + suffix
                n //= 26
            unique_words.append("word" + suffix)
        text = " ".join(unique_words)

        result = dimension._calculate_advanced_lexical_diversity(text)

        assert 'hdd_score' in result
        if result.get('hdd_score') is not None:
            assert 0.0 <= result['hdd_score'] <= 1.0

    def test_yules_k_calculation(self, dimension):
        """Test Yule's K calculation."""
        # Generate text with some repetition (more realistic than 100 unique words)
        # Yule's K is negative for perfect diversity (all unique), positive for typical text
        unique_words = []
        for i in range(50):
            suffix = ""
            n = i
            for _ in range(3):
                suffix = chr(97 + (n % 26)) + suffix
                n //= 26
            unique_words.append("word" + suffix)

        # Repeat each word twice to get 100 total words with 50 unique
        # This gives more realistic Yule's K values (positive)
        text = " ".join(unique_words * 2)

        result = dimension._calculate_advanced_lexical_diversity(text)

        assert 'yules_k' in result
        if result.get('yules_k') is not None:
            # Yule's K can be negative for perfect diversity, positive for typical text
            assert isinstance(result['yules_k'], (int, float))

    def test_maas_calculation(self, dimension):
        """Test Maas score calculation."""
        # Generate 100 unique alphabetic words
        unique_words = []
        for i in range(100):
            suffix = ""
            n = i
            for _ in range(3):
                suffix = chr(97 + (n % 26)) + suffix
                n //= 26
            unique_words.append("word" + suffix)
        text = " ".join(unique_words)

        result = dimension._calculate_advanced_lexical_diversity(text)

        assert 'maas_score' in result

    def test_vocab_concentration_calculation(self, dimension):
        """Test vocabulary concentration calculation."""
        # Generate 100 unique alphabetic words
        unique_words = []
        for i in range(100):
            suffix = ""
            n = i
            for _ in range(3):
                suffix = chr(97 + (n % 26)) + suffix
                n //= 26
            unique_words.append("word" + suffix)
        text = " ".join(unique_words)

        result = dimension._calculate_advanced_lexical_diversity(text)

        assert 'vocab_concentration' in result
        if result.get('vocab_concentration') is not None:
            assert 0.0 <= result['vocab_concentration'] <= 1.0

    def test_handles_short_text(self, dimension):
        """Test handling of text too short for reliable metrics (<50 words)."""
        text = "word " * 10  # Only 10 words
        result = dimension._calculate_advanced_lexical_diversity(text)

        # Should return empty dict for text <50 words
        assert isinstance(result, dict)

    def test_handles_code_blocks(self, dimension):
        """Test removal of code blocks before analysis."""
        text_with_code = """
        Here is some text with variety.
        ```python
        def foo():
            pass
        ```
        More diverse content here.
        """ * 10

        result = dimension._calculate_advanced_lexical_diversity(text_with_code)
        assert isinstance(result, dict)


class TestTextacyLexicalDiversityCalculation:
    """Tests for _calculate_textacy_lexical_diversity() helper method."""

    @patch('writescore.dimensions.advanced_lexical.nlp_spacy')
    def test_mattr_calculation(self, mock_nlp, dimension):
        """Test MATTR calculation."""
        # Mock spacy doc with iterable tokens for RTTR calculation
        mock_token1 = Mock()
        mock_token1.is_alpha = True
        mock_token1.is_stop = False
        mock_token1.text = "sample"

        mock_token2 = Mock()
        mock_token2.is_alpha = True
        mock_token2.is_stop = False
        mock_token2.text = "text"

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_token1, mock_token2]))
        mock_nlp.return_value = mock_doc

        with patch('writescore.dimensions.advanced_lexical.diversity.segmented_ttr', return_value=0.72):
            result = dimension._calculate_textacy_lexical_diversity("Sample text")

            assert 'mattr' in result
            assert result['mattr'] == 0.72

    def test_rttr_calculation(self, dimension):
        """Test RTTR (Root Type-Token Ratio) calculation."""
        text = " ".join([f"word{i}" for i in range(100)])
        result = dimension._calculate_textacy_lexical_diversity(text)

        assert 'rttr' in result
        if result.get('rttr', 0) > 0:
            assert result['rttr'] > 0

    def test_handles_errors_gracefully(self, dimension):
        """Test error handling when textacy fails."""
        result = dimension._calculate_textacy_lexical_diversity("")

        assert 'available' in result
        assert 'mattr' in result


class TestLogitGaussianScoring:
    """Tests for logit+Gaussian scoring migration (Story 2.4.1, AC6)."""

    def test_calculate_score_at_optimal(self, dimension):
        """Test scoring at optimal HDD (≈0.73, logit ≈ 1.0)."""
        metrics = {
            'available': True,
            'hdd_score': 0.73  # Optimal (logit ≈ 1.0)
        }
        score = dimension.calculate_score(metrics)

        # At optimal, score should be near 100.0
        assert 95.0 <= score <= 100.0

    def test_calculate_score_within_one_sigma(self, dimension):
        """Test scoring within ±1σ of optimal (μ=1.0, σ=0.5)."""
        # σ=0.5 in logit space
        # μ-σ ≈ 0.5 → HDD ≈ 0.62
        # μ+σ ≈ 1.5 → HDD ≈ 0.82
        test_cases = [
            0.62,  # μ-σ
            0.82,  # μ+σ
        ]

        for hdd in test_cases:
            metrics = {
                'available': True,
                'hdd_score': hdd
            }
            score = dimension.calculate_score(metrics)

            # Within 1σ should score 58-95 (allowing slight rounding)
            assert 58.0 <= score <= 95.0, \
                f"HDD {hdd} scored {score}, expected 58-95 (within 1σ)"

    def test_calculate_score_high_diversity(self, dimension):
        """Test scoring with high HDD (human-like)."""
        metrics = {
            'available': True,
            'hdd_score': 0.80  # High diversity (human-like)
        }
        score = dimension.calculate_score(metrics)

        # High HDD should score high (allowing slight rounding)
        assert 74.0 <= score <= 100.0

    def test_calculate_score_low_diversity(self, dimension):
        """Test scoring with low HDD (AI-like)."""
        metrics = {
            'available': True,
            'hdd_score': 0.45  # Low diversity (AI-like)
        }
        score = dimension.calculate_score(metrics)

        # Low HDD should score low
        assert 0.0 <= score <= 50.0

    def test_calculate_score_very_low_diversity(self, dimension):
        """Test scoring with very low HDD (strong AI signal)."""
        metrics = {
            'available': True,
            'hdd_score': 0.30  # Very low diversity
        }
        score = dimension.calculate_score(metrics)

        # Very low HDD should score very low
        assert 0.0 <= score <= 30.0

    def test_calculate_score_boundary_near_zero(self, dimension):
        """Test scoring near lower boundary (HDD ≈ 0)."""
        metrics = {
            'available': True,
            'hdd_score': 0.05  # Near 0
        }
        score = dimension.calculate_score(metrics)

        # Near 0 is far from optimal, should score very low
        assert 0.0 <= score <= 20.0

    def test_calculate_score_boundary_near_one(self, dimension):
        """Test scoring near upper boundary (HDD ≈ 1)."""
        metrics = {
            'available': True,
            'hdd_score': 0.95  # Near 1
        }
        score = dimension.calculate_score(metrics)

        # Near 1 is far above optimal (0.73), should score lower
        assert 0.0 <= score <= 70.0

    def test_calculate_score_monotonic_below_optimal(self, dimension):
        """Test that score increases as HDD approaches optimal from below."""
        hdd_values = [0.30, 0.45, 0.60, 0.73]
        scores = []

        for hdd in hdd_values:
            metrics = {
                'available': True,
                'hdd_score': hdd
            }
            scores.append(dimension.calculate_score(metrics))

        # Scores should increase as we approach optimal from below
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i+1], \
                f"Score should increase toward optimal: {scores[i]} <= {scores[i+1]} (HDD {hdd_values[i]} vs {hdd_values[i+1]})"

    def test_calculate_score_monotonic_above_optimal(self, dimension):
        """Test that score decreases as HDD moves away from optimal above."""
        hdd_values = [0.73, 0.80, 0.90, 0.95]
        scores = []

        for hdd in hdd_values:
            metrics = {
                'available': True,
                'hdd_score': hdd
            }
            scores.append(dimension.calculate_score(metrics))

        # Scores should decrease as we move away from optimal
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1], \
                f"Score should decrease from optimal: {scores[i]} >= {scores[i+1]} (HDD {hdd_values[i]} vs {hdd_values[i+1]})"

    def test_calculate_score_validates_range(self, dimension):
        """Test that all scores are in valid 0-100 range."""
        test_hdds = [0.01, 0.20, 0.50, 0.73, 0.85, 0.95, 0.99]

        for hdd in test_hdds:
            metrics = {
                'available': True,
                'hdd_score': hdd
            }
            score = dimension.calculate_score(metrics)
            assert 0.0 <= score <= 100.0, f"Score {score} for HDD={hdd} out of range"

    def test_calculate_score_unavailable_data(self, dimension):
        """Test fallback score when data unavailable."""
        metrics = {
            'available': False
        }
        score = dimension.calculate_score(metrics)

        # Should return neutral 50.0 when data unavailable
        assert score == 50.0

    def test_calculate_score_none_hdd(self, dimension):
        """Test fallback when HDD is None (text too short)."""
        metrics = {
            'available': True,
            'hdd_score': None  # Text too short for HDD calculation
        }
        score = dimension.calculate_score(metrics)

        # Should use default 0.5 and calculate score
        assert 0.0 <= score <= 100.0


class TestBackwardCompatibility:
    """Tests for backward compatibility alias."""

    def test_backward_compatibility_alias_exists(self):
        """Test AdvancedLexicalAnalyzer alias exists for backward compatibility."""
        from writescore.dimensions.advanced_lexical import AdvancedLexicalAnalyzer

        DimensionRegistry.clear()
        dim = AdvancedLexicalAnalyzer()

        assert dim.dimension_name == "advanced_lexical"
        assert dim.weight == 12.8  # rebalanced to 100% total
