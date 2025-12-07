"""
Dual score calculation module - Registry-based implementation.

Calculates Detection Risk (0-100, lower=better) and Quality Score (0-100, higher=better)
by dynamically discovering and scoring dimensions via DimensionRegistry.

This refactored version replaces 800+ lines of hardcoded dimension logic with a
registry-based approach that automatically incorporates new dimensions without
core algorithm modifications.

Refactored in Story 1.15 from monolithic 847-line implementation to registry-based
~180-line implementation (79% reduction).

Research Sources:
- GPTZero methodology (perplexity & burstiness)
- Originality.AI pattern recognition
- Academic NLP studies on AI detection
- Stanford research on demographic bias
- MIT/Northeastern research on syntactic templates
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import AnalysisResults
from writescore.core.weight_mediator import WeightMediator
from writescore.dimensions.base_strategy import DimensionTier
from writescore.scoring.dual_score import (
    DualScore,
    ImprovementAction,
    ScoreCategory,
    ScoreDimension,
)
from writescore.scoring.score_normalization import get_normalizer

logger = logging.getLogger(__name__)


def calculate_dual_score(
    results: AnalysisResults,
    detection_target: float = 30.0,
    quality_target: float = 85.0,
    config: Optional[Any] = None,
) -> DualScore:
    """
    Calculate dual scores using DimensionRegistry for dynamic dimension discovery.

    This registry-based implementation:
    1. Discovers all registered dimensions via DimensionRegistry
    2. Extracts dimension metrics from results.dimension_results
    3. Calls dimension.calculate_score() for each dimension
    4. Applies z-score normalization if enabled (Story 2.4.1, AC7)
    5. Groups dimensions by tier (ADVANCED/CORE/SUPPORTING/STRUCTURAL)
    6. Calculates Detection Risk and Quality Score from tier totals
    7. Generates recommendations via dimension.get_recommendations()

    Args:
        results: AnalysisResults containing dimension_results dict
        detection_target: Target detection risk (default 30 = low risk)
        quality_target: Target quality score (default 85 = excellent)
        config: Optional AnalysisConfig (for normalization settings)

    Returns:
        DualScore with comprehensive breakdown and optimization path

    Backward Compatibility:
        Returns identical DualScore structure as original implementation.
        Existing code using DualScore fields will work unchanged.
        Config parameter is optional for backward compatibility.
    """
    timestamp = datetime.now().isoformat()

    # PHASE 1: Discover and score all dimensions via registry
    dimension_scores = _build_dimension_scores(results, config)

    # PHASE 2: Group dimensions by tier for category scoring
    categories = _build_score_categories(dimension_scores)

    # PHASE 3: Calculate overall detection risk and quality score
    detection_risk, quality_score = _calculate_overall_scores(categories)

    # PHASE 4: Generate improvement recommendations
    improvements = _generate_improvements(dimension_scores, results)

    # PHASE 5: Build optimization path (sorted by ROI)
    path = _build_optimization_path(
        improvements, detection_risk, detection_target, quality_score, quality_target
    )

    # PHASE 6: Calculate interpretations and effort
    detection_interp = _interpret_detection(detection_risk)
    quality_interp = _interpret_quality(quality_score)
    # Clamp gaps to 0 when scores exceed targets (above target = no gap)
    detection_gap = max(0.0, detection_risk - detection_target)
    quality_gap = max(0.0, quality_target - quality_score)
    effort = _estimate_overall_effort(quality_gap)

    return DualScore(
        detection_risk=round(detection_risk, 1),
        quality_score=round(quality_score, 1),
        detection_interpretation=detection_interp,
        quality_interpretation=quality_interp,
        detection_target=detection_target,
        quality_target=quality_target,
        detection_gap=round(detection_gap, 1),
        quality_gap=round(quality_gap, 1),
        categories=categories,
        improvements=improvements,
        path_to_target=path,
        estimated_effort=effort,
        timestamp=timestamp,
        file_path=results.file_path,
        total_words=results.total_words,
    )


def _build_dimension_scores(
    results: AnalysisResults, config: Optional[Any] = None
) -> List[Tuple[Any, ScoreDimension]]:
    """
    Build ScoreDimension objects for all registered dimensions.

    Args:
        results: AnalysisResults with dimension_results dict
        config: Optional AnalysisConfig (for normalization settings)

    Returns:
        List of (dimension_instance, ScoreDimension) tuples

    Handles:
        - Missing dimensions (not loaded in selective loading mode)
        - Dimension errors (stored as {'available': False, 'error': '...'})
        - Score normalization (z-score if enabled in config)
        - Ensures 0-100 range
    """
    dimension_scores = []

    # Check if normalization is enabled
    enable_normalization = getattr(config, "enable_score_normalization", True) if config else True

    # Get normalizer (only loads stats if normalization enabled)
    normalizer = get_normalizer(enabled=enable_normalization)

    # Get all registered dimensions
    dimensions = DimensionRegistry.get_all()

    # STORY 2.4.1 Task 10.5: Ensure weights sum to exactly 100.0
    # Use WeightMediator to validate and rescale weights if needed
    mediator = WeightMediator(tolerance=0.1)
    effective_weights = {}  # Stores actual weights to use (rescaled or original)

    if not mediator.is_valid:
        # Weights don't sum to 100.0, get rescaling suggestions
        rescaled_weights = mediator.suggest_rebalancing()
        total_before = mediator.get_total_weight()

        # Store rescaled weights in effective_weights dict
        # Note: dimension.weight property remains unchanged (read-only)
        for dim in dimensions:
            if dim.dimension_name in rescaled_weights:
                effective_weights[dim.dimension_name] = rescaled_weights[dim.dimension_name]
                logger.debug(
                    f"Rescaled {dim.dimension_name}: {dim.weight:.2f} → {effective_weights[dim.dimension_name]:.10f}"
                )
            else:
                effective_weights[dim.dimension_name] = dim.weight

        logger.info(
            f"Weight rescaling applied: {total_before:.2f}% → 100.0000000000% "
            f"(Task 10.5: ensuring exact sum for precision)"
        )
    else:
        # Weights already sum to 100.0, use original weights
        for dim in dimensions:
            effective_weights[dim.dimension_name] = dim.weight

    for dim in dimensions:
        dim_name = dim.dimension_name

        # Extract metrics for this dimension
        metrics = results.dimension_results.get(dim_name, {})

        # Get effective weight (rescaled or original) for this dimension
        effective_weight = effective_weights.get(dim_name, dim.weight)

        # Handle selective loading (dimension not loaded)
        # Note: Using `== False` intentionally - None means "not set" (available), False means explicitly unavailable
        if not metrics or metrics.get("available") == False:  # noqa: E712
            # Create placeholder ScoreDimension with 0 contribution
            score_dim = ScoreDimension(
                name=dim.description,
                score=0.0,
                max_score=effective_weight,
                percentage=0.0,
                impact="NONE",
                gap=effective_weight,
                raw_value=None,
                recommendation=None,
            )
            dimension_scores.append((dim, score_dim))
            continue

        # Calculate score using dimension's calculate_score method
        try:
            # Check if a pre-calculated score is available (for testing/backward compat)
            if "score" in metrics and isinstance(metrics["score"], (int, float)):
                raw_score = float(metrics["score"])  # Use pre-calculated score
            else:
                raw_score = dim.calculate_score(metrics)  # Calculate from metrics

            # Apply z-score normalization if enabled (Story 2.4.1, AC7)
            # This ensures scores from different scoring functions (Gaussian, monotonic, threshold)
            # are on the same scale before weighted aggregation
            if enable_normalization:
                normalized_raw_score = normalizer.normalize_score(raw_score, dim_name)
            else:
                normalized_raw_score = raw_score

            # Normalize score to dimension's effective weight (rescaled or original)
            # 100 on dimension scale = full weight points
            # 0 on dimension scale = 0 points
            normalized_score = (normalized_raw_score / 100.0) * effective_weight

            # Calculate percentage (how much of max we achieved)
            percentage = normalized_raw_score  # Already 0-100 after normalization

            # Calculate impact level
            gap = effective_weight - normalized_score
            impact = _calculate_impact(gap, effective_weight)

            # Get primary metric for display
            raw_value = _extract_primary_metric(metrics, dim_name)

            # Get recommendation from dimension
            recommendations = dim.get_recommendations(raw_score, metrics)
            recommendation = recommendations[0] if recommendations else None

            score_dim = ScoreDimension(
                name=dim.description,
                score=normalized_score,
                max_score=effective_weight,
                percentage=percentage,
                impact=impact,
                gap=gap,
                raw_value=raw_value,
                recommendation=recommendation,
            )

            dimension_scores.append((dim, score_dim))

        except Exception as e:
            logger.error(f"Error calculating score for {dim_name}: {e}")
            # Create error placeholder
            score_dim = ScoreDimension(
                name=dim.description,
                score=0.0,
                max_score=effective_weight,
                percentage=0.0,
                impact="NONE",
                gap=effective_weight,
                raw_value=None,
                recommendation=f"Error: {str(e)}",
            )
            dimension_scores.append((dim, score_dim))

    return dimension_scores


def _build_score_categories(
    dimension_scores: List[Tuple[Any, ScoreDimension]],
) -> List[ScoreCategory]:
    """
    Group dimensions by tier into ScoreCategory objects.

    Tiers:
        - ADVANCED: ML-based, highest accuracy (Target: 30-40% of score)
        - CORE: Proven AI signatures (Target: 35-45% of score)
        - SUPPORTING: Quality indicators (Target: 15-25% of score)
        - STRUCTURAL: AST-based patterns (Target: 5-10% of score)

    Args:
        dimension_scores: List of (dimension, ScoreDimension) tuples

    Returns:
        List of ScoreCategory objects (one per tier)
    """
    # Group by tier
    tier_groups: Dict[str, List[ScoreDimension]] = {
        "ADVANCED": [],
        "CORE": [],
        "SUPPORTING": [],
        "STRUCTURAL": [],
    }

    tier_weights: Dict[str, float] = {
        "ADVANCED": 0.0,
        "CORE": 0.0,
        "SUPPORTING": 0.0,
        "STRUCTURAL": 0.0,
    }

    for dim, score_dim in dimension_scores:
        # Handle both enum and string tier values
        tier_name = dim.tier.value if hasattr(dim.tier, "value") else dim.tier
        tier_groups[tier_name].append(score_dim)
        tier_weights[tier_name] += dim.weight

    # Build ScoreCategory for each tier
    categories = []

    tier_display_names = {
        "ADVANCED": "Advanced Detection",
        "CORE": "Core Patterns",
        "SUPPORTING": "Supporting Indicators",
        "STRUCTURAL": "Structural Patterns",
    }

    for tier_name in ["ADVANCED", "CORE", "SUPPORTING", "STRUCTURAL"]:
        dimensions = tier_groups[tier_name]
        max_total = tier_weights[tier_name]
        total = sum(d.score for d in dimensions)
        percentage = (total / max_total * 100) if max_total > 0 else 0.0

        category = ScoreCategory(
            name=tier_display_names[tier_name],
            total=total,
            max_total=max_total,
            percentage=percentage,
            dimensions=dimensions,
        )
        categories.append(category)

    return categories


def _calculate_overall_scores(categories: List[ScoreCategory]) -> Tuple[float, float]:
    """
    Calculate Detection Risk and Quality Score from category totals.

    Detection Risk: 0-100 (lower = better, less detectable)
        100 - quality_score = detection_risk
        Perfect score (100) → 0% detection risk
        Worst score (0) → 100% detection risk

    Quality Score: 0-100 (higher = better, more human-like)
        Sum of all dimension scores
        Perfect: 100 points
        Worst: 0 points

    Args:
        categories: List of ScoreCategory objects

    Returns:
        Tuple of (detection_risk, quality_score)
    """
    # Quality score is sum of all category totals
    quality_score = sum(cat.total for cat in categories)

    # Detection risk is inverse of quality
    detection_risk = 100.0 - quality_score

    return detection_risk, quality_score


def _generate_improvements(
    dimension_scores: List[Tuple[Any, ScoreDimension]], results: AnalysisResults
) -> List[ImprovementAction]:
    """
    Generate improvement actions for all dimensions with gaps.

    Args:
        dimension_scores: List of (dimension, ScoreDimension) tuples
        results: AnalysisResults for context

    Returns:
        List of ImprovementAction sorted by potential impact
    """
    improvements = []
    priority = 1

    for dim, score_dim in dimension_scores:
        if score_dim.gap > 0.1 and score_dim.recommendation:  # Only include if gap exists
            # Estimate effort level for this dimension
            effort = _estimate_dimension_effort(dim, score_dim.gap)

            improvement = ImprovementAction(
                priority=priority,
                dimension=score_dim.name,
                current_score=score_dim.score,
                max_score=score_dim.max_score,
                potential_gain=score_dim.gap,
                impact_level=score_dim.impact,
                action=score_dim.recommendation,
                effort_level=effort,
                line_references=[],  # Could be enhanced with detailed analysis results
            )
            improvements.append(improvement)
            priority += 1

    # Sort by impact (HIGH > MEDIUM > LOW > NONE) and then by potential gain
    impact_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
    improvements.sort(key=lambda x: (impact_order.get(x.impact_level, 3), -x.potential_gain))

    # Re-assign priorities after sorting
    for i, improvement in enumerate(improvements, 1):
        improvement.priority = i

    return improvements


def _build_optimization_path(
    improvements: List[ImprovementAction],
    current_detection: float,
    target_detection: float,
    current_quality: float,
    target_quality: float,
) -> List[ImprovementAction]:
    """
    Build optimization path sorted by ROI (impact / effort).

    Args:
        improvements: All improvement actions
        current_detection: Current detection risk
        target_detection: Target detection risk
        current_quality: Current quality score
        target_quality: Target quality score

    Returns:
        Optimized list of improvements to reach targets
    """
    # If already at target, return empty path
    if current_detection <= target_detection and current_quality >= target_quality:
        return []

    # Calculate quality gap
    quality_gap = target_quality - current_quality

    # Filter to high-impact improvements that can close the gap
    path = [imp for imp in improvements if imp.impact_level in ["HIGH", "MEDIUM"]]

    # Sort by ROI: impact_weight / effort_weight
    effort_weights = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    impact_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}

    path.sort(
        key=lambda x: (
            impact_weights.get(x.impact_level, 0) / effort_weights.get(x.effort_level, 2),
            -x.potential_gain,
        ),
        reverse=True,
    )

    # Build path to reach target (100% of gap)
    cumulative_gain = 0.0
    optimized_path = []
    target_gain = quality_gap  # Aim to reach target, not just partial gap

    for improvement in path:
        optimized_path.append(improvement)
        cumulative_gain += improvement.potential_gain
        if cumulative_gain >= target_gain:
            break

    return optimized_path


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _calculate_impact(gap: float, max_points: float) -> str:
    """Calculate impact level based on gap and point weight."""
    if gap < 1.0:
        return "NONE"
    elif gap < 2.0:
        return "LOW"
    elif gap < 4.0:
        return "MEDIUM"
    else:
        return "HIGH"


def _estimate_dimension_effort(dimension: Any, gap: float) -> str:
    """
    Estimate effort required to close gap for a specific dimension.

    Uses dimension tier as heuristic:
    - STRUCTURAL: Easy to fix (formatting, mechanical patterns)
    - CORE: Medium effort (vocabulary, sentence variation)
    - SUPPORTING: Medium effort (context, quality indicators)
    - ADVANCED: Hard to fix (deep linguistic patterns)
    """
    tier = dimension.tier

    if tier == DimensionTier.STRUCTURAL:
        return "LOW" if gap < 3 else "MEDIUM"
    elif tier in [DimensionTier.CORE, DimensionTier.SUPPORTING]:
        return "MEDIUM" if gap < 4 else "HIGH"
    else:  # ADVANCED
        return "HIGH"


def _estimate_effort(dimension_name: str, gap: float) -> str:
    """
    DEPRECATED: Backward compatibility wrapper for old implementation.

    Uses hardcoded dimension name matching. New code should use
    _estimate_dimension_effort with dimension tier instead.

    Args:
        dimension_name: Dimension display name
        gap: Points below max

    Returns:
        Effort level: 'LOW', 'MEDIUM', or 'HIGH'
    """
    easy_fixes = [
        "Formatting Patterns",
        "Stylometric Markers",
        "Heading Hierarchy",
        "Bold/Italic Patterns",
        "Punctuation Clustering",
        "Whitespace Patterns",
        "Blockquote Distribution",
        "Link Anchor Text",
        "Punctuation Spacing",
        "List Symmetry (AST)",
        "Code Block Patterns",
    ]
    medium_fixes = [
        "Burstiness (Sentence Variation)",
        "Perplexity (Vocabulary)",
        "Structure & Organization",
        "Voice & Authenticity",
        "Technical Depth",
        "List Usage Patterns",
        "List Nesting Depth",
        "Heading Length Variance",
        "Heading Depth Navigation",
        "Paragraph Length Variance",
        "H2 Section Length Variance",
        "H3/H4 Subsection Asymmetry",
    ]

    if dimension_name in easy_fixes:
        return "LOW" if gap < 3 else "MEDIUM"
    elif dimension_name in medium_fixes:
        return "MEDIUM" if gap < 4 else "HIGH"
    else:  # hard_fixes or unknown
        return "HIGH"


def _estimate_overall_effort(quality_gap: float) -> str:
    """Estimate overall effort required to reach target."""
    if quality_gap < 5:
        return "MINIMAL"
    elif quality_gap < 10:
        return "LIGHT"
    elif quality_gap < 20:
        return "MODERATE"
    elif quality_gap < 30:
        return "SUBSTANTIAL"
    else:
        return "EXTENSIVE"


def _interpret_quality(score: float) -> str:
    """Interpret quality score."""
    if score >= 95:
        return "EXCEPTIONAL - Indistinguishable from human"
    elif score >= 85:
        return "EXCELLENT - Minimal AI signatures"
    elif score >= 70:
        return "GOOD - Natural with minor tells"
    elif score >= 50:
        return "MIXED - Needs moderate work"
    elif score >= 30:
        return "AI-LIKE - Substantial work needed"
    else:
        return "OBVIOUS AI - Complete rewrite"


def _interpret_detection(risk: float) -> str:
    """Interpret detection risk."""
    if risk >= 70:
        return "VERY HIGH - Will be flagged"
    elif risk >= 50:
        return "HIGH - Likely flagged"
    elif risk >= 30:
        return "MEDIUM - May be flagged"
    elif risk >= 15:
        return "LOW - Unlikely flagged"
    else:
        return "VERY LOW - Safe from detection"


def _extract_primary_metric(metrics: Dict[str, Any], dimension_name: str) -> Optional[Any]:
    """
    Extract the primary display metric for a dimension.

    Each dimension has key metrics that are most informative for users.
    This function extracts the most relevant one for display.

    Args:
        metrics: Dimension metrics dictionary
        dimension_name: Name of the dimension

    Returns:
        Primary metric value or None
    """
    # Map dimension names to their primary display metric
    primary_metrics = {
        "predictability": "gltr_top10_percentage",
        "perplexity": "ai_vocabulary_per_1k",
        "burstiness": "sentence_stdev",
        "structure": "heading_parallelism_score",
        "formatting": "em_dashes_per_page",
        "voice": "first_person_count",
        "readability": "flesch_reading_ease",
        "lexical": "unique_word_ratio",
        "sentiment": "sentiment_flatness_score",
        "syntactic": "subordination_index",
        "advanced_lexical": "hdd_score",
        "transition_marker": "transition_marker_density",
    }

    primary_key = primary_metrics.get(dimension_name)
    if primary_key and primary_key in metrics:
        return metrics[primary_key]

    # Fallback: return first numeric metric
    for _key, value in metrics.items():
        if isinstance(value, (int, float)):
            return value

    return None
