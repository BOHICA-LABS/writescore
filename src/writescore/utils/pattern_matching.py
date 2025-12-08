"""
Pattern matching utilities and constants.

This module contains all regex patterns and constants used for detecting
AI-generated content markers.
"""

import re
from typing import Dict, List, Optional

# ============================================================================
# AI VOCABULARY PATTERNS
# ============================================================================

AI_VOCABULARY = [
    # Tier 1 - Extremely High AI Association
    r"\bdelv(e|es|ing)\b",
    r"\brobust(ness)?\b",
    r"\bleverag(e|es|ing)\b",
    r"\bharness(es|ing)?\b",
    r"\bunderscore[sd]?\b",
    r"\bunderscoring\b",
    r"\bfacilitate[sd]?\b",
    r"\bfacilitating\b",
    r"\bpivotal\b",
    r"\bholistic(ally)?\b",
    # Tier 2 - High AI Association
    r"\bseamless(ly)?\b",
    r"\bcomprehensive(ly)?\b",
    r"\boptimiz(e|es|ation|ing)\b",
    r"\bstreamlin(e|ed|ing)\b",
    r"\bparamount\b",
    r"\bquintessential\b",
    r"\bmyriad\b",
    r"\bplethora\b",
    r"\butiliz(e|es|ation|ing)\b",
    r"\bcommence[sd]?\b",
    r"\bendeavor[sd]?\b",
    # Tier 3 - Context-Dependent
    r"\binnovative\b",
    r"\bcutting-edge\b",
    r"\brevolutionary\b",
    r"\bgame-changing\b",
    r"\btransformative\b",
    # Additional AI markers
    r"\bdive deep\b",
    r"\bdeep dive\b",
    r"\bunpack(s|ing)?\b",
    r"\bat the end of the day\b",
    r"\bsynerg(y|istic)\b",
    r"\becosystem\b",
    r"\blandscape\b",
    r"\bspace\s+\(",
    r"\bparadigm\s+shift\b",
]

# Formulaic transitions (from ai-detection-patterns.md)
FORMULAIC_TRANSITIONS = [
    r"\bFurthermore,",
    r"\bMoreover,",
    r"\bAdditionally,",
    r"\bIn addition,",
    r"\bIt is important to note that\b",
    r"\bIt is worth mentioning that\b",
    r"\bWhen it comes to\b",
    r"\bOne of the key aspects\b",
    r"\bFirst and foremost,",
    r"\bIn conclusion,",
    r"\bTo summarize,",
    r"\bIn summary,",
    r"\bAs mentioned earlier,",
    r"\bAs we have seen,",
    r"\bIt should be noted that\b",
    r"\bWith that said,",
    r"\bHaving said that\b",
    r"\bIn today\'s world,",
    r"\bIn the modern era,",
]

# Domain-specific technical terms (customizable per project)
DOMAIN_TERMS_DEFAULT = [
    # Example cybersecurity terms - customize for your domain
    r"\bTriton\b",
    r"\bTrisis\b",
    r"\bSIS\b",
    r"\bPLC\b",
    r"\bSCADA\b",
    r"\bDCS\b",
    r"\bICS\b",
    r"\bOT\b",
    r"\bransomware\b",
    r"\bmalware\b",
    r"\bNIST\b",
    r"\bISA\b",
    r"\bIEC\b",
    r"\bMITRE\b",
    r"\bSOC\b",
    r"\bSIEM\b",
    r"\bIDS\b",
    r"\bIPS\b",
]

