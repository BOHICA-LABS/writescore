"""
Thread-safe dimension registry for self-registering dimension architecture.

This module provides a class-based registry pattern for dimension discovery
and management without requiring core algorithm modifications when adding
new dimensions.
"""

import logging
import threading
from typing import Any, Dict, List

from writescore.core.exceptions import (
    DimensionNotFoundError,
    DuplicateDimensionError,
    InvalidTierError,
    InvalidWeightError,
)
from writescore.dimensions.base_strategy import DimensionStrategy

logger = logging.getLogger(__name__)


class DimensionRegistry:
    """
    Thread-safe registry for dimension discovery and management.

    Uses class-level storage for dimensions, making it easy to test and
    integrate with Python's module system. All methods are classmethods.

    Usage:
        # Registration (typically in dimension __init__)
        DimensionRegistry.register(self)

        # Retrieval
        dim = DimensionRegistry.get('perplexity')
        all_dims = DimensionRegistry.get_all()
        core_dims = DimensionRegistry.get_by_tier('CORE')

        # Testing
        DimensionRegistry.clear()

    Thread Safety:
        All operations are protected by threading.Lock for safe concurrent access.
    """

    # Class-level storage
    _dimensions: Dict[str, DimensionStrategy] = {}
    _tiers: Dict[str, List[str]] = {"ADVANCED": [], "CORE": [], "SUPPORTING": [], "STRUCTURAL": []}
    _name_map: Dict[str, str] = {}  # normalized → original name
    _lock = threading.Lock()

    VALID_TIERS = {"ADVANCED", "CORE", "SUPPORTING", "STRUCTURAL"}

    @classmethod
    def register(
        cls, dimension: DimensionStrategy, allow_overwrite: bool = True
    ) -> DimensionStrategy:
        """
        Register a dimension with the registry.

        Args:
            dimension: Dimension instance implementing DimensionStrategy
            allow_overwrite: If True, silently return existing dimension if already registered.
                           If False, raise DuplicateDimensionError on duplicate. Default: True.

        Returns:
            The registered dimension instance (or existing if already registered)

        Raises:
            DuplicateDimensionError: If dimension already registered and allow_overwrite=False
            InvalidTierError: If dimension tier is not valid
            InvalidWeightError: If dimension weight is not in [0, 100]

        Example:
            class MyDimension(DimensionStrategy):
                def __init__(self):
                    super().__init__()
                    DimensionRegistry.register(self)

        Note:
            By default (allow_overwrite=True), registration is idempotent - re-registering
            an existing dimension name will silently return the already-registered instance.
            This makes it safe for modules to be imported multiple times in test environments.
        """
        with cls._lock:
            # Validate dimension name
            name = dimension.dimension_name
            if not name or not isinstance(name, str):
                raise ValueError("Dimension name must be non-empty string")

            # Normalize name for case-insensitive lookup
            normalized_name = name.lower()

            # Check for duplicates
            if normalized_name in cls._dimensions:
                if allow_overwrite:
                    # Idempotent behavior: return existing dimension
                    logger.debug(
                        f"Dimension '{name}' already registered, returning existing instance"
                    )
                    return cls._dimensions[normalized_name]
                else:
                    raise DuplicateDimensionError(
                        f"Dimension '{name}' is already registered", dimension_name=name
                    )

            # Validate tier
            tier = dimension.tier
            # Handle both string and DimensionTier enum
            tier_str = tier.value if hasattr(tier, "value") else str(tier)
            if tier_str not in cls.VALID_TIERS:
                raise InvalidTierError(
                    f"Invalid tier '{tier_str}'. Must be one of: {cls.VALID_TIERS}",
                    tier=tier_str,
                    valid_tiers=cls.VALID_TIERS,
                )

            # Validate weight
            weight = dimension.weight
            if not (0 <= weight <= 100):
                raise InvalidWeightError(
                    f"Weight {weight} out of range. Must be between 0 and 100",
                    weight=weight,
                    valid_range=(0, 100),
                )

            # Register dimension
            cls._dimensions[normalized_name] = dimension
            cls._tiers[tier_str].append(normalized_name)
            cls._name_map[normalized_name] = name

            logger.debug(f"Registered dimension '{name}' (tier={tier_str}, weight={weight})")

            return dimension

    @classmethod
    def get(cls, dimension_name: str) -> DimensionStrategy:
        """
        Retrieve a dimension by name (case-insensitive).

        Args:
            dimension_name: Name of dimension to retrieve

        Returns:
            Dimension instance

        Raises:
            DimensionNotFoundError: If dimension not registered
        """
        with cls._lock:
            normalized_name = dimension_name.lower()
            if normalized_name not in cls._dimensions:
                raise DimensionNotFoundError(
                    f"Dimension '{dimension_name}' not found. "
                    f"Registered dimensions: {list(cls._name_map.values())}",
                    dimension_name=dimension_name,
                )
            return cls._dimensions[normalized_name]

    @classmethod
    def get_all(cls) -> List[DimensionStrategy]:
        """
        Get all registered dimensions.

        Returns:
            List of all dimension instances (shallow copy)
        """
        with cls._lock:
            return list(cls._dimensions.values())

    @classmethod
    def get_by_tier(cls, tier: str) -> List[DimensionStrategy]:
        """
        Get all dimensions for a specific tier.

        Args:
            tier: Tier name (ADVANCED, CORE, SUPPORTING, STRUCTURAL)

        Returns:
            List of dimension instances in that tier

        Raises:
            InvalidTierError: If tier is not valid
        """
        if tier not in cls.VALID_TIERS:
            raise InvalidTierError(
                f"Invalid tier '{tier}'. Must be one of: {cls.VALID_TIERS}",
                tier=tier,
                valid_tiers=cls.VALID_TIERS,
            )

        with cls._lock:
            dim_names = cls._tiers.get(tier, [])
            return [cls._dimensions[name] for name in dim_names]

    @classmethod
    def get_count(cls) -> int:
        """Get total number of registered dimensions."""
        with cls._lock:
            return len(cls._dimensions)

    @classmethod
    def get_tiers_summary(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of all tiers with counts and dimension names.

        Returns:
            Dict mapping tier name to {'count': int, 'dimensions': List[str]}
        """
        with cls._lock:
            summary = {}
            for tier, dim_names in cls._tiers.items():
                summary[tier] = {
                    "count": len(dim_names),
                    "dimensions": [cls._name_map[name] for name in dim_names],
                }
            return summary

    @classmethod
    def has(cls, dimension_name: str) -> bool:
        """
        Check if dimension is registered (case-insensitive).

        Args:
            dimension_name: Name to check

        Returns:
            True if registered, False otherwise
        """
        with cls._lock:
            return dimension_name.lower() in cls._dimensions

    @classmethod
    def clear(cls):
        """
        Clear all registered dimensions.

        Used primarily for testing to reset registry state between tests.
        """
        with cls._lock:
            cls._dimensions.clear()
            for tier_list in cls._tiers.values():
                tier_list.clear()
            cls._name_map.clear()
            logger.debug("Registry cleared")

    @classmethod
    def validate_no_deprecated(cls) -> bool:
        """
        Validate that no deprecated dimensions are registered.

        For use in v5.0.0+ to ensure cleanup is complete.

        Returns:
            True if no deprecated dimensions found

        Raises:
            RuntimeError: If deprecated dimensions still registered

        Example:
            >>> DimensionRegistry.validate_no_deprecated()  # Raises if any deprecated dims found
        """
        with cls._lock:
            deprecated = [
                d for d in cls._dimensions.values() if d.dimension_name.endswith("_deprecated")
            ]

            if deprecated:
                names = [d.dimension_name for d in deprecated]
                raise RuntimeError(
                    f"Deprecated dimensions still registered in v5.0.0: {names}. "
                    f"This indicates incomplete cleanup from Story 1.4.5."
                )

            return True

    @classmethod
    def __repr__(cls):
        """Debug representation showing registry state."""
        with cls._lock:
            tier_counts = {tier: len(dims) for tier, dims in cls._tiers.items()}
            total = len(cls._dimensions)
            return f"DimensionRegistry(total={total}, " f"tiers={tier_counts})"


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================


def register_dimension(dimension: DimensionStrategy) -> DimensionStrategy:
    """
    Convenience function for registering a dimension.

    Args:
        dimension: Dimension instance to register

    Returns:
        The registered dimension instance

    Example:
        >>> dim = MyDimension()
        >>> register_dimension(dim)
    """
    return DimensionRegistry.register(dimension)


def get_dimension(name: str) -> DimensionStrategy:
    """
    Convenience function for retrieving a dimension.

    Args:
        name: Dimension name to retrieve

    Returns:
        Dimension instance

    Example:
        >>> dim = get_dimension('perplexity')
    """
    return DimensionRegistry.get(name)


def list_dimensions() -> List[DimensionStrategy]:
    """
    Convenience function for listing all dimensions.

    Returns:
        List of all registered dimension instances

    Example:
        >>> all_dims = list_dimensions()
    """
    return DimensionRegistry.get_all()
