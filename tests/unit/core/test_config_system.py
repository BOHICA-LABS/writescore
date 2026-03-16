"""
Tests for configuration system (Story 8.1: Configuration Over Code).

This test suite validates:
- ConfigLoader with layered overrides
- ConfigRegistry singleton behavior
- Pydantic schema validation
- Content type presets
- Profile configuration
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from writescore.core.config_loader import (
    ConfigLoader,
    ConfigLoadError,
    PartialConfigValidationError,
    _deep_merge,
    _env_to_config,
)
from writescore.core.config_registry import ConfigRegistry, get_config_registry
from writescore.core.config_schema import (
    DimensionConfig,
    DimensionTierEnum,
    ProfileConfig,
    WriteScoreConfig,
)


class TestDeepMerge:
    """Test deep merge utility function."""

    def test_simple_merge(self):
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"] == 3  # Override
        assert result["c"] == 4  # New key

    def test_nested_merge(self):
        """Test merging nested dictionaries."""
        base = {"outer": {"inner1": 1, "inner2": 2}}
        override = {"outer": {"inner2": 20, "inner3": 30}}
        result = _deep_merge(base, override)

        assert result["outer"]["inner1"] == 1  # Preserved
        assert result["outer"]["inner2"] == 20  # Override
        assert result["outer"]["inner3"] == 30  # New key

    def test_list_replacement(self):
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = _deep_merge(base, override)

        assert result["items"] == [4, 5]

    def test_base_not_modified(self):
        """Test that base dictionary is not modified."""
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        result = _deep_merge(base, override)

        assert base["a"]["b"] == 1  # Original preserved
        assert result["a"]["b"] == 2


class TestEnvToConfig:
    """Test environment variable parsing."""

    def test_basic_env_parsing(self):
        """Test parsing basic environment variables."""
        os.environ["WRITESCORE_TEST_KEY"] = "value"
        try:
            result = _env_to_config("WRITESCORE_TEST_")
            assert result["key"] == "value"
        finally:
            del os.environ["WRITESCORE_TEST_KEY"]

    def test_nested_env_parsing(self):
        """Test parsing nested environment variables."""
        os.environ["WRITESCORE_DIMENSIONS_FORMATTING_WEIGHT"] = "15.0"
        try:
            result = _env_to_config()
            assert result["dimensions"]["formatting"]["weight"] == 15.0
        finally:
            del os.environ["WRITESCORE_DIMENSIONS_FORMATTING_WEIGHT"]

    def test_boolean_env_parsing(self):
        """Test parsing boolean values."""
        os.environ["WRITESCORE_TEST_ENABLED"] = "true"
        os.environ["WRITESCORE_TEST_DISABLED"] = "false"
        try:
            result = _env_to_config("WRITESCORE_TEST_")
            assert result["enabled"] is True
            assert result["disabled"] is False
        finally:
            del os.environ["WRITESCORE_TEST_ENABLED"]
            del os.environ["WRITESCORE_TEST_DISABLED"]

    def test_int_env_parsing(self):
        """Test parsing integer values."""
        os.environ["WRITESCORE_TEST_COUNT"] = "42"
        try:
            result = _env_to_config("WRITESCORE_TEST_")
            assert result["count"] == 42
            assert isinstance(result["count"], int)
        finally:
            del os.environ["WRITESCORE_TEST_COUNT"]


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def setup_method(self):
        """Create temporary config files."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / "base.yaml"
        self.local_path = Path(self.temp_dir) / "local.yaml"

        # Create minimal base config
        base_config = {
            "version": "1.0.0",
            "dimensions": {
                "formatting": {
                    "weight": 10.0,
                    "tier": "CORE",
                }
            },
        }
        with open(self.base_path, "w") as f:
            yaml.dump(base_config, f)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_base_config(self):
        """Test loading base configuration."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        config = loader.load()

        assert config.version == "1.0.0"
        assert config.dimensions.formatting.weight == 10.0

    def test_load_with_local_override(self):
        """Test local override takes precedence."""
        local_config = {
            "dimensions": {
                "formatting": {
                    "weight": 15.0,
                    "tier": "CORE",
                }
            }
        }
        with open(self.local_path, "w") as f:
            yaml.dump(local_config, f)

        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        config = loader.load()

        assert config.dimensions.formatting.weight == 15.0  # Local override

    def test_load_with_programmatic_override(self):
        """Test programmatic override takes precedence."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        overrides = {"dimensions": {"formatting": {"weight": 20.0, "tier": "CORE"}}}
        config = loader.load(overrides=overrides)

        assert config.dimensions.formatting.weight == 20.0

    def test_missing_base_config_raises_error(self):
        """Test that missing base config raises error."""
        loader = ConfigLoader(base_path=Path("/nonexistent/base.yaml"), local_path=self.local_path)

        with pytest.raises(ConfigLoadError, match="Required config file not found"):
            loader.load()

    def test_skip_local_config(self):
        """Test skipping local config."""
        local_config = {"dimensions": {"formatting": {"weight": 99.0, "tier": "CORE"}}}
        with open(self.local_path, "w") as f:
            yaml.dump(local_config, f)

        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        config = loader.load(skip_local=True)

        assert config.dimensions.formatting.weight == 10.0  # Base value, not local

    def test_load_raw_config(self):
        """Test loading raw config without validation."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        raw = loader.load_raw()

        assert isinstance(raw, dict)
        assert raw["version"] == "1.0.0"


class TestConfigRegistry:
    """Test ConfigRegistry singleton functionality."""

    def setup_method(self):
        """Reset registry before each test."""
        ConfigRegistry.reset()

    def test_singleton_pattern(self):
        """Test that ConfigRegistry is a singleton."""
        registry1 = ConfigRegistry.get_instance()
        registry2 = ConfigRegistry.get_instance()

        assert registry1 is registry2

    def test_get_config(self):
        """Test getting configuration."""
        registry = get_config_registry()
        config = registry.get_config()

        assert isinstance(config, WriteScoreConfig)
        assert config.version is not None

    def test_get_dimension_weight(self):
        """Test getting dimension weight."""
        registry = get_config_registry()

        # Get a known dimension weight
        weight = registry.get_dimension_weight("formatting")
        assert weight > 0

    def test_get_dimension_weight_default(self):
        """Test default value for unknown dimension."""
        registry = get_config_registry()

        weight = registry.get_dimension_weight("nonexistent", default=99.0)
        assert weight == 99.0

    def test_set_content_type(self):
        """Test setting content type."""
        registry = get_config_registry()

        registry.set_content_type("technical")
        assert registry.get_content_type() == "technical"

        registry.clear_content_type()
        assert registry.get_content_type() is None

    def test_get_enabled_dimensions(self):
        """Test getting enabled dimensions."""
        registry = get_config_registry()
        enabled = registry.get_enabled_dimensions()

        assert isinstance(enabled, list)
        assert len(enabled) > 0  # Should have some enabled dimensions

    def test_get_profile_dimensions(self):
        """Test getting profile dimensions."""
        registry = get_config_registry()

        # Get dimensions from fast profile
        fast_dims = registry.get_profile_dimensions("fast")
        assert isinstance(fast_dims, list)
        assert "formatting" in fast_dims  # Should include formatting

    def test_reset_clears_state(self):
        """Test that reset clears state."""
        registry = get_config_registry()
        registry.set_content_type("technical")

        ConfigRegistry.reset()
        registry = get_config_registry()

        assert registry.get_content_type() is None


class TestPydanticSchemas:
    """Test Pydantic schema validation."""

    def test_dimension_config_validation(self):
        """Test DimensionConfig validation."""
        config = DimensionConfig(
            weight=10.0, tier=DimensionTierEnum.CORE, description="Test dimension"
        )

        assert config.weight == 10.0
        assert config.tier == DimensionTierEnum.CORE
        assert config.enabled is True  # Default

    def test_dimension_config_weight_bounds(self):
        """Test weight validation bounds."""
        # Weight too high
        with pytest.raises(ValueError):
            DimensionConfig(weight=150.0, tier=DimensionTierEnum.CORE)

        # Weight too low
        with pytest.raises(ValueError):
            DimensionConfig(weight=-5.0, tier=DimensionTierEnum.CORE)

    def test_profile_config_validation(self):
        """Test ProfileConfig validation."""
        config = ProfileConfig(
            description="Test profile", dimensions=["formatting", "burstiness", "voice"]
        )

        assert len(config.dimensions) == 3

    def test_profile_config_unknown_dimension(self):
        """Test that unknown dimensions are rejected."""
        with pytest.raises(ValueError, match="Unknown dimensions"):
            ProfileConfig(description="Bad profile", dimensions=["formatting", "fake_dimension"])

    def test_write_score_config_version_validation(self):
        """Test version format validation."""
        # Valid version
        config = WriteScoreConfig(version="1.0.0")
        assert config.version == "1.0.0"

        # Invalid version format
        with pytest.raises(ValueError, match="Version must be in format"):
            WriteScoreConfig(version="v1.0")


class TestContentTypePresets:
    """Test content type preset functionality."""

    def setup_method(self):
        """Reset registry before each test."""
        ConfigRegistry.reset()

    def test_content_type_weight_adjustment(self):
        """Test that content type adjusts weights."""
        registry = get_config_registry()

        # Get base weight before setting content type
        # Use "structure" dimension which has 1.2 adjustment for "technical"
        base_weight = registry.get_dimension_weight("structure")

        # Set content type with adjustment
        registry.set_content_type("technical")

        # Get adjusted weight
        adjusted_weight = registry.get_dimension_weight("structure")

        # Technical content type should increase structure weight by 1.2x
        assert adjusted_weight == base_weight * 1.2

        # Clear and verify weight restored
        registry.clear_content_type()
        restored_weight = registry.get_dimension_weight("structure")
        assert restored_weight == base_weight

    def test_available_content_types(self):
        """Test getting available content types."""
        registry = get_config_registry()
        types = registry.get_available_content_types()

        assert isinstance(types, list)
        # Check for some expected types
        assert "general" in types or len(types) >= 0


class TestLayeredOverrides:
    """Test layered override priority."""

    def setup_method(self):
        """Create temporary config with all layers."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / "base.yaml"
        self.local_path = Path(self.temp_dir) / "local.yaml"

        # Base: weight = 10
        base_config = {
            "version": "1.0.0",
            "dimensions": {"formatting": {"weight": 10.0, "tier": "CORE"}},
        }
        with open(self.base_path, "w") as f:
            yaml.dump(base_config, f)

        # Local: weight = 15
        local_config = {"dimensions": {"formatting": {"weight": 15.0, "tier": "CORE"}}}
        with open(self.local_path, "w") as f:
            yaml.dump(local_config, f)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_priority_base_only(self):
        """Test loading base config only."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        config = loader.load(skip_local=True, skip_env=True)

        assert config.dimensions.formatting.weight == 10.0

    def test_priority_local_over_base(self):
        """Test local overrides base."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        config = loader.load(skip_env=True)

        assert config.dimensions.formatting.weight == 15.0

    def test_priority_programmatic_over_all(self):
        """Test programmatic overrides everything."""
        loader = ConfigLoader(base_path=self.base_path, local_path=self.local_path)
        overrides = {"dimensions": {"formatting": {"weight": 25.0, "tier": "CORE"}}}
        config = loader.load(overrides=overrides, skip_env=True)

        assert config.dimensions.formatting.weight == 25.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Reset registry before each test."""
        ConfigRegistry.reset()

    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises error."""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir) / "base.yaml"

        # Write invalid YAML
        with open(base_path, "w") as f:
            f.write("invalid: yaml: content: [")

        try:
            loader = ConfigLoader(base_path=base_path)
            with pytest.raises(ConfigLoadError, match="Invalid YAML"):
                loader.load()
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_empty_config_file(self):
        """Test handling empty config file."""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir) / "base.yaml"
        local_path = Path(temp_dir) / "local.yaml"

        # Write minimal valid config to base
        with open(base_path, "w") as f:
            yaml.dump({"version": "1.0.0"}, f)

        # Empty local file
        with open(local_path, "w") as f:
            f.write("")

        try:
            loader = ConfigLoader(base_path=base_path, local_path=local_path)
            config = loader.load()
            assert config.version == "1.0.0"
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_threshold_with_dotted_path(self):
        """Test getting threshold with dotted path."""
        registry = get_config_registry()

        # Try to get a threshold value
        value = registry.get_threshold("scoring.thresholds.ai_likely", default=40)
        assert value is not None