# AI vocabulary replacement suggestions
AI_VOCAB_REPLACEMENTS = {
    "delve": ["explore", "examine", "investigate", "study"],
    "robust": ["strong", "solid", "reliable", "effective"],
    "leverage": ["use", "apply", "employ", "utilize"],
    "harness": ["use", "apply", "employ"],
    "underscore": ["emphasize", "highlight", "stress", "show"],
    "facilitate": ["enable", "help", "allow", "support"],
    "pivotal": ["key", "crucial", "important", "critical"],
    "holistic": ["complete", "comprehensive", "full", "overall"],
    "seamless": ["smooth", "integrated", "unified"],
    "comprehensive": ["complete", "thorough", "full"],
    "optimize": ["improve", "enhance", "refine"],
    "streamline": ["simplify", "improve", "refine"],
    "paramount": ["essential", "critical", "vital"],
    "quintessential": ["classic", "typical", "ideal"],
    "myriad": ["many", "numerous", "countless"],
    "plethora": ["abundance", "many", "numerous"],
    "utilize": ["use", "employ", "apply"],
    "commence": ["start", "begin"],
    "endeavor": ["effort", "attempt", "try"],
}


# ============================================================================
# COMPILED PATTERN CLASS
# ============================================================================


class PatternMatcher:
    """Pre-compiled regex patterns for efficient pattern matching."""

    def __init__(self, domain_terms: Optional[List[str]] = None):
        """
        Initialize pattern matcher with optional custom domain terms.

        Args:
            domain_terms: Optional list of domain-specific terms
        """
        self.domain_terms = domain_terms or DOMAIN_TERMS_DEFAULT

        # Pre-compile all regex patterns (significant performance improvement)
        # AI Vocabulary patterns
        self._ai_vocab_patterns = {
            pattern: re.compile(pattern, re.IGNORECASE) for pattern in AI_VOCABULARY
        }

        # Formulaic transition patterns
        self._transition_patterns = [re.compile(pattern) for pattern in FORMULAIC_TRANSITIONS]

        # Domain term patterns
        self._domain_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.domain_terms
        ]

        # Formatting patterns
        self._bold_pattern = re.compile(r"\*\*[^*]+\*\*|__[^_]+__")
        self._italic_pattern = re.compile(r"\*[^*]+\*|_[^_]+_")
        self._em_dash_pattern = re.compile(r"—|--")

        # HTML comment pattern (metadata blocks to ignore)
        self._html_comment_pattern = re.compile(r"<!--.*?-->", re.DOTALL)

        # Text analysis patterns
        self._word_pattern = re.compile(r"\b[a-zA-Z]+\b")
        self._heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        # Punctuation patterns
        self._oxford_comma_pattern = re.compile(r",\s+and\b")
        self._serial_comma_pattern = re.compile(r",\s+[^,]+,\s+and\b")

        # First-person patterns
        self._first_person_pattern = re.compile(r"\b(I|we|my|our|me|us)\b", re.IGNORECASE)
        self._second_person_pattern = re.compile(r"\b(you|your|yours)\b", re.IGNORECASE)
        self._contraction_pattern = re.compile(r"\b\w+'\w+\b")

    def get_ai_vocab_patterns(self) -> Dict[str, re.Pattern]:
        """Get compiled AI vocabulary patterns."""
        return self._ai_vocab_patterns

    def get_transition_patterns(self) -> List[re.Pattern]:
        """Get compiled formulaic transition patterns."""
        return self._transition_patterns

    def get_domain_patterns(self) -> List[re.Pattern]:
        """Get compiled domain term patterns."""
        return self._domain_patterns

    @property
    def bold_pattern(self) -> re.Pattern:
        """Get bold formatting pattern."""
        return self._bold_pattern

    @property
    def italic_pattern(self) -> re.Pattern:
        """Get italic formatting pattern."""
        return self._italic_pattern

    @property
    def em_dash_pattern(self) -> re.Pattern:
        """Get em-dash pattern."""
        return self._em_dash_pattern

    @property
    def word_pattern(self) -> re.Pattern:
        """Get word extraction pattern."""
        return self._word_pattern

    @property
    def heading_pattern(self) -> re.Pattern:
        """Get heading pattern."""
        return self._heading_pattern

    @property
    def first_person_pattern(self) -> re.Pattern:
        """Get first-person pronoun pattern."""
        return self._first_person_pattern

    @property
    def second_person_pattern(self) -> re.Pattern:
        """Get second-person pronoun pattern."""
        return self._second_person_pattern

    @property
    def contraction_pattern(self) -> re.Pattern:
        """Get contraction pattern."""
        return self._contraction_pattern
