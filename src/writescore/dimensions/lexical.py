"""
Lexical dimension analyzer.

Analyzes lexical diversity and vocabulary patterns:
- Type-Token Ratio (TTR)
- Moving Average Type-Token Ratio (MTLD) - more accurate for long texts
- Stemmed diversity (catches word variants)
- Vocabulary richness

Requires optional dependency: nltk (for advanced metrics)

Low lexical diversity (repetitive vocabulary) is an AI signature.

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import nltk
from nltk.stem import PorterStemmer

# Required imports
from nltk.tokenize import word_tokenize

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier


class LexicalDimension(DimensionStrategy):
    """
    Analyzes lexical dimension - vocabulary diversity (TTR, MTLD).

    Weight: 3.0% of total score
    Tier: SUPPORTING

    Detects:
    - Low lexical diversity (repetitive vocabulary - AI signature)
    - Vocabulary richness patterns
    """

    def __init__(self):
        """Initialize and self-register with dimension registry."""
        super().__init__()
        # Self-register with registry
        DimensionRegistry.register(self)
        # Ensure NLTK punkt tokenizer is available
        self._setup_punkt()

    # ========================================================================
    # REQUIRED PROPERTIES - DimensionStrategy Contract
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Return dimension identifier."""
        return "lexical"

    @property
    def weight(self) -> float:
        """Return dimension weight (5.0% of total score)."""
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.SUPPORTING

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes vocabulary diversity using TTR, MTLD, and stemmed diversity"

    # ========================================================================
    # INITIALIZATION HELPERS
    # ========================================================================

    def _setup_punkt(self) -> None:
        """
        Ensure NLTK punkt tokenizer data is available, downloading if necessary.

        Required for word_tokenize() function.
        Following NLTK 3.9.2 best practices for resource management.

        Downloads:
        - punkt_tab: Punkt tokenizer models (~35MB)

        Raises:
            No exceptions - prints warnings and continues if downloads fail.
        """
        try:
            # Test if punkt_tab is accessible by tokenizing a test word
            word_tokenize("test")
        except LookupError:
            # punkt_tab not found - download it
            print("Downloading NLTK punkt tokenizer data (first run only)...", file=sys.stderr)
            try:
                nltk.download("punkt_tab", quiet=True)
                print("✓ Punkt tokenizer setup complete", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to download punkt_tab: {e}", file=sys.stderr)
                print("Tokenization may fail without punkt_tab", file=sys.stderr)

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
        Analyze text for lexical diversity.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with lexical analysis results
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
                lexical = self._analyze_lexical_diversity(sample_text)
                nltk_metrics = self._analyze_nltk_lexical(sample_text)
                lexical.update(nltk_metrics)
                sample_results.append({"lexical_diversity": lexical})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            lexical = self._analyze_lexical_diversity(analyzed_text)
            nltk_metrics = self._analyze_nltk_lexical(analyzed_text)
            lexical.update(nltk_metrics)
            aggregated = {"lexical_diversity": lexical}
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
        Detailed analysis - lexical diversity is typically aggregate.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            Dict with analysis results
        """
        # Lexical analysis is typically aggregate, not line-by-line
        text = "n".join(lines)
        return self.analyze(text, lines)

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate lexical diversity score.

        Args:
            analysis_results: Results dict with TTR metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        ttr = analysis_results.get("diversity", 0.0)

        if ttr >= 0.60:
            return (10.0, "HIGH")
        elif ttr >= 0.45:
            return (7.0, "MEDIUM")
        elif ttr >= 0.30:
            return (4.0, "LOW")
        else:
            return (2.0, "VERY LOW")

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on MTLD (lexical diversity) using monotonic scoring.

        Migrated to monotonic scoring in Story 2.4.1 based on research findings.
        Switched from TTR to MTLD per research recommendations.

        Research parameters (Story 2.4.0 literature review):
        - Metric: MTLD (Measure of Textual Lexical Diversity)
        - Threshold low: 60 (AI-like, low diversity)
        - Threshold high: 100 (human-like, high diversity)
        - Direction: Increasing (higher MTLD = higher score)
        - Confidence: High (MTLD more stable than TTR for long texts)
        - Rationale: Monotonic relationship - higher diversity always better

        MTLD advantages over TTR:
        - Not affected by text length (TTR decreases with length)
        - More stable and reliable for documents >50 words
        - Better discrimination between human and AI writing

        Algorithm:
        - Uses monotonic scoring: score = linear interpolation between thresholds
        - MTLD below 60: Score 0-20 (AI-like)
        - MTLD between 60-100: Score 20-80 (linear transition)
        - MTLD above 100: Score 80-100 (human-like)

        Fallback:
        - If MTLD unavailable (short text), falls back to TTR-based estimation

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        lexical = metrics.get("lexical_diversity", {})
        mtld = lexical.get("mtld_score", 0)

        # If MTLD is available, use it for scoring
        if mtld > 0:
            # Monotonic scoring with research-based parameters
            # Threshold low=60, high=100, direction=increasing
            # _monotonic_score() returns 0-100 scale directly
            score = self._monotonic_score(
                value=mtld, threshold_low=60.0, threshold_high=100.0, increasing=True
            )
        else:
            # Fallback to TTR if MTLD unavailable (short texts)
            ttr = lexical.get("diversity", 0.0)
            # Estimate MTLD from TTR: MTLD ≈ TTR × 140 (rough approximation)
            estimated_mtld = ttr * 140.0
            score = self._monotonic_score(
                value=estimated_mtld, threshold_low=60.0, threshold_high=100.0, increasing=True
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
        recommendations = []

        lexical = metrics.get("lexical_diversity", {})
        ttr = lexical.get("diversity", 0.0)
        unique_words = lexical.get("unique", 0)
        mtld = lexical.get("mtld_score", 0)

        if ttr < 0.45:
            recommendations.append(
                f"Increase vocabulary diversity (TTR={ttr:.2f}, target ≥0.45). "
                f"Use synonyms and varied expressions to avoid repetition."
            )

        if ttr < 0.30:
            recommendations.append(
                f"Very low lexical diversity detected (TTR={ttr:.2f}). "
                f"This is a strong AI signature. Rewrite using more varied vocabulary."
            )

        if mtld > 0 and mtld < 50:
            recommendations.append(
                f"MTLD score is low ({mtld:.1f}). "
                f"Increase vocabulary variety throughout the text, not just locally."
            )

        if unique_words > 0 and unique_words < 100:
            recommendations.append(
                f"Limited vocabulary ({unique_words} unique words). "
                f"Expand word choice and use more specific terminology."
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

    def _analyze_lexical_diversity(self, text: str) -> Dict:
        """Calculate Type-Token Ratio (lexical diversity)."""
        # Remove code blocks
        text = re.sub(r"```[sS]*?```", "", text)
        # Get all words (lowercase for uniqueness)
        words = [w.lower() for w in re.findall(r"\b[\w'-]+\b", text)]

        if not words:
            return {"unique": 0, "diversity": 0.0}

        unique = len(set(words))
        diversity = unique / len(words)

        return {"unique": unique, "diversity": round(diversity, 3)}

    def _analyze_nltk_lexical(self, text: str) -> Dict:
        """Enhanced lexical diversity using NLTK."""
        try:
            # Remove code blocks
            text = re.sub(r"```[sS]*?```", "", text)

            # Tokenize
            words = word_tokenize(text.lower())
            words = [w for w in words if w.isalnum()]  # Keep only alphanumeric

            if not words:
                return {}

            # Calculate MTLD (Moving Average Type-Token Ratio)
            # This is more accurate than simple TTR for longer texts
            mtld = self._calculate_mtld(words)

            # Calculate stemmed diversity (catches word variants)
            stemmer = PorterStemmer()
            stemmed = [stemmer.stem(w) for w in words]
            stemmed_unique = len(set(stemmed))
            stemmed_diversity = stemmed_unique / len(stemmed) if stemmed else 0

            return {"mtld_score": round(mtld, 2), "stemmed_diversity": round(stemmed_diversity, 3)}
        except Exception as e:
            print(f"Warning: NLTK lexical analysis failed: {e}", file=sys.stderr)
            return {}

    def _calculate_mtld(self, words: List[str], threshold: float = 0.72) -> float:
        """Calculate Moving Average Type-Token Ratio (MTLD)."""
        if len(words) < 50:
            return len(set(words)) / len(words) * 100  # Fallback to TTR

        def _mtld_direction(words_list):
            factor = 0
            factor_lengths = []
            types_seen = set()
            tokens = 0

            for word in words_list:
                tokens += 1
                types_seen.add(word)
                if len(types_seen) / tokens < threshold:
                    factor += 1
                    factor_lengths.append(tokens)
                    types_seen = set()
                    tokens = 0

            # Add partial factor
            if tokens > 0:
                factor += (1 - (len(types_seen) / tokens)) / (1 - threshold)

            return (len(words_list) / factor) if factor > 0 else len(words_list)

        # Calculate in both directions and average
        forward = _mtld_direction(words)
        backward = _mtld_direction(words[::-1])

        return float((forward + backward) / 2)


# Backward compatibility alias
LexicalAnalyzer = LexicalDimension

# Module-level singleton - triggers self-registration on module import
_instance = LexicalDimension()