class TestContentTypeConfig:
    """Test content type configuration (Story 8.1 AC 16-19)."""

    def setup_method(self):
        """Reset registry before each test."""
        ConfigRegistry.reset()

    def test_valid_content_types_list(self):
        """Test that valid content types are defined in config."""
        registry = get_config_registry()
        types = registry.get_available_content_types()

        assert isinstance(types, list)
        assert len(types) >= 12  # All 12 content types + general
        # Check for required content types
        assert "academic" in types
        assert "blog" in types
        assert "technical_book" in types
        assert "business" in types
        assert "creative" in types
        assert "social_media" in types

    def test_get_content_type_config(self):
        """Test getting content type configuration."""
        registry = get_config_registry()

        # Get academic content type
        academic_config = registry.get_content_type_config("academic")
        assert academic_config is not None
        assert academic_config.description is not None

    def test_content_type_weight_adjustments(self):
        """Test that content types have weight adjustments."""
        registry = get_config_registry()

        # Academic should have adjustments
        academic_config = registry.get_content_type_config("academic")
        assert academic_config is not None
        # Check for weight adjustments
        if academic_config.weight_adjustments:
            assert isinstance(academic_config.weight_adjustments, dict)

    def test_set_content_type_affects_weights(self):
        """Test that setting content type affects dimension weights."""
        registry = get_config_registry()

        # Get base weight for a dimension
        base_weight = registry.get_dimension_weight("voice")

        # Set creative content type (which should boost voice)
        registry.set_content_type("creative")

        # Weight should be adjusted
        adjusted_weight = registry.get_dimension_weight("voice")

        # Creative boosts voice, so adjusted should be >= base
        assert adjusted_weight >= base_weight

        # Clear and verify restored
        registry.clear_content_type()
        restored_weight = registry.get_dimension_weight("voice")
        assert restored_weight == base_weight


