"""
Integration test for dimension weight distribution verification.

Verifies that all 16 dimensions have correct weights as specified
after rebalancing to sum to 100%.

Total dimensions: 16
Total weight: 100%
"""

import pytest
from writescore.core.dimension_registry import DimensionRegistry

# Import all 16 dimensions
from writescore.dimensions.perplexity import PerplexityDimension
from writescore.dimensions.burstiness import BurstinessDimension
from writescore.dimensions.structure import StructureDimension
from writescore.dimensions.formatting import FormattingDimension
from writescore.dimensions.lexical import LexicalDimension
from writescore.dimensions.voice import VoiceDimension
from writescore.dimensions.syntactic import SyntacticDimension
from writescore.dimensions.sentiment import SentimentDimension
from writescore.dimensions.predictability import PredictabilityDimension
from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension
from writescore.dimensions.readability import ReadabilityDimension
from writescore.dimensions.transition_marker import TransitionMarkerDimension
from writescore.dimensions.figurative_language import FigurativeLanguageDimension
from writescore.dimensions.pragmatic_markers import PragmaticMarkersDimension
from writescore.dimensions.semantic_coherence import SemanticCoherenceDimension
from writescore.dimensions.ai_vocabulary import AiVocabularyDimension


# Expected weights after rebalancing (16 dimensions = 100%)
EXPECTED_WEIGHTS = {
    # ADVANCED tier
    'predictability': 18.1,       # Highest weight - GLTR token analysis
    'advanced_lexical': 12.8,     # HDD, Yule's K, MATTR diversity
    'transition_marker': 5.5,     # Basic + formulaic transitions
    'pragmatic_markers': 3.7,     # Hedging, boosting, evidentiality
    'perplexity': 2.8,            # True perplexity estimation
    'syntactic': 1.8,             # Dependency depth, subordination

    # SUPPORTING tier
    'sentiment': 15.6,            # Emotional variation patterns
    'semantic_coherence': 4.6,    # Paragraph/topic coherence
    'lexical': 2.8,               # Basic TTR, MTLD diversity
    'figurative_language': 2.8,   # Metaphors, similes, idioms

    # CORE tier
    'readability': 9.2,           # Flesch-Kincaid metrics
    'burstiness': 5.5,            # Sentence/paragraph variation
    'voice': 4.6,                 # First-person, contractions
    'formatting': 3.7,            # Em-dash, bold/italic patterns
    'structure': 3.7,             # Heading depth, list patterns
    'ai_vocabulary': 2.8,         # AI-characteristic word patterns
}

# Expected tiers
EXPECTED_TIERS = {
    # ADVANCED tier (6 dimensions)
    'predictability': 'ADVANCED',
    'advanced_lexical': 'ADVANCED',
    'transition_marker': 'ADVANCED',
    'pragmatic_markers': 'ADVANCED',
    'perplexity': 'ADVANCED',
    'syntactic': 'ADVANCED',

    # SUPPORTING tier (4 dimensions)
    'sentiment': 'SUPPORTING',
    'semantic_coherence': 'SUPPORTING',
    'lexical': 'SUPPORTING',
    'figurative_language': 'SUPPORTING',

    # CORE tier (6 dimensions)
    'readability': 'CORE',
    'burstiness': 'CORE',
    'voice': 'CORE',
    'formatting': 'CORE',
    'structure': 'CORE',
    'ai_vocabulary': 'CORE',
}


