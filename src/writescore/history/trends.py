"""
Trend analysis and reporting for score history.

This module provides comprehensive trend analysis, comparison reports,
sparkline visualization, and historical journey reporting.
"""

from typing import Any, Dict, List, Optional, Set

from writescore.history.tracker import HistoricalScore, ScoreHistory

# ============================================================================
# SPARKLINE VISUALIZATION
# ============================================================================


def generate_sparkline(values: List[float], width: int = 8) -> str:
    """
    Generate ASCII sparkline from values.

    Args:
        values: List of numeric values
        width: Maximum width of sparkline (uses unicode blocks)

    Returns:
        String with sparkline visualization

    Example:
        >>> generate_sparkline([1, 2, 4, 6, 8, 7, 6])
        '▁▂▄▆█▇▆'
    """
    if not values or len(values) == 0:
        return ""

    # Sparkline characters from lowest to highest
    chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    # Normalize values to 0-7 range
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return chars[4] * len(values)  # All same value, use middle character

    normalized = []
    for val in values:
        if max_val != min_val:
            norm = (val - min_val) / (max_val - min_val)
            index = min(int(norm * 7), 7)
            normalized.append(chars[index])
        else:
            normalized.append(chars[4])

    # Limit to width if specified
    if width and len(normalized) > width:
        # Sample evenly across the data
        step = len(normalized) / width
        normalized = [normalized[int(i * step)] for i in range(width)]

    return "".join(normalized)


def _calculate_trend_indicator(change: float, threshold: float = 1.0) -> str:
    """Calculate trend indicator arrows."""
    if change > threshold:
        return "↑"
    elif change < -threshold:
        return "↓"
    else:
        return "→"


def _format_score_change(change: float) -> str:
    """Format score change with sign."""
    return f"+{change:.1f}" if change >= 0 else f"{change:.1f}"


# ============================================================================
# DIMENSION TREND ANALYSIS
# ============================================================================


def generate_dimension_trend_report(history: ScoreHistory, top_n: int = 5) -> str:
    """
    Generate comprehensive dimension-level trend report.

    Args:
        history: ScoreHistory object
        top_n: Number of top improvements/declines to show

    Returns:
        Formatted trend report string
    """
    v2_scores = [s for s in history.scores if s.history_version == "2.0"]

    if len(v2_scores) < 2:
        return "⚠ Insufficient data for dimension trends (need 2+ v2.0 scores)"

    output = []
    output.append("")
    output.append("=" * 80)
    output.append(f"DIMENSION TREND ANALYSIS ({len(v2_scores)} iterations tracked)")
    output.append("=" * 80)
    output.append("")

    # Get all dimension trends
    first = v2_scores[0]
    last = v2_scores[-1]

    if not first.dimensions:
        return "⚠ No dimension data available"

    # Calculate changes for all dimensions
    dimension_changes: List[Dict[str, Any]] = []
    for dim_name in first.dimensions:
        if dim_name not in last.dimensions:
            continue

        first_dim = first.dimensions[dim_name]
        last_dim = last.dimensions[dim_name]
        change = last_dim.score - first_dim.score

        dimension_changes.append(
            {
                "name": dim_name,
                "first": first_dim.score,
                "last": last_dim.score,
                "change": change,
                "first_pct": first_dim.percentage,
                "last_pct": last_dim.percentage,
                "pct_change": last_dim.percentage - first_dim.percentage,
                "max_score": first_dim.max_score,
            }
        )

    # Sort by absolute change
    dimension_changes.sort(key=lambda x: abs(x["change"]), reverse=True)

    # Top improvements
    improvements = [d for d in dimension_changes if d["change"] > 0]
    if improvements:
        output.append(f"TOP {min(top_n, len(improvements))} DIMENSION IMPROVEMENTS:")
        output.append("")
        for i, dim in enumerate(improvements[:top_n], 1):
            indicator = _calculate_trend_indicator(dim["change"])
            impact = _get_improvement_impact(dim["change"], dim["max_score"])
            output.append(f"  {i}. {dim['name']}:")
            output.append(
                f"     {dim['first']:.1f} → {dim['last']:.1f}  ({_format_score_change(dim['change'])} pts)  {indicator}  {impact}"
            )
        output.append("")

    # Plateaued dimensions
    plateaued = history.get_plateaued_dimensions(lookback=min(3, len(v2_scores)), threshold=1.0)
    if plateaued:
        output.append(f"PLATEAUED DIMENSIONS (< 1pt change in last {min(3, len(v2_scores))} runs):")
        output.append("")
        for dim_name in plateaued[:top_n]:
            if dim_name in last.dimensions:
                dim_score = last.dimensions[dim_name]
                output.append(
                    f"  - {dim_name}: {dim_score.score:.1f}/{dim_score.max_score} ({dim_score.percentage:.0f}%)"
                )
        output.append("")

    # Declining dimensions
    declines = [d for d in dimension_changes if d["change"] < -1]
    if declines:
        output.append("DECLINING DIMENSIONS (needs attention):")
        output.append("")
        for dim in declines[:top_n]:
            indicator = _calculate_trend_indicator(dim["change"])
            output.append(
                f"  - {dim['name']}: {dim['first']:.1f} → {dim['last']:.1f}  ({_format_score_change(dim['change'])} pts)  {indicator}"
            )
        output.append("")
    else:
        output.append("DECLINING DIMENSIONS: None detected ✓")
        output.append("")

    return "\n".join(output)


