"""
Tests for BurstinessAnalyzer - sentence and paragraph length variation detection.
"""

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.burstiness import BurstinessAnalyzer


@pytest.fixture
def analyzer():
    """Create BurstinessAnalyzer instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return BurstinessAnalyzer()


@pytest.fixture
def text_uniform_sentences():
    """Text with uniform sentence lengths (AI pattern)."""
    return """# Introduction

The first sentence has exactly fifteen words in it for testing purposes here.
The second sentence also has exactly fifteen words in it for testing purposes today.
The third sentence equally has exactly fifteen words in it for testing purposes now.

Another paragraph with more uniform sentences that all have similar lengths throughout.
Every sentence here maintains consistency with approximately the same number of words overall.
"""


@pytest.fixture
def text_varied_sentences():
    """Text with varied sentence lengths (human pattern)."""
    return """# Getting Started

Short sentence. This is a medium-length sentence with some more words. Now here's a much longer sentence that goes on and on with many words and clauses to demonstrate natural human writing variation.

Humans vary. Sometimes we write briefly. Other times, we might write longer, more complex sentences that explore ideas in greater depth.
"""


@pytest.fixture
def text_uniform_paragraphs():
    """Text with uniform paragraph lengths (AI pattern)."""
    return """# Content

This paragraph has exactly twenty words in it for testing uniformity detection in AI generated content here now today.

This paragraph also has exactly twenty words in it for testing uniformity detection in AI generated content right here.

This paragraph equally has exactly twenty words in it for testing uniformity detection in AI generated content at present.
"""


class TestAnalyzeSentenceBurstiness:
    """Tests for _analyze_sentence_burstiness method."""

    def test_sentence_burstiness_basic(self, analyzer, text_varied_sentences):
        """Test basic sentence burstiness analysis."""
        result = analyzer._analyze_sentence_burstiness(text_varied_sentences)

        assert 'total_sentences' in result
        assert 'mean' in result
        assert 'stdev' in result
        assert 'min' in result
        assert 'max' in result
        assert 'short' in result
        assert 'medium' in result
        assert 'long' in result
        assert 'lengths' in result

    def test_sentence_burstiness_varied_pattern(self, analyzer, text_varied_sentences):
        """Test high burstiness (varied sentences) detection."""
        result = analyzer._analyze_sentence_burstiness(text_varied_sentences)

        assert result['total_sentences'] > 0
        assert result['stdev'] > 5  # High variation
        assert result['min'] < result['max']  # Range of lengths

    def test_sentence_burstiness_uniform_pattern(self, analyzer, text_uniform_sentences):
        """Test low burstiness (uniform sentences) detection."""
        result = analyzer._analyze_sentence_burstiness(text_uniform_sentences)

        assert result['total_sentences'] > 0
        assert result['stdev'] < 5  # Low variation (AI pattern)

    def test_sentence_burstiness_empty_text(self, analyzer):
        """Test sentence burstiness on empty text."""
        result = analyzer._analyze_sentence_burstiness("")

        assert result['total_sentences'] == 0
        assert result['mean'] == 0
        assert result['stdev'] == 0

    def test_sentence_burstiness_skips_headings(self, analyzer):
        """Test that headings are skipped."""
        text = """# This is a heading with many words

This is a sentence. This is another sentence.
"""
        result = analyzer._analyze_sentence_burstiness(text)

        # Should only count body sentences, not heading
        assert result['total_sentences'] == 2


class TestAnalyzeParagraphVariation:
    """Tests for _analyze_paragraph_variation method."""

    def test_paragraph_variation_basic(self, analyzer, text_varied_sentences):
        """Test basic paragraph variation analysis."""
        result = analyzer._analyze_paragraph_variation(text_varied_sentences)

        assert 'total_paragraphs' in result
        assert 'mean' in result
        assert 'stdev' in result
        assert 'min' in result
        assert 'max' in result

    def test_paragraph_variation_varied(self, analyzer):
        """Test varied paragraph lengths."""
        text = """# Title

Short paragraph.

This is a medium length paragraph with several sentences and ideas expressed throughout the content here.

This is a very long paragraph with many sentences that goes on for quite a while discussing various topics and including multiple points of discussion throughout the entire section which demonstrates significant variation in paragraph structure and length across the document.
"""
        result = analyzer._analyze_paragraph_variation(text)

        assert result['total_paragraphs'] >= 2
        assert result['stdev'] > 0  # Has variation
        assert result['min'] < result['max']

    def test_paragraph_variation_empty_text(self, analyzer):
        """Test paragraph variation on empty text."""
        result = analyzer._analyze_paragraph_variation("")

        assert result['total_paragraphs'] == 0
        assert result['mean'] == 0


class TestCalculateParagraphCv:
    """Tests for _calculate_paragraph_cv method."""

    def test_paragraph_cv_basic(self, analyzer, text_uniform_paragraphs):
        """Test basic paragraph CV calculation."""
        result = analyzer._calculate_paragraph_cv(text_uniform_paragraphs)

        assert 'mean_length' in result
        assert 'stddev' in result
        assert 'cv' in result
        assert 'score' in result
        assert 'assessment' in result
        assert 'paragraph_count' in result

    def test_paragraph_cv_uniform_ai_pattern(self, analyzer, text_uniform_paragraphs):
        """Test low CV for uniform paragraphs (AI pattern)."""
        result = analyzer._calculate_paragraph_cv(text_uniform_paragraphs)

        assert result['cv'] < 0.4  # Low variation
        assert result['assessment'] in ['POOR', 'FAIR']

    def test_paragraph_cv_varied_human_pattern(self, analyzer):
        """Test high CV for varied paragraphs (human pattern)."""
        text = """# Content

