"""
Tests for PragmaticMarkersDimension - Epistemic stance and pragmatic communication patterns.
Story 2.4.0.5 - Extracted from transition_marker.py.
Story 2.6 - Expanded from 52 to 126 patterns with new categories.
"""


import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.pragmatic_markers import PragmaticMarkersDimension


@pytest.fixture
def dimension():
    """Create PragmaticMarkersDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return PragmaticMarkersDimension()


@pytest.fixture
def text_with_high_hedging():
    """Text with excessive epistemic hedging (AI-like)."""
    return """
    It might possibly be the case that this could perhaps work. We may
    conceivably see some results if this potentially succeeds. It seems
    that this tends to indicate some possibilities. It appears that we
    might be able to suggest something here. This is likely to work.
    About five or almost ten items were found. Approximately three people
    came. Around four generally showed up. Roughly six largely agreed.
    """


@pytest.fixture
def text_with_frequency_hedges():
    """Text with frequency hedges."""
    return """
    This frequently happens in production. Users occasionally report issues.
    The system sometimes fails under load. We often see this pattern.
    Errors rarely occur in testing. Problems seldom manifest early.
    """


@pytest.fixture
def text_with_epistemic_verbs():
    """Text with epistemic verbs."""
    return """
    We assume this will work. Studies estimate the impact. Data indicates
    a trend. Experts speculate about causes. Researchers propose solutions.
    Authors claim benefits. Analysts argue for changes. Evidence suggests improvements.
    """


@pytest.fixture
def text_with_certainty():
    """Text with certainty markers."""
    return """
    This definitely works well. The solution certainly helps. Users absolutely
    love it. The system undoubtedly improves things. Results clearly show benefits.
    Performance obviously increases. I believe this is correct. I think we should
    proceed. We believe in this approach. In my view, it's the best option.
    """


@pytest.fixture
def text_with_speech_acts():
    """Text with speech act patterns."""
    return """
    I argue that this is important. We propose that changes are needed.
    This shows clear improvements. This demonstrates the value.
    It can be argued that benefits exist. One might argue that risks remain.
    It should be noted that testing matters. It is worth noting that quality counts.
    """


@pytest.fixture
def text_natural_balance():
    """Text with natural pragmatic balance (human-like) - genuinely natural writing."""
    return """
    Our team launched the new dashboard last quarter. The response from users has
    been positive. Login times dropped from twelve seconds to under three. Page
    load performance improved across all browsers. This shows the redesign worked.

    The navigation changes focused on simplifying user workflows. We moved the search bar
    to the header and consolidated the settings menu. Users found what they needed
    faster. Support tickets decreased by sixty percent.

    Development took four months from kickoff to launch. The backend team upgraded
    the database queries while frontend rebuilt the component library. We ran beta
    testing with fifty users for two weeks before the full rollout. I think this
    timeline was reasonable given the scope.

    A few bugs came up during the first week. The notification system sent duplicate
    emails to some users. We fixed that within twenty-four hours. The mobile view
    had layout issues on older Android devices. That took longer to resolve
    but we got it done.

    The analytics show engagement metrics trending upward. Users spend more time
    in the app and complete tasks without abandoning workflows. The redesign met
    its goals and the team learned valuable lessons.

    Next quarter we'll tackle the reporting module. It needs the same treatment
    this dashboard got. The data export features work but the interface can confuse
    people. Streamlining that workflow will help users get more value from their data.
    """


class TestDimensionMetadata:
    """Tests for dimension metadata and registration."""

    def test_dimension_name(self, dimension):
        """Test dimension name is 'pragmatic_markers'."""
        assert dimension.dimension_name == "pragmatic_markers"

    def test_dimension_weight(self, dimension):
        """Test dimension weight is 3.7% (rebalanced to 100% total)."""
        assert dimension.weight == 3.7

    def test_dimension_tier(self, dimension):
        """Test dimension tier is ADVANCED."""
        assert dimension.tier == "ADVANCED"

    def test_dimension_description(self, dimension):
        """Test dimension has meaningful description."""
        desc = dimension.description
        assert isinstance(desc, str)
        assert len(desc) > 20
        assert any(term in desc.lower() for term in ["marker", "hedge", "certainty", "epistemic", "pragmatic"])

    def test_dimension_registers_on_init(self):
        """Test dimension self-registers with registry on initialization."""
        DimensionRegistry.clear()
        dim = PragmaticMarkersDimension()

        registered = DimensionRegistry.get("pragmatic_markers")
        assert registered is dim


class TestPatternDetection:
    """Tests for pattern detection across all categories."""

    def test_epistemic_hedges_detection(self, dimension):
        """Test epistemic hedges are detected correctly."""
        text = "It might be possible. Perhaps we could try. It seems reasonable. It appears valid."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['total_count'] >= 4
        assert 'might' in hedging['counts_by_type']
        assert 'perhaps' in hedging['counts_by_type']
        assert 'it_seems' in hedging['counts_by_type']
        assert 'it_appears' in hedging['counts_by_type']

    def test_approximators_detection(self, dimension):
        """Test approximator patterns are detected."""
        text = "About five items. Almost ten people. Approximately three hours. Around four days. Roughly six months. Generally good. Largely successful."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['approximators_count'] >= 7
        assert hedging['counts_by_type']['about'] >= 1
        assert hedging['counts_by_type']['almost'] >= 1
        assert hedging['counts_by_type']['approximately'] >= 1

    def test_frequency_hedges_detection(self, dimension):
        """Test frequency hedges are detected."""
        text = "It frequently happens. Occasionally we see this. Sometimes it works. Often it fails. Rarely does it crash. Seldom do we notice."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['frequency_hedges_count'] >= 6
        assert hedging['counts_by_type']['frequently'] >= 1
        assert hedging['counts_by_type']['occasionally'] >= 1

    def test_epistemic_verbs_detection(self, dimension):
        """Test epistemic verbs are detected."""
        text = "We assume this works. Studies estimate the cost. Data indicates a trend. Experts speculate on causes. We propose solutions. Authors claim benefits. We argue for changes. Evidence suggests improvements."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['epistemic_verbs_count'] >= 8

    def test_strong_certainty_detection(self, dimension):
        """Test strong certainty markers are detected."""
        text = "This definitely works. It certainly helps. Users absolutely love it. The system undoubtedly improves. Results clearly show benefits. Performance obviously increases."
        result = dimension.analyze(text)

        certainty = result['certainty']
        assert certainty['total_count'] >= 6
        assert certainty['strong_counts']['definitely'] >= 1
        assert certainty['strong_counts']['certainly'] >= 1

    def test_subjective_certainty_detection(self, dimension):
        """Test subjective certainty markers are detected."""
        text = "I believe this is correct. I think we should proceed. We believe in this approach. In my view, it's the best option."
        result = dimension.analyze(text)

        certainty = result['certainty']
        assert certainty['subjective_counts']['i_believe'] >= 1
        assert certainty['subjective_counts']['i_think'] >= 1
        assert certainty['subjective_counts']['we_believe'] >= 1
        assert certainty['subjective_counts']['in_my_view'] >= 1

    def test_assertion_speech_acts_detection(self, dimension):
        """Test assertion speech acts are detected."""
        text = "I argue that this matters. We propose that changes are needed. This shows clear results. This demonstrates the value."
        result = dimension.analyze(text)

        speech_acts = result['speech_acts']
        assert speech_acts['assertion_count'] >= 4

    def test_formulaic_speech_acts_detection(self, dimension):
        """Test formulaic AI speech acts are detected."""
        text = "It can be argued that benefits exist. One might argue that risks remain. It should be noted that testing matters. It is worth noting that quality counts."
        result = dimension.analyze(text)

        speech_acts = result['speech_acts']
        assert speech_acts['formulaic_count'] >= 4


class TestAnalyzeMethod:
    """Tests for analyze() method."""

    def test_analyze_returns_complete_structure(self, dimension, text_with_high_hedging):
        """Test analyze() returns complete pragmatic marker structure."""
        result = dimension.analyze(text_with_high_hedging)

        # Core structure
        assert 'hedging' in result
        assert 'certainty' in result
        assert 'speech_acts' in result
        assert 'certainty_hedge_ratio' in result
        assert 'formulaic_ratio' in result
        assert 'pragmatic_balance' in result
        assert 'available' in result

        # Hedging details
        assert 'total_count' in result['hedging']
        assert 'per_1k' in result['hedging']
        assert 'variety_score' in result['hedging']
        assert 'counts_by_type' in result['hedging']

        # Certainty details
        assert 'total_count' in result['certainty']
        assert 'per_1k' in result['certainty']
        assert 'subjective_percentage' in result['certainty']

        # Speech acts details
        assert 'total_count' in result['speech_acts']
        assert 'per_1k' in result['speech_acts']
        assert 'formulaic_ratio' in result['speech_acts']

    def test_high_hedging_detected(self, dimension, text_with_high_hedging):
        """Test excessive hedging is detected (AI signature)."""
        result = dimension.analyze(text_with_high_hedging)

        hedging = result['hedging']
        # With so many hedges, should exceed human range (4-7 per 1k)
        assert hedging['per_1k'] > 7.0

    def test_natural_balance_detected(self, dimension, text_natural_balance):
        """Test natural pragmatic balance (human-like)."""
        result = dimension.analyze(text_natural_balance)

        hedging = result['hedging']
        # Should be in or near human range (4-7 per 1k)
        assert hedging['per_1k'] < 12.0  # Not excessively high

    def test_variety_score_calculation(self, dimension):
        """Test variety score is calculated correctly."""
        # Text with many different hedge types
        text = "It might work. Perhaps we could try. Possibly it succeeds. About five items. Frequently happens. Sometimes works."
        result = dimension.analyze(text)

        hedging = result['hedging']
        # Should have reasonable variety (multiple patterns used)
        assert hedging['variety_score'] > 0.0
        assert hedging['variety_score'] <= 1.0


class TestScoringMethods:
    """Tests for scoring methods."""

    def test_score_low_hedging_scores_high(self, dimension, text_natural_balance):
        """Test natural hedging levels score highly."""
        result = dimension.analyze(text_natural_balance)
        score = dimension.calculate_score(result)

        # Natural text should score well
        assert score >= 50.0

    def test_score_high_hedging_scores_low(self, dimension, text_with_high_hedging):
        """Test excessive hedging scores lowly."""
        result = dimension.analyze(text_with_high_hedging)
        score = dimension.calculate_score(result)

        # Excessive hedging should reduce score
        assert score < 75.0

    def test_score_range_valid(self, dimension, text_natural_balance):
        """Test score is always in valid 0-100 range."""
        result = dimension.analyze(text_natural_balance)
        score = dimension.calculate_score(result)

        assert 0.0 <= score <= 100.0

    def test_score_with_unavailable_data(self, dimension):
        """Test scoring with unavailable data returns neutral."""
        metrics = {'available': False}
        score = dimension.calculate_score(metrics)

        assert score == 50.0


class TestRecommendations:
    """Tests for recommendation generation."""

    def test_recommendations_for_high_hedging(self, dimension, text_with_high_hedging):
        """Test recommendations are generated for excessive hedging."""
        result = dimension.analyze(text_with_high_hedging)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        assert len(recommendations) > 0
        # Should recommend reducing hedging
        assert any('hedg' in rec.lower() for rec in recommendations)

    def test_recommendations_for_good_text(self, dimension, text_natural_balance):
        """Test positive recommendations for good text."""
        result = dimension.analyze(text_natural_balance)
        score = dimension.calculate_score(result)
        recommendations = dimension.get_recommendations(score, result)

        # Should have at least one recommendation
        assert len(recommendations) > 0

    def test_recommendations_with_unavailable_data(self, dimension):
        """Test recommendations with unavailable data."""
        metrics = {'available': False}
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) == 1
        assert 'unavailable' in recommendations[0].lower()


class TestCompositeMetrics:
    """Tests for composite metrics calculation."""

    def test_certainty_hedge_ratio_calculation(self, dimension):
        """Test certainty/hedge ratio is calculated correctly."""
        text = "I believe this. I think so. This definitely works. This certainly helps. It might work. Perhaps we try."
        result = dimension.analyze(text)

        # Should have both certainty and hedging
        assert result['certainty_hedge_ratio'] > 0.0

    def test_pragmatic_balance_calculation(self, dimension, text_natural_balance):
        """Test pragmatic balance is calculated."""
        result = dimension.analyze(text_natural_balance)

        # Should have balance score
        assert 'pragmatic_balance' in result
        assert 0.0 <= result['pragmatic_balance'] <= 1.0

    def test_formulaic_ratio_calculation(self, dimension, text_with_speech_acts):
        """Test formulaic ratio is calculated."""
        result = dimension.analyze(text_with_speech_acts)

        # Should have formulaic ratio
        assert 'formulaic_ratio' in result
        assert 0.0 <= result['formulaic_ratio'] <= 1.0


class TestPatternCounts:
    """Tests for pattern counting accuracy - Updated for Story 2.6 (126 patterns)."""

    def test_total_pattern_coverage(self, dimension):
        """Test all 126 patterns are defined and accessible (Story 2.6)."""
        # Count patterns across all categories
        epistemic_hedges = len(dimension.EPISTEMIC_HEDGES)
        frequency_hedges = len(dimension.FREQUENCY_HEDGES)
        epistemic_verbs = len(dimension.EPISTEMIC_VERBS)
        strong_certainty = len(dimension.STRONG_CERTAINTY)
        subjective_certainty = len(dimension.SUBJECTIVE_CERTAINTY)
        assertion_acts = len(dimension.ASSERTION_ACTS)
        formulaic_acts = len(dimension.FORMULAIC_AI_ACTS)
        # New categories in Story 2.6
        attitude_markers = len(dimension.ATTITUDE_MARKERS)
        likelihood_adverbials = len(dimension.LIKELIHOOD_ADVERBIALS)

        total = (epistemic_hedges + frequency_hedges + epistemic_verbs +
                 strong_certainty + subjective_certainty +
                 assertion_acts + formulaic_acts +
                 attitude_markers + likelihood_adverbials)

        # Story 2.6 expanded counts
        assert epistemic_hedges == 43, f"Expected 43 epistemic hedges, got {epistemic_hedges}"
        assert frequency_hedges == 6, f"Expected 6 frequency hedges, got {frequency_hedges}"
        assert epistemic_verbs == 8, f"Expected 8 epistemic verbs, got {epistemic_verbs}"
        assert strong_certainty == 18, f"Expected 18 strong certainty, got {strong_certainty}"
        assert subjective_certainty == 8, f"Expected 8 subjective certainty, got {subjective_certainty}"
        assert assertion_acts == 10, f"Expected 10 assertion acts, got {assertion_acts}"
        assert formulaic_acts == 4, f"Expected 4 formulaic acts, got {formulaic_acts}"
        assert attitude_markers == 18, f"Expected 18 attitude markers, got {attitude_markers}"
        assert likelihood_adverbials == 11, f"Expected 11 likelihood adverbials, got {likelihood_adverbials}"
        assert total == 126, f"Expected 126 total patterns, got {total}"

    def test_no_pattern_overlap(self, dimension):
        """Test no patterns are duplicated across categories."""
        all_patterns = set()

        # Collect all pattern names from all categories
        categories = [
            dimension.EPISTEMIC_HEDGES,
            dimension.FREQUENCY_HEDGES,
            dimension.EPISTEMIC_VERBS,
            dimension.STRONG_CERTAINTY,
            dimension.SUBJECTIVE_CERTAINTY,
            dimension.ASSERTION_ACTS,
            dimension.FORMULAIC_AI_ACTS,
            dimension.ATTITUDE_MARKERS,  # Story 2.6
            dimension.LIKELIHOOD_ADVERBIALS,  # Story 2.6
        ]

        for category in categories:
            for pattern_name in category:
                assert pattern_name not in all_patterns, f"Duplicate pattern: {pattern_name}"
                all_patterns.add(pattern_name)


class TestTiers:
    """Tests for tier definitions."""

    def test_get_tiers_returns_valid_structure(self, dimension):
        """Test get_tiers() returns valid tier ranges."""
        tiers = dimension.get_tiers()

        assert 'excellent' in tiers
        assert 'good' in tiers
        assert 'acceptable' in tiers
        assert 'poor' in tiers

        # Verify ranges
        for _tier_name, (min_score, max_score) in tiers.items():
            assert 0.0 <= min_score <= 100.0
            assert 0.0 <= max_score <= 100.0
            assert min_score <= max_score


# ============================================================================
# STORY 2.6 - New test classes for expanded pattern lexicon
# ============================================================================

@pytest.fixture
def text_with_attitude_markers():
    """Text with attitude markers (Story 2.6)."""
    return """
    Surprisingly, the results exceeded expectations. Unfortunately, the budget
    was limited. Fortunately, the team adapted quickly. Interestingly, users
    preferred the simpler design. Importantly, security remained a priority.
    Remarkably, all tests passed on first run. Significantly, performance improved.
    Unexpectedly, the competitor launched early. Curiously, only one group showed
    improvement. Strangely, the pattern did not repeat. Oddly, no participants
    reported issues. Regrettably, we had to delay the launch. Admittedly, there
    were some limitations. Notably, the API response time decreased.
    Predictably, usage peaked during business hours. Inevitably, some bugs emerged.
    Understandably, users needed time to adapt.
    """


@pytest.fixture
def text_with_likelihood_adverbials():
    """Text with likelihood adverbials (Story 2.6)."""
    return """
    The system will probably need updates. This is arguably the best approach.
    The results are apparently consistent. Evidently, the data supports our
    hypothesis. The solution is seemingly effective. Ostensibly, the feature
    works as intended. The bug was supposedly fixed last week. Reportedly,
    users are satisfied. The claim is allegedly unverified. The source has
    purportedly confirmed this. This could plausibly explain the anomaly.
    """


@pytest.fixture
def text_with_expanded_hedges():
    """Text with expanded epistemic hedges (Story 2.6)."""
    return """
    This would suggest a correlation. We should consider alternatives. The
    data seems to support this view. Results appear to confirm the hypothesis.
    I believe this interpretation is valid. We think this merits further study.
    I suspect confounding variables exist. Let us suppose this holds true.
    It is possible that other factors exist. It is probable that this persists.
    It is unlikely this is coincidental. The outcome remains uncertain.
    It remains unclear whether this applies. Nearly all subjects improved.
    The groups were essentially equivalent. This is relatively uncommon.
    Results were somewhat unexpected. The correlation was fairly strong.
    The effect was quite significant. This typically occurs in such cases.
    This usually happens in production. To some extent, this applies here.
    In general, the findings support this conclusion.
    """


@pytest.fixture
def text_with_expanded_certainty():
    """Text with expanded certainty markers (Story 2.6)."""
    return """
    This always produces consistent results. This never occurred in controls.
    We completely agree with the assessment. This is totally correct.
    We entirely support this approach. This is surely significant.
    This is truly important. Indeed, the data supports this claim.
    In fact, the effect was stronger than expected. Of course, this requires
    validation. This is unquestionably important. The impact is undeniably
    significant. We know this to be true. I am certain this will work.
    We are confident in our findings. It is clear that progress has been made.
    """


class TestExpandedEpistemicHedges:
    """Tests for expanded epistemic hedge patterns (Story 2.6)."""

    def test_new_modal_hedges(self, dimension):
        """Test new modal hedges (would, should) are detected."""
        text = "This would indicate a problem. We should consider alternatives."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['counts_by_type'].get('would', 0) >= 1
        assert hedging['counts_by_type'].get('should', 0) >= 1

    def test_new_lexical_verb_hedges(self, dimension):
        """Test new lexical verb hedges are detected."""
        text = "The data seems correct. Results appear valid. I believe this works. We think it helps. I suspect issues. We suppose it applies."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['counts_by_type'].get('seem', 0) >= 1
        assert hedging['counts_by_type'].get('appear', 0) >= 1
        assert hedging['counts_by_type'].get('believe', 0) >= 1
        assert hedging['counts_by_type'].get('think', 0) >= 1

    def test_new_adjective_hedges(self, dimension):
        """Test new adjective hedges are detected."""
        text = "It is possible this works. It is probable this applies. It is unlikely to fail. The outcome is uncertain. It remains unclear."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['counts_by_type'].get('possible', 0) >= 1
        assert hedging['counts_by_type'].get('probable', 0) >= 1
        assert hedging['counts_by_type'].get('unlikely', 0) >= 1
        assert hedging['counts_by_type'].get('uncertain', 0) >= 1
        assert hedging['counts_by_type'].get('unclear', 0) >= 1

    def test_new_approximators(self, dimension):
        """Test new approximator patterns are detected."""
        text = "Nearly all passed. Essentially equivalent. Relatively common. Somewhat unexpected. Fairly strong. Quite significant. Typically occurs. Usually happens."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['approximators_count'] >= 6

    def test_multiword_hedges(self, dimension):
        """Test multi-word hedge patterns are detected."""
        text = "To some extent this applies. In general the findings support this."
        result = dimension.analyze(text)

        hedging = result['hedging']
        assert hedging['counts_by_type'].get('to_some_extent', 0) >= 1
        assert hedging['counts_by_type'].get('in_general', 0) >= 1

    def test_expanded_hedge_variety(self, dimension, text_with_expanded_hedges):
        """Test variety score calculation with expanded lexicon."""
        result = dimension.analyze(text_with_expanded_hedges)

        hedging = result['hedging']
        # With many different hedges, variety should be significant
        assert hedging['variety_score'] > 0.1
        assert hedging['variety_score'] <= 1.0


class TestExpandedCertaintyMarkers:
    """Tests for expanded certainty marker patterns (Story 2.6)."""

    def test_absolute_certainty_markers(self, dimension):
        """Test absolute certainty markers are detected."""
        text = "This always works. It never fails. We completely agree. They totally understand. We entirely support this."
        result = dimension.analyze(text)

        certainty = result['certainty']
        assert certainty['strong_counts'].get('always', 0) >= 1
        assert certainty['strong_counts'].get('never', 0) >= 1
        assert certainty['strong_counts'].get('completely', 0) >= 1

    def test_emphatic_certainty_markers(self, dimension):
        """Test emphatic certainty markers are detected."""
        text = "This is surely important. It is truly significant. Indeed, this works. In fact, it improved."
        result = dimension.analyze(text)

        certainty = result['certainty']
        assert certainty['strong_counts'].get('surely', 0) >= 1
        assert certainty['strong_counts'].get('truly', 0) >= 1
        assert certainty['strong_counts'].get('indeed', 0) >= 1
        assert certainty['strong_counts'].get('in_fact', 0) >= 1

    def test_new_subjective_certainty(self, dimension):
        """Test new subjective certainty patterns are detected."""
        text = "We know this works. I am certain it will succeed. We are confident in the results. It is clear that progress was made."
        result = dimension.analyze(text)

        certainty = result['certainty']
        assert certainty['subjective_counts'].get('we_know', 0) >= 1
        assert certainty['subjective_counts'].get('i_am_certain', 0) >= 1
        assert certainty['subjective_counts'].get('we_are_confident', 0) >= 1
        assert certainty['subjective_counts'].get('it_is_clear', 0) >= 1


class TestAttitudeMarkers:
    """Tests for new ATTITUDE_MARKERS category (Story 2.6)."""

    def test_attitude_markers_detected(self, dimension, text_with_attitude_markers):
        """Test attitude markers are detected and counted."""
        result = dimension.analyze(text_with_attitude_markers)

        assert 'attitude_markers' in result
        attitude = result['attitude_markers']
        assert attitude['total_count'] >= 10
        assert attitude['per_1k'] > 0

    def test_individual_attitude_markers(self, dimension):
        """Test individual attitude marker patterns."""
        text = "Surprisingly, this worked. Unfortunately, it failed. Fortunately, we recovered. Interestingly, patterns emerged."
        result = dimension.analyze(text)

        attitude = result['attitude_markers']
        assert attitude['counts_by_type'].get('surprisingly', 0) >= 1
        assert attitude['counts_by_type'].get('unfortunately', 0) >= 1
        assert attitude['counts_by_type'].get('fortunately', 0) >= 1
        assert attitude['counts_by_type'].get('interestingly', 0) >= 1

    def test_attitude_marker_variety(self, dimension, text_with_attitude_markers):
        """Test attitude marker variety score."""
        result = dimension.analyze(text_with_attitude_markers)

        attitude = result['attitude_markers']
        assert 'variety_score' in attitude
        assert attitude['variety_score'] > 0.3  # Many markers used


class TestLikelihoodAdverbials:
    """Tests for new LIKELIHOOD_ADVERBIALS category (Story 2.6)."""

    def test_likelihood_adverbials_detected(self, dimension, text_with_likelihood_adverbials):
        """Test likelihood adverbials are detected and counted."""
        result = dimension.analyze(text_with_likelihood_adverbials)

        assert 'likelihood_adverbials' in result
        likelihood = result['likelihood_adverbials']
        assert likelihood['total_count'] >= 8
        assert likelihood['per_1k'] > 0

    def test_individual_likelihood_adverbials(self, dimension):
        """Test individual likelihood adverbial patterns."""
        text = "This will probably work. It is arguably important. Results are apparently valid. This is seemingly correct."
        result = dimension.analyze(text)

        likelihood = result['likelihood_adverbials']
        assert likelihood['counts_by_type'].get('probably', 0) >= 1
        assert likelihood['counts_by_type'].get('arguably', 0) >= 1
        assert likelihood['counts_by_type'].get('apparently', 0) >= 1
        assert likelihood['counts_by_type'].get('seemingly', 0) >= 1

    def test_evidential_likelihood_markers(self, dimension):
        """Test evidential likelihood markers."""
        text = "Evidently this matters. Ostensibly it works. Supposedly it was fixed. Reportedly users are happy. Allegedly this is true."
        result = dimension.analyze(text)

        likelihood = result['likelihood_adverbials']
        assert likelihood['counts_by_type'].get('evidently', 0) >= 1
        assert likelihood['counts_by_type'].get('ostensibly', 0) >= 1
        assert likelihood['counts_by_type'].get('supposedly', 0) >= 1
        assert likelihood['counts_by_type'].get('reportedly', 0) >= 1
        assert likelihood['counts_by_type'].get('allegedly', 0) >= 1

    def test_likelihood_variety_score(self, dimension, text_with_likelihood_adverbials):
        """Test likelihood adverbial variety score."""
        result = dimension.analyze(text_with_likelihood_adverbials)

        likelihood = result['likelihood_adverbials']
        assert 'variety_score' in likelihood
        assert likelihood['variety_score'] > 0.3


class TestExpandedAnalyzeStructure:
    """Tests for expanded analyze() return structure (Story 2.6)."""

    def test_analyze_includes_new_categories(self, dimension, text_natural_balance):
        """Test analyze() includes new Story 2.6 categories."""
        result = dimension.analyze(text_natural_balance)

        # New categories from Story 2.6
        assert 'attitude_markers' in result
        assert 'likelihood_adverbials' in result

        # Verify structure of new categories
        assert 'total_count' in result['attitude_markers']
        assert 'per_1k' in result['attitude_markers']
        assert 'counts_by_type' in result['attitude_markers']
        assert 'variety_score' in result['attitude_markers']

        assert 'total_count' in result['likelihood_adverbials']
        assert 'per_1k' in result['likelihood_adverbials']
        assert 'counts_by_type' in result['likelihood_adverbials']
        assert 'variety_score' in result['likelihood_adverbials']


class TestExpandedAssertionActs:
    """Tests for expanded assertion acts (Story 2.6)."""

    def test_new_assertion_verbs(self, dimension):
        """Test new assertion verbs are detected."""
        text = "This demonstrates the value. Results show improvement. Data proves the hypothesis. We establish the relationship. Tests confirm our predictions. Studies find strong evidence."
        result = dimension.analyze(text)

        speech_acts = result['speech_acts']
        assert speech_acts['assertion_count'] >= 6
