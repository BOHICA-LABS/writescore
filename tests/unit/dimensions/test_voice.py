"""
Tests for VoiceAnalyzer - voice and authenticity markers detection.
"""

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.voice import VoiceAnalyzer


@pytest.fixture
def analyzer():
    """Create VoiceAnalyzer instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return VoiceAnalyzer()


@pytest.fixture
def analyzer_with_domain_terms():
    """Create VoiceAnalyzer with domain terms."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return VoiceAnalyzer(domain_terms=[r'\bAPI\b', r'\bendpoint\b', r'\bHTTPS?\b'])


@pytest.fixture
def text_with_voice():
    """Text with personal voice markers."""
    return """# My Experience

I've been working with this technology, and I think it's great. We've found that
you can improve your results by following these steps. Here's what you'll need
to do: start with the basics, and you're going to see improvement quickly.

In my opinion, we're seeing a paradigm shift here. I'd recommend that you try
this approach, because it'll make your workflow much easier.
"""


@pytest.fixture
def text_impersonal():
    """Text without voice markers (AI-like)."""
    return """# Overview

This technology provides several benefits. The system offers improved performance
through optimization. Implementation requires following the documented procedures.
Results demonstrate significant improvements in efficiency metrics.
"""


@pytest.fixture
def text_with_technical_terms():
    """Text with technical domain terms."""
    return """# API Documentation

The REST API provides HTTP endpoints for data access. Configure HTTPS for
secure connections. Use the API key for authentication.
"""


class TestInit:
    """Tests for __init__ method."""

    def test_init_no_domain_terms(self):
        """Test initialization without domain terms."""
        DimensionRegistry.clear()
        analyzer = VoiceAnalyzer()
        assert analyzer.domain_terms == []

    def test_init_with_domain_terms(self):
        """Test initialization with domain terms."""
        DimensionRegistry.clear()
        terms = [r'\bAPI\b', r'\bHTTPS?\b']
        analyzer = VoiceAnalyzer(domain_terms=terms)
        assert analyzer.domain_terms == terms


class TestAnalyzeVoice:
    """Tests for _analyze_voice method."""

    def test_analyze_voice_with_markers(self, analyzer, text_with_voice):
        """Test voice analysis with personal markers."""
        result = analyzer._analyze_voice(text_with_voice)

        assert 'first_person' in result
        assert 'direct_address' in result
        assert 'contractions' in result
        assert result['first_person'] > 0
        assert result['direct_address'] > 0
        assert result['contractions'] > 0

    def test_analyze_voice_impersonal(self, analyzer, text_impersonal):
        """Test voice analysis on impersonal text."""
        result = analyzer._analyze_voice(text_impersonal)

        assert result['first_person'] == 0
        assert result['direct_address'] == 0
        assert result['contractions'] == 0

    def test_analyze_voice_first_person_detection(self, analyzer):
        """Test first-person pronoun detection."""
        text = "I think we should proceed. My opinion is that our approach works."
        result = analyzer._analyze_voice(text)

        assert result['first_person'] >= 4  # I, we, My, our

    def test_analyze_voice_direct_address_detection(self, analyzer):
        """Test direct address detection."""
        text = "You should try this. Your results will improve."
        result = analyzer._analyze_voice(text)

        assert result['direct_address'] >= 2  # You, Your

    def test_analyze_voice_contractions_detection(self, analyzer):
        """Test contraction detection."""
        text = "I've been working on this. We're making progress. It's working well."
        result = analyzer._analyze_voice(text)

        assert result['contractions'] >= 3


class TestAnalyzeTechnicalDepth:
    """Tests for _analyze_technical_depth method."""

    def test_technical_depth_with_terms(self, analyzer_with_domain_terms, text_with_technical_terms):
        """Test technical depth with domain terms."""
        result = analyzer_with_domain_terms._analyze_technical_depth(text_with_technical_terms)

        assert 'count' in result
        assert 'terms' in result
        assert result['count'] > 0
        assert len(result['terms']) > 0

    def test_technical_depth_no_terms(self, analyzer, text_with_voice):
        """Test technical depth without domain terms."""
        result = analyzer._analyze_technical_depth(text_with_voice)

        assert result['count'] == 0
        assert result['terms'] == []

    def test_technical_depth_limits_results(self, analyzer_with_domain_terms):
        """Test that results are limited to 20 terms."""
        # Create text with many matches
        text = " ".join(["API endpoint HTTP"] * 10)
        result = analyzer_with_domain_terms._analyze_technical_depth(text)

        assert result['count'] >= 20
        assert len(result['terms']) == 20  # Limited to 20


