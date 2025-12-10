"""
Advanced Lexical Diversity dimension analyzer.

Analyzes sophisticated lexical diversity metrics beyond basic Type-Token Ratio:
- HDD (Hypergeometric Distribution D) - most robust diversity metric
- Yule's K - vocabulary richness via frequency distribution
- MATTR (Moving Average Type-Token Ratio) - window-based diversity
- RTTR (Root Type-Token Ratio) - length-independent measure
- Maas - length-corrected TTR

Weight: 14.0% (second highest in ADVANCED tier)
Tier: ADVANCED

Requires dependencies: scipy, textacy, spacy

Research: +8% accuracy improvement over basic TTR/MTLD metrics
Refactored in Story 1.4.5 - Split from AdvancedDimension for single responsibility.
"""

import math
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from scipy.stats import hypergeom
from textacy.text_stats import diversity

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils import load_spacy_model

nlp_spacy = load_spacy_model("en_core_web_sm")


class AdvancedLexicalDimension(DimensionStrategy):
    """
    Analyzes advanced lexical diversity metrics (HDD, Yule's K, MATTR, RTTR, Maas).

    Weight: 14.0% of total score (second highest in ADVANCED tier)
    Tier: ADVANCED

    Detects:
    - Low lexical diversity (HDD <0.7, Yule's K >50)
    - Advanced diversity patterns beyond basic TTR
    - Window-based diversity (MATTR)
    - Length-independent measures (RTTR, Maas)

    Focuses ONLY on advanced lexical metrics - does not collect GLTR metrics.
    This separation (Story 1.4.5) eliminates wasted computation and clarifies purpose.
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
        return "advanced_lexical"

    @property
    def weight(self) -> float:
        """Return dimension weight (8.0% of total score)."""
        return 8.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes advanced lexical diversity (HDD, Yule's K, MATTR, RTTR, Maas)"

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
        Analyze advanced lexical diversity with adaptive behavior.

        HDD/Yule's K calculations can be slow for very long texts (>200k chars).
        This implementation uses adaptive sampling for extreme lengths.

        Modes:
        - FAST: Full analysis (already fast enough for typical docs)
        - ADAPTIVE: Sample only if >200k chars
        - SAMPLING: User-configured sampling
        - FULL: Analyze entire document (may be slow for very long texts)

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = ADAPTIVE)
            **kwargs: Additional parameters

        Returns:
            Dict with advanced lexical analysis results + metadata:
            - hdd_score: Hypergeometric Distribution D (0-1, higher=more diverse)
            - yules_k: Yule's K (lower=more diverse, higher=more repetitive)
            - mattr: Moving Average Type-Token Ratio (window-based diversity)
            - rttr: Root Type-Token Ratio (length-independent)
            - maas: Maas score (length-corrected TTR)
            - vocab_concentration: Top 10% word concentration
            - types: Number of unique words
            - tokens: Total word count
            - analysis_mode: Mode used (fast/adaptive/sampling/full)
            - samples_analyzed: Number of samples processed
            - total_text_length: Full document length
            - analyzed_text_length: Actual chars analyzed
            - coverage_percentage: % of document analyzed
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
                advanced_lexical = self._calculate_advanced_lexical_diversity(sample_text)
                textacy_metrics = self._calculate_textacy_lexical_diversity(sample_text)
                sample_results.append({**advanced_lexical, **textacy_metrics})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            advanced_lexical = self._calculate_advanced_lexical_diversity(analyzed_text)
            textacy_metrics = self._calculate_textacy_lexical_diversity(analyzed_text)
            aggregated = {**advanced_lexical, **textacy_metrics}
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

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on HDD using logit transform + Gaussian scoring.

        Migrated to transform-then-score approach in Story 2.4.1 (Group D).

        Research parameters (Story 2.4.0 literature review):
        - Metric: HDD (Hypergeometric Distribution D, bounded [0,1])
        - Transform: Logit to handle bounded data
        - Target (μ): 2.2 (post-transform, corresponds to HDD ≈ 0.90)
        - Width (σ): 0.8 (wider tolerance for natural variation)
        - Confidence: Medium
        - Rationale: High HDD (≈0.90) indicates optimal lexical diversity

        Algorithm:
        1. Apply logit transformation: logit(HDD) = log(HDD / (1-HDD))
        2. Apply Gaussian scoring on transformed value
        3. Handle boundary cases (HDD=0 or 1) with epsilon

        Higher HDD = more diverse vocabulary = higher score (human-like).
        Lower HDD = repetitive vocabulary = lower score (AI-like).

        Research findings (with corrected HDD formula):
        - Human HDD: 0.85-0.95 (median 0.90)
        - AI HDD: 0.70-0.82 (median 0.76)
        - HDD more robust than TTR for length variation

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Get HDD score (primary indicator for advanced lexical diversity)
        hdd = metrics.get("hdd_score", 0.5)

        # Handle None values (text too short for calculation)
        if hdd is None:
            hdd = 0.5  # Neutral default

        # Apply logit transformation to bounded [0,1] metric
        # This handles the constraint that HDD must be in [0,1]
        logit_hdd = self._logit_transform(hdd)

        # Gaussian scoring on transformed value
        # Target μ=2.2 (corresponds to HDD ≈ 0.90 - high diversity optimal)
        # Width σ=0.8 (wider tolerance for natural variation)
        score = self._gaussian_score(value=logit_hdd, target=2.2, width=0.8)

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
            recommendations.append(
                "Advanced lexical analysis unavailable. Install required dependencies: scipy, textacy, spacy."
            )
            return recommendations

        hdd = metrics.get("hdd_score", 0)
        yules_k = metrics.get("yules_k", 0)
        mattr = metrics.get("mattr", 0)

        if hdd and hdd < 0.85:
            recommendations.append(
                f"Low lexical diversity (HDD: {hdd:.2f}, target >0.85). "
                f"Increase vocabulary variety throughout the text. "
                f"Use more varied word choices and avoid repetition."
            )

        if yules_k and yules_k > 50:
            recommendations.append(
                f"High vocabulary repetition (Yule's K: {yules_k:.1f}, target <50). "
                f"Reduce word frequency patterns. Use synonyms and varied expressions."
            )

        if mattr and mattr < 0.70:
            recommendations.append(
                f"Low moving-average diversity (MATTR: {mattr:.3f}, target >=0.70). "
                f"Maintain lexical variety throughout text, not just at the beginning."
            )

        if hdd and hdd > 0.85 and yules_k and yules_k < 50:
            recommendations.append(
                f"Excellent lexical diversity (HDD: {hdd:.2f}, Yule's K: {yules_k:.1f}). "
                f"Text shows strong human-like vocabulary variation."
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
            "good": (70.0, 89.9),
            "acceptable": (50.0, 69.9),
            "poor": (0.0, 49.9),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _calculate_advanced_lexical_diversity(self, text: str) -> Dict:
        """
        Calculate advanced lexical diversity metrics using scipy.

        HDD (Hypergeometric Distribution D):
        - Most robust lexical diversity metric
        - AI: 0.40-0.55, Human: 0.65-0.85
        - Accounts for text length and vocabulary distribution

        Yule's K:
        - Vocabulary richness via frequency distribution
        - AI: 100-150, Human: 60-90
        - Lower = more diverse, higher = more repetitive

        Research: +8% accuracy improvement over TTR/MTLD
        """
        try:
            # Remove code blocks and extract words
            text = re.sub(r"```[\s\S]*?```", "", text)
            words = re.findall(r"\b[a-z]{3,}\b", text.lower())

            if len(words) < 50:
                return {}  # Not enough text for reliable metrics

            # Calculate word frequencies
            word_freq = Counter(words)
            N = len(words)  # Total tokens
            V = len(word_freq)  # Unique tokens (types)

            # ============================================================
            # 1. HDD (Hypergeometric Distribution D)
            # ============================================================
            # HDD = (sum of P(word drawn at least once in 42-token sample))
            # More robust than TTR because it's sample-size independent
            sample_size = 42  # Standard HDD sample size
            if sample_size > N:
                hdd_score = None
            else:
                hdd_sum = 0.0
                for _word, count in word_freq.items():
                    # Probability word is NOT drawn in sample
                    # P(not drawn) = hypergeom.pmf(0, N, count, sample_size)
                    prob_not_drawn = hypergeom.pmf(0, N, count, sample_size)
                    # P(drawn at least once) = 1 - P(not drawn)
                    prob_drawn = 1.0 - prob_not_drawn
                    hdd_sum += prob_drawn

                hdd_score = round(hdd_sum / sample_size, 3)

            # ============================================================
            # 2. Yule's K (Vocabulary Richness)
            # ============================================================
            # K = 10^4 * (M2 - M1) / M1^2
            # where M1 = sum of frequencies, M2 = sum of (freq * (freq - 1))
            M1 = N
            M2 = sum(freq * (freq - 1) for freq in word_freq.values())

            if M1 > 0:
                yules_k = 10000 * (M2 - M1) / (M1**2)
                yules_k = round(yules_k, 2)
            else:
                yules_k = None

            # ============================================================
            # 3. Maas (Length-Corrected TTR)
            # ============================================================
            # Maas = (log(N) - log(V)) / log(N)^2
            # Less affected by text length than raw TTR
            if N > 0 and V > 0:
                maas_score = (math.log(N) - math.log(V)) / (math.log(N) ** 2)
                maas_score = round(maas_score, 3)
            else:
                maas_score = None

            # ============================================================
            # 4. Vocabulary Concentration (Zipfian Analysis)
            # ============================================================
            # Measure how concentrated vocabulary is in high-frequency words
            # AI text tends to have higher concentration (more repetitive)
            sorted_freqs = sorted(word_freq.values(), reverse=True)
            top_10_percent = max(1, V // 10)
            top_10_concentration = sum(sorted_freqs[:top_10_percent]) / N

            return {
                "hdd_score": hdd_score,
                "yules_k": yules_k,
                "maas_score": maas_score,
                "vocab_concentration": round(top_10_concentration, 3),
            }
        except Exception as e:
            print(f"Warning: Advanced lexical diversity calculation failed: {e}", file=sys.stderr)
            return {}

    def _calculate_textacy_lexical_diversity(self, text: str) -> Dict:
        """
        Calculate MATTR and RTTR using textacy (Advanced lexical diversity metrics).

        NOTE: This method no longer truncates text - truncation/sampling
        is handled by caller via _prepare_text().

        MATTR (Moving Average Type-Token Ratio):
        - Window size 100 (research-validated default)
        - AI: <0.65, Human: ≥0.70
        - 0.89 correlation with human judgments (McCarthy & Jarvis, 2010)

        RTTR (Root Type-Token Ratio):
        - RTTR = Types / √Tokens
        - Length-independent measure
        - AI: <7.5, Human: ≥7.5

        Args:
            text: Text to analyze (pre-truncated/sampled by caller)

        Returns:
            Dict with mattr, rttr, scores, and assessments
        """
        try:
            # Remove code blocks for accurate text analysis
            text_clean = re.sub(r"```[\s\S]*?```", "", text)

            # Process with spaCy (now processes full text, pre-truncated/sampled by caller)
            doc = nlp_spacy(text_clean)

            # Calculate MATTR (segment size 100 is research-validated)
            # Using textacy's segmented_ttr with moving-avg variant (MATTR)
            try:
                mattr = diversity.segmented_ttr(doc, segment_size=100, variant="moving-avg")
            except Exception as e:
                # Fallback if text too short for segment size 100
                print(
                    f"Warning: MATTR calculation failed, trying smaller segment: {e}",
                    file=sys.stderr,
                )
                try:
                    # Try smaller segment size
                    mattr = diversity.segmented_ttr(doc, segment_size=50, variant="moving-avg")
                except Exception:
                    mattr = 0.0

            # Calculate RTTR
            # Count only alphabetic tokens for consistency
            tokens = [token for token in doc if token.is_alpha and not token.is_stop]
            types = {token.text.lower() for token in tokens}
            n_tokens = len(tokens)
            n_types = len(types)

            rttr = n_types / (n_tokens**0.5) if n_tokens > 0 else 0.0

            # Score MATTR (12 points max)
            if mattr >= 0.75:
                mattr_score, mattr_assessment = 12.0, "EXCELLENT"
            elif mattr >= 0.70:
                mattr_score, mattr_assessment = 9.0, "GOOD"
            elif mattr >= 0.65:
                mattr_score, mattr_assessment = 5.0, "FAIR"
            else:
                mattr_score, mattr_assessment = 0.0, "POOR"

            # Score RTTR (8 points max)
            if rttr >= 8.5:
                rttr_score, rttr_assessment = 8.0, "EXCELLENT"
            elif rttr >= 7.5:
                rttr_score, rttr_assessment = 6.0, "GOOD"
            elif rttr >= 6.5:
                rttr_score, rttr_assessment = 3.0, "FAIR"
            else:
                rttr_score, rttr_assessment = 0.0, "POOR"

            return {
                "available": True,
                "mattr": round(mattr, 3),
                "mattr_score": mattr_score,
                "mattr_assessment": mattr_assessment,
                "rttr": round(rttr, 2),
                "rttr_score": rttr_score,
                "rttr_assessment": rttr_assessment,
                "types": n_types,
                "tokens": n_tokens,
            }
        except Exception as e:
            print(f"Warning: Textacy lexical diversity calculation failed: {e}", file=sys.stderr)
            return {
                "available": False,
                "mattr": 0.0,
                "mattr_score": 0.0,
                "mattr_assessment": "ERROR",
                "rttr": 0.0,
                "rttr_score": 0.0,
                "rttr_assessment": "ERROR",
            }


# Backward compatibility alias
AdvancedLexicalAnalyzer = AdvancedLexicalDimension

# Module-level singleton - triggers self-registration on module import
_instance = AdvancedLexicalDimension()
