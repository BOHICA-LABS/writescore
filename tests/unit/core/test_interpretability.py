"""
Unit tests for score interpretability features.

Tests Story 2.5 Task 7: Interpretability Features.
"""

import pytest

from writescore.core.interpretability import (
    DistributionVisualizer,
    PercentileCalculator,
    PercentileContext,
    ScoreInterpretation,
    ScoreInterpreter,
    format_percentile_report,
)


class TestPercentileContext:
    """Test PercentileContext dataclass."""

    def test_basic_creation(self):
        """Test basic context creation."""
        context = PercentileContext(
            dimension_name="burstiness", raw_value=0.65, percentile_human=45.0, percentile_ai=30.0
        )

        assert context.dimension_name == "burstiness"
        assert context.raw_value == 0.65
        assert context.percentile_human == 45.0
        assert context.percentile_ai == 30.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        context = PercentileContext(
            dimension_name="lexical",
            raw_value=0.72,
            percentile_human=60.5,
            interpretation="Above average",
        )

        d = context.to_dict()

        assert d["dimension_name"] == "lexical"
        assert d["raw_value"] == 0.72
        assert d["percentile_human"] == 60.5
        assert d["interpretation"] == "Above average"

    def test_default_values(self):
        """Test default values."""
        context = PercentileContext(dimension_name="test", raw_value=0.5)

        assert context.percentile_human is None
        assert context.percentile_ai is None
        assert context.target_percentile == 50.0
        assert context.gap_to_target == 0.0


class TestScoreInterpretation:
    """Test ScoreInterpretation dataclass."""

    def test_empty_interpretation(self):
        """Test empty interpretation."""
        interp = ScoreInterpretation()

        assert interp.overall_quality_percentile is None
        assert len(interp.dimension_contexts) == 0
        assert len(interp.recommendations) == 0

    def test_with_dimension_contexts(self):
        """Test with dimension contexts."""
        interp = ScoreInterpretation()
        interp.dimension_contexts["burstiness"] = PercentileContext(
            dimension_name="burstiness", raw_value=0.65, percentile_human=45.0
        )

        assert "burstiness" in interp.dimension_contexts
        assert interp.dimension_contexts["burstiness"].percentile_human == 45.0

    def test_to_dict(self):
        """Test serialization."""
        interp = ScoreInterpretation(
            overall_quality_percentile=72.5,
            recommendations=["Improve burstiness", "Reduce hedging"],
        )
        interp.dimension_contexts["test"] = PercentileContext(dimension_name="test", raw_value=0.5)

        d = interp.to_dict()

        assert d["overall_quality_percentile"] == 72.5
        assert len(d["recommendations"]) == 2
        assert "test" in d["dimension_contexts"]


class TestPercentileCalculator:
    """Test PercentileCalculator class."""

    @pytest.fixture
    def sample_stats(self):
        """Sample distribution statistics."""
        return {
            "percentiles": {"p10": 0.3, "p25": 0.4, "p50": 0.5, "p75": 0.6, "p90": 0.7},
            "min_val": 0.1,
            "max_val": 0.9,
        }

    def test_calculate_at_known_percentile(self, sample_stats):
        """Test calculation at exact percentile values."""
        calc = PercentileCalculator(sample_stats)

        # At p50 value (0.5), should return approximately 50
        result = calc.calculate_percentile(0.5)
        assert 45 <= result <= 55  # Allow some tolerance for interpolation

    def test_calculate_below_min(self, sample_stats):
        """Test calculation for value below min."""
        calc = PercentileCalculator(sample_stats)

        result = calc.calculate_percentile(0.0)  # Below min of 0.1
        assert result == 0.0

    def test_calculate_above_max(self, sample_stats):
        """Test calculation for value above max."""
        calc = PercentileCalculator(sample_stats)

        result = calc.calculate_percentile(1.0)  # Above max of 0.9
        assert result == 100.0

    def test_calculate_interpolation(self, sample_stats):
        """Test linear interpolation between percentiles."""
        calc = PercentileCalculator(sample_stats)

        # Value between p25 (0.4) and p50 (0.5)
        result = calc.calculate_percentile(0.45)
        assert 25 < result < 50

    def test_empty_percentiles(self):
        """Test with no percentile data."""
        calc = PercentileCalculator({"percentiles": {}})

        result = calc.calculate_percentile(0.5)
        assert result == 50.0  # Default to median

    def test_calculate_at_boundaries(self, sample_stats):
        """Test calculation at min and max."""
        calc = PercentileCalculator(sample_stats)

        min_result = calc.calculate_percentile(0.1)  # At min
        max_result = calc.calculate_percentile(0.9)  # At max

        assert min_result <= 10  # Should be near 0
        assert max_result >= 90  # Should be near 100


