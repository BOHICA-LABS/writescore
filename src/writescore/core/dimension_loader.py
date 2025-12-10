"""Config-driven dimension loading with lazy import support.

This module provides the DimensionLoader class which enables selective,
lazy loading of dimension modules based on configuration profiles.
This avoids loading heavy ML dependencies (torch, transformers, spacy)
when not needed, providing significant performance improvements.

Created for Story 1.4.11: Migrate Analyzer to Registry-Based Dimension Discovery
"""

import importlib
import sys
from typing import Any, Dict, List

from writescore.core.analysis_config import AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry

# Mapping of dimension names to their module paths
DIMENSION_MODULE_MAP = {
    "perplexity": "writescore.dimensions.perplexity",
    "burstiness": "writescore.dimensions.burstiness",
    "structure": "writescore.dimensions.structure",
    "formatting": "writescore.dimensions.formatting",
    "voice": "writescore.dimensions.voice",
    "readability": "writescore.dimensions.readability",
    "lexical": "writescore.dimensions.lexical",
    "sentiment": "writescore.dimensions.sentiment",
    "syntactic": "writescore.dimensions.syntactic",
    "predictability": "writescore.dimensions.predictability",
    "advanced_lexical": "writescore.dimensions.advanced_lexical",
    "transition_marker": "writescore.dimensions.transition_marker",
    "pragmatic_markers": "writescore.dimensions.pragmatic_markers",
    "figurative_language": "writescore.dimensions.figurative_language",
    "semantic_coherence": "writescore.dimensions.semantic_coherence",
    "ai_vocabulary": "writescore.dimensions.ai_vocabulary",
    "energy": "writescore.dimensions.energy",
}

# Built-in dimension profiles
BUILTIN_DIMENSION_PROFILES = {
    "fast": ["perplexity", "burstiness", "structure", "formatting"],  # 4 dims, ~100ms
    "balanced": [
        "perplexity",
        "burstiness",
        "structure",
        "formatting",
        "voice",
        "lexical",
        "readability",
        "sentiment",
    ],  # 8 dims, ~200ms
    "full": list(DIMENSION_MODULE_MAP.keys()),  # 16 dims, ~4-6s (ML dependencies)
}

# User-defined custom profiles
_custom_profiles: Dict[str, List[str]] = {}


