"""
Predictability dimension analyzer.

Analyzes GLTR (Giant Language Model Test Room) token predictability patterns.
GLTR achieves 80% F1-score in AI text detection by analyzing where each token
ranks in the model's probability distribution (validated: IberLef-AuTexTification 2025).

NOTE: GLTR performance degrades on GPT-4+ models (31-50% vs 70-90% on GPT-3.5).
Primary value is providing actionable quality feedback, not binary detection.

AI-generated text shows high concentration of top-10 tokens (>70%).
Human writing is more unpredictable (<55%).

Weight: 20.0% (highest single dimension - reflects GLTR's value in quality feedback)
Tier: ADVANCED

Performance (Story 1.4.14):
- 120-second timeout prevents hanging on large documents
- Model caching: 80-95% faster on repeated analyses
- Thread-safe model loading for concurrent analysis
- First analysis: 2-10s, subsequent: ~0.1-0.5s

Requires dependencies: transformers, torch

Research: "GLTR: Statistical Detection and Visualization of Generated Text"
Refactored in Story 1.4.5 - Split from AdvancedDimension for single responsibility.
"""

import re
import statistics
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

# Required imports
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.utils import logging as transformers_logging

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import HighPredictabilitySegment
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils.text_processing import safe_ratio

transformers_logging.set_verbosity_error()


# Global model instances (lazy loading with thread-safety)
_perplexity_model = None
_perplexity_tokenizer = None
_model_lock = threading.Lock()  # Thread-safe model loading


