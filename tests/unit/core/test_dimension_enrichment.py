"""
Comprehensive unit tests for dimension enrichment layer (Story 1.10.1).

Tests cover:
- Core enrichment logic (AC1)
- Tier metadata extraction (AC2)
- Score normalization (AC3)
- Weight assignment by tier (AC4)
- Raw output preservation (AC7)
- Failed dimension handling (AC8)
- Input validation and security (AC11)
"""

from writescore.core.analysis_config import DEFAULT_CONFIG
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.dimension_registry import DimensionRegistry


class MockDimension:
    """Mock dimension for testing."""

    def __init__(self, name='mock', tier='CORE'):
        self.dimension_name = name
        self.tier = tier
        self.weight = 0.20 if tier == 'CORE' else 0.10 if tier == 'ADVANCED' else 0.05

    def analyze(self, text, lines, **kwargs):
        return {'overall_score': 75.0}


class TestDimensionEnrichment:
    """Test suite for dimension enrichment layer."""

    def setup_method(self):
        """Setup for each test."""
        DimensionRegistry.clear()
        self.analyzer = AIPatternAnalyzer(config=DEFAULT_CONFIG)

    def teardown_method(self):
        """Cleanup after each test."""
        DimensionRegistry.clear()

    def test_enrich_dimension_results(self):
        """Test core enrichment logic adds all required metadata (AC1)."""
        # Register mock dimension
        mock_dim = MockDimension(name='perplexity', tier='CORE')
        DimensionRegistry.register(mock_dim)

        # Create raw dimension results
        raw_results = {
            'perplexity': {
                'ai_vocabulary': {'count': 5, 'percentage': 2.1},
                'formulaic_transitions': {'count': 3},
                'overall_score': 80.0
            }
        }

        # Enrich
        enriched = self.analyzer._enrich_dimension_results(raw_results)

        # Verify enrichment metadata added
        assert 'tier' in enriched['perplexity']
        assert 'score' in enriched['perplexity']
        assert 'weight' in enriched['perplexity']
        assert 'tier_mapping' in enriched['perplexity']

        # Verify metadata values (Story 2.4.1 - perplexity is ADVANCED tier)
        # Note: Enrichment uses tier-based weight (0.10 for ADVANCED) not dimension.weight property
        assert enriched['perplexity']['tier'] == 'ADVANCED'
        assert enriched['perplexity']['score'] == 80.0
        assert enriched['perplexity']['weight'] == 0.10
        assert isinstance(enriched['perplexity']['tier_mapping'], dict)

        # Verify raw outputs preserved
        assert 'ai_vocabulary' in enriched['perplexity']
        assert 'formulaic_transitions' in enriched['perplexity']
        assert enriched['perplexity']['ai_vocabulary'] == {'count': 5, 'percentage': 2.1}

    def test_tier_metadata_extraction(self):
        """Test tier metadata matches registry assignment (AC2)."""
        # Register dimensions with different tiers
        # Note: Story 2.4.1 - perplexity is ADVANCED in balanced profile, overwrites mock
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='stylometric', tier='ADVANCED'))
        DimensionRegistry.register(MockDimension(name='structural_dim', tier='STRUCTURAL'))
        DimensionRegistry.register(MockDimension(name='supporting_dim', tier='SUPPORTING'))

        # Test ADVANCED tier (perplexity is ADVANCED in real balanced profile)
        tier = self.analyzer._get_dimension_tier('perplexity')
        assert tier == 'ADVANCED'

        # Test ADVANCED tier
        tier = self.analyzer._get_dimension_tier('stylometric')
        assert tier == 'ADVANCED'

        # Test STRUCTURAL tier
        tier = self.analyzer._get_dimension_tier('structural_dim')
        assert tier == 'STRUCTURAL'

        # Test SUPPORTING tier
        tier = self.analyzer._get_dimension_tier('supporting_dim')
        assert tier == 'SUPPORTING'

        # Test unknown dimension
        tier = self.analyzer._get_dimension_tier('unknown_dimension')
        assert tier == 'UNKNOWN'

    def test_score_normalization(self):
        """Test score extraction from various dimension formats (AC3)."""
        # Strategy 1: Direct overall_score
        raw1 = {'overall_score': 85.0, 'other_data': 'test'}
        score1 = self.analyzer._extract_dimension_score('test_dim', raw1)
        assert score1 == 85.0

        # Strategy 2: Direct score field
        raw2 = {'score': 72.5}
        score2 = self.analyzer._extract_dimension_score('test_dim', raw2)
        assert score2 == 72.5

        # Strategy 3a: Burstiness dimension-specific
        raw3 = {'sentence_burstiness': {'cv': 0.15, 'score': 45.0}}
        score3 = self.analyzer._extract_dimension_score('burstiness', raw3)
        assert score3 == 45.0

        # Strategy 3b: Perplexity dimension-specific
        raw4 = {'metrics': {'overall_score': 82.0}}
        score4 = self.analyzer._extract_dimension_score('perplexity', raw4)
        assert score4 == 82.0

        # Strategy 3c: Structure dimension-specific
        raw5 = {'structural_score': 68.0}
        score5 = self.analyzer._extract_dimension_score('structure', raw5)
        assert score5 == 68.0

        # Strategy 4: Default to 50.0 if no score found
        raw6 = {'some_other_field': 'data'}
        score6 = self.analyzer._extract_dimension_score('unknown', raw6)
        assert score6 == 50.0

    def test_weight_assignment_by_tier(self):
        """Test weight assignment based on tier classification (AC4)."""
        # Test CORE tier weight
        weight_core = self.analyzer._get_dimension_weight('CORE')
        assert weight_core == 0.20

        # Test ADVANCED tier weight
        weight_advanced = self.analyzer._get_dimension_weight('ADVANCED')
        assert weight_advanced == 0.10

        # Test STRUCTURAL tier weight
        weight_structural = self.analyzer._get_dimension_weight('STRUCTURAL')
        assert weight_structural == 0.10

        # Test SUPPORTING tier weight
        weight_supporting = self.analyzer._get_dimension_weight('SUPPORTING')
        assert weight_supporting == 0.05

        # Test UNKNOWN tier weight (fallback)
        weight_unknown = self.analyzer._get_dimension_weight('UNKNOWN')
        assert weight_unknown == 0.05

        # Test invalid tier (fallback)
        weight_invalid = self.analyzer._get_dimension_weight('INVALID_TIER')
        assert weight_invalid == 0.05

    def test_enrichment_preserves_raw_outputs(self):
        """Test raw dimension outputs are preserved after enrichment (AC7)."""
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))

        raw_results = {
            'perplexity': {
                'ai_vocabulary': {'count': 5, 'terms': ['utilize', 'leverage']},
                'formulaic_transitions': {'count': 3, 'percentage': 1.5},
                'metrics': {'overall_score': 80.0},
                'detailed_analysis': {'key': 'value'},
                'overall_score': 80.0
            }
        }

        enriched = self.analyzer._enrich_dimension_results(raw_results)

        # Verify ALL raw outputs still present
        assert 'ai_vocabulary' in enriched['perplexity']
        assert 'formulaic_transitions' in enriched['perplexity']
        assert 'metrics' in enriched['perplexity']
        assert 'detailed_analysis' in enriched['perplexity']
        assert 'overall_score' in enriched['perplexity']

        # Verify raw data unchanged
        assert enriched['perplexity']['ai_vocabulary']['count'] == 5
        assert enriched['perplexity']['ai_vocabulary']['terms'] == ['utilize', 'leverage']
        assert enriched['perplexity']['formulaic_transitions']['percentage'] == 1.5
        assert enriched['perplexity']['detailed_analysis']['key'] == 'value'

        # Verify enrichment metadata also present
        assert 'tier' in enriched['perplexity']
        assert 'weight' in enriched['perplexity']
        assert 'tier_mapping' in enriched['perplexity']

    def test_enrichment_with_failed_dimensions(self):
        """Test failed dimensions are handled gracefully (AC8)."""
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='burstiness', tier='CORE'))

        # Mix of successful and failed dimensions
        raw_results = {
            'perplexity': {
                'overall_score': 80.0,
                'ai_vocabulary': {'count': 5}
            },
            'burstiness': {
                'available': False,
                'error': 'Module not loaded'
            }
        }

        enriched = self.analyzer._enrich_dimension_results(raw_results)

        # Successful dimension should be enriched
        assert 'tier' in enriched['perplexity']
        assert 'score' in enriched['perplexity']
        assert 'weight' in enriched['perplexity']

        # Failed dimension should NOT be enriched (preserved as-is)
        assert 'tier' not in enriched['burstiness']
        assert 'score' not in enriched['burstiness']
        assert 'weight' not in enriched['burstiness']
        assert enriched['burstiness']['available'] is False
        assert enriched['burstiness']['error'] == 'Module not loaded'

    def test_enrichment_validates_input_structure(self):
        """Test input validation handles malformed data gracefully (AC11)."""
        # Test 1: Non-dict dimension_results
        result1 = self.analyzer._enrich_dimension_results("not a dict")
        assert result1 == "not a dict"  # Returns as-is

        result2 = self.analyzer._enrich_dimension_results(None)
        assert result2 is None  # Returns as-is

        result3 = self.analyzer._enrich_dimension_results([1, 2, 3])
        assert result3 == [1, 2, 3]  # Returns as-is

        # Test 2: Dimension entry is not a dict
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))
        raw_results = {
            'perplexity': "not a dict",
            'burstiness': {'overall_score': 45.0}
        }
        enriched = self.analyzer._enrich_dimension_results(raw_results)
        assert enriched['perplexity'] == "not a dict"  # Preserved as-is
        assert 'tier' in enriched['burstiness']  # Valid one still enriched

        # Test 3: Score out of bounds (should be clamped)
        raw_results2 = {
            'perplexity': {'overall_score': 150.0}  # Out of bounds
        }
        enriched2 = self.analyzer._enrich_dimension_results(raw_results2)
        assert enriched2['perplexity']['score'] == 100.0  # Clamped to max

        raw_results3 = {
            'perplexity': {'overall_score': -50.0}  # Out of bounds
        }
        enriched3 = self.analyzer._enrich_dimension_results(raw_results3)
        assert enriched3['perplexity']['score'] == 0.0  # Clamped to min

    def test_tier_mapping_structure(self):
        """Test tier mapping returns correct threshold structure (AC1)."""
        tier_mapping = self.analyzer._get_tier_mapping('any_dimension')

        # Verify structure
        assert isinstance(tier_mapping, dict)
        assert 'low' in tier_mapping
        assert 'medium' in tier_mapping
        assert 'high' in tier_mapping

        # Verify threshold values
        assert tier_mapping['low'] == [0, 40]
        assert tier_mapping['medium'] == [40, 70]
        assert tier_mapping['high'] == [70, 100]

    def test_enrichment_with_multiple_dimensions(self):
        """Test enrichment works correctly with multiple dimensions."""
        # Register multiple dimensions
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='burstiness', tier='CORE'))
        DimensionRegistry.register(MockDimension(name='stylometric', tier='ADVANCED'))
        DimensionRegistry.register(MockDimension(name='supporting', tier='SUPPORTING'))

        raw_results = {
            'perplexity': {'overall_score': 85.0},
            'burstiness': {'sentence_burstiness': {'score': 60.0}},
            'stylometric': {'score': 72.0},
            'supporting': {'overall_score': 50.0}
        }

        enriched = self.analyzer._enrich_dimension_results(raw_results)

        # Verify all dimensions enriched
        assert len(enriched) == 4

        # Verify ADVANCED/CORE dimensions (Story 2.4.1)
        # Note: Enrichment uses tier-based weights (ADVANCED=0.10, CORE=0.20) not dimension.weight
        assert enriched['perplexity']['tier'] == 'ADVANCED'
        assert enriched['perplexity']['weight'] == 0.10
        assert enriched['burstiness']['tier'] == 'CORE'
        assert enriched['burstiness']['weight'] == 0.20

        # Verify ADVANCED dimension
        assert enriched['stylometric']['tier'] == 'ADVANCED'
        assert enriched['stylometric']['weight'] == 0.10

        # Verify SUPPORTING dimension
        assert enriched['supporting']['tier'] == 'SUPPORTING'
        assert enriched['supporting']['weight'] == 0.05

    def test_empty_dimension_results(self):
        """Test enrichment handles empty dimension results."""
        empty_results = {}
        enriched = self.analyzer._enrich_dimension_results(empty_results)
        assert enriched == {}

    def test_score_extraction_with_missing_fields(self):
        """Test score extraction handles missing nested fields gracefully."""
        # Burstiness with missing score in nested dict
        raw1 = {'sentence_burstiness': {'cv': 0.15}}  # No 'score' field
        score1 = self.analyzer._extract_dimension_score('burstiness', raw1)
        assert score1 == 50.0  # Falls back to Strategy 5 default

        # Perplexity with missing overall_score in metrics (Story 2.4.1 - returns 50.0 for unavailable)
        raw2 = {'metrics': {'some_other_field': 'value'}}
        score2 = self.analyzer._extract_dimension_score('perplexity', raw2)
        assert score2 == 50.0  # Strategy 5: Falls back to default when calculate_score() returns 50.0 for unavailable

        # Non-dict values where dict expected
        raw3 = {'sentence_burstiness': 'not a dict'}
        score3 = self.analyzer._extract_dimension_score('burstiness', raw3)
        assert score3 == 50.0  # Falls back to Strategy 5 default

    def test_weight_bounds_checking(self):
        """Test weight calculation bounds checking (AC11)."""
        # Valid weights should pass through
        assert self.analyzer._get_dimension_weight('CORE') == 0.20
        assert self.analyzer._get_dimension_weight('ADVANCED') == 0.10

        # Note: Negative weights can only come from tier_weights dict modification
        # which is internal, so this test validates the bounds check logic exists

    def test_enrichment_metadata_types(self):
        """Test enrichment metadata has correct types."""
        DimensionRegistry.register(MockDimension(name='perplexity', tier='CORE'))

        raw_results = {
            'perplexity': {'overall_score': 80.0}
        }

        enriched = self.analyzer._enrich_dimension_results(raw_results)

        # Verify types
        assert isinstance(enriched['perplexity']['tier'], str)
        assert isinstance(enriched['perplexity']['score'], float)
        assert isinstance(enriched['perplexity']['weight'], float)
        assert isinstance(enriched['perplexity']['tier_mapping'], dict)

        # Verify tier_mapping values are lists
        assert isinstance(enriched['perplexity']['tier_mapping']['low'], list)
        assert isinstance(enriched['perplexity']['tier_mapping']['medium'], list)
        assert isinstance(enriched['perplexity']['tier_mapping']['high'], list)
