"""
Weight validation mediator for AI Pattern Analyzer dimensions.

This module implements the Mediator Pattern for validating dimension weights
and providing rebalancing suggestions. Ensures all dimension weights sum to
100.0% before analysis execution.

Version 2.0 Enhancements:
- Configurable tolerance via __init__
- Structured error collection (Pydantic-style)
- Complete edge case handling in rebalancing
- __repr__ and __str__ methods for debugging
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.exceptions import AIPatternAnalyzerError


@dataclass
class ValidationErrorDetail:
    """
    Structured error detail for weight validation failures.

    Follows Pydantic ValidationError pattern for structured error reporting.

    Attributes:
        dimension_name: Name of dimension with error (or '<all>', '<registry>')
        error_type: Type of validation error
        current_value: Actual value that failed validation
        expected_value: Expected value or constraint
        message: Human-readable error message
    """

    dimension_name: str
    error_type: str  # 'negative_weight', 'excessive_weight', 'invalid_total', 'zero_weight', 'no_dimensions'
    current_value: Any
    expected_value: Any
    message: str

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"ValidationErrorDetail(dimension_name={self.dimension_name!r}, "
            f"error_type={self.error_type!r}, current_value={self.current_value}, "
            f"expected_value={self.expected_value})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension_name": self.dimension_name,
            "error_type": self.error_type,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "message": self.message,
        }


class WeightValidationError(AIPatternAnalyzerError):
    """
    Raised when dimension weight validation fails.

    Includes structured error collection following Pydantic ValidationError pattern.
    Integrates with AIPatternAnalyzerError base exception from core/exceptions.py.

    Attributes:
        message: Human-readable error summary
        errors: List of ValidationErrorDetail objects with structured error information
        total_weight: Actual total weight that failed validation
        expected_weight: Expected total weight (100.0)
        tolerance: Tolerance value used for validation
    """

    def __init__(
        self,
        message: str,
        errors: Optional[List[ValidationErrorDetail]] = None,
        total_weight: Optional[float] = None,
        expected_weight: float = 100.0,
        tolerance: float = 0.1,
    ):
        """
        Initialize WeightValidationError.

        Args:
            message: Human-readable error summary
            errors: List of ValidationErrorDetail objects
            total_weight: Actual total weight that failed validation
            expected_weight: Expected total weight (default 100.0)
            tolerance: Tolerance value used for validation (default 0.1)
        """
        super().__init__(message)
        self.errors = errors or []
        self.total_weight = total_weight
        self.expected_weight = expected_weight
        self.tolerance = tolerance

    def __str__(self) -> str:
        """Human-readable error message with all error details."""
        lines = [str(self.args[0])]

        if self.total_weight is not None:
            lines.append(f"\nTotal weight: {self.total_weight:.2f}%")
            lines.append(f"Expected: {self.expected_weight:.2f}% ±{self.tolerance}%")
            lines.append(f"Difference: {self.total_weight - self.expected_weight:+.2f}%")

        if self.errors:
            lines.append(f"\nValidation errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"  {i}. {error.message}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"WeightValidationError(message={self.args[0]!r}, "
            f"errors={len(self.errors)} errors, "
            f"total_weight={self.total_weight})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "message": str(self.args[0]),
            "total_weight": self.total_weight,
            "expected_weight": self.expected_weight,
            "tolerance": self.tolerance,
            "error_count": len(self.errors),
            "errors": [error.to_dict() for error in self.errors],
        }


class WeightMediator:
    """
    Mediator for validating dimension weight configuration.

    Ensures all dimension weights are valid before analysis execution.
    Provides detailed validation reports and rebalancing suggestions.

    Version 2.0 Enhancements:
    - Configurable tolerance via __init__
    - Structured error collection (Pydantic-style)
    - Complete edge case handling in rebalancing
    - __repr__ and __str__ methods for debugging

    Attributes:
        registry: DimensionRegistry instance (uses class-level registry if None)
        tolerance: Tolerance for weight sum validation (default 0.1%)
        validation_errors: List of ValidationErrorDetail objects
        validation_warnings: List of warning messages
    """

    def __init__(self, registry: Optional[DimensionRegistry] = None, tolerance: float = 0.1):
        """
        Initialize WeightMediator.

        Args:
            registry: DimensionRegistry instance (uses class-level registry if None)
            tolerance: Tolerance for weight sum validation (default 0.1%)
                      Example: tolerance=0.1 allows total weight 99.9-100.1

        Raises:
            ValueError: If tolerance is negative or > 10.0
        """
        if tolerance < 0 or tolerance > 10.0:
            raise ValueError(f"Tolerance must be between 0 and 10.0, got {tolerance}")

        self.registry = registry  # If None, will use DimensionRegistry class methods
        self.tolerance = tolerance
        self.validation_errors: List[ValidationErrorDetail] = []
        self.validation_warnings: List[str] = []
        self._validation_cache: Optional[bool] = None  # Cache validation result for performance

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        dimension_count = self._get_dimension_count()
        total_weight = self.get_total_weight()
        return (
            f"WeightMediator(dimensions={dimension_count}, "
            f"total_weight={total_weight:.2f}, "
            f"tolerance={self.tolerance}, "
            f"is_valid={self.is_valid})"
        )

    def __str__(self) -> str:
        """Human-readable summary."""
        dimension_count = self._get_dimension_count()
        total_weight = self.get_total_weight()
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"WeightMediator: {dimension_count} dimensions, "
            f"total weight {total_weight:.2f}%, {status}"
        )

    @property
    def is_valid(self) -> bool:
        """
        Check if current weight configuration is valid.

        Uses cached validation result for performance. To force re-validation,
        call validate_weights(force=True) directly.

        Returns:
            True if valid, False otherwise
        """
        return self.validate_weights()

    def _get_dimension_count(self) -> int:
        """Get count of registered dimensions."""
        if self.registry is not None:
            return len(self.registry._dimensions)
        else:
            return DimensionRegistry.get_count()

    def _get_all_dimensions(self) -> List:
        """Get all registered dimensions."""
        if self.registry is not None:
            return list(self.registry._dimensions.values())
        else:
            return DimensionRegistry.get_all()

    def _format_percentage(self, value: float, show_sign: bool = False) -> str:
        """
        Format a value as percentage for error messages.

        Args:
            value: Numeric value to format
            show_sign: If True, always show + or - sign

        Returns:
            Formatted percentage string (e.g., "105.50%" or "+5.50%")
        """
        if show_sign:
            return f"{value:+.2f}%"
        else:
            return f"{value:.2f}%"

    def _validate_single_dimension(self, dimension) -> None:
        """
        Validate a single dimension's weight.

        Args:
            dimension: DimensionStrategy instance to validate

        Side Effects:
            Appends to self.validation_errors and self.validation_warnings
        """
        name = dimension.dimension_name
        weight = dimension.weight

        # Rule 2: No negative weights
        if weight < 0:
            self.validation_errors.append(
                ValidationErrorDetail(
                    dimension_name=name,
                    error_type="negative_weight",
                    current_value=weight,
                    expected_value=">= 0",
                    message=f"Dimension '{name}' has negative weight: {weight:.2f}",
                )
            )

        # Rule 3: No excessive weights
        if weight > 100:
            self.validation_errors.append(
                ValidationErrorDetail(
                    dimension_name=name,
                    error_type="excessive_weight",
                    current_value=weight,
                    expected_value="<= 100",
                    message=f"Dimension '{name}' has weight > 100: {weight:.2f}",
                )
            )

        # Zero weight dimensions are treated as errors (not just warnings)
        # Design Rationale: Zero-weight dimensions indicate a configuration issue
        # where a dimension is registered but will contribute nothing to the analysis.
        # This is likely unintentional and should be explicitly fixed by either:
        # 1. Removing the dimension from the registry, or
        # 2. Assigning it a meaningful weight
        # Treating as an error prevents silent failures where dimensions are
        # unexpectedly ignored during analysis.
        if weight == 0:
            self.validation_errors.append(
                ValidationErrorDetail(
                    dimension_name=name,
                    error_type="zero_weight",
                    current_value=0,
                    expected_value="> 0",
                    message=f"Dimension '{name}' has zero weight (will be ignored in analysis)",
                )
            )
            self.validation_warnings.append(
                f"Dimension '{name}' has zero weight and will be ignored"
            )

    def get_total_weight(self) -> float:
        """
        Calculate total weight of all registered dimensions.

        Returns:
            Sum of all dimension weights
        """
        dimensions = self._get_all_dimensions()
        return float(sum(d.weight for d in dimensions))

    def validate_weights(self, force: bool = False) -> bool:
        """
        Validate all dimension weights.

        Validation Rules:
        1. At least one dimension registered
        2. No negative weights
        3. No individual weights > 100
        4. Total weight sums to 100.0 (±tolerance)

        Args:
            force: If True, force re-validation even if cached result exists.
                   If False (default), returns cached result if available.

        Returns:
            True if valid, False otherwise

        Side Effects:
            Populates self.validation_errors and self.validation_warnings
            Caches validation result for subsequent calls
        """
        # Return cached result if available and not forced
        if not force and self._validation_cache is not None:
            return self._validation_cache

        # Clear previous validation results
        self.validation_errors.clear()
        self.validation_warnings.clear()

        dimensions = self._get_all_dimensions()

        # Rule 1: At least one dimension
        if not dimensions:
            self.validation_errors.append(
                ValidationErrorDetail(
                    dimension_name="<registry>",
                    error_type="no_dimensions",
                    current_value=0,
                    expected_value=">= 1",
                    message="No dimensions registered. At least one dimension required.",
                )
            )
            return False

        # Validate each dimension individually
        for dimension in dimensions:
            self._validate_single_dimension(dimension)

        # Rule 4: Total weight validation
        total_weight = sum(d.weight for d in dimensions)
        expected_weight = 100.0
        difference = abs(total_weight - expected_weight)

        if difference > self.tolerance:
            self.validation_errors.append(
                ValidationErrorDetail(
                    dimension_name="<all>",
                    error_type="invalid_total",
                    current_value=total_weight,
                    expected_value=expected_weight,
                    message=(
                        f"Total weight is {self._format_percentage(total_weight)}, "
                        f"expected {self._format_percentage(expected_weight)} "
                        f"(difference: {self._format_percentage(total_weight - expected_weight, show_sign=True)})"
                    ),
                )
            )

        # Cache result for performance
        result = len(self.validation_errors) == 0
        self._validation_cache = result
        return result

    def _get_weights_by_tier(self) -> Dict[str, Dict[str, Any]]:
        """
        Get weight breakdown by tier.

        Returns:
            Dict mapping tier name to tier summary:
            {
                'ADVANCED': {
                    'total_weight': float,
                    'dimension_count': int,
                    'dimensions': [{'name': str, 'weight': float}, ...]
                },
                ...
            }
        """
        dimensions = self._get_all_dimensions()

        tier_data: Dict[str, Dict[str, Any]] = {
            "ADVANCED": {"total_weight": 0.0, "dimension_count": 0, "dimensions": []},
            "CORE": {"total_weight": 0.0, "dimension_count": 0, "dimensions": []},
            "SUPPORTING": {"total_weight": 0.0, "dimension_count": 0, "dimensions": []},
            "STRUCTURAL": {"total_weight": 0.0, "dimension_count": 0, "dimensions": []},
        }

        for dimension in dimensions:
            tier = dimension.tier
            if tier in tier_data:
                tier_data[tier]["total_weight"] += dimension.weight
                tier_data[tier]["dimension_count"] += 1
                tier_data[tier]["dimensions"].append(
                    {"name": dimension.dimension_name, "weight": dimension.weight}
                )

        return tier_data

    def _adjust_rounding(self, suggestions: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust rounding to ensure suggested weights sum exactly to 100.0.

        Args:
            suggestions: Dict of dimension name → suggested weight

        Returns:
            Adjusted suggestions that sum to exactly 100.0
        """
        if not suggestions:
            return suggestions

        total = sum(suggestions.values())
        difference = 100.0 - total

        # If already exact, return as-is
        if abs(difference) < 0.001:
            return suggestions

        # Adjust the largest weight to compensate for rounding
        max_dimension = max(suggestions.items(), key=lambda x: x[1])
        suggestions[max_dimension[0]] = round(max_dimension[1] + difference, 2)

        return suggestions

    def suggest_rebalancing(self) -> Dict[str, float]:
        """
        Suggest weight rebalancing to achieve valid 100.0% total.

        Algorithm:
        1. If all weights are zero: equal distribution (100.0 / count)
        2. If total weight is zero but some non-zero: equal distribution
        3. If negative weights exist: skip negatives, rebalance positives
        4. If single dimension: set to 100.0
        5. Otherwise: proportional scaling (weight * 100.0 / total)

        Edge Cases Handled (NEW in v2.0):
        - All zero weights
        - Negative weights
        - Single dimension
        - Mixed positive/negative/zero
        - Rounding to ensure exact 100.0 sum

        Returns:
            Dict mapping dimension name to suggested weight
        """
        dimensions = self._get_all_dimensions()

        if not dimensions:
            return {}

        # Edge case: Single dimension
        if len(dimensions) == 1:
            return {dimensions[0].dimension_name: 100.0}

        # Separate dimensions by weight type
        positive_dims = [d for d in dimensions if d.weight > 0]
        zero_dims = [d for d in dimensions if d.weight == 0]
        negative_dims = [d for d in dimensions if d.weight < 0]

        # Calculate total of positive weights
        total_positive = sum(d.weight for d in positive_dims)

        # Edge case: All weights are zero or no positive weights
        if total_positive == 0:
            # Equal distribution across all dimensions
            equal_weight = 100.0 / len(dimensions)
            suggestions = {d.dimension_name: round(equal_weight, 2) for d in dimensions}
            # Adjust rounding to ensure exact 100.0
            suggestions = self._adjust_rounding(suggestions)
            return suggestions

        # Edge case: Has negative weights - skip them, rebalance positives only
        if negative_dims:
            # Distribute 100.0 across positive dimensions only
            suggestions = {}
            for d in positive_dims:
                suggested_weight = (d.weight / total_positive) * 100.0
                suggestions[d.dimension_name] = round(suggested_weight, 2)

            # Set negative and zero dimensions to 0.0
            for d in negative_dims + zero_dims:
                suggestions[d.dimension_name] = 0.0

            # Adjust rounding to ensure exact 100.0
            suggestions = self._adjust_rounding(suggestions)
            return suggestions

        # Normal case: Proportional scaling
        suggestions = {}
        for d in dimensions:
            if d.weight > 0:
                suggested_weight = (d.weight / total_positive) * 100.0
                suggestions[d.dimension_name] = round(suggested_weight, 2)
            else:
                suggestions[d.dimension_name] = 0.0

        # Adjust rounding to ensure exact 100.0
        suggestions = self._adjust_rounding(suggestions)
        return suggestions

    def get_validation_report(self, format: str = "dict") -> Union[Dict[str, Any], str]:
        """
        Generate comprehensive validation report.

        Args:
            format: Output format - 'dict' (default) or 'json'

        Returns:
            Comprehensive validation report as dict (if format='dict')
            or JSON string (if format='json')
        """
        dimensions = self._get_all_dimensions()
        total_weight = self.get_total_weight()
        expected_weight = 100.0
        difference = total_weight - expected_weight
        # Force re-validation to ensure report reflects current state
        is_valid = self.validate_weights(force=True)

        report = {
            "is_valid": is_valid,
            "total_weight": total_weight,
            "expected_weight": expected_weight,
            "difference": difference,
            "tolerance": self.tolerance,
            "dimension_count": len(dimensions),
            "dimension_weights": {d.dimension_name: d.weight for d in dimensions},
            "dimensions_by_tier": self._get_weights_by_tier(),
            "errors": [error.to_dict() for error in self.validation_errors],
            "warnings": self.validation_warnings.copy(),
        }

        # Add rebalancing suggestions if invalid
        if not is_valid:
            report["suggested_rebalancing"] = self.suggest_rebalancing()

        if format == "json":
            import json

            return json.dumps(report, indent=2)

        return report

    def require_valid(self) -> None:
        """
        Require weights to be valid, raise exception if not.

        This is the primary method to enforce weight validation before
        analysis execution (used by DynamicAnalysisEngine).

        Raises:
            WeightValidationError: If validation fails, includes all error details

        Example:
            mediator = WeightMediator()
            try:
                mediator.require_valid()  # Will raise if invalid
                # Safe to proceed with analysis
            except WeightValidationError as e:
                print(f"Weight validation failed: {e}")
                print(f"Errors: {len(e.errors)}")
                for error in e.errors:
                    print(f"  - {error.message}")
        """
        # Force re-validation for critical validation gate
        is_valid = self.validate_weights(force=True)

        if not is_valid:
            total_weight = self.get_total_weight()

            # Create detailed error message
            error_count = len(self.validation_errors)
            message = f"Dimension weight validation failed with {error_count} error(s)"

            # Raise with structured error collection
            raise WeightValidationError(
                message=message,
                errors=self.validation_errors.copy(),
                total_weight=total_weight,
                expected_weight=100.0,
                tolerance=self.tolerance,
            )
