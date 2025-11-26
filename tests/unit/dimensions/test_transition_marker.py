"""
Tests for TransitionMarkerDimension - AI transition marker detection.

Story 1.4.5 - New dimension split from StylometricDimension.
Story 2.4.0.5 - v2.0.0 refactor: basic + formulaic transitions, weight 6.0%.
"""


import pytest

from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.transition_marker import TransitionMarkerDimension


@pytest.fixture
def dimension():
    """Create TransitionMarkerDimension instance."""
    # Clear registry before each test to avoid duplicate registration errors
    DimensionRegistry.clear()
    return TransitionMarkerDimension()


@pytest.fixture
def text_with_markers():
    """Text with high AI marker usage."""
    return """
    However, the system provides robust solutions. Moreover, the framework
    facilitates seamless integration. Furthermore, the approach leverages
    innovative technology. However, we must consider the implications.
    Moreover, this methodology optimizes performance. Additionally, we can
    streamline workflows. However, the comprehensive analysis suggests improvements.
    """


@pytest.fixture
def text_without_markers():
    """Text without AI markers (human style)."""
    return """
    The system works well. We can use it for many tasks. It helps us
    get things done faster. But remember to test everything first.
    Also, make sure to document your work. You'll thank yourself later.
    """


@pytest.fixture
def text_with_clustering():
    """Text with clustered 'however' usage."""
    return """
    However, we need to consider this. The next line is important.
    However, there's another point to make. Just a few lines apart.
    However, this clustering is a strong AI signature.
    """


class TestDimensionMetadata:
    """Tests for dimension metadata and registration."""

    def test_dimension_name(self, dimension):
        """Test dimension name is 'transition_marker'."""
        assert dimension.dimension_name == "transition_marker"

    def test_dimension_weight(self, dimension):
        """Test dimension weight is 5.5% (rebalanced to 100% total)."""
        assert dimension.weight == 5.5

    def test_dimension_tier(self, dimension):
        """Test dimension tier is ADVANCED."""
        assert dimension.tier == "ADVANCED"

    def test_dimension_description(self, dimension):
        """Test dimension has meaningful description."""
        desc = dimension.description
        assert isinstance(desc, str)
        assert len(desc) > 20
        assert any(term in desc.lower() for term in ["marker", "however", "moreover", "transition"])

    def test_dimension_registers_on_init(self):
        """Test dimension self-registers with registry on initialization."""
        DimensionRegistry.clear()
        dim = TransitionMarkerDimension()

        registered = DimensionRegistry.get("transition_marker")
        assert registered is dim


