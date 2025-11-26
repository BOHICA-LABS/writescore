"""
Integration tests for Dynamic Reporting System.

Tests end-to-end reporting with real AnalysisResults from the analyzer.
Addresses MEDIUM issue TEST-001: Missing integration tests.
"""

import json
import tempfile
from pathlib import Path

import pytest

from writescore.core.analysis_config import AnalysisConfig
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.dynamic_reporter import DynamicReporter


@pytest.fixture
def sample_text():
    """Create sample text for analysis."""
    return """# AI Writing Patterns

Artificial intelligence has transformed content creation in remarkable ways.
Modern language models can generate coherent, contextually relevant text across
diverse topics and styles. However, this capability raises important questions
about authenticity and detection.

## Key Considerations

Writers must balance efficiency with authenticity. The goal is not to avoid
technology but to use it thoughtfully. Understanding AI detection patterns
helps create more natural, human-like content.

### Technical Analysis

Several dimensions contribute to detection risk:
- Perplexity measures word predictability
- Burstiness tracks sentence length variation
- Lexical diversity examines vocabulary richness
- Syntactic patterns reveal structural complexity

## Conclusion

By understanding these patterns, writers can make informed decisions about
their content creation process while maintaining authenticity and quality.
"""


@pytest.fixture
def sample_text_short():
    """Create short sample text for partial analysis testing.

    Note: Must be long enough to produce valid dimension results with 'tier'
    fields populated, but short enough to potentially produce some failures
    or edge cases in certain dimensions.
    """
    return """This is a short test document with minimal content.
It has a few sentences to ensure basic analysis can complete.
The analyzer should handle this gracefully without crashing.
Short texts may produce different results than longer documents."""


@pytest.fixture
def temp_text_file(sample_text):
    """Create temporary file with sample text."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_text)
        temp_file = f.name
    yield temp_file
    Path(temp_file).unlink(missing_ok=True)


@pytest.fixture
def temp_text_file_short(sample_text_short):
    """Create temporary file with short sample text."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_text_short)
        temp_file = f.name
    yield temp_file
    Path(temp_file).unlink(missing_ok=True)


