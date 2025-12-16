"""
Pydantic schemas for WriteScore configuration validation.

Provides type-safe configuration models with validation for:
- Dimension configurations (weights, thresholds, tiers)
- Scoring thresholds and calibration
- Analysis modes and profiles
- Content type presets

Story 8.1: Configuration Over Code
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class DimensionTierEnum(str, Enum):
    """Dimension tier classification."""

    ADVANCED = "ADVANCED"
    CORE = "CORE"
    SUPPORTING = "SUPPORTING"
    STRUCTURAL = "STRUCTURAL"


class AnalysisModeEnum(str, Enum):
    """Analysis mode options."""

    FAST = "fast"
    ADAPTIVE = "adaptive"
    SAMPLING = "sampling"
    FULL = "full"


# ==============================================================================
# Dimension Configuration Schemas
# ==============================================================================


class DimensionThresholds(BaseModel):
    """Generic threshold configuration for a dimension."""

    model_config = {"extra": "allow"}

    # Allow any threshold key with numeric values
    # Individual dimensions can define their specific thresholds


class DimensionScoring(BaseModel):
    """Scoring parameters for a dimension."""

    model_config = {"extra": "allow"}

    # Common scoring parameters
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    target: Optional[float] = None
    target_grade: Optional[float] = None
    target_width: Optional[float] = None
    direction: Optional[str] = None


class DimensionOptimization(BaseModel):
    """Performance optimization settings."""

    model_config = {"extra": "allow"}

    max_sentences_before_sampling: Optional[int] = None
    sample_size: Optional[int] = None
    batch_size: Optional[int] = None


class DimensionConfig(BaseModel):
    """Configuration for a single dimension."""

    model_config = {"extra": "forbid"}

    weight: float = Field(ge=0, le=100, description="Percentage weight (0-100)")
    tier: DimensionTierEnum = Field(description="Dimension tier classification")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    enabled: bool = Field(default=True, description="Whether dimension is enabled")
    thresholds: Optional[Dict[str, Union[float, int]]] = Field(
        default=None, description="Dimension-specific thresholds"
    )
    scoring: Optional[DimensionScoring] = Field(default=None, description="Scoring parameters")
    tier_weights: Optional[Dict[str, float]] = Field(default=None, description="Sub-tier weights")
    composite_weights: Optional[Dict[str, float]] = Field(
        default=None, description="Composite scoring weights"
    )
    optimization: Optional[DimensionOptimization] = Field(
        default=None, description="Performance optimization settings"
    )
    timeout_seconds: Optional[int] = Field(
        default=None, ge=1, description="Timeout for dimension analysis"
    )
    model: Optional[str] = Field(default=None, description="Model name for ML-based dimensions")

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Validate weight is a reasonable percentage."""
        if v < 0 or v > 100:
            raise ValueError(f"Weight must be between 0 and 100, got {v}")
        return v


class DimensionsConfig(BaseModel):
    """Container for all dimension configurations."""

    model_config = {"extra": "allow"}

    # Known dimensions with their configs
    # Using Optional to allow partial configs in overrides
    perplexity: Optional[DimensionConfig] = None
    burstiness: Optional[DimensionConfig] = None
    formatting: Optional[DimensionConfig] = None
    voice: Optional[DimensionConfig] = None
    structure: Optional[DimensionConfig] = None
    lexical: Optional[DimensionConfig] = None
    sentiment: Optional[DimensionConfig] = None
    readability: Optional[DimensionConfig] = None
    syntactic: Optional[DimensionConfig] = None
    predictability: Optional[DimensionConfig] = None
    ai_vocabulary: Optional[DimensionConfig] = None
    semantic_coherence: Optional[DimensionConfig] = None
    energy: Optional[DimensionConfig] = None
    figurative_language: Optional[DimensionConfig] = None
    pragmatic_markers: Optional[DimensionConfig] = None
    transition_marker: Optional[DimensionConfig] = None
    advanced_lexical: Optional[DimensionConfig] = None

    def get_all_dimensions(self) -> Dict[str, DimensionConfig]:
        """Get all configured dimensions as a dictionary."""
        result = {}
        for name in [
            "perplexity",
            "burstiness",
            "formatting",
            "voice",
            "structure",
            "lexical",
            "sentiment",
            "readability",
            "syntactic",
            "predictability",
            "ai_vocabulary",
            "semantic_coherence",
            "energy",
            "figurative_language",
            "pragmatic_markers",
            "transition_marker",
            "advanced_lexical",
        ]:
            config = getattr(self, name, None)
            if config is not None:
                result[name] = config
        return result

    def get_dimension(self, name: str) -> Optional[DimensionConfig]:
        """Get a specific dimension config by name."""
        return getattr(self, name, None)


