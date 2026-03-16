"""
AI Vocabulary dimension analyzer.

Detects AI-characteristic vocabulary patterns with tier-weighted scoring.
Extracted from perplexity.py in Story 2.4.0.6.

This dimension identifies specific vocabulary patterns that appear significantly
more frequently in AI-generated text compared to human-written text.

Tier Classification:
- Tier 1 (3× weight): Extremely high AI association (10-20× more frequent)
- Tier 2 (2× weight): High AI association (5-10× more frequent)
- Tier 3 (1× weight): Moderate AI association (2-5× more frequent)

Weight: 3.0% of total score
Tier: CORE
"""

import re
from typing import Any, Dict, List, Optional

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import VocabInstance
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils.text_processing import count_words

# Tier 1 - Extremely High AI Association (14 patterns, 3× weight)
TIER_1_PATTERNS = [
    "delve",
    "robust",
    "leverage",
    "harness",
    "underscore",
    "holistic",
    "myriad",
    "plethora",
    "quintessential",
    "paramount",
    "foster",
    "realm",
    "tapestry",
    "embark",
]

# Tier 2 - High AI Association (12 patterns, 2× weight)
TIER_2_PATTERNS = [
    "revolutionize",
    "game-changing",
    "cutting-edge",
    "pivotal",
    "intricate",
    "nuanced",
    "multifaceted",
    "comprehensive",
    "innovative",
    "transformative",
    "seamless",
    "dynamic",
]

# Tier 3 - Moderate AI Association (8 patterns, 1× weight)
TIER_3_PATTERNS = [
    "optimize",
    "streamline",
    "facilitate",
    "enhance",
    "mitigate",
    "navigate",
    "ecosystem",
    "landscape",
]

# Human-friendly alternatives for each AI vocabulary word
AI_VOCAB_ALTERNATIVES = {
    # Tier 1
    "delve": ["explore", "examine", "investigate", "look into"],
    "robust": ["strong", "reliable", "sturdy", "solid"],
    "leverage": ["use", "apply", "employ", "utilize"],
    "harness": ["use", "employ", "channel", "direct"],
    "underscore": ["emphasize", "highlight", "stress", "show"],
    "holistic": ["comprehensive", "complete", "integrated", "whole"],
    "myriad": ["many", "countless", "numerous", "various"],
    "plethora": ["many", "abundance", "wealth", "plenty"],
    "quintessential": ["typical", "classic", "perfect example", "ideal"],
    "paramount": ["critical", "essential", "crucial", "vital"],
    "foster": ["encourage", "promote", "support", "develop"],
    "realm": ["area", "field", "domain", "sphere"],
    "tapestry": ["collection", "mixture", "blend", "combination"],
    "embark": ["start", "begin", "undertake", "initiate"],
    # Tier 2
    "revolutionize": ["transform", "change", "improve", "reshape"],
    "game-changing": ["significant", "major", "important", "transformative"],
    "cutting-edge": ["advanced", "modern", "latest", "new"],
    "pivotal": ["key", "crucial", "important", "critical"],
    "intricate": ["complex", "detailed", "elaborate", "complicated"],
    "nuanced": ["subtle", "refined", "detailed", "complex"],
    "multifaceted": ["complex", "varied", "diverse", "many-sided"],
    "comprehensive": ["complete", "thorough", "full", "extensive"],
    "innovative": ["new", "creative", "novel", "original"],
    "transformative": ["significant", "major", "powerful", "impactful"],
    "seamless": ["smooth", "easy", "straightforward", "effortless"],
    "dynamic": ["changing", "active", "energetic", "flexible"],
    # Tier 3
    "optimize": ["improve", "enhance", "fine-tune", "refine"],
    "streamline": ["simplify", "improve", "make efficient", "refine"],
    "facilitate": ["enable", "help", "make easier", "support"],
    "enhance": ["improve", "strengthen", "boost", "increase"],
    "mitigate": ["reduce", "lessen", "minimize", "address"],
    "navigate": ["move through", "handle", "deal with", "manage"],
    "ecosystem": ["environment", "system", "network", "platform"],
    "landscape": ["field", "area", "space", "domain"],
}


