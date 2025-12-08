"""
Tests for history tracker v2.0 functionality.

Tests cover:
- DimensionScore dataclass
- HistoricalScore v2.0 with dimensions, tiers, and raw metrics
- Backward compatibility with v1.0 format
- Dimension trend analysis
- Tier trend analysis
- Plateau detection
- CSV export
- JSON serialization/deserialization
"""

import csv
import tempfile
from pathlib import Path

import pytest

from writescore.history.tracker import (
    DimensionScore,
    HistoricalScore,
    ScoreHistory,
    load_score_history,
    save_score_history,
)
from writescore.scoring.dual_score import DualScore, ScoreCategory, ScoreDimension

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_dimension_score():
    """Create a sample DimensionScore."""
    return DimensionScore(
        score=8.5, max_score=12.0, percentage=70.8, raw_value=0.72, interpretation="GOOD"
    )


@pytest.fixture
def sample_v2_dual_score():
    """Create a comprehensive v2.0 DualScore with all dimensions."""
    # Create sample dimensions for 4 tiers
    tier1_dims = [
        ScoreDimension("GLTR Token Ranking", 8.5, 12.0, 70.8, "GOOD", 3.5, 0.42, None),
        ScoreDimension("MATTR (Lexical Richness)", 9.0, 12.0, 75.0, "GOOD", 3.0, 0.72, None),
    ]
    tier2_dims = [
        ScoreDimension("Perplexity (AI Vocab)", 6.8, 12.0, 56.7, "FAIR", 5.2, 14.2, None),
        ScoreDimension("Burstiness (Sent. Var)", 7.8, 12.0, 65.0, "GOOD", 4.2, 8.1, None),
    ]
    tier3_dims = [
        ScoreDimension("Em-Dash Formatting", 4.1, 8.0, 51.3, "FAIR", 3.9, 5.7, None),
        ScoreDimension("Heading Parallelism", 5.5, 8.0, 68.8, "GOOD", 2.5, 0.78, None),
    ]
    tier4_dims = [
        ScoreDimension("Blockquote Usage", 6.0, 8.0, 75.0, "GOOD", 2.0, 3.1, None),
    ]

    categories = [
        ScoreCategory("Tier 1 (Advanced Detection)", 17.5, 24.0, 72.9, tier1_dims),
        ScoreCategory("Tier 2 (Core Patterns)", 14.6, 24.0, 60.8, tier2_dims),
        ScoreCategory("Tier 3 (Supporting Indicators)", 9.6, 16.0, 60.0, tier3_dims),
        ScoreCategory("Tier 4 (Advanced Structural)", 6.0, 8.0, 75.0, tier4_dims),
    ]

    return DualScore(
        detection_risk=35.0,
        quality_score=72.0,
        detection_interpretation="MODERATE",
        quality_interpretation="GOOD",
        detection_target=30.0,
        quality_target=85.0,
        detection_gap=5.0,
        quality_gap=13.0,
        categories=categories,
        improvements=[],
        path_to_target=[],
        estimated_effort="MODERATE",
        timestamp="2025-01-15T10:30:00",
        file_path="/path/to/test.md",
        total_words=3847,
    )


@pytest.fixture
def sample_analysis_results():
    """Create a mock AnalysisResults object."""

    class MockResults:
        ai_vocabulary_per_1k = 14.2
        sentence_stdev = 8.1
        em_dashes_per_page = 5.7
        heading_parallelism_score = 0.78
        paragraph_cv = 0.31
        section_variance_pct = 18.5
        mattr = 0.72
        rttr = 6.5
        blockquote_per_page = 3.1
        generic_link_ratio = 0.58
        bold_per_1k = 4.2
        italic_per_1k = 2.8

    return MockResults()


# ============================================================================
# DimensionScore Tests
# ============================================================================