class TestAnalyze:
    """Tests for main analyze method."""

    def test_analyze_basic(self, analyzer, text_with_voice):
        """Test basic analyze method."""
        result = analyzer.analyze(text_with_voice)

        assert 'voice' in result
        assert 'technical_depth' in result
        assert isinstance(result['voice'], dict)
        assert isinstance(result['technical_depth'], dict)

    def test_analyze_empty_text(self, analyzer):
        """Test analyze on empty text."""
        result = analyzer.analyze("")

        assert result['voice']['first_person'] == 0
        assert result['voice']['direct_address'] == 0
        assert result['technical_depth']['count'] == 0


class TestAnalyzeDetailed:
    """Tests for analyze_detailed method."""

    def test_analyze_detailed_basic(self, analyzer, text_with_voice):
        """Test detailed analysis method."""
        lines = text_with_voice.split('\n')
        result = analyzer.analyze_detailed(lines)

        assert 'voice' in result
        assert 'technical_depth' in result


class TestScore:
    """Tests for score method."""

    def test_score_high_voice(self, analyzer):
        """Test score for strong personal voice."""
        analysis = {
            'first_person': 5,
            'direct_address': 15,
            'contractions': 3,
            'total_words': 100
        }
        score, label = analyzer.score(analysis)

        assert score == 10.0
        assert label == "EXCELLENT"

    def test_score_medium_voice(self, analyzer):
        """Test score for medium personal voice."""
        analysis = {
            'first_person': 5,
            'direct_address': 5,
            'contractions': 2,  # 2% contraction ratio
            'total_words': 100
        }
        score, label = analyzer.score(analysis)

        assert score == 7.0
        assert label == "GOOD"

    def test_score_low_voice(self, analyzer):
        """Test score for weak personal voice."""
        analysis = {
            'first_person': 0,
            'direct_address': 15,
            'contractions': 0,
            'total_words': 100
        }
        score, label = analyzer.score(analysis)

        assert score == 4.0
        assert label == "NEEDS WORK"

    def test_score_very_low_voice(self, analyzer):
        """Test score for no personal voice."""
        analysis = {
            'first_person': 0,
            'direct_address': 0,
            'contractions': 0,
            'total_words': 100
        }
        score, label = analyzer.score(analysis)

        assert score == 2.0
        assert label == "POOR"


