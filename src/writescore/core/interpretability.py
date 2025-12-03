"""
Score interpretability features for percentile-anchored parameters.

This module provides tools for:
1. Mapping raw scores to percentile rankings
2. Generating contextual recommendations with percentile information
3. Creating ASCII visualizations of score positions on distributions

Created in Story 2.5 Task 7 to enhance user understanding of scores.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PercentileContext:
    """
    Percentile-based interpretation of a dimension score.

    Attributes:
        dimension_name: Name of the dimension
        raw_value: The raw metric value
        percentile_human: Percentile rank relative to human distribution (0-100)
        percentile_ai: Percentile rank relative to AI distribution (0-100)
        percentile_combined: Percentile rank relative to combined distribution
        interpretation: Human-readable interpretation
        target_percentile: Target percentile for "human-like" writing
        gap_to_target: Distance from current to target percentile
    """

    dimension_name: str
    raw_value: float
    percentile_human: Optional[float] = None
    percentile_ai: Optional[float] = None
    percentile_combined: Optional[float] = None
    interpretation: str = ""
    target_percentile: float = 50.0  # Default: median of human distribution
    gap_to_target: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension_name": self.dimension_name,
            "raw_value": round(self.raw_value, 4),
            "percentile_human": round(self.percentile_human, 1) if self.percentile_human else None,
            "percentile_ai": round(self.percentile_ai, 1) if self.percentile_ai else None,
            "percentile_combined": round(self.percentile_combined, 1)
            if self.percentile_combined
            else None,
            "interpretation": self.interpretation,
            "target_percentile": self.target_percentile,
            "gap_to_target": round(self.gap_to_target, 1),
        }


@dataclass
class ScoreInterpretation:
    """
    Complete interpretation of an analysis result with percentile context.

    Attributes:
        overall_quality_percentile: Where overall quality falls in distribution
        overall_detection_percentile: Where detection risk falls in distribution
        dimension_contexts: Per-dimension percentile contexts
        recommendations: Prioritized recommendations with percentile context
    """

    overall_quality_percentile: Optional[float] = None
    overall_detection_percentile: Optional[float] = None
    dimension_contexts: Dict[str, PercentileContext] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_quality_percentile": self.overall_quality_percentile,
            "overall_detection_percentile": self.overall_detection_percentile,
            "dimension_contexts": {
                name: ctx.to_dict() for name, ctx in self.dimension_contexts.items()
            },
            "recommendations": self.recommendations,
        }


class PercentileCalculator:
    """
    Calculates percentile rankings for raw metric values.

    Uses linear interpolation between stored percentiles to estimate
    the percentile rank of any given value.
    """

    def __init__(self, distribution_stats: Dict[str, Any]):
        """
        Initialize with distribution statistics.

        Args:
            distribution_stats: Dictionary with percentile data, e.g.:
                {
                    "percentiles": {"p10": 0.5, "p25": 0.6, "p50": 0.7, "p75": 0.8, "p90": 0.9},
                    "min_val": 0.3,
                    "max_val": 1.0
                }
        """
        self.stats = distribution_stats
        self.percentiles = distribution_stats.get("percentiles", {})
        self.min_val = distribution_stats.get("min_val", 0.0)
        self.max_val = distribution_stats.get("max_val", 1.0)

    def calculate_percentile(self, value: float) -> float:
        """
        Calculate the percentile rank for a given value.

        Uses linear interpolation between known percentile points.

        Args:
            value: Raw metric value

        Returns:
            Estimated percentile (0-100)
        """
        if not self.percentiles:
            return 50.0  # Default to median if no data

        # Build sorted list of (percentile, value) pairs
        points = []

        # Add min as p0 and max as p100
        points.append((0, self.min_val))

        for pname, pval in sorted(self.percentiles.items()):
            # Extract numeric percentile from name like "p10", "p25", etc.
            try:
                p = int(pname[1:])  # "p10" -> 10
                points.append((p, pval))
            except (ValueError, IndexError):
                continue

        points.append((100, self.max_val))

        # Sort by value for interpolation
        points.sort(key=lambda x: x[1])

        # Handle edge cases
        if value <= points[0][1]:
            return float(points[0][0])
        if value >= points[-1][1]:
            return float(points[-1][0])

        # Linear interpolation
        for i in range(len(points) - 1):
            p1, v1 = points[i]
            p2, v2 = points[i + 1]

            if v1 <= value <= v2:
                if v2 == v1:  # Avoid division by zero
                    return float(p1)
                # Interpolate percentile
                fraction = (value - v1) / (v2 - v1)
                return float(p1 + fraction * (p2 - p1))

        return 50.0  # Fallback


class ScoreInterpreter:
    """
    Interprets analysis scores with percentile context.

    Provides human-readable interpretations and recommendations
    based on where scores fall in the distribution.
    """

    def __init__(
        self,
        human_stats: Optional[Dict[str, Dict[str, Any]]] = None,
        ai_stats: Optional[Dict[str, Dict[str, Any]]] = None,
        combined_stats: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Initialize with distribution statistics.

        Args:
            human_stats: Per-dimension statistics from human samples
            ai_stats: Per-dimension statistics from AI samples
            combined_stats: Per-dimension statistics from all samples
        """
        self.human_stats = human_stats or {}
        self.ai_stats = ai_stats or {}
        self.combined_stats = combined_stats or {}

    def interpret_dimension(
        self, dimension_name: str, raw_value: float, target_percentile: float = 50.0
    ) -> PercentileContext:
        """
        Generate percentile-based interpretation for a dimension.

        Args:
            dimension_name: Name of the dimension
            raw_value: Raw metric value from analysis
            target_percentile: Target percentile for "good" writing

        Returns:
            PercentileContext with interpretation
        """
        context = PercentileContext(
            dimension_name=dimension_name, raw_value=raw_value, target_percentile=target_percentile
        )

        # Calculate percentiles for each distribution
        if dimension_name in self.human_stats:
            calc = PercentileCalculator(self.human_stats[dimension_name])
            context.percentile_human = calc.calculate_percentile(raw_value)

        if dimension_name in self.ai_stats:
            calc = PercentileCalculator(self.ai_stats[dimension_name])
            context.percentile_ai = calc.calculate_percentile(raw_value)

        if dimension_name in self.combined_stats:
            calc = PercentileCalculator(self.combined_stats[dimension_name])
            context.percentile_combined = calc.calculate_percentile(raw_value)

        # Calculate gap to target (using human percentile as primary)
        if context.percentile_human is not None:
            context.gap_to_target = target_percentile - context.percentile_human

        # Generate interpretation
        context.interpretation = self._generate_interpretation(context)

        return context

    def _generate_interpretation(self, context: PercentileContext) -> str:
        """Generate human-readable interpretation."""
        parts = []

        if context.percentile_human is not None:
            # Determine quality descriptor
            p = context.percentile_human
            if p >= 40 and p <= 60:
                quality = "typical of"
            elif p >= 25 and p < 40:
                quality = "below average for"
            elif p > 60 and p <= 75:
                quality = "above average for"
            elif p < 25:
                quality = "unusually low for"
            else:  # > 75
                quality = "unusually high for"

            parts.append(
                f"{context.dimension_name}: {context.raw_value:.2f} is at "
                f"{context.percentile_human:.0f}th percentile ({quality} human writing)"
            )

        if context.percentile_ai is not None and context.percentile_human is not None:
            # Compare to AI distribution
            diff = context.percentile_human - context.percentile_ai
            if abs(diff) > 20:
                if diff > 0:
                    parts.append("More human-like than AI on this dimension")
                else:
                    parts.append("More AI-like than human on this dimension")

        if abs(context.gap_to_target) > 10:
            direction = "increase" if context.gap_to_target > 0 else "decrease"
            parts.append(
                f"Target: {direction} to reach {context.target_percentile:.0f}th percentile"
            )

        return "; ".join(parts) if parts else "No interpretation available"

    def generate_recommendation(self, dimension_name: str, context: PercentileContext) -> str:
        """
        Generate a recommendation with percentile context.

        Args:
            dimension_name: Name of the dimension
            context: PercentileContext for this dimension

        Returns:
            Recommendation string with percentile information
        """
        if context.percentile_human is None:
            return f"Improve {dimension_name} (no percentile data available)"

        p = context.percentile_human
        target = context.target_percentile

        # Dimension-specific recommendations
        recommendations = {
            "burstiness": {
                "low": "Add more sentence length variation (currently too uniform)",
                "high": "Smooth out extreme sentence length variations",
                "target": "Sentence length variation is well-balanced",
            },
            "lexical": {
                "low": "Increase vocabulary diversity with more varied word choices",
                "high": "Consider simplifying some vocabulary for readability",
                "target": "Vocabulary diversity is appropriate",
            },
            "sentiment": {
                "low": "Add more emotional variation and tonal shifts",
                "high": "Tone down extreme emotional swings",
                "target": "Emotional variation is natural",
            },
            "voice": {
                "low": "Use more active voice constructions",
                "high": "Balance active voice with some passive where appropriate",
                "target": "Voice balance is good",
            },
            "readability": {
                "low": "Simplify sentence structure for better readability",
                "high": "Add some complexity to avoid overly simple prose",
                "target": "Readability level is appropriate",
            },
            "transition_marker": {
                "low": "Add more transitional phrases to improve flow",
                "high": "Reduce excessive transition markers",
                "target": "Transition usage is natural",
            },
        }

        dim_recs = recommendations.get(
            dimension_name,
            {
                "low": f"Increase {dimension_name} metric",
                "high": f"Decrease {dimension_name} metric",
                "target": f"{dimension_name} is at target",
            },
        )

        # Determine which recommendation to use
        if abs(p - target) <= 10:
            rec_type = "target"
        elif p < target:
            rec_type = "low"
        else:
            rec_type = "high"

        base_rec = dim_recs[rec_type]

        # Add percentile context
        if rec_type != "target":
            return (
                f"{base_rec} - currently at {p:.0f}th percentile of human writing "
                f"(target: {target:.0f}th)"
            )
        else:
            return f"{base_rec} ({p:.0f}th percentile)"


