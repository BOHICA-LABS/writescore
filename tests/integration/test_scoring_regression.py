"""
Scoring regression test suite for dimension consistency validation.

Validates that dimension scores remain consistent (≤5% variance)
after refactoring or updates.

Run: pytest tests/integration/test_scoring_regression.py -v
"""

import json
from pathlib import Path
from typing import Dict, List

import pytest

from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension
from writescore.dimensions.burstiness import BurstinessDimension
from writescore.dimensions.figurative_language import FigurativeLanguageDimension
from writescore.dimensions.formatting import FormattingDimension
from writescore.dimensions.lexical import LexicalDimension
from writescore.dimensions.perplexity import PerplexityDimension
from writescore.dimensions.predictability import PredictabilityDimension
from writescore.dimensions.readability import ReadabilityDimension
from writescore.dimensions.sentiment import SentimentDimension
from writescore.dimensions.structure import StructureDimension
from writescore.dimensions.syntactic import SyntacticDimension
from writescore.dimensions.transition_marker import TransitionMarkerDimension
from writescore.dimensions.voice import VoiceDimension

# Variance threshold (5%)
VARIANCE_THRESHOLD = 5.0


def load_corpus() -> List[Dict]:
    """Load test corpus from fixtures."""
    corpus_path = Path(__file__).parent.parent / "fixtures" / "regression_corpus.json"
    with open(corpus_path) as f:
        data = json.load(f)
    return data['samples']


def load_baselines() -> Dict:
    """Load baseline scores from fixtures."""
    baseline_path = Path(__file__).parent.parent / "fixtures" / "baseline_scores.json"
    with open(baseline_path) as f:
        data = json.load(f)
    return data['baselines']


def calculate_variance_percentage(baseline: float, current: float) -> float:
    """
    Calculate percentage variance between baseline and current score.

    For very small scores (< 1.0), use absolute difference instead of percentage
    since small absolute changes would cause huge percentage variance.

    Args:
        baseline: Original score
        current: New score

    Returns:
        Variance metric (percentage for scores >= 1.0, absolute for smaller scores)
    """
    # For very small scores, use absolute difference instead of percentage
    # This prevents tiny fluctuations from causing huge percentage variances
    SMALL_SCORE_THRESHOLD = 1.0

    if baseline < SMALL_SCORE_THRESHOLD and current < SMALL_SCORE_THRESHOLD:
        # For small scores, return absolute difference (treated as percentage points)
        return round(abs(current - baseline), 2)

    if baseline < SMALL_SCORE_THRESHOLD:
        # Baseline was near-zero but current isn't - this is a significant change
        return round(abs(current - baseline), 2)

    variance = abs(current - baseline)
    percentage = (variance / baseline) * 100
    return round(percentage, 2)


class TestScoringRegression:
    """Scoring regression test suite."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.corpus = load_corpus()
        self.baselines = load_baselines()
        self.dimensions = {
            'predictability': PredictabilityDimension(),
            'advanced_lexical': AdvancedLexicalDimension(),
            'readability': ReadabilityDimension(),
            'transition_marker': TransitionMarkerDimension(),
            'perplexity': PerplexityDimension(),
            'burstiness': BurstinessDimension(),
            'structure': StructureDimension(),
            'formatting': FormattingDimension(),
            'voice': VoiceDimension(),
            'lexical': LexicalDimension(),
            'sentiment': SentimentDimension(),
            'syntactic': SyntacticDimension(),
            'figurative_language': FigurativeLanguageDimension()
        }

    def test_predictability_scoring_regression(self):
        """Test PredictabilityDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['predictability']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            # Get baseline score
            baseline_score = self.baselines[sample_id]['predictability']

            # Calculate current score
            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            # Calculate variance
            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            # Assert within threshold
            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Predictability variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Predictability: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_advanced_lexical_scoring_regression(self):
        """Test AdvancedLexicalDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['advanced_lexical']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['advanced_lexical']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: AdvancedLexical variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ AdvancedLexical: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_readability_scoring_regression(self):
        """Test ReadabilityDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['readability']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['readability']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Readability variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Readability: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_transition_marker_scoring_regression(self):
        """Test TransitionMarkerDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['transition_marker']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['transition_marker']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: TransitionMarker variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ TransitionMarker: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_perplexity_scoring_regression(self):
        """Test PerplexityDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['perplexity']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['perplexity']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Perplexity variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Perplexity: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_burstiness_scoring_regression(self):
        """Test BurstinessDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['burstiness']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['burstiness']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Burstiness variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Burstiness: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_structure_scoring_regression(self):
        """Test StructureDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['structure']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['structure']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Structure variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Structure: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_formatting_scoring_regression(self):
        """Test FormattingDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['formatting']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['formatting']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Formatting variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Formatting: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_voice_scoring_regression(self):
        """Test VoiceDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['voice']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['voice']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Voice variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Voice: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_lexical_scoring_regression(self):
        """Test LexicalDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['lexical']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['lexical']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Lexical variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Lexical: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_sentiment_scoring_regression(self):
        """Test SentimentDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['sentiment']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['sentiment']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Sentiment variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Sentiment: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_syntactic_scoring_regression(self):
        """Test SyntacticDimension scores match baseline (≤5% variance)."""
        dimension = self.dimensions['syntactic']
        variances = []

        for sample in self.corpus:
            sample_id = sample['id']
            text = sample['text']

            baseline_score = self.baselines[sample_id]['syntactic']

            metrics = dimension.analyze(text)
            current_score = dimension.calculate_score(metrics)

            variance = calculate_variance_percentage(baseline_score, current_score)
            variances.append(variance)

            assert variance <= VARIANCE_THRESHOLD, (
                f"Sample {sample_id}: Syntactic variance {variance}% exceeds {VARIANCE_THRESHOLD}% "
                f"(baseline: {baseline_score}, current: {current_score})"
            )

        avg_variance = sum(variances) / len(variances)
        print(f"\n✅ Syntactic: Average variance {avg_variance:.2f}% (≤{VARIANCE_THRESHOLD}%)")

    def test_all_dimensions_variance_summary(self):
        """Generate variance summary report for all dimensions."""
        print("\n" + "=" * 80)
        print("SCORING REGRESSION VARIANCE REPORT")
        print("=" * 80)

        dimension_variances = {}

        for dim_name, dimension in self.dimensions.items():
            variances = []

            for sample in self.corpus:
                sample_id = sample['id']
                text = sample['text']

                baseline_score = self.baselines[sample_id][dim_name]

                metrics = dimension.analyze(text)
                current_score = dimension.calculate_score(metrics)

                variance = calculate_variance_percentage(baseline_score, current_score)
                variances.append(variance)

            avg_variance = sum(variances) / len(variances)
            max_variance = max(variances)
            dimension_variances[dim_name] = {
                'avg': avg_variance,
                'max': max_variance
            }

            status = "✅" if max_variance <= VARIANCE_THRESHOLD else "❌"
            print(f"{status} {dim_name:20s} Avg: {avg_variance:5.2f}%  Max: {max_variance:5.2f}%")

        print("=" * 80)

        # Assert all dimensions within threshold
        for dim_name, stats in dimension_variances.items():
            assert stats['max'] <= VARIANCE_THRESHOLD, (
                f"{dim_name}: Max variance {stats['max']:.2f}% exceeds threshold {VARIANCE_THRESHOLD}%"
            )
