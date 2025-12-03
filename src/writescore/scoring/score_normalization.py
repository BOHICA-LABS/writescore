"""
Score normalization module for z-score normalization across dimensions.

Implements AC7 from Story 2.4.1: Normalization Infrastructure.

Purpose:
    Different dimensions use different scoring functions (Gaussian, monotonic, threshold),
    which can lead to clustering artifacts in aggregate scores. Z-score normalization
    ensures scores from all dimensions are on the same scale before weighted aggregation.

Algorithm:
    1. Load dimension statistics (μ, σ) from dimension_stats.json
    2. Apply z-score normalization: normalized = (raw_score - μ) / σ
    3. Transform to 0-100 scale: final = 50 + (normalized * 15)
    4. Clamp to [0, 100] range

Research Rationale:
    - Gaussian dimensions naturally center around their target μ
    - Monotonic dimensions can cluster near 0, 100, or mid-range
    - Threshold dimensions produce discrete bands
    - Normalization equalizes distribution shapes before aggregation
    - Preserves relative ordering within dimensions

Created: 2025-01-24
Story: 2.4.1 (Dimension Scoring Optimization)
"""

import json
import logging
import statistics
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default path to dimension statistics
DEFAULT_STATS_PATH = Path(__file__).parent / "dimension_stats.json"