def _get_improvement_impact(change: float, max_score: float) -> str:
    """Determine improvement impact level."""
    pct = (abs(change) / max_score) * 100 if max_score > 0 else 0

    if pct >= 50:
        return "EXCELLENT improvement"
    elif pct >= 30:
        return "STRONG improvement"
    elif pct >= 15:
        return "GOOD improvement"
    elif pct >= 5:
        return "FAIR improvement"
    else:
        return "SLIGHT improvement"


# ============================================================================
# AGGREGATE TREND ANALYSIS
# ============================================================================


def generate_aggregate_trend_report(history: ScoreHistory) -> str:
    """
    Generate aggregate score trends (quality and detection).

    Args:
        history: ScoreHistory object

    Returns:
        Formatted aggregate trend report
    """
    if len(history.scores) < 2:
        return ""

    output = []
    output.append("AGGREGATE SCORES:")

    first = history.scores[0]
    last = history.scores[-1]

    qual_change = last.quality_score - first.quality_score
    det_change = last.detection_risk - first.detection_risk

    qual_indicator = _calculate_trend_indicator(qual_change)
    det_indicator = _calculate_trend_indicator(-det_change)  # Lower is better for detection

    qual_trend = "IMPROVING" if qual_change > 1 else "DECLINING" if qual_change < -1 else "STABLE"
    det_trend = "IMPROVING" if det_change < -1 else "WORSENING" if det_change > 1 else "STABLE"

    output.append(
        f"  Quality:   {first.quality_score:.1f} → {last.quality_score:.1f}  ({_format_score_change(qual_change)} pts)  {qual_trend} {qual_indicator}"
    )
    output.append(
        f"  Detection: {first.detection_risk:.1f} → {last.detection_risk:.1f}  ({_format_score_change(det_change)} pts)  {det_trend} {det_indicator}"
    )
    output.append("")

    return "\n".join(output)


# ============================================================================
# TIER TREND ANALYSIS
# ============================================================================


def generate_tier_trend_report(history: ScoreHistory) -> str:
    """
    Generate tier-level trend report.

    Args:
        history: ScoreHistory object

    Returns:
        Formatted tier trend report
    """
    tier_trends = history.get_tier_trends()

    if not tier_trends:
        return ""

    output = []
    output.append("TIER TRENDS:")

    for tier_name, trend in tier_trends.items():
        change = trend["change"]
        indicator = _calculate_trend_indicator(change)
        trend_text = trend["trend"]

        output.append(
            f"  {tier_name}:  {trend['first']:.1f} → {trend['last']:.1f}  "
            + f"({_format_score_change(change)} pts / {trend['max']} max)  {trend_text} {indicator}"
        )

    output.append("")
    return "\n".join(output)


# ============================================================================
# ITERATION COMPARISON
# ============================================================================


