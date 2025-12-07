"""
Percentile-anchored parameter infrastructure for adaptive scoring.

This module provides the PercentileParameters class and related infrastructure
for storing, validating, and working with percentile-based scoring parameters
that automatically adapt to empirical distributions.

Created in Story 2.5 to enable automatic recalibration when new AI models emerge.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ScoringType(str, Enum):
    """Valid scoring algorithm types for dimensions."""

    GAUSSIAN = "gaussian"
    MONOTONIC = "monotonic"
    THRESHOLD = "threshold"


class PercentileSource(str, Enum):
    """Source type for parameter values."""

    PERCENTILE = "percentile"  # Derived from percentile (e.g., p50_human)
    STDEV = "stdev"  # Derived from standard deviation
    IQR = "iqr"  # Derived from interquartile range
    LITERATURE = "literature"  # Manual value from research literature
    FALLBACK = "fallback"  # Fallback value due to insufficient data


@dataclass
class ParameterValue:
    """
    Represents a single parameter value with its derivation metadata.

    Attributes:
        value: The numeric parameter value
        source: How this value was derived (percentile, stdev, etc.)
        percentile: Which percentile was used (if source=PERCENTILE), e.g., "p50_human"
        description: Human-readable description
    """

    value: float
    source: PercentileSource
    percentile: Optional[str] = None
    description: Optional[str] = None

    def validate(self) -> None:
        """Validate parameter value constraints."""
        if self.source == PercentileSource.PERCENTILE and not self.percentile:
            raise ValueError("Percentile source requires percentile attribute")

        # Additional validation can be added here
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"Parameter value must be numeric, got {type(self.value)}")


@dataclass
class GaussianParameters:
    """
    Parameters for Gaussian (bell curve) scoring.

    Used for dimensions with symmetric optima (e.g., burstiness, sentiment).
    Score is highest at target and decreases with distance from target.

    Attributes:
        target: Optimal value (typically p50 of human distribution)
        width: Spread/tolerance (typically stdev or IQR/1.35)
    """

    target: ParameterValue
    width: ParameterValue

    def validate(self) -> None:
        """Validate Gaussian parameter constraints."""
        self.target.validate()
        self.width.validate()

        if self.width.value <= 0:
            raise ValueError(f"Gaussian width must be > 0, got {self.width.value}")


@dataclass
class MonotonicParameters:
    """
    Parameters for monotonic (linear) scoring.

    Used for "more is better" or "less is better" dimensions.
    Score increases/decreases linearly between thresholds.

    Attributes:
        threshold_low: Lower threshold (typically p25 of human)
        threshold_high: Upper threshold (typically p75 of human)
        direction: "increasing" (higher is better) or "decreasing" (lower is better)
    """

    threshold_low: ParameterValue
    threshold_high: ParameterValue
    direction: str = "increasing"

    def validate(self) -> None:
        """Validate monotonic parameter constraints."""
        self.threshold_low.validate()
        self.threshold_high.validate()

        if self.threshold_low.value >= self.threshold_high.value:
            raise ValueError(
                f"threshold_low ({self.threshold_low.value}) must be < "
                f"threshold_high ({self.threshold_high.value})"
            )

        if self.direction not in ("increasing", "decreasing"):
            raise ValueError(
                f"Direction must be 'increasing' or 'decreasing', got '{self.direction}'"
            )


@dataclass
class ThresholdParameters:
    """
    Parameters for discrete threshold scoring.

    Used for count-based dimensions with multiple quality tiers.

    Attributes:
        thresholds: List of threshold values defining category boundaries
        labels: Labels for each category (e.g., ["excellent", "good", "concerning", "poor"])
        scores: Score for each category (e.g., [100, 75, 40, 10])
    """

    thresholds: List[ParameterValue]
    labels: List[str]
    scores: List[float]

    def validate(self) -> None:
        """Validate threshold parameter constraints."""
        for threshold in self.thresholds:
            threshold.validate()

        # Check monotonicity of thresholds
        threshold_values = [t.value for t in self.thresholds]
        if threshold_values != sorted(threshold_values):
            raise ValueError(f"Thresholds must be in ascending order: {threshold_values}")

        # Check consistency of array lengths
        if len(self.labels) != len(self.scores):
            raise ValueError(
                f"Labels ({len(self.labels)}) and scores ({len(self.scores)}) "
                f"must have same length"
            )

        # Thresholds define N+1 categories (N thresholds create N+1 ranges)
        expected_categories = len(self.thresholds) + 1
        if len(self.labels) != expected_categories:
            raise ValueError(
                f"Expected {expected_categories} categories for {len(self.thresholds)} "
                f"thresholds, got {len(self.labels)} labels"
            )

        # Check score validity (0-100 range)
        for score in self.scores:
            if not (0 <= score <= 100):
                raise ValueError(f"Scores must be in range [0, 100], got {score}")


@dataclass
class DimensionParameters:
    """
    Complete parameter set for a single dimension.

    Attributes:
        dimension_name: Name of the dimension
        scoring_type: Type of scoring algorithm
        parameters: The actual parameters (Gaussian, Monotonic, or Threshold)
        version: Parameter version for tracking
        validation_dataset_version: Version of validation dataset used
        timestamp: When these parameters were derived
        notes: Optional notes about derivation or special handling
    """

    dimension_name: str
    scoring_type: ScoringType
    parameters: Any  # Union[GaussianParameters, MonotonicParameters, ThresholdParameters]
    version: str = "1.0"
    validation_dataset_version: Optional[str] = None
    timestamp: Optional[str] = None
    notes: Optional[str] = None

    def validate(self) -> None:
        """Validate dimension parameters."""
        # Validate parameters match scoring type
        if self.scoring_type == ScoringType.GAUSSIAN:
            if not isinstance(self.parameters, GaussianParameters):
                raise ValueError(
                    f"Gaussian scoring requires GaussianParameters, " f"got {type(self.parameters)}"
                )
        elif self.scoring_type == ScoringType.MONOTONIC:
            if not isinstance(self.parameters, MonotonicParameters):
                raise ValueError(
                    f"Monotonic scoring requires MonotonicParameters, "
                    f"got {type(self.parameters)}"
                )
        elif self.scoring_type == ScoringType.THRESHOLD and not isinstance(
            self.parameters, ThresholdParameters
        ):
            raise ValueError(
                f"Threshold scoring requires ThresholdParameters, " f"got {type(self.parameters)}"
            )

        # Validate the actual parameters
        # The isinstance checks above ensure parameters has validate() method
        if hasattr(self.parameters, "validate"):
            self.parameters.validate()


@dataclass
class PercentileParameters:
    """
    Container for all dimension parameters with version tracking.

    This is the top-level container that holds parameters for all dimensions
    and manages versioning and metadata.

    Attributes:
        version: Overall parameter set version
        timestamp: When this parameter set was created
        validation_dataset_version: Version of validation dataset
        dimensions: Dict mapping dimension name to DimensionParameters
        metadata: Additional metadata (recalibration trigger, notes, etc.)
    """

    version: str
    timestamp: str
    validation_dataset_version: str
    dimensions: Dict[str, DimensionParameters] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dimension(self, dim_params: DimensionParameters) -> None:
        """Add or update dimension parameters."""
        dim_params.validate()
        self.dimensions[dim_params.dimension_name] = dim_params
        logger.info(f"Added parameters for dimension: {dim_params.dimension_name}")

    def get_dimension(self, dimension_name: str) -> Optional[DimensionParameters]:
        """Retrieve parameters for a specific dimension."""
        return self.dimensions.get(dimension_name)

    def validate(self) -> None:
        """Validate all dimension parameters."""
        for dim_name, dim_params in self.dimensions.items():
            try:
                dim_params.validate()
            except ValueError as e:
                raise ValueError(f"Validation failed for dimension '{dim_name}': {e}") from e

        logger.info(f"Validated {len(self.dimensions)} dimension parameter sets")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics about parameters."""
        scoring_type_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}

        for dim_params in self.dimensions.values():
            # Count scoring types
            scoring_type = dim_params.scoring_type.value
            scoring_type_counts[scoring_type] = scoring_type_counts.get(scoring_type, 0) + 1

            # Count parameter sources
            if isinstance(dim_params.parameters, GaussianParameters):
                for param_value in [dim_params.parameters.target, dim_params.parameters.width]:
                    source = param_value.source.value
                    source_counts[source] = source_counts.get(source, 0) + 1
            elif isinstance(dim_params.parameters, MonotonicParameters):
                for param_value in [
                    dim_params.parameters.threshold_low,
                    dim_params.parameters.threshold_high,
                ]:
                    source = param_value.source.value
                    source_counts[source] = source_counts.get(source, 0) + 1
            elif isinstance(dim_params.parameters, ThresholdParameters):
                for param_value in dim_params.parameters.thresholds:
                    source = param_value.source.value
                    source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "validation_dataset_version": self.validation_dataset_version,
            "total_dimensions": len(self.dimensions),
            "scoring_types": scoring_type_counts,
            "parameter_sources": source_counts,
            "metadata": self.metadata,
        }
