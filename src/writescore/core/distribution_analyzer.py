"""
Distribution analysis for percentile-anchored parameters.

Analyzes validation dataset across all dimensions to compute empirical
distributions, percentiles, and statistics for parameter derivation.

Created in Story 2.5 Task 3.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from writescore.core.dataset import ValidationDataset
from writescore.core.dimension_loader import DimensionLoader
from writescore.core.dimension_registry import DimensionRegistry

logger = logging.getLogger(__name__)


@dataclass
class DimensionStatistics:
    """
    Statistical summary for a dimension's metric values.

    Attributes:
        dimension_name: Name of the dimension
        metric_name: Primary metric name (e.g., 'variance', 'ratio')
        values: All observed metric values
        mean: Arithmetic mean
        median: 50th percentile
        stdev: Standard deviation
        iqr: Interquartile range (p75 - p25)
        percentiles: Dictionary of percentiles (p10, p25, p50, p75, p90)
        min_val: Minimum value
        max_val: Maximum value
        count: Number of observations
        skewness: Distribution skewness
        kurtosis: Distribution kurtosis
    """

    dimension_name: str
    metric_name: str
    values: List[float] = field(default_factory=list)
    mean: float = 0.0
    median: float = 0.0
    stdev: float = 0.0
    iqr: float = 0.0
    percentiles: Dict[str, float] = field(default_factory=dict)
    min_val: float = 0.0
    max_val: float = 0.0
    count: int = 0
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

    def compute(self) -> None:
        """Compute all statistics from values."""
        if not self.values:
            logger.warning(f"No values for {self.dimension_name}.{self.metric_name}")
            return

        arr = np.array(self.values)

        # Basic statistics
        self.mean = float(np.mean(arr))
        self.median = float(np.median(arr))
        self.stdev = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        self.min_val = float(np.min(arr))
        self.max_val = float(np.max(arr))
        self.count = len(arr)

        # Percentiles
        self.percentiles = {
            "p10": float(np.percentile(arr, 10)),
            "p25": float(np.percentile(arr, 25)),
            "p50": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
            "p90": float(np.percentile(arr, 90)),
        }

        self.iqr = self.percentiles["p75"] - self.percentiles["p25"]

        # Higher-order statistics
        if len(arr) >= 3:
            from scipy import stats

            self.skewness = float(stats.skew(arr))
            self.kurtosis = float(stats.kurtosis(arr))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension_name": self.dimension_name,
            "metric_name": self.metric_name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "stdev": round(self.stdev, 4),
            "iqr": round(self.iqr, 4),
            "percentiles": {k: round(v, 4) for k, v in self.percentiles.items()},
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "skewness": round(self.skewness, 4) if self.skewness is not None else None,
            "kurtosis": round(self.kurtosis, 4) if self.kurtosis is not None else None,
        }


@dataclass
class DistributionAnalysis:
    """
    Complete distribution analysis results for all dimensions.

    Attributes:
        dataset_version: Version of validation dataset analyzed
        timestamp: When analysis was performed
        dimensions: Dictionary mapping dimension names to label-specific statistics
        metadata: Additional metadata
    """

    dataset_version: str
    timestamp: str
    dimensions: Dict[str, Dict[str, DimensionStatistics]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dimension_stats(
        self, dimension_name: str, label: str, stats: DimensionStatistics
    ) -> None:
        """Add statistics for a dimension and label."""
        if dimension_name not in self.dimensions:
            self.dimensions[dimension_name] = {}
        self.dimensions[dimension_name][label] = stats

    def get_dimension_stats(self, dimension_name: str, label: str) -> Optional[DimensionStatistics]:
        """Get statistics for specific dimension and label."""
        return self.dimensions.get(dimension_name, {}).get(label)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        dimensions_dict = {}
        for dim_name, label_stats in self.dimensions.items():
            dimensions_dict[dim_name] = {
                label: stats.to_dict() for label, stats in label_stats.items()
            }

        return {
            "dataset_version": self.dataset_version,
            "timestamp": self.timestamp,
            "dimensions": dimensions_dict,
            "metadata": self.metadata,
        }

    def save_json(self, output_path: Path) -> None:
        """Save analysis to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Saved distribution analysis to {output_path}")

    @classmethod
    def load_json(cls, input_path: Path) -> "DistributionAnalysis":
        """Load analysis from JSON file."""
        with open(input_path) as f:
            data = json.load(f)

        analysis = cls(
            dataset_version=data["dataset_version"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )

        # Reconstruct dimension statistics
        for dim_name, label_stats_dict in data["dimensions"].items():
            for label, stats_dict in label_stats_dict.items():
                stats = DimensionStatistics(
                    dimension_name=stats_dict["dimension_name"],
                    metric_name=stats_dict["metric_name"],
                    count=stats_dict["count"],
                    mean=stats_dict["mean"],
                    median=stats_dict["median"],
                    stdev=stats_dict["stdev"],
                    iqr=stats_dict["iqr"],
                    percentiles=stats_dict["percentiles"],
                    min_val=stats_dict["min"],
                    max_val=stats_dict["max"],
                    skewness=stats_dict.get("skewness"),
                    kurtosis=stats_dict.get("kurtosis"),
                )
                analysis.add_dimension_stats(dim_name, label, stats)

        return analysis


class DistributionAnalyzer:
    """
    Analyzes validation dataset to compute empirical distributions.

    Runs all dimension analyzers on validation documents, collects metric
    values, computes statistics, and generates percentile data for parameter
    derivation.
    """

    def __init__(self, registry: Optional[DimensionRegistry] = None):
        """
        Initialize analyzer.

        Args:
            registry: DimensionRegistry with loaded dimensions. If None, creates new.
        """
        self.registry = registry or DimensionRegistry
        if self.registry.get_count() == 0:
            # Load dimensions if registry is empty
            loader = DimensionLoader()
            loader.load_from_profile("full")

    def analyze_dataset(
        self, dataset: ValidationDataset, dimension_names: Optional[List[str]] = None
    ) -> DistributionAnalysis:
        """
        Analyze validation dataset across all dimensions.

        Args:
            dataset: ValidationDataset to analyze
            dimension_names: Optional list of dimensions to analyze. If None, analyzes all.

        Returns:
            DistributionAnalysis with complete statistics
        """
        logger.info(f"Starting distribution analysis on dataset {dataset.version}")
        logger.info(f"Dataset: {len(dataset.documents)} documents")

        # Determine which dimensions to analyze
        if dimension_names is None:
            all_dims = self.registry.get_all()
            dimension_names = [dim.dimension_name for dim in all_dims]

        logger.info(f"Analyzing {len(dimension_names)} dimensions")

        # Collect metric values for each dimension, split by label
        metric_values = self._collect_metric_values(dataset, dimension_names)

        # Compute statistics for each dimension and label
        analysis = DistributionAnalysis(
            dataset_version=dataset.version,
            timestamp=datetime.now().isoformat(),
            metadata={
                "total_documents": len(dataset.documents),
                "dimensions_analyzed": len(dimension_names),
            },
        )

        for dim_name in dimension_names:
            for label in ["human", "ai", "combined"]:
                if label in metric_values.get(dim_name, {}):
                    stats = self._compute_statistics(
                        dim_name, label, metric_values[dim_name][label]
                    )
                    analysis.add_dimension_stats(dim_name, label, stats)

        logger.info("Distribution analysis complete")
        return analysis

    def _collect_metric_values(
        self, dataset: ValidationDataset, dimension_names: List[str]
    ) -> Dict[str, Dict[str, Dict[str, List[float]]]]:
        """
        Collect metric values for each dimension, split by label.

        Returns:
            Dict[dimension_name][label][metric_name] = List[values]
        """
        # Structure: dimension -> label -> metric_name -> values
        values: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        # Process each document
        for doc in dataset.documents:
            for dim_name in dimension_names:
                try:
                    metrics = self._analyze_document(dim_name, doc.text)

                    # Extract primary metric value(s)
                    metric_dict = self._extract_metrics(dim_name, metrics)

                    # Add to label-specific and combined lists
                    for metric_name, value in metric_dict.items():
                        values[dim_name][doc.label][metric_name].append(value)
                        values[dim_name]["combined"][metric_name].append(value)

                except Exception as e:
                    logger.warning(f"Error analyzing {dim_name} on doc {doc.id}: {e}")
                    continue

        # Convert nested defaultdicts to regular dicts for type compatibility
        return {
            dim: {label: dict(metrics) for label, metrics in labels.items()}
            for dim, labels in values.items()
        }

    def _analyze_document(self, dimension_name: str, text: str) -> Dict[str, Any]:
        """Run dimension analyzer on document text."""
        dimension = self.registry.get(dimension_name)
        lines = text.split("\n")
        return dimension.analyze(text, lines)

    def _extract_metrics(self, dimension_name: str, metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key metric value(s) from dimension metrics dict.

        Returns dict of metric_name -> value. Most dimensions have one primary
        metric, but some may have multiple.
        """
        # Map dimension names to their primary metric keys
        # This is based on the existing dimension implementations
        metric_mapping = {
            "burstiness": ["variance"],
            "lexical": ["type_token_ratio"],
            "advanced_lexical": ["gltr_rank_10_ratio"],
            "perplexity": ["perplexity"],
            "predictability": ["avg_rank"],
            "readability": ["flesch_reading_ease"],
            "sentiment": ["sentiment_variance"],
            "syntactic": ["avg_depth"],
            "structure": ["avg_paragraph_length"],
            "transition_marker": ["density"],
            "voice": ["passive_ratio"],
            "formatting": ["em_dash_density"],
            "semantic_coherence": ["coherence_score"],
            "pragmatic_markers": ["hedging_density"],
            "ai_vocabulary": ["ai_vocab_density"],
            "figurative_language": ["figurative_ratio"],
        }

        result = {}
        metric_keys = metric_mapping.get(dimension_name, [])

        for key in metric_keys:
            if key in metrics:
                value = metrics[key]
                # Ensure it's a number
                if isinstance(value, (int, float)):
                    result[key] = float(value)

        # If no mapped keys found, try to find any numeric value
        if not result:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    result[key] = float(value)
                    break

        return result

    def _compute_statistics(
        self, dimension_name: str, label: str, metric_values: Dict[str, List[float]]
    ) -> DimensionStatistics:
        """Compute statistics for dimension metric values."""
        # Use first metric (most dimensions have only one primary metric)
        metric_name = list(metric_values.keys())[0]
        values = metric_values[metric_name]

        stats = DimensionStatistics(
            dimension_name=dimension_name, metric_name=metric_name, values=values
        )
        stats.compute()

        logger.info(
            f"{dimension_name} ({label}): n={stats.count}, "
            f"mean={stats.mean:.2f}, p50={stats.percentiles.get('p50', 0):.2f}"
        )

        return stats

    def generate_summary_report(
        self, analysis: DistributionAnalysis, output_path: Optional[Path] = None
    ) -> str:
        """
        Generate human-readable summary report.

        Args:
            analysis: DistributionAnalysis results
            output_path: Optional path to save report

        Returns:
            Report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DISTRIBUTION ANALYSIS SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Dataset Version: {analysis.dataset_version}")
        lines.append(f"Timestamp: {analysis.timestamp}")
        lines.append(f"Total Documents: {analysis.metadata.get('total_documents', 0)}")
        lines.append(f"Dimensions Analyzed: {analysis.metadata.get('dimensions_analyzed', 0)}")
        lines.append("")

        for dim_name in sorted(analysis.dimensions.keys()):
            lines.append(f"\n{dim_name.upper()}")
            lines.append("-" * 80)

            for label in ["human", "ai", "combined"]:
                stats = analysis.get_dimension_stats(dim_name, label)
                if not stats:
                    continue

                lines.append(f"\n  {label.capitalize()} Distribution:")
                lines.append(f"    Count: {stats.count}")
                lines.append(f"    Mean: {stats.mean:.4f}, Stdev: {stats.stdev:.4f}")
                lines.append(f"    Median (p50): {stats.median:.4f}")
                lines.append(f"    IQR: {stats.iqr:.4f} (p75 - p25)")
                lines.append("    Percentiles:")
                for p, val in sorted(stats.percentiles.items()):
                    lines.append(f"      {p}: {val:.4f}")
                lines.append(f"    Range: [{stats.min_val:.4f}, {stats.max_val:.4f}]")
                if stats.skewness is not None:
                    lines.append(f"    Skewness: {stats.skewness:.4f}")
                if stats.kurtosis is not None:
                    lines.append(f"    Kurtosis: {stats.kurtosis:.4f}")

        lines.append("\n" + "=" * 80)

        report = "\n".join(lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Saved summary report to {output_path}")

        return report
