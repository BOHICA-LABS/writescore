"""
Configuration loader with layered override support.

Loads configuration from multiple sources in priority order:
1. Base config (config/base.yaml) - lowest priority
2. Local config (config/local.yaml) - user overrides, git-ignored
3. Environment variables (WRITESCORE_*) - highest priority
4. Programmatic overrides - runtime overrides

Story 8.1: Configuration Over Code
"""

import os
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from writescore.core.config_schema import (
    PartialWriteScoreConfig,
    WriteScoreConfig,
)


class PartialConfigValidationError(Exception):
    """Raised when partial/override configuration validation fails."""

    pass


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


def _get_project_root() -> Path:
    """
    Get the project root directory.

    Handles both development and PyInstaller frozen environments.
    """
    import sys

    # Check if running in a PyInstaller frozen environment
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # In frozen mode, config is bundled with the executable
        meipass = Path(sys._MEIPASS)
        if (meipass / "config" / "base.yaml").exists():
            return meipass
        # Also check next to the executable
        exe_dir = Path(sys.executable).parent
        if (exe_dir / "config" / "base.yaml").exists():
            return exe_dir

    # Development mode: walk up from this file to find pyproject.toml
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    # Fallback to current working directory
    return Path.cwd()


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Override values take precedence. Nested dicts are merged recursively.
    Lists are replaced, not merged.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = _deep_merge(result[key], value)
        else:
            # Override the value (including lists)
            result[key] = deepcopy(value)

    return result


def _env_to_config(env_prefix: str = "WRITESCORE_") -> Dict[str, Any]:
    """
    Convert environment variables to config dictionary.

    Environment variable naming convention:
    - WRITESCORE_DIMENSIONS_FORMATTING_WEIGHT=12.0
    - WRITESCORE_SCORING_THRESHOLDS_AI_LIKELY=35

    Args:
        env_prefix: Prefix for environment variables

    Returns:
        Configuration dictionary from environment variables
    """
    result: Dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(env_prefix):
            continue

        # Remove prefix and convert to lowercase
        config_key = key[len(env_prefix) :].lower()
        parts = config_key.split("_")

        # Build nested dict structure
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the final value with type conversion
        final_key = parts[-1]
        current[final_key] = _convert_env_value(value)

    return result


def _convert_env_value(value: str) -> Union[str, int, float, bool]:
    """Convert environment variable string to appropriate type."""
    # Boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String
    return value