class TestDimensionScore:
    """Tests for DimensionScore dataclass."""

    def test_dimension_score_creation(self):
        """Test creating a DimensionScore."""
        dim = DimensionScore(
            score=8.5, max_score=12.0, percentage=70.8, raw_value=0.72, interpretation="GOOD"
        )

        assert dim.score == 8.5
        assert dim.max_score == 12.0
        assert dim.percentage == 70.8
        assert dim.raw_value == 0.72
        assert dim.interpretation == "GOOD"

    def test_dimension_score_to_dict(self, sample_dimension_score):
        """Test DimensionScore serialization to dict."""
        dim_dict = sample_dimension_score.to_dict()

        assert dim_dict["score"] == 8.5
        assert dim_dict["max_score"] == 12.0
        assert dim_dict["percentage"] == 70.8
        assert dim_dict["raw_value"] == 0.72
        assert dim_dict["interpretation"] == "GOOD"

    def test_dimension_score_from_dict(self):
        """Test DimensionScore deserialization from dict."""
        dim_dict = {
            "score": 8.5,
            "max_score": 12.0,
            "percentage": 70.8,
            "raw_value": 0.72,
            "interpretation": "GOOD",
        }

        dim = DimensionScore.from_dict(dim_dict)

        assert dim.score == 8.5
        assert dim.max_score == 12.0
        assert dim.percentage == 70.8
        assert dim.raw_value == 0.72
        assert dim.interpretation == "GOOD"

    def test_dimension_score_roundtrip(self, sample_dimension_score):
        """Test DimensionScore serialization roundtrip."""
        dim_dict = sample_dimension_score.to_dict()
        reconstructed = DimensionScore.from_dict(dim_dict)

        assert reconstructed.score == sample_dimension_score.score
        assert reconstructed.max_score == sample_dimension_score.max_score
        assert reconstructed.percentage == sample_dimension_score.percentage
        assert reconstructed.raw_value == sample_dimension_score.raw_value
        assert reconstructed.interpretation == sample_dimension_score.interpretation


# ============================================================================
# HistoricalScore v2.0 Tests
# ============================================================================


class TestHistoricalScoreV2:
    """Tests for HistoricalScore v2.0 functionality."""

    def test_v2_creation_with_all_fields(self):
        """Test creating a v2.0 HistoricalScore with all fields."""
        dimensions = {
            "perplexity": DimensionScore(6.8, 12.0, 56.7, 14.2, "FAIR"),
            "burstiness": DimensionScore(7.8, 12.0, 65.0, 8.1, "GOOD"),
        }

        raw_metrics = {
            "ai_vocabulary_per_1k": 14.2,
            "sentence_stdev": 8.1,
            "em_dashes_per_page": 5.7,
        }

        score = HistoricalScore(
            timestamp="2025-01-15T10:30:00",
            total_words=3847,
            notes="Initial baseline",
            history_version="2.0",
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            tier1_score=17.5,
            tier2_score=14.6,
            tier3_score=9.6,
            tier4_score=6.0,
            dimensions=dimensions,
            raw_metrics=raw_metrics,
        )

        assert score.history_version == "2.0"
        assert score.tier1_score == 17.5
        assert score.tier2_score == 14.6
        assert score.tier3_score == 9.6
        assert score.tier4_score == 6.0
        assert len(score.dimensions) == 2
        assert len(score.raw_metrics) == 3
        assert "perplexity" in score.dimensions
        assert "ai_vocabulary_per_1k" in score.raw_metrics

    def test_v2_to_dict_serialization(self):
        """Test v2.0 HistoricalScore serialization."""
        dimensions = {"perplexity": DimensionScore(6.8, 12.0, 56.7, 14.2, "FAIR")}

        score = HistoricalScore(
            timestamp="2025-01-15T10:30:00",
            total_words=3847,
            history_version="2.0",
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            tier1_score=17.5,
            dimensions=dimensions,
            raw_metrics={"ai_vocabulary_per_1k": 14.2},
        )

        score_dict = score.to_dict()

        assert score_dict["history_version"] == "2.0"
        assert score_dict["tier1_score"] == 17.5
        assert "dimensions" in score_dict
        assert "perplexity" in score_dict["dimensions"]
        assert score_dict["dimensions"]["perplexity"]["score"] == 6.8
        assert score_dict["raw_metrics"]["ai_vocabulary_per_1k"] == 14.2

    def test_v2_from_dict_deserialization(self):
        """Test v2.0 HistoricalScore deserialization."""
        score_dict = {
            "timestamp": "2025-01-15T10:30:00",
            "total_words": 3847,
            "notes": "Test",
            "history_version": "2.0",
            "detection_risk": 35.0,
            "quality_score": 72.0,
            "detection_interpretation": "MODERATE",
            "quality_interpretation": "GOOD",
            "tier1_score": 17.5,
            "tier2_score": 14.6,
            "tier3_score": 9.6,
            "tier4_score": 6.0,
            "dimensions": {
                "perplexity": {
                    "score": 6.8,
                    "max_score": 12.0,
                    "percentage": 56.7,
                    "raw_value": 14.2,
                    "interpretation": "FAIR",
                }
            },
            "raw_metrics": {"ai_vocabulary_per_1k": 14.2},
        }

        score = HistoricalScore.from_dict(score_dict)

        assert score.history_version == "2.0"
        assert score.tier1_score == 17.5
        assert score.tier2_score == 14.6
        assert score.tier3_score == 9.6
        assert score.tier4_score == 6.0
        assert "perplexity" in score.dimensions
        assert score.dimensions["perplexity"].score == 6.8
        assert score.raw_metrics["ai_vocabulary_per_1k"] == 14.2


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