class TestScoreInterpreter:
    """Test ScoreInterpreter class."""

    @pytest.fixture
    def human_stats(self):
        """Sample human distribution stats."""
        return {
            "burstiness": {
                "percentiles": {"p10": 5.0, "p25": 8.0, "p50": 12.0, "p75": 16.0, "p90": 20.0},
                "min_val": 2.0,
                "max_val": 25.0,
            },
            "lexical": {
                "percentiles": {"p10": 0.4, "p25": 0.5, "p50": 0.6, "p75": 0.7, "p90": 0.8},
                "min_val": 0.3,
                "max_val": 0.9,
            },
        }

    @pytest.fixture
    def ai_stats(self):
        """Sample AI distribution stats."""
        return {
            "burstiness": {
                "percentiles": {"p10": 3.0, "p25": 5.0, "p50": 7.0, "p75": 9.0, "p90": 11.0},
                "min_val": 1.0,
                "max_val": 15.0,
            },
            "lexical": {
                "percentiles": {"p10": 0.5, "p25": 0.55, "p50": 0.6, "p75": 0.65, "p90": 0.7},
                "min_val": 0.4,
                "max_val": 0.75,
            },
        }

    def test_interpret_dimension_human_only(self, human_stats):
        """Test interpretation with only human stats."""
        interpreter = ScoreInterpreter(human_stats=human_stats)

        context = interpreter.interpret_dimension("burstiness", 12.0)

        assert context.dimension_name == "burstiness"
        assert context.raw_value == 12.0
        assert context.percentile_human is not None
        assert 45 <= context.percentile_human <= 55  # Near median
        assert context.percentile_ai is None

    def test_interpret_dimension_both_distributions(self, human_stats, ai_stats):
        """Test interpretation with both distributions."""
        interpreter = ScoreInterpreter(human_stats=human_stats, ai_stats=ai_stats)

        # Value typical of human but unusual for AI
        context = interpreter.interpret_dimension("burstiness", 15.0)

        assert context.percentile_human is not None
        assert context.percentile_ai is not None
        # Human: 15 is between p50 (12) and p75 (16), so ~62nd percentile
        # AI: 15 is above p90 (11), so ~95th+ percentile
        assert context.percentile_ai > context.percentile_human

    def test_interpret_dimension_with_target(self, human_stats):
        """Test interpretation with custom target percentile."""
        interpreter = ScoreInterpreter(human_stats=human_stats)

        context = interpreter.interpret_dimension("burstiness", 8.0, target_percentile=75.0)

        assert context.target_percentile == 75.0
        # Value 8.0 is at p25, target is p75, so gap should be positive
        assert context.gap_to_target > 0

    def test_generate_recommendation(self, human_stats):
        """Test recommendation generation."""
        interpreter = ScoreInterpreter(human_stats=human_stats)

        context = interpreter.interpret_dimension("burstiness", 5.0)  # Low value
        rec = interpreter.generate_recommendation("burstiness", context)

        assert "sentence length variation" in rec.lower() or "percentile" in rec.lower()

    def test_interpretation_text_generation(self, human_stats, ai_stats):
        """Test that interpretation text is generated."""
        interpreter = ScoreInterpreter(human_stats=human_stats, ai_stats=ai_stats)

        context = interpreter.interpret_dimension("burstiness", 12.0)

        assert context.interpretation != ""
        assert "burstiness" in context.interpretation.lower()


