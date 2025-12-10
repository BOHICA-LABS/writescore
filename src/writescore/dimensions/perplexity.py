"""
Perplexity dimension analyzer.

Measures language model uncertainty using mathematical perplexity calculation.

**Mathematical Definition**:
Perplexity = exp(-(1/N) × Σ log P(w_i | context))

**Interpretation**:
- Lower perplexity (15-25): Very predictable text (AI-like)
- Medium perplexity (25-45): Transitional range
- Higher perplexity (35-50+): Unpredictable text (human-like)

**Research Findings**:
- Human median: 35.9
- AI median: 21.2 (40% lower)
- Strong discrimination signal

**Performance**: Requires GPT-2 language model (~2-3 seconds per 1k words)

Weight: 3.0% of total score (validated with 29.5% discrimination)
Tier: ADVANCED (requires language model)

Implemented in Story 2.4.0.7.
Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import math
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

# Required imports
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.utils import logging as transformers_logging

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

transformers_logging.set_verbosity_error()


# Global model instances (lazy loading with thread-safety)
_perplexity_model = None
_perplexity_tokenizer = None
_perplexity_device = None  # Device for model inference (MPS, CUDA, or CPU)
_model_lock = threading.Lock()  # Thread-safe model loading


class PerplexityDimension(DimensionStrategy):
    """
    Perplexity dimension - measures language model uncertainty.

    Weight: 3.0% of total score (validated with 29.5% discrimination)
    Tier: ADVANCED

    Uses GPT-2 model to calculate mathematical perplexity:
    - Perplexity = exp(-(1/N) × Σ log P(w_i | context))
    - Lower perplexity indicates predictable text (AI-like)
    - Higher perplexity indicates unpredictable text (human-like)

    Research findings (medical abstracts study):
    - Human median: 35.9
    - AI median: 21.2 (40% lower than human)
    - Strong AI detection signal

    Monotonic scoring:
    - Threshold low: 25.0 (AI-like)
    - Threshold high: 45.0 (human-like)
    - Higher perplexity = higher score (more human-like)
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
        return "perplexity"

    @property
    def weight(self) -> float:
        """Return dimension weight (3.0% of total score)."""
        return 3.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Mathematical perplexity calculation using language model (29.5% discrimination, 24.6 point score difference)"

    # ========================================================================
    # MODEL LOADING AND CACHING
    # ========================================================================

    @classmethod
    def _get_device(cls):
        """
        Get optimal device for model inference.

        Priority order:
        1. MPS (Apple Silicon Metal Performance Shaders) - 5-10× faster on M1/M2
        2. CUDA (NVIDIA GPU)
        3. CPU (fallback)

        Returns:
            torch.device: Optimal device for inference
        """
        global _perplexity_device
        if _perplexity_device is None:
            # Check for Apple Silicon MPS
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                _perplexity_device = torch.device("mps")
            # Check for NVIDIA CUDA
            elif torch.cuda.is_available():
                _perplexity_device = torch.device("cuda")
            # Fallback to CPU
            else:
                _perplexity_device = torch.device("cpu")
        return _perplexity_device

    @classmethod
    def _get_model(cls):
        """
        Load and cache GPT-2 model for perplexity calculation.

        Thread-safe lazy loading with module-level caching.
        First call loads model (~2-5 seconds), subsequent calls instant.

        Performance optimization:
        - Automatically uses MPS (Apple Silicon) if available for 5-10× speedup
        - Falls back to CUDA (NVIDIA) or CPU

        Returns:
            Cached GPT-2 model instance on optimal device
        """
        global _perplexity_model
        if _perplexity_model is None:
            with _model_lock:
                # Double-check after acquiring lock
                if _perplexity_model is None:
                    device = cls._get_device()
                    print(
                        "Loading GPT-2 model for perplexity calculation (one-time setup)...",
                        file=sys.stderr,
                    )
                    print(f"Using device: {device}", file=sys.stderr)

                    _perplexity_model = AutoModelForCausalLM.from_pretrained("gpt2")
                    _perplexity_model.eval()

                    # Move model to optimal device (MPS on M1, CUDA on NVIDIA, CPU otherwise)
                    _perplexity_model.to(device)
                    print(f"Model loaded and moved to {device}", file=sys.stderr)
        return _perplexity_model

    @classmethod
    def _get_tokenizer(cls):
        """
        Load and cache GPT-2 tokenizer.

        Thread-safe lazy loading with module-level caching.

        Returns:
            Cached GPT-2 tokenizer instance
        """
        global _perplexity_tokenizer
        if _perplexity_tokenizer is None:
            with _model_lock:
                # Double-check after acquiring lock
                if _perplexity_tokenizer is None:
                    _perplexity_tokenizer = AutoTokenizer.from_pretrained("gpt2")
        return _perplexity_tokenizer

    @classmethod
    def clear_model_cache(cls):
        """
        Clear cached perplexity model.

        Useful for:
        - Testing (reset state between tests)
        - Memory management (free ~500MB RAM)
        - Model reload after updates

        Thread-safe via lock protection.
        """
        global _perplexity_model, _perplexity_tokenizer, _perplexity_device
        with _model_lock:
            _perplexity_model = None
            _perplexity_tokenizer = None
            _perplexity_device = None

    # ========================================================================
    # PERPLEXITY CALCULATION
    # ========================================================================

    def _tokenize(self, text: str) -> torch.Tensor:
        """
        Tokenize text with input validation.

        Args:
            text: Input text to tokenize

        Returns:
            Token tensor

        Raises:
            ValueError: If text is invalid (empty, too long, etc.)
        """
        # Input validation for security
        if not text or len(text) == 0:
            raise ValueError("Text must be non-empty")

        if len(text) > 1_000_000:  # 1MB text limit
            raise ValueError("Text must be under 1MB")

        # Sanitize: Remove null bytes and control characters that could cause issues
        text = "".join(char for char in text if char.isprintable() or char.isspace())

        if not text.strip():
            raise ValueError("Text must contain printable characters")

        tokenizer = self._get_tokenizer()
        tokens: torch.Tensor = tokenizer.encode(text, return_tensors="pt")

        # Validate token length (prevent memory exhaustion)
        if tokens.shape[1] > 50_000:  # ~200k chars, reasonable max
            raise ValueError("Text produces too many tokens (>50k)")

        if tokens.shape[1] < 2:  # Need at least 2 tokens for perplexity
            raise ValueError("Text must produce at least 2 tokens")

        return tokens

    def _get_token_log_prob(self, context: torch.Tensor, target: torch.Tensor) -> float:
        """
        Get log probability of target token given context.

        Args:
            context: Context tokens [1, context_length]
            target: Target token [1, 1]

        Returns:
            Log probability of target token
        """
        model = self._get_model()
        device = self._get_device()

        # Move tensors to device
        context = context.to(device)
        target = target.to(device)

        with torch.no_grad():
            outputs = model(context)
            logits = outputs.logits[0, -1, :]  # Last token's predictions
            log_probs = torch.log_softmax(logits, dim=-1)

            target_id = target[0, 0].item()
            log_prob = log_probs[target_id].item()

        return float(log_prob)

    def _calculate_perplexity(self, text: str) -> Tuple[float, float, int]:
        """
        Calculate mathematical perplexity using GPT-2 model (optimized).

        Formula: Perplexity = exp(-(1/N) × Σ log P(w_i | context))

        Performance optimizations:
        - Uses PyTorch's built-in cross-entropy loss (much faster than token-by-token)
        - Limits to first 1024 tokens for very long documents
        - Single forward pass through model
        - MPS acceleration on Apple Silicon (5-10× speedup on M1/M2)

        Args:
            text: Input text

        Returns:
            Tuple of (perplexity, avg_log_prob, token_count)

        Raises:
            ValueError: If text is invalid
        """
        tokens = self._tokenize(text)
        token_count = tokens.shape[1]

        # Limit context window for performance (1024 tokens ≈ 4000 chars)
        MAX_TOKENS = 1024
        if token_count > MAX_TOKENS:
            tokens = tokens[:, :MAX_TOKENS]
            token_count = MAX_TOKENS

        model = self._get_model()
        device = self._get_device()

        # Move tokens to same device as model (MPS, CUDA, or CPU)
        tokens = tokens.to(device)

        # Efficient computation using PyTorch's built-in cross-entropy loss
        # This is much faster than token-by-token calculation (single forward pass)
        with torch.no_grad():
            # Model expects input_ids and labels
            # We shift labels by 1 to predict next token
            outputs = model(tokens, labels=tokens)

            # loss is average negative log-likelihood
            loss = outputs.loss.item()

        # Average log probability is negative of loss
        avg_log_prob = -loss

        # Perplexity = exp(-avg_log_prob) = exp(loss)
        perplexity = math.exp(loss)

        return perplexity, avg_log_prob, token_count

    # ========================================================================
    # SCORING METHODS
    # ========================================================================

    def _score_perplexity(self, perplexity_value: float) -> float:
        """
        Apply monotonic increasing scoring function.

        Scoring:
        - Below 25.0: Score 0-20 (very AI-like)
        - Between 25.0-45.0: Score 20-80 (linear interpolation)
        - Above 45.0: Score 80-100 (very human-like)

        Args:
            perplexity_value: Calculated perplexity

        Returns:
            Score from 0.0 to 100.0
        """
        threshold_low = 25.0  # AI-like
        threshold_high = 45.0  # Human-like

        if perplexity_value <= threshold_low:
            # Below threshold: 0-20 points (proportional)
            return 0.0 + (perplexity_value / threshold_low) * 20.0
        elif perplexity_value >= threshold_high:
            # Above threshold: 80-100 points (capped at 100)
            excess = (perplexity_value - threshold_high) / 20.0
            return 80.0 + min(excess, 1.0) * 20.0
        else:
            # Linear interpolation between 20 and 80
            range_size = threshold_high - threshold_low
            position = (perplexity_value - threshold_low) / range_size
            return 20.0 + position * 60.0

    def _interpret_perplexity(self, perplexity: float) -> str:
        """
        Interpret perplexity value.

        Args:
            perplexity: Perplexity value

        Returns:
            Human-readable interpretation
        """
        if perplexity < 25.0:
            return "Very low perplexity - highly predictable text (AI-like)"
        elif perplexity < 35.0:
            return "Low to moderate perplexity - somewhat predictable"
        elif perplexity < 45.0:
            return "Moderate to high perplexity - good variation"
        else:
            return "High perplexity - unpredictable text (human-like)"

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
        Analyze text perplexity with configurable modes.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = default)
            **kwargs: Additional parameters

        Returns:
            Dict with perplexity metrics:
            - score: 0-100 score (monotonic scoring)
            - raw_value: perplexity value (e.g., 35.9)
            - perplexity: same as raw_value
            - token_count: number of tokens analyzed
            - avg_log_prob: average log probability
            - threshold_low: 25.0
            - threshold_high: 45.0
            - interpretation: human-readable interpretation
            - available: whether analysis succeeded
        """
        config = config or DEFAULT_CONFIG

        # Handle empty text
        if not text or not text.strip():
            return {
                "score": 50.0,  # Neutral
                "raw_value": 0.0,
                "perplexity": 0.0,
                "token_count": 0,
                "avg_log_prob": 0.0,
                "threshold_low": 25.0,
                "threshold_high": 45.0,
                "interpretation": "No text to analyze",
                "available": False,
                "analysis_mode": config.mode.value,
            }

        try:
            # Calculate perplexity
            perplexity, avg_log_prob, token_count = self._calculate_perplexity(text)

            # Apply monotonic scoring
            score = self._score_perplexity(perplexity)

            return {
                "score": score,
                "raw_value": perplexity,
                "perplexity": perplexity,
                "token_count": token_count,
                "avg_log_prob": avg_log_prob,
                "threshold_low": 25.0,
                "threshold_high": 45.0,
                "interpretation": self._interpret_perplexity(perplexity),
                "available": True,
                "analysis_mode": config.mode.value,
            }

        except Exception as e:
            print(f"Warning: Perplexity calculation failed: {e}", file=sys.stderr)
            return {
                "score": 50.0,  # Neutral
                "raw_value": 0.0,
                "perplexity": 0.0,
                "token_count": 0,
                "avg_log_prob": 0.0,
                "threshold_low": 25.0,
                "threshold_high": 45.0,
                "interpretation": f"Error: {str(e)}",
                "available": False,
                "error": str(e),
                "analysis_mode": config.mode.value,
            }

    def analyze_detailed(self, lines: List[str], html_comment_checker=None) -> Dict[str, Any]:
        """
        Detailed analysis (not applicable for perplexity).

        Perplexity is a document-level metric, not line-by-line.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            Empty dict (perplexity not applicable to line-level analysis)
        """
        return {"note": "Perplexity is a document-level metric"}

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on perplexity using monotonic scoring.

        Migrated to use shared `_monotonic_score()` helper in Story 2.4.1 for consistency.
        Previously used custom `_score_perplexity()` method with identical logic.

        Research parameters (Story 2.4.0 literature review):
        - Metric: Mathematical perplexity from GPT-2 language model
        - Threshold low: 25.0 (AI-like, very predictable)
        - Threshold high: 45.0 (human-like, unpredictable)
        - Direction: Increasing (higher perplexity = higher score)
        - Confidence: High (validated with 29.5% discrimination, 24.6 point score difference)
        - Rationale: Monotonic relationship - higher unpredictability always better

        Research findings:
        - Human median: 35.9
        - AI median: 21.2 (40% lower than human)
        - Strong discrimination signal

        Algorithm:
        - Uses monotonic scoring: score = linear interpolation between thresholds
        - Perplexity below 25.0: Score 0-20 (AI-like)
        - Perplexity between 25.0-45.0: Score 20-80 (linear transition)
        - Perplexity above 45.0: Score 80-100 (human-like)

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Extract raw perplexity value
        perplexity = metrics.get("perplexity", 0.0)

        # Monotonic scoring with research-based parameters
        # Threshold low=25.0, high=45.0, direction=increasing
        # _monotonic_score() returns 0-100 scale directly
        score = self._monotonic_score(
            value=perplexity, threshold_low=25.0, threshold_high=45.0, increasing=True
        )

        self._validate_score(score)
        return score

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on perplexity.

        Args:
            score: Current score from calculate_score()
            metrics: Raw metrics from analyze()

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not metrics.get("available", False):
            recommendations.append(
                "Perplexity analysis unavailable. Install required dependencies: transformers, torch."
            )
            return recommendations

        perplexity = metrics.get("perplexity", 0.0)

        if perplexity < 25.0:
            recommendations.append(
                f"Very low perplexity ({perplexity:.1f}, threshold 25.0) indicates highly predictable text. "
                f"This is a strong AI signature. Consider: "
                f"(1) Varying sentence structures, "
                f"(2) Using less common word choices, "
                f"(3) Introducing more stylistic variation, "
                f"(4) Adding personal voice elements."
            )
        elif perplexity < 35.0:
            recommendations.append(
                f"Low to moderate perplexity ({perplexity:.1f}, human median 35.9) suggests somewhat predictable text. "
                f"Consider increasing naturalness with more varied vocabulary and sentence structures."
            )
        elif perplexity > 45.0:
            recommendations.append(
                f"High perplexity ({perplexity:.1f}, threshold 45.0) indicates unpredictable, human-like text. "
                f"Good level of natural variation and unpredictability."
            )
        else:
            recommendations.append(
                f"Moderate perplexity ({perplexity:.1f}) in human-like range (25.0-45.0). "
                f"Text shows good balance of predictability and variation."
            )

        return recommendations

    def format_display(self, metrics: Dict[str, Any]) -> str:
        """Format perplexity display for reports."""
        if not metrics.get("available", False):
            return "(unavailable)"

        perplexity = metrics.get("perplexity", 0.0)
        interpretation = metrics.get("interpretation", "")

        return f"Perplexity: {perplexity:.1f} ({interpretation})"

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
    # LEGACY COMPATIBILITY
    # ========================================================================

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate perplexity score (legacy method).

        Args:
            analysis_results: Results dict

        Returns:
            Tuple of (score_value, score_label)
        """
        perplexity = analysis_results.get("perplexity", 0.0)
        score = self._score_perplexity(perplexity)

        # Convert to 10-point scale for legacy compatibility
        legacy_score = score / 10.0

        if score >= 80.0:
            label = "EXCELLENT"
        elif score >= 60.0:
            label = "GOOD"
        elif score >= 40.0:
            label = "ACCEPTABLE"
        else:
            label = "POOR"

        return (legacy_score, label)


# Backward compatibility alias
PerplexityAnalyzer = PerplexityDimension

# Module-level singleton - triggers self-registration on module import
_instance = PerplexityDimension()
