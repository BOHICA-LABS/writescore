"""
Unit tests for percentile-anchored parameter infrastructure.

Tests Story 2.5 Task 1: PercentileParameters class and ParameterLoader.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from writescore.core.parameters import (
    PercentileParameters,
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    ThresholdParameters,
    ParameterValue,
    ScoringType,
    PercentileSource
)
from writescore.core.parameter_loader import ParameterLoader
from writescore.core.exceptions import ParameterLoadError


class TestParameterValue:
    """Test ParameterValue dataclass."""

    def test_valid_percentile_parameter(self):
        """Test creating a valid percentile-based parameter."""
        param = ParameterValue(
            value=10.5,
            source=PercentileSource.PERCENTILE,
            percentile="p50_human",
            description="Median of human distribution"
        )
        param.validate()
        assert param.value == 10.5
        assert param.source == PercentileSource.PERCENTILE
        assert param.percentile == "p50_human"

    def test_valid_stdev_parameter(self):
        """Test creating a valid stdev-based parameter."""
        param = ParameterValue(
            value=2.3,
            source=PercentileSource.STDEV,
            description="Standard deviation"
        )
        param.validate()
        assert param.value == 2.3
        assert param.source == PercentileSource.STDEV

    def test_percentile_source_requires_percentile(self):
        """Test that PERCENTILE source requires percentile attribute."""
        param = ParameterValue(
            value=10.0,
            source=PercentileSource.PERCENTILE
            # Missing percentile attribute
        )
        with pytest.raises(ValueError, match="Percentile source requires percentile"):
            param.validate()

    def test_invalid_value_type(self):
        """Test that non-numeric values are rejected."""
        param = ParameterValue(
            value="not_a_number",
            source=PercentileSource.LITERATURE
        )
        with pytest.raises(ValueError, match="must be numeric"):
            param.validate()


class TestGaussianParameters:
    """Test GaussianParameters dataclass."""

    def test_valid_gaussian_parameters(self):
        """Test creating valid Gaussian parameters."""
        params = GaussianParameters(
            target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
            width=ParameterValue(2.0, PercentileSource.STDEV)
        )
        params.validate()
        assert params.target.value == 10.0
        assert params.width.value == 2.0

    def test_zero_width_rejected(self):
        """Test that width must be > 0."""
        params = GaussianParameters(
            target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
            width=ParameterValue(0.0, PercentileSource.STDEV)
        )
        with pytest.raises(ValueError, match="width must be > 0"):
            params.validate()

    def test_negative_width_rejected(self):
        """Test that negative width is rejected."""
        params = GaussianParameters(
            target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
            width=ParameterValue(-1.0, PercentileSource.STDEV)
        )
        with pytest.raises(ValueError, match="width must be > 0"):
            params.validate()


class TestMonotonicParameters:
    """Test MonotonicParameters dataclass."""

    def test_valid_monotonic_parameters(self):
        """Test creating valid monotonic parameters."""
        params = MonotonicParameters(
            threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human"),
            threshold_high=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human"),
            direction="increasing"
        )
        params.validate()
        assert params.threshold_low.value == 0.5
        assert params.threshold_high.value == 0.8
        assert params.direction == "increasing"

    def test_reversed_thresholds_rejected(self):
        """Test that threshold_low must be < threshold_high."""
        params = MonotonicParameters(
            threshold_low=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human"),
            threshold_high=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human")
        )
        with pytest.raises(ValueError, match="threshold_low .* must be <"):
            params.validate()

    def test_equal_thresholds_rejected(self):
        """Test that thresholds cannot be equal."""
        params = MonotonicParameters(
            threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p50_human"),
            threshold_high=ParameterValue(0.5, PercentileSource.PERCENTILE, "p50_human")
        )
        with pytest.raises(ValueError, match="threshold_low .* must be <"):
            params.validate()

    def test_invalid_direction_rejected(self):
        """Test that invalid direction is rejected."""
        params = MonotonicParameters(
            threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human"),
            threshold_high=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human"),
            direction="sideways"  # Invalid
        )
        with pytest.raises(ValueError, match="Direction must be"):
            params.validate()


class TestThresholdParameters:
    """Test ThresholdParameters dataclass."""

    def test_valid_threshold_parameters(self):
        """Test creating valid threshold parameters."""
        params = ThresholdParameters(
            thresholds=[
                ParameterValue(2.0, PercentileSource.PERCENTILE, "p25_ai"),
                ParameterValue(5.0, PercentileSource.PERCENTILE, "p50_combined"),
                ParameterValue(8.0, PercentileSource.PERCENTILE, "p75_human")
            ],
            labels=["excellent", "good", "concerning", "poor"],
            scores=[100.0, 75.0, 40.0, 10.0]
        )
        params.validate()
        assert len(params.thresholds) == 3
        assert len(params.labels) == 4
        assert len(params.scores) == 4

    def test_unordered_thresholds_rejected(self):
        """Test that thresholds must be in ascending order."""
        params = ThresholdParameters(
            thresholds=[
                ParameterValue(8.0, PercentileSource.PERCENTILE, "p75_human"),
                ParameterValue(5.0, PercentileSource.PERCENTILE, "p50_combined"),
                ParameterValue(2.0, PercentileSource.PERCENTILE, "p25_ai")
            ],
            labels=["excellent", "good", "concerning", "poor"],
            scores=[100.0, 75.0, 40.0, 10.0]
        )
        with pytest.raises(ValueError, match="must be in ascending order"):
            params.validate()

    def test_mismatched_labels_scores(self):
        """Test that labels and scores must have same length."""
        params = ThresholdParameters(
            thresholds=[
                ParameterValue(2.0, PercentileSource.PERCENTILE, "p25_ai"),
                ParameterValue(5.0, PercentileSource.PERCENTILE, "p50_combined")
            ],
            labels=["excellent", "good", "concerning"],
            scores=[100.0, 75.0]  # Only 2 scores for 3 labels
        )
        with pytest.raises(ValueError, match="must have same length"):
            params.validate()

    def test_incorrect_category_count(self):
        """Test that N thresholds require N+1 categories."""
        params = ThresholdParameters(
            thresholds=[
                ParameterValue(2.0, PercentileSource.PERCENTILE, "p25_ai"),
                ParameterValue(5.0, PercentileSource.PERCENTILE, "p50_combined")
            ],
            labels=["excellent", "good"],  # Should be 3 labels for 2 thresholds
            scores=[100.0, 75.0]
        )
        with pytest.raises(ValueError, match="Expected .* categories"):
            params.validate()

    def test_score_out_of_range(self):
        """Test that scores must be in [0, 100] range."""
        params = ThresholdParameters(
            thresholds=[
                ParameterValue(2.0, PercentileSource.PERCENTILE, "p25_ai")
            ],
            labels=["excellent", "poor"],
            scores=[150.0, 10.0]  # 150 is out of range
        )
        with pytest.raises(ValueError, match="must be in range"):
            params.validate()


class TestDimensionParameters:
    """Test DimensionParameters dataclass."""

    def test_gaussian_dimension_parameters(self):
        """Test creating Gaussian dimension parameters."""
        params = DimensionParameters(
            dimension_name="burstiness",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            ),
            version="1.0"
        )
        params.validate()
        assert params.dimension_name == "burstiness"
        assert params.scoring_type == ScoringType.GAUSSIAN

    def test_type_mismatch_rejected(self):
        """Test that parameter type must match scoring type."""
        params = DimensionParameters(
            dimension_name="test",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=MonotonicParameters(  # Wrong type
                threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human"),
                threshold_high=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human")
            )
        )
        with pytest.raises(ValueError, match="Gaussian scoring requires GaussianParameters"):
            params.validate()


class TestPercentileParameters:
    """Test PercentileParameters container."""

    def test_create_empty_parameters(self):
        """Test creating empty parameter set."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v1.0"
        )
        assert params.version == "1.0"
        assert len(params.dimensions) == 0

    def test_add_dimension(self):
        """Test adding a dimension to parameters."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v1.0"
        )

        dim_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            )
        )

        params.add_dimension(dim_params)
        assert len(params.dimensions) == 1
        assert "burstiness" in params.dimensions

    def test_get_dimension(self):
        """Test retrieving dimension parameters."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v1.0"
        )

        dim_params = DimensionParameters(
            dimension_name="test_dim",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(5.0, PercentileSource.LITERATURE),
                width=ParameterValue(1.0, PercentileSource.LITERATURE)
            )
        )

        params.add_dimension(dim_params)

        retrieved = params.get_dimension("test_dim")
        assert retrieved is not None
        assert retrieved.dimension_name == "test_dim"

        missing = params.get_dimension("nonexistent")
        assert missing is None

    def test_validate_all_dimensions(self):
        """Test validation of all dimensions."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v1.0"
        )

        # Add valid dimension
        params.add_dimension(DimensionParameters(
            dimension_name="valid",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.LITERATURE),
                width=ParameterValue(2.0, PercentileSource.LITERATURE)
            )
        ))

        # Should validate successfully
        params.validate()

    def test_get_summary(self):
        """Test getting summary statistics."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v1.0",
            metadata={"trigger": "initial"}
        )

        params.add_dimension(DimensionParameters(
            dimension_name="gaussian_dim",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            )
        ))

        params.add_dimension(DimensionParameters(
            dimension_name="monotonic_dim",
            scoring_type=ScoringType.MONOTONIC,
            parameters=MonotonicParameters(
                threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human"),
                threshold_high=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human")
            )
        ))

        summary = params.get_summary()
        assert summary['version'] == "1.0"
        assert summary['total_dimensions'] == 2
        assert summary['scoring_types']['gaussian'] == 1
        assert summary['scoring_types']['monotonic'] == 1
        assert summary['parameter_sources']['percentile'] == 3  # target + 2 thresholds
        assert summary['parameter_sources']['stdev'] == 1


