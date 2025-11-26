"""
Tests for score_normalization module (Story 2.4.1, AC7).
"""

import json
import tempfile
from pathlib import Path

import pytest

from writescore.scoring.score_normalization import ScoreNormalizer, get_normalizer, normalize_score


@pytest.fixture
def temp_stats_file():
    """Create temporary stats file for testing."""
    stats_data = {
        '_metadata': {
            'version': '1.0.0',
            'created': '2025-01-24',
            'story': '2.4.1',
            'description': 'Test statistics',
            'validation_set_size': 100
        },
        'dimensions': {
            'perplexity': {
                'mean': 45.0,
                'stdev': 12.0,
                'min': 20.0,
                'max': 80.0,
                'n_samples': 100
            },
            'burstiness': {
                'mean': 55.0,
                'stdev': 18.0,
                'min': 10.0,
                'max': 95.0,
                'n_samples': 100
            },
            'voice': {
                'mean': 50.0,
                'stdev': 15.0,
                'min': 15.0,
                'max': 90.0,
                'n_samples': 100
            },
            'zero_stdev': {
                'mean': 50.0,
                'stdev': 0.0,  # Edge case: zero variance
                'min': 50.0,
                'max': 50.0,
                'n_samples': 100
            }
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(stats_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


class TestScoreNormalizerInit:
    """Tests for ScoreNormalizer __init__."""

    def test_init_with_stats_file(self, temp_stats_file):
        """Test initialization with stats file."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        assert normalizer.enabled is True
        assert len(normalizer.stats) == 4
        assert 'perplexity' in normalizer.stats
        assert normalizer.stats['perplexity']['mean'] == 45.0

    def test_init_disabled(self):
        """Test initialization with normalization disabled."""
        normalizer = ScoreNormalizer(enabled=False)

        assert normalizer.enabled is False
        assert len(normalizer.stats) == 0

    def test_init_missing_file(self):
        """Test initialization with missing stats file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            ScoreNormalizer(stats_path=Path("/nonexistent/path.json"), enabled=True)

        assert "not found" in str(exc_info.value)

    def test_init_invalid_json(self):
        """Test initialization with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                ScoreNormalizer(stats_path=temp_path, enabled=True)

            assert "Invalid JSON" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_init_missing_dimensions_key(self):
        """Test initialization with missing 'dimensions' key."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({'_metadata': {}}, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                ScoreNormalizer(stats_path=temp_path, enabled=True)

            assert "missing 'dimensions' key" in str(exc_info.value)
        finally:
            temp_path.unlink()


class TestNormalizeScore:
    """Tests for normalize_score method."""

    def test_normalize_score_at_mean(self, temp_stats_file):
        """Test normalization at mean (should return ~50)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, score=45 -> z=0 -> normalized=50
        score = normalizer.normalize_score(45.0, 'perplexity')
        assert 49.0 <= score <= 51.0

    def test_normalize_score_above_mean(self, temp_stats_file):
        """Test normalization above mean (should return >50)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, stdev=12, score=57 (+1σ)
        # z = (57-45)/12 = 1.0
        # normalized = 50 + (1.0 * 15) = 65
        score = normalizer.normalize_score(57.0, 'perplexity')
        assert 64.0 <= score <= 66.0

    def test_normalize_score_below_mean(self, temp_stats_file):
        """Test normalization below mean (should return <50)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, stdev=12, score=33 (-1σ)
        # z = (33-45)/12 = -1.0
        # normalized = 50 + (-1.0 * 15) = 35
        score = normalizer.normalize_score(33.0, 'perplexity')
        assert 34.0 <= score <= 36.0

    def test_normalize_score_extreme_high(self, temp_stats_file):
        """Test normalization with extreme high score (should clamp to 100)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, stdev=12, score=150 (way above)
        # z = (150-45)/12 = 8.75
        # normalized = 50 + (8.75 * 15) = 181.25 -> clamped to 100
        score = normalizer.normalize_score(150.0, 'perplexity')
        assert score == 100.0

    def test_normalize_score_extreme_low(self, temp_stats_file):
        """Test normalization with extreme low score (should clamp to 0)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, stdev=12, score=-50 (way below)
        # z = (-50-45)/12 = -7.92
        # normalized = 50 + (-7.92 * 15) = -68.75 -> clamped to 0
        score = normalizer.normalize_score(-50.0, 'perplexity')
        assert score == 0.0

    def test_normalize_score_zero_stdev(self, temp_stats_file):
        """Test normalization with zero stdev (should use fallback stdev=1.0)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # zero_stdev: mean=50, stdev=0, score=55
        # Uses fallback stdev=1.0
        # z = (55-50)/1.0 = 5.0
        # normalized = 50 + (5.0 * 15) = 125 -> clamped to 100
        score = normalizer.normalize_score(55.0, 'zero_stdev')
        assert score == 100.0

    def test_normalize_score_disabled(self, temp_stats_file):
        """Test normalization when disabled (should return raw score)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=False)

        score = normalizer.normalize_score(75.0, 'perplexity')
        assert score == 75.0

    def test_normalize_score_unknown_dimension(self, temp_stats_file):
        """Test normalization with unknown dimension (should return raw score with warning)."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        score = normalizer.normalize_score(65.0, 'unknown_dimension')
        assert score == 65.0  # Returns raw score when dimension not in stats


class TestComputeDimensionStatistics:
    """Tests for compute_dimension_statistics method."""

    def test_compute_statistics_basic(self):
        """Test computing statistics from dimension scores."""
        normalizer = ScoreNormalizer(enabled=False)

        scores = {
            'perplexity': [40.0, 45.0, 50.0, 55.0, 60.0],
            'burstiness': [30.0, 40.0, 50.0, 60.0, 70.0]
        }

        stats = normalizer.compute_dimension_statistics(scores)

        assert 'perplexity' in stats
        assert 'burstiness' in stats
        assert stats['perplexity']['mean'] == 50.0
        assert stats['perplexity']['n_samples'] == 5
        assert stats['perplexity']['min'] == 40.0
        assert stats['perplexity']['max'] == 60.0
        # Stdev should be around 7.07
        assert 7.0 <= stats['perplexity']['stdev'] <= 8.0

    def test_compute_statistics_saves_file(self):
        """Test that compute_dimension_statistics saves to file."""
        normalizer = ScoreNormalizer(enabled=False)

        scores = {
            'perplexity': [40.0, 50.0, 60.0]
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            normalizer.compute_dimension_statistics(scores, output_path=temp_path)

            # Check file was created
            assert temp_path.exists()

            # Check file contents
            with open(temp_path) as f:
                data = json.load(f)

            assert 'dimensions' in data
            assert 'perplexity' in data['dimensions']
            assert data['dimensions']['perplexity']['mean'] == 50.0

        finally:
            temp_path.unlink()

    def test_compute_statistics_empty_scores(self):
        """Test computing statistics with empty score list."""
        normalizer = ScoreNormalizer(enabled=False)

        scores = {
            'perplexity': []
        }

        stats = normalizer.compute_dimension_statistics(scores)

        # Should skip dimensions with no scores
        assert 'perplexity' not in stats

    def test_compute_statistics_single_score(self):
        """Test computing statistics with single score (insufficient for stdev)."""
        normalizer = ScoreNormalizer(enabled=False)

        scores = {
            'perplexity': [50.0]
        }

        stats = normalizer.compute_dimension_statistics(scores)

        # Should skip dimensions with only 1 sample (can't compute stdev)
        assert 'perplexity' not in stats


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_normalizer_singleton(self, temp_stats_file):
        """Test that get_normalizer returns singleton."""
        # Clear singleton first
        import writescore.scoring.score_normalization as sn
        sn._default_normalizer = None

        normalizer1 = get_normalizer(enabled=True)
        normalizer2 = get_normalizer(enabled=True)

        assert normalizer1 is normalizer2  # Same instance

    def test_normalize_score_convenience(self, temp_stats_file):
        """Test module-level normalize_score function."""
        # This should work without explicitly creating a normalizer
        # Since we don't have stats in default location, it will return raw score
        score = normalize_score(75.0, 'perplexity', enabled=False)
        assert score == 75.0


class TestNormalizationIntegration:
    """Integration tests for normalization."""

    def test_normalization_preserves_ordering(self, temp_stats_file):
        """Test that normalization preserves relative ordering within dimension."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        scores_raw = [30.0, 45.0, 60.0, 75.0]
        scores_normalized = [
            normalizer.normalize_score(s, 'perplexity') for s in scores_raw
        ]

        # Normalized scores should maintain same ordering
        assert scores_normalized == sorted(scores_normalized)

    def test_normalization_equalizes_distributions(self, temp_stats_file):
        """Test that normalization brings different dimensions to similar scale."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Perplexity: mean=45, stdev=12
        # Burstiness: mean=55, stdev=18
        # Voice: mean=50, stdev=15

        # Take scores at +1σ from each dimension's mean
        perp_score = normalizer.normalize_score(45.0 + 12.0, 'perplexity')
        burst_score = normalizer.normalize_score(55.0 + 18.0, 'burstiness')
        voice_score = normalizer.normalize_score(50.0 + 15.0, 'voice')

        # All should normalize to approximately 65 (50 + 1*15)
        assert 63.0 <= perp_score <= 67.0
        assert 63.0 <= burst_score <= 67.0
        assert 63.0 <= voice_score <= 67.0

    def test_normalization_handles_different_scoring_functions(self, temp_stats_file):
        """Test that normalization works with different scoring function outputs."""
        normalizer = ScoreNormalizer(stats_path=temp_stats_file, enabled=True)

        # Simulate scores from different scoring functions
        gaussian_score = 45.0  # Gaussian (centered at mean)
        monotonic_score = 80.0  # Monotonic (often high)
        threshold_score = 25.0  # Threshold (discrete bands)

        # All should normalize to reasonable ranges
        norm_gaussian = normalizer.normalize_score(gaussian_score, 'perplexity')
        norm_monotonic = normalizer.normalize_score(monotonic_score, 'burstiness')
        norm_threshold = normalizer.normalize_score(threshold_score, 'voice')

        # Check all are in valid range
        assert 0 <= norm_gaussian <= 100
        assert 0 <= norm_monotonic <= 100
        assert 0 <= norm_threshold <= 100
