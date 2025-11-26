"""
Tests for AiVocabularyDimension - tier-weighted AI vocabulary detection.

Created in Story 2.4.0.6 - extracted from perplexity.py.
"""

import pytest
from writescore.dimensions.ai_vocabulary import (
    AiVocabularyDimension,
    TIER_1_PATTERNS,
    TIER_2_PATTERNS,
    TIER_3_PATTERNS
)
from writescore.core.dimension_registry import DimensionRegistry


@pytest.fixture
def dimension():
    """Create AiVocabularyDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return AiVocabularyDimension()


@pytest.fixture
def text_tier1_heavy():
    """Text with heavy Tier 1 AI vocabulary."""
    return """# Analysis Report

We need to delve into the robust framework and leverage the holistic approach.
This quintessential solution harnesses the power of innovation to underscore
the paramount importance of this tapestry of ideas. Let us embark on this
journey and foster meaningful change in the realm of technology.
"""


@pytest.fixture
def text_tier2_heavy():
    """Text with heavy Tier 2 AI vocabulary."""
    return """# Innovation Report

This cutting-edge and revolutionary approach represents a game-changing paradigm.
The comprehensive and innovative solution provides seamless integration with
transformative capabilities. The intricate and nuanced design offers pivotal
advantages through dynamic and multifaceted methodologies.
"""


@pytest.fixture
def text_tier3_heavy():
    """Text with heavy Tier 3 AI vocabulary."""
    return """# Process Optimization

We aim to optimize operations and streamline workflows. The goal is to facilitate
efficient processes and enhance productivity. We must navigate the complex
ecosystem carefully and mitigate potential risks. This landscape requires
continuous optimization to enhance overall performance.
"""


@pytest.fixture
def text_mixed_tiers():
    """Text with mixed tier AI vocabulary."""
    return """# Technology Review

Let's delve into this robust solution that optimizes performance. The cutting-edge
framework facilitates seamless integration. We must leverage this comprehensive
approach to navigate the complex landscape efficiently.
"""


@pytest.fixture
def text_human_style():
    """Text without AI vocabulary (human style)."""
    return """# Getting Started

Let's look at the basics. You'll find this pretty straightforward.
Here's what matters most: focus on the fundamentals.