def generate_comparison_report(history: ScoreHistory, idx1: int, idx2: int) -> str:
    """
    Generate side-by-side comparison of two iterations.

    Args:
        history: ScoreHistory object
        idx1: First iteration index (0-based)
        idx2: Second iteration index (0-based)

    Returns:
        Formatted comparison report
    """
    if idx1 < 0 or idx1 >= len(history.scores) or idx2 < 0 or idx2 >= len(history.scores):
        return "Error: Invalid iteration indices"

    score1 = history.scores[idx1]
    score2 = history.scores[idx2]

    output = []
    output.append("")
    output.append("=" * 80)
    output.append(f"ITERATION COMPARISON: Iteration {idx1+1} vs. Iteration {idx2+1}")
    output.append("=" * 80)
    output.append("")

    # Show metadata comparison
    mode1 = (
        score1.analysis_mode.upper()
        if hasattr(score1, "analysis_mode") and score1.analysis_mode
        else "N/A"
    )
    mode2 = (
        score2.analysis_mode.upper()
        if hasattr(score2, "analysis_mode") and score2.analysis_mode
        else "N/A"
    )
    time1 = (
        f"{score1.analysis_time_seconds:.1f}s"
        if hasattr(score1, "analysis_time_seconds") and score1.analysis_time_seconds > 0
        else "N/A"
    )
    time2 = (
        f"{score2.analysis_time_seconds:.1f}s"
        if hasattr(score2, "analysis_time_seconds") and score2.analysis_time_seconds > 0
        else "N/A"
    )

    output.append(f"Iteration {idx1+1}: {score1.timestamp[:10]} | Mode: {mode1} | Time: {time1}")
    output.append(f"Iteration {idx2+1}: {score2.timestamp[:10]} | Mode: {mode2} | Time: {time2}")
    output.append("")
    output.append(
        f"                               Iteration {idx1+1:<7} Iteration {idx2:<7} Change      Impact"
    )
    output.append("-" * 80)

    # Aggregate scores
    output.append("AGGREGATE SCORES:")
    qual_change = score2.quality_score - score1.quality_score
    det_change = score2.detection_risk - score1.detection_risk

    output.append(
        f"  Quality Score                {score1.quality_score:>7.1f}        {score2.quality_score:>7.1f}      {qual_change:>+6.1f}    {_get_comparison_impact(qual_change, 'quality')}"
    )
    output.append(
        f"  Detection Risk               {score1.detection_risk:>7.1f}        {score2.detection_risk:>7.1f}      {det_change:>+6.1f}    {_get_comparison_impact(-det_change, 'detection')}"
    )
    output.append("")

    # Only compare dimensions if both are v2.0
    if (
        score1.history_version == "2.0"
        and score2.history_version == "2.0"
        and score1.dimensions
        and score2.dimensions
    ):
        # Tier comparison
        output.append("TIER SCORES:")
        for tier_num in [1, 2, 3, 4]:
            attr = f"tier{tier_num}_score"
            val1 = getattr(score1, attr, 0.0)
            val2 = getattr(score2, attr, 0.0)
            change = val2 - val1
            tier_names = {
                1: "Tier 1 - Advanced Detection",
                2: "Tier 2 - Core Patterns",
                3: "Tier 3 - Supporting Indicators",
                4: "Tier 4 - Advanced Structural",
            }
            output.append(
                f"  {tier_names[tier_num]:<26} {val1:>7.1f}        {val2:>7.1f}      {change:>+6.1f}    {_get_comparison_impact(change, 'tier')}"
            )
        output.append("")

        # Significant dimension changes (> 2pts)
        significant_changes: List[Dict[str, Any]] = []
        for dim_name in score1.dimensions:
            if dim_name not in score2.dimensions:
                continue

            dim1 = score1.dimensions[dim_name]
            dim2 = score2.dimensions[dim_name]
            change = dim2.score - dim1.score

            if abs(change) >= 2.0:
                significant_changes.append(
                    {
                        "name": dim_name,
                        "val1": dim1.score,
                        "val2": dim2.score,
                        "change": change,
                        "max": dim1.max_score,
                    }
                )

        if significant_changes:
            significant_changes.sort(key=lambda x: abs(x["change"]), reverse=True)
            output.append("SIGNIFICANT DIMENSION CHANGES (±2pts):")
            for dim in significant_changes:
                impact = _get_improvement_impact(abs(dim["change"]), dim["max"])
                indicator = "⭐" if abs(dim["change"]) >= 4 else ""
                output.append(
                    f"  {dim['name']:<35} {dim['val1']:>5.1f}          {dim['val2']:>5.1f}      {dim['change']:>+6.1f}    {impact} {indicator}"
                )
            output.append("")

    # Key insights
    output.append("-" * 80)
    output.append("KEY INSIGHTS:")
    output.append("")

    insights = _generate_comparison_insights(score1, score2)
    for insight in insights:
        output.append(insight)

    return "\n".join(output)


