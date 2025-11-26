"""
Tests for pattern_matching utilities.

Tests cover pattern compilation, matching, and AI vocabulary detection.
"""

import re

from writescore.utils.pattern_matching import (
    AI_VOCAB_REPLACEMENTS,
    AI_VOCABULARY,
    DOMAIN_TERMS_DEFAULT,
    FORMULAIC_TRANSITIONS,
    PatternMatcher,
)


class TestPatternMatcherInitialization:
    """Tests for PatternMatcher initialization."""

    def test_init_default(self):
        """Test initialization with default domain terms."""
        matcher = PatternMatcher()

        assert matcher.domain_terms == DOMAIN_TERMS_DEFAULT
        assert matcher._ai_vocab_patterns is not None
        assert matcher._transition_patterns is not None
        assert matcher._domain_patterns is not None

    def test_init_custom_domain_terms(self):
        """Test initialization with custom domain terms."""
        custom_terms = [r'\bPython\b', r'\bDjango\b']
        matcher = PatternMatcher(domain_terms=custom_terms)

        assert matcher.domain_terms == custom_terms

    def test_init_compiles_patterns(self):
        """Test that all patterns are pre-compiled."""
        matcher = PatternMatcher()

        # Check that patterns are compiled regex objects
        for pattern in matcher._ai_vocab_patterns.values():
            assert isinstance(pattern, re.Pattern)

        for pattern in matcher._transition_patterns:
            assert isinstance(pattern, re.Pattern)

        for pattern in matcher._domain_patterns:
            assert isinstance(pattern, re.Pattern)


class TestGetPatternMethods:
    """Tests for pattern getter methods."""

    def test_get_ai_vocab_patterns(self):
        """Test getting AI vocabulary patterns."""
        matcher = PatternMatcher()
        patterns = matcher.get_ai_vocab_patterns()

        assert isinstance(patterns, dict)
        assert len(patterns) == len(AI_VOCABULARY)

        # Check all are compiled patterns
        for pattern in patterns.values():
            assert isinstance(pattern, re.Pattern)

    def test_get_transition_patterns(self):
        """Test getting formulaic transition patterns."""
        matcher = PatternMatcher()
        patterns = matcher.get_transition_patterns()

        assert isinstance(patterns, list)
        assert len(patterns) == len(FORMULAIC_TRANSITIONS)

        # Check all are compiled patterns
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)

    def test_get_domain_patterns(self):
        """Test getting domain term patterns."""
        matcher = PatternMatcher()
        patterns = matcher.get_domain_patterns()

        assert isinstance(patterns, list)
        assert len(patterns) == len(DOMAIN_TERMS_DEFAULT)

        # Check all are compiled patterns
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)