class ConfigLoader:
    """
    Configuration loader with layered override support.

    Loads configuration from multiple sources in priority order:
    1. Base config (config/base.yaml) - lowest priority
    2. Local config (config/local.yaml) - user overrides
    3. Environment variables (WRITESCORE_*) - high priority
    4. Programmatic overrides - highest priority

    Usage:
        loader = ConfigLoader()
        config = loader.load()

        # With programmatic overrides
        config = loader.load(overrides={"dimensions": {"formatting": {"weight": 15.0}}})

        # Custom config paths
        loader = ConfigLoader(
            base_path="my/base.yaml",
            local_path="my/local.yaml"
        )
    """

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        local_path: Optional[Union[str, Path]] = None,
        project_root: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the config loader.

        Args:
            base_path: Path to base config file (default: config/base.yaml)
            local_path: Path to local override file (default: config/local.yaml)
            project_root: Project root directory (auto-detected if not provided)
        """
        self._project_root = Path(project_root) if project_root else _get_project_root()

        # Set default paths relative to project root
        self._base_path = (
            Path(base_path) if base_path else self._project_root / "config" / "base.yaml"
        )
        self._local_path = (
            Path(local_path) if local_path else self._project_root / "config" / "local.yaml"
        )

        self._cached_config: Optional[WriteScoreConfig] = None
        self._cached_raw: Optional[Dict[str, Any]] = None

    def _validate_partial(
        self,
        config: Dict[str, Any],
        source: str,
    ) -> None:
        """
        Validate a partial/override configuration.

        Args:
            config: Configuration dictionary to validate
            source: Description of config source (for error messages)

        Raises:
            PartialConfigValidationError: If validation fails
        """
        try:
            PartialWriteScoreConfig(**config)
        except Exception as e:
            raise PartialConfigValidationError(
                f"Partial config validation failed for {source}: {e}"
            ) from e

    def load(
        self,
        overrides: Optional[Dict[str, Any]] = None,
        skip_env: bool = False,
        skip_local: bool = False,
        validate: bool = True,
    ) -> WriteScoreConfig:
        """
        Load configuration with all layers merged.

        Args:
            overrides: Programmatic overrides (highest priority)
            skip_env: Skip environment variable processing
            skip_local: Skip local.yaml loading
            validate: Whether to validate with Pydantic schema

        Returns:
            Validated WriteScoreConfig instance

        Raises:
            ConfigLoadError: If base config cannot be loaded
            PartialConfigValidationError: If override config validation fails
            ConfigValidationError: If final merged config validation fails
        """
        # Load base config (required)
        config = self._load_yaml(self._base_path, required=True)

        # Load local overrides (optional) - validate before merging
        if not skip_local and self._local_path.exists():
            local_config = self._load_yaml(self._local_path, required=False)
            if local_config:
                if validate:
                    self._validate_partial(local_config, str(self._local_path))
                config = _deep_merge(config, local_config)

        # Apply environment variable overrides - validate before merging
        if not skip_env:
            env_config = _env_to_config()
            if env_config:
                if validate:
                    self._validate_partial(env_config, "environment variables")
                config = _deep_merge(config, env_config)

        # Apply programmatic overrides - validate before merging
        if overrides:
            if validate:
                self._validate_partial(overrides, "programmatic overrides")
            config = _deep_merge(config, overrides)

        # Cache raw config
        self._cached_raw = config

        # Validate final merged config and return
        if validate:
            try:
                self._cached_config = WriteScoreConfig(**config)
                return self._cached_config
            except Exception as e:
                raise ConfigValidationError(f"Configuration validation failed: {e}") from e
        else:
            # Skip validation
            self._cached_config = WriteScoreConfig(**config)
            return self._cached_config

    def load_raw(
        self,
        overrides: Optional[Dict[str, Any]] = None,
        skip_env: bool = False,
        skip_local: bool = False,
    ) -> Dict[str, Any]:
        """
        Load raw configuration without Pydantic validation.

        Useful for inspection or when you need the raw dict.

        Args:
            overrides: Programmatic overrides
            skip_env: Skip environment variable processing
            skip_local: Skip local.yaml loading

        Returns:
            Raw configuration dictionary
        """
        # Load base config (required)
        config = self._load_yaml(self._base_path, required=True)

        # Load local overrides (optional)
        if not skip_local and self._local_path.exists():
            local_config = self._load_yaml(self._local_path, required=False)
            if local_config:
                config = _deep_merge(config, local_config)

        # Apply environment variable overrides
        if not skip_env:
            env_config = _env_to_config()
            if env_config:
                config = _deep_merge(config, env_config)

        # Apply programmatic overrides
        if overrides:
            config = _deep_merge(config, overrides)

        return config

    def _load_yaml(self, path: Path, required: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load a YAML file.

        Args:
            path: Path to YAML file
            required: Whether file must exist

        Returns:
            Parsed YAML as dict, or None if optional file doesn't exist

        Raises:
            ConfigLoadError: If required file missing or invalid YAML
        """
        if not path.exists():
            if required:
                raise ConfigLoadError(f"Required config file not found: {path}")
            return None

        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {path}: {e}") from e
        except Exception as e:
            raise ConfigLoadError(f"Failed to load {path}: {e}") from e

    def get_cached_config(self) -> Optional[WriteScoreConfig]:
        """Get the last loaded config without reloading."""
        return self._cached_config

    def get_cached_raw(self) -> Optional[Dict[str, Any]]:
        """Get the last loaded raw config without reloading."""
        return self._cached_raw

    def reload(self, **kwargs) -> WriteScoreConfig:
        """Force reload configuration."""
        self._cached_config = None
        self._cached_raw = None
        return self.load(**kwargs)

    @property
    def base_path(self) -> Path:
        """Get base config path."""
        return self._base_path

    @property
    def local_path(self) -> Path:
        """Get local config path."""
        return self._local_path

    @property
    def project_root(self) -> Path:
        """Get project root path."""
        return self._project_root


# ==============================================================================
# Module-level convenience functions
# ==============================================================================


@lru_cache(maxsize=1)
def get_default_loader() -> ConfigLoader:
    """Get the default config loader (cached)."""
    return ConfigLoader()


def load_config(overrides: Optional[Dict[str, Any]] = None, **kwargs) -> WriteScoreConfig:
    """
    Load configuration using the default loader.

    Convenience function for quick config access.

    Args:
        overrides: Programmatic overrides
        **kwargs: Additional arguments passed to ConfigLoader.load()

    Returns:
        Validated WriteScoreConfig instance
    """
    loader = get_default_loader()
    return loader.load(overrides=overrides, **kwargs)


def load_config_raw(overrides: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """
    Load raw configuration using the default loader.

    Args:
        overrides: Programmatic overrides
        **kwargs: Additional arguments passed to ConfigLoader.load_raw()

    Returns:
        Raw configuration dictionary
    """
    loader = get_default_loader()
    return loader.load_raw(overrides=overrides, **kwargs)


def reload_config(**kwargs) -> WriteScoreConfig:
    """
    Reload configuration, clearing the cache.

    Args:
        **kwargs: Arguments passed to ConfigLoader.reload()

    Returns:
        Fresh WriteScoreConfig instance
    """
    # Clear the cached loader
    get_default_loader.cache_clear()
    return load_config(**kwargs)
