"""
Voice dimension analyzer.

Analyzes voice and authenticity markers:
- First-person perspective (I, we, my, our)
- Direct address (you, your)
- Contractions
- Technical domain expertise

Human writing shows personal voice, while AI tends toward impersonal formality.

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.scoring.dual_score import THRESHOLDS


class VoiceDimension(DimensionStrategy):
    """
    Analyzes voice dimension - first-person, direct address, contractions, technical depth.

    Weight: 5.0% of total score
    Tier: CORE

    Detects:
    - Personal voice markers (first-person, direct address)
    - Conversational tone (contractions)
    - Technical domain expertise (via domain_terms)
    """

    def __init__(self, domain_terms: Optional[List[str]] = None):
        """
        Initialize voice analyzer with optional domain terms.

        Args:
            domain_terms: Optional list of domain-specific technical terms to detect.
                         Supports regex patterns for flexible matching.
                         Example: ['bmachine learningb', 'bneural networkb']
        """
        super().__init__()
        # Store domain terms before registration
        self.domain_terms = domain_terms or []
        # Self-register with registry
        DimensionRegistry.register(self)

    # ========================================================================
    # REQUIRED PROPERTIES - DimensionStrategy Contract
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Return dimension identifier."""
        return "voice"

    @property
    def weight(self) -> float:
        """Return dimension weight (7.0% of total score)."""
        return 7.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.CORE

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes personal voice, conversational tone, and domain expertise"

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
        Analyze text for voice patterns.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with voice analysis results
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
                voice = self._analyze_voice(sample_text)
                technical = self._analyze_technical_depth(sample_text)
                sample_results.append({"voice": voice, "technical_depth": technical})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            voice = self._analyze_voice(analyzed_text)
            technical = self._analyze_technical_depth(analyzed_text)
            aggregated = {
                "voice": voice,
                "technical_depth": technical,
            }
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

    def analyze_detailed(self, lines: List[str], html_comment_checker=None) -> Dict[str, Any]:
        """
        Detailed analysis - voice typically doesn't need line-level detail.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            Dict with summary analysis
        """
        # Voice analysis is typically aggregate, not line-by-line
        text = "n".join(lines)
        return self.analyze(text, lines)

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate voice score.

        Human writing shows personal voice through first-person perspective,
        direct address, and contractions. AI tends toward impersonal formality.

        Args:
            analysis_results: Results dict with voice metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        from writescore.utils.text_processing import safe_ratio

        markers = 0

        first_person = analysis_results.get("first_person", 0)
        direct_address = analysis_results.get("direct_address", 0)
        contractions = analysis_results.get("contractions", 0)
        total_words = analysis_results.get("total_words", 1)

        # First person or direct address
        if first_person > 0 or direct_address > 10:
            markers += 1

        # Contractions (indicates conversational tone)
        contraction_ratio = safe_ratio(contractions, total_words, 0) * 100
        if contraction_ratio > THRESHOLDS.CONTRACTION_RATIO_GOOD:  # >1% contraction use
            markers += 1

        # Check for both types of engagement
        if first_person > 0 and direct_address > 10:
            markers += 1

        if markers >= 3:
            return (10.0, "EXCELLENT")
        elif markers == 2:
            return (7.0, "GOOD")
        elif markers == 1:
            return (4.0, "NEEDS WORK")
        else:
            return (2.0, "POOR")

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on contraction ratio using monotonic scoring.

        Migrated to monotonic increasing scoring in Story 2.4.1 (Group D).

        Research parameters (Story 2.4.0 literature review):
        - Metric: Contraction ratio (contractions / total_words)
        - Threshold low: 0.005 (0.5%, AI writing)
        - Threshold high: 0.015 (1.5%, human writing)
        - Direction: Increasing (higher ratio = more conversational = more human-like)
        - Confidence: Medium
        - Rationale: Contractions indicate conversational, personal voice

        Algorithm:
        Uses monotonic increasing scoring with three zones:
        - Below 0.005: Score 25.0 (formal AI writing)
        - Between 0.005-0.015: Linear 25-75 (transition zone)
        - Above 0.015: Asymptotic 75-100 (conversational human writing)

        Higher contraction ratio = more conversational = more human-like = higher score.
        Lower contraction ratio = more formal = more AI-like = lower score.

        Research findings:
        - Human writing: 1-3% contractions (conversational tone)
        - AI writing: 0-0.5% contractions (formal, academic tone)
        - Contractions are primary indicator of personal voice

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        from writescore.utils.text_processing import safe_ratio

        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        voice = metrics.get("voice", {})
        contractions = voice.get("contractions", 0)

        # Use actual word count from analysis, fallback to estimation if not available
        total_words = voice.get("total_words", max(contractions, 100))

        # Calculate contraction ratio
        contraction_ratio = safe_ratio(contractions, total_words, 0)

        # Monotonic increasing scoring: higher values = higher scores
        # threshold_low=0.005 (AI), threshold_high=0.015 (human)
        score = self._monotonic_score(
            value=contraction_ratio, threshold_low=0.005, threshold_high=0.015, increasing=True
        )

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
        from writescore.utils.text_processing import safe_ratio

        recommendations = []

        voice = metrics.get("voice", {})
        first_person = voice.get("first_person", 0)
        direct_address = voice.get("direct_address", 0)
        contractions = voice.get("contractions", 0)

        # Use actual word count from analysis, fallback to estimation if not available
        total_words = voice.get(
            "total_words", max(first_person + direct_address + contractions, 100)
        )
        contraction_ratio = safe_ratio(contractions, total_words, 0) * 100

        if first_person == 0 and direct_address < 10:
            recommendations.append(
                "Add personal voice markers. Use first-person perspective (I, we, my) or "
                "direct address (you, your) to create engagement and authenticity."
            )

        if first_person == 0:
            recommendations.append(
                "Consider adding first-person perspective (I, we, my, our) to show "
                "personal investment and authentic voice."
            )

        if direct_address < 10:
            recommendations.append(
                f"Increase direct address usage (currently {direct_address} instances). "
                f"Use 'you' and 'your' to engage readers directly."
            )

        if contraction_ratio < THRESHOLDS.CONTRACTION_RATIO_GOOD:
            recommendations.append(
                f"Use more contractions ({contraction_ratio:.1f}%, target >{THRESHOLDS.CONTRACTION_RATIO_GOOD}%). "
                f"Contractions like don't, can't, it's create conversational tone."
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

    def _analyze_voice(self, text: str) -> Dict:
        """Analyze voice and authenticity markers."""
        first_person = len(
            re.findall(
                r"\b(I|we|my|our|us|me|I've|I'm|we've|I'd|we're|I'll|we'll)\b", text, re.IGNORECASE
            )
        )

        direct_address = len(
            re.findall(r"\b(you|your|you're|you'll|you've|you'd)\b", text, re.IGNORECASE)
        )

        # Count contractions
        contractions = len(
            re.findall(
                r"\b\w+'\w+\b",  # Word with apostrophe (simplified)
                text,
            )
        )

        # Calculate actual word count for accurate ratio calculation
        words = re.findall(r"\b\w+\b", text)
        total_words = len(words)

        return {
            "first_person": first_person,
            "direct_address": direct_address,
            "contractions": contractions,
            "total_words": total_words,
        }

    def _analyze_technical_depth(self, text: str) -> Dict:
        """Analyze technical domain expertise signals."""
        terms_found = []
        for pattern in self.domain_terms:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            terms_found.extend([m.group() for m in matches])

        return {
            "count": len(terms_found),
            "terms": terms_found[:20],  # Limit for readability
        }


# Backward compatibility alias
VoiceAnalyzer = VoiceDimension

# Module-level singleton - triggers self-registration on module import
_instance = VoiceDimension()