class TestPatternProperties:
    """Tests for pattern property accessors."""

    def test_bold_pattern(self):
        """Test bold pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.bold_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("**bold text**") is not None
        assert pattern.search("__bold text__") is not None
        assert pattern.search("normal text") is None

    def test_italic_pattern(self):
        """Test italic pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.italic_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("*italic*") is not None
        assert pattern.search("_italic_") is not None
        assert pattern.search("normal text") is None

    def test_em_dash_pattern(self):
        """Test em-dash pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.em_dash_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("text—with em dash") is not None
        assert pattern.search("text--with double dash") is not None
        assert pattern.search("normal text") is None

    def test_word_pattern(self):
        """Test word extraction pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.word_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        matches = pattern.findall("Hello world 123")
        assert len(matches) == 2  # "Hello" and "world", not "123"
        assert "Hello" in matches
        assert "world" in matches

    def test_heading_pattern(self):
        """Test heading pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.heading_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        match = pattern.search("# Heading 1")
        assert match is not None
        assert match.group(1) == "#"
        assert match.group(2) == "Heading 1"

    def test_first_person_pattern(self):
        """Test first-person pronoun pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.first_person_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("I think") is not None
        assert pattern.search("We are") is not None
        assert pattern.search("my book") is not None
        assert pattern.search("our code") is not None
        assert pattern.search("The system") is None

    def test_second_person_pattern(self):
        """Test second-person pronoun pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.second_person_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("you should") is not None
        assert pattern.search("your code") is not None
        assert pattern.search("The system") is None

    def test_contraction_pattern(self):
        """Test contraction pattern property."""
        matcher = PatternMatcher()
        pattern = matcher.contraction_pattern

        assert isinstance(pattern, re.Pattern)

        # Test matching
        assert pattern.search("don't") is not None
        assert pattern.search("can't") is not None
        assert pattern.search("it's") is not None
        assert pattern.search("cannot") is None


class TestAIVocabularyMatching:
    """Tests for AI vocabulary pattern matching."""

    def test_ai_vocab_delve(self):
        """Test detection of 'delve' variations."""
        matcher = PatternMatcher()
        patterns = matcher.get_ai_vocab_patterns()

        # Find the delve pattern
        delve_pattern = [p for k, p in patterns.items() if 'delv' in k][0]

        assert delve_pattern.search("Let's delve into this") is not None
        assert delve_pattern.search("delving deeper") is not None
        assert delve_pattern.search("delves into") is not None

    def test_ai_vocab_robust(self):
        """Test detection of 'robust' variations."""
        matcher = PatternMatcher()
        patterns = matcher.get_ai_vocab_patterns()

        # Find the robust pattern
        robust_pattern = [p for k, p in patterns.items() if 'robust' in k][0]

        assert robust_pattern.search("A robust solution") is not None
        assert robust_pattern.search("robustness of the system") is not None

    def test_ai_vocab_leverage(self):
        """Test detection of 'leverage' variations."""
        matcher = PatternMatcher()
        patterns = matcher.get_ai_vocab_patterns()

        # Find the leverage pattern
        leverage_pattern = [p for k, p in patterns.items() if 'leverag' in k][0]

        assert leverage_pattern.search("leverage the framework") is not None
        assert leverage_pattern.search("leveraging tools") is not None
        assert leverage_pattern.search("leverages AI") is not None

    def test_ai_vocab_case_insensitive(self):
        """Test that AI vocabulary matching is case-insensitive."""
        matcher = PatternMatcher()
        patterns = matcher.get_ai_vocab_patterns()

        # Get a pattern (delve)
        delve_pattern = [p for k, p in patterns.items() if 'delv' in k][0]

        assert delve_pattern.search("DELVE into") is not None
        assert delve_pattern.search("Delve into") is not None
        assert delve_pattern.search("delve into") is not None


class TestFormuliaicTransitionMatching:
    """Tests for formulaic transition pattern matching."""

    def test_transition_furthermore(self):
        """Test detection of 'Furthermore'."""
        matcher = PatternMatcher()
        patterns = matcher.get_transition_patterns()

        # Find Furthermore pattern
        furthermore_pattern = [p for p in patterns if p.pattern == r'\bFurthermore,'][0]

        assert furthermore_pattern.search("Furthermore, we can") is not None
        assert furthermore_pattern.search("Furthermore") is None  # Need comma

    def test_transition_moreover(self):
        """Test detection of 'Moreover'."""
        matcher = PatternMatcher()
        patterns = matcher.get_transition_patterns()

        # Find Moreover pattern
        moreover_pattern = [p for p in patterns if p.pattern == r'\bMoreover,'][0]

        assert moreover_pattern.search("Moreover, this shows") is not None

    def test_transition_in_conclusion(self):
        """Test detection of 'In conclusion'."""
        matcher = PatternMatcher()
        patterns = matcher.get_transition_patterns()

        # Find In conclusion pattern
        conclusion_pattern = [p for p in patterns if 'conclusion' in p.pattern.lower()][0]

        assert conclusion_pattern.search("In conclusion, we see") is not None


class TestDomainTermMatching:
    """Tests for domain term pattern matching."""

    def test_domain_terms_default(self):
        """Test detection of default domain terms."""
        matcher = PatternMatcher()
        patterns = matcher.get_domain_patterns()

        # There should be patterns for default terms
        assert len(patterns) == len(DOMAIN_TERMS_DEFAULT)

    def test_domain_terms_custom(self):
        """Test detection of custom domain terms."""
        custom_terms = [r'\bPython\b', r'\bDjango\b']
        matcher = PatternMatcher(domain_terms=custom_terms)
        patterns = matcher.get_domain_patterns()

        assert len(patterns) == 2

        # Test matching
        python_found = any(p.search("Python is great") for p in patterns)
        django_found = any(p.search("Django framework") for p in patterns)

        assert python_found
        assert django_found


class TestFormattingPatterns:
    """Tests for formatting pattern matching."""

    def test_bold_double_asterisk(self):
        """Test bold with double asterisks."""
        matcher = PatternMatcher()
        text = "This is **bold** text"
        matches = matcher.bold_pattern.findall(text)

        assert len(matches) == 1
        assert matches[0] == "**bold**"

    def test_bold_double_underscore(self):
        """Test bold with double underscores."""
        matcher = PatternMatcher()
        text = "This is __bold__ text"
        matches = matcher.bold_pattern.findall(text)

        assert len(matches) == 1
        assert matches[0] == "__bold__"

    def test_italic_single_asterisk(self):
        """Test italic with single asterisk."""
        matcher = PatternMatcher()
        text = "This is *italic* text"
        matches = matcher.italic_pattern.findall(text)

        assert len(matches) == 1
        assert matches[0] == "*italic*"

    def test_italic_single_underscore(self):
        """Test italic with single underscore."""
        matcher = PatternMatcher()
        text = "This is _italic_ text"
        matches = matcher.italic_pattern.findall(text)

        assert len(matches) == 1
        assert matches[0] == "_italic_"

    def test_em_dash_detection(self):
        """Test em-dash detection."""
        matcher = PatternMatcher()

        matches1 = matcher.em_dash_pattern.findall("Text—with em dash")
        matches2 = matcher.em_dash_pattern.findall("Text--with double dash")

        assert len(matches1) == 1
        assert len(matches2) == 1


class TestVoicePatterns:
    """Tests for voice and pronoun pattern matching."""

    def test_first_person_pronouns(self):
        """Test first-person pronoun detection."""
        matcher = PatternMatcher()

        text = "I think we should use our approach"
        matches = matcher.first_person_pattern.findall(text)

        assert len(matches) == 3  # I, we, our

    def test_second_person_pronouns(self):
        """Test second-person pronoun detection."""
        matcher = PatternMatcher()

        text = "You should use your code"
        matches = matcher.second_person_pattern.findall(text)

        assert len(matches) == 2  # you, your

    def test_contractions(self):
        """Test contraction detection."""
        matcher = PatternMatcher()

        text = "Don't worry, it's working and we'll fix it"
        matches = matcher.contraction_pattern.findall(text)

        assert len(matches) == 3  # Don't, it's, we'll


class TestConstants:
    """Tests for constant definitions."""

    def test_ai_vocabulary_list(self):
        """Test AI_VOCABULARY constant."""
        assert isinstance(AI_VOCABULARY, list)
        assert len(AI_VOCABULARY) > 0

        # Check some key patterns exist
        assert any('delv' in p for p in AI_VOCABULARY)
        assert any('robust' in p for p in AI_VOCABULARY)
        assert any('leverag' in p for p in AI_VOCABULARY)

    def test_formulaic_transitions_list(self):
        """Test FORMULAIC_TRANSITIONS constant."""
        assert isinstance(FORMULAIC_TRANSITIONS, list)
        assert len(FORMULAIC_TRANSITIONS) > 0

        # Check some key patterns exist
        assert any('Furthermore' in p for p in FORMULAIC_TRANSITIONS)
        assert any('Moreover' in p for p in FORMULAIC_TRANSITIONS)
        assert any('conclusion' in p for p in FORMULAIC_TRANSITIONS)

    def test_domain_terms_default(self):
        """Test DOMAIN_TERMS_DEFAULT constant."""
        assert isinstance(DOMAIN_TERMS_DEFAULT, list)
        assert len(DOMAIN_TERMS_DEFAULT) > 0

    def test_ai_vocab_replacements(self):
        """Test AI_VOCAB_REPLACEMENTS constant."""
        assert isinstance(AI_VOCAB_REPLACEMENTS, dict)
        assert len(AI_VOCAB_REPLACEMENTS) > 0

        # Check some key replacements exist
        assert 'delve' in AI_VOCAB_REPLACEMENTS
        assert 'robust' in AI_VOCAB_REPLACEMENTS
        assert 'leverage' in AI_VOCAB_REPLACEMENTS

        # Check replacement values are lists
        assert isinstance(AI_VOCAB_REPLACEMENTS['delve'], list)
        assert len(AI_VOCAB_REPLACEMENTS['delve']) > 0


class TestIntegration:
    """Integration tests for pattern matching."""

    def test_full_text_analysis(self):
        """Test complete pattern matching on sample text."""
        matcher = PatternMatcher()

        text = """# Introduction

