"""
Parameter loader for YAML-based configuration files.

Loads, validates, and manages percentile-anchored scoring parameters from
YAML configuration files. Provides fallback to literature-based defaults
when configuration is unavailable.

Created in Story 2.5 for automatic recalibration infrastructure.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from writescore.core.exceptions import ParameterLoadError
from writescore.core.parameters import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    ParameterValue,
    PercentileParameters,
    PercentileSource,
    ScoringType,
    ThresholdParameters,
)

logger = logging.getLogger(__name__)


class ParameterLoader:
    """
    Loads and manages percentile-anchored scoring parameters.

    Handles:
    - Loading from YAML configuration files
    - Validation of parameter structure and values
    - Fallback to literature-based defaults
    - Parameter versioning and migration
    """

    DEFAULT_CONFIG_PATH = Path("config/scoring_parameters.yaml")
    FALLBACK_CONFIG_PATH = Path("config/scoring_parameters_fallback.yaml")

    @classmethod
    def load(
        cls, config_path: Optional[Path] = None, use_fallback: bool = False
    ) -> PercentileParameters:
        """
        Load parameters from YAML configuration.

        Args:
            config_path: Path to configuration file (default: config/scoring_parameters.yaml)
            use_fallback: If True, use fallback defaults without trying to load config

        Returns:
            PercentileParameters instance

        Raises:
            ParameterLoadError: If configuration cannot be loaded or is invalid
        """
        if use_fallback:
            logger.info("Using fallback parameters (literature-based defaults)")
            return cls._load_fallback_parameters()

        if config_path is None:
            config_path = cls.DEFAULT_CONFIG_PATH

        try:
            return cls._load_from_file(config_path)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            logger.info("Attempting to load fallback parameters")
            return cls._load_fallback_parameters()
        except Exception as e:
            logger.error(f"Failed to load parameters from {config_path}: {e}")
            raise ParameterLoadError(f"Cannot load parameter configuration: {e}") from e

    @classmethod
    def _load_from_file(cls, config_path: Path) -> PercentileParameters:
        """Load and parse YAML configuration file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            raise ParameterLoadError("Configuration file is empty")

        return cls._parse_config(config_data)

    @classmethod
    def _parse_config(cls, config_data: Dict[str, Any]) -> PercentileParameters:
        """Parse configuration dictionary into PercentileParameters."""
        # Extract top-level metadata
        version = config_data.get("version")
        timestamp = config_data.get("timestamp")
        validation_dataset_version = config_data.get("validation_dataset_version")

        if not all([version, timestamp, validation_dataset_version]):
            raise ParameterLoadError(
                "Configuration must include: version, timestamp, validation_dataset_version"
            )

        # Create PercentileParameters container
        # Cast to str since we've validated they exist above
        params = PercentileParameters(
            version=str(version),
            timestamp=str(timestamp),
            validation_dataset_version=str(validation_dataset_version),
            metadata=config_data.get("metadata", {}),
        )

        # Parse dimension parameters
        dimensions_config = config_data.get("parameters", {})
        if not dimensions_config:
            logger.warning("No dimension parameters found in configuration")

        for dim_name, dim_config in dimensions_config.items():
            try:
                dim_params = cls._parse_dimension(dim_name, dim_config)
                params.add_dimension(dim_params)
            except Exception as e:
                logger.error(f"Failed to parse dimension '{dim_name}': {e}")
                raise ParameterLoadError(
                    f"Invalid configuration for dimension '{dim_name}': {e}"
                ) from e

        # Validate complete parameter set
        params.validate()

        logger.info(f"Loaded parameters version {version} with {len(params.dimensions)} dimensions")
        return params

    @classmethod
    def _parse_dimension(cls, dim_name: str, dim_config: Dict[str, Any]) -> DimensionParameters:
        """Parse a single dimension's configuration."""
        scoring_type = dim_config.get("scoring_type")
        if not scoring_type:
            raise ValueError(f"Missing 'scoring_type' for dimension '{dim_name}'")

        try:
            scoring_type_enum = ScoringType(scoring_type)
        except ValueError as e:
            raise ValueError(
                f"Invalid scoring_type '{scoring_type}' for dimension '{dim_name}'. "
                f"Must be one of: {[t.value for t in ScoringType]}"
            ) from e

        # Parse parameters based on scoring type
        parameters: Union[GaussianParameters, MonotonicParameters, ThresholdParameters]
        if scoring_type_enum == ScoringType.GAUSSIAN:
            parameters = cls._parse_gaussian_params(dim_config)
        elif scoring_type_enum == ScoringType.MONOTONIC:
            parameters = cls._parse_monotonic_params(dim_config)
        elif scoring_type_enum == ScoringType.THRESHOLD:
            parameters = cls._parse_threshold_params(dim_config)
        else:
            raise ValueError(f"Unsupported scoring type: {scoring_type_enum}")

        return DimensionParameters(
            dimension_name=dim_name,
            scoring_type=scoring_type_enum,
            parameters=parameters,
            version=dim_config.get("version", "1.0"),
            validation_dataset_version=dim_config.get("validation_dataset_version"),
            timestamp=dim_config.get("timestamp"),
            notes=dim_config.get("notes"),
        )

    @classmethod
    def _parse_parameter_value(cls, param_config: Dict[str, Any]) -> ParameterValue:
        """Parse a single parameter value from configuration."""
        if not isinstance(param_config, dict):
            raise ValueError(f"Parameter must be a dict, got {type(param_config)}")

        value = param_config.get("value")
        source = param_config.get("source")

        if value is None:
            raise ValueError("Parameter must have 'value' field")
        if source is None:
            raise ValueError("Parameter must have 'source' field")

        try:
            source_enum = PercentileSource(source)
        except ValueError as e:
            raise ValueError(
                f"Invalid source '{source}'. Must be one of: {[s.value for s in PercentileSource]}"
            ) from e

        return ParameterValue(
            value=float(value),
            source=source_enum,
            percentile=param_config.get("percentile"),
            description=param_config.get("description"),
        )

    @classmethod
    def _parse_gaussian_params(cls, dim_config: Dict[str, Any]) -> GaussianParameters:
        """Parse Gaussian parameters."""
        target_config = dim_config.get("target")
        width_config = dim_config.get("width")

        if not target_config:
            raise ValueError("Gaussian parameters require 'target'")
        if not width_config:
            raise ValueError("Gaussian parameters require 'width'")

        return GaussianParameters(
            target=cls._parse_parameter_value(target_config),
            width=cls._parse_parameter_value(width_config),
        )

    @classmethod
    def _parse_monotonic_params(cls, dim_config: Dict[str, Any]) -> MonotonicParameters:
        """Parse Monotonic parameters."""
        threshold_low_config = dim_config.get("threshold_low")
        threshold_high_config = dim_config.get("threshold_high")

        if not threshold_low_config:
            raise ValueError("Monotonic parameters require 'threshold_low'")
        if not threshold_high_config:
            raise ValueError("Monotonic parameters require 'threshold_high'")

        return MonotonicParameters(
            threshold_low=cls._parse_parameter_value(threshold_low_config),
            threshold_high=cls._parse_parameter_value(threshold_high_config),
            direction=dim_config.get("direction", "increasing"),
        )

    @classmethod
    def _parse_threshold_params(cls, dim_config: Dict[str, Any]) -> ThresholdParameters:
        """Parse Threshold parameters."""
        thresholds_config = dim_config.get("thresholds")
        labels = dim_config.get("labels")
        scores = dim_config.get("scores")

        if not thresholds_config:
            raise ValueError("Threshold parameters require 'thresholds'")
        if not labels:
            raise ValueError("Threshold parameters require 'labels'")
        if not scores:
            raise ValueError("Threshold parameters require 'scores'")

        thresholds = [cls._parse_parameter_value(t) for t in thresholds_config]

        return ThresholdParameters(
            thresholds=thresholds, labels=labels, scores=[float(s) for s in scores]
        )

    @classmethod
    def _load_fallback_parameters(cls) -> PercentileParameters:
        """
        Load fallback parameters based on Story 2.4.1 literature-based values.

        These are used when:
        - Configuration file is missing
        - Validation dataset is insufficient
        - User explicitly requests fallback with use_fallback=True
        """
        # Check if fallback config exists
        if cls.FALLBACK_CONFIG_PATH.exists():
            try:
                return cls._load_from_file(cls.FALLBACK_CONFIG_PATH)
            except Exception as e:
                logger.warning(f"Failed to load fallback config: {e}")

        # Generate minimal fallback parameters programmatically
        logger.info("Generating minimal fallback parameters from defaults")

        params = PercentileParameters(
            version="1.0-fallback",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="none",
            metadata={"source": "fallback", "note": "Literature-based defaults from Story 2.4.1"},
        )

        # Add a few critical dimensions with literature-based parameters
        # These are examples - full set would come from validation dataset
        params.add_dimension(
            DimensionParameters(
                dimension_name="burstiness",
                scoring_type=ScoringType.GAUSSIAN,
                parameters=GaussianParameters(
                    target=ParameterValue(
                        10.2,
                        PercentileSource.LITERATURE,
                        description="Literature-based human median",
                    ),
                    width=ParameterValue(
                        2.3, PercentileSource.LITERATURE, description="Literature-based human stdev"
                    ),
                ),
                notes="Fallback parameters from GPTZero research",
            )
        )

        params.add_dimension(
            DimensionParameters(
                dimension_name="lexical",
                scoring_type=ScoringType.MONOTONIC,
                parameters=MonotonicParameters(
                    threshold_low=ParameterValue(
                        0.55, PercentileSource.LITERATURE, description="Literature-based p25 human"
                    ),
                    threshold_high=ParameterValue(
                        0.72, PercentileSource.LITERATURE, description="Literature-based p75 human"
                    ),
                    direction="increasing",
                ),
                notes="Fallback parameters from linguistic diversity research",
            )
        )

        logger.warning(
            "Using minimal fallback parameters. For production use, generate "
            "full parameter set from validation dataset."
        )

        return params

    @classmethod
    def save(cls, params: PercentileParameters, config_path: Optional[Path] = None) -> None:
        """
        Save parameters to YAML configuration file.

        Args:
            params: PercentileParameters to save
            config_path: Where to save (default: config/scoring_parameters.yaml)
        """
        if config_path is None:
            config_path = cls.DEFAULT_CONFIG_PATH

        # Validate before saving
        params.validate()

        # Convert to dict for YAML serialization
        config_data = cls._serialize_parameters(params)

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved parameters version {params.version} to {config_path}")

    @classmethod
    def _serialize_parameters(cls, params: PercentileParameters) -> Dict[str, Any]:
        """Convert PercentileParameters to dict for YAML serialization."""
        config_data: Dict[str, Any] = {
            "version": params.version,
            "timestamp": params.timestamp,
            "validation_dataset_version": params.validation_dataset_version,
            "metadata": params.metadata,
            "parameters": {},
        }

        for dim_name, dim_params in params.dimensions.items():
            dim_config: Dict[str, Any] = {
                "scoring_type": dim_params.scoring_type.value,
            }

            if dim_params.version:
                dim_config["version"] = dim_params.version
            if dim_params.notes:
                dim_config["notes"] = dim_params.notes

            # Serialize parameters based on type
            if isinstance(dim_params.parameters, GaussianParameters):
                dim_config["target"] = cls._serialize_parameter_value(dim_params.parameters.target)
                dim_config["width"] = cls._serialize_parameter_value(dim_params.parameters.width)
            elif isinstance(dim_params.parameters, MonotonicParameters):
                dim_config["threshold_low"] = cls._serialize_parameter_value(
                    dim_params.parameters.threshold_low
                )
                dim_config["threshold_high"] = cls._serialize_parameter_value(
                    dim_params.parameters.threshold_high
                )
                dim_config["direction"] = dim_params.parameters.direction
            elif isinstance(dim_params.parameters, ThresholdParameters):
                dim_config["thresholds"] = [
                    cls._serialize_parameter_value(t) for t in dim_params.parameters.thresholds
                ]
                dim_config["labels"] = dim_params.parameters.labels
                dim_config["scores"] = dim_params.parameters.scores

            config_data["parameters"][dim_name] = dim_config

        return config_data

    @classmethod
    def _serialize_parameter_value(cls, param_value: ParameterValue) -> Dict[str, Any]:
        """Convert ParameterValue to dict."""
        result = {"value": param_value.value, "source": param_value.source.value}

        if param_value.percentile:
            result["percentile"] = param_value.percentile
        if param_value.description:
            result["description"] = param_value.description

        return result