class DimensionLoader:
    """
    Lazy loader for dimension modules based on configuration.

    Uses importlib to dynamically import only requested dimensions,
    avoiding heavy ML dependency loads (torch, transformers, spacy)
    when not needed.

    Example:
        >>> loader = DimensionLoader()
        >>> result = loader.load_from_profile('fast')
        >>> print(f"Loaded {len(result['loaded'])} dimensions")
        Loaded 4 dimensions
    """

    def __init__(self):
        """Initialize loader with empty module tracking."""
        self._loaded_modules = set()

    def load_dimensions(self, dimension_names: List[str]) -> Dict[str, Any]:
        """
        Load specified dimensions using dynamic import.

        Args:
            dimension_names: List of dimension names to load

        Returns:
            Dict with 'loaded' list and 'failed' dict
            Example: {'loaded': ['perplexity', 'burstiness'], 'failed': {}}
        """
        loaded: List[str] = []
        failed: Dict[str, str] = {}

        for dim_name in dimension_names:
            if dim_name not in DIMENSION_MODULE_MAP:
                failed[dim_name] = f"Unknown dimension: {dim_name}"
                continue

            # Check if dimension is already registered (not just loaded by this instance)
            if DimensionRegistry.has(dim_name) and dim_name in self._loaded_modules:
                loaded.append(dim_name)
                continue

            module_path = DIMENSION_MODULE_MAP[dim_name]

            try:
                # === KEY LAZY LOADING STEP ===
                # Import module, which triggers module-level singleton instantiation
                # The _instance = DimensionClass() line at end of each dimension file
                # executes, which calls __init__, which calls DimensionRegistry.register()
                #
                # If module was already imported but dimension not registered (e.g., registry
                # was cleared), force reload to trigger re-registration
                if module_path in sys.modules and not DimensionRegistry.has(dim_name):
                    importlib.reload(sys.modules[module_path])
                else:
                    importlib.import_module(module_path)

                self._loaded_modules.add(dim_name)

                # Verify dimension self-registered
                if not DimensionRegistry.has(dim_name):
                    failed[dim_name] = "Module loaded but dimension did not self-register"
                    continue

                loaded.append(dim_name)

            except Exception as e:
                failed[dim_name] = str(e)
                print(f"Warning: Failed to load dimension '{dim_name}': {e}", file=sys.stderr)

        return {"loaded": loaded, "failed": failed}

    @classmethod
    def register_custom_profile(cls, profile_name: str, dimensions: List[str]) -> None:
        """
        Register a custom user-defined dimension profile.

        Args:
            profile_name: Name for the custom profile
            dimensions: List of dimension names in this profile

        Raises:
            ValueError: If trying to override built-in profile or invalid dimension names

        Example:
            >>> DimensionLoader.register_custom_profile(
            ...     'writing_quality',
            ...     ['perplexity', 'burstiness', 'voice']
            ... )
        """
        if profile_name in BUILTIN_DIMENSION_PROFILES:
            raise ValueError(
                f"Cannot override built-in profile '{profile_name}'. "
                f"Built-in profiles: {list(BUILTIN_DIMENSION_PROFILES.keys())}"
            )

        # Validate dimension names
        invalid = [d for d in dimensions if d not in DIMENSION_MODULE_MAP]
        if invalid:
            raise ValueError(f"Unknown dimensions in profile: {invalid}")

        _custom_profiles[profile_name] = dimensions

    @classmethod
    def list_profiles(cls) -> Dict[str, List[str]]:
        """
        Get all available profiles (built-in + custom).

        Returns:
            Dict mapping profile_name -> dimension_list

        Example:
            >>> profiles = DimensionLoader.list_profiles()
            >>> print(profiles.keys())
            dict_keys(['fast', 'balanced', 'full'])
        """
        return {**BUILTIN_DIMENSION_PROFILES, **_custom_profiles}

    def load_from_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Load dimensions from a profile (built-in or custom).

        Args:
            profile_name: Name of profile to load ('fast', 'balanced', 'full', or custom)

        Returns:
            Dict with 'loaded' list and 'failed' dict

        Raises:
            ValueError: If profile doesn't exist

        Example:
            >>> loader = DimensionLoader()
            >>> result = loader.load_from_profile('balanced')
            >>> print(result['loaded'])
            ['perplexity', 'burstiness', 'structure', 'formatting', 'voice', 'lexical', 'readability', 'sentiment']
        """
        if profile_name in BUILTIN_DIMENSION_PROFILES:
            dimensions = BUILTIN_DIMENSION_PROFILES[profile_name]
        elif profile_name in _custom_profiles:
            dimensions = _custom_profiles[profile_name]
        else:
            raise ValueError(
                f"Unknown profile: '{profile_name}'. "
                f"Available profiles: {list(self.list_profiles().keys())}"
            )

        print(f"Loading dimensions from profile '{profile_name}': {dimensions}", file=sys.stderr)
        return self.load_dimensions(dimensions)

    def load_from_config(self, config: AnalysisConfig) -> Dict[str, Any]:
        """
        Load dimensions based on AnalysisConfig.

        Args:
            config: AnalysisConfig with dimension loading settings

        Returns:
            Dict with 'loaded' list and 'failed' dict

        Example:
            >>> from writescore.core.analysis_config import AnalysisConfig
            >>> config = AnalysisConfig(dimension_profile='fast')
            >>> loader = DimensionLoader()
            >>> result = loader.load_from_config(config)
        """
        # Explicit dimension list takes precedence over profile
        if hasattr(config, "dimensions_to_load") and config.dimensions_to_load:
            return self.load_dimensions(config.dimensions_to_load)

        # Otherwise use profile
        profile = getattr(config, "dimension_profile", "balanced")
        return self.load_from_profile(profile)