class ScoreNormalizer:
    """
    Handles z-score normalization for dimension scores.

    Attributes:
        stats: Dict mapping dimension_name -> {mean, stdev, min, max, n_samples}
        enabled: Whether normalization is enabled
    """

    def __init__(self, stats_path: Optional[Path] = None, enabled: bool = True):
        """
        Initialize score normalizer.

        Args:
            stats_path: Path to dimension_stats.json (uses default if None)
            enabled: Whether normalization is enabled
        """
        self.enabled = enabled
        self.stats: Dict[str, Dict[str, float]] = {}

        if enabled:
            self.load_statistics(stats_path or DEFAULT_STATS_PATH)

    def load_statistics(self, stats_path: Path) -> None:
        """
        Load dimension statistics from JSON file.

        Args:
            stats_path: Path to dimension_stats.json

        Raises:
            FileNotFoundError: If stats file doesn't exist
            ValueError: If stats file is invalid
        """
        if not stats_path.exists():
            raise FileNotFoundError(
                f"Dimension statistics file not found: {stats_path}\n"
                f"Run compute_dimension_statistics() to generate it."
            )

        try:
            with open(stats_path) as f:
                data = json.load(f)

            # Validate structure
            if "dimensions" not in data:
                raise ValueError("Invalid stats file: missing 'dimensions' key")

            self.stats = data["dimensions"]

            # Validate each dimension has required fields
            required_fields = {"mean", "stdev"}
            for dim_name, dim_stats in self.stats.items():
                missing = required_fields - set(dim_stats.keys())
                if missing:
                    raise ValueError(f"Dimension {dim_name} missing required fields: {missing}")

            logger.info(f"Loaded statistics for {len(self.stats)} dimensions from {stats_path}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in stats file: {e}") from e

    def normalize_score(self, raw_score: float, dimension_name: str) -> float:
        """
        Apply z-score normalization to a raw dimension score.

        Args:
            raw_score: Raw score from dimension.calculate_score() (0-100)
            dimension_name: Name of dimension (e.g., 'perplexity', 'burstiness')

        Returns:
            Normalized score (0-100), or raw_score if normalization disabled

        Algorithm:
            1. Z-score: z = (raw_score - μ) / σ
            2. Transform to 0-100: normalized = 50 + (z * 15)
            3. Clamp to [0, 100]

        Notes:
            - If normalization disabled, returns raw_score unchanged
            - If dimension not in stats, returns raw_score with warning
            - Uses stdev = 1.0 fallback if σ = 0 to avoid division by zero
        """
        if not self.enabled:
            return raw_score

        # Check if dimension has statistics
        if dimension_name not in self.stats:
            logger.warning(
                f"No statistics for dimension '{dimension_name}', returning raw score. "
                f"Run compute_dimension_statistics() to generate stats."
            )
            return raw_score

        dim_stats = self.stats[dimension_name]
        mean = dim_stats["mean"]
        stdev = dim_stats["stdev"]

        # Avoid division by zero (use stdev=1.0 as fallback)
        if stdev == 0.0:
            logger.warning(f"Dimension '{dimension_name}' has stdev=0, using stdev=1.0 fallback")
            stdev = 1.0

        # Apply z-score normalization
        z_score = (raw_score - mean) / stdev

        # Transform to 0-100 scale (mean=50, stdev=15)
        # This maps ±3σ to roughly [5, 95] range
        normalized = 50.0 + (z_score * 15.0)

        # Clamp to valid range
        normalized = max(0.0, min(100.0, normalized))

        return normalized

    def compute_dimension_statistics(
        self, dimension_scores: Dict[str, List[float]], output_path: Optional[Path] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute mean and stdev for each dimension from validation set.

        Args:
            dimension_scores: Dict mapping dimension_name -> list of scores
            output_path: Path to save statistics JSON (uses default if None)

        Returns:
            Dict mapping dimension_name -> {mean, stdev, min, max, n_samples}

        Example:
            >>> scores = {
            ...     'perplexity': [45.2, 52.1, 48.9, 51.0, 49.5],
            ...     'burstiness': [38.7, 42.3, 40.1, 39.8, 41.2]
            ... }
            >>> stats = normalizer.compute_dimension_statistics(scores)
            >>> print(stats['perplexity'])
            {'mean': 49.34, 'stdev': 2.45, 'min': 45.2, 'max': 52.1, 'n_samples': 5}
        """
        computed_stats = {}

        for dim_name, scores in dimension_scores.items():
            if not scores:
                logger.warning(f"No scores for dimension '{dim_name}', skipping")
                continue

            if len(scores) < 2:
                logger.warning(
                    f"Dimension '{dim_name}' has only {len(scores)} sample(s), "
                    f"need at least 2 for stdev calculation"
                )
                continue

            computed_stats[dim_name] = {
                "mean": round(statistics.mean(scores), 2),
                "stdev": round(statistics.stdev(scores), 2),
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
                "n_samples": len(scores),
            }

        # Save to file if requested
        if output_path:
            self._save_statistics(computed_stats, output_path)

        # Update internal stats
        self.stats = computed_stats

        logger.info(
            f"Computed statistics for {len(computed_stats)} dimensions " f"from validation set"
        )

        return computed_stats

    def _save_statistics(
        self, computed_stats: Dict[str, Dict[str, float]], output_path: Path
    ) -> None:
        """Save computed statistics to JSON file."""
        from datetime import datetime

        output_data = {
            "_metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "story": "2.4.1",
                "description": "Dimension score normalization statistics (mean, stdev) computed from validation set",
                "validation_set_size": sum(s["n_samples"] for s in computed_stats.values()),
                "note": "Generated by compute_dimension_statistics()",
            },
            "dimensions": computed_stats,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Saved dimension statistics to {output_path}")


# Singleton instance for module-level convenience functions
_default_normalizer: Optional[ScoreNormalizer] = None


def get_normalizer(enabled: bool = True) -> ScoreNormalizer:
    """
    Get singleton ScoreNormalizer instance.

    Args:
        enabled: Whether normalization should be enabled

    Returns:
        ScoreNormalizer instance (cached)
    """
    global _default_normalizer

    if _default_normalizer is None or _default_normalizer.enabled != enabled:
        _default_normalizer = ScoreNormalizer(enabled=enabled)

    return _default_normalizer


def normalize_score(raw_score: float, dimension_name: str, enabled: bool = True) -> float:
    """
    Convenience function for normalizing a single score.

    Args:
        raw_score: Raw score from dimension.calculate_score()
        dimension_name: Name of dimension
        enabled: Whether normalization is enabled

    Returns:
        Normalized score (0-100)
    """
    normalizer = get_normalizer(enabled=enabled)
    return normalizer.normalize_score(raw_score, dimension_name)