class TestBackwardCompatibility:
    """Tests for v1.0 to v2.0 backward compatibility."""

    def test_load_v1_format(self):
        """Test loading v1.0 format history."""
        v1_dict = {
            "timestamp": "2025-01-15T10:30:00",
            "detection_risk": 45.3,
            "quality_score": 76.2,
            "detection_interpretation": "MEDIUM-HIGH",
            "quality_interpretation": "GOOD",
            "total_words": 3847,
            "notes": "Legacy format",
            # No history_version, dimensions, or raw_metrics
        }

        score = HistoricalScore.from_dict(v1_dict)

        assert score.history_version == "1.0"  # Detected as v1.0
        assert score.detection_risk == 45.3
        assert score.quality_score == 76.2
        assert len(score.dimensions) == 0  # Empty for v1.0
        assert len(score.raw_metrics) == 0  # Empty for v1.0
        assert score.tier1_score == 0.0  # Default
        assert score.tier2_score == 0.0
        assert score.tier3_score == 0.0
        assert score.tier4_score == 0.0

    def test_mixed_v1_v2_history(self):
        """Test ScoreHistory with mixed v1.0 and v2.0 scores."""
        history_dict = {
            "file_path": "/path/to/test.md",
            "scores": [
                {
                    # v1.0 score
                    "timestamp": "2025-01-15T10:00:00",
                    "detection_risk": 45.0,
                    "quality_score": 76.0,
                    "detection_interpretation": "HIGH",
                    "quality_interpretation": "GOOD",
                    "total_words": 3800,
                },
                {
                    # v2.0 score
                    "timestamp": "2025-01-15T11:00:00",
                    "history_version": "2.0",
                    "detection_risk": 35.0,
                    "quality_score": 82.0,
                    "detection_interpretation": "MODERATE",
                    "quality_interpretation": "VERY GOOD",
                    "total_words": 3847,
                    "tier1_score": 20.0,
                    "tier2_score": 18.0,
                    "tier3_score": 12.0,
                    "tier4_score": 7.0,
                    "dimensions": {},
                    "raw_metrics": {},
                },
            ],
        }

        history = ScoreHistory.from_dict(history_dict)

        assert len(history.scores) == 2
        assert history.scores[0].history_version == "1.0"
        assert history.scores[1].history_version == "2.0"
        assert history.scores[0].tier1_score == 0.0  # v1.0 has no tiers
        assert history.scores[1].tier1_score == 20.0  # v2.0 has tiers


# ============================================================================
# ScoreHistory v2.0 Tests
# ============================================================================