# ==============================================================================
# Scoring Configuration Schemas
# ==============================================================================


class ScoringThresholdsConfig(BaseModel):
    """Scoring threshold configuration."""

    model_config = {"extra": "allow"}

    # AI Likelihood thresholds
    ai_very_likely: float = Field(default=25, description="Score threshold for 'AI Very Likely'")
    ai_likely: float = Field(default=40, description="Score threshold for 'AI Likely'")
    ai_possibly: float = Field(default=55, description="Score threshold for 'AI Possibly'")
    mixed_content: float = Field(default=70, description="Score threshold for 'Mixed Content'")
    human_likely: float = Field(default=85, description="Score threshold for 'Human Likely'")

    # Quality thresholds
    quality_excellent: float = Field(default=85, description="Score threshold for 'Excellent'")
    quality_good: float = Field(default=70, description="Score threshold for 'Good'")
    quality_acceptable: float = Field(default=55, description="Score threshold for 'Acceptable'")
    quality_poor: float = Field(default=40, description="Score threshold for 'Poor'")

    # Dimension-specific thresholds (from ScoringThresholds dataclass)
    heading_parallelism_high: float = Field(default=0.8)
    heading_parallelism_medium: float = Field(default=0.6)
    heading_verbose_ratio: float = Field(default=0.3)
    sentence_stdev_low: float = Field(default=3.0)


class ScoringCalibrationConfig(BaseModel):
    """Calibration weights for scoring."""

    model_config = {"extra": "allow"}

    ai_detection_weight: float = Field(
        default=0.6, ge=0, le=1, description="Weight for AI detection score"
    )
    quality_weight: float = Field(default=0.4, ge=0, le=1, description="Weight for quality score")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ScoringCalibrationConfig":
        """Validate that weights sum to 1.0."""
        total = self.ai_detection_weight + self.quality_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Calibration weights must sum to 1.0, got {total}")
        return self


class ScoringConfig(BaseModel):
    """Complete scoring configuration."""

    model_config = {"extra": "forbid"}

    thresholds: ScoringThresholdsConfig = Field(default_factory=ScoringThresholdsConfig)
    calibration: ScoringCalibrationConfig = Field(default_factory=ScoringCalibrationConfig)


# ==============================================================================
# Analysis Configuration Schemas
# ==============================================================================


class AnalysisModeConfig(BaseModel):
    """Configuration for a single analysis mode."""

    model_config = {"extra": "forbid"}

    description: Optional[str] = None
    max_chars: Optional[int] = Field(default=None, ge=100)
    sampling_threshold: Optional[int] = Field(default=None, ge=1000)
    sections: Optional[int] = Field(default=None, ge=1)


class AnalysisModesConfig(BaseModel):
    """Container for all analysis mode configurations."""

    model_config = {"extra": "forbid"}

    fast: Optional[AnalysisModeConfig] = None
    adaptive: Optional[AnalysisModeConfig] = None
    sampling: Optional[AnalysisModeConfig] = None
    full: Optional[AnalysisModeConfig] = None


class AnalysisDefaultsConfig(BaseModel):
    """Default analysis settings."""

    model_config = {"extra": "forbid"}

    mode: AnalysisModeEnum = Field(
        default=AnalysisModeEnum.ADAPTIVE, description="Default analysis mode"
    )
    sampling_sections: int = Field(
        default=5, ge=1, description="Default number of sections for sampling"
    )


class AnalysisConfig(BaseModel):
    """Complete analysis configuration."""

    model_config = {"extra": "forbid"}

    modes: Optional[AnalysisModesConfig] = Field(default=None)
    defaults: AnalysisDefaultsConfig = Field(default_factory=AnalysisDefaultsConfig)


# ==============================================================================
# Profile Configuration Schemas
# ==============================================================================


class ProfileConfig(BaseModel):
    """Configuration for a dimension profile."""

    model_config = {"extra": "forbid"}

    description: Optional[str] = Field(default=None, description="Profile description")
    dimensions: List[str] = Field(description="List of dimension names to include")

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: List[str]) -> List[str]:
        """Validate dimension names are known."""
        known_dimensions = {
            "perplexity",
            "burstiness",
            "formatting",
            "voice",
            "structure",
            "lexical",
            "sentiment",
            "readability",
            "syntactic",
            "predictability",
            "ai_vocabulary",
            "semantic_coherence",
            "energy",
            "figurative_language",
            "pragmatic_markers",
            "transition_marker",
            "advanced_lexical",
        }
        unknown = set(v) - known_dimensions
        if unknown:
            raise ValueError(f"Unknown dimensions: {unknown}")
        return v