class DistributionVisualizer:
    """
    Creates ASCII visualizations of score distributions.
    """

    def __init__(self, width: int = 60):
        """
        Initialize visualizer.

        Args:
            width: Width of ASCII visualization in characters
        """
        self.width = width

    def visualize_position(
        self, value: float, stats: Dict[str, Any], label: str = "Your score"
    ) -> str:
        """
        Create ASCII visualization showing position on distribution.

        Args:
            value: The value to position
            stats: Distribution statistics with percentiles
            label: Label for the marker

        Returns:
            ASCII visualization string
        """
        percentiles = stats.get("percentiles", {})
        min_val = stats.get("min_val", 0.0)
        max_val = stats.get("max_val", 1.0)

        # Avoid division by zero
        range_val = max_val - min_val
        if range_val == 0:
            range_val = 1.0

        # Calculate position (0 to width)
        pos = int((value - min_val) / range_val * self.width)
        pos = max(0, min(self.width - 1, pos))

        # Build visualization
        lines = []

        # Scale line with percentile markers
        scale = ["-"] * self.width
        markers = []

        for pname, pval in percentiles.items():
            p_pos = int((pval - min_val) / range_val * self.width)
            p_pos = max(0, min(self.width - 1, p_pos))
            if 0 <= p_pos < self.width:
                scale[p_pos] = "|"
                markers.append((p_pos, pname))

        # Add current value marker
        scale[pos] = "*"

        # Header
        lines.append(f"Distribution: {stats.get('dimension_name', 'Unknown')}")
        lines.append("=" * self.width)

        # Main scale
        lines.append("".join(scale))

        # Position indicator line
        indicator = [" "] * self.width
        indicator[pos] = "^"
        lines.append("".join(indicator))

        # Value label
        value_label = f"{label}: {value:.3f}"
        label_start = max(0, pos - len(value_label) // 2)
        lines.append(" " * label_start + value_label)

        # Percentile labels (compact)
        p_labels = []
        for _p_pos, pname in sorted(markers):
            pval = percentiles[pname]
            p_labels.append(f"{pname}={pval:.2f}")
        lines.append("Percentiles: " + ", ".join(p_labels))

        # Range
        lines.append(f"Range: [{min_val:.3f}, {max_val:.3f}]")

        return "\n".join(lines)

    def visualize_comparison(
        self,
        value: float,
        human_stats: Dict[str, Any],
        ai_stats: Dict[str, Any],
        dimension_name: str,
    ) -> str:
        """
        Create side-by-side comparison of human vs AI distributions.

        Args:
            value: The value to position
            human_stats: Human distribution statistics
            ai_stats: AI distribution statistics
            dimension_name: Name of the dimension

        Returns:
            ASCII visualization string
        """
        lines = []
        lines.append(f"Distribution Comparison: {dimension_name}")
        lines.append("=" * self.width)

        # Calculate percentile in each distribution
        human_calc = PercentileCalculator(human_stats)
        ai_calc = PercentileCalculator(ai_stats)

        human_pct = human_calc.calculate_percentile(value)
        ai_pct = ai_calc.calculate_percentile(value)

        # Create bar representations
        human_bar = self._create_percentile_bar(human_pct, "Human")
        ai_bar = self._create_percentile_bar(ai_pct, "AI")

        lines.append(human_bar)
        lines.append(ai_bar)
        lines.append("")
        lines.append(f"Your value: {value:.3f}")
        lines.append(f"Human percentile: {human_pct:.1f}%")
        lines.append(f"AI percentile: {ai_pct:.1f}%")

        # Interpretation
        if human_pct > ai_pct + 10:
            lines.append("=> More characteristic of human writing")
        elif ai_pct > human_pct + 10:
            lines.append("=> More characteristic of AI writing")
        else:
            lines.append("=> Similar to both human and AI distributions")

        return "\n".join(lines)

    def _create_percentile_bar(self, percentile: float, label: str) -> str:
        """Create a single percentile bar."""
        bar_width = self.width - 10  # Leave room for label
        filled = int(percentile / 100 * bar_width)
        filled = max(0, min(bar_width, filled))

        bar = "[" + "#" * filled + "-" * (bar_width - filled) + "]"
        return f"{label:6s} {bar} {percentile:5.1f}%"


def format_percentile_report(
    interpretation: ScoreInterpretation, include_visualizations: bool = False
) -> str:
    """
    Format a complete percentile-based interpretation report.

    Args:
        interpretation: ScoreInterpretation with all contexts
        include_visualizations: Whether to include ASCII visualizations

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("PERCENTILE-BASED SCORE INTERPRETATION")
    lines.append("=" * 70)

    if interpretation.overall_quality_percentile:
        lines.append(
            f"\nOverall Quality: {interpretation.overall_quality_percentile:.1f}th percentile"
        )
    if interpretation.overall_detection_percentile:
        lines.append(
            f"Detection Risk: {interpretation.overall_detection_percentile:.1f}th percentile"
        )

    lines.append("\nPER-DIMENSION ANALYSIS")
    lines.append("-" * 40)

    for dim_name, context in sorted(interpretation.dimension_contexts.items()):
        lines.append(f"\n{dim_name.upper()}")
        lines.append(f"  Raw value: {context.raw_value:.4f}")

        if context.percentile_human is not None:
            lines.append(f"  Human percentile: {context.percentile_human:.1f}%")
        if context.percentile_ai is not None:
            lines.append(f"  AI percentile: {context.percentile_ai:.1f}%")
        if context.interpretation:
            lines.append(f"  {context.interpretation}")

    if interpretation.recommendations:
        lines.append("\nRECOMMENDATIONS")
        lines.append("-" * 40)
        for i, rec in enumerate(interpretation.recommendations, 1):
            lines.append(f"  {i}. {rec}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)
