"""
Comprehensive unit tests for DynamicReporter.

Tests cover:
- Comprehensive report generation
- Tier summary generation
- Recommendation prioritization
- Weight distribution calculation
- Markdown formatting
- JSON formatting
- Text formatting (CLI compatible)
- Grade calculation
- Impact level determination
- Backward compatibility
- Selective loading scenarios (AC8, AC9, AC10)
"""

import json

from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.dynamic_reporter import DynamicReporter
from writescore.core.results import AnalysisResults


class MockDimension:
    """Mock dimension for testing."""

    def __init__(self, name='mock', weight=10.0, tier='CORE'):
        self.dimension_name = name
        self.weight = weight
        self.tier = tier
        # Auto-register
        DimensionRegistry.register(self)


def create_mock_analysis_results() -> AnalysisResults:
    """
    Create mock AnalysisResults for testing.

    IMPORTANT: Matches enriched structure from analyzer.py after Story 1.10.1.
    Includes both enrichment metadata AND raw dimension outputs.
    """
    dimension_results = {
        'perplexity': {
            # Enrichment metadata (Story 1.10.1):
            'tier': 'CORE',
            'score': 80.0,
            'weight': 5.0,
            'tier_mapping': {'low': [0, 40], 'medium': [40, 70], 'high': [70, 100]},
            # Raw outputs (what real perplexity dimension produces):
            'ai_vocabulary': {'count': 5, 'percentage': 2.5, 'terms': ['utilize', 'leverage']},
            'formulaic_transitions': {'count': 2, 'percentage': 1.0},
            'metrics': {'overall_score': 80.0},
            'recommendations': ['Reduce AI vocabulary'],
            'error': None
        },
        'burstiness': {
            # Enrichment metadata (Story 1.10.1):
            'tier': 'CORE',
            'score': 45.0,
            'weight': 6.0,
            'tier_mapping': {'low': [0, 40], 'medium': [40, 70], 'high': [70, 100]},
            # Raw outputs (what real burstiness dimension produces):
            'sentence_burstiness': {'cv': 0.15, 'score': 45.0, 'analysis': 'Low variation'},
            'paragraph_variation': {'cv': 0.22},
            'recommendations': ['Increase sentence variation'],
            'error': None
        },
        'predictability': {
            # Enrichment metadata (Story 1.10.1):
            'tier': 'ADVANCED',
            'score': 68.5,
            'weight': 5.0,
            'tier_mapping': {'low': [0, 40], 'medium': [40, 70], 'high': [70, 100]},
            # Raw outputs (what real predictability dimension produces):
            'overall_score': 68.5,
            'recommendations': ['Vary sentence patterns'],
            'error': None
        }
    }

    return AnalysisResults(
        file_path='test.md',
        total_words=1000,
        total_sentences=50,
        total_paragraphs=10,
        ai_vocabulary_count=5,
        ai_vocabulary_per_1k=5.0,
        ai_vocabulary_list=['leverage', 'utilize'],
        formulaic_transitions_count=2,
        formulaic_transitions_list=['Furthermore', 'Moreover'],
        sentence_mean_length=20.0,
        sentence_stdev=5.0,
        sentence_min=10,
        sentence_max=30,
        sentence_range=(10, 30),
        short_sentences_count=10,
        medium_sentences_count=30,
        long_sentences_count=10,
        sentence_lengths=[20, 15, 25],
        paragraph_mean_words=100.0,
        paragraph_stdev=20.0,
        paragraph_range=(50, 150),
        unique_words=500,
        lexical_diversity=0.5,
        bullet_list_lines=5,
        numbered_list_lines=3,
        total_headings=5,
        heading_depth=3,
        h1_count=1,
        h2_count=2,
        h3_count=2,
        h4_plus_count=0,
        headings_per_page=2.0,
        heading_parallelism_score=0.5,
        verbose_headings_count=1,
        avg_heading_length=5.0,
        first_person_count=5,
        direct_address_count=3,
        contraction_count=2,
        domain_terms_count=10,
        domain_terms_list=['API', 'database'],
        em_dash_count=2,
        em_dashes_per_page=0.8,
        bold_markdown_count=3,
        italic_markdown_count=2,
        overall_score=78.5,
        overall_assessment='MIXED',
        dimension_results=dimension_results,
        execution_time=0.287,
        dimension_count=3
    )


