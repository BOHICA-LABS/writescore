"""
Tests for history/tracker.py - score history tracking.

Tests cover:
- HistoricalScore dataclass creation
- ScoreHistory dataclass creation and operations
- add_score() method
- get_trend() method with various scenarios
"""

import pytest

from writescore.history.tracker import HistoricalScore, ScoreHistory
from writescore.scoring.dual_score import DualScore


@pytest.fixture
def sample_dual_score():
    """Create a sample DualScore object for testing."""
    return DualScore(
        detection_risk=35.0,
        quality_score=72.0,
        detection_interpretation="MODERATE",
        quality_interpretation="GOOD",
        detection_target=25.0,
        quality_target=80.0,
        detection_gap=10.0,
        quality_gap=8.0,
        categories=[],
        improvements=[],
        path_to_target=[],
        estimated_effort="MODERATE",
        timestamp="2024-01-15T10:30:00",
        file_path="/path/to/test.md",
        total_words=500,
    )


@pytest.fixture
def sample_dual_score_improved():
    """Create an improved version of the sample score."""
    return DualScore(
        detection_risk=28.0,  # Decreased by 7
        quality_score=78.0,  # Increased by 6
        detection_interpretation="LOW",
        quality_interpretation="GOOD",
        detection_target=25.0,
        quality_target=80.0,
        detection_gap=3.0,
        quality_gap=2.0,
        categories=[],
        improvements=[],
        path_to_target=[],
        estimated_effort="LIGHT",
        timestamp="2024-01-15T11:30:00",
        file_path="/path/to/test.md",
        total_words=520,
    )


@pytest.fixture
def sample_dual_score_worsened():
    """Create a worsened version of the sample score."""
    return DualScore(
        detection_risk=42.0,  # Increased by 7
        quality_score=65.0,  # Decreased by 7
        detection_interpretation="HIGH",
        quality_interpretation="FAIR",
        detection_target=25.0,
        quality_target=80.0,
        detection_gap=17.0,
        quality_gap=15.0,
        categories=[],
        improvements=[],
        path_to_target=[],
        estimated_effort="SUBSTANTIAL",
        timestamp="2024-01-15T11:30:00",
        file_path="/path/to/test.md",
        total_words=480,
    )


# ============================================================================
# HistoricalScore Tests
# ============================================================================


class TestHistoricalScore:
    """Tests for HistoricalScore dataclass."""

    def test_historical_score_creation(self):
        """Test creating a HistoricalScore."""
        score = HistoricalScore(
            timestamp="2024-01-15T10:30:00",
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            total_words=500,
        )

        assert score.timestamp == "2024-01-15T10:30:00"
        assert score.detection_risk == 35.0
        assert score.quality_score == 72.0
        assert score.detection_interpretation == "MODERATE"
        assert score.quality_interpretation == "GOOD"
        assert score.total_words == 500
        assert score.notes == ""  # Default

    def test_historical_score_with_notes(self):
        """Test creating a HistoricalScore with notes."""
        score = HistoricalScore(
            timestamp="2024-01-15T10:30:00",
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            total_words=500,
            notes="After first revision",
        )

        assert score.notes == "After first revision"


# ============================================================================
# ScoreHistory Tests
# ============================================================================


class TestScoreHistoryInitialization:
    """Tests for ScoreHistory initialization."""

    def test_score_history_creation(self):
        """Test creating a ScoreHistory."""
        history = ScoreHistory(file_path="/path/to/test.md")

        assert history.file_path == "/path/to/test.md"
        assert history.scores == []

    def test_score_history_with_existing_scores(self):
        """Test creating a ScoreHistory with initial scores."""
        score1 = HistoricalScore(
            timestamp="2024-01-15T10:30:00",
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            total_words=500,
        )

        history = ScoreHistory(file_path="/path/to/test.md", scores=[score1])

        assert len(history.scores) == 1
        assert history.scores[0] == score1


# ============================================================================
# add_score() Tests
# ============================================================================