class AiVocabularyDimension(DimensionStrategy):
    """
    Analyzes AI-characteristic vocabulary patterns with tier-weighted scoring.

    Weight: 3.0% of total score
    Tier: CORE

    Detects 34 AI vocabulary patterns across 3 tiers:
    - Tier 1 (14 patterns): Extremely high AI association (3× weight)
    - Tier 2 (12 patterns): High AI association (2× weight)
    - Tier 3 (8 patterns): Moderate AI association (1× weight)

    Extracted from perplexity.py in Story 2.4.0.6.
    """

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
        return "ai_vocabulary"

    @property
    def weight(self) -> float:
        """Return dimension weight (5.0% of total score)."""
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.CORE

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Detects AI-characteristic vocabulary patterns with tier-weighted scoring"

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
        Analyze text for AI vocabulary patterns with tier-weighted scoring.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with AI vocabulary analysis results including tier breakdown
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
                tier_metrics = self._analyze_ai_vocabulary_tiered(sample_text)
                sample_results.append(tier_metrics)

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_tier_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            aggregated = self._analyze_ai_vocabulary_tiered(analyzed_text)
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
        Detailed analysis with line numbers and suggestions.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            Dict with detailed analysis including vocab instances with tiers
        """
        vocab_instances = self._analyze_ai_vocabulary_detailed(lines, html_comment_checker)

        return {"vocab_instances": vocab_instances}

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on tier-weighted AI vocabulary frequency.

        Scoring uses threshold-based classification (Group C):
        - Weighted frequency per 1k words: 0-2.0 = HIGH (100), 2.0-8.0 = MEDIUM (linear),
          8.0+ = LOW (25)

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        weighted_per_1k = metrics.get("weighted_per_1k", 0.0)

        # Threshold-based scoring (Group C classification)
        # Expected ranges: Human 0.5-2.0, AI 5.0-15.0
        threshold_low = 2.0
        threshold_high = 8.0

        if weighted_per_1k <= threshold_low:
            score = 100.0  # Excellent - minimal AI vocabulary
        elif weighted_per_1k <= threshold_high:
            # Linear interpolation between thresholds
            range_size = threshold_high - threshold_low
            position = (weighted_per_1k - threshold_low) / range_size
            score = 100.0 - (position * 75.0)  # Scale from 100 to 25
        else:
            score = 25.0  # Poor - heavy AI vocabulary usage

        self._validate_score(score)
        return max(0.0, min(100.0, score))

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations based on score and metrics.

        Args:
            score: Current score from calculate_score()
            metrics: Raw metrics from analyze()

        Returns:
            List of recommendation strings with tier-specific guidance
        """
        recommendations = []
        weighted_per_1k = metrics.get("weighted_per_1k", 0.0)

        if weighted_per_1k >= 2.0:  # Above threshold
            tier_breakdown = metrics.get("tier_breakdown", {})
            tier1_count = tier_breakdown.get("tier1", {}).get("count", 0)
            tier2_count = tier_breakdown.get("tier2", {}).get("count", 0)
            tier3_count = tier_breakdown.get("tier3", {}).get("count", 0)

            # Overall recommendation
            recommendations.append(
                f"Reduce AI vocabulary from {weighted_per_1k:.1f} to <2.0 per 1k words (weighted). "
                f"Found: {tier1_count} Tier-1, {tier2_count} Tier-2, {tier3_count} Tier-3 words"
            )

            # Tier-specific recommendations
            if tier1_count > 0:
                words = tier_breakdown.get("tier1", {}).get("words", [])[:3]
                recommendations.append(
                    f"Priority: Replace {tier1_count} Tier-1 words (3× weight): {', '.join(words)}"
                )

            if tier2_count > 2:
                words = tier_breakdown.get("tier2", {}).get("words", [])[:3]
                recommendations.append(
                    f"Replace {tier2_count} Tier-2 words (2× weight): {', '.join(words)}"
                )

        return recommendations

    def format_display(self, metrics: Dict[str, Any]) -> str:
        """Format AI vocabulary display for reports."""
        total_count = metrics.get("total_count", 0)
        weighted_per_1k = metrics.get("weighted_per_1k", 0.0)
        tier_breakdown = metrics.get("tier_breakdown", {})

        t1 = tier_breakdown.get("tier1", {}).get("count", 0)
        t2 = tier_breakdown.get("tier2", {}).get("count", 0)
        t3 = tier_breakdown.get("tier3", {}).get("count", 0)

        return f"(AI vocab: {total_count} words, {weighted_per_1k:.1f}/1k weighted | T1:{t1} T2:{t2} T3:{t3})"

    def get_tiers(self) -> Dict[str, tuple]:
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
    # INTERNAL ANALYSIS METHODS
    # ========================================================================

    def _analyze_ai_vocabulary_tiered(self, text: str) -> Dict[str, Any]:
        """
        Detect AI vocabulary patterns with tier classification and weighting.

        Args:
            text: Text to analyze

        Returns:
            Dict with tier-weighted metrics
        """
        word_count = count_words(text)

        # Detect patterns for each tier
        tier1_words = self._detect_tier_patterns(text, TIER_1_PATTERNS)
        tier2_words = self._detect_tier_patterns(text, TIER_2_PATTERNS)
        tier3_words = self._detect_tier_patterns(text, TIER_3_PATTERNS)

        # Calculate weighted count
        tier1_count = len(tier1_words)
        tier2_count = len(tier2_words)
        tier3_count = len(tier3_words)

        weighted_count = (tier1_count * 3) + (tier2_count * 2) + (tier3_count * 1)
        total_count = tier1_count + tier2_count + tier3_count

        # Normalize to per 1k words
        weighted_per_1k = (weighted_count / word_count * 1000) if word_count > 0 else 0
        total_per_1k = (total_count / word_count * 1000) if word_count > 0 else 0

        return {
            "total_count": total_count,
            "total_per_1k": round(total_per_1k, 2),
            "weighted_count": weighted_count,
            "weighted_per_1k": round(weighted_per_1k, 2),
            "word_count": word_count,
            "tier_breakdown": {
                "tier1": {"count": tier1_count, "words": tier1_words[:10], "weight": 3},
                "tier2": {"count": tier2_count, "words": tier2_words[:10], "weight": 2},
                "tier3": {"count": tier3_count, "words": tier3_words[:10], "weight": 1},
            },
        }

    def _detect_tier_patterns(self, text: str, tier_patterns: List[str]) -> List[str]:
        """
        Detect patterns for a specific tier.

        Args:
            text: Text to analyze
            tier_patterns: List of pattern strings to detect

        Returns:
            List of detected words
        """
        # Comprehensive pattern mappings for each base word
        pattern_mappings = {
            "delve": r"\bdelv(e|es|ing)\b",
            "robust": r"\brobust(ness)?\b",
            "leverage": r"\bleverag(e|es|ing)\b",
            "harness": r"\bharness(es|ing)?\b",
            "underscore": r"\bunderscore[sd]?\b|\bunderscoring\b",
            "holistic": r"\bholistic(ally)?\b",
            "myriad": r"\bmyriad\b",
            "plethora": r"\bplethora\b",
            "quintessential": r"\bquintessential\b",
            "paramount": r"\bparamount\b",
            "foster": r"\bfoster(s|ed|ing)?\b",
            "realm": r"\brealm(s)?\b",
            "tapestry": r"\btapestr(y|ies)\b",
            "embark": r"\bembark(s|ed|ing)?\b",
            "revolutionize": r"\brevolutioniz(e|es|ed|ing)\b",
            "game-changing": r"\bgame-changing\b",
            "cutting-edge": r"\bcutting-edge\b",
            "pivotal": r"\bpivotal\b",
            "intricate": r"\bintricate(ly)?\b",
            "nuanced": r"\bnuanced?\b",
            "multifaceted": r"\bmultifaceted\b",
            "comprehensive": r"\bcomprehensive(ly)?\b",
            "innovative": r"\binnovative(ly)?\b",
            "transformative": r"\btransformative(ly)?\b",
            "seamless": r"\bseamless(ly)?\b",
            "dynamic": r"\bdynamic(ally|s)?\b",
            "optimize": r"\boptimiz(e|es|ation|ing)\b",
            "streamline": r"\bstreamlin(e|ed|ing)\b",
            "facilitate": r"\bfacilitate[sd]?\b|\bfacilitating\b",
            "enhance": r"\benhance(s|d|ment|ing)?\b",
            "mitigate": r"\bmitigat(e|es|ed|ing|ion)\b",
            "navigate": r"\bnavigat(e|es|ed|ing|ion)\b",
            "ecosystem": r"\becosystem(s)?\b",
            "landscape": r"\blandscape(s)?\b",
        }

        words_found = []

        # Build regex patterns for tier words
        for word in tier_patterns:
            # Get comprehensive pattern or use simple fallback
            pattern = pattern_mappings.get(word, rf"\b{word}(?:s|es|ed|ing)?\b")
            matches = re.finditer(pattern, text, re.IGNORECASE)
            words_found.extend([m.group() for m in matches])

        return words_found

    def _aggregate_sampled_tier_metrics(self, sample_results: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate tier metrics from multiple samples.

        Args:
            sample_results: List of tier metric dicts from samples

        Returns:
            Aggregated tier metrics
        """
        if not sample_results:
            return {
                "total_count": 0,
                "total_per_1k": 0.0,
                "weighted_count": 0,
                "weighted_per_1k": 0.0,
                "word_count": 0,
                "tier_breakdown": {
                    "tier1": {"count": 0, "words": [], "weight": 3},
                    "tier2": {"count": 0, "words": [], "weight": 2},
                    "tier3": {"count": 0, "words": [], "weight": 1},
                },
            }

        # Sum counts across samples
        total_count = sum(r.get("total_count", 0) for r in sample_results)
        weighted_count = sum(r.get("weighted_count", 0) for r in sample_results)
        word_count = sum(r.get("word_count", 0) for r in sample_results)

        # Aggregate tier breakdowns
        tier1_count = sum(
            r.get("tier_breakdown", {}).get("tier1", {}).get("count", 0) for r in sample_results
        )
        tier2_count = sum(
            r.get("tier_breakdown", {}).get("tier2", {}).get("count", 0) for r in sample_results
        )
        tier3_count = sum(
            r.get("tier_breakdown", {}).get("tier3", {}).get("count", 0) for r in sample_results
        )

        # Collect words from all samples
        tier1_words = []
        tier2_words = []
        tier3_words = []

        for r in sample_results:
            tier_breakdown = r.get("tier_breakdown", {})
            tier1_words.extend(tier_breakdown.get("tier1", {}).get("words", []))
            tier2_words.extend(tier_breakdown.get("tier2", {}).get("words", []))
            tier3_words.extend(tier_breakdown.get("tier3", {}).get("words", []))

        # Calculate normalized rates
        weighted_per_1k = (weighted_count / word_count * 1000) if word_count > 0 else 0
        total_per_1k = (total_count / word_count * 1000) if word_count > 0 else 0

        return {
            "total_count": total_count,
            "total_per_1k": round(total_per_1k, 2),
            "weighted_count": weighted_count,
            "weighted_per_1k": round(weighted_per_1k, 2),
            "word_count": word_count,
            "tier_breakdown": {
                "tier1": {"count": tier1_count, "words": tier1_words[:10], "weight": 3},
                "tier2": {"count": tier2_count, "words": tier2_words[:10], "weight": 2},
                "tier3": {"count": tier3_count, "words": tier3_words[:10], "weight": 1},
            },
        }

    def _analyze_ai_vocabulary_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[VocabInstance]:
        """
        Detect AI vocabulary with line numbers, context, and tier classification.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of VocabInstance objects with tier information
        """
        instances = []

        for line_num, line in enumerate(lines, start=1):
            # Skip HTML comments, headings, and code blocks
            if html_comment_checker and html_comment_checker(line):
                continue
            if line.strip().startswith("#") or line.strip().startswith("```"):
                continue

            # Check all tiers
            for _tier_num, tier_patterns in enumerate(
                [TIER_1_PATTERNS, TIER_2_PATTERNS, TIER_3_PATTERNS], 1
            ):
                for word in tier_patterns:
                    pattern = rf"\b{word}(?:s|es|ed|ing)?\b"
                    for match in re.finditer(pattern, line, re.IGNORECASE):
                        matched_word = match.group()
                        # Extract context (20 chars each side)
                        start = max(0, match.start() - 20)
                        end = min(len(line), match.end() + 20)
                        context = f"...{line[start:end]}..."

                        # Get base word for suggestions
                        base_word = word.lower()
                        suggestions = AI_VOCAB_ALTERNATIVES.get(
                            base_word, ["use simpler alternative"]
                        )

                        instances.append(
                            VocabInstance(
                                line_number=line_num,
                                word=matched_word,
                                context=context,
                                full_line=line.strip(),
                                suggestions=suggestions[:5],  # Top 5 suggestions
                            )
                        )

        return instances


# Backward compatibility alias
AiVocabularyAnalyzer = AiVocabularyDimension

# Module-level singleton - triggers self-registration on module import
_instance = AiVocabularyDimension()