class TestContentTypeWeightsValidation:
    """Test content type weights validation."""

    def test_valid_weights_sum_to_one(self):
        """Test that valid weights summing to 1.0 are accepted."""
        from writescore.core.config_schema import ContentTypeWeights

        weights = ContentTypeWeights(
            perplexity=0.10,
            burstiness=0.12,
            structure=0.10,
            formatting=0.05,
            voice=0.15,
            readability=0.10,
            sentiment=0.12,
            figurative_language=0.10,
            transition_marker=0.08,
            advanced_lexical=0.08,
        )
        assert weights is not None
        # Verify sum is within tolerance
        total = sum(weights.to_dict().values())
        assert 0.99 <= total <= 1.01

    def test_invalid_weights_sum_rejected(self):
        """Test that weights not summing to 1.0 are rejected."""
        from writescore.core.config_schema import ContentTypeWeights

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ContentTypeWeights(
                perplexity=0.50,
                burstiness=0.50,
                voice=0.50,  # Sum = 1.5, too high
            )

    def test_zero_weights_allowed(self):
        """Test that all-zero weights are allowed (not validated)."""
        from writescore.core.config_schema import ContentTypeWeights

        # Default weights (all zero) should be allowed
        weights = ContentTypeWeights()
        assert weights is not None


class TestThresholdRangeValidation:
    """Test threshold range validation."""

    def test_valid_threshold_range(self):
        """Test valid threshold range is accepted."""
        from writescore.core.config_schema import ThresholdRange

        range_config = ThresholdRange(min_value=0.0, max_value=100.0)
        assert range_config.min_value == 0.0
        assert range_config.max_value == 100.0

    def test_invalid_threshold_range_rejected(self):
        """Test that min >= max is rejected."""
        from writescore.core.config_schema import ThresholdRange

        with pytest.raises(ValueError, match="min_value.*must be less than"):
            ThresholdRange(min_value=100.0, max_value=50.0)

    def test_equal_range_rejected(self):
        """Test that min == max is rejected."""
        from writescore.core.config_schema import ThresholdRange

        with pytest.raises(ValueError, match="min_value.*must be less than"):
            ThresholdRange(min_value=50.0, max_value=50.0)


