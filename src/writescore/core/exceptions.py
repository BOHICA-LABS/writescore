"""
Custom exceptions for AI Pattern Analyzer package.

This module defines all package-wide exceptions with contextual information
for better error handling and debugging.
"""


class AIPatternAnalyzerError(Exception):
    """Base exception for all AI Pattern Analyzer package errors."""

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__str__()!r})"


class DimensionNotFoundError(AIPatternAnalyzerError):
    """
    Raised when attempting to retrieve a dimension that doesn't exist.

    Attributes:
        dimension_name (str): The name of the dimension that was not found
        message (str): Error message with details

    Example:
        >>> raise DimensionNotFoundError(
        ...     "Dimension 'foo' not found",
        ...     dimension_name='foo'
        ... )
    """

    def __init__(self, message, dimension_name=None):
        """
        Initialize DimensionNotFoundError.

        Args:
            message (str): Error message
            dimension_name (str, optional): Name of the dimension that was not found
        """
        super().__init__(message)
        self.dimension_name = dimension_name

    def __repr__(self):
        return f"DimensionNotFoundError(dimension_name={self.dimension_name!r})"


class DuplicateDimensionError(AIPatternAnalyzerError):
    """
    Raised when attempting to register a dimension that already exists.

    Attributes:
        dimension_name (str): The name of the duplicate dimension
        message (str): Error message with details

    Example:
        >>> raise DuplicateDimensionError(
        ...     "Dimension 'bar' already registered",
        ...     dimension_name='bar'
        ... )
    """

    def __init__(self, message, dimension_name=None):
        """
        Initialize DuplicateDimensionError.

        Args:
            message (str): Error message
            dimension_name (str, optional): Name of the duplicate dimension
        """
        super().__init__(message)
        self.dimension_name = dimension_name

    def __repr__(self):
        return f"DuplicateDimensionError(dimension_name={self.dimension_name!r})"


class InvalidTierError(AIPatternAnalyzerError):
    """
    Raised when dimension tier is not valid.

    Attributes:
        tier (str): The invalid tier value
        valid_tiers (set): Set of valid tier values
        message (str): Error message with details

    Example:
        >>> raise InvalidTierError(
        ...     "Invalid tier 'INVALID'",
        ...     tier='INVALID',
        ...     valid_tiers={'ADVANCED', 'CORE', 'SUPPORTING', 'STRUCTURAL'}
        ... )
    """

    def __init__(self, message, tier=None, valid_tiers=None):
        """
        Initialize InvalidTierError.

        Args:
            message (str): Error message
            tier (str, optional): The invalid tier value
            valid_tiers (set, optional): Set of valid tier values
        """
        super().__init__(message)
        self.tier = tier
        self.valid_tiers = valid_tiers

    def __repr__(self):
        return f"InvalidTierError(tier={self.tier!r}, " f"valid_tiers={self.valid_tiers})"


class InvalidWeightError(AIPatternAnalyzerError):
    """
    Raised when dimension weight is out of valid range [0, 100].

    Attributes:
        weight (float): The invalid weight value
        valid_range (tuple): The valid range (min, max)
        message (str): Error message with details

    Example:
        >>> raise InvalidWeightError(
        ...     "Weight 150 out of range",
        ...     weight=150,
        ...     valid_range=(0, 100)
        ... )
    """

    def __init__(self, message, weight=None, valid_range=None):
        """
        Initialize InvalidWeightError.

        Args:
            message (str): Error message
            weight (float, optional): The invalid weight value
            valid_range (tuple, optional): The valid range (min, max), defaults to (0, 100)
        """
        super().__init__(message)
        self.weight = weight
        self.valid_range = valid_range or (0, 100)

    def __repr__(self):
        return f"InvalidWeightError(weight={self.weight}, " f"valid_range={self.valid_range})"


class ParameterLoadError(AIPatternAnalyzerError):
    """
    Raised when parameter configuration cannot be loaded or is invalid.

    Introduced in Story 2.5 for percentile-anchored parameter infrastructure.

    Attributes:
        message (str): Error message with details
        config_path (str, optional): Path to configuration file that failed to load

    Example:
        >>> raise ParameterLoadError(
        ...     "Cannot parse YAML configuration",
        ...     config_path="config/scoring_parameters.yaml"
        ... )
    """

    def __init__(self, message, config_path=None):
        """
        Initialize ParameterLoadError.

        Args:
            message (str): Error message
            config_path (str, optional): Path to configuration file
        """
        super().__init__(message)
        self.config_path = config_path

    def __repr__(self):
        return f"ParameterLoadError(config_path={self.config_path!r})"