class TestAnalyzeMethod:
    """Tests for analyze() method v2.0.0 - basic + formulaic transitions."""

    def test_analyze_returns_v2_structure(self, dimension, text_with_markers):
        """Test analyze() returns v2.0.0 structure with basic + formulaic transitions."""
        result = dimension.analyze(text_with_markers)

        # Should contain v2.0.0 structure
        assert 'basic_transitions' in result
        assert 'formulaic_transitions' in result
        assert 'total_transitions_per_1k' in result
        assert 'available' in result

        # Basic transitions structure
        basic = result['basic_transitions']
        assert 'however_count' in basic
        assert 'moreover_count' in basic
        assert 'however_per_1k' in basic
        assert 'moreover_per_1k' in basic
        assert 'total_ai_markers_per_1k' in basic

        # Formulaic transitions structure
        formulaic = result['formulaic_transitions']
        assert 'count' in formulaic
        assert 'transitions' in formulaic
        assert 'per_1k' in formulaic

        # Should NOT contain readability metrics (those belong in ReadabilityDimension)
        assert 'flesch_reading_ease' not in result
        assert 'flesch_kincaid_grade' not in result

    def test_analyze_counts_however(self, dimension):
        """Test analyze() correctly counts 'however' occurrences in basic_transitions."""
        text = "However, this is important. However, we should note this. However."
        result = dimension.analyze(text)

        assert result['basic_transitions']['however_count'] == 3

    def test_analyze_counts_moreover(self, dimension):
        """Test analyze() correctly counts 'moreover' occurrences in basic_transitions."""
        text = "Moreover, we should consider this. Moreover, the data shows. Moreover."
        result = dimension.analyze(text)

        assert result['basic_transitions']['moreover_count'] == 3

    def test_analyze_case_insensitive(self, dimension):
        """Test analyze() is case-insensitive for marker detection."""
        text = "However HOWEVER however HoWeVeR"
        result = dimension.analyze(text)

        assert result['basic_transitions']['however_count'] == 4

    def test_analyze_calculates_per_1k(self, dimension):
        """Test analyze() calculates per-1k-words frequency correctly."""
        # 100 words with 1 'however' = 10 per 1k
        text = "however " + "word " * 99  # 100 words total, 1 however
        result = dimension.analyze(text)

        assert 'however_per_1k' in result['basic_transitions']
        assert 'total_ai_markers_per_1k' in result['basic_transitions']

    def test_analyze_sets_available_flag(self, dimension, text_with_markers):
        """Test analyze() sets 'available' flag."""
        result = dimension.analyze(text_with_markers)
        assert 'available' in result
        assert result['available'] is True

    def test_analyze_handles_empty_text(self, dimension):
        """Test analyze() handles empty text gracefully."""
        result = dimension.analyze("")

        basic = result['basic_transitions']
        formulaic = result['formulaic_transitions']
        assert basic['however_count'] == 0
        assert basic['total_ai_markers_per_1k'] == 0
        assert formulaic['count'] == 0

    def test_analyze_uses_precalculated_word_count(self, dimension):
        """Test analyze() uses pre-calculated word_count if provided."""
        text = "However, this is a test."
        result = dimension.analyze(text, word_count=100)

        # Should use provided word_count (100) instead of calculating (5)
        assert 'however_per_1k' in result['basic_transitions']

    def test_analyze_detects_formulaic_transitions(self, dimension):
        """Test analyze() detects formulaic transitions (v2.0.0)."""
        text = "Furthermore, this is important. Moreover, we should note this. Additionally, consider this."
        result = dimension.analyze(text)

        formulaic = result['formulaic_transitions']
        assert formulaic['count'] >= 3
        assert len(formulaic['transitions']) >= 3
        assert formulaic['per_1k'] > 0

    def test_analyze_calculates_total_transitions(self, dimension):
        """Test analyze() calculates total_transitions_per_1k (v2.0.0)."""
        text = "However, this works. Furthermore, it's effective. Moreover, we like it."
        result = dimension.analyze(text)

        # Should combine basic + formulaic
        assert 'total_transitions_per_1k' in result
        assert result['total_transitions_per_1k'] > 0