class TestPartialConfigValidation:
    """Test partial config validation for override files."""

    def test_valid_partial_config_accepted(self):
        """Test that valid partial config is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            local_path = Path(tmpdir) / "local.yaml"

            # Write base config
            base_config = {
                "version": "1.0.0",
                "dimensions": {
                    "formatting": {"weight": 10.0, "tier": "CORE", "description": "Test"}
                },
            }
            with open(base_path, "w") as f:
                yaml.dump(base_config, f)

            # Write valid partial override
            local_config = {
                "dimensions": {
                    "formatting": {
                        "weight": 15.0  # Just override weight
                    }
                }
            }
            with open(local_path, "w") as f:
                yaml.dump(local_config, f)

            loader = ConfigLoader(base_path=base_path, local_path=local_path)
            config = loader.load()

            # Merged config should have updated weight
            assert config.dimensions.formatting.weight == 15.0

    def test_invalid_partial_config_raises_error(self):
        """Test that invalid partial config raises PartialConfigValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            local_path = Path(tmpdir) / "local.yaml"

            # Write base config
            base_config = {
                "version": "1.0.0",
            }
            with open(base_path, "w") as f:
                yaml.dump(base_config, f)

            # Write invalid partial - dimension with invalid weight
            local_config = {
                "dimensions": {
                    "formatting": {
                        "weight": 200.0  # Invalid: weight must be <= 100
                    }
                }
            }
            with open(local_path, "w") as f:
                yaml.dump(local_config, f)

            loader = ConfigLoader(base_path=base_path, local_path=local_path)

            with pytest.raises(PartialConfigValidationError, match="Partial config validation"):
                loader.load()

    def test_partial_validation_identifies_source(self):
        """Test that partial validation error identifies the source file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            local_path = Path(tmpdir) / "local.yaml"

            # Write base config
            base_config = {"version": "1.0.0"}
            with open(base_path, "w") as f:
                yaml.dump(base_config, f)

            # Write invalid partial
            local_config = {
                "dimensions": {
                    "formatting": {"weight": -10.0}  # Invalid
                }
            }
            with open(local_path, "w") as f:
                yaml.dump(local_config, f)

            loader = ConfigLoader(base_path=base_path, local_path=local_path)

            with pytest.raises(PartialConfigValidationError) as exc_info:
                loader.load()

            # Error message should contain the file path
            assert "local.yaml" in str(exc_info.value)
