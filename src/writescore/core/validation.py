"""
Parameter validation and score shift analysis for backward compatibility.

This module provides tools for:
1. Validating parameter constraints (ranges, relationships)
2. Analyzing score shifts between parameter versions
3. Generating compatibility reports

Created in Story 2.5 Task 6 to ensure safe parameter updates.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.parameters import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    PercentileParameters,
    ScoringType,
    ThresholdParameters,
)

logger = logging.getLogger(__name__)


# Score shift thresholds
SHIFT_WARNING_THRESHOLD = 10.0  # Points - warn if shift > this
SHIFT_ERROR_THRESHOLD = 15.0  # Points - error if shift > this
MAX_ACCEPTABLE_MEAN_SHIFT = 5.0  # Average shift across all documents


@dataclass
class DocumentScoreShift:
    """Score shift analysis for a single document."""

    document_id: str
    old_scores: Dict[str, float]
    new_scores: Dict[str, float]
    dimension_shifts: Dict[str, float] = field(default_factory=dict)
    total_shift: float = 0.0

    def __post_init__(self):
        """Calculate shifts after initialization."""
        self._calculate_shifts()

    def _calculate_shifts(self):
        """Calculate per-dimension and total shifts."""
        all_dims = set(self.old_scores.keys()) | set(self.new_scores.keys())

        total = 0.0
        count = 0

        for dim in all_dims:
            old = self.old_scores.get(dim, 0.0)
            new = self.new_scores.get(dim, 0.0)
            shift = new - old
            self.dimension_shifts[dim] = shift
            total += abs(shift)
            count += 1

        self.total_shift = total / count if count > 0 else 0.0

    def has_warning_shift(self) -> bool:
        """Check if any dimension has a warning-level shift."""
        return any(abs(s) > SHIFT_WARNING_THRESHOLD for s in self.dimension_shifts.values())

    def has_error_shift(self) -> bool:
        """Check if any dimension has an error-level shift."""
        return any(abs(s) > SHIFT_ERROR_THRESHOLD for s in self.dimension_shifts.values())

    def get_flagged_dimensions(self) -> List[Tuple[str, float]]:
        """Get dimensions with shifts above warning threshold."""
        return [
            (dim, shift)
            for dim, shift in self.dimension_shifts.items()
            if abs(shift) > SHIFT_WARNING_THRESHOLD
        ]


@dataclass
class ScoreShiftReport:
    """Comprehensive score shift analysis report."""

    old_params_version: str
    new_params_version: str
    timestamp: str
    document_shifts: List[DocumentScoreShift] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

    def add_document_shift(self, shift: DocumentScoreShift):
        """Add a document's shift analysis."""
        self.document_shifts.append(shift)

    def calculate_summary(self):
        """Calculate summary statistics across all documents."""
        if not self.document_shifts:
            self.summary_stats = {
                "total_documents": 0,
                "mean_total_shift": 0.0,
                "max_total_shift": 0.0,
                "warning_count": 0,
                "error_count": 0,
                "dimension_mean_shifts": {},
                "is_acceptable": True,
            }
            return

        # Calculate overall stats
        total_shifts = [d.total_shift for d in self.document_shifts]
        warning_count = sum(1 for d in self.document_shifts if d.has_warning_shift())
        error_count = sum(1 for d in self.document_shifts if d.has_error_shift())

        # Calculate per-dimension mean shifts
        all_dims = set()
        for d in self.document_shifts:
            all_dims.update(d.dimension_shifts.keys())

        dimension_mean_shifts = {}
        for dim in all_dims:
            shifts = [d.dimension_shifts.get(dim, 0.0) for d in self.document_shifts]
            dimension_mean_shifts[dim] = sum(shifts) / len(shifts)

        mean_total_shift = sum(total_shifts) / len(total_shifts)

        self.summary_stats = {
            "total_documents": len(self.document_shifts),
            "mean_total_shift": mean_total_shift,
            "max_total_shift": max(total_shifts),
            "min_total_shift": min(total_shifts),
            "warning_count": warning_count,
            "error_count": error_count,
            "warning_percentage": warning_count / len(self.document_shifts) * 100,
            "error_percentage": error_count / len(self.document_shifts) * 100,
            "dimension_mean_shifts": dimension_mean_shifts,
            "is_acceptable": mean_total_shift <= MAX_ACCEPTABLE_MEAN_SHIFT and error_count == 0,
        }

    def is_acceptable(self) -> bool:
        """Check if the shift is within acceptable bounds."""
        if not self.summary_stats:
            self.calculate_summary()
        return bool(self.summary_stats.get("is_acceptable", False))

    def get_flagged_documents(self) -> List[DocumentScoreShift]:
        """Get documents with warning or error level shifts."""
        return [d for d in self.document_shifts if d.has_warning_shift()]

    def format_text_report(self) -> str:
        """Generate human-readable report."""
        if not self.summary_stats:
            self.calculate_summary()

        lines = [
            "=" * 80,
            "SCORE SHIFT ANALYSIS REPORT",
            "=" * 80,
            f"Old Parameters: {self.old_params_version}",
            f"New Parameters: {self.new_params_version}",
            f"Timestamp: {self.timestamp}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Documents Analyzed: {self.summary_stats['total_documents']}",
            f"Mean Score Shift: {self.summary_stats['mean_total_shift']:.2f} points",
            f"Max Score Shift: {self.summary_stats['max_total_shift']:.2f} points",
            f"Documents with Warnings: {self.summary_stats['warning_count']} ({self.summary_stats.get('warning_percentage', 0):.1f}%)",
            f"Documents with Errors: {self.summary_stats['error_count']} ({self.summary_stats.get('error_percentage', 0):.1f}%)",
            "",
            f"Acceptable: {'YES' if self.summary_stats['is_acceptable'] else 'NO'}",
            "",
        ]

        # Per-dimension shifts
        lines.append("DIMENSION MEAN SHIFTS")
        lines.append("-" * 40)
        for dim, shift in sorted(self.summary_stats.get("dimension_mean_shifts", {}).items()):
            indicator = ""
            if abs(shift) > SHIFT_ERROR_THRESHOLD:
                indicator = " [ERROR]"
            elif abs(shift) > SHIFT_WARNING_THRESHOLD:
                indicator = " [WARNING]"
            lines.append(f"  {dim}: {shift:+.2f}{indicator}")

        # Flagged documents
        flagged = self.get_flagged_documents()
        if flagged:
            lines.append("")
            lines.append("FLAGGED DOCUMENTS")
            lines.append("-" * 40)
            for doc in flagged[:10]:  # Show top 10
                lines.append(f"  {doc.document_id}: avg shift {doc.total_shift:.2f}")
                for dim, shift in doc.get_flagged_dimensions():
                    lines.append(f"    - {dim}: {shift:+.2f}")
            if len(flagged) > 10:
                lines.append(f"  ... and {len(flagged) - 10} more")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        if not self.summary_stats:
            self.calculate_summary()

        return {
            "old_params_version": self.old_params_version,
            "new_params_version": self.new_params_version,
            "timestamp": self.timestamp,
            "summary": self.summary_stats,
            "document_shifts": [
                {
                    "document_id": d.document_id,
                    "total_shift": d.total_shift,
                    "dimension_shifts": d.dimension_shifts,
                    "has_warning": d.has_warning_shift(),
                    "has_error": d.has_error_shift(),
                }
                for d in self.document_shifts
            ],
        }

    def save(self, path: Path):
        """Save report to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved score shift report to {path}")


class ParameterValidator:
    """Validates parameter sets for correctness and compatibility."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_parameters(self, params: PercentileParameters) -> bool:
        """
        Validate a complete parameter set.

        Returns True if valid, False if errors found.
        """
        self.errors = []
        self.warnings = []

        # Validate each dimension
        for dim_name, dim_params in params.dimensions.items():
            self._validate_dimension(dim_name, dim_params)

        # Check for required dimensions
        required_dims = [
            "burstiness",
            "lexical",
            "readability",
            "syntactic",
            "sentiment",
            "voice",
            "structure",
            "formatting",
        ]
        for dim in required_dims:
            if dim not in params.dimensions:
                self.warnings.append(f"Missing recommended dimension: {dim}")

        return len(self.errors) == 0

    def _validate_dimension(self, name: str, params: DimensionParameters):
        """Validate a single dimension's parameters."""
        try:
            params.validate()
        except ValueError as e:
            self.errors.append(f"{name}: {e}")
            return

        # Additional range checks based on scoring type
        if params.scoring_type == ScoringType.GAUSSIAN:
            self._validate_gaussian(name, params.parameters)
        elif params.scoring_type == ScoringType.MONOTONIC:
            self._validate_monotonic(name, params.parameters)
        elif params.scoring_type == ScoringType.THRESHOLD:
            self._validate_threshold(name, params.parameters)

    def _validate_gaussian(self, name: str, params: GaussianParameters):
        """Validate Gaussian-specific constraints."""
        # Width should be reasonable relative to target
        if params.target.value != 0:
            cv = params.width.value / abs(params.target.value)
            if cv > 2.0:
                self.warnings.append(
                    f"{name}: Very high coefficient of variation ({cv:.2f}), "
                    "scores may be unstable"
                )

        # Target should be positive for most metrics
        if params.target.value < 0:
            self.warnings.append(f"{name}: Negative target value ({params.target.value})")

    def _validate_monotonic(self, name: str, params: MonotonicParameters):
        """Validate monotonic-specific constraints."""
        # Check threshold spread
        spread = params.threshold_high.value - params.threshold_low.value
        if spread < 0.01:
            self.warnings.append(
                f"{name}: Very narrow threshold range ({spread:.4f}), "
                "most scores will be at extremes"
            )

        # Check for reasonable ranges
        if params.threshold_low.value < 0:
            self.warnings.append(f"{name}: Negative low threshold ({params.threshold_low.value})")

    def _validate_threshold(self, name: str, params: ThresholdParameters):
        """Validate threshold-specific constraints."""
        # Check score monotonicity (higher categories should have higher scores)
        if params.scores != sorted(params.scores, reverse=True):
            self.warnings.append(f"{name}: Scores are not monotonically decreasing with threshold")

    def get_report(self) -> str:
        """Get validation report as text."""
        lines = ["Parameter Validation Report", "=" * 40]

        if self.errors:
            lines.append(f"\nERRORS ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  - {err}")

        if self.warnings:
            lines.append(f"\nWARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  - {warn}")

        if not self.errors and not self.warnings:
            lines.append("\nNo issues found.")

        return "\n".join(lines)