class TestReportingIntegration:
    """Integration tests for dynamic reporting with real analyzer output."""

    def test_full_analysis_with_json_report(self, temp_text_file):
        """Test complete analysis workflow with JSON output format."""
        # Run real analysis with full dimension loading
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate JSON report
        reporter = DynamicReporter()
        json_output = reporter.format_as_json(results)

        # Verify JSON is valid
        report = json.loads(json_output)

        # Verify metadata structure
        assert 'metadata' in report
        metadata = report['metadata']
        assert 'dimension_count' in metadata
        assert 'dimensions_loaded' in metadata
        assert 'dimensions_available' in metadata
        assert 'execution_time' in metadata
        assert 'is_partial_analysis' in metadata
        assert metadata['dimension_count'] > 0

        # Verify overall summary
        assert 'overall' in report
        overall = report['overall']
        assert 'score' in overall
        assert 'grade' in overall
        assert 'assessment' in overall
        assert 0 <= overall['score'] <= 100

        # Verify tier breakdown exists
        assert 'tier_breakdown' in report
        tier_breakdown = report['tier_breakdown']
        # Tier names are actual tier identifiers like 'CORE', 'ADVANCED', etc.
        assert len(tier_breakdown) > 0

        # Verify recommendations
        assert 'recommendations' in report
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)

        # Verify weight distribution
        assert 'weight_distribution' in report
        weights = report['weight_distribution']
        assert 'by_tier' in weights
        assert 'by_dimension' in weights

    def test_full_analysis_with_markdown_report(self, temp_text_file):
        """Test complete analysis workflow with Markdown output format."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate Markdown report
        reporter = DynamicReporter()
        markdown_output = reporter.format_as_markdown(results)

        # Verify Markdown structure
        assert '# AI Pattern Analysis Report' in markdown_output
        assert '## Overall Assessment' in markdown_output
        assert '## Dimension Analysis by Tier' in markdown_output
        assert '## Prioritized Recommendations' in markdown_output
        assert '## Weight Distribution' in markdown_output

        # Verify tier sections exist (actual tier names from system)
        assert 'CORE' in markdown_output or 'ADVANCED' in markdown_output or 'SUPPORTING' in markdown_output

    def test_full_analysis_with_text_report(self, temp_text_file):
        """Test complete analysis workflow with CLI-compatible text output."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate text report
        reporter = DynamicReporter()
        text_output = reporter.format_as_text(results)

        # Verify text structure
        assert '=== AI Pattern Analysis Results ===' in text_output
        assert 'Overall Score:' in text_output
        assert 'Tier' in text_output or 'CORE' in text_output or 'ADVANCED' in text_output

        # Verify dimension capitalization (e.g., "Perplexity" not "perplexity")
        lines = text_output.split('\n')
        dimension_lines = [line for line in lines if ':' in line and 'Score' in line]
        for line in dimension_lines:
            dimension_part = line.split(':')[0].strip()
            if dimension_part and not dimension_part.isupper():
                # Should be capitalized (e.g., "Perplexity")
                assert dimension_part[0].isupper(), f"Expected capitalized dimension: {dimension_part}"

    def test_partial_analysis_detection(self, sample_text):
        """Test that partial analysis is correctly detected in metadata."""
        # Run analysis with fast profile (loads fewer dimensions - partial analysis)
        config = AnalysisConfig(dimension_profile="fast")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_text(sample_text)

        # Generate report
        reporter = DynamicReporter()
        json_output = reporter.format_as_json(results)
        report = json.loads(json_output)

        # Verify partial analysis metadata
        metadata = report['metadata']
        assert metadata['is_partial_analysis'] is True
        assert metadata['dimensions_loaded'] < metadata['dimensions_available']
        assert 'loaded_dimensions' in metadata
        assert 'not_loaded_dimensions' in metadata
        assert len(metadata['not_loaded_dimensions']) > 0

    def test_comprehensive_report_structure(self, temp_text_file):
        """Test comprehensive report contains all required sections."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate comprehensive report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results, file_path='test.md')

        # Verify all top-level sections
        assert 'metadata' in report
        assert 'overall' in report
        assert 'tier_breakdown' in report
        assert 'recommendations' in report
        assert 'weight_distribution' in report

        # Verify file_path is included
        assert report['metadata']['file_path'] == 'test.md'

    def test_tier_score_calculation_with_real_data(self, temp_text_file):
        """Test tier score calculation with real dimension results."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Verify tier scores
        tier_breakdown = report['tier_breakdown']

        for tier_name, tier_data in tier_breakdown.items():
            assert 'tier_score' in tier_data
            assert 'dimensions' in tier_data

            # Tier score should be between 0 and 100
            tier_score = tier_data['tier_score']
            assert 0 <= tier_score <= 100, f"{tier_name} score out of range: {tier_score}"

            # Each dimension should have required fields
            # Note: dimensions is a list of dicts, not a dict
            dimensions = tier_data['dimensions']
            if isinstance(dimensions, list):
                for dim_data in dimensions:
                    assert 'name' in dim_data
                    assert 'score' in dim_data
                    assert 'weight' in dim_data
            elif isinstance(dimensions, dict):
                for _dim_name, dim_data in dimensions.items():
                    assert 'score' in dim_data
                    assert 'weight' in dim_data

    def test_recommendations_prioritization(self, temp_text_file):
        """Test that recommendations are properly prioritized."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Verify recommendations structure
        recommendations = report['recommendations']

        if len(recommendations) > 0:
            # Each recommendation should have required fields per DynamicReporter implementation
            for rec in recommendations:
                assert 'dimension' in rec
                assert 'tier' in rec
                assert 'recommendation' in rec  # Actual field name (not 'message')
                assert 'impact_level' in rec    # Actual field name (not 'impact')
                assert 'priority' in rec
                assert 'weight' in rec

                # Impact level should be valid (uppercase per implementation)
                assert rec['impact_level'] in ['HIGH', 'MEDIUM', 'LOW', 'NONE']

    def test_weight_distribution_totals(self, temp_text_file):
        """Test that weight distribution totals are correct."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Verify weight distribution
        weight_dist = report['weight_distribution']
        # Actual field name is 'by_tier', not 'weights_by_tier'
        assert 'by_tier' in weight_dist
        assert 'by_dimension' in weight_dist

        # Verify tier weights structure
        tier_weights = weight_dist['by_tier']
        assert isinstance(tier_weights, dict)
        # All tier weights should be >= 0
        for _tier_name, weight in tier_weights.items():
            assert weight >= 0

    def test_json_serialization_no_errors(self, temp_text_file):
        """Test that JSON serialization completes without errors."""
        # Run real analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_file(temp_text_file)

        # Generate JSON report - should not raise exception
        reporter = DynamicReporter()
        json_output = reporter.format_as_json(results)

        # Should be valid JSON
        report = json.loads(json_output)
        assert isinstance(report, dict)

    def test_selective_loading_metadata_accuracy(self, sample_text):
        """Test metadata accuracy with different dimension loading profiles."""
        # Test with full profile (all dimensions)
        config_full = AnalysisConfig(dimension_profile="full")
        analyzer_full = AIPatternAnalyzer(config=config_full)
        results_full = analyzer_full.analyze_text(sample_text)

        reporter = DynamicReporter()
        report_full = reporter.generate_comprehensive_report(results_full)

        # Test with fast profile (fewer dimensions)
        config_partial = AnalysisConfig(dimension_profile="fast")
        analyzer_partial = AIPatternAnalyzer(config=config_partial)
        results_partial = analyzer_partial.analyze_text(sample_text)

        report_partial = reporter.generate_comprehensive_report(results_partial)

        # Compare metadata - full should load more dimensions than fast
        assert (report_full['metadata']['dimensions_loaded'] >=
                report_partial['metadata']['dimensions_loaded'])

    def test_failed_dimensions_handling(self, sample_text_short):
        """Test that reports handle failed dimensions gracefully."""
        # Analyze very short text (may cause some dimensions to fail)
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_text(sample_text_short)

        # Generate report - should not crash
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Report should still have valid structure
        assert 'metadata' in report
        assert 'overall' in report
        assert 'tier_breakdown' in report

        # Overall score should be valid even with failures
        assert 0 <= report['overall']['score'] <= 100

    def test_dimension_loader_integration(self, sample_text):
        """Test that dimension list matches DimensionLoader registry."""
        from writescore.core.dimension_loader import DIMENSION_MODULE_MAP

        # Run analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_text(sample_text)

        # Generate report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Metadata should reflect actual DIMENSION_MODULE_MAP
        metadata = report['metadata']
        expected_available = len(DIMENSION_MODULE_MAP)
        assert metadata['dimensions_available'] == expected_available

    def test_backward_compatibility_dimension_count(self, sample_text):
        """Test that dimension_count field exists for backward compatibility."""
        # Run analysis
        config = AnalysisConfig(dimension_profile="full")
        analyzer = AIPatternAnalyzer(config=config)
        results = analyzer.analyze_text(sample_text)

        # Generate report
        reporter = DynamicReporter()
        report = reporter.generate_comprehensive_report(results)

        # Verify both old and new fields exist
        metadata = report['metadata']
        assert 'dimension_count' in metadata  # Old field (backward compat)
        assert 'dimensions_loaded' in metadata  # New field
        assert metadata['dimension_count'] == metadata['dimensions_loaded']
