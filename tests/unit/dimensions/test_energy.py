"""
Tests for EnergyDimension - writing dynamism and engagement analysis.
"""

import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.energy import EnergyDimension


@pytest.fixture
def analyzer():
    """Create EnergyDimension instance."""
    DimensionRegistry.clear()
    return EnergyDimension()


@pytest.fixture
def high_energy_text():
    """Text with high energy markers."""
    return """
    The team attacked the problem head-on. They seized every opportunity,
    smashed through obstacles, and conquered each challenge. Ideas exploded
    in the brainstorming session. Engineers raced to implement solutions.

    We launched the product. It transformed the market. Customers rushed
    to sign up. Sales rocketed past projections. The breakthrough was real.
    """


@pytest.fixture
def low_energy_text():
    """Text with low energy markers (AI-like)."""
    return """
    The methodology was implemented according to the framework. The system
    is designed to include various components. The process was being
    considered by the team. The approach seems to be appropriate.

    It appears that the concept has implications for the situation. The
    relationship between the factors was examined. The paradigm is
    characterized by certain properties. The nature of the phenomenon
    is being studied.
    """


@pytest.fixture
def mixed_energy_text():
    """Text with mixed energy levels."""
    return """
    We attacked the problem with a new approach. The methodology was refined
    and the team worked to understand the implications. Then we launched
    the solution.

    The framework appears to be effective. Results show improvement. We're
    racing to implement more features. The concept seems promising.
    """


class TestProperties:
    """Tests for dimension properties."""

    def test_dimension_name(self, analyzer):
        """Test dimension name property."""
        assert analyzer.dimension_name == "energy"

    def test_weight(self, analyzer):
        """Test weight property."""
        assert analyzer.weight == 5.0

    def test_tier(self, analyzer):
        """Test tier property."""
        from writescore.dimensions.base_strategy import DimensionTier

        assert analyzer.tier == DimensionTier.SUPPORTING

    def test_description(self, analyzer):
        """Test description property."""
        assert "dynamism" in analyzer.description.lower()


class TestAnalyze:
    """Tests for analyze method."""

    def test_analyze_returns_required_keys(self, analyzer, high_energy_text):
        """Test that analyze returns all required keys."""
        result = analyzer.analyze(high_energy_text)

        assert "energy" in result
        assert "available" in result
        assert result["available"] is True

        energy = result["energy"]
        assert "passive_ratio" in energy
        assert "dynamic_verb_ratio" in energy
        assert "abstract_ratio" in energy
        assert "power_word_density" in energy
        assert "rhythm_contrast" in energy

    def test_high_energy_text_has_low_passive_ratio(self, analyzer, high_energy_text):
        """Test that high energy text has low passive voice usage."""
        result = analyzer.analyze(high_energy_text)
        energy = result["energy"]

        # High energy text should have low passive ratio
        assert energy["passive_ratio"] < 0.3

    def test_low_energy_text_has_high_passive_ratio(self, analyzer, low_energy_text):
        """Test that low energy text has high passive voice usage."""
        result = analyzer.analyze(low_energy_text)
        energy = result["energy"]

        # Low energy text should have higher passive ratio
        assert energy["passive_ratio"] > 0.2

    def test_high_energy_text_has_dynamic_verbs(self, analyzer, high_energy_text):
        """Test that high energy text has dynamic verbs."""
        result = analyzer.analyze(high_energy_text)
        energy = result["energy"]

        # High energy text should have some dynamic verbs
        assert energy["dynamic_verb_count"] > 0
        assert energy["dynamic_verb_ratio"] > 0.05

    def test_low_energy_text_has_high_static_ratio(self, analyzer, low_energy_text):
        """Test that low energy text has high static verb ratio."""
        result = analyzer.analyze(low_energy_text)
        energy = result["energy"]

        # Low energy text should have high static verb ratio
        assert energy["static_verb_ratio"] > 0.3

    def test_low_energy_text_has_abstract_words(self, analyzer, low_energy_text):
        """Test that low energy text has abstract words."""
        result = analyzer.analyze(low_energy_text)
        energy = result["energy"]

        # Low energy text should have abstract words
        assert energy["abstract_count"] > 0
        assert energy["abstract_ratio"] > 0.02


