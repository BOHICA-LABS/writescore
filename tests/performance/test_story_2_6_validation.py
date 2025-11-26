"""
Performance validation for Story 2.6: Expanded Pragmatic Markers Lexicon.

Tests:
1. Analysis time < 2s per 1000 words
2. AI/Human score separation maintained (comparative validation)
3. Pattern detection accuracy across expanded lexicon
4. New category (attitude markers, likelihood adverbials) detection

Run with: pytest tests/performance/test_story_2_6_validation.py -v
"""

import json
import time
import statistics
from pathlib import Path
import pytest

from writescore.dimensions.pragmatic_markers import PragmaticMarkersDimension


class TestStory26PerformanceValidation:
    """Performance validation tests for Story 2.6."""

    @pytest.fixture
    def dimension(self):
        """Create fresh dimension instance."""
        return PragmaticMarkersDimension()

    @pytest.fixture
    def regression_corpus(self):
        """Load regression test corpus."""
        corpus_path = Path(__file__).parent.parent / "fixtures" / "regression_corpus.json"
        with open(corpus_path) as f:
            return json.load(f)

    @pytest.fixture
    def human_text(self):
        """Load human-written sample text."""
        text_path = Path(__file__).parent.parent / "fixtures" / "sample_human_text.md"
        return text_path.read_text()

    @pytest.fixture
    def ai_text(self):
        """Load AI-generated sample text."""
        text_path = Path(__file__).parent.parent / "fixtures" / "sample_ai_text.md"
        return text_path.read_text()

    # =========================================================================
    # Performance Tests - AC2 Requirement: Analysis time < 2s per 1000 words
    # =========================================================================

    def test_analysis_time_requirement(self, dimension, human_text, ai_text):
        """Test that analysis completes in < 2s per 1000 words."""
        # Test on combined human + AI text
        combined_text = human_text + "\n\n" + ai_text
        word_count = len(combined_text.split())

        # Run analysis and measure time
        start_time = time.perf_counter()
        result = dimension.analyze(combined_text)
        end_time = time.perf_counter()

        elapsed_time = end_time - start_time
        time_per_1k = (elapsed_time / word_count) * 1000

        # Requirement: < 2s per 1000 words
        assert time_per_1k < 2.0, f"Analysis took {time_per_1k:.3f}s per 1k words (limit: 2.0s)"
        print(f"\n✓ Analysis time: {time_per_1k:.4f}s per 1k words (limit: 2.0s)")

    def test_bulk_analysis_performance(self, dimension, regression_corpus):
        """Test bulk analysis performance across all corpus samples."""
        samples = regression_corpus['samples']

        times = []
        word_counts = []

        for sample in samples:
            text = sample['text']
            word_count = len(text.split())
            word_counts.append(word_count)

            start_time = time.perf_counter()
            result = dimension.analyze(text)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        total_words = sum(word_counts)
        total_time = sum(times)
        time_per_1k = (total_time / total_words) * 1000 if total_words > 0 else 0

        # Requirement: < 2s per 1000 words
        assert time_per_1k < 2.0, f"Bulk analysis: {time_per_1k:.3f}s per 1k words"

        print(f"\n✓ Bulk analysis ({len(samples)} samples, {total_words} words)")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Time per 1k words: {time_per_1k:.4f}s")
        print(f"  Mean per sample: {statistics.mean(times)*1000:.2f}ms")

    # =========================================================================
    # Comparative Validation - AI/Human Score Separation
    # =========================================================================

    def test_ai_human_score_separation(self, dimension, regression_corpus):
        """Test that AI and human samples maintain score separation."""
        samples = regression_corpus['samples']

        ai_scores = []
        human_scores = []

        for sample in samples:
            text = sample['text']
            category = sample['category']

            result = dimension.analyze(text)
            score = dimension.calculate_score(result)

            if category == 'ai_generated':
                ai_scores.append(score)
            elif category == 'human_written':
                human_scores.append(score)

        # Calculate statistics
        ai_mean = statistics.mean(ai_scores)
        human_mean = statistics.mean(human_scores)
        separation = human_mean - ai_mean

        # Requirement: Human scores should be higher than AI scores
        # With expanded lexicon, we expect better separation
        assert human_mean > ai_mean, f"Human mean ({human_mean:.1f}) should exceed AI mean ({ai_mean:.1f})"

        print(f"\n✓ AI/Human Score Separation Analysis")
        print(f"  AI samples (n={len(ai_scores)}): mean={ai_mean:.1f}, std={statistics.stdev(ai_scores):.1f}")
        print(f"  Human samples (n={len(human_scores)}): mean={human_mean:.1f}, std={statistics.stdev(human_scores):.1f}")
        print(f"  Separation: {separation:.1f} points")

    def test_full_document_separation(self, dimension, human_text, ai_text):
        """Test score separation on full document samples."""
        human_result = dimension.analyze(human_text)
        ai_result = dimension.analyze(ai_text)

        human_score = dimension.calculate_score(human_result)
        ai_score = dimension.calculate_score(ai_result)

        # Human document should score higher (more human-like)
        assert human_score > ai_score, f"Human ({human_score:.1f}) should exceed AI ({ai_score:.1f})"

        print(f"\n✓ Full Document Score Comparison")
        print(f"  Human document: {human_score:.1f}")
        print(f"  AI document: {ai_score:.1f}")
        print(f"  Separation: {human_score - ai_score:.1f} points")

    # =========================================================================
    # Pattern Detection Validation
    # =========================================================================

    def test_expanded_pattern_count(self, dimension):
        """Verify 126 patterns implemented (Story 2.6 AC1)."""
        total_patterns = (
            len(dimension.EPISTEMIC_HEDGES) +
            len(dimension.FREQUENCY_HEDGES) +
            len(dimension.EPISTEMIC_VERBS) +
            len(dimension.STRONG_CERTAINTY) +
            len(dimension.SUBJECTIVE_CERTAINTY) +
            len(dimension.ASSERTION_ACTS) +
            len(dimension.FORMULAIC_AI_ACTS) +
            len(dimension.ATTITUDE_MARKERS) +
            len(dimension.LIKELIHOOD_ADVERBIALS)
        )

        assert total_patterns == 126, f"Expected 126 patterns, found {total_patterns}"

        print(f"\n✓ Pattern Count Validation")
        print(f"  EPISTEMIC_HEDGES: {len(dimension.EPISTEMIC_HEDGES)}")
        print(f"  FREQUENCY_HEDGES: {len(dimension.FREQUENCY_HEDGES)}")
        print(f"  EPISTEMIC_VERBS: {len(dimension.EPISTEMIC_VERBS)}")
        print(f"  STRONG_CERTAINTY: {len(dimension.STRONG_CERTAINTY)}")
        print(f"  SUBJECTIVE_CERTAINTY: {len(dimension.SUBJECTIVE_CERTAINTY)}")
        print(f"  ASSERTION_ACTS: {len(dimension.ASSERTION_ACTS)}")
        print(f"  FORMULAIC_AI_ACTS: {len(dimension.FORMULAIC_AI_ACTS)}")
        print(f"  ATTITUDE_MARKERS: {len(dimension.ATTITUDE_MARKERS)}")
        print(f"  LIKELIHOOD_ADVERBIALS: {len(dimension.LIKELIHOOD_ADVERBIALS)}")
        print(f"  TOTAL: {total_patterns}")

    def test_new_categories_detection(self, dimension):
        """Test detection of new Story 2.6 categories."""
        # Text with attitude markers and likelihood adverbials
        test_text = """
        Surprisingly, the results were better than expected. Unfortunately,
        the timeline was aggressive. Importantly, we delivered on time.

        The data probably indicates a trend. Apparently, users prefer simplicity.
        Seemingly, the approach worked. Arguably, this is the best method.
        """

        result = dimension.analyze(test_text)

        # Verify new categories detected
        assert 'attitude_markers' in result
        assert 'likelihood_adverbials' in result

        attitude = result['attitude_markers']
        likelihood = result['likelihood_adverbials']

        assert attitude['total_count'] >= 3, f"Expected 3+ attitude markers, found {attitude['total_count']}"
        assert likelihood['total_count'] >= 4, f"Expected 4+ likelihood adverbials, found {likelihood['total_count']}"

        print(f"\n✓ New Category Detection")
        print(f"  Attitude markers: {attitude['total_count']} detected")
        print(f"  Likelihood adverbials: {likelihood['total_count']} detected")

    def test_expanded_hedging_patterns(self, dimension):
        """Test detection of expanded epistemic hedge patterns."""
        test_text = """
        This would indicate a problem. We should consider alternatives.
        It seems likely that the approach is correct. The data appears valid.
        I believe this is accurate. We think this method works.

        The results are possible but uncertain. It's unclear whether this applies.
        The sample is nearly complete, essentially finished.
        In general, we typically see this pattern. Usually, it works.
        """

        result = dimension.analyze(test_text)
        hedging = result['hedging']

        # Story 2.6 new patterns should be detected
        counts = hedging['counts_by_type']

        # Check for new modal hedges
        assert counts.get('would', 0) >= 1, "Modal hedge 'would' not detected"
        assert counts.get('should', 0) >= 1, "Modal hedge 'should' not detected"

        # Check for new lexical verb hedges
        assert counts.get('seem', 0) >= 1 or counts.get('it_seems', 0) >= 1, "Lexical verb 'seem/seems' not detected"
        assert counts.get('believe', 0) >= 1, "Epistemic verb 'believe' not detected"

        # Check for new approximators
        assert counts.get('typically', 0) >= 1, "Approximator 'typically' not detected"
        assert counts.get('usually', 0) >= 1, "Approximator 'usually' not detected"

        print(f"\n✓ Expanded Hedging Pattern Detection")
        print(f"  Total hedge count: {hedging['total_count']}")
        print(f"  Per 1k words: {hedging['per_1k']:.2f}")
        print(f"  Variety score: {hedging['variety_score']:.3f}")


