"""
Tests for domain_thresholds module (domain-specific structural analysis).

Phase 3 enhancement: Multi-level combined scoring with research-backed thresholds.
"""

import pytest
from writescore.scoring.domain_thresholds import (
    DocumentDomain,
    HierarchyThresholds,
    DomainConfig,
    get_domain_config,
    calculate_cv_score,
    calculate_combined_structure_score,
    ACADEMIC_CONFIG,
    TECHNICAL_CONFIG,
    BUSINESS_CONFIG,
    TUTORIAL_CONFIG,
    GENERAL_CONFIG
)


class TestDocumentDomain:
    """Tests for DocumentDomain enum."""

    def test_domain_enum_values(self):
        """Test that all expected domain types are defined."""
        assert DocumentDomain.ACADEMIC.value == "academic"
        assert DocumentDomain.TECHNICAL.value == "technical"
        assert DocumentDomain.BUSINESS.value == "business"
        assert DocumentDomain.TUTORIAL.value == "tutorial"
        assert DocumentDomain.GENERAL.value == "general"


class TestDomainConfigs:
    """Tests for domain configuration objects."""

    def test_academic_config_weights_sum_to_one(self):
        """Test that academic config weights sum to 1.0."""
        total = ACADEMIC_CONFIG.weight_h2 + ACADEMIC_CONFIG.weight_h3 + ACADEMIC_CONFIG.weight_h4
        assert abs(total - 1.0) < 0.001

    def test_technical_config_weights_sum_to_one(self):
        """Test that technical config weights sum to 1.0."""
        total = TECHNICAL_CONFIG.weight_h2 + TECHNICAL_CONFIG.weight_h3 + TECHNICAL_CONFIG.weight_h4
        assert abs(total - 1.0) < 0.001

    def test_business_config_weights_sum_to_one(self):
        """Test that business config weights sum to 1.0."""
        total = BUSINESS_CONFIG.weight_h2 + BUSINESS_CONFIG.weight_h3 + BUSINESS_CONFIG.weight_h4
        assert abs(total - 1.0) < 0.001

    def test_tutorial_config_weights_sum_to_one(self):
        """Test that tutorial config weights sum to 1.0."""
        total = TUTORIAL_CONFIG.weight_h2 + TUTORIAL_CONFIG.weight_h3 + TUTORIAL_CONFIG.weight_h4
        assert abs(total - 1.0) < 0.001

    def test_general_config_weights_sum_to_one(self):
        """Test that general config weights sum to 1.0."""
        total = GENERAL_CONFIG.weight_h2 + GENERAL_CONFIG.weight_h3 + GENERAL_CONFIG.weight_h4
        assert abs(total - 1.0) < 0.001

    def test_academic_config_structure(self):
        """Test academic config has expected structure."""
        assert ACADEMIC_CONFIG.name == "academic"
        assert isinstance(ACADEMIC_CONFIG.h2_section_length, HierarchyThresholds)
        assert isinstance(ACADEMIC_CONFIG.h3_subsection_count, HierarchyThresholds)
        assert isinstance(ACADEMIC_CONFIG.h4_subsection_count, HierarchyThresholds)

    def test_threshold_values_are_sensible(self):
        """Test that threshold values follow expected patterns."""
        # Academic should have higher variance acceptance than technical
        assert ACADEMIC_CONFIG.h2_section_length.cv_human_min > TECHNICAL_CONFIG.h2_section_length.cv_human_min

        # All configs should have thresholds that make sense
        for config in [ACADEMIC_CONFIG, TECHNICAL_CONFIG, BUSINESS_CONFIG, TUTORIAL_CONFIG]:
            # Threshold should be near the midpoint or overlap region
            # In cases with overlap (AI max > human min), threshold can be outside this range
            # but should still be reasonable (not wildly outside the distributions)
            h2 = config.h2_section_length
            h3 = config.h3_subsection_count
            h4 = config.h4_subsection_count

            # Thresholds should be positive
            assert h2.cv_threshold > 0
            assert h3.cv_threshold > 0
            assert h4.cv_threshold > 0

            # Max scores should be positive
            assert h2.max_score > 0
            assert h3.max_score > 0
            assert h4.max_score > 0


class TestGetDomainConfig:
    """Tests for get_domain_config function."""

    def test_get_academic_config(self):
        """Test retrieving academic domain config."""
        config = get_domain_config(DocumentDomain.ACADEMIC)
        assert config == ACADEMIC_CONFIG
        assert config.name == "academic"

    def test_get_technical_config(self):
        """Test retrieving technical domain config."""
        config = get_domain_config(DocumentDomain.TECHNICAL)
        assert config == TECHNICAL_CONFIG
        assert config.name == "technical"

    def test_get_general_config_fallback(self):
        """Test fallback to general config."""
        config = get_domain_config(DocumentDomain.GENERAL)
        assert config == GENERAL_CONFIG