class TestDistributionVisualizer:
    """Test DistributionVisualizer class."""

    @pytest.fixture
    def sample_stats(self):
        """Sample distribution statistics."""
        return {
            "dimension_name": "burstiness",
            "percentiles": {"p10": 5.0, "p25": 8.0, "p50": 12.0, "p75": 16.0, "p90": 20.0},
            "min_val": 2.0,
            "max_val": 25.0,
        }

    def test_visualize_position(self, sample_stats):
        """Test basic position visualization."""
        viz = DistributionVisualizer(width=40)

        result = viz.visualize_position(12.0, sample_stats, "Test")

        assert "burstiness" in result
        assert "*" in result  # Position marker
        assert "Test" in result
        assert "12.0" in result or "12.000" in result

    def test_visualize_at_extremes(self, sample_stats):
        """Test visualization at min and max values."""
        viz = DistributionVisualizer(width=40)

        min_viz = viz.visualize_position(2.0, sample_stats)
        max_viz = viz.visualize_position(25.0, sample_stats)

        assert "*" in min_viz
        assert "*" in max_viz

    def test_visualize_comparison(self):
        """Test human vs AI comparison visualization."""
        human_stats = {"percentiles": {"p50": 12.0}, "min_val": 2.0, "max_val": 25.0}
        ai_stats = {"percentiles": {"p50": 7.0}, "min_val": 1.0, "max_val": 15.0}

        viz = DistributionVisualizer(width=50)
        result = viz.visualize_comparison(10.0, human_stats, ai_stats, "burstiness")

        assert "Human" in result
        assert "AI" in result
        assert "burstiness" in result

    def test_custom_width(self):
        """Test custom visualization width."""
        stats = {
            "dimension_name": "test",
            "percentiles": {"p50": 0.5},
            "min_val": 0.0,
            "max_val": 1.0,
        }

        viz_narrow = DistributionVisualizer(width=20)
        viz_wide = DistributionVisualizer(width=80)

        narrow = viz_narrow.visualize_position(0.5, stats)
        wide = viz_wide.visualize_position(0.5, stats)

        # Wide visualization should have more characters
        assert len(wide) > len(narrow)


class TestFormatPercentileReport:
    """Test format_percentile_report function."""

    def test_empty_report(self):
        """Test formatting empty interpretation."""
        interp = ScoreInterpretation()

        report = format_percentile_report(interp)

        assert "PERCENTILE-BASED SCORE INTERPRETATION" in report

    def test_full_report(self):
        """Test formatting complete interpretation."""
        interp = ScoreInterpretation(
            overall_quality_percentile=72.5,
            overall_detection_percentile=25.0,
            recommendations=["Improve burstiness", "Reduce hedging"],
        )
        interp.dimension_contexts["burstiness"] = PercentileContext(
            dimension_name="burstiness",
            raw_value=12.0,
            percentile_human=50.0,
            percentile_ai=85.0,
            interpretation="At median of human writing",
        )

        report = format_percentile_report(interp)

        assert "72.5" in report  # Overall quality
        assert "25.0" in report  # Detection risk
        assert "BURSTINESS" in report
        assert "12.0" in report or "12.00" in report
        assert "50.0" in report  # Human percentile
        assert "Improve burstiness" in report

    def test_report_structure(self):
        """Test report has expected sections."""
        interp = ScoreInterpretation(recommendations=["Test recommendation"])
        interp.dimension_contexts["test"] = PercentileContext(dimension_name="test", raw_value=0.5)

        report = format_percentile_report(interp)

        assert "PER-DIMENSION ANALYSIS" in report
        assert "RECOMMENDATIONS" in report


class TestPercentileEdgeCases:
    """Test edge cases in percentile calculations."""

    def test_identical_percentile_values(self):
        """Test when all percentile values are the same."""
        stats = {
            "percentiles": {"p10": 5.0, "p25": 5.0, "p50": 5.0, "p75": 5.0, "p90": 5.0},
            "min_val": 5.0,
            "max_val": 5.0,
        }

        calc = PercentileCalculator(stats)
        result = calc.calculate_percentile(5.0)

        # Should return something reasonable without crashing
        assert 0 <= result <= 100

    def test_negative_values(self):
        """Test with negative metric values."""
        stats = {"percentiles": {"p50": -0.5}, "min_val": -1.0, "max_val": 0.0}

        calc = PercentileCalculator(stats)
        result = calc.calculate_percentile(-0.5)

        assert 0 <= result <= 100

    def test_very_large_values(self):
        """Test with very large values."""
        stats = {"percentiles": {"p50": 1000000.0}, "min_val": 0.0, "max_val": 2000000.0}

        calc = PercentileCalculator(stats)
        result = calc.calculate_percentile(1500000.0)

        assert 0 <= result <= 100