class TestAddScore:
    """Tests for ScoreHistory.add_score() method."""

    def test_add_score_basic(self, sample_dual_score):
        """Test adding a score to history."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        assert len(history.scores) == 1
        assert history.scores[0].timestamp == "2024-01-15T10:30:00"
        assert history.scores[0].detection_risk == 35.0
        assert history.scores[0].quality_score == 72.0
        assert history.scores[0].detection_interpretation == "MODERATE"
        assert history.scores[0].quality_interpretation == "GOOD"
        assert history.scores[0].total_words == 500
        assert history.scores[0].notes == ""

    def test_add_score_with_notes(self, sample_dual_score):
        """Test adding a score with notes."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score, notes="Initial version")

        assert len(history.scores) == 1
        assert history.scores[0].notes == "Initial version"

    def test_add_multiple_scores(self, sample_dual_score, sample_dual_score_improved):
        """Test adding multiple scores to history."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score, notes="Version 1")
        history.add_score(sample_dual_score_improved, notes="Version 2")

        assert len(history.scores) == 2
        assert history.scores[0].notes == "Version 1"
        assert history.scores[1].notes == "Version 2"
        assert history.scores[0].detection_risk == 35.0
        assert history.scores[1].detection_risk == 28.0

    def test_add_score_preserves_order(self, sample_dual_score):
        """Test that scores are added in order."""
        history = ScoreHistory(file_path="/path/to/test.md")

        for i in range(5):
            score = DualScore(
                detection_risk=35.0 - i,
                quality_score=72.0 + i,
                detection_interpretation="MODERATE",
                quality_interpretation="GOOD",
                detection_target=25.0,
                quality_target=80.0,
                detection_gap=10.0,
                quality_gap=8.0,
                categories=[],
                improvements=[],
                path_to_target=[],
                estimated_effort="MODERATE",
                timestamp=f"2024-01-15T10:{30+i}:00",
                file_path="/path/to/test.md",
                total_words=500 + i,
            )
            history.add_score(score)

        assert len(history.scores) == 5
        for i in range(5):
            assert history.scores[i].detection_risk == 35.0 - i
            assert history.scores[i].quality_score == 72.0 + i


# ============================================================================
# get_trend() Tests
# ============================================================================


class TestGetTrend:
    """Tests for ScoreHistory.get_trend() method."""

    def test_get_trend_no_scores(self):
        """Test trend with no scores."""
        history = ScoreHistory(file_path="/path/to/test.md")
        trend = history.get_trend()

        assert trend["detection"] == "N/A"
        assert trend["quality"] == "N/A"

    def test_get_trend_single_score(self, sample_dual_score):
        """Test trend with single score."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)
        trend = history.get_trend()

        assert trend["detection"] == "N/A"
        assert trend["quality"] == "N/A"

    def test_get_trend_detection_improving(self, sample_dual_score, sample_dual_score_improved):
        """Test trend when detection is improving (risk decreasing)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)
        history.add_score(sample_dual_score_improved)
        trend = history.get_trend()

        # Detection decreased by 7 (35 -> 28), so improving
        assert trend["detection"] == "IMPROVING"
        assert trend["detection_change"] == -7.0

    def test_get_trend_detection_worsening(self, sample_dual_score, sample_dual_score_worsened):
        """Test trend when detection is worsening (risk increasing)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)
        history.add_score(sample_dual_score_worsened)
        trend = history.get_trend()

        # Detection increased by 7 (35 -> 42), so worsening
        assert trend["detection"] == "WORSENING"
        assert trend["detection_change"] == 7.0

    def test_get_trend_detection_stable(self, sample_dual_score):
        """Test trend when detection is stable (small change)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        # Small change (within ±1)
        score_stable = DualScore(
            detection_risk=35.5,  # Changed by 0.5
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=10.5,
            quality_gap=8.0,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_stable)
        trend = history.get_trend()

        assert trend["detection"] == "STABLE"
        assert trend["detection_change"] == 0.5

    def test_get_trend_quality_improving(self, sample_dual_score, sample_dual_score_improved):
        """Test trend when quality is improving (score increasing)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)
        history.add_score(sample_dual_score_improved)
        trend = history.get_trend()

        # Quality increased by 6 (72 -> 78), so improving
        assert trend["quality"] == "IMPROVING"
        assert trend["quality_change"] == 6.0

    def test_get_trend_quality_declining(self, sample_dual_score, sample_dual_score_worsened):
        """Test trend when quality is declining (score decreasing)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)
        history.add_score(sample_dual_score_worsened)
        trend = history.get_trend()

        # Quality decreased by 7 (72 -> 65), so declining
        assert trend["quality"] == "DECLINING"
        assert trend["quality_change"] == -7.0

    def test_get_trend_quality_stable(self, sample_dual_score):
        """Test trend when quality is stable (small change)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        # Small change (within ±1)
        score_stable = DualScore(
            detection_risk=35.0,
            quality_score=72.8,  # Changed by 0.8
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=10.0,
            quality_gap=7.2,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_stable)
        trend = history.get_trend()

        assert trend["quality"] == "STABLE"
        assert trend["quality_change"] == 0.8

    def test_get_trend_boundary_improving_detection(self, sample_dual_score):
        """Test trend at boundary for improving detection (exactly -1.0)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        score_boundary = DualScore(
            detection_risk=34.0,  # Exactly -1.0 change
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=9.0,
            quality_gap=8.0,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_boundary)
        trend = history.get_trend()

        # Change of -1.0 should be STABLE (threshold is > 1)
        assert trend["detection"] == "STABLE"
        assert trend["detection_change"] == -1.0

    def test_get_trend_boundary_worsening_detection(self, sample_dual_score):
        """Test trend at boundary for worsening detection (exactly +1.0)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        score_boundary = DualScore(
            detection_risk=36.0,  # Exactly +1.0 change
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=11.0,
            quality_gap=8.0,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_boundary)
        trend = history.get_trend()

        # Change of +1.0 should be STABLE (threshold is > 1)
        assert trend["detection"] == "STABLE"
        assert trend["detection_change"] == 1.0

    def test_get_trend_boundary_improving_quality(self, sample_dual_score):
        """Test trend at boundary for improving quality (exactly +1.0)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        score_boundary = DualScore(
            detection_risk=35.0,
            quality_score=73.0,  # Exactly +1.0 change
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=10.0,
            quality_gap=7.0,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_boundary)
        trend = history.get_trend()

        # Change of +1.0 should be STABLE (threshold is > 1)
        assert trend["quality"] == "STABLE"
        assert trend["quality_change"] == 1.0

    def test_get_trend_boundary_declining_quality(self, sample_dual_score):
        """Test trend at boundary for declining quality (exactly -1.0)."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        score_boundary = DualScore(
            detection_risk=35.0,
            quality_score=71.0,  # Exactly -1.0 change
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=10.0,
            quality_gap=9.0,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_boundary)
        trend = history.get_trend()

        # Change of -1.0 should be STABLE (threshold is < -1)
        assert trend["quality"] == "STABLE"
        assert trend["quality_change"] == -1.0

    def test_get_trend_multiple_scores_uses_last_two(self, sample_dual_score):
        """Test that trend only uses last two scores."""
        history = ScoreHistory(file_path="/path/to/test.md")

        # Add 5 scores
        for i in range(5):
            score = DualScore(
                detection_risk=40.0 - i * 2,
                quality_score=70.0 + i * 2,
                detection_interpretation="MODERATE",
                quality_interpretation="GOOD",
                detection_target=25.0,
                quality_target=80.0,
                detection_gap=15.0 - i * 2,
                quality_gap=10.0 - i * 2,
                categories=[],
                improvements=[],
                path_to_target=[],
                estimated_effort="MODERATE",
                timestamp=f"2024-01-15T10:{30+i}:00",
                file_path="/path/to/test.md",
                total_words=500 + i * 10,
            )
            history.add_score(score)

        trend = history.get_trend()

        # Should compare last two: 34 -> 32 (detection) and 76 -> 78 (quality)
        assert trend["detection_change"] == -2.0
        assert trend["quality_change"] == 2.0

    def test_get_trend_rounding(self, sample_dual_score):
        """Test that trend changes are rounded to 1 decimal place."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_dual_score)

        score_precise = DualScore(
            detection_risk=34.567,  # Change of -0.433
            quality_score=72.123,  # Change of +0.123
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            detection_target=25.0,
            quality_target=80.0,
            detection_gap=9.567,
            quality_gap=7.877,
            categories=[],
            improvements=[],
            path_to_target=[],
            estimated_effort="MODERATE",
            timestamp="2024-01-15T11:30:00",
            file_path="/path/to/test.md",
            total_words=500,
        )
        history.add_score(score_precise)
        trend = history.get_trend()

        # Should be rounded to 1 decimal place
        assert trend["detection_change"] == -0.4
        assert trend["quality_change"] == 0.1


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_history_workflow(self, sample_dual_score, sample_dual_score_improved):
        """Test complete workflow of creating history and tracking progress."""
        # Create history
        history = ScoreHistory(file_path="/path/to/document.md")

        # Initial score
        history.add_score(sample_dual_score, notes="Initial draft")
        assert len(history.scores) == 1

        # Check trend with only one score
        trend = history.get_trend()
        assert trend["detection"] == "N/A"
        assert trend["quality"] == "N/A"

        # Add improved score
        history.add_score(sample_dual_score_improved, notes="After humanization")
        assert len(history.scores) == 2

        # Check trend showing improvement
        trend = history.get_trend()
        assert trend["detection"] == "IMPROVING"
        assert trend["quality"] == "IMPROVING"
        assert trend["detection_change"] == -7.0
        assert trend["quality_change"] == 6.0

    def test_tracking_multiple_revisions(self):
        """Test tracking multiple revisions over time."""
        history = ScoreHistory(file_path="/path/to/document.md")

        # Simulate 5 revisions with gradual improvement
        base_detection = 50.0
        base_quality = 60.0

        for i in range(5):
            score = DualScore(
                detection_risk=base_detection - i * 3,
                quality_score=base_quality + i * 4,
                detection_interpretation="MODERATE",
                quality_interpretation="GOOD",
                detection_target=25.0,
                quality_target=80.0,
                detection_gap=base_detection - i * 3 - 25.0,
                quality_gap=80.0 - (base_quality + i * 4),
                categories=[],
                improvements=[],
                path_to_target=[],
                estimated_effort="MODERATE",
                timestamp=f"2024-01-{15+i}T10:30:00",
                file_path="/path/to/document.md",
                total_words=500 + i * 20,
            )
            history.add_score(score, notes=f"Revision {i+1}")

        assert len(history.scores) == 5

        # Check that all scores are recorded
        assert history.scores[0].detection_risk == 50.0
        assert history.scores[4].detection_risk == 38.0
        assert history.scores[0].quality_score == 60.0
        assert history.scores[4].quality_score == 76.0

        # Trend should show improvement
        trend = history.get_trend()
        assert trend["detection"] == "IMPROVING"
        assert trend["quality"] == "IMPROVING"
