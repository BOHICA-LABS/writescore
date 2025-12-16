"""
ConfigRegistry - Thread-safe singleton for global configuration access.

Provides centralized access to WriteScore configuration with:
- Thread-safe singleton pattern
- Lazy initialization
- Content type support
- Dimension weight retrieval
- Threshold access with fallbacks

Story 8.1: Configuration Over Code
"""

import threading
from typing import Any, Dict, List, Optional, Union

from writescore.core.config_loader import ConfigLoader
from writescore.core.config_schema import (
    ContentTypeConfig,
    DimensionConfig,
    ProfileConfig,
    WriteScoreConfig,
)


class ConfigRegistry:
    """
    Thread-safe singleton registry for global configuration access.

    Provides convenient methods to access configuration values with
    type safety and fallback support.

    Usage:
        # Get singleton instance
        registry = ConfigRegistry.get_instance()

        # Access dimension weight
        weight = registry.get_dimension_weight("formatting")

        # Access threshold with fallback
        threshold = registry.get_threshold("scoring.thresholds.ai_likely", default=40)

        # Set content type for adjusted weights
        registry.set_content_type("technical")

        # Reset to reload config
        ConfigRegistry.reset()
    """

    _instance: Optional["ConfigRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigRegistry":
        """Thread-safe singleton creation."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry (only runs once due to singleton)."""
        if self._initialized:
            return

        self._config: Optional[WriteScoreConfig] = None
        self._loader: Optional[ConfigLoader] = None
        self._content_type: Optional[str] = None
        self._overrides: Dict[str, Any] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "ConfigRegistry":
        """Get the singleton instance."""
        return cls()

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._config = None
                cls._instance._loader = None
                cls._instance._content_type = None
                cls._instance._overrides = {}

    def _ensure_loaded(self) -> WriteScoreConfig:
        """Ensure configuration is loaded."""
        if self._config is None:
            self._loader = ConfigLoader()
            self._config = self._loader.load(overrides=self._overrides)
        return self._config

    def get_config(self) -> WriteScoreConfig:
        """Get the full configuration object."""
        return self._ensure_loaded()

    def reload(self, overrides: Optional[Dict[str, Any]] = None) -> WriteScoreConfig:
        """
        Reload configuration from disk.

        Args:
            overrides: Optional new overrides to apply

        Returns:
            Fresh WriteScoreConfig instance
        """
        if overrides is not None:
            self._overrides = overrides
        self._config = None
        self._loader = None
        return self._ensure_loaded()

    def set_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Set programmatic overrides and reload.

        Args:
            overrides: Configuration overrides to apply
        """
        self._overrides = overrides
        self._config = None  # Force reload on next access

    def set_content_type(self, content_type: str) -> None:
        """
        Set the active content type for weight/threshold adjustments.

        Args:
            content_type: Content type name (e.g., "technical", "academic")
        """
        self._content_type = content_type

    def get_content_type(self) -> Optional[str]:
        """Get the active content type."""
        return self._content_type

    def clear_content_type(self) -> None:
        """Clear the active content type."""
        self._content_type = None

    # =========================================================================
    # Dimension Access Methods
    # =========================================================================

    def get_dimension_config(self, dimension_name: str) -> Optional[DimensionConfig]:
        """
        Get configuration for a specific dimension.

        Args:
            dimension_name: Name of the dimension

        Returns:
            DimensionConfig or None if not found
        """
        config = self._ensure_loaded()
        if config.dimensions:
            return config.dimensions.get_dimension(dimension_name)
        return None

    def get_dimension_weight(self, dimension_name: str, default: float = 5.0) -> float:
        """
        Get weight for a dimension, adjusted for content type if set.

        Args:
            dimension_name: Name of the dimension
            default: Default weight if not found

        Returns:
            Dimension weight (possibly adjusted for content type)
        """
        config = self._ensure_loaded()

        # Get base weight
        base_weight = default
        if config.dimensions:
            dim_config = config.dimensions.get_dimension(dimension_name)
            if dim_config:
                base_weight = dim_config.weight

        # Apply content type adjustment if set
        if self._content_type and config.content_types:
            ct_config = config.content_types.get_content_type(self._content_type)
            if ct_config and ct_config.weight_adjustments:
                adjustment = ct_config.weight_adjustments.get(dimension_name, 1.0)
                return base_weight * adjustment

        return base_weight

    def get_dimension_weights(self) -> Dict[str, float]:
        """
        Get all dimension weights, adjusted for content type if set.

        Returns:
            Dictionary of dimension_name -> weight
        """
        config = self._ensure_loaded()
        weights = {}

        if config.dimensions:
            for name, dim_config in config.dimensions.get_all_dimensions().items():
                weights[name] = self.get_dimension_weight(name, dim_config.weight)

        return weights

    def is_dimension_enabled(self, dimension_name: str) -> bool:
        """
        Check if a dimension is enabled.

        Args:
            dimension_name: Name of the dimension

        Returns:
            True if enabled, False otherwise
        """
        dim_config = self.get_dimension_config(dimension_name)
        if dim_config:
            return dim_config.enabled
        return True  # Default to enabled for unknown dimensions

    def get_enabled_dimensions(self) -> List[str]:
        """
        Get list of enabled dimension names.

        Returns:
            List of dimension names that are enabled
        """
        config = self._ensure_loaded()
        return config.get_enabled_dimensions()

    # =========================================================================
    # Threshold Access Methods
    # =========================================================================

    def get_threshold(
        self, path: str, default: Optional[Union[float, int]] = None
    ) -> Optional[Union[float, int]]:
        """
        Get a threshold value by dotted path.

        Args:
            path: Dotted path (e.g., "scoring.thresholds.ai_likely")
            default: Default value if not found

        Returns:
            Threshold value or default
        """
        config = self._ensure_loaded()

        # Navigate the path
        parts = path.split(".")
        current: Any = config

        for part in parts:
            if current is None:
                return default

            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return default

        return current if current is not None else default

    def get_dimension_threshold(
        self, dimension_name: str, threshold_name: str, default: Optional[Union[float, int]] = None
    ) -> Optional[Union[float, int]]:
        """
        Get a threshold for a specific dimension.

        Args:
            dimension_name: Name of the dimension
            threshold_name: Name of the threshold
            default: Default value if not found

        Returns:
            Threshold value or default
        """
        config = self._ensure_loaded()

        # First check content type overrides
        if self._content_type and config.content_types:
            ct_config = config.content_types.get_content_type(self._content_type)
            if ct_config and ct_config.threshold_adjustments:
                dim_adjustments = ct_config.threshold_adjustments.get(dimension_name, {})
                if threshold_name in dim_adjustments:
                    return dim_adjustments[threshold_name]

        # Then check dimension config
        dim_config = self.get_dimension_config(dimension_name)
        if dim_config and dim_config.thresholds:
            return dim_config.thresholds.get(threshold_name, default)

        return default

    # =========================================================================
    # Profile Access Methods
    # =========================================================================

    def get_profile(self, profile_name: str) -> Optional[ProfileConfig]:
        """
        Get a dimension profile configuration.

        Args:
            profile_name: Name of the profile

        Returns:
            ProfileConfig or None if not found
        """
        config = self._ensure_loaded()
        if config.profiles:
            return config.profiles.get_profile(profile_name)
        return None

    def get_profile_dimensions(self, profile_name: str) -> List[str]:
        """
        Get list of dimensions for a profile.

        Args:
            profile_name: Name of the profile

        Returns:
            List of dimension names in the profile
        """
        profile = self.get_profile(profile_name)
        if profile:
            return profile.dimensions
        return []

    # =========================================================================
    # Content Type Access Methods
    # =========================================================================

    def get_content_type_config(self, content_type_name: str) -> Optional[ContentTypeConfig]:
        """
        Get configuration for a content type.

        Args:
            content_type_name: Name of the content type

        Returns:
            ContentTypeConfig or None if not found
        """
        config = self._ensure_loaded()
        if config.content_types:
            return config.content_types.get_content_type(content_type_name)
        return None

    def get_available_content_types(self) -> List[str]:
        """
        Get list of available content type names.

        Returns:
            List of content type names
        """
        config = self._ensure_loaded()
        if config.content_types:
            # Use dynamic types list if available
            if hasattr(config.content_types, "types") and config.content_types.types:
                return config.content_types.types
            # Fallback to checking for defined content types
            return [
                name
                for name in [
                    "general",
                    "technical",
                    "academic",
                    "creative",
                    "social_media",
                    "business",
                ]
                if config.content_types.get_content_type(name) is not None
            ]
        return []

    def get_content_type_weights(self, content_type_name: str) -> Optional[Dict[str, float]]:
        """
        Get dimension weights for a content type.

        Args:
            content_type_name: Name of the content type

        Returns:
            Dictionary of dimension_name -> weight, or None if not found
        """
        config = self._ensure_loaded()
        if config.content_types:
            return config.content_types.get_weights(content_type_name)
        return None

    def get_content_type_thresholds(self, content_type_name: str) -> Optional[Any]:
        """
        Get thresholds for a content type.

        Args:
            content_type_name: Name of the content type

        Returns:
            ContentTypeThresholds or None if not found
        """
        config = self._ensure_loaded()
        if config.content_types:
            return config.content_types.get_thresholds(content_type_name)
        return None

    # =========================================================================
    # Scoring Access Methods
    # =========================================================================

    def get_scoring_threshold(
        self, threshold_name: str, default: Optional[float] = None
    ) -> Optional[float]:
        """
        Get a scoring threshold value.

        Args:
            threshold_name: Name of the threshold
            default: Default value if not found

        Returns:
            Threshold value or default
        """
        return self.get_threshold(f"scoring.thresholds.{threshold_name}", default=default)

    # =========================================================================
    # Analysis Mode Access Methods
    # =========================================================================

    def get_default_analysis_mode(self) -> str:
        """Get the default analysis mode."""
        config = self._ensure_loaded()
        if config.analysis and config.analysis.defaults:
            return config.analysis.defaults.mode.value
        return "adaptive"

    def get_sampling_sections(self) -> int:
        """Get default sampling sections count."""
        config = self._ensure_loaded()
        if config.analysis and config.analysis.defaults:
            return config.analysis.defaults.sampling_sections
        return 5


# ==============================================================================
# Module-level convenience function
# ==============================================================================


def get_config_registry() -> ConfigRegistry:
    """Get the global ConfigRegistry singleton."""
    return ConfigRegistry.get_instance()