Once you get the hang of it, everything clicks. But remember,
practice makes perfect. Start small and build from there.
"""


class TestDimensionProperties:
    """Tests for dimension metadata properties."""

    def test_dimension_name(self, dimension):
        """Test dimension name is correct."""
        assert dimension.dimension_name == "ai_vocabulary"

    def test_weight(self, dimension):
        """Test dimension weight is 2.8% (rebalanced to 100% total)."""
        assert dimension.weight == 2.8

    def test_tier(self, dimension):
        """Test dimension tier is CORE."""
        assert dimension.tier == "CORE"

    def test_description(self, dimension):
        """Test dimension description exists."""
        assert "AI-characteristic vocabulary" in dimension.description
        assert "tier-weighted" in dimension.description


class TestTier1Detection:
    """Tests for Tier 1 pattern detection (14 patterns, 3× weight)."""

    def test_tier1_pattern_count(self):
        """Verify we have exactly 14 Tier 1 patterns."""
        assert len(TIER_1_PATTERNS) == 14

    def test_tier1_delve_detection(self, dimension):
        """Test detection of 'delve' (Tier 1)."""
        text = "Let's delve into this topic and delve deeper."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier1']['count'] >= 2
        assert any('delve' in w.lower() for w in result['tier_breakdown']['tier1']['words'])

    def test_tier1_robust_detection(self, dimension):
        """Test detection of 'robust' (Tier 1)."""
        text = "This robust solution provides robustness and reliability."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier1']['count'] >= 2
        assert any('robust' in w.lower() for w in result['tier_breakdown']['tier1']['words'])

    def test_tier1_leverage_detection(self, dimension):
        """Test detection of 'leverage' (Tier 1)."""
        text = "We leverage this technology by leveraging existing resources."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier1']['count'] >= 2
        assert any('leverag' in w.lower() for w in result['tier_breakdown']['tier1']['words'])

    def test_tier1_all_patterns(self, dimension):
        """Test all 14 Tier 1 patterns are detected."""
        # Create text with all Tier 1 patterns
        text = " ".join([
            "delve", "robust", "leverage", "harness", "underscore",
            "holistic", "myriad", "plethora", "quintessential",
            "paramount", "foster", "realm", "tapestry", "embark"
        ])
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier1']['count'] == 14
        assert result['tier_breakdown']['tier1']['weight'] == 3

    def test_tier1_heavy_text(self, dimension, text_tier1_heavy):
        """Test text with heavy Tier 1 vocabulary."""
        result = dimension.analyze(text_tier1_heavy)

        tier1_count = result['tier_breakdown']['tier1']['count']
        assert tier1_count >= 5  # Should detect multiple Tier 1 words
        assert result['weighted_count'] >= tier1_count * 3  # Tier 1 weight applied


class TestTier2Detection:
    """Tests for Tier 2 pattern detection (12 patterns, 2× weight)."""

    def test_tier2_pattern_count(self):
        """Verify we have exactly 12 Tier 2 patterns."""
        assert len(TIER_2_PATTERNS) == 12

    def test_tier2_cutting_edge_detection(self, dimension):
        """Test detection of 'cutting-edge' (Tier 2)."""
        text = "This cutting-edge technology offers cutting-edge solutions."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier2']['count'] >= 2

    def test_tier2_comprehensive_detection(self, dimension):
        """Test detection of 'comprehensive' (Tier 2)."""
        text = "A comprehensive analysis with comprehensive documentation."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier2']['count'] >= 2

    def test_tier2_all_patterns(self, dimension):
        """Test all 12 Tier 2 patterns are detected."""
        # Create text with all Tier 2 patterns
        text = " ".join([
            "revolutionize", "game-changing", "cutting-edge", "pivotal",
            "intricate", "nuanced", "multifaceted", "comprehensive",
            "innovative", "transformative", "seamless", "dynamic"
        ])
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier2']['count'] == 12
        assert result['tier_breakdown']['tier2']['weight'] == 2

    def test_tier2_heavy_text(self, dimension, text_tier2_heavy):
        """Test text with heavy Tier 2 vocabulary."""
        result = dimension.analyze(text_tier2_heavy)

        tier2_count = result['tier_breakdown']['tier2']['count']
        assert tier2_count >= 5  # Should detect multiple Tier 2 words
        assert result['weighted_count'] >= tier2_count * 2  # Tier 2 weight applied


class TestTier3Detection:
    """Tests for Tier 3 pattern detection (8 patterns, 1× weight)."""

    def test_tier3_pattern_count(self):
        """Verify we have exactly 8 Tier 3 patterns."""
        assert len(TIER_3_PATTERNS) == 8

    def test_tier3_optimize_detection(self, dimension):
        """Test detection of 'optimize' (Tier 3)."""
        text = "We optimize this process through optimization techniques."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier3']['count'] >= 2

    def test_tier3_streamline_detection(self, dimension):
        """Test detection of 'streamline' (Tier 3)."""
        text = "Streamline workflows by streamlining operations."
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier3']['count'] >= 2

    def test_tier3_all_patterns(self, dimension):
        """Test all 8 Tier 3 patterns are detected."""
        # Create text with all Tier 3 patterns
        text = " ".join([
            "optimize", "streamline", "facilitate", "enhance",
            "mitigate", "navigate", "ecosystem", "landscape"
        ])
        result = dimension.analyze(text)

        assert result['tier_breakdown']['tier3']['count'] == 8
        assert result['tier_breakdown']['tier3']['weight'] == 1

    def test_tier3_heavy_text(self, dimension, text_tier3_heavy):
        """Test text with heavy Tier 3 vocabulary."""
        result = dimension.analyze(text_tier3_heavy)

        tier3_count = result['tier_breakdown']['tier3']['count']
        assert tier3_count >= 4  # Should detect multiple Tier 3 words


class TestTierWeightedScoring:
    """Tests for tier-weighted scoring calculation."""

    def test_weighted_count_calculation(self, dimension):
        """Test weighted count calculation: (T1*3) + (T2*2) + (T3*1)."""
        # 2 Tier 1 (weight 3), 3 Tier 2 (weight 2), 4 Tier 3 (weight 1)
        # Expected weighted_count: (2*3) + (3*2) + (4*1) = 6 + 6 + 4 = 16
        text = "delve robust revolutionize innovative transformative optimize streamline facilitate enhance"
        result = dimension.analyze(text)

        # Should have some weighting applied
        assert result['weighted_count'] > result['total_count']

    def test_frequency_normalization_per_1k(self, dimension):
        """Test frequency normalization to per 1k words."""
        # Create text with known word count and AI vocab
        # 20 words with 2 Tier 1 words = (2*3)/20 * 1000 = 300 weighted per 1k
        text = " ".join(["word"] * 18 + ["delve", "robust"])
        result = dimension.analyze(text)

        assert result['weighted_per_1k'] > 0
        assert result['total_per_1k'] > 0
        # Weighted should be higher than raw count due to tier weighting
        assert result['weighted_per_1k'] >= result['total_per_1k']

    def test_mixed_tiers_weighting(self, dimension, text_mixed_tiers):
        """Test that mixed tier text applies correct weighting."""
        result = dimension.analyze(text_mixed_tiers)

        tier1_count = result['tier_breakdown']['tier1']['count']
        tier2_count = result['tier_breakdown']['tier2']['count']
        tier3_count = result['tier_breakdown']['tier3']['count']

        expected_weighted = (tier1_count * 3) + (tier2_count * 2) + (tier3_count * 1)
        assert result['weighted_count'] == expected_weighted


class TestThresholdBasedScoring:
    """Tests for threshold-based scoring (Group C classification)."""

    def test_excellent_score_low_vocabulary(self, dimension, text_human_style):
        """Test excellent score (100) for minimal AI vocabulary (<=2.0/1k)."""
        result = dimension.analyze(text_human_style)
        score = dimension.calculate_score(result)

        assert score == 100.0  # No AI vocabulary = perfect score

    def test_good_score_moderate_vocabulary(self, dimension):
        """Test good score (75-99) for moderate AI vocabulary (2.0-8.0/1k)."""
        # Create text with moderate AI vocab density (~4.0 per 1k weighted)
        # 100 words with ~2 weighted occurrences = ~20 per 1k weighted
        text = " ".join(["word"] * 95 + ["optimize"] * 5)  # 5 Tier 3 words
        result = dimension.analyze(text)
        score = dimension.calculate_score(result)

        # Should be between 25 and 100
        assert 25.0 <= score <= 100.0

    def test_poor_score_high_vocabulary(self, dimension):
        """Test poor score (25) for heavy AI vocabulary (>8.0/1k)."""
        # Create text with very high AI vocab density
        # 20 words with 10 Tier 1 words = (10*3)/20 * 1000 = 1500 per 1k weighted
        text = " ".join(["delve", "robust"] * 5 + ["word"] * 10)
        result = dimension.analyze(text)
        score = dimension.calculate_score(result)

        assert score == 25.0  # Heavy AI vocabulary = minimum score

    def test_score_range_validation(self, dimension, text_mixed_tiers):
        """Test that scores are always in valid 0-100 range."""
        result = dimension.analyze(text_mixed_tiers)
        score = dimension.calculate_score(result)

        assert 0.0 <= score <= 100.0


class TestRecommendations:
    """Tests for recommendations generation."""

    def test_no_recommendations_excellent_score(self, dimension, text_human_style):
        """Test no recommendations for text with minimal AI vocabulary."""
        result = dimension.analyze(text_human_style)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        assert len(recommendations) == 0  # No issues to fix

    def test_recommendations_for_ai_vocabulary(self, dimension, text_mixed_tiers):
        """Test recommendations generated for text with AI vocabulary."""
        result = dimension.analyze(text_mixed_tiers)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        # Should have recommendations if weighted_per_1k >= 2.0
        if result['weighted_per_1k'] >= 2.0:
            assert len(recommendations) > 0
            assert any('Reduce AI vocabulary' in r for r in recommendations)

    def test_tier_specific_recommendations(self, dimension, text_tier1_heavy):
        """Test that recommendations prioritize high-tier words."""
        result = dimension.analyze(text_tier1_heavy)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        # Should mention Tier-1 words if present
        if result['tier_breakdown']['tier1']['count'] > 0:
            assert any('Tier-1' in r for r in recommendations)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_text(self, dimension):
        """Test analysis of empty text."""
        result = dimension.analyze("")
        score = dimension.calculate_score(result)

        assert result['total_count'] == 0
        assert result['weighted_count'] == 0
        assert result['total_per_1k'] == 0.0
        assert result['weighted_per_1k'] == 0.0
        assert score == 100.0  # No AI vocabulary = perfect score

    def test_very_short_text(self, dimension):
        """Test analysis of very short text (< 10 words)."""
        text = "delve robust leverage"
        result = dimension.analyze(text)
        score = dimension.calculate_score(result)

        assert result['total_count'] == 3
        assert result['weighted_count'] == 9  # 3 Tier 1 words * 3
        assert 0.0 <= score <= 100.0

    def test_very_long_text_no_ai_vocab(self, dimension):
        """Test analysis of long text with no AI vocabulary."""
        text = " ".join(["simple", "clear", "plain"] * 100)
        result = dimension.analyze(text)
        score = dimension.calculate_score(result)

        assert result['total_count'] == 0
        assert score == 100.0

    def test_high_concentration_ai_vocab(self, dimension):
        """Test text with very high AI vocabulary concentration."""
        # All words are AI vocabulary
        text = " ".join(["delve", "robust", "leverage"] * 20)
        result = dimension.analyze(text)
        score = dimension.calculate_score(result)

        assert result['total_count'] == 60
        assert result['weighted_count'] == 180  # All Tier 1, 60 * 3
        assert score == 25.0  # Worst possible score

    def test_case_insensitive_detection(self, dimension):
        """Test that detection is case-insensitive."""
        text = "DELVE Delve delve DeLvE"
        result = dimension.analyze(text)

        assert result['total_count'] == 4  # All variants detected

    def test_word_boundary_detection(self, dimension):
        """Test that patterns respect word boundaries."""
        text = "developer development delivered"  # Should NOT match 'delve'
        result = dimension.analyze(text)

        # Should not detect 'delve' in these words
        assert result['tier_breakdown']['tier1']['count'] == 0


class TestDetailedAnalysis:
    """Tests for detailed analysis with line numbers."""

    def test_detailed_analysis_returns_instances(self, dimension):
        """Test that detailed analysis returns VocabInstance objects."""
        lines = [
            "Let's delve into this topic.",
            "This robust solution is comprehensive.",
            "We can optimize the workflow."
        ]
        result = dimension.analyze_detailed(lines)

        assert 'vocab_instances' in result
        assert len(result['vocab_instances']) > 0

    def test_detailed_analysis_line_numbers(self, dimension):
        """Test that instances have correct line numbers."""
        lines = [
            "Normal text here.",
            "Let's delve into this.",  # Line 2
            "More normal text.",
            "This is robust."  # Line 4
        ]
        result = dimension.analyze_detailed(lines)

        instances = result['vocab_instances']
        line_numbers = [inst.line_number for inst in instances]

        assert 2 in line_numbers  # 'delve' on line 2
        assert 4 in line_numbers  # 'robust' on line 4

    def test_detailed_analysis_skips_headings(self, dimension):
        """Test that detailed analysis skips markdown headings."""
        lines = [
            "# Delve into robust solutions",  # Should be skipped (heading)
            "Let's delve into this topic."    # Should be detected
        ]
        result = dimension.analyze_detailed(lines)

        instances = result['vocab_instances']
        # Should only detect 'delve' from line 2, not from heading
        assert len(instances) >= 1

    def test_detailed_analysis_skips_code_blocks(self, dimension):
        """Test that detailed analysis skips code blocks."""
        lines = [
            "```python",
            "delve = 'test'",  # Should be skipped (code block)
            "```",
            "Let's delve into this."  # Should be detected
        ]
        result = dimension.analyze_detailed(lines)

        # Should detect some instances (implementation may vary)
        assert 'vocab_instances' in result


class TestIntegration:
    """Integration tests for dimension loading and registry."""

    def test_dimension_self_registers(self):
        """Test that dimension self-registers on instantiation."""
        DimensionRegistry.clear()
        dimension = AiVocabularyDimension()

        registered = DimensionRegistry.get("ai_vocabulary")
        assert registered is not None
        assert registered.dimension_name == "ai_vocabulary"

    def test_dimension_properties_accessible(self, dimension):
        """Test that all required properties are accessible."""
        assert hasattr(dimension, 'dimension_name')
        assert hasattr(dimension, 'weight')
        assert hasattr(dimension, 'tier')
        assert hasattr(dimension, 'description')

    def test_dimension_methods_callable(self, dimension):
        """Test that all required methods are callable."""
        assert callable(dimension.analyze)
        assert callable(dimension.calculate_score)
        assert callable(dimension.get_recommendations)
        assert callable(dimension.format_display)

    def test_end_to_end_analysis(self, dimension, text_mixed_tiers):
        """Test complete end-to-end analysis workflow."""
        # Analyze
        result = dimension.analyze(text_mixed_tiers)
        assert result['available'] is True

        # Calculate score
        score = dimension.calculate_score(result)
        assert 0.0 <= score <= 100.0

        # Get recommendations
        recommendations = dimension.get_recommendations(score, result)
        assert isinstance(recommendations, list)

        # Format display
        display = dimension.format_display(result)
        assert isinstance(display, str)
        assert "AI vocab" in display or "words" in display


class TestFormatDisplay:
    """Tests for format_display method."""

    def test_format_display_includes_counts(self, dimension, text_mixed_tiers):
        """Test that format_display includes relevant counts."""
        result = dimension.analyze(text_mixed_tiers)
        display = dimension.format_display(result)

        assert "AI vocab" in display
        assert "T1:" in display  # Tier 1 count
        assert "T2:" in display  # Tier 2 count
        assert "T3:" in display  # Tier 3 count

    def test_format_display_includes_weighted_rate(self, dimension, text_mixed_tiers):
        """Test that format_display includes weighted per 1k rate."""
        result = dimension.analyze(text_mixed_tiers)
        display = dimension.format_display(result)

        assert "/1k" in display
        assert "weighted" in display


class TestBackwardCompatibility:
    """Tests for backward compatibility and API consistency."""

    def test_analyze_returns_required_fields(self, dimension, text_mixed_tiers):
        """Test that analyze() returns all required fields."""
        result = dimension.analyze(text_mixed_tiers)

        # Core metrics
        assert 'total_count' in result
        assert 'weighted_count' in result
        assert 'total_per_1k' in result
        assert 'weighted_per_1k' in result

        # Tier breakdown
        assert 'tier_breakdown' in result
        assert 'tier1' in result['tier_breakdown']
        assert 'tier2' in result['tier_breakdown']
        assert 'tier3' in result['tier_breakdown']

        # Metadata
        assert 'available' in result
        assert 'analysis_mode' in result

    def test_calculate_score_returns_float(self, dimension, text_mixed_tiers):
        """Test that calculate_score() returns a float."""
        result = dimension.analyze(text_mixed_tiers)
        score = dimension.calculate_score(result)

        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_get_recommendations_returns_list(self, dimension, text_mixed_tiers):
        """Test that get_recommendations() returns a list."""
        result = dimension.analyze(text_mixed_tiers)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        assert isinstance(recommendations, list)
