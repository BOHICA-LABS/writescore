"""
Burstiness dimension analyzer.

Analyzes sentence and paragraph length variation - a core metric from GPTZero methodology.
Low variation (low burstiness) is a strong AI signal, while high variation is human-like.

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
import statistics
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import SentenceBurstinessIssue
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.scoring.dual_score import THRESHOLDS
from writescore.utils.text_processing import safe_ratio


class BurstinessDimension(DimensionStrategy):
    """
    Analyzes burstiness dimension - sentence and paragraph variation.

    Weight: 6.0% of total score
    Tier: CORE

    Detects:
    - Low sentence length variation (AI signature)
    - Uniform paragraph lengths (AI signature)
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
        return "burstiness"

    @property
    def weight(self) -> float:
        """Return dimension weight (8.0% of total score)."""
        return 8.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.CORE

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes sentence and paragraph length variation (GPTZero burstiness metric)"

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
        Analyze text for sentence and paragraph variation.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with burstiness analysis results
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
                sentence_burst = self._analyze_sentence_burstiness(sample_text)
                paragraph_var = self._analyze_paragraph_variation(sample_text)
                paragraph_cv = self._calculate_paragraph_cv(sample_text)
                sample_results.append(
                    {
                        "sentence_burstiness": sentence_burst,
                        "paragraph_variation": paragraph_var,
                        "paragraph_cv": paragraph_cv,
                    }
                )

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            sentence_burst = self._analyze_sentence_burstiness(analyzed_text)
            paragraph_var = self._analyze_paragraph_variation(analyzed_text)
            paragraph_cv = self._calculate_paragraph_cv(analyzed_text)
            aggregated = {
                "sentence_burstiness": sentence_burst,
                "paragraph_variation": paragraph_var,
                "paragraph_cv": paragraph_cv,
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

    def analyze_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[SentenceBurstinessIssue]:
        """
        Detailed analysis of burstiness issues with line numbers.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of SentenceBurstinessIssue objects
        """
        return self._analyze_burstiness_issues_detailed(lines, html_comment_checker)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on burstiness metrics using Gaussian scoring.

        Migrated to Gaussian scoring in Story 2.4.1 based on research findings.
        Uses sentence length standard deviation with research-based parameters.

        Research parameters (Story 2.4.0 literature review):
        - Target (μ): 15.0 words (optimal sentence length variation)
        - Width (σ): 5.0 (wide tolerance for domain variation)
        - Confidence: Medium (varies by domain)
        - Rationale: Symmetric optimum (too low = robotic, too high = chaotic)

        Algorithm:
        - Uses Gaussian distribution: score = exp(-0.5 × ((value - μ) / σ)²)
        - Higher stdev (more variation) scores higher up to optimal (15.0)
        - Lower stdev (uniform) or extremely high stdev both score lower

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        sentence_burst = metrics.get("sentence_burstiness", {})
        total_sentences = sentence_burst.get("total_sentences", 0)

        if total_sentences == 0:
            # Insufficient data - return neutral score
            return 50.0

        stdev = sentence_burst.get("stdev", 0)

        # Gaussian scoring with research-based parameters
        # Target μ=15.0, Width σ=5.0 (Story 2.4.1, AC3)
        # _gaussian_score() returns 0-100 scale directly
        score = self._gaussian_score(value=stdev, target=15.0, width=5.0)

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
        recommendations: List[str] = []

        sentence_burst = metrics.get("sentence_burstiness", {})
        stdev = sentence_burst.get("stdev", 0)
        short_count = sentence_burst.get("short", 0)
        long_count = sentence_burst.get("long", 0)
        total_sentences = sentence_burst.get("total_sentences", 0)

        if total_sentences == 0:
            return recommendations

        short_pct = safe_ratio(short_count, total_sentences) * 100
        long_pct = safe_ratio(long_count, total_sentences) * 100

        # Recommendation for low variation
        if stdev < 5:
            recommendations.append(
                f"Increase sentence length variation (current σ={stdev:.1f}, target σ≥8). "
                f"Mix short (5-10 words), medium (15-25 words), and long (30-45 words) sentences."
            )

        # Recommendation for insufficient short sentences
        if short_pct < THRESHOLDS.SHORT_SENTENCE_MIN_RATIO * 100:
            recommendations.append(
                f"Add more short sentences (currently {short_pct:.0f}%, target ≥{THRESHOLDS.SHORT_SENTENCE_MIN_RATIO * 100:.0f}%). "
                f"Short punchy sentences increase burstiness."
            )

        # Recommendation for insufficient long sentences
        if long_pct < THRESHOLDS.LONG_SENTENCE_MIN_RATIO * 100:
            recommendations.append(
                f"Add more complex long sentences (currently {long_pct:.0f}%, target ≥{THRESHOLDS.LONG_SENTENCE_MIN_RATIO * 100:.0f}%). "
                f"Long sentences with clauses increase variation."
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
    # LEGACY COMPATIBILITY
    # ========================================================================

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate burstiness score.

        Args:
            analysis_results: Results dict with sentence burstiness metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        total_sentences = analysis_results.get("total_sentences", 0)
        if total_sentences == 0:
            return (0.0, "UNKNOWN")

        stdev = analysis_results.get("stdev", 0)
        short_count = analysis_results.get("short", 0)
        long_count = analysis_results.get("long", 0)

        short_pct = safe_ratio(short_count, total_sentences)
        long_pct = safe_ratio(long_count, total_sentences)

        # High burstiness: high stdev, good mix of short/long
        if (
            stdev >= 8
            and short_pct >= THRESHOLDS.SHORT_SENTENCE_MIN_RATIO
            and long_pct >= THRESHOLDS.LONG_SENTENCE_MIN_RATIO
        ):
            return (10.0, "HIGH")
        elif stdev >= 5:
            return (7.0, "MEDIUM")
        elif stdev >= THRESHOLDS.SENTENCE_STDEV_LOW:
            return (4.0, "LOW")
        else:
            return (2.0, "VERY LOW")

    def _analyze_sentence_burstiness(self, text: str) -> Dict:
        """Analyze sentence length variation."""
        # Remove headings and list markers for sentence analysis
        lines = []
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            # Remove list markers
            line = re.sub(r"^\s*[-*+0-9]+[.)]\s*", "", line)
            lines.append(line)

        clean_text = "\n".join(lines)

        # Split into paragraphs
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if p.strip()]

        # Split paragraphs into sentences
        sent_pattern = re.compile(r"(?<=[.!?])\s+")
        all_lengths = []

        for para in paragraphs:
            # Skip code blocks
            if "```" in para:
                continue
            sentences = [s.strip() for s in sent_pattern.split(para) if s.strip()]
            for sent in sentences:
                word_count = len(re.findall(r"[\w'-]+", sent))
                if word_count > 0:  # Only count non-empty sentences
                    all_lengths.append(word_count)

        if not all_lengths:
            return {
                "total_sentences": 0,
                "mean": 0,
                "stdev": 0,
                "min": 0,
                "max": 0,
                "short": 0,
                "medium": 0,
                "long": 0,
                "lengths": [],
            }

        short = sum(1 for x in all_lengths if x <= 10)
        medium = sum(1 for x in all_lengths if 11 <= x <= 25)
        long = sum(1 for x in all_lengths if x >= 30)

        return {
            "total_sentences": len(all_lengths),
            "mean": round(statistics.mean(all_lengths), 1),
            "stdev": round(statistics.stdev(all_lengths), 1) if len(all_lengths) > 1 else 0,
            "min": min(all_lengths),
            "max": max(all_lengths),
            "short": short,
            "medium": medium,
            "long": long,
            "lengths": all_lengths,
        }

    def _analyze_paragraph_variation(self, text: str) -> Dict[str, Any]:
        """Analyze paragraph length variation."""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        # Filter out headings and code blocks
        para_words = []
        for para in paragraphs:
            if para.startswith("#") or "```" in para:
                continue
            words = re.findall(r"\b[\w'-]+\b", para)
            if words:
                para_words.append(len(words))

        if not para_words:
            return {"total_paragraphs": 0, "mean": 0, "stdev": 0, "min": 0, "max": 0}

        return {
            "total_paragraphs": len(para_words),
            "mean": round(statistics.mean(para_words), 1),
            "stdev": round(statistics.stdev(para_words), 1) if len(para_words) > 1 else 0,
            "min": min(para_words),
            "max": max(para_words),
        }

    def _calculate_paragraph_cv(self, text: str) -> Dict[str, Any]:
        """
        Calculate coefficient of variation for paragraph lengths.

        Phase 1 High-ROI pattern: Detects unnaturally uniform paragraph lengths,
        a strong AI signature. Human writing typically shows CV ≥0.4, while
        AI-generated content often has CV <0.3.

        Returns:
            Dict with mean_length, stddev, cv, score, assessment, paragraph_count
        """
        # Split by double newlines to get paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Filter out headings, code blocks, and very short lines
        filtered_paragraphs = []
        for p in paragraphs:
            # Skip headings (start with #)
            if p.startswith("#"):
                continue
            # Skip code blocks
            if "```" in p:
                continue
            # Skip very short lines (likely not real paragraphs)
            if len(p.split()) < 10:
                continue
            filtered_paragraphs.append(p)

        # Count words per paragraph
        lengths = [len(p.split()) for p in filtered_paragraphs]

        if len(lengths) < 3:
            return {
                "mean_length": 0.0,
                "stddev": 0.0,
                "cv": 0.0,
                "score": 10.0,  # Benefit of doubt for insufficient data
                "assessment": "INSUFFICIENT_DATA",
                "paragraph_count": len(lengths),
            }

        mean_length = statistics.mean(lengths)
        stddev = statistics.stdev(lengths)
        cv = stddev / mean_length if mean_length > 0 else 0.0

        # Scoring based on research thresholds
        if cv >= 0.6:
            score, assessment = 10.0, "EXCELLENT"
        elif cv >= 0.4:
            score, assessment = 7.0, "GOOD"
        elif cv >= 0.3:
            score, assessment = 4.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "mean_length": round(mean_length, 1),
            "stddev": round(stddev, 1),
            "cv": round(cv, 2),
            "score": score,
            "assessment": assessment,
            "paragraph_count": len(lengths),
        }

    def _analyze_burstiness_issues_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[SentenceBurstinessIssue]:
        """Detect sections with uniform sentence lengths (low burstiness)."""
        issues = []

        # Split into paragraphs
        current_para = []

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip HTML comments, headings, and code blocks
            if html_comment_checker and html_comment_checker(line):
                continue
            if stripped.startswith("#") or stripped.startswith("```"):
                continue

            if stripped:
                current_para.append((line_num, line))
            else:
                # End of paragraph - analyze it
                if len(current_para) >= 3:
                    para_text = " ".join([item[1] for item in current_para])
                    sent_pattern = re.compile(r"(?<=[.!?])\s+")
                    sentences = [s.strip() for s in sent_pattern.split(para_text) if s.strip()]

                    if len(sentences) >= 3:
                        lengths = [len(re.findall(r"[\w'-]+", s)) for s in sentences]
                        if len(lengths) > 1:
                            mean = statistics.mean(lengths)
                            stdev = statistics.stdev(lengths)

                            # Low burstiness: stdev < 5 words (AI signature)
                            if stdev < 5:
                                # Get preview of sentences with their lengths
                                preview = []
                                for i, sent in enumerate(sentences[:3]):
                                    preview.append(
                                        (
                                            current_para[0][0] + i,  # Line number
                                            sent[:60] + "..." if len(sent) > 60 else sent,
                                            lengths[i],
                                        )
                                    )

                                issues.append(
                                    SentenceBurstinessIssue(
                                        start_line=current_para[0][0],
                                        end_line=current_para[-1][0],
                                        sentence_count=len(sentences),
                                        mean_length=round(mean, 1),
                                        stdev=round(stdev, 1),
                                        problem=f"Uniform sentence lengths ({int(min(lengths))}-{int(max(lengths))} words, σ={stdev:.1f})",
                                        sentences_preview=preview,
                                        suggestion="Add variety: combine short sentences (5-10 words), keep medium (15-25), add complex (30-45 words)",
                                    )
                                )

                current_para = []
                line_num + 1

        return issues


# Backward compatibility alias
BurstinessAnalyzer = BurstinessDimension

# Module-level singleton - triggers self-registration on module import
_instance = BurstinessDimension()