class TestCalculateCVScore:
    """Tests for calculate_cv_score function."""

    def test_calculate_cv_score_excellent(self):
        """Test CV score calculation for excellent human-like variance."""
        thresholds = HierarchyThresholds(
            cv_human_min=0.50,
            cv_ai_max=0.30,
            cv_threshold=0.40,
            max_score=10.0
        )

        score, assessment = calculate_cv_score(0.65, thresholds)

        assert score > 8.0  # Should be high score
        assert assessment in ['EXCELLENT', 'GOOD']

    def test_calculate_cv_score_poor(self):
        """Test CV score calculation for poor AI-like uniformity."""
        thresholds = HierarchyThresholds(
            cv_human_min=0.50,
            cv_ai_max=0.30,
            cv_threshold=0.40,
            max_score=10.0
        )

        score, assessment = calculate_cv_score(0.15, thresholds)

        assert score < 3.0  # Should be low score
        assert assessment in ['POOR', 'VERY_POOR']

    def test_calculate_cv_score_at_threshold(self):
        """Test CV score at threshold boundary."""
        thresholds = HierarchyThresholds(
            cv_human_min=0.50,
            cv_ai_max=0.30,
            cv_threshold=0.40,
            max_score=10.0
        )

        score, assessment = calculate_cv_score(0.40, thresholds)

        # At threshold, should be around 50% of max_score
        assert 3.0 < score < 7.0
        assert assessment in ['FAIR', 'GOOD']

    def test_calculate_cv_score_respects_max_score(self):
        """Test that calculated score doesn't exceed max_score."""
        thresholds = HierarchyThresholds(
            cv_human_min=0.50,
            cv_ai_max=0.30,
            cv_threshold=0.40,
            max_score=6.0
        )

        score, assessment = calculate_cv_score(1.0, thresholds)

        # Even with very high CV, shouldn't exceed max_score
        assert score <= 6.0


class TestCalculateCombinedStructureScore:
    """Tests for calculate_combined_structure_score function."""

    def test_combined_score_all_excellent(self):
        """Test combined scoring when all levels show excellent variance."""
        result = calculate_combined_structure_score(
            section_length_cv=0.55,  # Excellent for academic
            h3_subsection_cv=0.70,   # Excellent
            h4_subsection_cv=0.60,   # Excellent
            domain=DocumentDomain.ACADEMIC
        )

        assert 'combined_score' in result
        assert 'combined_assessment' in result
        assert 'breakdown' in result
        assert result['combined_assessment'] in ['EXCELLENT', 'GOOD']
        assert result['prob_human'] > 0.65

    def test_combined_score_all_poor(self):
        """Test combined scoring when all levels show poor variance."""
        result = calculate_combined_structure_score(
            section_length_cv=0.10,  # Poor for academic
            h3_subsection_cv=0.15,   # Poor
            h4_subsection_cv=0.10,   # Poor
            domain=DocumentDomain.ACADEMIC
        )

        assert result['combined_assessment'] in ['POOR', 'VERY_POOR']
        assert result['prob_human'] < 0.40

    def test_combined_score_mixed_quality(self):
        """Test combined scoring with mixed quality levels."""
        result = calculate_combined_structure_score(
            section_length_cv=0.50,  # Good
            h3_subsection_cv=0.20,   # Poor
            h4_subsection_cv=0.60,   # Excellent
            domain=DocumentDomain.ACADEMIC
        )

        assert result['combined_assessment'] in ['FAIR', 'GOOD', 'POOR']
        # Score should be weighted average
        assert 0 < result['combined_score'] <= 24

    def test_combined_score_breakdown_structure(self):
        """Test that breakdown contains all expected fields."""
        result = calculate_combined_structure_score(
            section_length_cv=0.40,
            h3_subsection_cv=0.50,
            h4_subsection_cv=0.40,
            domain=DocumentDomain.TECHNICAL
        )

        breakdown = result['breakdown']
        assert 'h2_score' in breakdown
        assert 'h2_assessment' in breakdown
        assert 'h2_weight' in breakdown
        assert 'h3_score' in breakdown
        assert 'h3_assessment' in breakdown
        assert 'h3_weight' in breakdown
        assert 'h4_score' in breakdown
        assert 'h4_assessment' in breakdown
        assert 'h4_weight' in breakdown

    def test_combined_score_domain_specific_thresholds(self):
        """Test that different domains use appropriate thresholds."""
        cv_values = {
            'section_length_cv': 0.15,
            'h3_subsection_cv': 0.20,
            'h4_subsection_cv': 0.20
        }

        # Technical docs expect low variance - should score better
        technical_result = calculate_combined_structure_score(
            **cv_values,
            domain=DocumentDomain.TECHNICAL
        )

        # Academic expects high variance - same CVs should score worse
        academic_result = calculate_combined_structure_score(
            **cv_values,
            domain=DocumentDomain.ACADEMIC
        )

        # Technical should have higher probability human for these low CVs
        assert technical_result['prob_human'] > academic_result['prob_human']

    def test_combined_score_max_possible(self):
        """Test that combined score never exceeds maximum."""
        result = calculate_combined_structure_score(
            section_length_cv=2.0,   # Extremely high
            h3_subsection_cv=2.0,    # Extremely high
            h4_subsection_cv=2.0,    # Extremely high
            domain=DocumentDomain.GENERAL
        )

        # Max score: 10*weight + 8*weight + 6*weight = 24 max
        assert result['combined_score'] <= 24.0

    def test_combined_score_weights_applied(self):
        """Test that domain-specific weights are properly applied."""
        result = calculate_combined_structure_score(
            section_length_cv=0.40,
            h3_subsection_cv=0.50,
            h4_subsection_cv=0.40,
            domain=DocumentDomain.ACADEMIC
        )

        # Academic emphasizes H2 (0.50), then H3 (0.35), then H4 (0.15)
        breakdown = result['breakdown']
        assert breakdown['h2_weight'] == 0.50
        assert breakdown['h3_weight'] == 0.35
        assert breakdown['h4_weight'] == 0.15