def instantiate_all_dimensions():
    """Helper to instantiate all 16 dimensions."""
    return [
        PredictabilityDimension(),
        AdvancedLexicalDimension(),
        TransitionMarkerDimension(),
        PragmaticMarkersDimension(),
        PerplexityDimension(),
        SyntacticDimension(),
        SentimentDimension(),
        SemanticCoherenceDimension(),
        LexicalDimension(),
        FigurativeLanguageDimension(),
        ReadabilityDimension(),
        BurstinessDimension(),
        VoiceDimension(),
        FormattingDimension(),
        StructureDimension(),
        AiVocabularyDimension(),
    ]


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before and after each test."""
    DimensionRegistry.clear()
    yield
    DimensionRegistry.clear()


class TestWeightDistribution:
    """Tests for dimension weight distribution."""

    def test_all_dimensions_register(self):
        """Test that all 16 dimensions register successfully."""
        instantiate_all_dimensions()

        all_dimensions = DimensionRegistry.get_all()
        assert len(all_dimensions) == 16, f"Expected 16 dimensions, got {len(all_dimensions)}"

    def test_individual_dimension_weights(self):
        """Test that each dimension has the correct weight."""
        instantiate_all_dimensions()

        for dimension_name, expected_weight in EXPECTED_WEIGHTS.items():
            dimension = DimensionRegistry.get(dimension_name)
            assert dimension is not None, f"Dimension '{dimension_name}' not found in registry"
            actual_weight = dimension.weight
            assert actual_weight == expected_weight, \
                f"Dimension '{dimension_name}' has weight {actual_weight}, expected {expected_weight}"

    def test_individual_dimension_tiers(self):
        """Test that each dimension has the correct tier."""
        instantiate_all_dimensions()

        for dimension_name, expected_tier in EXPECTED_TIERS.items():
            dimension = DimensionRegistry.get(dimension_name)
            assert dimension is not None, f"Dimension '{dimension_name}' not found in registry"
            actual_tier = dimension.tier
            assert actual_tier == expected_tier, \
                f"Dimension '{dimension_name}' has tier {actual_tier}, expected {expected_tier}"

    def test_weight_sum(self):
        """Test that dimension weights sum to 100%."""
        instantiate_all_dimensions()

        total_weight = sum(EXPECTED_WEIGHTS.values())
        # Allow tiny floating point tolerance
        assert abs(total_weight - 100.0) < 0.01, \
            f"Total weight is {total_weight}, expected 100.0"

    def test_dimension_names_match(self):
        """Test that dimension_name property matches registry key."""
        dimensions = instantiate_all_dimensions()

        for dimension in dimensions:
            name = dimension.dimension_name
            registered = DimensionRegistry.get(name)
            assert registered is dimension, \
                f"Dimension '{name}' not found by name in registry"

    def test_weight_range_validation(self):
        """Test that all weights are within valid range (0-100)."""
        instantiate_all_dimensions()

        all_dimensions = DimensionRegistry.get_all()
        for dimension in all_dimensions:
            weight = dimension.weight
            assert 0 <= weight <= 100, \
                f"Dimension '{dimension.dimension_name}' has invalid weight {weight} (must be 0-100)"

    def test_tier_categorization(self):
        """Test dimension tier distribution: CORE=6, SUPPORTING=4, ADVANCED=6."""
        instantiate_all_dimensions()

        tier_counts = {}
        all_dimensions = DimensionRegistry.get_all()
        for dimension in all_dimensions:
            tier = dimension.tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        assert tier_counts.get('CORE', 0) == 6, f"Expected 6 CORE dimensions, got {tier_counts.get('CORE', 0)}"
        assert tier_counts.get('SUPPORTING', 0) == 4, f"Expected 4 SUPPORTING dimensions, got {tier_counts.get('SUPPORTING', 0)}"
        assert tier_counts.get('ADVANCED', 0) == 6, f"Expected 6 ADVANCED dimensions, got {tier_counts.get('ADVANCED', 0)}"

    def test_required_methods_implemented(self):
        """Test that all dimensions implement required DimensionStrategy methods."""
        dimensions = instantiate_all_dimensions()

        required_methods = [
            'dimension_name',
            'weight',
            'tier',
            'description',
            'analyze',
            'calculate_score',
            'get_recommendations',
            'get_tiers',
        ]

        for dimension in dimensions:
            for method_name in required_methods:
                assert hasattr(dimension, method_name), \
                    f"Dimension '{dimension.dimension_name}' missing required method/property '{method_name}'"