class TestScoreHistoryV2:
    """Tests for ScoreHistory v2.0 functionality."""

    def test_add_score_with_results(self, sample_v2_dual_score, sample_analysis_results):
        """Test adding v2.0 score with analysis results."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_v2_dual_score, sample_analysis_results, notes="Initial baseline")

        assert len(history.scores) == 1
        score = history.scores[0]

        assert score.history_version == "2.0"
        assert score.tier1_score == 17.5  # Sum of tier 1 dimensions
        assert score.tier2_score == 14.6  # Sum of tier 2 dimensions
        assert score.tier3_score == 9.6  # Sum of tier 3 dimensions
        assert score.tier4_score == 6.0  # Sum of tier 4 dimensions
        assert len(score.dimensions) == 7  # Total dimensions from sample
        assert len(score.raw_metrics) == 12  # All raw metrics

        # Check specific dimension
        assert "MATTR (Lexical Richness)" in score.dimensions
        assert score.dimensions["MATTR (Lexical Richness)"].score == 9.0

        # Check specific raw metric
        assert score.raw_metrics["ai_vocabulary_per_1k"] == 14.2
        assert score.raw_metrics["sentence_stdev"] == 8.1

    def test_get_dimension_trend(self, sample_v2_dual_score, sample_analysis_results):
        """Test dimension trend analysis."""
        history = ScoreHistory(file_path="/path/to/test.md")

        # Add first score
        history.add_score(sample_v2_dual_score, sample_analysis_results, notes="Iteration 1")

        # Create improved version
        improved_score = sample_v2_dual_score
        improved_score.categories[1].dimensions[
            0
        ].score = 9.8  # Perplexity improved from 6.8 to 9.8
        improved_score.timestamp = "2025-01-15T14:00:00"

        history.add_score(improved_score, sample_analysis_results, notes="Iteration 2")

        # Get trend
        trend = history.get_dimension_trend("Perplexity (AI Vocab)")

        assert trend["trend"] == "IMPROVING"
        assert trend["change"] == 3.0  # 9.8 - 6.8
        assert trend["first_score"] == 6.8
        assert trend["last_score"] == 9.8

    def test_get_tier_trends(self, sample_v2_dual_score, sample_analysis_results):
        """Test tier-level trend analysis."""
        history = ScoreHistory(file_path="/path/to/test.md")

        # Add two scores
        history.add_score(sample_v2_dual_score, sample_analysis_results, notes="Iteration 1")

        # Create improved version
        improved_score = sample_v2_dual_score
        improved_score.timestamp = "2025-01-15T14:00:00"
        # Improve tier 1 scores
        improved_score.categories[0].dimensions[0].score = 10.0  # GLTR: 8.5 → 10.0
        improved_score.categories[0].dimensions[1].score = 10.5  # MATTR: 9.0 → 10.5

        history.add_score(improved_score, sample_analysis_results, notes="Iteration 2")

        # Get tier trends
        trends = history.get_tier_trends()

        assert "Tier 1 (Advanced Detection)" in trends
        tier1_trend = trends["Tier 1 (Advanced Detection)"]

        assert tier1_trend["change"] > 0  # Should show improvement
        assert tier1_trend["trend"] == "IMPROVING"
        assert tier1_trend["max"] == 70  # Max score for tier 1

    def test_get_plateaued_dimensions(self, sample_v2_dual_score, sample_analysis_results):
        """Test plateau detection."""
        history = ScoreHistory(file_path="/path/to/test.md")

        # Add 4 scores where one dimension plateaus
        for i in range(4):
            score = sample_v2_dual_score
            score.timestamp = f"2025-01-15T{10+i}:00:00"

            # Perplexity keeps improving
            score.categories[1].dimensions[0].score = 6.8 + i * 2.0

            # Burstiness plateaus (changes < 1pt)
            score.categories[1].dimensions[1].score = 7.8 + i * 0.2

            history.add_score(score, sample_analysis_results, notes=f"Iteration {i+1}")

        # Check for plateaus (last 3 iterations)
        plateaued = history.get_plateaued_dimensions(lookback=3, threshold=1.0)

        assert "Burstiness (Sent. Var)" in plateaued  # Should be detected as plateaued
        assert "Perplexity (AI Vocab)" not in plateaued  # Should not be plateaued


# ============================================================================
# CSV Export Tests
# ============================================================================


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_export_to_csv_basic(self, sample_v2_dual_score, sample_analysis_results):
        """Test basic CSV export."""
        history = ScoreHistory(file_path="/path/to/test.md")
        history.add_score(sample_v2_dual_score, sample_analysis_results, notes="Test iteration")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            history.export_to_csv(output_path)

            # Read back and verify
            with open(output_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                assert row["iteration"] == "1"
                assert row["quality_score"] == "72.0"
                assert row["detection_risk"] == "35.0"
                assert row["tier1_score"] == "17.5"
                assert "ai_vocabulary_per_1k" in row
                assert row["ai_vocabulary_per_1k"] == "14.2"

        finally:
            Path(output_path).unlink()

    def test_export_multiple_iterations(self, sample_v2_dual_score, sample_analysis_results):
        """Test CSV export with multiple iterations."""
        history = ScoreHistory(file_path="/path/to/test.md")

        for i in range(3):
            score = sample_v2_dual_score
            score.timestamp = f"2025-01-15T{10+i}:00:00"
            history.add_score(score, sample_analysis_results, notes=f"Iteration {i+1}")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            history.export_to_csv(output_path)

            # Read back and verify
            with open(output_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3
                assert rows[0]["iteration"] == "1"
                assert rows[1]["iteration"] == "2"
                assert rows[2]["iteration"] == "3"

        finally:
            Path(output_path).unlink()


# ============================================================================
# Save/Load Tests
# ============================================================================


class TestSaveLoad:
    """Tests for save/load functionality."""

    def test_save_and_load_v2_history(self, sample_v2_dual_score, sample_analysis_results):
        """Test saving and loading v2.0 history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.touch()

            # Create and populate history
            history = ScoreHistory(file_path=str(file_path))
            history.add_score(sample_v2_dual_score, sample_analysis_results, notes="Test iteration")

            # Save
            save_score_history(history)

            # Verify history file exists
            history_file = Path(tmpdir) / ".test.md.history.json"
            assert history_file.exists()

            # Load
            loaded_history = load_score_history(str(file_path))

            assert len(loaded_history.scores) == 1
            assert loaded_history.scores[0].history_version == "2.0"
            assert loaded_history.scores[0].tier1_score == 17.5
            assert len(loaded_history.scores[0].dimensions) == 7
            assert len(loaded_history.scores[0].raw_metrics) == 12

    def test_load_nonexistent_history(self):
        """Test loading history when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nonexistent.md"

            history = load_score_history(str(file_path))

            assert len(history.scores) == 0
            assert history.file_path == str(file_path)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationV2:
    """Integration tests for complete v2.0 workflows."""

    def test_complete_optimization_journey(self, sample_v2_dual_score, sample_analysis_results):
        """Test complete optimization journey with v2.0 tracking."""
        history = ScoreHistory(file_path="/path/to/document.md")

        # Simulate 5 iterations of optimization
        base_qual = 70.0
        base_det = 45.0

        for i in range(5):
            score = sample_v2_dual_score
            score.timestamp = f"2025-01-{15+i}T10:00:00"
            score.quality_score = base_qual + i * 3
            score.detection_risk = base_det - i * 2.5

            # Improve perplexity dimension
            score.categories[1].dimensions[0].score = 6.8 + i * 1.5

            history.add_score(score, sample_analysis_results, notes=f"Iteration {i+1}")

        # Verify progression
        assert len(history.scores) == 5
        assert history.scores[0].quality_score == 70.0
        assert history.scores[4].quality_score == 82.0
        assert history.scores[0].detection_risk == 45.0
        assert history.scores[4].detection_risk == 35.0

        # Check dimension improvement
        first_perp = history.scores[0].dimensions["Perplexity (AI Vocab)"].score
        last_perp = history.scores[4].dimensions["Perplexity (AI Vocab)"].score
        assert last_perp > first_perp

        # Verify trends
        trend = history.get_dimension_trend("Perplexity (AI Vocab)")
        assert trend["trend"] == "IMPROVING"
        assert trend["change"] > 0

    def test_csv_export_for_analysis(self, sample_v2_dual_score, sample_analysis_results):
        """Test CSV export for external analysis tools."""
        history = ScoreHistory(file_path="/path/to/document.md")

        # Add several iterations
        for i in range(5):
            score = sample_v2_dual_score
            score.timestamp = f"2025-01-{15+i}T10:00:00"
            history.add_score(score, sample_analysis_results, notes=f"Iteration {i+1}")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            history.export_to_csv(output_path)

            # Verify file structure
            with open(output_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                # Check for key headers
                assert "timestamp" in headers
                assert "quality_score" in headers
                assert "detection_risk" in headers
                assert "tier1_score" in headers
                assert "tier2_score" in headers
                assert "tier3_score" in headers
                assert "tier4_score" in headers

                # Check dimension scores are included
                dimension_score_headers = [
                    h
                    for h in headers
                    if h.endswith("_score")
                    and "tier" not in h
                    and h not in ["quality_score", "detection_risk"]
                ]
                assert len(dimension_score_headers) > 0

                # Check raw metrics are included
                assert "ai_vocabulary_per_1k" in headers
                assert "sentence_stdev" in headers

                # Verify data
                rows = list(reader)
                assert len(rows) == 5

        finally:
            Path(output_path).unlink()