class ProfilesConfig(BaseModel):
    """Container for all profile configurations."""

    model_config = {"extra": "allow"}

    all: Optional[ProfileConfig] = None
    fast: Optional[ProfileConfig] = None
    balanced: Optional[ProfileConfig] = None
    advanced: Optional[ProfileConfig] = None

    def get_profile(self, name: str) -> Optional[ProfileConfig]:
        """Get a profile by name."""
        return getattr(self, name, None)


# ==============================================================================
# Content Type Configuration Schemas
# ==============================================================================


# Valid content types (Story 8.1 AC 16)
VALID_CONTENT_TYPES = [
    "academic",
    "professional_bio",
    "personal_statement",
    "blog",
    "technical_docs",
    "technical_book",
    "business",
    "creative",
    "creative_fiction",
    "news",
    "marketing",
    "social_media",
    "general",
]


class ContentTypeWeights(BaseModel):
    """Dimension weights for a content type (must sum to 1.0 ± 0.01)."""

    model_config = {"extra": "forbid"}

    # All possible dimensions with optional weights
    perplexity: float = Field(default=0.0, ge=0.0, le=1.0)
    burstiness: float = Field(default=0.0, ge=0.0, le=1.0)
    structure: float = Field(default=0.0, ge=0.0, le=1.0)
    formatting: float = Field(default=0.0, ge=0.0, le=1.0)
    voice: float = Field(default=0.0, ge=0.0, le=1.0)
    readability: float = Field(default=0.0, ge=0.0, le=1.0)
    lexical: float = Field(default=0.0, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.0, ge=0.0, le=1.0)
    syntactic: float = Field(default=0.0, ge=0.0, le=1.0)
    predictability: float = Field(default=0.0, ge=0.0, le=1.0)
    advanced_lexical: float = Field(default=0.0, ge=0.0, le=1.0)
    transition_marker: float = Field(default=0.0, ge=0.0, le=1.0)
    pragmatic_markers: float = Field(default=0.0, ge=0.0, le=1.0)
    figurative_language: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    ai_vocabulary: float = Field(default=0.0, ge=0.0, le=1.0)
    energy: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ContentTypeWeights":
        """Validate that weights sum to 1.0 ± 0.01."""
        total = sum(
            [
                self.perplexity,
                self.burstiness,
                self.structure,
                self.formatting,
                self.voice,
                self.readability,
                self.lexical,
                self.sentiment,
                self.syntactic,
                self.predictability,
                self.advanced_lexical,
                self.transition_marker,
                self.pragmatic_markers,
                self.figurative_language,
                self.semantic_coherence,
                self.ai_vocabulary,
                self.energy,
            ]
        )
        # Only validate if weights are actually set (non-zero total)
        if total > 0.0 and not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0 ± 0.01, got {total:.3f}")
        return self

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary of non-zero weights."""
        return {k: v for k, v in self.model_dump().items() if v > 0}


class ThresholdRange(BaseModel):
    """A threshold range with min and max values."""

    model_config = {"extra": "forbid"}

    min_value: float = Field(description="Minimum value for this range")
    max_value: float = Field(description="Maximum value for this range")

    @model_validator(mode="after")
    def validate_range(self) -> "ThresholdRange":
        """Validate min < max."""
        if self.min_value >= self.max_value:
            raise ValueError(
                f"min_value ({self.min_value}) must be less than " f"max_value ({self.max_value})"
            )
        return self


class ContentTypeThresholds(BaseModel):
    """Threshold ranges for a content type's scoring assessments."""

    model_config = {"extra": "allow"}

    # Each metric can have threshold ranges for different assessment levels
    readability: Optional[Dict[str, Dict[str, List[float]]]] = None
    sentiment: Optional[Dict[str, Dict[str, List[float]]]] = None
    burstiness: Optional[Dict[str, Dict[str, List[float]]]] = None
    # Additional metrics can be added as needed


