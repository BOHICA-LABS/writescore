"""
Transition Marker dimension analyzer.

Analyzes AI-specific transition patterns that distinguish AI from human text:
- Basic discourse markers: "however" (Human: 0-3 per 1k, AI: 5-10+ per 1k),
  "moreover" (Human: 0-1 per 1k, AI: 3-8+ per 1k)
- Formulaic transitions: "Furthermore", "Moreover", "Additionally", "In conclusion", etc.
- Marker clustering patterns (multiple markers in close proximity)

Refactored in Story 2.4.0.5:
- Pragmatic markers extracted to pragmatic_markers.py
- Formulaic transitions merged from perplexity.py
- Now combines basic + formulaic transitions as unified dimension

Weight: 6.0%
Tier: ADVANCED

These formal transition markers are reliable AI signatures.
Human writers use them sparingly, while AI models overuse them.

Requires dependencies: re (standard library)

Version History:
- v2.0.0 (v6.0.0): Refactored to combine basic + formulaic transitions (Story 2.4.0.5)
  - Pragmatic markers extracted to pragmatic_markers.py
  - Formulaic transitions merged from perplexity.py
  - Weight reduced from 10% to 6%
  - Composite scoring: 50% basic + 50% formulaic
- v1.2.0 (v5.1.1): Expanded pragmatic marker lexicon - Story 2.2.1 [DEPRECATED - moved to pragmatic_markers.py]
- v1.1.0 (v5.1.0): Added pragmatic markers - Story 2.2 [DEPRECATED - moved to pragmatic_markers.py]
- v1.0.0 (v5.0.0): Basic transition markers (however, moreover) - Story 1.4.5
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import TransitionInstance
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils.pattern_matching import FORMULAIC_TRANSITIONS


class TransitionMarkerDimension(DimensionStrategy):
    """
    Analyzes transition marker patterns: basic discourse markers and formulaic transitions.

    Weight: 6.0% of total score
    Tier: ADVANCED (specialized AI detection pattern)

    Version History:
    - v2.0.0 (v6.0.0): Combined basic + formulaic transitions (Story 2.4.0.5)
    - v1.0.0 (v5.0.0): Basic transition markers (however, moreover)

    Detects:
    - Basic transitions: "however" (AI: 5-10+/1k, Human: 0-3/1k), "moreover" (AI: 3-8+/1k, Human: 0-1/1k)
    - Formulaic transitions: 19 patterns (Furthermore, Moreover, Additionally, In conclusion, etc.)
    - Marker clustering and transition density

    Focuses on structural transition markers that distinguish AI from human writing.
    """

    # ========================================================================
    # SCORING THRESHOLDS - Research-backed baselines
    # ========================================================================

    # Basic transition thresholds (per 1k words)
    # Research: Human 0-3 for however, 0-1 for moreover
    BASIC_TRANSITION_EXCELLENT = 2.0
    BASIC_TRANSITION_GOOD = 4.0
    BASIC_TRANSITION_CONCERNING = 8.0

    # Formulaic transition thresholds (total count)
    # Research: Human 0-1, AI 3+
    FORMULAIC_EXCELLENT = 1
    FORMULAIC_GOOD = 2
    FORMULAIC_CONCERNING = 4

    # Composite scoring weights
    WEIGHT_BASIC = 0.50  # Basic transitions (however, moreover)
    WEIGHT_FORMULAIC = 0.50  # Formulaic transitions

    def __init__(self):
        """Initialize and self-register with dimension registry."""
        super().__init__()
        # Self-register with registry
        DimensionRegistry.register(self)

    # ========================================================================
    # REQUIRED PROPERTIES - DimensionStrategy Contract
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Return dimension identifier."""
        return "transition_marker"

    @property
    def weight(self) -> float:
        """Return dimension weight (5.0% of total score)."""
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes transition markers: basic discourse markers and formulaic transitions"

    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================

    def analyze(
        self,
        text: str,
        lines: Optional[List[str]] = None,
        config: Optional[AnalysisConfig] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Analyze text for transition marker patterns (v2.0.0).

        Analyzes both basic transitions (however, moreover) and formulaic transitions
        (Furthermore, Moreover, Additionally, etc.).

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters (word_count if pre-calculated)

        Returns:
            Dict with transition marker analysis results:
            - basic_transitions: Dict with however/moreover counts and frequencies
            - formulaic_transitions: Dict with formulaic transition analysis
            - total_transitions_per_1k: Combined frequency metric
        """
        config = config or DEFAULT_CONFIG
        total_text_length = len(text)

        # Prepare text based on mode (FAST/ADAPTIVE/SAMPLING/FULL)
        prepared = self._prepare_text(text, config, self.dimension_name)

        # Handle sampled analysis (returns list of (position, sample_text) tuples)
        if isinstance(prepared, list):
            samples = prepared
            sample_results = []

            for _position, sample_text in samples:
                transition_analysis = self._analyze_transitions(sample_text, **kwargs)
                sample_results.append(transition_analysis)

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            aggregated = self._analyze_transitions(analyzed_text, **kwargs)
            analyzed_length = len(analyzed_text)
            samples_analyzed = 1

        # Add consistent metadata
        return {
            **aggregated,
            "available": True,
            "analysis_mode": config.mode.value,
            "samples_analyzed": samples_analyzed,
            "total_text_length": total_text_length,
            "analyzed_text_length": analyzed_length,
            "coverage_percentage": (analyzed_length / total_text_length * 100.0)
            if total_text_length > 0
            else 0.0,
        }

    def analyze_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[TransitionInstance]:
        """
        Detailed analysis with line numbers and suggestions.
        Identifies each transition marker occurrence and clustering patterns.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of TransitionInstance objects
        """
        return self._analyze_stylometric_issues_detailed(lines, html_comment_checker)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def _score_basic_transitions(self, basic: Dict[str, Any]) -> float:
        """
        Score basic transition patterns (however, moreover).

        Human-like: 0-2 per 1k
        AI-like: 5-10+ per 1k

        Args:
            basic: Basic transitions dict from analyze()

        Returns:
            Score 0-100 (higher = more human-like)
        """
        total_per_1k = basic["total_ai_markers_per_1k"]

        if total_per_1k <= self.BASIC_TRANSITION_EXCELLENT:
            return 100.0  # Excellent - human range
        elif total_per_1k <= self.BASIC_TRANSITION_GOOD:
            return 75.0  # Good - upper human range
        elif total_per_1k <= self.BASIC_TRANSITION_CONCERNING:
            return 50.0  # Concerning - lower AI range
        else:
            return 25.0  # Strong AI signature

    def _score_formulaic_transitions(self, formulaic: Dict[str, Any]) -> float:
        """
        Score formulaic transition patterns.

        Human-like: 0-1 instances
        AI-like: 3+ instances

        Args:
            formulaic: Formulaic transitions dict from analyze()

        Returns:
            Score 0-100 (higher = more human-like)
        """
        count = formulaic["count"]

        if count <= self.FORMULAIC_EXCELLENT:
            return 100.0  # Excellent - human range
        elif count <= self.FORMULAIC_GOOD:
            return 75.0  # Good
        elif count <= self.FORMULAIC_CONCERNING:
            return 50.0  # Concerning
        else:
            return 25.0  # Strong AI signature

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score using weighted composite of basic + formulaic transitions (v2.0.0).

        Weighted Components:
        - Basic transitions: 50% (however/moreover)
        - Formulaic transitions: 50% (Furthermore, Moreover, etc.)

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Score both components
        basic_score = self._score_basic_transitions(metrics["basic_transitions"])
        formulaic_score = self._score_formulaic_transitions(metrics["formulaic_transitions"])

        # Weighted composite (equal weight)
        score = basic_score * self.WEIGHT_BASIC + formulaic_score * self.WEIGHT_FORMULAIC

        self._validate_score(score)
        return score

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations based on score and metrics.

        Args:
            score: Current score from calculate_score()
            metrics: Raw metrics from analyze()

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not metrics.get("available", False):
            recommendations.append("Transition marker analysis unavailable.")
            return recommendations

        basic = metrics.get("basic_transitions", {})
        formulaic = metrics.get("formulaic_transitions", {})

        however_per_1k = basic.get("however_per_1k", 0.0)
        moreover_per_1k = basic.get("moreover_per_1k", 0.0)
        total_basic = basic.get("total_ai_markers_per_1k", 0.0)
        formulaic_count = formulaic.get("count", 0)

        # Basic transition recommendations
        if total_basic > self.BASIC_TRANSITION_GOOD:
            recommendations.append(
                f"Reduce basic AI transition markers ({total_basic:.1f} per 1k words, target ≤{self.BASIC_TRANSITION_EXCELLENT}). "
                f"These formal transitions are overused by AI text generators."
            )

        if however_per_1k > 3.0:
            recommendations.append(
                f"High 'however' usage ({however_per_1k:.1f} per 1k, target ≤3.0). "
                f"Replace with: 'but', 'yet', 'still', or natural flow without transition."
            )

        if moreover_per_1k > 1.0:
            recommendations.append(
                f"'Moreover' detected ({moreover_per_1k:.1f} per 1k, target ≤1.0). "
                f"This is a strong AI signature. Replace with: 'also', 'and', 'plus', or remove."
            )

        # Formulaic transition recommendations
        if formulaic_count > self.FORMULAIC_GOOD:
            examples = ", ".join(formulaic.get("transitions", [])[:3])
            recommendations.append(
                f"Reduce formulaic transitions (found {formulaic_count}, target ≤{self.FORMULAIC_EXCELLENT}). "
                f"Examples: {examples}. Use more natural, conversational transitions."
            )

        # Positive feedback
        if score >= 90:
            recommendations.append(
                "Excellent transition marker usage. Text shows natural, human-like transition patterns."
            )

        return recommendations

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """
        Define score tier ranges for this dimension.

        Returns:
            Dict mapping tier name to (min_score, max_score) tuple
        """
        return {
            "excellent": (90.0, 100.0),
            "good": (75.0, 89.9),
            "acceptable": (50.0, 74.9),
            "poor": (0.0, 49.9),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _analyze_transitions(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Comprehensive transition marker analysis (v2.0.0).

        Orchestrates basic and formulaic transition analysis.

        Args:
            text: Text to analyze
            **kwargs: Additional parameters (word_count if pre-calculated)

        Returns:
            Dict with complete transition analysis:
            - basic_transitions: Basic transition marker dict
            - formulaic_transitions: Formulaic transition dict
            - total_transitions_per_1k: Combined metric
        """
        # Calculate word count once (used by both methods)
        total_words = kwargs.get("word_count")
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        # Run both analyses
        basic = self._analyze_basic_transitions(text, word_count=total_words)
        formulaic = self._analyze_formulaic_transitions(text, word_count=total_words)

        # Calculate combined metric
        words_in_thousands = total_words / 1000 if total_words > 0 else 1
        total_transitions = basic["however_count"] + basic["moreover_count"] + formulaic["count"]
        total_transitions_per_1k = (
            total_transitions / words_in_thousands if words_in_thousands > 0 else 0.0
        )

        # Build result
        return {
            "basic_transitions": basic,
            "formulaic_transitions": formulaic,
            "total_transitions_per_1k": total_transitions_per_1k,
        }

    def _analyze_basic_transitions(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze basic AI-specific transition markers (however, moreover).

        Collects:
        - Raw counts of each marker
        - Frequency per 1k words
        - Total combined marker frequency
        """
        result: Dict[str, Any] = {}

        # Count AI-specific markers: however and moreover
        however_pattern = re.compile(r"\bhowever\b", re.IGNORECASE)
        moreover_pattern = re.compile(r"\bmoreover\b", re.IGNORECASE)

        however_count = len(however_pattern.findall(text))
        moreover_count = len(moreover_pattern.findall(text))

        # Calculate per 1k words
        # Use pre-calculated word_count if provided, otherwise calculate
        total_words = kwargs.get("word_count")
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        result["however_count"] = however_count
        result["moreover_count"] = moreover_count
        result["however_per_1k"] = (
            however_count / words_in_thousands if words_in_thousands > 0 else 0.0
        )
        result["moreover_per_1k"] = (
            moreover_count / words_in_thousands if words_in_thousands > 0 else 0.0
        )
        result["total_ai_markers_per_1k"] = (
            (however_count + moreover_count) / words_in_thousands if words_in_thousands > 0 else 0.0
        )

        return result

    def _analyze_formulaic_transitions(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze formulaic transition patterns (v2.0.0).

        Detects 19 formulaic transition patterns from utils/pattern_matching.py:
        - Furthermore, Moreover, Additionally, In addition
        - First and foremost, In conclusion, To summarize, In summary
        - It is important to note that, It is worth mentioning that
        - When it comes to, With that said, Having said that
        - etc.

        Human writers: 0-1 instances
        AI writers: 3+ instances

        Args:
            text: Text to analyze
            **kwargs: Additional parameters (word_count if pre-calculated)

        Returns:
            Dict with:
            - count: Total formulaic transitions found
            - transitions: List of transition instances (first 15)
            - per_1k: Transitions per 1000 words
        """
        transitions_found = []

        # Detect all formulaic transitions from shared patterns
        for pattern in FORMULAIC_TRANSITIONS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            transitions_found.extend([m.group() for m in matches])

        # Calculate per 1k words
        total_words = kwargs.get("word_count")
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        return {
            "count": len(transitions_found),
            "transitions": transitions_found[:15],  # Limit to first 15 for readability
            "per_1k": len(transitions_found) / words_in_thousands
            if words_in_thousands > 0
            else 0.0,
        }

    def _analyze_stylometric_issues_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[TransitionInstance]:
        """Detect AI-specific stylometric markers (however, moreover, clustering)."""
        issues = []

        # Track "however" and "moreover" usage
        however_pattern = re.compile(r"\bhowever\b", re.IGNORECASE)
        moreover_pattern = re.compile(r"\bmoreover\b", re.IGNORECASE)

        # Count total words for frequency calculation
        total_words = sum(len(re.findall(r"\b\w+\b", line)) for line in lines)
        total_words / 1000 if total_words > 0 else 1

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip HTML comments (metadata), headings, and code blocks
            if html_comment_checker and html_comment_checker(line):
                continue
            if stripped.startswith("#") or stripped.startswith("```"):
                continue

            # Check for "however" (AI: 5-10 per 1k, Human: 1-3 per 1k)
            however_matches = list(however_pattern.finditer(line))
            for _match in however_matches:
                context = line.strip()
                issues.append(
                    TransitionInstance(
                        line_number=line_num,
                        transition="however",
                        context=context[:120] + "..." if len(context) > 120 else context,
                        suggestions=[
                            'Replace with: "But", "Yet", "Still"',
                            "Use natural flow without transition",
                        ],
                    )
                )

            # Check for "moreover" (AI: 3-7 per 1k, Human: 0-1 per 1k)
            moreover_matches = list(moreover_pattern.finditer(line))
            for _match in moreover_matches:
                context = line.strip()
                issues.append(
                    TransitionInstance(
                        line_number=line_num,
                        transition="moreover",
                        context=context[:120] + "..." if len(context) > 120 else context,
                        suggestions=[
                            'Replace with: "Also", "And", "Plus"',
                            "Remove transition entirely",
                        ],
                    )
                )

            # Check for formulaic transitions
            for pattern in FORMULAIC_TRANSITIONS:
                matches = list(re.finditer(pattern, line, re.IGNORECASE))
                for match in matches:
                    transition = match.group()
                    context = line.strip()
                    issues.append(
                        TransitionInstance(
                            line_number=line_num,
                            transition=transition,
                            context=context[:120] + "..." if len(context) > 120 else context,
                            suggestions=[
                                "Use more natural transition",
                                "Remove formulaic transition",
                            ],
                        )
                    )

        # Check for clusters (multiple "however" in close proximity)
        however_lines = [i for i, line in enumerate(lines, start=1) if however_pattern.search(line)]
        for i in range(len(however_lines) - 1):
            if however_lines[i + 1] - however_lines[i] <= 3:  # Within 3 lines
                issues.append(
                    TransitionInstance(
                        line_number=however_lines[i],
                        transition="however_cluster",
                        context=f"Lines {however_lines[i]}-{however_lines[i+1]}",
                        suggestions=["Vary transitions", "Remove some instances entirely"],
                    )
                )

        return issues


# Backward compatibility alias
TransitionMarkerAnalyzer = TransitionMarkerDimension

# Module-level singleton - triggers self-registration on module import
_instance = TransitionMarkerDimension()
