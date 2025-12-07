"""
Parameter derivation from distribution analysis.

Derives scoring parameters from empirical distribution percentiles for
percentile-anchored scoring system.

Created in Story 2.5 Task 4.
Enhanced with Shapiro-Wilk normality testing in Story 2.5.1.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from writescore.core.distribution_analyzer import DimensionStatistics, DistributionAnalysis
from writescore.core.normality import NormalityResult, NormalityTester

logger = logging.getLogger(__name__)


class ScoringMethod(Enum):
    """Scoring method type for dimension."""

    GAUSSIAN = "gaussian"  # Bell curve centered on human median
    MONOTONIC = "monotonic"  # Linear increase/decrease
    THRESHOLD = "threshold"  # Discrete category boundaries


@dataclass
class GaussianParameters:
    """
    Parameters for Gaussian (bell curve) scoring.

    Attributes:
        target: Center point (human p50 median)
        width: Spread/tolerance (stdev or IQR-based)
        method: Derivation method used ('stdev' or 'iqr')
    """

    target: float
    width: float
    method: str = "stdev"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target": round(self.target, 4),
            "width": round(self.width, 4),
            "method": self.method,
        }


@dataclass
class MonotonicParameters:
    """
    Parameters for monotonic (linear) scoring.

    Attributes:
        threshold_low: Lower boundary (human p25)
        threshold_high: Upper boundary (human p75)
        inverted: Whether higher values indicate AI-like behavior
    """

    threshold_low: float
    threshold_high: float
    inverted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "threshold_low": round(self.threshold_low, 4),
            "threshold_high": round(self.threshold_high, 4),
            "inverted": self.inverted,
        }


@dataclass
class ThresholdParameters:
    """
    Parameters for threshold (discrete category) scoring.

    Attributes:
        boundaries: Dictionary of category boundaries
            Example: {
                'excellent_good': 0.75,  # human p75
                'good_acceptable': 0.50,  # combined p50
                'acceptable_poor': 0.25  # ai p25
            }
    """

    boundaries: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"boundaries": {k: round(v, 4) for k, v in self.boundaries.items()}}


@dataclass
class DimensionParameters:
    """
    Complete parameter set for a dimension.

    Attributes:
        dimension_name: Dimension identifier
        scoring_method: Type of scoring (GAUSSIAN, MONOTONIC, THRESHOLD)
        parameters: Actual parameter values (GaussianParameters, MonotonicParameters, or ThresholdParameters)
        metadata: Additional metadata (distribution stats, derivation info)
    """

    dimension_name: str
    scoring_method: ScoringMethod
    parameters: Any  # GaussianParameters | MonotonicParameters | ThresholdParameters
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension_name": self.dimension_name,
            "scoring_method": self.scoring_method.value,
            "parameters": self.parameters.to_dict(),
            "metadata": self.metadata,
        }


class ParameterDeriver:
    """
    Derives scoring parameters from distribution analysis.

    Takes DistributionAnalysis results and computes appropriate parameters
    for each dimension based on empirical percentiles and distribution shape.

    With auto_select_method=True, uses Shapiro-Wilk normality testing to
    automatically select the most appropriate scoring method for each dimension.
    """

    def __init__(self, auto_select_method: bool = False, normality_alpha: float = 0.05):
        """
        Initialize parameter deriver.

        Args:
            auto_select_method: If True, use Shapiro-Wilk normality testing to
                              automatically select scoring method instead of
                              using hardcoded defaults. Default: False.
            normality_alpha: Significance level for normality test (default 0.05).
                           Only used when auto_select_method=True.
        """
        self.auto_select_method = auto_select_method
        self.normality_tester = (
            NormalityTester(alpha=normality_alpha) if auto_select_method else None
        )
        self.normality_results: Dict[str, NormalityResult] = {}  # Cache results

        # Map dimension names to their preferred scoring methods
        # Used when auto_select_method=False, or as fallback
        self.default_scoring_methods = {
            "burstiness": ScoringMethod.GAUSSIAN,
            "sentiment": ScoringMethod.GAUSSIAN,
            "lexical": ScoringMethod.MONOTONIC,
            "perplexity": ScoringMethod.MONOTONIC,
            "readability": ScoringMethod.THRESHOLD,
            "syntactic": ScoringMethod.GAUSSIAN,
            "structure": ScoringMethod.GAUSSIAN,
            "transition_marker": ScoringMethod.MONOTONIC,
            "voice": ScoringMethod.MONOTONIC,
            "formatting": ScoringMethod.THRESHOLD,
            "semantic_coherence": ScoringMethod.GAUSSIAN,
            "pragmatic_markers": ScoringMethod.GAUSSIAN,
            "ai_vocabulary": ScoringMethod.MONOTONIC,
            "advanced_lexical": ScoringMethod.MONOTONIC,
            "predictability": ScoringMethod.MONOTONIC,
            "figurative_language": ScoringMethod.GAUSSIAN,
        }

    def derive_all_parameters(
        self, analysis: DistributionAnalysis, dimension_names: Optional[List[str]] = None
    ) -> Dict[str, DimensionParameters]:
        """
        Derive parameters for all dimensions in analysis.

        Args:
            analysis: DistributionAnalysis with computed statistics
            dimension_names: Optional list of dimensions to derive. If None, derives all.

        Returns:
            Dict mapping dimension names to DimensionParameters
        """
        if dimension_names is None:
            dimension_names = list(analysis.dimensions.keys())

        logger.info(f"Deriving parameters for {len(dimension_names)} dimensions")

        derived_params = {}
        for dim_name in dimension_names:
            try:
                params = self.derive_dimension_parameters(analysis, dim_name)
                if params:
                    derived_params[dim_name] = params
                    logger.info(f"Derived {params.scoring_method.value} parameters for {dim_name}")
            except Exception as e:
                logger.error(f"Failed to derive parameters for {dim_name}: {e}")
                continue

        logger.info(f"Successfully derived parameters for {len(derived_params)} dimensions")
        return derived_params

    def derive_dimension_parameters(
        self,
        analysis: DistributionAnalysis,
        dimension_name: str,
        scoring_method: Optional[ScoringMethod] = None,
    ) -> Optional[DimensionParameters]:
        """
        Derive parameters for a single dimension.

        Args:
            analysis: DistributionAnalysis with computed statistics
            dimension_name: Name of dimension to derive parameters for
            scoring_method: Optional override for scoring method. If None, uses
                          auto-selection (if enabled) or default mapping.

        Returns:
            DimensionParameters or None if derivation fails
        """
        # Get statistics for this dimension
        human_stats = analysis.get_dimension_stats(dimension_name, "human")
        ai_stats = analysis.get_dimension_stats(dimension_name, "ai")
        combined_stats = analysis.get_dimension_stats(dimension_name, "combined")

        if not human_stats:
            logger.warning(f"No human statistics for {dimension_name}, cannot derive parameters")
            return None

        # Initialize normality metadata
        normality_metadata: Dict[str, Any] = {"method_auto_selected": False}

        # Determine scoring method
        if scoring_method is None:
            if self.auto_select_method and human_stats.values:
                # Use Shapiro-Wilk normality testing to auto-select method
                # Normality tester is always initialized when auto_select_method is True
                assert self.normality_tester is not None
                normality_result = self.normality_tester.test_normality(
                    human_stats.values, dimension_name
                )

                # Cache the result
                self.normality_results[dimension_name] = normality_result

                # Map recommendation string to ScoringMethod enum
                method_map = {
                    "gaussian": ScoringMethod.GAUSSIAN,
                    "monotonic": ScoringMethod.MONOTONIC,
                    "threshold": ScoringMethod.THRESHOLD,
                }
                scoring_method = method_map.get(
                    normality_result.recommendation, ScoringMethod.GAUSSIAN
                )

                # Store normality info in metadata
                normality_metadata = {
                    "method_auto_selected": True,
                    "normality_p_value": normality_result.p_value,
                    "normality_is_normal": normality_result.is_normal,
                    "normality_skewness": normality_result.skewness,
                    "normality_kurtosis": normality_result.kurtosis,
                    "normality_confidence": normality_result.confidence,
                    "normality_rationale": normality_result.rationale,
                }

                logger.info(
                    f"{dimension_name}: Auto-selected {scoring_method.value} "
                    f"(p={normality_result.p_value:.4f}, confidence={normality_result.confidence})"
                )
            else:
                # Fall back to hardcoded defaults
                scoring_method = self.default_scoring_methods.get(
                    dimension_name,
                    ScoringMethod.GAUSSIAN,  # Default fallback
                )

        # Derive parameters based on method
        params: Union[GaussianParameters, MonotonicParameters, ThresholdParameters]
        if scoring_method == ScoringMethod.GAUSSIAN:
            params = self._derive_gaussian_parameters(human_stats)
        elif scoring_method == ScoringMethod.MONOTONIC:
            params = self._derive_monotonic_parameters(human_stats, ai_stats)
        elif scoring_method == ScoringMethod.THRESHOLD:
            params = self._derive_threshold_parameters(human_stats, ai_stats, combined_stats)
        else:
            logger.error(f"Unknown scoring method: {scoring_method}")
            return None

        # Build metadata
        metadata = {
            "human_p50": human_stats.median,
            "human_p25": human_stats.percentiles["p25"],
            "human_p75": human_stats.percentiles["p75"],
            "human_stdev": human_stats.stdev,
            "human_count": human_stats.count,
        }

        if ai_stats:
            metadata.update({"ai_p50": ai_stats.median, "ai_count": ai_stats.count})

        # Add normality testing metadata
        metadata.update(normality_metadata)

        return DimensionParameters(
            dimension_name=dimension_name,
            scoring_method=scoring_method,
            parameters=params,
            metadata=metadata,
        )

    def get_normality_results(self) -> Dict[str, NormalityResult]:
        """
        Get cached normality test results.

        Returns:
            Dictionary mapping dimension names to NormalityResult objects.
            Only populated when auto_select_method=True and derive_* has been called.
        """
        return self.normality_results

    def _derive_gaussian_parameters(self, human_stats: DimensionStatistics) -> GaussianParameters:
        """
        Derive Gaussian parameters from human distribution.

        Uses human median as target and stdev (or IQR-based) as width.

        Args:
            human_stats: Human distribution statistics

        Returns:
            GaussianParameters
        """
        target = human_stats.median

        # Use standard deviation if available
        if human_stats.stdev > 0:
            width = human_stats.stdev
            method = "stdev"
        else:
            # Fallback to IQR-based width
            # IQR / 1.35 approximates stdev for normal distribution
            iqr = human_stats.iqr
            width = iqr / 1.35 if iqr > 0 else 1.0
            method = "iqr"

        # Sanity check: width must be positive
        if width <= 0:
            logger.warning(
                f"Invalid width {width} for {human_stats.dimension_name}, using fallback"
            )
            width = abs(target * 0.15) if target != 0 else 1.0

        return GaussianParameters(target=target, width=width, method=method)

    def _derive_monotonic_parameters(
        self, human_stats: DimensionStatistics, ai_stats: Optional[DimensionStatistics] = None
    ) -> MonotonicParameters:
        """
        Derive monotonic parameters from human distribution.

        Uses human p25 and p75 as threshold boundaries.

        Args:
            human_stats: Human distribution statistics
            ai_stats: Optional AI distribution statistics

        Returns:
            MonotonicParameters
        """
        threshold_low = human_stats.percentiles["p25"]
        threshold_high = human_stats.percentiles["p75"]

        # Determine if inverted (higher = more AI-like)
        # If AI median > human median, then higher values indicate AI behavior
        inverted = False
        if ai_stats and ai_stats.median > human_stats.median:
            inverted = True

        # Sanity check: ensure monotonic ordering
        if threshold_low >= threshold_high:
            logger.warning(
                f"Invalid monotonic thresholds for {human_stats.dimension_name}: "
                f"low={threshold_low} >= high={threshold_high}"
            )
            # Use median ± IQR/4 as fallback, or ±15% of median if IQR is 0
            if human_stats.iqr > 0:
                threshold_low = human_stats.median - (human_stats.iqr / 4)
                threshold_high = human_stats.median + (human_stats.iqr / 4)
            else:
                # IQR is 0, use percentage of median
                spread = abs(human_stats.median * 0.15) if human_stats.median != 0 else 5.0
                threshold_low = human_stats.median - spread
                threshold_high = human_stats.median + spread

        return MonotonicParameters(
            threshold_low=threshold_low, threshold_high=threshold_high, inverted=inverted
        )

    def _derive_threshold_parameters(
        self,
        human_stats: DimensionStatistics,
        ai_stats: Optional[DimensionStatistics],
        combined_stats: Optional[DimensionStatistics],
    ) -> ThresholdParameters:
        """
        Derive threshold parameters for discrete categories.

        Creates boundaries between excellent/good/acceptable/poor categories
        using percentiles from human, AI, and combined distributions.

        Args:
            human_stats: Human distribution statistics
            ai_stats: AI distribution statistics
            combined_stats: Combined distribution statistics

        Returns:
            ThresholdParameters
        """
        boundaries = {}

        # Excellent/Good boundary: human p75
        boundaries["excellent_good"] = human_stats.percentiles["p75"]

        # Good/Acceptable boundary: combined p50 or human p50
        if combined_stats:
            boundaries["good_acceptable"] = combined_stats.percentiles["p50"]
        else:
            boundaries["good_acceptable"] = human_stats.percentiles["p50"]

        # Acceptable/Poor boundary: AI p25 or human p25
        if ai_stats:
            boundaries["acceptable_poor"] = ai_stats.percentiles["p25"]
        else:
            boundaries["acceptable_poor"] = human_stats.percentiles["p25"]

        # Sanity check: ensure proper ordering
        vals = [
            boundaries["excellent_good"],
            boundaries["good_acceptable"],
            boundaries["acceptable_poor"],
        ]

        if not all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
            logger.warning(
                f"Threshold boundaries not properly ordered for {human_stats.dimension_name}: {vals}"
            )
            # Use quartiles as fallback
            boundaries["excellent_good"] = human_stats.percentiles["p75"]
            boundaries["good_acceptable"] = human_stats.percentiles["p50"]
            boundaries["acceptable_poor"] = human_stats.percentiles["p25"]

        return ThresholdParameters(boundaries=boundaries)

    def save_parameters(
        self,
        parameters: Dict[str, DimensionParameters],
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save derived parameters to JSON file.

        Args:
            parameters: Dictionary of DimensionParameters
            output_path: Path to save JSON file
            metadata: Optional metadata to include
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "2.5",
            "metadata": metadata or {},
            "parameters": {name: params.to_dict() for name, params in parameters.items()},
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(parameters)} parameter sets to {output_path}")

    @staticmethod
    def load_parameters(input_path: Path) -> Dict[str, DimensionParameters]:
        """
        Load derived parameters from JSON file.

        Args:
            input_path: Path to JSON file

        Returns:
            Dictionary of DimensionParameters
        """
        with open(input_path) as f:
            data = json.load(f)

        parameters = {}
        for name, param_data in data["parameters"].items():
            scoring_method = ScoringMethod(param_data["scoring_method"])

            # Reconstruct parameter objects
            params: Union[GaussianParameters, MonotonicParameters, ThresholdParameters]
            if scoring_method == ScoringMethod.GAUSSIAN:
                params = GaussianParameters(**param_data["parameters"])
            elif scoring_method == ScoringMethod.MONOTONIC:
                params = MonotonicParameters(**param_data["parameters"])
            elif scoring_method == ScoringMethod.THRESHOLD:
                params = ThresholdParameters(**param_data["parameters"])
            else:
                logger.warning(f"Unknown scoring method for {name}: {scoring_method}")
                continue

            parameters[name] = DimensionParameters(
                dimension_name=name,
                scoring_method=scoring_method,
                parameters=params,
                metadata=param_data.get("metadata", {}),
            )

        logger.info(f"Loaded {len(parameters)} parameter sets from {input_path}")
        return parameters