def _get_comparison_impact(change: float, context: str) -> str:
    """Get impact assessment for comparison."""
    abs_change = abs(change)

    if context == "quality":
        if abs_change >= 10:
            return "EXCELLENT"
        elif abs_change >= 5:
            return "STRONG"
        elif abs_change >= 2:
            return "GOOD"
        elif abs_change >= 1:
            return "FAIR"
        else:
            return "SLIGHT"
    elif context == "detection":
        if abs_change >= 10:
            return "EXCELLENT"
        elif abs_change >= 5:
            return "STRONG"
        elif abs_change >= 2:
            return "GOOD"
        else:
            return "SLIGHT"
    elif context == "tier":
        if abs_change >= 5:
            return "STRONG"
        elif abs_change >= 2:
            return "GOOD"
        elif abs_change >= 1:
            return "FAIR"
        else:
            return "SLIGHT"

    return ""


def _generate_comparison_insights(score1: HistoricalScore, score2: HistoricalScore) -> List[str]:
    """Generate insights from comparison."""
    insights = []

    qual_change = score2.quality_score - score1.quality_score
    det_change = score2.detection_risk - score1.detection_risk

    # Overall assessment
    if qual_change > 5 and det_change < -5:
        insights.append("✅ EXCELLENT PROGRESS: Both quality and detection significantly improved")
    elif qual_change > 2 and det_change < -2:
        insights.append("✅ GOOD PROGRESS: Both metrics improved")
    elif qual_change < -2 or det_change > 5:
        insights.append("⚠ REGRESSION DETECTED: Scores declined")

    # Dimension-specific insights (v2.0 only)
    if (
        score1.history_version == "2.0"
        and score2.history_version == "2.0"
        and score1.dimensions
        and score2.dimensions
    ):
        improvements = []
        declines = []

        for dim_name in score1.dimensions:
            if dim_name not in score2.dimensions:
                continue

            change = score2.dimensions[dim_name].score - score1.dimensions[dim_name].score
            if change >= 4:
                improvements.append((dim_name, change))
            elif change <= -2:
                declines.append((dim_name, change))

        if improvements:
            improvements.sort(key=lambda x: x[1], reverse=True)
            insights.append("")
            insights.append("✅ TOP 3 IMPROVEMENTS:")
            for i, (name, change) in enumerate(improvements[:3], 1):
                insights.append(f"  {i}. {name} ({change:+.1f} pts)")

        if declines:
            declines.sort(key=lambda x: x[1])
            insights.append("")
            insights.append("⚠ DECLINES:")
            for name, change in declines[:3]:
                insights.append(f"  - {name} ({change:+.1f} pts)")

    # Add notes comparison
    if score1.notes or score2.notes:
        insights.append("")
        if score1.notes:
            insights.append(f"Iteration {1} notes: {score1.notes}")
        if score2.notes:
            insights.append(f"Iteration {2} notes: {score2.notes}")

    return insights


# ============================================================================
# COMPREHENSIVE HISTORY REPORT
# ============================================================================


