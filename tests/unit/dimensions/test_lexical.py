"""
Tests for LexicalAnalyzer - vocabulary diversity and richness detection.
"""

import pytest
from writescore.dimensions.lexical import LexicalAnalyzer
from writescore.core.dimension_registry import DimensionRegistry


@pytest.fixture
def analyzer():
    """Create LexicalAnalyzer instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return LexicalAnalyzer()


@pytest.fixture
def text_high_diversity():
    """Text with high lexical diversity (human pattern)."""
    return """# Introduction

Writing demonstrates remarkable versatility through varied vocabulary selection.
Authors employ distinctive terminology throughout compositions, exhibiting linguistic
richness. Creative expression flourishes when utilizing diverse lexical choices,
enhancing readability and engagement significantly."""


@pytest.fixture
def text_low_diversity():
    """Text with low lexical diversity (AI pattern)."""
    return """# Overview

The system is important. The system provides value. The system offers benefits.
The system demonstrates quality. The system ensures reliability. The system
maintains consistency. The system supports functionality. The system enables
performance. The system achieves results."""


@pytest.fixture
def text_with_code():
    """Text with code blocks that should be excluded."""
    return """# Code Example

Here's some diverse descriptive text before the code block.

```python
def function():
    return value
```

More interesting and varied vocabulary after the code section."""


class TestAnalyzeLexicalDiversity:
    """Tests for _analyze_lexical_diversity method."""

    def test_lexical_diversity_basic(self, analyzer, text_high_diversity):
        """Test basic lexical diversity analysis."""
        result = analyzer._analyze_lexical_diversity(text_high_diversity)

        assert 'unique' in result
        assert 'diversity' in result
        assert isinstance(result['unique'], int)
        assert isinstance(result['diversity'], float)
        assert result['unique'] > 0
        assert 0 <= result['diversity'] <= 1

    def test_lexical_diversity_high_variation(self, analyzer, text_high_diversity):
        """Test high diversity detection (human pattern)."""
        result = analyzer._analyze_lexical_diversity(text_high_diversity)

        # High diversity text should have TTR > 0.6
        assert result['diversity'] >= 0.6

    def test_lexical_diversity_low_variation(self, analyzer, text_low_diversity):
        """Test low diversity detection (AI pattern)."""
        result = analyzer._analyze_lexical_diversity(text_low_diversity)

        # Low diversity text should have low TTR
        assert result['diversity'] < 0.6

    def test_lexical_diversity_excludes_code(self, analyzer, text_with_code):
        """Test that code blocks are excluded from analysis."""
        result = analyzer._analyze_lexical_diversity(text_with_code)

        # Should still calculate diversity from non-code text
        assert result['unique'] > 0
        assert result['diversity'] > 0

    def test_lexical_diversity_empty_text(self, analyzer):
        """Test lexical diversity on empty text."""
        result = analyzer._analyze_lexical_diversity("")

        assert result['unique'] == 0
        assert result['diversity'] == 0

    def test_lexical_diversity_case_insensitive(self, analyzer):
        """Test that diversity is case-insensitive."""
        text = "Word word WORD Word"
        result = analyzer._analyze_lexical_diversity(text)

        # All variants of "word" should count as one unique word
        assert result['unique'] == 1
        assert result['diversity'] == 0.25  # 1 unique / 4 total


class TestAnalyzeNltkLexical:
    """Tests for _analyze_nltk_lexical method (requires NLTK)."""

    def test_nltk_lexical_basic(self, analyzer, text_high_diversity):
        """Test NLTK lexical analysis."""
        result = analyzer._analyze_nltk_lexical(text_high_diversity)

        assert 'mtld_score' in result
        assert 'stemmed_diversity' in result
        assert isinstance(result['mtld_score'], float)
        assert isinstance(result['stemmed_diversity'], float)

    def test_nltk_lexical_empty_text(self, analyzer):
        """Test NLTK analysis on empty text."""
        result = analyzer._analyze_nltk_lexical("")

        # Should return empty dict for empty text
        assert result == {}

    def test_nltk_lexical_excludes_code(self, analyzer, text_with_code):
        """Test that code blocks are excluded from NLTK analysis."""
        result = analyzer._analyze_nltk_lexical(text_with_code)

        # Should still calculate metrics from non-code text
        if result:  # If NLTK processing succeeds
            assert 'mtld_score' in result
            assert result['mtld_score'] > 0


class TestCalculateMtld:
    """Tests for _calculate_mtld method."""

    def test_mtld_long_text(self, analyzer):
        """Test MTLD calculation on long text."""
        # Create list with 100 diverse words
        words = [f"word{i}" for i in range(100)]
        result = analyzer._calculate_mtld(words)

        assert isinstance(result, float)
        assert result > 0

    def test_mtld_short_text_fallback(self, analyzer):
        """Test MTLD fallback for short text (< 50 words)."""
        words = ["word" + str(i) for i in range(20)]
        result = analyzer._calculate_mtld(words)

        # Should fallback to TTR * 100
        expected_ttr = len(set(words)) / len(words) * 100
        assert result == expected_ttr

    def test_mtld_repetitive_text(self, analyzer):
        """Test MTLD on repetitive text (low diversity)."""
        words = ["the", "system"] * 50  # Very repetitive
        result = analyzer._calculate_mtld(words)

        # Low diversity should give low MTLD score
        assert result < 50


class TestAnalyze:
    """Tests for main analyze method."""

    def test_analyze_basic(self, analyzer, text_high_diversity):
        """Test basic analyze method."""
        result = analyzer.analyze(text_high_diversity)

        assert 'lexical_diversity' in result
        assert isinstance(result['lexical_diversity'], dict)
        assert 'unique' in result['lexical_diversity']
        assert 'diversity' in result['lexical_diversity']

    def test_analyze_with_nltk(self, analyzer, text_high_diversity):
        """Test analyze includes NLTK metrics when available."""
        result = analyzer.analyze(text_high_diversity)

        lexical = result['lexical_diversity']
        assert 'mtld_score' in lexical
        assert 'stemmed_diversity' in lexical

    def test_analyze_empty_text(self, analyzer):
        """Test analyze on empty text."""
        result = analyzer.analyze("")

        assert result['lexical_diversity']['unique'] == 0
        assert result['lexical_diversity']['diversity'] == 0


class TestAnalyzeDetailed:
    """Tests for analyze_detailed method."""

    def test_analyze_detailed_basic(self, analyzer, text_high_diversity):
        """Test detailed analysis method."""
        lines = text_high_diversity.split('\n')
        result = analyzer.analyze_detailed(lines)

        assert 'lexical_diversity' in result
        assert isinstance(result['lexical_diversity'], dict)

    def test_analyze_detailed_joins_lines(self, analyzer):
        """Test that analyze_detailed joins lines properly."""
        lines = ["Word1 word2 word3.", "Word4 word5 word6."]
        result = analyzer.analyze_detailed(lines)

        # Should analyze all words from all lines
        assert result['lexical_diversity']['unique'] >= 6


class TestScore:
    """Tests for score method."""

    def test_score_high_diversity(self, analyzer):
        """Test score for high diversity (human pattern)."""
        analysis = {'diversity': 0.65}  # >= 0.60 threshold
        score, label = analyzer.score(analysis)

        assert score == 10.0
        assert label == "HIGH"

    def test_score_medium_diversity(self, analyzer):
        """Test score for medium diversity."""
        analysis = {'diversity': 0.50}  # >= 0.45 threshold
        score, label = analyzer.score(analysis)

        assert score == 7.0
        assert label == "MEDIUM"

    def test_score_low_diversity(self, analyzer):
        """Test score for low diversity."""
        analysis = {'diversity': 0.35}  # >= 0.30 threshold
        score, label = analyzer.score(analysis)

        assert score == 4.0
        assert label == "LOW"

    def test_score_very_low_diversity(self, analyzer):
        """Test score for very low diversity (AI pattern)."""
        analysis = {'diversity': 0.20}  # < 0.30 threshold
        score, label = analyzer.score(analysis)

        assert score == 2.0
        assert label == "VERY LOW"

    def test_score_missing_diversity(self, analyzer):
        """Test score with missing diversity field."""
        analysis = {}
        score, label = analyzer.score(analysis)

        # Should default to 0.0 diversity (very low)
        assert score == 2.0
        assert label == "VERY LOW"


class TestMonotonicScoring:
    """Tests for monotonic scoring migration (Story 2.4.1, AC4)."""

    def test_calculate_score_at_threshold_low(self, analyzer):
        """Test scoring at threshold low (MTLD=60)."""
        metrics = {
            'lexical_diversity': {
                'mtld_score': 60.0,  # At threshold low
                'diversity': 0.5
            }
        }
        score = analyzer.calculate_score(metrics)

        # At threshold_low=60, monotonic scoring returns 25.0
        assert score == 25.0

    def test_calculate_score_below_threshold_low(self, analyzer):
        """Test scoring below threshold low (MTLD<60, AI-like)."""
        metrics = {
            'lexical_diversity': {
                'mtld_score': 40.0,  # Below threshold (AI-like)
                'diversity': 0.3
            }
        }
        score = analyzer.calculate_score(metrics)

        # Below 60: should be fixed at 25.0
        assert score == 25.0

    def test_calculate_score_mid_range(self, analyzer):
        """Test scoring in mid-range (MTLD between 60-100)."""
        metrics = {
            'lexical_diversity': {
                'mtld_score': 80.0,  # Mid-range
                'diversity': 0.6
            }
        }
        score = analyzer.calculate_score(metrics)

        # Between 60-100: should be 25-75 (linear)
        # 80 is halfway, so score should be around 50
        assert 45.0 <= score <= 55.0

    def test_calculate_score_at_threshold_high(self, analyzer):
        """Test scoring at threshold high (MTLD=100)."""
        metrics = {
            'lexical_diversity': {
                'mtld_score': 100.0,  # At threshold high
                'diversity': 0.7
            }
        }
        score = analyzer.calculate_score(metrics)

        # At threshold_high=100, monotonic scoring returns 75.0
        assert score == 75.0

    def test_calculate_score_above_threshold_high(self, analyzer):
        """Test scoring above threshold high (MTLD>100, human-like)."""
        metrics = {
            'lexical_diversity': {
                'mtld_score': 120.0,  # Above threshold (human-like)
                'diversity': 0.75
            }
        }
        score = analyzer.calculate_score(metrics)

        # Above 100: should be 75-100 (asymptotic)
        assert 75.0 <= score <= 100.0

    def test_calculate_score_monotonic_increasing(self, analyzer):
        """Test that scoring is monotonic increasing with MTLD."""
        mtld_values = [40.0, 60.0, 80.0, 100.0, 120.0]
        scores = []

        for mtld in mtld_values:
            metrics = {
                'lexical_diversity': {
                    'mtld_score': mtld,
                    'diversity': 0.5
                }
            }
            scores.append(analyzer.calculate_score(metrics))

        # Scores should increase monotonically (or stay same for values below threshold)
        # Below threshold_low (60): all get 25.0
        # Then increases from 60 to 100 (25.0 to 75.0)
        # Then increases from 100+ (75.0 to 100.0 asymptotic)
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i+1], \
                f"Score should increase or stay same: {scores[i]} <= {scores[i+1]} (MTLD {mtld_values[i]} vs {mtld_values[i+1]})"

    def test_calculate_score_fallback_to_ttr(self, analyzer):
        """Test fallback to TTR estimation when MTLD unavailable."""
        # No mtld_score, only diversity (TTR)
        metrics = {
            'lexical_diversity': {
                'diversity': 0.5  # TTR=0.5 → estimated MTLD ≈ 70
            }
        }
        score = analyzer.calculate_score(metrics)

        # Estimated MTLD = 0.5 × 140 = 70, between thresholds (60-100)
        # Should score in mid-range (25-75)
        assert 25.0 <= score <= 75.0

    def test_calculate_score_validates_range(self, analyzer):
        """Test that all scores are in valid 0-100 range."""
        test_mtld_values = [0, 30.0, 60.0, 80.0, 100.0, 150.0]

        for mtld in test_mtld_values:
            metrics = {
                'lexical_diversity': {
                    'mtld_score': mtld,
                    'diversity': 0.5
                }
            }
            score = analyzer.calculate_score(metrics)
            assert 0.0 <= score <= 100.0, f"Score {score} for MTLD={mtld} out of range"


class TestIntegration:
    """Integration tests."""

    def test_full_analysis_pipeline(self, analyzer, text_high_diversity):
        """Test complete analysis pipeline."""
        result = analyzer.analyze(text_high_diversity)

        assert result['lexical_diversity']['diversity'] > 0.5

        # Detailed analysis
        lines = text_high_diversity.split('\n')
        detailed = analyzer.analyze_detailed(lines)

        assert detailed['lexical_diversity']['diversity'] > 0.5

    def test_comparison_high_vs_low(self, analyzer, text_high_diversity, text_low_diversity):
        """Test that analyzer distinguishes high from low diversity."""
        high_result = analyzer.analyze(text_high_diversity)
        low_result = analyzer.analyze(text_low_diversity)

        high_div = high_result['lexical_diversity']['diversity']
        low_div = low_result['lexical_diversity']['diversity']

        # High diversity text should have higher TTR
        assert high_div > low_div
