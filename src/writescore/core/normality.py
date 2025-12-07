"""
Normality testing for scoring method selection.

Implements Shapiro-Wilk normality testing to automatically determine
the most appropriate scoring method (Gaussian, Monotonic, or Threshold)
for each dimension based on the empirical distribution shape.

Created in Story 2.5.1 (Shapiro-Wilk Enhancement).
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class NormalityResult:
    """
    Result of normality test for a dimension.

    Attributes:
        dimension_name: Name of the dimension tested
        is_normal: Whether the distribution passes normality test
        p_value: P-value from Shapiro-Wilk test (>0.05 suggests normality)
        test_statistic: Shapiro-Wilk W statistic (closer to 1 = more normal)
        sample_size: Number of samples tested
        skewness: Distribution skewness (0 = symmetric)
        kurtosis: Excess kurtosis (0 = normal, >0 = heavy tails)
        recommendation: Recommended scoring method ('gaussian', 'monotonic', 'threshold')
        confidence: Confidence level in recommendation ('high', 'medium', 'low')
        rationale: Human-readable explanation of the recommendation
    """

    dimension_name: str
    is_normal: bool
    p_value: float
    test_statistic: float
    sample_size: int
    skewness: float
    kurtosis: float
    recommendation: str
    confidence: str = "medium"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension_name": self.dimension_name,
            "is_normal": self.is_normal,
            "p_value": round(self.p_value, 6),
            "test_statistic": round(self.test_statistic, 6),
            "sample_size": self.sample_size,
            "skewness": round(self.skewness, 4),
            "kurtosis": round(self.kurtosis, 4),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


class NormalityTester:
    """
    Tests distribution normality to guide scoring method selection.

    Uses the Shapiro-Wilk test along with skewness and kurtosis analysis
    to recommend the most appropriate scoring method for each dimension.

    Scoring Method Selection Logic:
    - Gaussian: For normally distributed data with symmetric shape
    - Monotonic: For skewed data or "more is better/worse" relationships
    - Threshold: For data with heavy tails or discrete category boundaries
    """

    # Shapiro-Wilk test limits
    MIN_SAMPLES = 3  # Statistical minimum
    RECOMMENDED_SAMPLES = 50  # For reliable results
    MAX_SAMPLES = 5000  # scipy.stats.shapiro limit

    # Shape thresholds
    SKEWNESS_SYMMETRIC = 0.5  # |skew| < 0.5 = roughly symmetric
    SKEWNESS_MODERATE = 1.0  # |skew| < 1.0 = moderately skewed
    SKEWNESS_HIGH = 2.0  # |skew| > 2.0 = highly skewed
    KURTOSIS_NORMAL = 1.0  # |kurtosis| < 1.0 = normal-like tails
    KURTOSIS_HEAVY = 3.0  # |kurtosis| > 3.0 = heavy tails

    def __init__(
        self,
        alpha: float = 0.05,
        min_samples: Optional[int] = None,
        max_samples: Optional[int] = None,
    ):
        """
        Initialize normality tester.

        Args:
            alpha: Significance level for normality test (default 0.05).
                   Lower values are more conservative (harder to reject normality).
            min_samples: Minimum samples required for reliable test.
                        If fewer samples, returns conservative recommendation.
            max_samples: Maximum samples for Shapiro-Wilk (5000 limit).
                        Larger samples are randomly subsampled.
        """
        self.alpha = alpha
        self.min_samples = min_samples or self.RECOMMENDED_SAMPLES
        self.max_samples = max_samples or self.MAX_SAMPLES

    def test_normality(self, values: List[float], dimension_name: str) -> NormalityResult:
        """
        Test if values follow a normal distribution.

        Args:
            values: Raw metric values from distribution analysis
            dimension_name: Name of dimension being tested

        Returns:
            NormalityResult with test outcome and scoring method recommendation
        """
        arr = np.array(values, dtype=float)

        # Remove NaN/Inf values
        arr = arr[np.isfinite(arr)]
        n = len(arr)

        # Handle insufficient data
        if n < self.MIN_SAMPLES:
            logger.warning(
                f"{dimension_name}: Only {n} samples (need {self.MIN_SAMPLES}). "
                "Cannot perform normality test, using conservative default."
            )
            return NormalityResult(
                dimension_name=dimension_name,
                is_normal=True,  # Assume normal, use robust IQR width
                p_value=1.0,
                test_statistic=1.0,
                sample_size=n,
                skewness=0.0,
                kurtosis=0.0,
                recommendation="gaussian",
                confidence="low",
                rationale=f"Insufficient data ({n} samples). Defaulting to Gaussian with IQR-based width.",
            )

        # Warn if below recommended sample size
        if n < self.min_samples:
            logger.info(
                f"{dimension_name}: {n} samples (recommended: {self.min_samples}). "
                "Results may be less reliable."
            )

        # Subsample if too large for Shapiro-Wilk
        original_n = n
        if n > self.max_samples:
            logger.info(f"{dimension_name}: Subsampling {n} -> {self.max_samples} for Shapiro-Wilk")
            np.random.seed(42)  # Reproducibility
            arr = np.random.choice(arr, size=self.max_samples, replace=False)
            n = self.max_samples

        # Run Shapiro-Wilk test
        try:
            stat, p_value = stats.shapiro(arr)
        except Exception as e:
            logger.error(f"{dimension_name}: Shapiro-Wilk test failed: {e}")
            return NormalityResult(
                dimension_name=dimension_name,
                is_normal=True,
                p_value=1.0,
                test_statistic=0.0,
                sample_size=original_n,
                skewness=0.0,
                kurtosis=0.0,
                recommendation="gaussian",
                confidence="low",
                rationale=f"Shapiro-Wilk test failed ({e}). Defaulting to Gaussian.",
            )

        # Calculate shape metrics
        skewness = float(stats.skew(arr))
        kurtosis = float(stats.kurtosis(arr))  # Excess kurtosis (normal = 0)

        # Determine if normal based on p-value
        # Explicitly convert to Python bool to avoid numpy.bool_ identity issues
        is_normal = bool(p_value > self.alpha)

        # Generate recommendation based on test results and shape
        recommendation, confidence, rationale = self._get_recommendation(
            is_normal, p_value, skewness, kurtosis, dimension_name
        )

        logger.info(
            f"{dimension_name}: Shapiro-Wilk W={stat:.4f}, p={p_value:.4f}, "
            f"skew={skewness:.2f}, kurtosis={kurtosis:.2f} -> {recommendation} ({confidence})"
        )

        return NormalityResult(
            dimension_name=dimension_name,
            is_normal=is_normal,
            p_value=float(p_value),
            test_statistic=float(stat),
            sample_size=original_n,
            skewness=skewness,
            kurtosis=kurtosis,
            recommendation=recommendation,
            confidence=confidence,
            rationale=rationale,
        )

    def _get_recommendation(
        self, is_normal: bool, p_value: float, skewness: float, kurtosis: float, dimension_name: str
    ) -> Tuple[str, str, str]:
        """
        Recommend scoring method based on distribution shape.

        Returns:
            Tuple of (recommendation, confidence, rationale)
        """
        abs_skew = abs(skewness)
        abs_kurt = abs(kurtosis)

        # Case 1: Strong normality (high p-value, symmetric, normal tails)
        if is_normal and abs_skew < self.SKEWNESS_SYMMETRIC and abs_kurt < self.KURTOSIS_NORMAL:
            return (
                "gaussian",
                "high",
                f"Strong normality: p={p_value:.3f}, symmetric (skew={skewness:.2f}), "
                f"normal tails (kurtosis={kurtosis:.2f})",
            )

        # Case 2: Acceptable normality (passes test, moderate shape)
        if is_normal and abs_skew < self.SKEWNESS_MODERATE:
            return (
                "gaussian",
                "medium",
                f"Acceptable normality: p={p_value:.3f}, moderate skew ({skewness:.2f}). "
                "Consider IQR-based width for robustness.",
            )

        # Case 3: Heavy tails -> Threshold (robust to outliers)
        if abs_kurt > self.KURTOSIS_HEAVY:
            return (
                "threshold",
                "high",
                f"Heavy tails (kurtosis={kurtosis:.2f}). Threshold scoring is more robust "
                "to extreme values.",
            )

        # Case 4: Strong skewness -> Monotonic
        if abs_skew > self.SKEWNESS_HIGH:
            return (
                "monotonic",
                "high",
                f"Highly skewed distribution (skew={skewness:.2f}). Monotonic scoring "
                "handles asymmetry better.",
            )

        # Case 5: Moderate skewness -> Monotonic
        if abs_skew > self.SKEWNESS_MODERATE:
            return (
                "monotonic",
                "medium",
                f"Moderately skewed (skew={skewness:.2f}). Monotonic scoring recommended.",
            )

        # Case 6: Non-normal but not strongly skewed -> Monotonic (safer default)
        if not is_normal:
            return (
                "monotonic",
                "medium",
                f"Failed normality test (p={p_value:.3f}). Using monotonic scoring "
                "for non-normal distribution.",
            )

        # Case 7: Borderline normal with elevated kurtosis
        if abs_kurt > self.KURTOSIS_NORMAL:
            return (
                "gaussian",
                "low",
                f"Borderline normal: p={p_value:.3f}, elevated kurtosis ({kurtosis:.2f}). "
                "Gaussian may work but consider IQR-based width.",
            )

        # Default fallback
        return (
            "gaussian",
            "medium",
            f"Default recommendation: p={p_value:.3f}, skew={skewness:.2f}, "
            f"kurtosis={kurtosis:.2f}",
        )

    def test_all_dimensions(
        self, dimension_values: Dict[str, List[float]]
    ) -> Dict[str, NormalityResult]:
        """
        Test normality for multiple dimensions.

        Args:
            dimension_values: Dictionary mapping dimension names to value lists

        Returns:
            Dictionary mapping dimension names to NormalityResults
        """
        results = {}
        for dim_name, values in dimension_values.items():
            results[dim_name] = self.test_normality(values, dim_name)
        return results


def format_normality_report(results: Dict[str, NormalityResult]) -> str:
    """
    Generate human-readable normality test report.

    Args:
        results: Dictionary of NormalityResult objects

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("NORMALITY TEST REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Summary counts
    gaussian_count = sum(1 for r in results.values() if r.recommendation == "gaussian")
    monotonic_count = sum(1 for r in results.values() if r.recommendation == "monotonic")
    threshold_count = sum(1 for r in results.values() if r.recommendation == "threshold")

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total dimensions tested: {len(results)}")
    lines.append(f"Recommended Gaussian: {gaussian_count}")
    lines.append(f"Recommended Monotonic: {monotonic_count}")
    lines.append(f"Recommended Threshold: {threshold_count}")
    lines.append("")

    # Per-dimension results
    lines.append("PER-DIMENSION RESULTS")
    lines.append("-" * 40)

    for dim_name in sorted(results.keys()):
        r = results[dim_name]
        normal_str = "NORMAL" if r.is_normal else "NOT NORMAL"
        lines.append(f"\n{dim_name.upper()}")
        lines.append(f"  Shapiro-Wilk: W={r.test_statistic:.4f}, p={r.p_value:.4f} [{normal_str}]")
        lines.append(f"  Shape: skewness={r.skewness:.2f}, kurtosis={r.kurtosis:.2f}")
        lines.append(f"  Samples: {r.sample_size}")
        lines.append(
            f"  -> Recommendation: {r.recommendation.upper()} (confidence: {r.confidence})"
        )
        lines.append(f"  -> Rationale: {r.rationale}")

    lines.append("\n" + "=" * 80)

    return "\n".join(lines)