class ScoreShiftAnalyzer:
    """Analyzes score shifts between parameter versions."""

    def __init__(self):
        self.validator = ParameterValidator()

    def analyze_shift(
        self,
        old_scores: Dict[str, Dict[str, float]],
        new_scores: Dict[str, Dict[str, float]],
        old_version: str = "unknown",
        new_version: str = "unknown",
    ) -> ScoreShiftReport:
        """
        Analyze score shift between two scoring runs.

        Args:
            old_scores: Dict mapping document_id to dimension scores (old params)
            new_scores: Dict mapping document_id to dimension scores (new params)
            old_version: Version string for old parameters
            new_version: Version string for new parameters

        Returns:
            ScoreShiftReport with detailed analysis
        """
        report = ScoreShiftReport(
            old_params_version=old_version,
            new_params_version=new_version,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        # Analyze each document present in both
        common_docs = set(old_scores.keys()) & set(new_scores.keys())

        for doc_id in sorted(common_docs):
            shift = DocumentScoreShift(
                document_id=doc_id, old_scores=old_scores[doc_id], new_scores=new_scores[doc_id]
            )
            report.add_document_shift(shift)

        report.calculate_summary()

        # Log missing documents
        old_only = set(old_scores.keys()) - set(new_scores.keys())
        new_only = set(new_scores.keys()) - set(old_scores.keys())

        if old_only:
            logger.warning(f"Documents only in old scores: {old_only}")
        if new_only:
            logger.warning(f"Documents only in new scores: {new_only}")

        return report

    def analyze_from_files(self, old_scores_path: Path, new_scores_path: Path) -> ScoreShiftReport:
        """
        Analyze score shift from JSON score files.

        Args:
            old_scores_path: Path to JSON with old scores
            new_scores_path: Path to JSON with new scores

        Returns:
            ScoreShiftReport with detailed analysis
        """
        with open(old_scores_path) as f:
            old_data = json.load(f)

        with open(new_scores_path) as f:
            new_data = json.load(f)

        # Extract scores and versions
        old_version = old_data.get("version", "unknown")
        new_version = new_data.get("version", "unknown")

        old_scores = old_data.get("baselines", old_data.get("scores", {}))
        new_scores = new_data.get("baselines", new_data.get("scores", {}))

        return self.analyze_shift(old_scores, new_scores, old_version, new_version)


def validate_parameter_update(
    old_params: Optional[PercentileParameters],
    new_params: PercentileParameters,
    test_scores: Optional[Dict[str, Dict[str, float]]] = None,
) -> Tuple[bool, str]:
    """
    Validate that a parameter update is safe.

    Args:
        old_params: Previous parameter set (None if first deployment)
        new_params: New parameter set to validate
        test_scores: Optional test document scores for shift analysis

    Returns:
        Tuple of (is_valid, report_text)
    """
    validator = ParameterValidator()

    # Validate new parameters
    is_valid = validator.validate_parameters(new_params)
    report_lines = [validator.get_report()]

    # If we have old params and test scores, do shift analysis
    if old_params and test_scores:
        # Note: This would require re-scoring documents with both param sets
        # For now, we just validate the parameter structure
        report_lines.append("\nNote: Score shift analysis requires re-scoring test documents")

    return is_valid, "\n".join(report_lines)