class TestCalculateScore:
    """Tests for calculate_score method."""

    def test_score_range(self, analyzer, high_energy_text):
        """Test that score is in valid range."""
        metrics = analyzer.analyze(high_energy_text)
        score = analyzer.calculate_score(metrics)

        assert 0.0 <= score <= 100.0

    def test_high_energy_text_scores_higher(self, analyzer, high_energy_text, low_energy_text):
        """Test that high energy text scores higher than low energy text."""
        high_metrics = analyzer.analyze(high_energy_text)
        low_metrics = analyzer.analyze(low_energy_text)

        high_score = analyzer.calculate_score(high_metrics)
        low_score = analyzer.calculate_score(low_metrics)

        assert high_score > low_score

    def test_unavailable_metrics_return_neutral(self, analyzer):
        """Test that unavailable metrics return neutral score."""
        metrics = {"available": False}
        score = analyzer.calculate_score(metrics)

        assert score == 50.0


class TestGetRecommendations:
    """Tests for get_recommendations method."""

    def test_low_energy_gets_recommendations(self, analyzer, low_energy_text):
        """Test that low energy text gets recommendations."""
        metrics = analyzer.analyze(low_energy_text)
        score = analyzer.calculate_score(metrics)
        recommendations = analyzer.get_recommendations(score, metrics)

        assert len(recommendations) > 0

    def test_passive_voice_recommendation(self, analyzer, low_energy_text):
        """Test recommendation for passive voice."""
        metrics = analyzer.analyze(low_energy_text)
        score = analyzer.calculate_score(metrics)
        recommendations = analyzer.get_recommendations(score, metrics)

        # Should have recommendation about passive voice
        passive_recs = [r for r in recommendations if "passive" in r.lower()]
        assert len(passive_recs) > 0

    def test_abstract_language_recommendation(self, analyzer, low_energy_text):
        """Test recommendation for abstract language."""
        metrics = analyzer.analyze(low_energy_text)
        score = analyzer.calculate_score(metrics)
        recommendations = analyzer.get_recommendations(score, metrics)

        # Should have recommendation about abstract language
        abstract_recs = [r for r in recommendations if "abstract" in r.lower()]
        assert len(abstract_recs) > 0


class TestGetTiers:
    """Tests for get_tiers method."""

    def test_tiers_defined(self, analyzer):
        """Test that tiers are properly defined."""
        tiers = analyzer.get_tiers()

        assert "excellent" in tiers
        assert "good" in tiers
        assert "acceptable" in tiers
        assert "poor" in tiers

    def test_tier_ranges_valid(self, analyzer):
        """Test that tier ranges are valid."""
        tiers = analyzer.get_tiers()

        for _tier_name, (min_score, max_score) in tiers.items():
            assert min_score >= 0.0
            assert max_score <= 100.0
            assert min_score < max_score


class TestRhythmContrast:
    """Tests for rhythm contrast calculation."""

    def test_rhythm_contrast_varies(self, analyzer):
        """Test that varied sentence lengths produce higher contrast."""
        # Text with varied sentence lengths
        varied = "Short. This is a much longer sentence with many more words. Tiny. Another very long sentence here."

        # Text with uniform sentence lengths
        uniform = "This is normal. That is normal. Here is normal. There is normal."

        varied_result = analyzer.analyze(varied)
        uniform_result = analyzer.analyze(uniform)

        # Varied text should have higher rhythm contrast
        assert (
            varied_result["energy"]["rhythm_contrast"] > uniform_result["energy"]["rhythm_contrast"]
        )

    def test_single_sentence_returns_zero(self, analyzer):
        """Test that single sentence returns zero contrast."""
        single = "This is just one sentence."
        result = analyzer.analyze(single)

        assert result["energy"]["rhythm_contrast"] == 0.0


class TestRegistration:
    """Tests for dimension registration."""

    def test_self_registers(self):
        """Test that dimension self-registers on instantiation."""
        DimensionRegistry.clear()
        dim = EnergyDimension()

        registered = DimensionRegistry.get("energy")
        assert registered is dim

    def test_backward_compat_alias(self):
        """Test backward compatibility alias."""
        from writescore.dimensions.energy import EnergyAnalyzer

        assert EnergyAnalyzer is EnergyDimension
