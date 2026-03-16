"""
Sentiment dimension analyzer.

Analyzes emotional variation patterns:
- Sentiment variance across text chunks
- Emotional flatness detection (AI signature)
- Average sentiment intensity

AI writing tends to show low emotional variation (variance < 0.10),
while human writing shows natural emotional range (variance > 0.15).

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import statistics
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

# Lazy load transformers
_sentiment_pipeline = None


def get_sentiment_pipeline():
    """Lazy load sentiment analysis pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        from transformers.utils import logging as transformers_logging

        transformers_logging.set_verbosity_error()

        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,  # Use CPU
        )
    return _sentiment_pipeline


class SentimentDimension(DimensionStrategy):
    """
    Analyzes sentiment dimension - emotional variation and flatness.

    Weight: 17.0% of total score
    Tier: SUPPORTING

    Detects:
    - Emotional flatness (AI signature)
    - Sentiment variance across text chunks
    - Monotonous emotional tone
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
        return "sentiment"

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
        return "Analyzes emotional variation patterns and sentiment flatness detection"

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
        Analyze text for sentiment variation patterns.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with sentiment analysis results
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
                sentiment_results = self._analyze_sentiment_variance(sample_text)
                sample_results.append({"sentiment": sentiment_results})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            sentiment_results = self._analyze_sentiment_variance(analyzed_text)
            aggregated = {"sentiment": sentiment_results}
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

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate sentiment variation score.

        Human writing shows emotional variation (variance > 0.15).
        AI tends toward emotional flatness (variance < 0.10).

        Args:
            analysis_results: Results dict with sentiment metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        sentiment = analysis_results.get("sentiment", {})
        variance = sentiment.get("variance", 0.0)

        # Thresholds based on research:
        # Human: variance > 0.15
        # AI: variance < 0.10
        # Gray zone: 0.10 - 0.15

        if variance >= 0.20:
            return (10.0, "VERY HIGH")  # Strong emotional variation
        elif variance >= 0.15:
            return (7.0, "HIGH")  # Good variation (human-like)
        elif variance >= 0.10:
            return (5.0, "MEDIUM")  # Moderate variation
        elif variance >= 0.05:
            return (4.0, "LOW")  # Limited variation (AI-like)
        else:
            return (2.0, "VERY LOW")  # Flat affect (strong AI signal)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on mean sentiment polarity using Gaussian scoring.

        Migrated to Gaussian scoring in Story 2.4.1 based on research findings.
        Switched from variance-based scoring to mean polarity per research recommendations.

        Research parameters (Story 2.4.0 literature review):
        - Target (μ): 0.0 (neutral sentiment optimal for most writing)
        - Width (σ): 0.3 (moderate tolerance)
        - Confidence: High (VADER sentiment analysis well-validated)
        - Rationale: Symmetric optimum at neutral point (neither overly positive nor negative)

        Research observations:
        - AI text: Positive bias (mean +0.1 to +0.2 higher than human)
        - Human text: More neutral on average, higher variance
        - AI shows "optimistic" tone in neutral contexts

        Algorithm:
        - Uses Gaussian distribution: score = exp(-0.5 × ((value - μ) / σ)²)
        - Polarity near 0.0 (neutral) scores highest
        - Positive or negative bias both score lower

        Implementation note:
        - Previous implementation scored on variance (emotional variation)
        - New implementation scores on mean polarity (detecting AI positive bias)
        - Both are valid AI signals - mean polarity aligns with research findings

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        sentiment = metrics.get("sentiment", {})
        mean_polarity = sentiment.get("mean", 0.0)

        # Gaussian scoring with research-based parameters
        # Target μ=0.0 (neutral), Width σ=0.3 (Story 2.4.1, AC3)
        # _gaussian_score() returns 0-100 scale directly
        score = self._gaussian_score(value=mean_polarity, target=0.0, width=0.3)

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

        sentiment = metrics.get("sentiment", {})
        variance = sentiment.get("variance", 0.0)
        mean = sentiment.get("mean", 0.0)
        emotionally_flat = sentiment.get("emotionally_flat", False)

        if emotionally_flat or variance < 0.10:
            recommendations.append(
                f"Emotional flatness detected (variance={variance:.3f}, target ≥0.15). "
                f"This is a strong AI signature. Add emotional variety and natural tonal shifts."
            )

        if variance < 0.15:
            recommendations.append(
                f"Low sentiment variation (variance={variance:.3f}, target ≥0.15). "
                f"Incorporate varied emotional tones: mix analytical, enthusiastic, cautious, and direct passages."
            )

        if abs(mean) > 0.8:
            recommendations.append(
                f"Monotonous emotional tone (mean={mean:.2f}). "
                f"Balance positive and negative sentiments for natural human variation."
            )

        if variance < 0.05:
            recommendations.append(
                "Very flat emotional affect detected. "
                "This suggests mechanical text generation. Rewrite with natural emotional range."
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
            "acceptable": (55.0, 69.9),
            "poor": (0.0, 54.9),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _analyze_sentiment_variance(self, text: str) -> Dict:
        """
        Analyze sentiment variance across text chunks.

        AI writing shows emotional flatness (low variance).
        Human writing shows natural emotional range (high variance).
        """
        pipeline = get_sentiment_pipeline()

        # Split into paragraphs (more meaningful than sentences)
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]

        if len(paragraphs) < 3:
            # Fallback to sentences if too few paragraphs
            import re

            sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 20]
            chunks = sentences[:50]  # Limit for performance
        else:
            chunks = paragraphs[:30]  # Limit for performance

        if len(chunks) < 3:
            # Not enough text to analyze variance
            return {"variance": 0.0, "mean": 0.0, "count": len(chunks), "emotionally_flat": True}

        # Analyze sentiment for each chunk
        # Pipeline returns: [{'label': 'POSITIVE', 'score': 0.9998}]
        sentiments = []
        for chunk in chunks:
            try:
                # Truncate long chunks to avoid token limit
                chunk_text = chunk[:512]
                result = pipeline(chunk_text)[0]

                # Convert to numeric: POSITIVE = +score, NEGATIVE = -score
                score = result["score"]
                if result["label"] == "NEGATIVE":
                    score = -score

                sentiments.append(score)
            except Exception:
                # Skip problematic chunks
                continue

        if len(sentiments) < 3:
            return {
                "variance": 0.0,
                "mean": 0.0,
                "count": len(sentiments),
                "emotionally_flat": True,
            }

        # Calculate variance and mean
        variance = statistics.variance(sentiments)
        mean = statistics.mean(sentiments)

        # Determine if emotionally flat (AI signature)
        emotionally_flat = variance < 0.10

        return {
            "variance": variance,
            "mean": mean,
            "count": len(sentiments),
            "emotionally_flat": emotionally_flat,
            "scores": sentiments[:10],  # Store first 10 for debugging
        }


# Backward compatibility alias
SentimentAnalyzer = SentimentDimension

# Module-level singleton - triggers self-registration on module import
_instance = SentimentDimension()
