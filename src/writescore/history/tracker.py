"""
Score history tracking module (v2.0).

This module handles comprehensive tracking of score history over time,
allowing users to monitor improvements and trends across all 33 dimensions,
tier scores, and raw metrics.

Version History:
- v1.0: Basic aggregate scores (quality_score, detection_risk)
- v2.0: Comprehensive tracking with dimension scores, tier scores, and raw metrics
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DimensionScore:
    """
    Individual dimension score for history tracking.

    Attributes:
        score: Actual score achieved (0 to max_score)
        max_score: Maximum possible score for this dimension
        percentage: Score as percentage (0-100)
        raw_value: Original metric value (e.g., 0.72 for MATTR, 12.4 for AI vocab)
        interpretation: Quality interpretation ('EXCELLENT', 'GOOD', 'FAIR', 'POOR')
    """

    score: float
    max_score: float
    percentage: float
    raw_value: Optional[float] = None
    interpretation: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "raw_value": self.raw_value,
            "interpretation": self.interpretation,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DimensionScore":
        """Reconstruct from dict (JSON deserialization)."""
        return cls(
            score=data["score"],
            max_score=data["max_score"],
            percentage=data["percentage"],
            raw_value=data.get("raw_value"),
            interpretation=data.get("interpretation", ""),
        )


@dataclass
class HistoricalScore:
    """
    Comprehensive historical score tracking (v2.0).

    Captures all dimensions, tier scores, and raw metrics for complete
    optimization journey tracking.
    """

    # Metadata
    timestamp: str
    total_words: int
    total_sentences: int = 0
    total_paragraphs: int = 0
    notes: str = ""
    history_version: str = "2.0"
    analysis_mode: str = "adaptive"  # Analysis mode used (fast, adaptive, sampling, full)
    analysis_time_seconds: float = 0.0  # Time taken for analysis

    # Aggregate scores (v1.0 compatibility)
    detection_risk: float = 0.0
    quality_score: float = 0.0
    detection_interpretation: str = ""
    quality_interpretation: str = ""

    # Tier scores (v2.0) - 4 tiers
    tier1_score: float = 0.0  # Advanced Detection (max 70 pts)
    tier2_score: float = 0.0  # Core Patterns (max 74 pts)
    tier3_score: float = 0.0  # Supporting Indicators (max 46 pts)
    tier4_score: float = 0.0  # Advanced Structural (max 10 pts)

    # All dimension scores (v2.0) - 33 dimensions
    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)

    # Key raw metrics for detailed trend analysis (v2.0)
    raw_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_words": self.total_words,
            "total_sentences": self.total_sentences,
            "total_paragraphs": self.total_paragraphs,
            "notes": self.notes,
            "history_version": self.history_version,
            "analysis_mode": self.analysis_mode,
            "analysis_time_seconds": self.analysis_time_seconds,
            "detection_risk": self.detection_risk,
            "quality_score": self.quality_score,
            "detection_interpretation": self.detection_interpretation,
            "quality_interpretation": self.quality_interpretation,
            "tier1_score": self.tier1_score,
            "tier2_score": self.tier2_score,
            "tier3_score": self.tier3_score,
            "tier4_score": self.tier4_score,
            "dimensions": {name: dim.to_dict() for name, dim in self.dimensions.items()},
            "raw_metrics": self.raw_metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HistoricalScore":
        """
        Reconstruct from dict with backward compatibility.

        Supports both v1.0 (aggregate only) and v2.0 (comprehensive) formats.
        """
        # Detect version
        version = data.get("history_version", "1.0")

        # Reconstruct dimensions if present
        dimensions = {}
        if "dimensions" in data:
            for name, dim_data in data["dimensions"].items():
                dimensions[name] = DimensionScore.from_dict(dim_data)

        return cls(
            timestamp=data["timestamp"],
            total_words=data.get("total_words", 0),
            total_sentences=data.get("total_sentences", 0),
            total_paragraphs=data.get("total_paragraphs", 0),
            notes=data.get("notes", ""),
            history_version=version,
            analysis_mode=data.get("analysis_mode", "adaptive"),
            analysis_time_seconds=data.get("analysis_time_seconds", 0.0),
            detection_risk=data.get("detection_risk", 0.0),
            quality_score=data.get("quality_score", 0.0),
            detection_interpretation=data.get("detection_interpretation", ""),
            quality_interpretation=data.get("quality_interpretation", ""),
            tier1_score=data.get("tier1_score", 0.0),
            tier2_score=data.get("tier2_score", 0.0),
            tier3_score=data.get("tier3_score", 0.0),
            tier4_score=data.get("tier4_score", 0.0),
            dimensions=dimensions,
            raw_metrics=data.get("raw_metrics", {}),
        )


@dataclass
class ScoreHistory:
    """
    Score history for a document with comprehensive tracking.

    Supports both v1.0 (legacy) and v2.0 (comprehensive) score formats.
    """

    file_path: str
    scores: List[HistoricalScore] = field(default_factory=list)

    def add_score(self, score, results=None, notes: str = ""):
        """
        Add comprehensive score to history (v2.0).

        Args:
            score: DualScore object with all dimension information
            results: AnalysisResults object with raw metrics
            notes: Optional notes about this iteration
        """
        # Extract all dimension scores from DualScore
        dimensions = {}
        tier_scores = [0.0, 0.0, 0.0, 0.0]  # 4 tiers

        for tier_idx, category in enumerate(score.categories):
            tier_total = 0.0
            for dimension in category.dimensions:
                dimensions[dimension.name] = DimensionScore(
                    score=dimension.score,
                    max_score=dimension.max_score,
                    percentage=dimension.percentage,
                    raw_value=dimension.raw_value,
                    interpretation=dimension.impact,
                )
                tier_total += dimension.score
            if tier_idx < 4:
                tier_scores[tier_idx] = tier_total

        # Extract key raw metrics from AnalysisResults
        raw_metrics = {}
        total_sentences = 0
        total_paragraphs = 0
        if results:
            # Core metrics that exist in current implementation
            raw_metrics["ai_vocabulary_per_1k"] = getattr(results, "ai_vocabulary_per_1k", 0.0)
            raw_metrics["sentence_stdev"] = getattr(results, "sentence_stdev", 0.0)
            raw_metrics["em_dashes_per_page"] = getattr(results, "em_dashes_per_page", 0.0)
            raw_metrics["heading_parallelism"] = getattr(results, "heading_parallelism_score", 0.0)
            raw_metrics["paragraph_cv"] = getattr(results, "paragraph_cv", 0.0)
            raw_metrics["section_variance_pct"] = getattr(results, "section_variance_pct", 0.0)
            raw_metrics["mattr"] = getattr(results, "mattr", 0.0)
            raw_metrics["rttr"] = getattr(results, "rttr", 0.0)
            raw_metrics["blockquote_per_page"] = getattr(results, "blockquote_per_page", 0.0)
            raw_metrics["generic_link_ratio"] = getattr(results, "generic_link_ratio", 0.0)
            raw_metrics["bold_per_1k"] = getattr(results, "bold_per_1k", 0.0)
            raw_metrics["italic_per_1k"] = getattr(results, "italic_per_1k", 0.0)

            # Extract counts
            total_sentences = getattr(results, "total_sentences", 0)
            total_paragraphs = getattr(results, "total_paragraphs", 0)

        self.scores.append(
            HistoricalScore(
                timestamp=score.timestamp,
                detection_risk=score.detection_risk,
                quality_score=score.quality_score,
                detection_interpretation=score.detection_interpretation,
                quality_interpretation=score.quality_interpretation,
                total_words=score.total_words,
                total_sentences=total_sentences,
                total_paragraphs=total_paragraphs,
                notes=notes,
                history_version="2.0",
                tier1_score=tier_scores[0],
                tier2_score=tier_scores[1],
                tier3_score=tier_scores[2],
                tier4_score=tier_scores[3],
                dimensions=dimensions,
                raw_metrics=raw_metrics,
            )
        )

    def get_trend(self) -> Dict[str, Any]:
        """
        Get aggregate trend direction (backward compatible with v1.0).

        Returns:
            Dict with detection and quality trends
        """
        if len(self.scores) < 2:
            return {"detection": "N/A", "quality": "N/A"}

        det_change = self.scores[-1].detection_risk - self.scores[-2].detection_risk
        qual_change = self.scores[-1].quality_score - self.scores[-2].quality_score

        return {
            "detection": "IMPROVING"
            if det_change < -1
            else "WORSENING"
            if det_change > 1
            else "STABLE",
            "quality": "IMPROVING"
            if qual_change > 1
            else "DECLINING"
            if qual_change < -1
            else "STABLE",
            "detection_change": round(det_change, 1),
            "quality_change": round(qual_change, 1),
        }

    def get_dimension_trend(self, dimension_name: str) -> Dict:
        """
        Get trend for specific dimension (v2.0).

        Args:
            dimension_name: Name of dimension to analyze

        Returns:
            Dict with trend information including change, first/last scores, and raw values
        """
        if len(self.scores) < 2:
            return {"trend": "N/A", "change": 0.0}

        # Only analyze v2.0 scores
        v2_scores = [s for s in self.scores if s.history_version == "2.0"]
        if len(v2_scores) < 2:
            return {"trend": "N/A", "change": 0.0}

        # Get dimension from first and last v2.0 scores
        first_dim = v2_scores[0].dimensions.get(dimension_name)
        last_dim = v2_scores[-1].dimensions.get(dimension_name)

        if not first_dim or not last_dim:
            return {"trend": "N/A", "change": 0.0}

        change = last_dim.score - first_dim.score

        return {
            "trend": "IMPROVING" if change > 1 else "DECLINING" if change < -1 else "STABLE",
            "change": round(change, 1),
            "first_score": first_dim.score,
            "last_score": last_dim.score,
            "first_raw": first_dim.raw_value,
            "last_raw": last_dim.raw_value,
            "percentage_change": round(last_dim.percentage - first_dim.percentage, 1),
        }

    def get_tier_trends(self) -> Dict[str, Dict]:
        """
        Get trend analysis for all tiers (v2.0).

        Returns:
            Dict with tier names and their trend information
        """
        if len(self.scores) < 2:
            return {}

        v2_scores = [s for s in self.scores if s.history_version == "2.0"]
        if len(v2_scores) < 2:
            return {}

        first = v2_scores[0]
        last = v2_scores[-1]

        tier_info = [
            ("Tier 1 (Advanced Detection)", "tier1_score", 70),
            ("Tier 2 (Core Patterns)", "tier2_score", 74),
            ("Tier 3 (Supporting Indicators)", "tier3_score", 46),
            ("Tier 4 (Advanced Structural)", "tier4_score", 10),
        ]

        trends = {}
        for name, attr, max_score in tier_info:
            first_val = getattr(first, attr, 0.0)
            last_val = getattr(last, attr, 0.0)
            change = last_val - first_val

            trends[name] = {
                "first": first_val,
                "last": last_val,
                "change": round(change, 1),
                "max": max_score,
                "trend": "IMPROVING" if change > 1 else "DECLINING" if change < -1 else "STABLE",
            }

        return trends

    def get_plateaued_dimensions(self, lookback: int = 3, threshold: float = 1.0) -> List[str]:
        """
        Identify dimensions that have plateaued (v2.0).

        Args:
            lookback: Number of recent iterations to analyze
            threshold: Minimum change to not be considered plateaued

        Returns:
            List of dimension names that have plateaued
        """
        if len(self.scores) < lookback:
            return []

        v2_scores = [s for s in self.scores if s.history_version == "2.0"]
        if len(v2_scores) < lookback:
            return []

        recent_scores = v2_scores[-lookback:]
        plateaued = []

        # Get all dimension names
        if not recent_scores[0].dimensions:
            return []

        for dim_name in recent_scores[0].dimensions:
            # Check if dimension exists in all recent scores
            if not all(dim_name in score.dimensions for score in recent_scores):
                continue

            # Calculate max change across lookback window
            scores = [score.dimensions[dim_name].score for score in recent_scores]
            max_change = max(scores) - min(scores)

            if max_change < threshold:
                plateaued.append(dim_name)

        return plateaued

    def export_to_csv(self, output_path: str):
        """
        Export history to CSV for analysis in Excel/Pandas/R.

        Args:
            output_path: Path to output CSV file
        """
        import csv

        if not self.scores:
            return

        # Build header
        header = [
            "timestamp",
            "iteration",
            "total_words",
            "total_sentences",
            "total_paragraphs",
            "notes",
            "history_version",
            "quality_score",
            "detection_risk",
            "tier1_score",
            "tier2_score",
            "tier3_score",
            "tier4_score",
        ]

        # Add dimension scores (use first v2.0 score to get dimension names)
        v2_scores = [s for s in self.scores if s.history_version == "2.0" and s.dimensions]
        if v2_scores:
            dim_names = sorted(v2_scores[0].dimensions.keys())
            header.extend([f"{name}_score" for name in dim_names])
            header.extend([f"{name}_pct" for name in dim_names])

            # Add raw metrics
            if v2_scores[0].raw_metrics:
                metric_names = sorted(v2_scores[0].raw_metrics.keys())
                header.extend(metric_names)

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            writer.writeheader()

            for i, score in enumerate(self.scores, start=1):
                row = {
                    "timestamp": score.timestamp,
                    "iteration": i,
                    "total_words": score.total_words,
                    "total_sentences": score.total_sentences,
                    "total_paragraphs": score.total_paragraphs,
                    "notes": score.notes,
                    "history_version": score.history_version,
                    "quality_score": score.quality_score,
                    "detection_risk": score.detection_risk,
                    "tier1_score": score.tier1_score,
                    "tier2_score": score.tier2_score,
                    "tier3_score": score.tier3_score,
                    "tier4_score": score.tier4_score,
                }

                # Add dimension scores
                for name, dim in score.dimensions.items():
                    row[f"{name}_score"] = dim.score
                    row[f"{name}_pct"] = dim.percentage

                # Add raw metrics
                for name, value in score.raw_metrics.items():
                    row[name] = value

                writer.writerow(row)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {"file_path": self.file_path, "scores": [score.to_dict() for score in self.scores]}

    @classmethod
    def from_dict(cls, data: Dict) -> "ScoreHistory":
        """Reconstruct from dict with backward compatibility."""
        scores = [HistoricalScore.from_dict(s) for s in data.get("scores", [])]
        return cls(file_path=data["file_path"], scores=scores)


def load_score_history(file_path: str) -> ScoreHistory:
    """
    Load score history from JSON file.

    Supports both v1.0 and v2.0 formats with automatic detection.

    Args:
        file_path: Path to the markdown file (history stored as .file.history.json)

    Returns:
        ScoreHistory object
    """
    history_file = Path(file_path).parent / f".{Path(file_path).name}.history.json"

    if not history_file.exists():
        return ScoreHistory(file_path=file_path)

    try:
        with open(history_file, encoding="utf-8") as f:
            data = json.load(f)
            return ScoreHistory.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not load history from {history_file}: {e}")
        return ScoreHistory(file_path=file_path)


def save_score_history(history: ScoreHistory):
    """
    Save score history to JSON file.

    Args:
        history: ScoreHistory object to save
    """
    history_file = Path(history.file_path).parent / f".{Path(history.file_path).name}.history.json"

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history.to_dict(), f, indent=2)