Furthermore, we should leverage robust solutions to delve into this ecosystem.
Moreover, this holistic approach facilitates seamless integration.

I think **you** should use your code with _italic_ emphasis—it's comprehensive.
"""

        # Test AI vocabulary detection
        ai_matches = []
        for _pattern_str, pattern in matcher.get_ai_vocab_patterns().items():
            matches = pattern.findall(text)
            ai_matches.extend(matches)

        assert len(ai_matches) > 0  # Should find several AI vocab words

        # Test transition detection
        transition_matches = []
        for pattern in matcher.get_transition_patterns():
            matches = pattern.findall(text)
            transition_matches.extend(matches)

        assert len(transition_matches) >= 2  # Furthermore, Moreover

        # Test formatting
        bold_count = len(matcher.bold_pattern.findall(text))
        italic_count = len(matcher.italic_pattern.findall(text))
        em_dash_count = len(matcher.em_dash_pattern.findall(text))

        assert bold_count == 1
        # Note: italic_count is 2 because **you** contains *you* which matches italic pattern
        assert italic_count == 2  # *you* from **you** + _italic_
        assert em_dash_count == 1

        # Test voice
        first_person_count = len(matcher.first_person_pattern.findall(text))
        second_person_count = len(matcher.second_person_pattern.findall(text))

        assert first_person_count >= 1  # "I"
        assert second_person_count >= 2  # "you", "your"

    def test_pattern_reusability(self):
        """Test that matcher can be reused across multiple texts."""
        matcher = PatternMatcher()

        text1 = "Let's delve into this robust solution"
        text2 = "We should leverage the comprehensive framework"

        # Get patterns once
        patterns = matcher.get_ai_vocab_patterns()

        # Use on multiple texts
        matches1 = sum(len(p.findall(text1)) for p in patterns.values())
        matches2 = sum(len(p.findall(text2)) for p in patterns.values())

        assert matches1 > 0
        assert matches2 > 0
