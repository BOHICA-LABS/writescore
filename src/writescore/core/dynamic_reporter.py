# core/dynamic_reporter.py

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from writescore.core.dimension_loader import DIMENSION_MODULE_MAP
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import AnalysisResults

# Constants
NORMALIZATION_THRESHOLD = 0.01  # Threshold for detecting if weights need normalization
DEFAULT_TIER_SCORE = 50.0  # Neutral score when all dimensions fail


class DynamicReporter:
    """
    Dynamic report generator for analysis results.

    Features:
    - Automatic dimension discovery from registry
    - Tier-based dimension grouping
    - Prioritized recommendation aggregation
    - Multiple output formats (JSON, Markdown, Text)
    - Backward compatible CLI text output

    Example:
        reporter = DynamicReporter()

        # Generate comprehensive report
        report = reporter.generate_comprehensive_report(results)

        # Format as markdown
        markdown = reporter.format_as_markdown(results)

        # Format as JSON
        json_output = reporter.format_as_json(results)

        # Format as text (CLI compatible)
        text_output = reporter.format_as_text(results)
    """

    def __init__(self, registry: Optional[DimensionRegistry] = None):
        """
        Initialize Dynamic Reporter.

        Args:
            registry: DimensionRegistry instance (uses global if None)
        """
        self.registry = registry or DimensionRegistry

    def generate_comprehensive_report(
        self, results: AnalysisResults, file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report from analysis results.

        Structure:
        - metadata: file info, timestamp
        - overall: score, assessment, grade
        - tier_breakdown: dimensions grouped by tier
        - recommendations: prioritized list
        - weight_distribution: tier and dimension weights

        Args:
            results: AnalysisResults from DynamicAnalysisEngine
            file_path: Optional file path for metadata

        Returns:
            Comprehensive report dict

        Raises:
            ValueError: If results.dimension_results is None or empty
        """
        # Input validation
        if results.dimension_results is None or len(results.dimension_results) == 0:
            raise ValueError("Cannot generate report: dimension_results is empty or None")

        report = {
            "metadata": self._generate_metadata(results, file_path),
            "overall": self._generate_overall_summary(results),
            "tier_breakdown": self.generate_tier_summary(results),
            "recommendations": self.generate_prioritized_recommendations(results),
            "weight_distribution": self.generate_weight_distribution(),
        }

        return report

    def _generate_metadata(
        self, results: AnalysisResults, file_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Generate report metadata.

        NEW (AC8, AC9): Includes information about loaded vs available dimensions
        to handle selective loading from DimensionLoader.
        """
        loaded_count = results.dimension_count
        available_count = len(DIMENSION_MODULE_MAP)  # Total possible dimensions from loader

        # Get loaded dimension names from results
        loaded_dimensions = list(results.dimension_results.keys())

        # All possible dimensions from DIMENSION_MODULE_MAP (single source of truth)
        all_dimensions = list(DIMENSION_MODULE_MAP.keys())

        # Determine which dimensions were not loaded
        not_loaded = [d for d in all_dimensions if d not in loaded_dimensions]

        # Determine if this is a partial analysis
        is_partial = loaded_count < available_count

        return {
            "file_path": file_path or "unknown",
            "analysis_timestamp": datetime.now().isoformat(),
            "dimension_count": loaded_count,  # Keep for backward compatibility
            "execution_time": results.execution_time,
            # NEW: Selective loading metadata (AC8, AC9)
            "dimensions_loaded": loaded_count,
            "dimensions_available": available_count,
            "is_partial_analysis": is_partial,
            "loaded_dimensions": loaded_dimensions,
            "not_loaded_dimensions": not_loaded if is_partial else [],
        }

    def _generate_overall_summary(self, results: AnalysisResults) -> Dict[str, Any]:
        """Generate overall summary with score, assessment, and grade."""
        return {
            "score": results.overall_score,
            "assessment": results.overall_assessment,
            "grade": self._calculate_grade(results.overall_score),
        }

    def generate_tier_summary(self, results: AnalysisResults) -> Dict[str, Dict[str, Any]]:
        """
        Generate tier-based summary of dimensions.

        Groups dimensions by tier and calculates tier-level scores.

        Algorithm:
        1. Group dimensions by tier
        2. For each tier:
           - Collect dimension scores and weights
           - Calculate weighted tier score
           - Build dimension list

        Args:
            results: AnalysisResults from analysis

        Returns:
            Dict mapping tier_name → tier summary dict
        """
        tier_summary = {}
        dimension_results = results.dimension_results

        # Group dimensions by tier
        tiers = ["ADVANCED", "CORE", "SUPPORTING", "STRUCTURAL"]

        for tier in tiers:
            tier_dimensions = []
            total_weighted_score = 0.0
            total_weight = 0.0

            for dim_name, dim_result in dimension_results.items():
                # Skip dimensions that failed and don't have tier metadata
                if "tier" not in dim_result:
                    continue
                if dim_result["tier"] == tier:
                    score = dim_result["score"]
                    weight = dim_result["weight"]
                    impact_level = self._determine_impact_level(score)

                    tier_dimensions.append(
                        {
                            "name": dim_name,
                            "score": score,
                            "tier_mapping": dim_result["tier_mapping"],
                            "weight": weight,
                            "impact_level": impact_level,
                            "error": dim_result.get("error"),
                        }
                    )

                    # Include in tier score if no error
                    if dim_result.get("error") is None:
                        total_weighted_score += score * weight
                        total_weight += weight

            # Calculate tier score (with error handling for division by zero)
            try:
                tier_score = (
                    total_weighted_score / total_weight
                    if total_weight > 0
                    else DEFAULT_TIER_SCORE  # Neutral if all failed
                )
            except (ZeroDivisionError, TypeError):
                tier_score = DEFAULT_TIER_SCORE

            tier_summary[tier] = {
                "tier_score": tier_score,
                "tier_weight": total_weight,
                "dimensions": tier_dimensions,
            }

        return tier_summary

    def generate_prioritized_recommendations(
        self, results: AnalysisResults
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations across all dimensions.

        Priority Formula:
        priority = impact_multiplier × dimension_weight

        Impact Multipliers:
        - HIGH: 4
        - MEDIUM: 3
        - LOW: 2
        - NONE: 1

        Args:
            results: AnalysisResults from analysis

        Returns:
            Ordered list of recommendations (highest priority first)
        """
        all_recommendations = []
        dimension_results = results.dimension_results

        impact_multiplier = {"HIGH": 4, "MEDIUM": 3, "LOW": 2, "NONE": 1}

        for dim_name, dim_result in dimension_results.items():
            if dim_result.get("error") is not None:
                continue  # Skip failed dimensions

            recommendations = dim_result.get("recommendations", [])
            score = dim_result["score"]
            weight = dim_result["weight"]
            tier = dim_result["tier"]
            impact_level = self._determine_impact_level(score)

            # Calculate priority
            priority = impact_multiplier[impact_level] * weight

            for rec_text in recommendations:
                all_recommendations.append(
                    {
                        "priority": priority,
                        "dimension": dim_name,
                        "tier": tier,
                        "impact_level": impact_level,
                        "weight": weight,
                        "recommendation": rec_text,
                    }
                )

        # Sort by priority (descending)
        all_recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return all_recommendations

    def generate_weight_distribution(self, normalize: bool = True) -> Dict[str, Any]:
        """
        Generate weight distribution data for visualization.

        NEW (AC10): Supports weight normalization for selective loading scenarios.
        When only a subset of dimensions are loaded, their weights are normalized
        to sum to 100% for proper visualization.

        Args:
            normalize: If True, normalize weights to sum to 100% (default True)

        Returns:
            Dict with 'by_tier' and 'by_dimension' weight breakdowns
        """
        dimensions = self.registry.get_all()

        # Calculate raw tier totals and dimension weights
        tier_totals: Dict[str, float] = {}
        dimension_weights: List[Dict[str, Any]] = []
        total_weight = 0.0

        for dim in dimensions:
            tier = dim.tier
            weight = dim.weight
            total_weight += weight

            # Accumulate tier totals
            tier_totals[tier] = tier_totals.get(tier, 0.0) + weight

            # Add dimension entry (will normalize later if needed)
            dimension_weights.append({"name": dim.dimension_name, "weight": weight, "tier": tier})

        # NEW (AC10): Normalize weights if requested and total != 100
        normalization_factor = 100.0 / total_weight if normalize and total_weight > 0 else 1.0
        is_normalized = abs(normalization_factor - 1.0) > NORMALIZATION_THRESHOLD

        # Apply normalization
        if is_normalized:
            tier_totals = {
                tier: weight * normalization_factor for tier, weight in tier_totals.items()
            }
            for dim_weight in dimension_weights:
                dim_weight["weight"] = dim_weight["weight"] * normalization_factor
                dim_weight["percentage"] = f"{dim_weight['weight']:.1f}%"
        else:
            for dim_weight in dimension_weights:
                dim_weight["percentage"] = f"{dim_weight['weight']:.1f}%"

        # Sort by weight descending
        dimension_weights.sort(key=lambda x: x["weight"], reverse=True)

        return {
            "by_tier": tier_totals,
            "by_dimension": dimension_weights,
            "is_normalized": is_normalized,  # NEW: Indicates if weights were normalized
            "total_weight_before_normalization": total_weight,  # NEW: Original weight sum
        }

    def format_as_markdown(self, results: AnalysisResults) -> str:
        """
        Format analysis results as markdown.

        Features:
        - Headers for sections
        - Pipe tables with alignment
        - Bullet lists for recommendations
        - Weight distribution table

        Markdown Table Format:
        - Headers: | Column 1 | Column 2 |
        - Alignment: |:---------|:--------:|  (left, center, right)
        - Rows: | Value 1 | Value 2 |

        Args:
            results: AnalysisResults from analysis

        Returns:
            Markdown-formatted string
        """
        report = self.generate_comprehensive_report(results)

        lines = []
        lines.append("# AI Pattern Analysis Report")
        lines.append("")

        # NEW (AC8, AC9): Add partial analysis notice if applicable
        metadata = report["metadata"]
        if metadata.get("is_partial_analysis", False):
            lines.append(
                "> **Note**: This is a partial analysis based on "
                + f"{metadata['dimensions_loaded']} of {metadata['dimensions_available']} "
                + "available dimensions."
            )
            if metadata["not_loaded_dimensions"]:
                not_loaded = ", ".join(metadata["not_loaded_dimensions"])
                lines.append(f"> **Not loaded**: {not_loaded}")
            lines.append("")

        # Overall Assessment
        lines.append("## Overall Assessment")
        lines.append(f"- **Score**: {report['overall']['score']:.2f}")
        lines.append(f"- **Assessment**: {report['overall']['assessment']}")
        lines.append(f"- **Grade**: {report['overall']['grade']}")
        lines.append("")

        # Dimension Analysis by Tier
        lines.append("## Dimension Analysis by Tier")
        lines.append("")

        tier_order = ["ADVANCED", "CORE", "SUPPORTING", "STRUCTURAL"]
        for tier in tier_order:
            if tier not in report["tier_breakdown"]:
                continue

            tier_data = report["tier_breakdown"][tier]
            tier_score = tier_data["tier_score"]
            tier_weight = tier_data["tier_weight"]

            lines.append(f"### {tier} Tier (Score: {tier_score:.1f}, Weight: {tier_weight:.1f}%)")
            lines.append("")

            # Dimension table with proper alignment
            lines.append("| Dimension | Score | Rating | Weight | Impact |")
            lines.append("|:----------|------:|:------:|-------:|:------:|")

            for dim in tier_data["dimensions"]:
                name = dim["name"]
                score = dim["score"]
                rating = dim["tier_mapping"]
                weight = dim["weight"]
                impact = dim["impact_level"]

                lines.append(f"| {name} | {score:.1f} | {rating} | {weight:.1f}% | {impact} |")

            lines.append("")

        # Prioritized Recommendations
        lines.append("## Prioritized Recommendations")
        lines.append("")

        # Group by impact level
        high_recs = [r for r in report["recommendations"] if r["impact_level"] == "HIGH"]
        medium_recs = [r for r in report["recommendations"] if r["impact_level"] == "MEDIUM"]
        low_recs = [r for r in report["recommendations"] if r["impact_level"] == "LOW"]

        if high_recs:
            lines.append("### High Priority")
            for i, rec in enumerate(high_recs, 1):
                dim = rec["dimension"]
                tier = rec["tier"]
                text = rec["recommendation"]
                lines.append(f"{i}. **[{dim} - {tier}]** {text}")
            lines.append("")

        if medium_recs:
            lines.append("### Medium Priority")
            for i, rec in enumerate(medium_recs, 1):
                dim = rec["dimension"]
                tier = rec["tier"]
                text = rec["recommendation"]
                lines.append(f"{i}. **[{dim} - {tier}]** {text}")
            lines.append("")

        if low_recs:
            lines.append("### Low Priority")
            for i, rec in enumerate(low_recs, 1):
                dim = rec["dimension"]
                tier = rec["tier"]
                text = rec["recommendation"]
                lines.append(f"{i}. **[{dim} - {tier}]** {text}")
            lines.append("")

        # Weight Distribution
        lines.append("## Weight Distribution")
        lines.append("")
        lines.append("### By Tier")
        for tier, weight in report["weight_distribution"]["by_tier"].items():
            lines.append(f"- **{tier}**: {weight:.1f}%")
        lines.append("")

        lines.append("### By Dimension")
        lines.append("")
        lines.append("| Dimension | Weight | Tier |")
        lines.append("|:----------|-------:|:-----|")
        for dim in report["weight_distribution"]["by_dimension"]:
            name = dim["name"]
            weight = dim["weight"]
            tier = dim["tier"]
            lines.append(f"| {name} | {weight:.1f}% | {tier} |")
        lines.append("")

        return "\n".join(lines)

    def format_as_json(self, results: AnalysisResults) -> str:
        """
        Format analysis results as JSON.

        Args:
            results: AnalysisResults from analysis

        Returns:
            JSON string with 2-space indentation

        Raises:
            TypeError: If report contains non-serializable objects
        """
        report = self.generate_comprehensive_report(results)
        try:
            return json.dumps(report, indent=2)
        except TypeError as e:
            # Re-raise with more context for debugging
            raise TypeError(f"Failed to serialize report to JSON: {e}") from e

    def format_as_text(self, results: AnalysisResults, file_path: Optional[str] = None) -> str:
        """
        Format analysis results as plain text (CLI compatible).

        Maintains exact backward compatibility with legacy CLI output:
        - Section separators: ===, ---
        - Number formatting: 1,234 with commas
        - Line structure matches legacy format

        Args:
            results: AnalysisResults from analysis
            file_path: Optional file path for display

        Returns:
            Plain text formatted string
        """
        lines = []

        # Header
        lines.append("=== AI Pattern Analysis Results ===")
        lines.append("")

        # File metadata
        if file_path:
            lines.append(f"File: {file_path}")
        lines.append("")

        # Overall score
        score = results.overall_score
        assessment = results.overall_assessment
        grade = self._calculate_grade(score)
        lines.append(f"Overall Score: {score:.1f} ({assessment}) - Grade: {grade}")
        lines.append("")

        # Dimension scores by tier
        lines.append("--- Dimension Scores ---")
        lines.append("")

        tier_summary = self.generate_tier_summary(results)
        tier_order = ["ADVANCED", "CORE", "SUPPORTING", "STRUCTURAL"]

        for tier in tier_order:
            if tier not in tier_summary:
                continue

            tier_data = tier_summary[tier]
            lines.append(f"{tier} Tier (Score: {tier_data['tier_score']:.1f}):")

            for dim in tier_data["dimensions"]:
                name = dim["name"].capitalize()
                rating = dim["tier_mapping"]
                score_val = dim["score"]
                lines.append(f"  {name}: {rating} ({score_val:.1f})")

            lines.append("")

        # Recommendations
        recommendations = self.generate_prioritized_recommendations(results)

        if recommendations:
            lines.append("--- Recommendations ---")
            lines.append("")

            for i, rec in enumerate(recommendations, 1):
                text = rec["recommendation"]
                lines.append(f"{i}. {text}")

            lines.append("")

        # Weight distribution
        lines.append("--- Weight Distribution ---")
        lines.append("")

        weight_dist = self.generate_weight_distribution()
        for tier, weight in weight_dist["by_tier"].items():
            lines.append(f"{tier}: {weight:.1f}%")

        lines.append("")
        lines.append("=" * 35)

        return "\n".join(lines)

    def _calculate_grade(self, score: float) -> str:
        """
        Calculate letter grade from score.

        Grading Scale:
        - A: 90-100
        - B: 80-89
        - C: 70-79
        - D: 60-69
        - F: 0-59

        Args:
            score: Overall score (0-100)

        Returns:
            Letter grade
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _determine_impact_level(self, score: float) -> str:
        """
        Determine impact level from dimension score.

        Impact Levels:
        - HIGH: score < 50 (AI-likely, needs attention)
        - MEDIUM: 50 ≤ score < 70 (mixed, improvements recommended)
        - LOW: 70 ≤ score < 85 (acceptable, minor improvements)
        - NONE: score ≥ 85 (human-like, no action needed)

        Args:
            score: Dimension score (0-100)

        Returns:
            Impact level string
        """
        if score < 50:
            return "HIGH"
        elif score < 70:
            return "MEDIUM"
        elif score < 85:
            return "LOW"
        else:
            return "NONE"