class TestParameterLoader:
    """Test ParameterLoader class."""

    def test_load_fallback_parameters(self):
        """Test loading fallback parameters."""
        params = ParameterLoader.load(use_fallback=True)
        assert params is not None
        assert params.version.endswith('-fallback')
        assert len(params.dimensions) >= 2  # burstiness and lexical

    def test_load_missing_file_uses_fallback(self):
        """Test that missing config file falls back to defaults."""
        params = ParameterLoader.load(config_path=Path("/nonexistent/path.yaml"))
        assert params is not None
        assert params.version.endswith('-fallback')

    def test_save_and_load_roundtrip(self):
        """Test saving and loading parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"

            # Create test parameters
            original = PercentileParameters(
                version="1.0-test",
                timestamp=datetime.now().isoformat(),
                validation_dataset_version="v1.0"
            )

            original.add_dimension(DimensionParameters(
                dimension_name="test_dim",
                scoring_type=ScoringType.GAUSSIAN,
                parameters=GaussianParameters(
                    target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                    width=ParameterValue(2.0, PercentileSource.STDEV)
                )
            ))

            # Save
            ParameterLoader.save(original, config_path)
            assert config_path.exists()

            # Load
            loaded = ParameterLoader.load(config_path)
            assert loaded.version == original.version
            assert len(loaded.dimensions) == len(original.dimensions)
            assert "test_dim" in loaded.dimensions

            # Verify parameter values preserved
            loaded_dim = loaded.get_dimension("test_dim")
            assert loaded_dim.scoring_type == ScoringType.GAUSSIAN
            assert loaded_dim.parameters.target.value == 10.0
            assert loaded_dim.parameters.width.value == 2.0

    def test_load_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises ParameterLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.yaml"

            # Write invalid YAML
            with open(config_path, 'w') as f:
                f.write("{ invalid yaml content [")

            with pytest.raises(ParameterLoadError):
                ParameterLoader.load(config_path)

    def test_load_missing_required_fields_raises_error(self):
        """Test that missing required fields raise ParameterLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "incomplete.yaml"

            # Write incomplete config
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump({'version': '1.0'}, f)  # Missing timestamp, validation_dataset_version

            with pytest.raises(ParameterLoadError, match="must include"):
                ParameterLoader.load(config_path)