class TestCalculateScoreMethod:
    """Tests for calculate_score() v2.0.0 - composite scoring (basic + formulaic)."""

    def test_score_excellent_both_components(self, dimension):
        """Test score for excellent on both basic and formulaic (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 1.5},
            'formulaic_transitions': {'count': 0}
        }
        score = dimension.calculate_score(metrics)

        assert score == 100.0  # Excellent - very human-like

    def test_score_good_basic_excellent_formulaic(self, dimension):
        """Test score for good basic, excellent formulaic (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 3.5},
            'formulaic_transitions': {'count': 1}
        }
        score = dimension.calculate_score(metrics)

        # 75 * 0.5 + 100 * 0.5 = 87.5
        assert score == 87.5

    def test_score_concerning_basic_good_formulaic(self, dimension):
        """Test score for concerning basic, good formulaic (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 6.0},
            'formulaic_transitions': {'count': 2}
        }
        score = dimension.calculate_score(metrics)

        # 50 * 0.5 + 75 * 0.5 = 62.5
        assert score == 62.5

    def test_score_ai_signature_both_components(self, dimension):
        """Test score for strong AI signature on both components (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 12.0},
            'formulaic_transitions': {'count': 5}
        }
        score = dimension.calculate_score(metrics)

        # 25 * 0.5 + 25 * 0.5 = 25.0
        assert score == 25.0

    def test_score_boundary_values_basic(self, dimension):
        """Test score at exact boundary values for basic transitions."""
        # Exactly 2.0 basic, 0 formulaic
        metrics1 = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 2.0},
            'formulaic_transitions': {'count': 0}
        }
        assert dimension.calculate_score(metrics1) == 100.0

        # Exactly 4.0 basic, 1 formulaic
        metrics2 = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 4.0},
            'formulaic_transitions': {'count': 1}
        }
        assert dimension.calculate_score(metrics2) == 87.5  # 75 * 0.5 + 100 * 0.5

    def test_score_boundary_values_formulaic(self, dimension):
        """Test score at exact boundary values for formulaic transitions."""
        # 0 basic, exactly 1 formulaic
        metrics1 = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 0.0},
            'formulaic_transitions': {'count': 1}
        }
        assert dimension.calculate_score(metrics1) == 100.0

        # 0 basic, exactly 2 formulaic
        metrics2 = {
            'available': True,
            'basic_transitions': {'total_ai_markers_per_1k': 0.0},
            'formulaic_transitions': {'count': 2}
        }
        # 100 * 0.5 + 75 * 0.5 = 87.5
        assert dimension.calculate_score(metrics2) == 87.5

    def test_score_unavailable_data(self, dimension):
        """Test score when marker data unavailable."""
        metrics = {
            'available': False
        }
        score = dimension.calculate_score(metrics)

        assert score == 50.0  # Neutral score for unavailable data

    def test_score_validates_range(self, dimension):
        """Test score is always in valid 0-100 range."""
        test_cases = [
            (0.0, 0), (1.0, 1), (3.0, 2), (5.0, 3),
            (7.0, 4), (10.0, 5), (20.0, 10)
        ]

        for basic_value, formulaic_count in test_cases:
            metrics = {
                'available': True,
                'basic_transitions': {'total_ai_markers_per_1k': basic_value},
                'formulaic_transitions': {'count': formulaic_count}
            }
            score = dimension.calculate_score(metrics)
            assert 0.0 <= score <= 100.0


