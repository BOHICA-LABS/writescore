"""
Tests for history/trends.py - trend analysis and reporting.

Tests cover:
- Sparkline generation
- Dimension trend reports
- Aggregate trend reports
- Tier trend reports
- Iteration comparison reports
- Full history reports
- Raw metric trend visualization
"""

import pytest

from writescore.history.tracker import DimensionScore, HistoricalScore, ScoreHistory
from writescore.history.trends import (
    generate_aggregate_trend_report,
    generate_comparison_report,
    generate_dimension_trend_report,
    generate_full_history_report,
    generate_raw_metric_trends,
    generate_sparkline,
    generate_tier_trend_report,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_v2_history():
    """Create a sample v2.0 history with multiple iterations."""
    history = ScoreHistory(file_path="/path/to/test.md")

    # Create 5 iterations showing improvement
    for i in range(5):
        dimensions = {
            "Perplexity (AI Vocab)": DimensionScore(
                score=6.0 + i * 1.5,
                max_score=12.0,
                percentage=(6.0 + i * 1.5) / 12.0 * 100,
                raw_value=15.0 - i * 2.0,
                interpretation="IMPROVING",
            ),
            "Burstiness (Sent. Var)": DimensionScore(
                score=7.0 + i * 0.8,
                max_score=12.0,
                percentage=(7.0 + i * 0.8) / 12.0 * 100,
                raw_value=6.0 + i * 1.5,
                interpretation="IMPROVING",
            ),
            "MATTR (Lexical Richness)": DimensionScore(
                score=8.0 + i * 0.3,
                max_score=12.0,
                percentage=(8.0 + i * 0.3) / 12.0 * 100,
                raw_value=0.65 + i * 0.02,
                interpretation="STABLE",
            ),
        }

        raw_metrics = {
            "ai_vocabulary_per_1k": 15.0 - i * 2.0,
            "sentence_stdev": 6.0 + i * 1.5,
            "em_dashes_per_page": 8.0 - i * 1.2,
        }

        score = HistoricalScore(
            timestamp=f"2025-01-{15+i}T10:00:00",
            total_words=3800 + i * 50,
            notes=f"Iteration {i+1}",
            history_version="2.0",
            detection_risk=45.0 - i * 2.5,
            quality_score=70.0 + i * 3.0,
            detection_interpretation="IMPROVING",
            quality_interpretation="IMPROVING",
            tier1_score=18.0 + i * 2.0,
            tier2_score=15.0 + i * 1.8,
            tier3_score=10.0 + i * 1.2,
            tier4_score=6.0 + i * 0.5,
            dimensions=dimensions,
            raw_metrics=raw_metrics,
        )

        history.scores.append(score)

    return history


# ============================================================================
# Sparkline Generation Tests
# ============================================================================


class TestSparklineGeneration:
    """Tests for sparkline generation."""

    def test_generate_sparkline_basic(self):
        """Test basic sparkline generation."""
        values = [1, 2, 4, 6, 8, 7, 6]
        sparkline = generate_sparkline(values)

        assert len(sparkline) == 7
        assert all(c in "▁▂▃▄▅▆▇█" for c in sparkline)
        assert sparkline[0] == "▁"  # Min value
        assert sparkline[4] == "█"  # Max value

    def test_generate_sparkline_all_same(self):
        """Test sparkline with all same values."""
        values = [5, 5, 5, 5, 5]
        sparkline = generate_sparkline(values)

        # All should be same character (when min == max)
        assert len(set(sparkline)) == 1  # All characters the same
        assert len(sparkline) == 5

    def test_generate_sparkline_empty(self):
        """Test sparkline with empty values."""
        values = []
        sparkline = generate_sparkline(values)

        assert sparkline == ""

    def test_generate_sparkline_single_value(self):
        """Test sparkline with single value."""
        values = [42]
        sparkline = generate_sparkline(values)

        assert len(sparkline) == 1

    def test_generate_sparkline_with_width_limit(self):
        """Test sparkline with width constraint."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        sparkline = generate_sparkline(values, width=5)

        assert len(sparkline) == 5

    def test_generate_sparkline_increasing(self):
        """Test sparkline with increasing values."""
        values = [1, 2, 3, 4, 5]
        sparkline = generate_sparkline(values)

        # Should show progression from low to high
        chars = list(sparkline)
        for i in range(len(chars) - 1):
            assert chars[i] <= chars[i + 1]


# ============================================================================
# Dimension Trend Report Tests
# ============================================================================


class TestDimensionTrendReport:
    """Tests for dimension trend report generation."""

    def test_generate_dimension_trend_report_basic(self, sample_v2_history):
        """Test basic dimension trend report."""
        report = generate_dimension_trend_report(sample_v2_history)

        assert "DIMENSION TREND ANALYSIS" in report
        assert "TOP" in report
        assert "IMPROVEMENT" in report
        assert "Perplexity (AI Vocab)" in report
        assert "Burstiness (Sent. Var)" in report

    def test_dimension_trend_report_insufficient_data(self):
        """Test report with insufficient data."""
        history = ScoreHistory(file_path="/path/to/test.md")
        report = generate_dimension_trend_report(history)

        assert "Insufficient data" in report

    def test_dimension_trend_report_top_n(self, sample_v2_history):
        """Test limiting top improvements shown."""
        report = generate_dimension_trend_report(sample_v2_history, top_n=2)

        # Should limit output
        assert "TOP 2" in report


# ============================================================================
# Aggregate Trend Report Tests
# ============================================================================


class TestAggregateTrendReport:
    """Tests for aggregate trend report generation."""

    def test_generate_aggregate_trend_report(self, sample_v2_history):
        """Test aggregate trend report."""
        report = generate_aggregate_trend_report(sample_v2_history)

        assert "AGGREGATE SCORES:" in report
        assert "Quality:" in report
        assert "Detection:" in report
        assert "IMPROVING" in report
        assert "→" in report or "↑" in report or "↓" in report

    def test_aggregate_trend_insufficient_data(self):
        """Test with insufficient data."""
        history = ScoreHistory(file_path="/path/to/test.md")
        report = generate_aggregate_trend_report(history)

        assert report == ""


# ============================================================================
# Tier Trend Report Tests
# ============================================================================


class TestTierTrendReport:
    """Tests for tier trend report generation."""

    def test_generate_tier_trend_report(self, sample_v2_history):
        """Test tier trend report."""
        report = generate_tier_trend_report(sample_v2_history)

        assert "TIER TRENDS:" in report
        assert "Tier 1" in report
        assert "Tier 2" in report
        assert "Tier 3" in report
        assert "Tier 4" in report

    def test_tier_trend_insufficient_data(self):
        """Test with insufficient data."""
        history = ScoreHistory(file_path="/path/to/test.md")
        report = generate_tier_trend_report(history)

        assert report == ""


# ============================================================================
# Comparison Report Tests
# ============================================================================


class TestComparisonReport:
    """Tests for iteration comparison report generation."""

    def test_generate_comparison_report_basic(self, sample_v2_history):
        """Test basic comparison report."""
        report = generate_comparison_report(sample_v2_history, 0, 4)

        assert "ITERATION COMPARISON" in report
        assert "Iteration 1 vs. Iteration 5" in report
        assert "AGGREGATE SCORES:" in report
        assert "Quality Score" in report
        assert "Detection Risk" in report
        assert "TIER SCORES:" in report

    def test_comparison_report_invalid_indices(self, sample_v2_history):
        """Test comparison with invalid indices."""
        report = generate_comparison_report(sample_v2_history, 0, 10)

        assert "Error" in report or "Invalid" in report

    def test_comparison_report_insights(self, sample_v2_history):
        """Test that insights are generated."""
        report = generate_comparison_report(sample_v2_history, 0, 4)

        assert "KEY INSIGHTS:" in report


# ============================================================================
# Full History Report Tests
# ============================================================================


class TestFullHistoryReport:
    """Tests for full history report generation."""

    def test_generate_full_history_report(self, sample_v2_history):
        """Test full history report."""
        report = generate_full_history_report(sample_v2_history)

        assert "COMPLETE OPTIMIZATION JOURNEY" in report
        assert "AGGREGATE SCORES:" in report
        assert "ITERATION SUMMARY:" in report
        assert "FINAL ASSESSMENT" in report
        assert "Publication Readiness:" in report
        assert "ITERATION 1:" in report
        assert "ITERATION 5:" in report

    def test_full_history_report_empty(self):
        """Test with empty history."""
        history = ScoreHistory(file_path="/path/to/test.md")
        report = generate_full_history_report(history)

        assert "No history data" in report

    def test_full_history_report_sparklines(self, sample_v2_history):
        """Test that sparklines are included."""
        report = generate_full_history_report(sample_v2_history)

        assert "Sparkline View" in report
        # Should contain sparkline characters
        assert any(c in report for c in "▁▂▃▄▅▆▇█")


# ============================================================================
# Raw Metric Trends Tests
# ============================================================================


class TestRawMetricTrends:
    """Tests for raw metric trend visualization."""

    def test_generate_raw_metric_trends_basic(self, sample_v2_history):
        """Test basic raw metric trends."""
        report = generate_raw_metric_trends(sample_v2_history)

        assert "RAW METRIC TRENDS" in report
        assert "ai_vocabulary_per_1k" in report
        assert "sentence_stdev" in report
        assert "em_dashes_per_page" in report
        # Should contain sparklines
        assert any(c in report for c in "▁▂▃▄▅▆▇█")

    def test_raw_metric_trends_specific_metrics(self, sample_v2_history):
        """Test with specific metrics requested."""
        report = generate_raw_metric_trends(
            sample_v2_history, metric_names=["ai_vocabulary_per_1k"]
        )

        assert "ai_vocabulary_per_1k" in report
        # Should not include other metrics
        assert "sentence_stdev" not in report

    def test_raw_metric_trends_insufficient_data(self):
        """Test with insufficient data."""
        history = ScoreHistory(file_path="/path/to/test.md")
        report = generate_raw_metric_trends(history)

        assert "Insufficient" in report or "v2.0 data" in report


# ============================================================================
# Integration Tests
# ============================================================================


class TestTrendsIntegration:
    """Integration tests for complete trend workflows."""

    def test_complete_reporting_workflow(self, sample_v2_history):
        """Test generating all reports in sequence."""
        # Generate all reports
        aggregate_report = generate_aggregate_trend_report(sample_v2_history)
        tier_report = generate_tier_trend_report(sample_v2_history)
        dimension_report = generate_dimension_trend_report(sample_v2_history)
        comparison_report = generate_comparison_report(sample_v2_history, 0, 4)
        full_report = generate_full_history_report(sample_v2_history)
        raw_metric_report = generate_raw_metric_trends(sample_v2_history)

        # Verify all generated successfully
        assert len(aggregate_report) > 0
        assert len(tier_report) > 0
        assert len(dimension_report) > 0
        assert len(comparison_report) > 0
        assert len(full_report) > 0
        assert len(raw_metric_report) > 0

        # Verify no errors in any report
        assert "Error" not in aggregate_report
        assert "Error" not in tier_report
        assert "Error" not in dimension_report
        assert "Error" not in full_report

    def test_sparkline_in_multiple_contexts(self, sample_v2_history):
        """Test sparklines appear in relevant reports."""
        full_report = generate_full_history_report(sample_v2_history)
        raw_metric_report = generate_raw_metric_trends(sample_v2_history)

        # Both should contain sparkline characters
        sparkline_chars = "▁▂▃▄▅▆▇█"
        assert any(c in full_report for c in sparkline_chars)
        assert any(c in raw_metric_report for c in sparkline_chars)