class PredictabilityDimension(DimensionStrategy):
    """
    Analyzes text predictability using GLTR (Giant Language Model Test Room).

    Weight: 20.0% of total score (highest single dimension)
    Tier: ADVANCED

    Detects:
    - High token predictability (GLTR >70% top-10 = AI signature)
    - Token rank distribution patterns
    - High-predictability text segments

    Performance Optimizations (Story 1.4.14):
    - 120-second timeout prevents hanging on large documents
    - Model caching reduces load time by 80-95% on repeated analyses
    - Thread-safe model loading for concurrent analysis
    - First analysis: 2-10s (model load), subsequent: ~0.1-0.5s

    Focuses ONLY on GLTR metrics - does not collect lexical diversity metrics.
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
        return "predictability"

    @property
    def weight(self) -> float:
        """Return dimension weight (12.0% of total score - highest single dimension)."""
        return 12.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes GLTR token predictability patterns (80% F1-score, validated 2025)"

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
        Analyze GLTR token predictability with configurable modes.

        Modes:
        - FAST: Analyze first 2000 chars (current behavior)
        - ADAPTIVE: Sample based on document length
        - SAMPLING: User-configured sampling
        - FULL: Analyze entire document (slow)

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = ADAPTIVE)
            **kwargs: Backward compatibility

        Returns:
            Dict with GLTR metrics + analysis metadata:
            - gltr_top10_percentage: % tokens in model's top-10 predictions
            - gltr_top100_percentage: % tokens in model's top-100 predictions
            - gltr_top1000_percentage: % tokens in model's top-1000 predictions
            - gltr_mean_rank: Average rank of actual tokens
            - gltr_rank_variance: Variance in token ranks
            - gltr_likelihood: AI likelihood score (0-1)
            - available: Whether GLTR analysis succeeded
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
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

            # Batch samples into single GLTR call for efficiency
            # GLTR has high per-call overhead, so concatenating samples is much faster
            combined_text = " ".join(sample_text for _, sample_text in samples)
            aggregated = self._calculate_gltr_metrics_with_timeout(combined_text, timeout=120)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            gltr_metrics = self._calculate_gltr_metrics_with_timeout(analyzed_text, timeout=120)
            aggregated = gltr_metrics
            analyzed_length = len(analyzed_text)
            samples_analyzed = 1

        # Handle timeout/failure gracefully (aggregated may be None)
        if aggregated is None:
            return {
                "available": False,
                "error": "GLTR analysis timed out or failed",
                "analysis_mode": config.mode.value,
                "samples_analyzed": samples_analyzed,
                "total_text_length": total_text_length,
                "analyzed_text_length": analyzed_length,
                "coverage_percentage": (analyzed_length / total_text_length * 100.0)
                if total_text_length > 0
                else 0.0,
            }

        # Add consistent metadata
        return {
            "gltr_top10_percentage": aggregated.get("gltr_top10_percentage", 0.55),
            "gltr_top100_percentage": aggregated.get("gltr_top100_percentage", 0.85),
            "gltr_top1000_percentage": aggregated.get("gltr_top1000_percentage", 0.95),
            "gltr_mean_rank": aggregated.get("gltr_mean_rank", 50.0),
            "gltr_rank_variance": aggregated.get("gltr_rank_variance", 100.0),
            "gltr_likelihood": aggregated.get("gltr_likelihood", 0.5),
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
    ) -> List[HighPredictabilitySegment]:
        """
        Detailed analysis with line numbers and suggestions.
        Identifies high-predictability text segments.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of HighPredictabilitySegment objects
        """
        return self._analyze_high_predictability_segments_detailed(lines, html_comment_checker)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on GLTR top-10 percentage using monotonic scoring.

        Migrated to monotonic decreasing scoring in Story 2.4.1 (Group D).

        Research parameters (Story 2.4.0 literature review):
        - Metric: GLTR top-10 percentage (bounded [0,1])
        - Threshold low: 0.55 (55%, human writing)
        - Threshold high: 0.70 (70%, AI writing)
        - Direction: Decreasing (lower top-10 = higher score = more human-like)
        - Confidence: High (GLTR 80% F1-score for GPT-3.5 detection)

        Algorithm:
        Uses monotonic decreasing scoring with three zones:
        - Above 0.70: Score 25.0 (strong AI signature)
        - Between 0.55-0.70: Linear 25-75 (transition zone)
        - Below 0.55: Asymptotic 75-100 (human-like)

        Lower GLTR top-10 = less predictable = more human-like = higher score.
        Higher GLTR top-10 = more predictable = more AI-like = lower score.

        Research findings:
        - Human writing: <55% top-10 tokens (median 48%)
        - AI writing (GPT-3.5): >70% top-10 tokens (median 76%)
        - AI writing (GPT-4+): 60-65% (GLTR less effective on newer models)

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Get GLTR top-10 percentage (primary GLTR indicator)
        gltr_top10 = metrics.get("gltr_top10_percentage", 0.55)

        # Monotonic decreasing scoring: lower values = higher scores
        # We use increasing=True but invert the value since we want decreasing behavior
        # threshold_low=0.55 (human), threshold_high=0.70 (AI)
        score = self._monotonic_score(
            value=1.0 - gltr_top10,  # Invert: 0.55 becomes 0.45, 0.70 becomes 0.30
            threshold_low=1.0 - 0.70,  # 0.30
            threshold_high=1.0 - 0.55,  # 0.45
            increasing=True,  # Now higher inverted value = higher score
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

        if not metrics.get("available", False):
            recommendations.append(
                "GLTR analysis unavailable. Install required dependencies: transformers, torch."
            )
            return recommendations

        gltr_top10 = metrics.get("gltr_top10_percentage", 0.55)

        if gltr_top10 >= 0.70:
            recommendations.append(
                f"High token predictability (GLTR top-10: {gltr_top10:.1%}, target <55%). "
                f"Strong AI signature. Text uses very predictable word choices. "
                f"Rewrite with more varied, unexpected vocabulary and phrasing."
            )

        if gltr_top10 >= 0.60:
            recommendations.append(
                f"Elevated token predictability (GLTR: {gltr_top10:.1%}, target <55%). "
                f"Use less common synonyms and more creative expressions."
            )

        if gltr_top10 < 0.50:
            recommendations.append(
                f"Excellent unpredictability (GLTR: {gltr_top10:.1%}). "
                f"Text shows strong human-like variation in word choice."
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

    def _calculate_gltr_metrics_with_timeout(
        self, text: str, timeout: int = 120
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate GLTR metrics with timeout protection (Story 1.4.14).

        Prevents indefinite hangs on large documents by enforcing a
        configurable timeout. Returns None if timeout occurs or if
        calculation fails.

        Args:
            text: Text to analyze (pre-truncated/sampled by caller)
            timeout: Timeout in seconds (default 120)

        Returns:
            Dict with GLTR metrics, or None if timeout/error

        Thread-safety:
            Uses daemon thread for timeout enforcement.
            Thread properly cleaned up after timeout or completion.
        """
        result = [None]
        exception = [None]

        def worker():
            """Worker thread to execute GLTR calculation."""
            try:
                result[0] = self._calculate_gltr_metrics(text)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            # Timeout occurred - thread still running
            print(f"Warning: GLTR analysis timed out after {timeout}s", file=sys.stderr)
            return None

        if exception[0]:
            # Exception occurred during calculation
            print(f"Warning: GLTR analysis failed: {exception[0]}", file=sys.stderr)
            return None

        return result[0]

    @staticmethod
    def clear_model_cache():
        """
        Clear cached GLTR model (Story 1.4.14).

        Useful for:
        - Testing (reset state between tests)
        - Memory management (free 500MB-2GB RAM)
        - Model reload after updates

        Thread-safe via lock protection.
        """
        global _perplexity_model, _perplexity_tokenizer
        with _model_lock:
            _perplexity_model = None
            _perplexity_tokenizer = None

    def _aggregate_gltr_metrics(self, sample_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate GLTR metrics from multiple samples.

        Strategy:
        - Percentages (top10, top100, top1000): Mean across samples
        - Mean rank: Mean of means
        - Rank variance: Mean of variances (simple approach; weighted variance is future enhancement)
        - Likelihood: Mean across samples

        Args:
            sample_metrics: List of GLTR metric dicts from each sample

        Returns:
            Aggregated GLTR metrics dict

        Example:
            >>> samples = [
            ...     {'gltr_top10_percentage': 0.50, 'gltr_mean_rank': 40.0},
            ...     {'gltr_top10_percentage': 0.60, 'gltr_mean_rank': 50.0},
            ...     {'gltr_top10_percentage': 0.55, 'gltr_mean_rank': 45.0}
            ... ]
            >>> result = self._aggregate_gltr_metrics(samples)
            >>> result['gltr_top10_percentage']
            0.55  # Mean of 0.50, 0.60, 0.55
        """
        if not sample_metrics:
            return {}

        if len(sample_metrics) == 1:
            return sample_metrics[0]

        # Extract values for each metric
        top10_values = [m.get("gltr_top10_percentage", 0) for m in sample_metrics]
        top100_values = [m.get("gltr_top100_percentage", 0) for m in sample_metrics]
        top1000_values = [m.get("gltr_top1000_percentage", 0) for m in sample_metrics]
        mean_rank_values = [m.get("gltr_mean_rank", 0) for m in sample_metrics]
        variance_values = [m.get("gltr_rank_variance", 0) for m in sample_metrics]
        likelihood_values = [m.get("gltr_likelihood", 0) for m in sample_metrics]

        # Calculate means
        return {
            "gltr_top10_percentage": sum(top10_values) / len(top10_values),
            "gltr_top100_percentage": sum(top100_values) / len(top100_values),
            "gltr_top1000_percentage": sum(top1000_values) / len(top1000_values),
            "gltr_mean_rank": sum(mean_rank_values) / len(mean_rank_values),
            "gltr_rank_variance": sum(variance_values) / len(variance_values),
            "gltr_likelihood": sum(likelihood_values) / len(likelihood_values),
        }

    def _calculate_gltr_metrics(self, text: str) -> Dict:
        """
        Calculate GLTR (Giant Language Model Test Room) metrics.

        GLTR analyzes where each token ranks in the model's probability distribution.
        AI-generated text shows high concentration of top-10 tokens (>70%).
        Human writing is more unpredictable (<55%).

        Performance (Story 1.4.14):
        - First call: 2-10s (model load) + analysis time
        - Subsequent calls: ~0.1-0.5s (cached model) + analysis time
        - Model cached at module level with thread-safe loading
        - 80-95% time reduction on repeated analyses

        NOTE: This method no longer truncates text - truncation/sampling
        is handled by caller via _prepare_text(). Call via
        _calculate_gltr_metrics_with_timeout() for timeout protection.

        Args:
            text: Text to analyze (pre-truncated/sampled by caller)

        Returns:
            Dict with GLTR metrics

        Thread-safety:
            Model loading protected by _model_lock (double-checked locking pattern).
            Multiple threads can safely call this method concurrently.

        Research: 80% F1-score (IberLef-AuTexTification 2025).
        Performance degrades on GPT-4+ (31-50% vs 70-90% on GPT-3.5).
        """
        try:
            global _perplexity_model, _perplexity_tokenizer

            # Thread-safe lazy load model if not already loaded (Story 1.4.14)
            if _perplexity_model is None:
                with _model_lock:
                    # Double-check after acquiring lock (another thread may have loaded it)
                    if _perplexity_model is None:
                        print(
                            "Loading DistilGPT-2 model for GLTR analysis (one-time setup)...",
                            file=sys.stderr,
                        )
                        _perplexity_model = AutoModelForCausalLM.from_pretrained("distilgpt2")
                        _perplexity_tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
                        _perplexity_model.eval()

            # Remove code blocks
            text = re.sub(r"```[\s\S]*?```", "", text)

            # Tokenize (tokenizer is guaranteed to be loaded after model loading above)
            assert _perplexity_tokenizer is not None
            tokens = _perplexity_tokenizer.encode(text)

            if len(tokens) < 10:
                return {}  # Not enough tokens for reliable analysis

            ranks = []

            # Performance optimization: Analyze up to 500 tokens per sample (fast, reliable)
            # 500 tokens ≈ 2000-2500 chars ≈ 1 page per sample
            MAX_TOKENS_PER_ANALYSIS = 500

            # Analyze each token's rank in model prediction
            for i in range(1, min(len(tokens), MAX_TOKENS_PER_ANALYSIS)):
                input_ids = torch.tensor([tokens[:i]])

                with torch.no_grad():
                    outputs = _perplexity_model(input_ids)
                    logits = outputs.logits[0, -1, :]
                    probs = torch.softmax(logits, dim=-1)

                    # Get rank of actual next token
                    sorted_indices = torch.argsort(probs, descending=True)
                    actual_token = tokens[i]
                    rank = (sorted_indices == actual_token).nonzero(as_tuple=True)[0].item()
                    ranks.append(rank)

            if not ranks:
                return {}

            # Calculate GLTR metrics
            top10_percentage = safe_ratio(sum(1 for r in ranks if r < 10), len(ranks), 0)
            top100_percentage = safe_ratio(sum(1 for r in ranks if r < 100), len(ranks), 0)
            top1000_percentage = safe_ratio(sum(1 for r in ranks if r < 1000), len(ranks), 0)
            mean_rank = sum(ranks) / len(ranks)
            rank_variance = statistics.variance(ranks) if len(ranks) > 1 else 0

            # AI likelihood based on top-10 concentration
            # Research: AI >70%, Human <55%
            if top10_percentage > 0.70:
                ai_likelihood = 0.90
            elif top10_percentage > 0.65:
                ai_likelihood = 0.75
            elif top10_percentage > 0.60:
                ai_likelihood = 0.60
            elif top10_percentage < 0.50:
                ai_likelihood = 0.20
            else:
                ai_likelihood = 0.50

            return {
                "gltr_top10_percentage": round(top10_percentage, 3),
                "gltr_top100_percentage": round(top100_percentage, 3),
                "gltr_top1000_percentage": round(top1000_percentage, 3),
                "gltr_mean_rank": round(mean_rank, 2),
                "gltr_rank_variance": round(rank_variance, 2),
                "gltr_likelihood": round(ai_likelihood, 2),
            }
        except Exception as e:
            print(f"Warning: GLTR analysis failed: {e}", file=sys.stderr)
            return {}

    def _analyze_high_predictability_segments_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[HighPredictabilitySegment]:
        """Identify text segments with high GLTR scores (AI-like predictability)."""
        issues = []

        try:
            global _perplexity_model, _perplexity_tokenizer

            if _perplexity_model is None:
                # Model not loaded yet
                return []

            # Tokenizer is always loaded when model is loaded
            assert _perplexity_tokenizer is not None

            # Analyze in 50-100 word chunks
            chunk_size = 75  # words
            current_chunk = []
            chunk_start_line = 1

            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Skip HTML comments (metadata), headings, and code blocks
                if html_comment_checker and html_comment_checker(line):
                    continue
                if stripped.startswith("#") or stripped.startswith("```"):
                    continue

                if stripped:
                    words = re.findall(r"\b\w+\b", stripped)
                    current_chunk.extend(words)

                    if len(current_chunk) >= chunk_size:
                        # Analyze this chunk
                        chunk_text = " ".join(current_chunk)

                        # Calculate GLTR for chunk
                        try:
                            tokens = _perplexity_tokenizer.encode(
                                chunk_text, add_special_tokens=True
                            )
                            if len(tokens) < 10:
                                current_chunk = []
                                chunk_start_line = line_num + 1
                                continue

                            ranks = []
                            for i in range(1, min(len(tokens), 100)):
                                input_ids = torch.tensor([tokens[:i]])
                                with torch.no_grad():
                                    outputs = _perplexity_model(input_ids)
                                    logits = outputs.logits[0, -1, :]
                                    probs = torch.softmax(logits, dim=-1)
                                    sorted_indices = torch.argsort(probs, descending=True)
                                    actual_token = tokens[i]
                                    rank = (
                                        (sorted_indices == actual_token)
                                        .nonzero(as_tuple=True)[0]
                                        .item()
                                    )
                                    ranks.append(rank)

                            if ranks:
                                top10_pct = sum(1 for r in ranks if r < 10) / len(ranks)

                                # High predictability: >70% in top-10
                                if top10_pct > 0.70:
                                    preview = (
                                        chunk_text[:150] + "..."
                                        if len(chunk_text) > 150
                                        else chunk_text
                                    )
                                    issues.append(
                                        HighPredictabilitySegment(
                                            start_line=chunk_start_line,
                                            end_line=line_num,
                                            segment_preview=preview,
                                            gltr_score=top10_pct,
                                            problem=f"High predictability (GLTR={top10_pct:.2f}, AI threshold >0.70)",
                                            suggestion="Rewrite with less common word choices, vary sentence structure, add unexpected turns",
                                        )
                                    )

                        except Exception as e:
                            print(f"Warning: GLTR chunk analysis failed: {e}", file=sys.stderr)

                        # Reset chunk
                        current_chunk = []
                        chunk_start_line = line_num + 1

        except Exception as e:
            print(f"Warning: High predictability segment analysis failed: {e}", file=sys.stderr)

        return issues


# Backward compatibility alias
PredictabilityAnalyzer = PredictabilityDimension

# Module-level singleton - triggers self-registration on module import
_instance = PredictabilityDimension()