def generate_full_history_report(history: ScoreHistory) -> str:
    """
    Generate complete optimization journey report.

    Args:
        history: ScoreHistory object with complete history

    Returns:
        Comprehensive formatted report
    """
    if not history.scores:
        return "No history data available"

    output = []
    output.append("")
    output.append("=" * 80)
    output.append("COMPLETE OPTIMIZATION JOURNEY")
    output.append("=" * 80)
    output.append(f"Document: {history.file_path}")
    output.append(
        f"Iterations: {len(history.scores)} ({history.scores[0].timestamp[:10]} to {history.scores[-1].timestamp[:10]})"
    )
    output.append("=" * 80)
    output.append("")

    # Aggregate trends
    output.append(generate_aggregate_trend_report(history))

    # Tier trends (if v2.0 data available)
    v2_scores = [s for s in history.scores if s.history_version == "2.0"]
    if v2_scores:
        output.append(generate_tier_trend_report(history))

    # Iteration-by-iteration summary
    output.append("ITERATION SUMMARY:")
    output.append("-" * 80)

    for i, score in enumerate(history.scores, 1):
        output.append("")
        output.append(f"ITERATION {i}: {score.notes or 'No notes'}")
        output.append(f"Timestamp:     {score.timestamp}")
        output.append(
            f"Mode:          {score.analysis_mode.upper() if hasattr(score, 'analysis_mode') and score.analysis_mode else 'N/A'}"
        )
        if hasattr(score, "analysis_time_seconds") and score.analysis_time_seconds > 0:
            output.append(f"Analysis Time: {score.analysis_time_seconds:.1f}s")
        output.append(
            f"Quality:       {score.quality_score:.1f} / 100  ({score.quality_interpretation})"
        )
        output.append(
            f"Detection:     {score.detection_risk:.1f} / 100  ({score.detection_interpretation})"
        )
        output.append(f"Total Words:   {score.total_words}")
        if score.total_sentences > 0:
            output.append(f"Sentences:     {score.total_sentences}")
        if score.total_paragraphs > 0:
            output.append(f"Paragraphs:    {score.total_paragraphs}")

        if i > 1:
            prev = history.scores[i - 2]
            qual_change = score.quality_score - prev.quality_score
            det_change = score.detection_risk - prev.detection_risk
            output.append(
                f"Changes:       Quality {_format_score_change(qual_change)} pts, "
                + f"Detection {_format_score_change(det_change)} pts"
            )

        if score.history_version == "2.0" and score.dimensions:
            output.append("Version:       v2.0 (comprehensive tracking)")
            output.append(
                f"Tiers:         T1={score.tier1_score:.1f}/70  T2={score.tier2_score:.1f}/74  "
                + f"T3={score.tier3_score:.1f}/46  T4={score.tier4_score:.1f}/10"
            )

    output.append("")
    output.append("-" * 80)

    # Dimension trends (if v2.0 data)
    if len(v2_scores) >= 2:
        output.append("")
        output.append(generate_dimension_trend_report(history, top_n=5))

    # Sparkline visualization
    if len(history.scores) >= 3:
        output.append("")
        output.append("SCORE TRENDS (Sparkline View):")
        output.append("-" * 80)

        qual_values = [s.quality_score for s in history.scores]
        det_values = [s.detection_risk for s in history.scores]

        qual_spark = generate_sparkline(qual_values)
        det_spark = generate_sparkline(det_values)

        output.append(
            f"Quality:       {qual_spark}  {qual_values[0]:.0f}→{qual_values[-1]:.0f} "
            + f"({_format_score_change(qual_values[-1] - qual_values[0])} pts)"
        )
        output.append(
            f"Detection:     {det_spark}  {det_values[0]:.0f}→{det_values[-1]:.0f} "
            + f"({_format_score_change(det_values[-1] - det_values[0])} pts)"
        )

        if v2_scores and len(v2_scores) >= 3:
            output.append("")
            # Show sparklines for top changing dimensions
            first_v2 = v2_scores[0]
            v2_scores[-1]

            dim_changes = []
            for dim_name in first_v2.dimensions:
                if all(dim_name in s.dimensions for s in v2_scores):
                    values = [s.dimensions[dim_name].score for s in v2_scores]
                    change = values[-1] - values[0]
                    if abs(change) >= 2:
                        dim_changes.append((dim_name, values, change))

            dim_changes.sort(key=lambda x: abs(x[2]), reverse=True)

            for dim_name, values, change in dim_changes[:5]:
                spark = generate_sparkline(values)
                indicator = _calculate_trend_indicator(change)
                output.append(
                    f"{dim_name:<30} {spark}  {values[0]:.1f}→{values[-1]:.1f} "
                    + f"({_format_score_change(change)}) {indicator}"
                )

        output.append("")

    # Final assessment
    output.append("=" * 80)
    output.append("FINAL ASSESSMENT")
    output.append("=" * 80)
    output.append("")

    first = history.scores[0]
    last = history.scores[-1]

    qual_total = last.quality_score - first.quality_score
    det_total = last.detection_risk - first.detection_risk

    output.append("Overall Progress:")
    output.append(
        f"  Quality:       {first.quality_score:.1f} → {last.quality_score:.1f}  "
        + f"({_format_score_change(qual_total)} pts, {(qual_total/first.quality_score*100) if first.quality_score > 0 else 0:+.0f}% improvement)"
    )
    output.append(
        f"  Detection:     {first.detection_risk:.1f} → {last.detection_risk:.1f}  "
        + f"({_format_score_change(det_total)} pts, {(det_total/first.detection_risk*100) if first.detection_risk > 0 else 0:+.0f}% risk reduction)"
    )
    output.append("")

    # Publication readiness
    qual_ready = last.quality_score >= 85
    det_ready = last.detection_risk <= 30

    output.append("Publication Readiness:")
    output.append(
        f"  Quality target (≥85):     {'✓ MET' if qual_ready else f'✗ NOT MET (need {85 - last.quality_score:+.1f} pts)'} ({last.quality_score:.1f})"
    )
    output.append(
        f"  Detection target (≤30):   {'✓ MET' if det_ready else f'⚠ NOT MET ({last.detection_risk:.1f})'} ({last.detection_risk:.1f})"
    )
    output.append("")

    if qual_ready and det_ready:
        output.append("Status: PUBLICATION READY ✓")
    elif qual_ready or det_ready:
        output.append("Status: NEARLY READY - Minor improvements needed")
    else:
        output.append("Status: IN PROGRESS - Continue optimization")

    output.append("")

    return "\n".join(output)