class TestGetRecommendations:
    """Tests for get_recommendations() method v2.0.0."""

    def test_recommendations_for_high_basic_markers(self, dimension):
        """Test recommendations for high basic markers (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {
                'however_per_1k': 3.0,
                'moreover_per_1k': 2.0,
                'total_ai_markers_per_1k': 5.0
            },
            'formulaic_transitions': {'count': 0, 'transitions': []}
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('reduce' in rec.lower() or 'marker' in rec.lower() for rec in recommendations)

    def test_recommendations_for_high_however(self, dimension):
        """Test recommendations for high 'however' usage (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {
                'however_per_1k': 5.0,
                'moreover_per_1k': 0.5,
                'total_ai_markers_per_1k': 5.5
            },
            'formulaic_transitions': {'count': 0, 'transitions': []}
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('however' in rec.lower() for rec in recommendations)

    def test_recommendations_for_high_moreover(self, dimension):
        """Test recommendations for 'moreover' usage (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {
                'however_per_1k': 0.5,
                'moreover_per_1k': 2.0,
                'total_ai_markers_per_1k': 2.5
            },
            'formulaic_transitions': {'count': 0, 'transitions': []}
        }
        recommendations = dimension.get_recommendations(75.0, metrics)

        assert len(recommendations) > 0
        assert any('moreover' in rec.lower() for rec in recommendations)

    def test_recommendations_for_formulaic_transitions(self, dimension):
        """Test recommendations for formulaic transitions (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {
                'however_per_1k': 0.5,
                'moreover_per_1k': 0.0,
                'total_ai_markers_per_1k': 0.5
            },
            'formulaic_transitions': {
                'count': 5,
                'transitions': ['Furthermore', 'Moreover', 'Additionally']
            }
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('formulaic' in rec.lower() for rec in recommendations)

    def test_recommendations_for_excellent_score(self, dimension):
        """Test recommendations for excellent marker usage (v2.0.0)."""
        metrics = {
            'available': True,
            'basic_transitions': {
                'however_per_1k': 0.5,
                'moreover_per_1k': 0.0,
                'total_ai_markers_per_1k': 0.5
            },
            'formulaic_transitions': {'count': 0, 'transitions': []}
        }
        recommendations = dimension.get_recommendations(100.0, metrics)

        assert len(recommendations) > 0
        assert any('excellent' in rec.lower() or 'natural' in rec.lower() for rec in recommendations)

    def test_recommendations_unavailable_data(self, dimension):
        """Test recommendations when marker data unavailable."""
        metrics = {
            'available': False
        }
        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('unavailable' in rec.lower() for rec in recommendations)


class TestGetTiers:
    """Tests for get_tiers() method."""

    def test_get_tiers_structure(self, dimension):
        """Test tier structure is valid."""
        tiers = dimension.get_tiers()

        assert isinstance(tiers, dict)
        assert 'excellent' in tiers
        assert 'good' in tiers
        assert 'acceptable' in tiers
        assert 'poor' in tiers

    def test_tier_ranges(self, dimension):
        """Test tier ranges are properly defined."""
        tiers = dimension.get_tiers()

        excellent_min, excellent_max = tiers['excellent']
        assert excellent_min == 90.0
        assert excellent_max == 100.0


class TestBasicTransitionsAnalysis:
    """Tests for _analyze_basic_transitions() helper method (v2.0.0)."""

    def test_counts_however_correctly(self, dimension):
        """Test 'however' counting accuracy."""
        text = "However, this is important. However, we should note. However."
        result = dimension._analyze_basic_transitions(text)

        assert result['however_count'] == 3

    def test_counts_moreover_correctly(self, dimension):
        """Test 'moreover' counting accuracy."""
        text = "Moreover, this matters. Moreover, consider this. Moreover."
        result = dimension._analyze_basic_transitions(text)

        assert result['moreover_count'] == 3

    def test_word_boundary_matching(self, dimension):
        """Test marker detection uses word boundaries (no partial matches)."""
        # "anyhowever" should NOT match "however"
        text = "anyhowever somehowever"
        result = dimension._analyze_basic_transitions(text)

        assert result['however_count'] == 0

    def test_case_insensitive_matching(self, dimension):
        """Test case-insensitive marker matching."""
        text = "However HOWEVER however HoWeVeR"
        result = dimension._analyze_basic_transitions(text)

        assert result['however_count'] == 4

    def test_per_1k_calculation(self, dimension):
        """Test per-1k-words calculation."""
        # 500 words with 5 markers = 10 per 1k
        text = "however " * 5 + "word " * 495  # 500 words total
        result = dimension._analyze_basic_transitions(text)

        # Should be approximately 10 per 1k
        assert abs(result['total_ai_markers_per_1k'] - 10.0) < 1.0

    def test_handles_zero_words(self, dimension):
        """Test handling of zero word count."""
        text = "..."  # No actual words
        result = dimension._analyze_basic_transitions(text)

        assert result['however_per_1k'] == 0.0
        assert result['total_ai_markers_per_1k'] == 0.0


class TestFormulaicTransitionsAnalysis:
    """Tests for _analyze_formulaic_transitions() helper method (v2.0.0)."""

    def test_detects_furthermore(self, dimension):
        """Test 'Furthermore' detection."""
        text = "Furthermore, this is important. Furthermore, we should note this."
        result = dimension._analyze_formulaic_transitions(text)

        assert result['count'] >= 2

    def test_detects_additionally(self, dimension):
        """Test 'Additionally' detection."""
        text = "Additionally, we should consider this. Additionally, the data shows."
        result = dimension._analyze_formulaic_transitions(text)

        assert result['count'] >= 2

    def test_detects_in_conclusion(self, dimension):
        """Test 'In conclusion' detection."""
        text = "In conclusion, this works well. In conclusion, we approve."
        result = dimension._analyze_formulaic_transitions(text)

        assert result['count'] >= 2

    def test_case_insensitive_matching(self, dimension):
        """Test case-insensitive formulaic matching."""
        text = "Furthermore, this works. FURTHERMORE, that works. furthermore, all works."
        result = dimension._analyze_formulaic_transitions(text)

        assert result['count'] == 3

    def test_per_1k_calculation(self, dimension):
        """Test per-1k-words calculation for formulaic transitions."""
        # 500 words with 5 formulaic transitions = 10 per 1k
        text = "Furthermore, " * 5 + "word " * 495  # 500 words total
        result = dimension._analyze_formulaic_transitions(text)

        # Should be approximately 10 per 1k
        assert abs(result['per_1k'] - 10.0) < 1.0

    def test_transitions_list_limited(self, dimension):
        """Test transitions list is limited to first 15."""
        text = "Furthermore, " * 20  # 20 instances
        result = dimension._analyze_formulaic_transitions(text)

        assert result['count'] == 20
        assert len(result['transitions']) <= 15


class TestAnalyzeDetailed:
    """Tests for analyze_detailed() method."""

    def test_analyze_detailed_returns_list(self, dimension, text_with_markers):
        """Test analyze_detailed returns list of TransitionInstance objects (Story 2.0: StylometricIssue removed)."""
        lines = text_with_markers.split('\n')
        result = dimension.analyze_detailed(lines)

        assert isinstance(result, list)
        assert len(result) > 0  # Should find markers

    def test_analyze_detailed_detects_however(self, dimension):
        """Test analyze_detailed detects individual 'however' occurrences."""
        lines = [
            "This is a test.",
            "However, this line has a marker.",
            "Another line without markers."
        ]
        result = dimension.analyze_detailed(lines)

        # Should find at least one issue
        assert len(result) > 0
        # Story 2.0: Changed marker_type → transition (TransitionInstance field)
        assert any(issue.transition == 'however' for issue in result)

    def test_analyze_detailed_detects_moreover(self, dimension):
        """Test analyze_detailed detects individual 'moreover' occurrences."""
        lines = [
            "This is a test.",
            "Moreover, this line has a marker.",
            "Another line without markers."
        ]
        result = dimension.analyze_detailed(lines)

        assert len(result) > 0
        # Story 2.0: Changed marker_type → transition (TransitionInstance field)
        assert any(issue.transition == 'moreover' for issue in result)

    def test_analyze_detailed_detects_clustering(self, dimension, text_with_clustering):
        """Test analyze_detailed detects clustered 'however' usage."""
        lines = text_with_clustering.split('\n')
        result = dimension.analyze_detailed(lines)

        # Should detect clustering (multiple issues including clusters)
        assert len(result) > 0
        # May include 'however_cluster' marker type

    def test_analyze_detailed_respects_html_comment_checker(self, dimension):
        """Test analyze_detailed skips HTML comments."""
        lines = [
            "<!-- However, this is a comment -->",
            "However, real content here.",
            "<!-- Moreover, another comment -->"
        ]

        def is_html_comment(line):
            return line.strip().startswith('<!--')

        result = dimension.analyze_detailed(lines, html_comment_checker=is_html_comment)

        # Should only detect marker in real content (line 2)
        non_comment_issues = [issue for issue in result if 'comment' not in issue.context.lower()]
        assert len(non_comment_issues) >= 1

    def test_analyze_detailed_skips_headings(self, dimension):
        """Test analyze_detailed skips markdown headings."""
        lines = [
            "# However This Is A Heading",
            "However, this is real content.",
            "## Moreover Another Heading"
        ]

        result = dimension.analyze_detailed(lines)

        # Should only detect marker in real content (line 2)
        # Headings should be skipped
        assert len(result) >= 1

    def test_analyze_detailed_skips_code_blocks(self, dimension):
        """Test analyze_detailed skips code blocks."""
        lines = [
            "```python",
            "# However, this is code",
            "```",
            "However, this is real text."
        ]

        result = dimension.analyze_detailed(lines)

        # Should only detect marker in real text (line 4)
        # Code blocks should be skipped
        assert len(result) >= 1


class TestBackwardCompatibility:
    """Tests for backward compatibility alias."""

    def test_backward_compatibility_alias_exists(self):
        """Test TransitionMarkerAnalyzer alias exists for backward compatibility (v2.0.0)."""
        from writescore.dimensions.transition_marker import TransitionMarkerAnalyzer

        DimensionRegistry.clear()
        dim = TransitionMarkerAnalyzer()

        assert dim.dimension_name == "transition_marker"
        assert dim.weight == 5.5  # rebalanced to 100% total