class TestDynamicReporter:
    """Test suite for DynamicReporter."""

    def setup_method(self):
        """Setup for each test."""
        DimensionRegistry.clear()

    def test_generate_comprehensive_report(self):
        """Test comprehensive report generation."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        report = reporter.generate_comprehensive_report(results)

        assert 'metadata' in report
        assert 'overall' in report
        assert 'tier_breakdown' in report
        assert 'recommendations' in report
        assert 'weight_distribution' in report

    def test_metadata_generation(self):
        """Test metadata generation includes selective loading info."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        report = reporter.generate_comprehensive_report(results, file_path='test.md')
        metadata = report['metadata']

        assert metadata['file_path'] == 'test.md'
        assert metadata['dimension_count'] == 3
        assert metadata['execution_time'] == 0.287
        assert 'analysis_timestamp' in metadata
        # NEW: AC8, AC9 - selective loading metadata
        assert 'dimensions_loaded' in metadata
        assert 'dimensions_available' in metadata
        assert 'is_partial_analysis' in metadata
        assert 'loaded_dimensions' in metadata
        assert 'not_loaded_dimensions' in metadata

    def test_partial_analysis_detection(self):
        """Test partial analysis is correctly detected (AC9)."""
        results = create_mock_analysis_results()
        results.dimension_count = 3  # Only 3 of 12 loaded
        reporter = DynamicReporter()

        report = reporter.generate_comprehensive_report(results)
        metadata = report['metadata']

        assert metadata['is_partial_analysis'] is True
        assert metadata['dimensions_loaded'] == 3
        assert metadata['dimensions_available'] == 16
        assert len(metadata['not_loaded_dimensions']) == 13

    def test_overall_summary_includes_grade(self):
        """Test overall summary includes grade calculation."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        report = reporter.generate_comprehensive_report(results)
        overall = report['overall']

        assert 'score' in overall
        assert 'assessment' in overall
        assert 'grade' in overall
        assert overall['grade'] in ['A', 'B', 'C', 'D', 'F']
        assert overall['score'] == 78.5
        assert overall['assessment'] == 'MIXED'
        assert overall['grade'] == 'C'  # 78.5 → C grade

    def test_generate_tier_summary(self):
        """Test tier summary generation."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        tier_summary = reporter.generate_tier_summary(results)

        assert 'ADVANCED' in tier_summary
        assert 'CORE' in tier_summary
        assert tier_summary['CORE']['tier_score'] > 0
        assert len(tier_summary['CORE']['dimensions']) > 0

        # Verify dimension has impact_level
        core_dims = tier_summary['CORE']['dimensions']
        assert len(core_dims) == 2  # perplexity and burstiness
        for dim in core_dims:
            assert 'impact_level' in dim
            assert dim['impact_level'] in ['HIGH', 'MEDIUM', 'LOW', 'NONE']

    def test_tier_score_calculation(self):
        """Test tier score is correctly calculated as weighted average."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        tier_summary = reporter.generate_tier_summary(results)
        core_tier = tier_summary['CORE']

        # CORE has perplexity (80.0, weight 5.0) and burstiness (45.0, weight 6.0)
        # Expected: (80.0*5.0 + 45.0*6.0) / (5.0 + 6.0) = (400 + 270) / 11 = 60.9
        expected_score = (80.0 * 5.0 + 45.0 * 6.0) / (5.0 + 6.0)
        assert abs(core_tier['tier_score'] - expected_score) < 0.1

    def test_prioritized_recommendations(self):
        """Test recommendation prioritization."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        recommendations = reporter.generate_prioritized_recommendations(results)

        # Should be sorted by priority (descending)
        assert len(recommendations) > 0
        if len(recommendations) > 1:
            assert recommendations[0]['priority'] >= recommendations[-1]['priority']

        # High impact + high weight dimensions should be first
        # burstiness: score=45.0 (HIGH impact=4) × weight=6.0 = priority 24.0
        assert recommendations[0]['dimension'] == 'burstiness'
        assert recommendations[0]['impact_level'] == 'HIGH'
        assert recommendations[0]['priority'] == 24.0

    def test_impact_levels_in_recommendations(self):
        """Test impact levels are correctly assigned."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        recommendations = reporter.generate_prioritized_recommendations(results)

        # Check each recommendation has proper fields
        for rec in recommendations:
            assert 'priority' in rec
            assert 'dimension' in rec
            assert 'tier' in rec
            assert 'impact_level' in rec
            assert 'weight' in rec
            assert 'recommendation' in rec

    def test_weight_distribution(self):
        """Test weight distribution calculation."""
        # Register dimensions
        MockDimension(name='dim1', weight=50.0, tier='CORE')
        MockDimension(name='dim2', weight=50.0, tier='ADVANCED')

        reporter = DynamicReporter()
        weight_dist = reporter.generate_weight_distribution()

        assert 'by_tier' in weight_dist
        assert 'by_dimension' in weight_dist
        assert weight_dist['by_tier']['CORE'] == 50.0
        assert weight_dist['by_tier']['ADVANCED'] == 50.0
        assert len(weight_dist['by_dimension']) == 2

    def test_weight_normalization(self):
        """Test weight normalization for selective loading (AC10)."""
        # Register dimensions that don't sum to 100
        MockDimension(name='dim1', weight=30.0, tier='CORE')
        MockDimension(name='dim2', weight=20.0, tier='ADVANCED')
        # Total = 50, should normalize to 100

        reporter = DynamicReporter()
        weight_dist = reporter.generate_weight_distribution(normalize=True)

        # Should be normalized
        assert weight_dist['is_normalized'] is True
        assert weight_dist['total_weight_before_normalization'] == 50.0
        # After normalization, weights should sum to 100
        assert abs(weight_dist['by_tier']['CORE'] - 60.0) < 0.1  # 30/50 * 100 = 60
        assert abs(weight_dist['by_tier']['ADVANCED'] - 40.0) < 0.1  # 20/50 * 100 = 40

    def test_format_as_markdown(self):
        """Test markdown formatting."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        markdown = reporter.format_as_markdown(results)

        # Verify structure
        assert '# AI Pattern Analysis Report' in markdown
        assert '## Overall Assessment' in markdown
        assert '## Dimension Analysis by Tier' in markdown
        assert '## Prioritized Recommendations' in markdown
        assert '## Weight Distribution' in markdown

        # Verify markdown table format
        assert '| Dimension | Score | Rating | Weight | Impact |' in markdown
        assert '|:----------|------:|:------:|-------:|:------:|' in markdown

    def test_markdown_partial_analysis_notice(self):
        """Test markdown includes partial analysis notice (AC8, AC9)."""
        results = create_mock_analysis_results()
        results.dimension_count = 3  # Partial analysis
        reporter = DynamicReporter()

        markdown = reporter.format_as_markdown(results)

        assert 'partial analysis' in markdown.lower()
        assert '3 of 16' in markdown

    def test_format_as_json(self):
        """Test JSON formatting."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        json_str = reporter.format_as_json(results)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert 'metadata' in parsed
        assert 'overall' in parsed
        assert 'tier_breakdown' in parsed
        assert 'recommendations' in parsed

        # Verify 2-space indentation
        lines = json_str.splitlines()
        # Check for 2-space indented line
        assert any(line.startswith('  "metadata"') for line in lines)

    def test_format_as_text_cli_compatible(self):
        """Test text formatting matches CLI format."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        text = reporter.format_as_text(results, file_path='test.md')

        # Verify expected sections
        assert '=== AI Pattern Analysis Results ===' in text
        assert 'File: test.md' in text
        assert 'Overall Score:' in text
        assert '--- Dimension Scores ---' in text
        assert '--- Recommendations ---' in text
        assert '--- Weight Distribution ---' in text

        # Verify section separator at end
        assert '===================================' in text

        # Verify tier format
        assert 'CORE Tier (Score:' in text
        assert 'ADVANCED Tier (Score:' in text

    def test_calculate_grade(self):
        """Test grade calculation."""
        reporter = DynamicReporter()

        assert reporter._calculate_grade(95.0) == 'A'
        assert reporter._calculate_grade(90.0) == 'A'
        assert reporter._calculate_grade(85.0) == 'B'
        assert reporter._calculate_grade(80.0) == 'B'
        assert reporter._calculate_grade(75.0) == 'C'
        assert reporter._calculate_grade(70.0) == 'C'
        assert reporter._calculate_grade(65.0) == 'D'
        assert reporter._calculate_grade(60.0) == 'D'
        assert reporter._calculate_grade(55.0) == 'F'
        assert reporter._calculate_grade(0.0) == 'F'

    def test_determine_impact_level(self):
        """Test impact level determination."""
        reporter = DynamicReporter()

        assert reporter._determine_impact_level(45.0) == 'HIGH'
        assert reporter._determine_impact_level(49.9) == 'HIGH'
        assert reporter._determine_impact_level(50.0) == 'MEDIUM'
        assert reporter._determine_impact_level(65.0) == 'MEDIUM'
        assert reporter._determine_impact_level(69.9) == 'MEDIUM'
        assert reporter._determine_impact_level(70.0) == 'LOW'
        assert reporter._determine_impact_level(75.0) == 'LOW'
        assert reporter._determine_impact_level(84.9) == 'LOW'
        assert reporter._determine_impact_level(85.0) == 'NONE'
        assert reporter._determine_impact_level(90.0) == 'NONE'
        assert reporter._determine_impact_level(100.0) == 'NONE'

    def test_empty_recommendations(self):
        """Test handling of dimensions with no recommendations."""
        results = create_mock_analysis_results()
        # Clear recommendations
        for dim_result in results.dimension_results.values():
            dim_result['recommendations'] = []

        reporter = DynamicReporter()
        recommendations = reporter.generate_prioritized_recommendations(results)

        assert len(recommendations) == 0

    def test_failed_dimension_handling(self):
        """Test failed dimensions are excluded from recommendations."""
        results = create_mock_analysis_results()
        # Mark one dimension as failed
        results.dimension_results['perplexity']['error'] = 'Test error'

        reporter = DynamicReporter()
        recommendations = reporter.generate_prioritized_recommendations(results)

        # Should only have recommendations from successful dimensions
        dim_names = [rec['dimension'] for rec in recommendations]
        assert 'perplexity' not in dim_names
        assert 'burstiness' in dim_names

    def test_tier_score_with_failed_dimensions(self):
        """Test tier score calculation excludes failed dimensions."""
        results = create_mock_analysis_results()
        # Mark one dimension as failed
        results.dimension_results['perplexity']['error'] = 'Test error'

        reporter = DynamicReporter()
        tier_summary = reporter.generate_tier_summary(results)

        # CORE tier should only include burstiness now
        core_tier = tier_summary['CORE']
        assert core_tier['tier_score'] == 45.0  # Only burstiness score
        assert core_tier['tier_weight'] == 6.0  # Only burstiness weight

    def test_multiple_tiers(self):
        """Test dimensions are correctly grouped by tier."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        tier_summary = reporter.generate_tier_summary(results)

        # Check CORE tier
        core_dims = [d['name'] for d in tier_summary['CORE']['dimensions']]
        assert 'perplexity' in core_dims
        assert 'burstiness' in core_dims

        # Check ADVANCED tier
        advanced_dims = [d['name'] for d in tier_summary['ADVANCED']['dimensions']]
        assert 'predictability' in advanced_dims

    def test_recommendation_priority_ordering(self):
        """Test recommendations are ordered by priority correctly."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        recommendations = reporter.generate_prioritized_recommendations(results)

        # Expected priorities:
        # burstiness: 45.0 score (HIGH=4) × 6.0 weight = 24.0
        # perplexity: 80.0 score (LOW=2) × 5.0 weight = 10.0
        # predictability: 68.5 score (MEDIUM=3) × 5.0 weight = 15.0

        assert recommendations[0]['dimension'] == 'burstiness'
        assert recommendations[0]['priority'] == 24.0

        assert recommendations[1]['dimension'] == 'predictability'
        assert recommendations[1]['priority'] == 15.0

        assert recommendations[2]['dimension'] == 'perplexity'
        assert recommendations[2]['priority'] == 10.0

    def test_text_format_dimension_capitalization(self):
        """Test text format capitalizes dimension names."""
        results = create_mock_analysis_results()
        reporter = DynamicReporter()

        text = reporter.format_as_text(results)

        # Dimension names should be capitalized in text format
        assert 'Perplexity:' in text
        assert 'Burstiness:' in text
        assert 'Predictability:' in text

    def test_registry_parameter(self):
        """Test DynamicReporter can accept custom registry."""
        # Create custom registry (uses class-level storage)
        custom_registry = DimensionRegistry

        reporter = DynamicReporter(registry=custom_registry)
        assert reporter.registry is custom_registry

    def test_default_registry(self):
        """Test DynamicReporter uses global registry by default."""
        reporter = DynamicReporter()
        assert reporter.registry is DimensionRegistry