class TestMonotonicIncreasingScoring:
    """Tests for monotonic increasing scoring (Story 2.4.1, Group D)."""

    def test_calculate_score_at_threshold_low(self, analyzer):
        """Test score exactly at threshold_low (0.5% contractions)."""
        metrics = {
            'available': True,
            'voice': {
                'contractions': 5,
                'total_words': 1000  # 0.5% ratio
            }
        }
        score = analyzer.calculate_score(metrics)

        # At threshold_low, should be around 25 (bottom of linear zone)
        assert 24 <= score <= 26

    def test_calculate_score_below_threshold_low(self, analyzer):
        """Test score below threshold_low (0.2% contractions)."""
        metrics = {
            'available': True,
            'voice': {
                'contractions': 2,
                'total_words': 1000  # 0.2% ratio
            }
        }
        score = analyzer.calculate_score(metrics)

        # Below threshold_low, should be fixed at 25
        assert score == 25.0

    def test_calculate_score_mid_range(self, analyzer):
        """Test score in mid-range (1.0% contractions)."""
        metrics = {
            'available': True,
            'voice': {
                'contractions': 10,
                'total_words': 1000  # 1.0% ratio
            }
        }
        score = analyzer.calculate_score(metrics)

        # In linear zone between thresholds, should be 25-75
        assert 45 <= score <= 55  # Around midpoint

    def test_calculate_score_at_threshold_high(self, analyzer):
        """Test score exactly at threshold_high (1.5% contractions)."""
        metrics = {
            'available': True,
            'voice': {
                'contractions': 15,
                'total_words': 1000  # 1.5% ratio
            }
        }
        score = analyzer.calculate_score(metrics)

        # At threshold_high, should be around 75 (top of linear zone)
        assert 74 <= score <= 76

    def test_calculate_score_above_threshold_high(self, analyzer):
        """Test score above threshold_high (2.5% contractions)."""
        metrics = {
            'available': True,
            'voice': {
                'contractions': 25,
                'total_words': 1000  # 2.5% ratio
            }
        }
        score = analyzer.calculate_score(metrics)

        # Above threshold_high, should be asymptotic 75-100
        assert 75 <= score <= 100

    def test_calculate_score_monotonic_increasing(self, analyzer):
        """Test that score increases monotonically with contraction ratio."""
        ratios = [0.002, 0.005, 0.010, 0.015, 0.020, 0.030]
        scores = []

        for ratio in ratios:
            metrics = {
                'available': True,
                'voice': {
                    'contractions': int(ratio * 1000),
                    'total_words': 1000
                }
            }
            scores.append(analyzer.calculate_score(metrics))

        # Scores should increase monotonically
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], f"Score decreased: {scores[i]} -> {scores[i + 1]} at ratio {ratios[i]} -> {ratios[i+1]}"

    def test_calculate_score_human_like_range(self, analyzer):
        """Test human-like contraction ratios (1-3%)."""
        human_ratios = [0.010, 0.015, 0.020, 0.025, 0.030]

        for ratio in human_ratios:
            metrics = {
                'available': True,
                'voice': {
                    'contractions': int(ratio * 1000),
                    'total_words': 1000
                }
            }
            score = analyzer.calculate_score(metrics)

            # Human-like contractions should score high (50+)
            assert score >= 50, f"Human ratio {ratio*100}% scored too low: {score}"

    def test_calculate_score_ai_like_range(self, analyzer):
        """Test AI-like contraction ratios (0-0.5%)."""
        ai_ratios = [0.000, 0.001, 0.003, 0.005]

        for ratio in ai_ratios:
            metrics = {
                'available': True,
                'voice': {
                    'contractions': int(ratio * 1000),
                    'total_words': 1000
                }
            }
            score = analyzer.calculate_score(metrics)

            # AI-like (low) contractions should score low (≤50)
            assert score <= 50, f"AI ratio {ratio*100}% scored too high: {score}"

    def test_calculate_score_validates_range(self, analyzer):
        """Test that all scores are in valid 0-100 range."""
        test_ratios = [0.0, 0.005, 0.010, 0.015, 0.020, 0.050, 0.100]

        for ratio in test_ratios:
            metrics = {
                'available': True,
                'voice': {
                    'contractions': int(ratio * 1000) if ratio > 0 else 0,
                    'total_words': 1000
                }
            }
            score = analyzer.calculate_score(metrics)

            assert 0 <= score <= 100, f"Score {score} out of range for ratio {ratio}"

    def test_calculate_score_unavailable_data(self, analyzer):
        """Test handling of unavailable data."""
        metrics = {'available': False}
        score = analyzer.calculate_score(metrics)

        assert score == 50.0  # Neutral score for unavailable data

    def test_calculate_score_default_value(self, analyzer):
        """Test handling of missing voice metrics."""
        metrics = {
            'available': True,
            'voice': {}  # Missing contractions and total_words
        }
        score = analyzer.calculate_score(metrics)

        # Should handle missing data gracefully
        assert 0 <= score <= 100


class TestIntegration:
    """Integration tests."""

    def test_full_analysis_pipeline(self, analyzer, text_with_voice):
        """Test complete analysis pipeline."""
        result = analyzer.analyze(text_with_voice)

        assert result['voice']['first_person'] > 0
        assert result['voice']['direct_address'] > 0
        assert result['voice']['contractions'] > 0

    def test_with_domain_terms_pipeline(self, analyzer_with_domain_terms, text_with_technical_terms):
        """Test pipeline with domain terms."""
        result = analyzer_with_domain_terms.analyze(text_with_technical_terms)

        assert result['technical_depth']['count'] > 0
