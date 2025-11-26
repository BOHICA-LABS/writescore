"""
Unit tests for PredictabilityDimension analysis modes.

Tests FAST, ADAPTIVE, SAMPLING, and FULL modes for GLTR analysis.
Story 1.4.7: Enable Full Document GLTR Analysis
"""

import pytest

from writescore.core.analysis_config import AnalysisConfig, AnalysisMode
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.predictability import PredictabilityDimension


@pytest.fixture
def dim():
    """Create PredictabilityDimension instance with clean registry and model cache."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    # Clear GLTR model cache to ensure fresh model state for each test
    PredictabilityDimension.clear_model_cache()
    return PredictabilityDimension()


class TestDataHelpers:
    """Helper methods for generating test data."""

    @staticmethod
    def _load_sample_chapter() -> str:
        """Generate ~180k char test text (90 pages × 2000 chars/page)."""
        # Use repetitive but varied text
        sentences = [
            "The industrial control system monitors critical infrastructure.",
            "Security operations require continuous vigilance and analysis.",
            "Data patterns reveal insights into system behavior.",
            "Automated detection helps identify potential anomalies.",
        ]
        # 90 pages × 2000 chars/page = 180k chars
        # Each sentence ~60 chars, need ~3000 repetitions
        return " ".join(sentences * 750)  # ~180k chars

    @staticmethod
    def _load_known_ai_text() -> str:
        """Known AI-generated text with expected GLTR ~0.70-0.75."""
        # Highly predictable, repetitive AI-like text
        return """Artificial intelligence represents a transformative paradigm shift
        in computational methodology. It is important to note that machine learning
        algorithms leverage statistical patterns to optimize predictive accuracy.
        Furthermore, deep learning architectures utilize hierarchical representations
        to extract meaningful features from complex datasets. In conclusion, AI systems
        demonstrate remarkable capabilities across diverse application domains.""" * 100

    @staticmethod
    def _load_known_human_text() -> str:
        """Known human text with expected GLTR ~0.45-0.55."""
        # Large collection of unique, natural human sentences (no repetition)
        sentences = [
            "I stumbled upon this old notebook yesterday—pages yellowed, ink fading in spots.",
            "Mom's handwriting is unmistakable.",
            "The cat knocked over my coffee this morning.",
            "Third time this week, honestly.",
            "I'm starting to think it's personal.",
            "Sometimes I wonder what happened to that hiking trail we used to take.",
            "Probably overgrown by now.",
            "My neighbor just got a new dog.",
            "Barks at literally everything.",
            "Even the wind sets it off.",
            "I need to fix that squeaky door hinge.",
            "Been saying that for three months now.",
            "Found an old mixtape in the garage.",
            "No idea what's on it—player's been broken for years.",
            "The grocery store moved the cereal aisle again.",
            "Why do they keep doing that?",
            "I should probably water those plants.",
            "They're looking a bit droopy.",
            "My uncle tells the same three stories at every family gathering.",
            "We all know them by heart now.",
            "There's a weird stain on the ceiling.",
            "Not sure I want to know how it got there.",
            "Left my keys somewhere again.",
            "Checked the usual spots—nothing.",
            "They'll turn up eventually.",
            "The dishwasher's making that noise again.",
            "Guess I'll just ignore it.",
            "Rain finally stopped after four days straight.",
            "Everything's soggy and miserable outside.",
            "My sister called about Thanksgiving plans.",
            "Same debate as last year.",
            "Someone parked in my spot again.",
            "Left a note, but who knows if they'll see it.",
            "The book I ordered still hasn't arrived.",
            "Been two weeks already.",
            "Maybe I should just buy it locally.",
            "Tried that new restaurant downtown.",
            "Food was decent, service was slow.",
            "Probably won't go back though.",
            "My phone battery dies so fast now.",
            "Needs charging twice a day at this point.",
            "Remember when it lasted all day?",
            "Those were the days.",
            "The neighbor's kid is learning trumpet.",
            "It's... not going well.",
            "Earplugs are becoming essential.",
            "I miss the old coffee shop that closed down.",
            "New place just isn't the same.",
            "Coffee tastes different somehow.",
            "Found an old photo album in the closet.",
            "Half the people I don't even recognize anymore.",
            "Time does weird things to memory.",
            "The washing machine is off-balance again.",
            "Sounds like a helicopter taking off.",
            "Need to redistribute the load, I guess.",
            "Traffic was ridiculous this morning.",
            "Took forty minutes for what's usually fifteen.",
            "No idea what the holdup was.",
            "My watch stopped working last Tuesday.",
            "Battery's dead and I keep forgetting to replace it.",
            "Been checking my phone for the time instead.",
            "The mailman delivered someone else's package again.",
            "Wrong address, wrong name, wrong everything.",
            "Happens more often than you'd think.",
            "I can't remember the last time I used that blender.",
            "Just sits there taking up counter space.",
            "Should probably donate it or something.",
            "My computer's acting weird lately.",
            "Freezes randomly, no pattern to it.",
            "Probably time for an update I've been avoiding.",
            "The parking meter ate my quarters.",
            "Didn't even register the payment.",
            "Of course a cop showed up five minutes later.",
            "Started reading that book everyone recommended.",
            "Fifty pages in and I'm not feeling it.",
            "Maybe it gets better?",
            "The lightbulb in the hallway finally died.",
            "Been flickering for weeks.",
            "Guess I have to change it now.",
            "Someone left their shopping cart in the parking spot next to mine.",
            "Right up against my door.",
            "Had to climb in from the passenger side.",
            "My coworker microwaved fish again.",
            "The whole office smells terrible.",
            "How is this still happening?",
            "The remote control disappeared into the couch cushions.",
            "It's like the Bermuda Triangle in there.",
            "Gave up and used my phone instead.",
        ]
        return " ".join(sentences)


class TestPredictabilityModes:
    """Test PredictabilityDimension with different analysis modes."""

    def test_fast_mode_truncates_to_2000(self, dim):
        """Test FAST mode maintains 2000-char truncation."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        long_text = "word " * 50000  # 250k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'fast'
        assert result['samples_analyzed'] == 1
        assert result['analyzed_text_length'] <= 2000

    def test_adaptive_mode_samples_long_documents(self, dim):
        """Test ADAPTIVE mode samples 90-page chapters."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        chapter_text = "word " * 36000  # ~180k chars (90 pages)
        result = dim.analyze(chapter_text, config=config)

        assert result['analysis_mode'] == 'adaptive'
        assert result['samples_analyzed'] >= 5  # Should sample
        assert result['total_text_length'] == len(chapter_text)
        assert result['coverage_percentage'] > 5.0  # >5% analyzed

    def test_full_mode_analyzes_entire_document(self, dim):
        """Test FULL mode processes entire text."""
        config = AnalysisConfig(mode=AnalysisMode.FULL)

        long_text = "word " * 10000  # ~50k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'full'
        assert result['analyzed_text_length'] == result['total_text_length']
        assert result['coverage_percentage'] == 100.0

    @pytest.mark.slow
    def test_sampling_mode_uses_configured_samples(self, dim):
        """Test SAMPLING mode respects sample configuration."""
        config = AnalysisConfig(
            mode=AnalysisMode.SAMPLING,
            sampling_sections=7,
            sampling_chars_per_section=3000
        )

        long_text = "word " * 50000  # 250k chars
        result = dim.analyze(long_text, config=config)

        assert result['analysis_mode'] == 'sampling'
        assert result['samples_analyzed'] == 7
        # Each sample ~3000 chars, so total ~21k analyzed
        assert 18000 <= result['analyzed_text_length'] <= 24000

    def test_aggregate_gltr_metrics_calculates_mean(self, dim):
        """Test GLTR aggregation uses mean."""
        samples = [
            {'gltr_top10_percentage': 0.50, 'gltr_mean_rank': 40.0, 'gltr_top100_percentage': 0.80, 'gltr_top1000_percentage': 0.95, 'gltr_rank_variance': 100.0, 'gltr_likelihood': 0.5},
            {'gltr_top10_percentage': 0.60, 'gltr_mean_rank': 50.0, 'gltr_top100_percentage': 0.85, 'gltr_top1000_percentage': 0.96, 'gltr_rank_variance': 120.0, 'gltr_likelihood': 0.6},
            {'gltr_top10_percentage': 0.70, 'gltr_mean_rank': 60.0, 'gltr_top100_percentage': 0.90, 'gltr_top1000_percentage': 0.97, 'gltr_rank_variance': 140.0, 'gltr_likelihood': 0.7}
        ]

        result = dim._aggregate_gltr_metrics(samples)

        assert result['gltr_top10_percentage'] == 0.60  # Mean
        assert result['gltr_mean_rank'] == 50.0  # Mean
        assert result['gltr_top100_percentage'] == 0.85  # Mean
        assert result['gltr_top1000_percentage'] == pytest.approx(0.96, abs=0.01)  # Mean
        assert result['gltr_rank_variance'] == 120.0  # Mean
        assert result['gltr_likelihood'] == pytest.approx(0.6, abs=0.01)  # Mean

    def test_metadata_included_in_results(self, dim):
        """Test analysis metadata is included in results."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        text = "This is a test text with some content. " * 100
        result = dim.analyze(text, config=config)

        # Check metadata fields
        assert 'analysis_mode' in result
        assert 'samples_analyzed' in result
        assert 'total_text_length' in result
        assert 'analyzed_text_length' in result
        assert 'coverage_percentage' in result
        assert result['total_text_length'] == len(text)

    def test_short_text_uses_full_analysis(self, dim):
        """Test short text (<5k chars) gets full analysis even in ADAPTIVE mode."""
        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        short_text = "word " * 500  # ~2.5k chars
        result = dim.analyze(short_text, config=config)

        # ADAPTIVE mode on short text should analyze fully
        assert result['samples_analyzed'] == 1
        assert result['coverage_percentage'] == 100.0

    def test_empty_text_handles_gracefully(self, dim):
        """Test empty text doesn't crash."""
        config = AnalysisConfig(mode=AnalysisMode.FAST)

        result = dim.analyze("", config=config)

        assert 'available' in result
        assert result['total_text_length'] == 0

    def test_default_config_uses_adaptive(self, dim):
        """Test None config defaults to ADAPTIVE mode."""
        text = "word " * 10000  # 50k chars
        result = dim.analyze(text, config=None)

        # DEFAULT_CONFIG uses ADAPTIVE mode
        assert result['analysis_mode'] == 'adaptive'