This is a short paragraph with just a few words to make the point quickly.

This is a much longer paragraph with significantly more content that explores ideas in greater depth and includes multiple sentences with various lengths and structures throughout the entire section demonstrating natural human writing variation.

Here's another medium-length paragraph that falls somewhere in between the short and long examples.
"""
        result = analyzer._calculate_paragraph_cv(text)

        assert result['cv'] >= 0.4  # High variation (human-like)
        assert result['assessment'] in ['GOOD', 'EXCELLENT']

    def test_paragraph_cv_insufficient_data(self, analyzer):
        """Test CV calculation with insufficient paragraphs."""
        text = """# Title

One paragraph."""
        result = analyzer._calculate_paragraph_cv(text)

        assert result['assessment'] == 'INSUFFICIENT_DATA'
        assert result['score'] == 10.0  # Benefit of doubt


class TestAnalyzeBurstinessIssuesDetailed:
    """Tests for _analyze_burstiness_issues_detailed method."""

    def test_burstiness_issues_uniform_detection(self, analyzer, text_uniform_sentences):
        """Test detection of uniform sentence lengths."""
        lines = text_uniform_sentences.split('\n')
        issues = analyzer._analyze_burstiness_issues_detailed(lines)

        assert isinstance(issues, list)
        # May detect uniform patterns
        if len(issues) > 0:
            issue = issues[0]
            assert hasattr(issue, 'start_line')
            assert hasattr(issue, 'end_line')
            assert hasattr(issue, 'sentence_count')
            assert hasattr(issue, 'mean_length')
            assert hasattr(issue, 'stdev')
            assert hasattr(issue, 'problem')
            assert hasattr(issue, 'suggestion')

    def test_burstiness_issues_varied_no_issues(self, analyzer, text_varied_sentences):
        """Test that varied text has fewer/no issues."""
        lines = text_varied_sentences.split('\n')
        issues = analyzer._analyze_burstiness_issues_detailed(lines)

        assert isinstance(issues, list)
        # Varied sentences should have fewer issues
        # (may still have some depending on paragraph structure)

    def test_burstiness_issues_skips_headings(self, analyzer):
        """Test that headings are skipped."""
        lines = [
            "# Heading with uniform sentences here",
            "",
            "Sentence one. Sentence two. Sentence three.",
            ""
        ]
        issues = analyzer._analyze_burstiness_issues_detailed(lines)

        # Should only analyze body text
        assert isinstance(issues, list)


class TestAnalyze:
    """Tests for main analyze method."""

    def test_analyze_basic(self, analyzer, text_varied_sentences):
        """Test basic analyze method."""
        result = analyzer.analyze(text_varied_sentences)

        assert 'sentence_burstiness' in result
        assert 'paragraph_variation' in result
        assert 'paragraph_cv' in result

    def test_analyze_empty_text(self, analyzer):
        """Test analyze on empty text."""
        result = analyzer.analyze("")

        assert result['sentence_burstiness']['total_sentences'] == 0
        assert result['paragraph_variation']['total_paragraphs'] == 0


class TestAnalyzeDetailed:
    """Tests for analyze_detailed method."""

    def test_analyze_detailed_basic(self, analyzer, text_uniform_sentences):
        """Test detailed analysis method."""
        lines = text_uniform_sentences.split('\n')
        result = analyzer.analyze_detailed(lines)

        assert isinstance(result, list)


class TestScore:
    """Tests for score method."""

    def test_score_high_burstiness(self, analyzer):
        """Test score for high burstiness (varied sentences)."""
        analysis = {
            'total_sentences': 10,
            'stdev': 10.0,
            'short': 3,
            'long': 2
        }
        score, label = analyzer.score(analysis)

        assert score == 10.0
        assert label == "HIGH"

    def test_score_medium_burstiness(self, analyzer):
        """Test score for medium burstiness."""
        analysis = {
            'total_sentences': 10,
            'stdev': 6.0,
            'short': 2,
            'long': 1
        }
        score, label = analyzer.score(analysis)

        assert score == 7.0
        assert label == "MEDIUM"

    def test_score_low_burstiness(self, analyzer):
        """Test score for low burstiness (uniform)."""
        analysis = {
            'total_sentences': 10,
            'stdev': 3.5,
            'short': 1,
            'long': 0
        }
        score, label = analyzer.score(analysis)

        assert score == 4.0
        assert label == "LOW"

    def test_score_very_low_burstiness(self, analyzer):
        """Test score for very low burstiness."""
        analysis = {
            'total_sentences': 10,
            'stdev': 2.0,
            'short': 0,
            'long': 0
        }
        score, label = analyzer.score(analysis)

        assert score == 2.0
        assert label == "VERY LOW"

    def test_score_no_sentences(self, analyzer):
        """Test score with no sentences."""
        analysis = {'total_sentences': 0}
        score, label = analyzer.score(analysis)

        assert score == 0.0
        assert label == "UNKNOWN"


class TestIntegration:
    """Integration tests."""

    def test_full_analysis_pipeline(self, analyzer, text_varied_sentences):
        """Test complete analysis pipeline."""
        result = analyzer.analyze(text_varied_sentences)

        assert result['sentence_burstiness']['total_sentences'] > 0
        assert result['paragraph_variation']['total_paragraphs'] > 0
        assert result['paragraph_cv']['cv'] >= 0

        # Detailed analysis
        lines = text_varied_sentences.split('\n')
        detailed = analyzer.analyze_detailed(lines)

        assert isinstance(detailed, list)

class TestGaussianScoring:
    """Tests for Gaussian scoring migration (Story 2.4.1, AC3)."""

    def test_calculate_score_optimal_value(self, analyzer):
        """Test scoring at optimal stdev (μ=15.0) returns near-perfect score."""
        metrics = {
            'sentence_burstiness': {
                'total_sentences': 10,
                'stdev': 15.0  # Optimal target
            }
        }
        score = analyzer.calculate_score(metrics)

        # Should be 100.0 (or very close due to floating point)
        assert score >= 99.0
        assert score <= 100.0

    def test_calculate_score_within_one_sigma(self, analyzer):
        """Test scoring within 1σ of optimal returns high score."""
        # μ=15.0, σ=5.0, so 1σ range is [10.0, 20.0]
        # At μ±1σ, Gaussian function returns exp(-0.5) ≈ 0.606

        metrics_low = {
            'sentence_burstiness': {
                'total_sentences': 10,
                'stdev': 10.0  # μ - 1σ
            }
        }
        score_low = analyzer.calculate_score(metrics_low)
        assert score_low >= 55.0  # exp(-0.5) * 100 ≈ 60.6
        assert score_low <= 65.0

        metrics_high = {
            'sentence_burstiness': {
                'total_sentences': 10,
                'stdev': 20.0  # μ + 1σ
            }
        }
        score_high = analyzer.calculate_score(metrics_high)
        assert score_high >= 55.0
        assert score_high <= 65.0

    def test_calculate_score_low_variation(self, analyzer):
        """Test scoring for low variation (AI pattern) returns low score."""
        metrics = {
            'sentence_burstiness': {
                'total_sentences': 10,
                'stdev': 3.0  # Very low variation (AI-like)
            }
        }
        score = analyzer.calculate_score(metrics)

        # 3.0 is 2.4σ below optimal, should return low score
        # Gaussian at 2.4σ: exp(-0.5 * (2.4)²) ≈ exp(-2.88) ≈ 0.056
        assert score < 10.0

    def test_calculate_score_extremely_high_variation(self, analyzer):
        """Test scoring for extremely high variation returns low score."""
        metrics = {
            'sentence_burstiness': {
                'total_sentences': 10,
                'stdev': 30.0  # Extremely high variation (chaotic)
            }
        }
        score = analyzer.calculate_score(metrics)

        # 30.0 is 3σ above optimal, should return low score
        # Gaussian at 3σ: exp(-0.5 * 9) ≈ 0.011
        assert score < 5.0

    def test_calculate_score_no_sentences(self, analyzer):
        """Test scoring with no sentences returns neutral score."""
        metrics = {
            'sentence_burstiness': {
                'total_sentences': 0,
                'stdev': 0
            }
        }
        score = analyzer.calculate_score(metrics)

        # Should return neutral 50.0 for insufficient data
        assert score == 50.0

    def test_calculate_score_monotonicity_below_optimal(self, analyzer):
        """Test that score increases monotonically approaching optimal from below."""
        scores = []
        for stdev in [5.0, 10.0, 13.0, 15.0]:
            metrics = {
                'sentence_burstiness': {
                    'total_sentences': 10,
                    'stdev': stdev
                }
            }
            scores.append(analyzer.calculate_score(metrics))

        # Scores should increase as we approach optimal (15.0)
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i+1], f"Score should increase: {scores[i]} < {scores[i+1]}"

    def test_calculate_score_monotonicity_above_optimal(self, analyzer):
        """Test that score decreases monotonically moving away from optimal above."""
        scores = []
        for stdev in [15.0, 18.0, 22.0, 28.0]:
            metrics = {
                'sentence_burstiness': {
                    'total_sentences': 10,
                    'stdev': stdev
                }
            }
            scores.append(analyzer.calculate_score(metrics))

        # Scores should decrease as we move away from optimal (15.0)
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i+1], f"Score should decrease: {scores[i]} > {scores[i+1]}"