class TestStory26ValidationReport:
    """Generate comprehensive validation report."""

    @pytest.fixture
    def dimension(self):
        return PragmaticMarkersDimension()

    @pytest.fixture
    def regression_corpus(self):
        corpus_path = Path(__file__).parent.parent / "fixtures" / "regression_corpus.json"
        with open(corpus_path) as f:
            return json.load(f)

    @pytest.fixture
    def human_text(self):
        text_path = Path(__file__).parent.parent / "fixtures" / "sample_human_text.md"
        return text_path.read_text()

    @pytest.fixture
    def ai_text(self):
        text_path = Path(__file__).parent.parent / "fixtures" / "sample_ai_text.md"
        return text_path.read_text()

    def test_generate_validation_report(self, dimension, regression_corpus, human_text, ai_text):
        """Generate comprehensive validation report for Story 2.6."""
        print("\n" + "="*70)
        print("STORY 2.6 PERFORMANCE VALIDATION REPORT")
        print("="*70)

        # 1. Pattern Count Validation
        print("\n--- PATTERN COUNT VALIDATION (AC1) ---")
        total_patterns = (
            len(dimension.EPISTEMIC_HEDGES) +
            len(dimension.FREQUENCY_HEDGES) +
            len(dimension.EPISTEMIC_VERBS) +
            len(dimension.STRONG_CERTAINTY) +
            len(dimension.SUBJECTIVE_CERTAINTY) +
            len(dimension.ASSERTION_ACTS) +
            len(dimension.FORMULAIC_AI_ACTS) +
            len(dimension.ATTITUDE_MARKERS) +
            len(dimension.LIKELIHOOD_ADVERBIALS)
        )
        status = "✓ PASS" if total_patterns == 126 else "✗ FAIL"
        print(f"Total patterns: {total_patterns}/126 {status}")

        # 2. Performance Validation (AC2)
        print("\n--- PERFORMANCE VALIDATION (AC2) ---")
        combined_text = human_text + "\n\n" + ai_text
        word_count = len(combined_text.split())

        start_time = time.perf_counter()
        result = dimension.analyze(combined_text)
        elapsed = time.perf_counter() - start_time

        time_per_1k = (elapsed / word_count) * 1000
        status = "✓ PASS" if time_per_1k < 2.0 else "✗ FAIL"
        print(f"Analysis time: {time_per_1k:.4f}s per 1k words (limit: 2.0s) {status}")

        # 3. Comparative Validation
        print("\n--- COMPARATIVE VALIDATION ---")
        samples = regression_corpus['samples']

        ai_scores = []
        human_scores = []
        ai_hedging = []
        human_hedging = []
        ai_certainty = []
        human_certainty = []

        for sample in samples:
            text = sample['text']
            category = sample['category']

            result = dimension.analyze(text)
            score = dimension.calculate_score(result)

            if category == 'ai_generated':
                ai_scores.append(score)
                ai_hedging.append(result['hedging']['per_1k'])
                ai_certainty.append(result['certainty']['per_1k'])
            elif category == 'human_written':
                human_scores.append(score)
                human_hedging.append(result['hedging']['per_1k'])
                human_certainty.append(result['certainty']['per_1k'])

        ai_mean = statistics.mean(ai_scores)
        human_mean = statistics.mean(human_scores)
        separation = human_mean - ai_mean

        print(f"AI samples (n={len(ai_scores)}):")
        print(f"  Score: mean={ai_mean:.1f}, std={statistics.stdev(ai_scores):.1f}")
        print(f"  Hedging/1k: mean={statistics.mean(ai_hedging):.1f}")
        print(f"  Certainty/1k: mean={statistics.mean(ai_certainty):.1f}")

        print(f"Human samples (n={len(human_scores)}):")
        print(f"  Score: mean={human_mean:.1f}, std={statistics.stdev(human_scores):.1f}")
        print(f"  Hedging/1k: mean={statistics.mean(human_hedging):.1f}")
        print(f"  Certainty/1k: mean={statistics.mean(human_certainty):.1f}")

        status = "✓ PASS" if human_mean > ai_mean else "✗ FAIL"
        print(f"Score separation: {separation:.1f} points {status}")

        # 4. New Category Detection
        print("\n--- NEW CATEGORY DETECTION (AC3) ---")
        test_text = """
        Surprisingly, the results exceeded expectations. Unfortunately,
        delays occurred. Importantly, we succeeded. Probably the best approach.
        Apparently, users agree. Seemingly effective. Arguably optimal.
        """
        result = dimension.analyze(test_text)

        attitude_count = result['attitude_markers']['total_count']
        likelihood_count = result['likelihood_adverbials']['total_count']

        print(f"Attitude markers detected: {attitude_count}")
        print(f"Likelihood adverbials detected: {likelihood_count}")

        # 5. Full Document Analysis
        print("\n--- FULL DOCUMENT ANALYSIS ---")
        human_result = dimension.analyze(human_text)
        ai_result = dimension.analyze(ai_text)

        human_score = dimension.calculate_score(human_result)
        ai_score = dimension.calculate_score(ai_result)

        print(f"Human document score: {human_score:.1f}")
        print(f"AI document score: {ai_score:.1f}")
        print(f"Separation: {human_score - ai_score:.1f} points")

        print("\n" + "="*70)
        print("VALIDATION COMPLETE")
        print("="*70)

        # Assert critical validations
        assert total_patterns == 126
        assert time_per_1k < 2.0
        assert human_mean > ai_mean


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
