"""
Readability dimension analyzer.

Analyzes text readability and complexity using established readability metrics:
- Flesch Reading Ease (primary scoring metric)
- Flesch-Kincaid Grade Level
- Automated Readability Index
- Average word length
- Average sentence length
- Syllable patterns

Weight: 10.0% (promoted to CORE tier - fundamental text property)
Tier: CORE

AI text tends toward specific readability ranges (observed: 60-70 Flesch).
Extreme values (<30 or >90) indicate AI signature.

Requires dependencies: textstat, nltk

Refactored in Story 1.4.5 - Split from StylometricDimension for single responsibility.
"""

import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Required imports
import textstat

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier


class ReadabilityDimension(DimensionStrategy):
    """
    Analyzes text readability via Flesch-Kincaid and related metrics.

    Weight: 10.0% of total score
    Tier: CORE (fundamental text property applicable to all documents)

    Detects:
    - Extreme readability values (<30 or >90 Flesch = AI signature)
    - Consistent mid-range clustering (60-70 = neutral, common in AI)
    - Natural variation in readability (human-like)

    Focuses ONLY on readability metrics - does not collect transition markers.
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
        return "readability"

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
        return "Analyzes text readability using Flesch-Kincaid and related metrics"

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
        Analyze text for readability patterns.

        ONLY collects readability metrics (no transition markers).
        This focused approach eliminates wasted computation.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with readability analysis results:
            - flesch_reading_ease: Flesch Reading Ease score (0-100)
            - flesch_kincaid_grade: Flesch-Kincaid Grade Level
            - automated_readability_index: ARI score
            - avg_word_length: Average word length in characters
            - avg_sentence_length: Average sentence length in words
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
                readability = self._analyze_readability_patterns(sample_text)
                sample_results.append(readability)

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            readability = self._analyze_readability_patterns(analyzed_text)
            aggregated = readability
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
        Calculate 0-100 score based on Flesch-Kincaid Grade Level using Gaussian scoring.

        Migrated to Gaussian scoring in Story 2.4.1 based on research findings.
        Switched from Flesch Reading Ease to FK Grade Level per research recommendations.

        Research parameters (Story 2.4.0 literature review):
        - Target (μ): 9.0 (general readability sweet spot, grade 8-10)
        - Width (σ): 2.5 (±2 grades tolerance)
        - Confidence: High (well-established metric)
        - Rationale: Symmetric optimum (too simple = childish, too complex = inaccessible)

        Domain-specific variants noted in research (not yet implemented):
        - Academic: μ=12.0 (higher complexity acceptable)
        - Social Media: μ=7.0 (lower complexity expected)
        - Business: μ=10.0 (moderate complexity)

        Algorithm:
        - Uses Gaussian distribution: score = exp(-0.5 × ((value - μ) / σ)²)
        - Grade level near 9.0 scores highest
        - Extreme simplicity or complexity both score lower

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Score on Flesch-Kincaid Grade Level (not Reading Ease)
        # Migrated from Flesch Reading Ease in Story 2.4.1
        fk_grade = metrics.get("flesch_kincaid_grade", 9.0)

        # Gaussian scoring with research-based parameters
        # Target μ=9.0, Width σ=2.5 (Story 2.4.1, AC3)
        # _gaussian_score() returns 0-100 scale directly
        score = self._gaussian_score(value=fk_grade, target=9.0, width=2.5)

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
                "Readability analysis unavailable. Install required dependencies: textstat, nltk."
            )
            return recommendations

        flesch = metrics.get("flesch_reading_ease", 60.0)
        grade = metrics.get("flesch_kincaid_grade", 8.0)

        if flesch < 30:
            recommendations.append(
                f"Extremely low readability (Flesch: {flesch:.1f}, grade {grade:.1f}). "
                f"Text is very difficult to read. This extreme complexity can be an AI signature. "
                f"Simplify sentence structure and use more common words."
            )

        if flesch > 90:
            recommendations.append(
                f"Extremely high readability (Flesch: {flesch:.1f}). "
                f"Text is overly simple. This extreme simplicity can be an AI signature. "
                f"Add more varied sentence structures and vocabulary complexity."
            )

        if 60 <= flesch <= 70:
            recommendations.append(
                f"Standard mid-range readability (Flesch: {flesch:.1f}, grade {grade:.1f}). "
                f"While acceptable, this range is common in AI text. "
                f"Consider varying sentence complexity for more natural flow."
            )

        if 40 <= flesch <= 60 or 70 <= flesch <= 80:
            recommendations.append(
                f"Good readability variation (Flesch: {flesch:.1f}). "
                f"Text shows natural complexity. Maintain this variety."
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

    def _analyze_readability_patterns(self, text: str) -> Dict:
        """
        Analyze readability patterns using textstat.

        Collects:
        - Flesch Reading Ease (0-100, higher = easier)
        - Flesch-Kincaid Grade Level (US grade level)
        - Automated Readability Index
        - Gunning Fog Index
        - SMOG Index
        - Average word/sentence length
        """
        result = {
            "flesch_reading_ease": 60.0,  # Default neutral
            "flesch_kincaid_grade": 8.0,
            "automated_readability_index": 8.0,
            "gunning_fog": 8.0,
            "smog_index": 8.0,
            "avg_word_length": 0.0,
            "avg_sentence_length": 0.0,
        }

        try:
            # Calculate readability metrics
            result["flesch_reading_ease"] = textstat.flesch_reading_ease(text)
            result["flesch_kincaid_grade"] = textstat.flesch_kincaid_grade(text)
            result["automated_readability_index"] = textstat.automated_readability_index(text)
            result["gunning_fog"] = textstat.gunning_fog(text)
            result["smog_index"] = textstat.smog_index(text)

            # Calculate basic statistics
            words = re.findall(r"\b\w+\b", text)
            sentences = re.split(r"[.!?]+", text)
            sentences = [s for s in sentences if s.strip()]  # Remove empty

            if words:
                total_chars = sum(len(word) for word in words)
                result["avg_word_length"] = round(total_chars / len(words), 2)

            if sentences and words:
                result["avg_sentence_length"] = round(len(words) / len(sentences), 2)

            # Calculate syllables (for additional context)
            try:
                syllable_count = textstat.syllable_count(text)
                result["syllable_count"] = syllable_count
                if words:
                    result["avg_syllables_per_word"] = round(syllable_count / len(words), 2)
            except Exception:
                pass

        except Exception as e:
            print(f"Warning: Readability calculation failed: {e}", file=sys.stderr)
            pass

        return result


# Backward compatibility alias
ReadabilityAnalyzer = ReadabilityDimension

# Module-level singleton - triggers self-registration on module import
_instance = ReadabilityDimension()