# ============================================================================
# RAW METRIC TREND VISUALIZATION
# ============================================================================


def generate_raw_metric_trends(
    history: ScoreHistory, metric_names: Optional[List[str]] = None
) -> str:
    """
    Generate raw metric trend visualization.

    Args:
        history: ScoreHistory object
        metric_names: Specific metrics to show (None = show all)

    Returns:
        Formatted raw metric trends
    """
    v2_scores = [s for s in history.scores if s.history_version == "2.0" and s.raw_metrics]

    if len(v2_scores) < 2:
        return "⚠ Insufficient v2.0 data for raw metric trends"

    output = []
    output.append("")
    output.append("=" * 80)
    output.append(f"RAW METRIC TRENDS ({len(v2_scores)} iterations)")
    output.append("=" * 80)
    output.append("")

    # Get all available metrics
    all_metrics: Set[str] = set()
    for score in v2_scores:
        all_metrics.update(score.raw_metrics.keys())

    # Filter to requested metrics
    if metric_names:
        metrics_to_show = [m for m in metric_names if m in all_metrics]
    else:
        metrics_to_show = sorted(all_metrics)

    for metric_name in metrics_to_show:
        # Get values across iterations
        values = []
        for score in v2_scores:
            val = score.raw_metrics.get(metric_name, 0.0)
            values.append(val)

        if not values:
            continue

        # Generate sparkline
        spark = generate_sparkline(values)

        # Calculate change
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        pct_change = (change / first_val * 100) if first_val != 0 else 0

        # Trend indicator
        indicator = _calculate_trend_indicator(change, threshold=first_val * 0.1)  # 10% threshold

        output.append(f"{metric_name}:")
        output.append(
            f"  {spark}  {first_val:.2f} → {last_val:.2f}  "
            + f"({_format_score_change(change)}, {pct_change:+.0f}%)  {indicator}"
        )
        output.append("")

    return "\n".join(output)