class ContentTypeConfig(BaseModel):
    """Configuration for a content type preset."""

    model_config = {"extra": "forbid"}

    description: Optional[str] = Field(default=None, description="Content type description")
    weight_adjustments: Dict[str, float] = Field(
        default_factory=dict, description="Multipliers for dimension weights"
    )
    threshold_adjustments: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Override threshold values"
    )
    weights: Optional[ContentTypeWeights] = Field(
        default=None, description="Dimension weights for this content type"
    )
    thresholds: Optional[ContentTypeThresholds] = Field(
        default=None, description="Threshold configurations for this content type"
    )

    @field_validator("weight_adjustments")
    @classmethod
    def validate_weight_adjustments(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate weight adjustment values are positive."""
        for key, value in v.items():
            if value < 0:
                raise ValueError(f"Weight adjustment for {key} must be non-negative, got {value}")
        return v


class ContentTypesConfig(BaseModel):
    """Container for content type configurations."""

    model_config = {"extra": "allow"}

    # Valid content types list (Story 8.1 AC 16)
    types: List[str] = Field(default=VALID_CONTENT_TYPES, description="List of valid content types")

    # All 12 content types from Story 8.1 + general
    general: Optional[ContentTypeConfig] = None
    academic: Optional[ContentTypeConfig] = None
    professional_bio: Optional[ContentTypeConfig] = None
    personal_statement: Optional[ContentTypeConfig] = None
    blog: Optional[ContentTypeConfig] = None
    technical_docs: Optional[ContentTypeConfig] = None
    technical_book: Optional[ContentTypeConfig] = None
    business: Optional[ContentTypeConfig] = None
    creative: Optional[ContentTypeConfig] = None
    creative_fiction: Optional[ContentTypeConfig] = None
    news: Optional[ContentTypeConfig] = None
    marketing: Optional[ContentTypeConfig] = None
    social_media: Optional[ContentTypeConfig] = None

    # Legacy field for backwards compatibility
    technical: Optional[ContentTypeConfig] = None

    @field_validator("types")
    @classmethod
    def validate_types(cls, v: List[str]) -> List[str]:
        """Validate content types list."""
        invalid = [t for t in v if t not in VALID_CONTENT_TYPES]
        if invalid:
            raise ValueError(f"Invalid content types: {invalid}")
        return v

    def get_content_type(self, name: str) -> Optional[ContentTypeConfig]:
        """Get a content type by name."""
        return getattr(self, name, None)

    def get_weights(self, name: str) -> Optional[Dict[str, float]]:
        """Get dimension weights for a content type."""
        content_type = self.get_content_type(name)
        if content_type and content_type.weights:
            return content_type.weights.to_dict()
        return None

    def get_thresholds(self, name: str) -> Optional[ContentTypeThresholds]:
        """Get thresholds for a content type."""
        content_type = self.get_content_type(name)
        if content_type:
            return content_type.thresholds
        return None


# ==============================================================================
# Root Configuration Schema
# ==============================================================================


class WriteScoreConfig(BaseModel):
    """Root configuration schema for WriteScore."""

    model_config = {"extra": "forbid"}

    version: str = Field(description="Configuration schema version")
    dimensions: Optional[DimensionsConfig] = Field(
        default=None, description="Dimension configurations"
    )
    scoring: Optional[ScoringConfig] = Field(default=None, description="Scoring configuration")
    analysis: Optional[AnalysisConfig] = Field(default=None, description="Analysis configuration")
    profiles: Optional[ProfilesConfig] = Field(default=None, description="Dimension profiles")
    content_types: Optional[ContentTypesConfig] = Field(
        default=None, description="Content type presets"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        import re

        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError(f"Version must be in format X.Y.Z, got {v}")
        return v

    def get_dimension_weight(self, dimension_name: str) -> Optional[float]:
        """Get weight for a specific dimension."""
        if self.dimensions:
            config = self.dimensions.get_dimension(dimension_name)
            if config:
                return config.weight
        return None

    def get_enabled_dimensions(self) -> List[str]:
        """Get list of enabled dimension names."""
        if not self.dimensions:
            return []
        return [
            name for name, config in self.dimensions.get_all_dimensions().items() if config.enabled
        ]


# ==============================================================================
# Partial Config Schema for Overrides
# ==============================================================================


class PartialDimensionConfig(BaseModel):
    """Partial dimension config for override files."""

    model_config = {"extra": "allow"}

    weight: Optional[float] = Field(default=None, ge=0, le=100)
    tier: Optional[DimensionTierEnum] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    thresholds: Optional[Dict[str, Union[float, int]]] = None
    scoring: Optional[Dict[str, Any]] = None
    tier_weights: Optional[Dict[str, float]] = None
    composite_weights: Optional[Dict[str, float]] = None
    optimization: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(default=None, ge=1)
    model: Optional[str] = None


class PartialWriteScoreConfig(BaseModel):
    """Partial config schema for override files (local.yaml)."""

    model_config = {"extra": "allow"}

    version: Optional[str] = None
    dimensions: Optional[Dict[str, PartialDimensionConfig]] = None
    scoring: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    profiles: Optional[Dict[str, Any]] = None
    content_types: Optional[Dict[str, Any]] = None
