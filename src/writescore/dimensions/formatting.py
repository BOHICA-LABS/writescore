"""
Formatting dimension analyzer.

Analyzes formatting patterns including:
- Em-dash usage (frequency and clustering) - STRONGEST AI signal (95% accuracy)
- Bold and italic overuse (ChatGPT uses 10x more than humans)
- Quotation patterns
- Formatting consistency (mechanical distribution)

Research: Em-dash overuse is the single strongest AI detection signal.
ChatGPT uses 10x more em-dashes and bold formatting than human writers.

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
import statistics
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import EmDashInstance, FormattingIssue
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.scoring.dual_score import THRESHOLDS
from writescore.utils.text_processing import count_words


class FormattingDimension(DimensionStrategy):
    """
    Analyzes formatting dimension - em-dash, bold/italic, quotations.

    Weight: 4.0% of total score
    Tier: CORE

    Detects:
    - Em-dash overuse (95% AI detection accuracy)
    - Bold/italic overuse (ChatGPT uses 10x more)
    - Mechanical formatting distribution
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
        return "formatting"

    @property
    def weight(self) -> float:
        """Return dimension weight (10.0% of total score)."""
        return 10.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.CORE

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes em-dash overuse, bold/italic patterns, and formatting consistency"

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
        Analyze text for formatting patterns.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with formatting analysis results
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
                formatting = self._analyze_formatting(sample_text)
                bold_italic = self._analyze_bold_italic_patterns(sample_text)
                list_usage = self._analyze_list_usage(sample_text)
                punctuation = self._analyze_punctuation_clustering(sample_text)
                whitespace = self._analyze_whitespace_patterns(sample_text)
                punctuation_spacing_cv = self._analyze_punctuation_spacing_cv(sample_text)
                sample_results.append(
                    {
                        "formatting": formatting,
                        "bold_italic": bold_italic,
                        "list_usage": list_usage,
                        "punctuation_clustering": punctuation,
                        "whitespace_patterns": whitespace,
                        "punctuation_spacing_cv": punctuation_spacing_cv,
                    }
                )

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            formatting = self._analyze_formatting(analyzed_text)
            bold_italic = self._analyze_bold_italic_patterns(analyzed_text)
            list_usage = self._analyze_list_usage(analyzed_text)
            punctuation = self._analyze_punctuation_clustering(analyzed_text)
            whitespace = self._analyze_whitespace_patterns(analyzed_text)
            punctuation_spacing_cv = self._analyze_punctuation_spacing_cv(analyzed_text)
            aggregated = {
                "formatting": formatting,
                "bold_italic": bold_italic,
                "list_usage": list_usage,
                "punctuation_clustering": punctuation,
                "whitespace_patterns": whitespace,
                "punctuation_spacing_cv": punctuation_spacing_cv,
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
        Detailed analysis with line numbers and suggestions.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            Dict with detailed analysis including instances
        """
        em_dash_instances = self._analyze_em_dashes_detailed(lines, html_comment_checker)
        formatting_issues = self._analyze_formatting_issues_detailed(lines, html_comment_checker)

        return {
            "em_dash_instances": em_dash_instances,
            "formatting_issues": formatting_issues,
        }

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate formatting score.

        Combines em-dash usage and bold/italic density scoring.
        Em-dash overuse is the STRONGEST single AI detection signal (95% accuracy).

        Args:
            analysis_results: Results dict with formatting metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        issues = 0

        # Primary signal: em-dashes per page
        em_per_page = analysis_results.get("em_dashes_per_page", 0)
        if em_per_page > 10:
            issues += 3  # Very strong AI signal
        elif em_per_page > 5:
            issues += 2
        elif em_per_page > THRESHOLDS.EM_DASH_MAX_PER_PAGE:
            issues += 1

        # Bold density (ChatGPT uses 10x more bold)
        bold_per_1k = analysis_results.get("bold_per_1k", 0)
        if bold_per_1k > THRESHOLDS.BOLD_EXTREME_AI_PER_1K:
            issues += 3  # Extreme AI marker
        elif bold_per_1k > THRESHOLDS.BOLD_AI_MIN_PER_1K:
            issues += 2
        elif bold_per_1k > THRESHOLDS.BOLD_HUMAN_MAX_PER_1K:
            issues += 1

        # Formatting consistency (mechanical distribution)
        consistency = analysis_results.get("formatting_consistency", 0)
        if consistency > THRESHOLDS.FORMATTING_CONSISTENCY_AI_THRESHOLD:
            issues += 2
        elif consistency > THRESHOLDS.FORMATTING_CONSISTENCY_MEDIUM:
            issues += 1

        # Score based on total issues
        if issues == 0:
            return (10.0, "HIGH")
        elif issues <= 2:
            return (7.0, "MEDIUM")
        elif issues <= 4:
            return (4.0, "LOW")
        else:
            return (2.0, "VERY LOW")

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on formatting metrics.

        Scoring logic extracted from dual_score_calculator.py.
        Lower formatting issues = higher score (human-like).
        High em-dash usage and bold density = low score (AI-like).

        Algorithm:
        - Em-dash per page: >10 = VERY LOW, 5-10 = LOW, 3-5 = MEDIUM, <3 = HIGH
        - Bold per 1k: >50 = VERY LOW, 20-50 = LOW, 10-20 = MEDIUM, <10 = HIGH
        - Formatting consistency: >0.7 = AI-like, <0.5 = human-like

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        issues = 0

        # Get nested formatting metrics
        formatting = metrics.get("formatting", {})
        bold_italic = metrics.get("bold_italic", {})

        # Calculate em-dashes per page (assuming ~300 words per page)
        em_dashes = formatting.get("em_dashes", 0)
        word_count = count_words("")  # Will be calculated from text if available
        # For scoring, we use the pre-calculated metrics
        em_per_page = em_dashes / 3 if word_count == 0 else (em_dashes / word_count * 300)

        # Primary signal: em-dashes per page
        if em_per_page > 10:
            issues += 3  # Very strong AI signal
        elif em_per_page > 5:
            issues += 2
        elif em_per_page > THRESHOLDS.EM_DASH_MAX_PER_PAGE:
            issues += 1

        # Bold density (ChatGPT uses 10x more bold)
        bold_per_1k = bold_italic.get("bold_per_1k", 0)
        if bold_per_1k > THRESHOLDS.BOLD_EXTREME_AI_PER_1K:
            issues += 3  # Extreme AI marker
        elif bold_per_1k > THRESHOLDS.BOLD_AI_MIN_PER_1K:
            issues += 2
        elif bold_per_1k > THRESHOLDS.BOLD_HUMAN_MAX_PER_1K:
            issues += 1

        # Formatting consistency (mechanical distribution)
        consistency = bold_italic.get("formatting_consistency", 0)
        if consistency > THRESHOLDS.FORMATTING_CONSISTENCY_AI_THRESHOLD:
            issues += 2
        elif consistency > THRESHOLDS.FORMATTING_CONSISTENCY_MEDIUM:
            issues += 1

        # Convert issues to 0-100 score
        if issues == 0:
            score = 100.0
        elif issues <= 2:
            score = 75.0
        elif issues <= 4:
            score = 50.0
        else:
            score = 25.0

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

        # Get nested metrics
        formatting = metrics.get("formatting", {})
        bold_italic = metrics.get("bold_italic", {})

        em_dashes = formatting.get("em_dashes", 0)
        bold_per_1k = bold_italic.get("bold_per_1k", 0)
        italic_per_1k = bold_italic.get("italic_per_1k", 0)
        consistency = bold_italic.get("formatting_consistency", 0)

        # Em-dash recommendations
        if em_dashes > 5:
            recommendations.append(
                f"Reduce em-dash usage ({em_dashes} found). Replace with periods, semicolons, "
                f"commas, or parentheses for more natural flow."
            )

        # Bold density recommendations
        if bold_per_1k > THRESHOLDS.BOLD_AI_MIN_PER_1K:
            recommendations.append(
                f"Reduce bold formatting ({bold_per_1k:.1f} per 1k words, target <{THRESHOLDS.BOLD_HUMAN_MAX_PER_1K}). "
                f"Overuse of bold is a strong AI signal."
            )

        # Italic recommendations
        if italic_per_1k > 15:
            recommendations.append(
                f"Reduce italic usage ({italic_per_1k:.1f} per 1k words). "
                f"Excessive emphasis formatting is characteristic of AI writing."
            )

        # Formatting consistency recommendations
        if consistency > THRESHOLDS.FORMATTING_CONSISTENCY_AI_THRESHOLD:
            recommendations.append(
                f"Vary formatting distribution (consistency={consistency:.2f}). "
                f"Mechanical, evenly-spaced formatting suggests AI generation."
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

    def _count_words(self, text: str) -> int:
        """Count total words in text"""
        # Remove code blocks
        text = re.sub(r"```[sS]*?```", "", text)
        # Count words
        words = re.findall(r"\b[\w'-]+\b", text)
        return len(words)

    def _analyze_formatting(self, text: str) -> Dict:
        """Analyze formatting patterns."""
        # Em-dashes (— or --)
        em_dashes = len(re.findall(r"—|--", text))

        # Bold (markdown **text** or __text__)
        bold = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", text))

        # Italic (markdown *text* or _text_)
        italic = len(re.findall(r"\*[^*]+\*|_[^_]+_", text))

        return {"em_dashes": em_dashes, "bold": bold, "italics": italic}

    def _analyze_bold_italic_patterns(self, text: str) -> Dict:
        """
        Analyze bold/italic formatting distribution patterns.

        AI models (especially ChatGPT) use 10x more bold than humans.
        Research: Humans ~1-5 bold per 1k words, AI ~10-50 per 1k words.
        """
        word_count = count_words(text)

        # Bold (markdown **text** or __text__)
        bold_instances = re.findall(r"\*\*[^*]+\*\*|__[^_]+__", text)
        bold_count = len(bold_instances)
        bold_per_1k = (bold_count / word_count * 1000) if word_count > 0 else 0

        # Italic (markdown *text* or _text_)
        italic_instances = re.findall(r"\*[^*]+\*|_[^_]+_", text)
        italic_count = len(italic_instances)
        italic_per_1k = (italic_count / word_count * 1000) if word_count > 0 else 0

        # Calculate formatting consistency (spacing between bold/italic)
        # AI tends to use formatting at regular intervals
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        formatting_per_para = []
        for para in paragraphs:
            para_bold = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", para))
            para_italic = len(re.findall(r"\*[^*]+\*|_[^_]+_", para))
            formatting_per_para.append(para_bold + para_italic)

        # Low variance = high consistency (AI-like)
        if len(formatting_per_para) > 1:
            mean_fmt = statistics.mean(formatting_per_para)
            stdev_fmt = statistics.stdev(formatting_per_para)
            consistency = 1.0 - min(1.0, stdev_fmt / (mean_fmt + 1))
        else:
            consistency = 0.0

        return {
            "bold_per_1k": round(bold_per_1k, 2),
            "italic_per_1k": round(italic_per_1k, 2),
            "formatting_consistency": round(consistency, 3),
        }

    def _analyze_em_dashes_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[EmDashInstance]:
        """Track em-dashes with line numbers and context."""
        instances = []

        for line_num, line in enumerate(lines, start=1):
            # Skip HTML comments (metadata) and code blocks
            if html_comment_checker and html_comment_checker(line):
                continue
            if line.strip().startswith("```"):
                continue

            for match in re.finditer(r"—|--", line):
                # Get context around em-dash
                start = max(0, match.start() - 30)
                end = min(len(line), match.end() + 30)
                context = f"...{line[start:end]}..."

                instances.append(
                    EmDashInstance(
                        line_number=line_num,
                        context=context,
                        suggestion="Replace with period, semicolon, comma, or parentheses",
                    )
                )

        return instances

    def _analyze_formatting_issues_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[FormattingIssue]:
        """Detect excessive bold/italic usage and mechanical formatting patterns."""
        issues = []

        bold_pattern = re.compile(r"\*\*[^*]+\*\*|__[^_]+__")
        italic_pattern = re.compile(r"\*[^*]+\*|_[^_]+_")

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip HTML comments (metadata), headings, and code blocks
            if html_comment_checker and html_comment_checker(line):
                continue
            if stripped.startswith("#") or stripped.startswith("```"):
                continue

            if not stripped:
                continue

            # Count formatting on this line
            word_count = len(re.findall(r"\b\w+\b", line))
            if word_count == 0:
                continue

            bold_matches = list(bold_pattern.finditer(line))
            italic_matches = list(italic_pattern.finditer(line))

            bold_words = sum(len(re.findall(r"\b\w+\b", match.group())) for match in bold_matches)
            italic_words = sum(
                len(re.findall(r"\b\w+\b", match.group())) for match in italic_matches
            )

            bold_density = (bold_words / word_count) * 100 if word_count > 0 else 0
            italic_density = (italic_words / word_count) * 100 if word_count > 0 else 0

            # Excessive bold (>10% of words)
            if bold_density > 10:
                context = line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                issues.append(
                    FormattingIssue(
                        line_number=line_num,
                        issue_type="bold_dense",
                        context=context,
                        density=bold_density,
                        problem=f"Excessive bolding ({bold_density:.1f}% of words, target <5%)",
                        suggestion="Remove bold from less critical terms; reserve for key concepts only",
                    )
                )

            # Excessive italic (>15% of words, excluding functional use)
            if italic_density > 15:
                context = line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                issues.append(
                    FormattingIssue(
                        line_number=line_num,
                        issue_type="italic_dense",
                        context=context,
                        density=italic_density,
                        problem=f"Excessive italics ({italic_density:.1f}% of words, target <10%)",
                        suggestion="Use italics functionally: titles, defined terms, subtle emphasis only",
                    )
                )

        return issues

    # ========================================================================
    # PHASE 3 ADVANCED FORMATTING ANALYSIS METHODS
    # ========================================================================

    def _analyze_list_usage(self, text: str) -> Dict:
        """
        Analyze list structure and distribution.
        Research shows AI uses lists in 78% of responses, with 61% unordered vs 12% ordered.
        """
        lines = text.split("\n")

        ordered_items = []
        unordered_items = []

        # Detect list items
        for line in lines:
            stripped = line.strip()
            # Ordered list: "1. ", "2) ", "a. ", etc.
            if re.match(r"^(\d+|[a-z])[.)]\s+\S", stripped):
                # Extract item text
                item_text = re.sub(r"^(\d+|[a-z])[.)]\s+", "", stripped)
                ordered_items.append(item_text)
            # Unordered list: "- ", "* ", "+ "
            elif re.match(r"^[-*+]\s+\S", stripped):
                item_text = re.sub(r"^[-*+]\s+", "", stripped)
                unordered_items.append(item_text)

        total_items = len(ordered_items) + len(unordered_items)

        # Calculate list-to-text ratio (proportion of content in lists)
        word_count = self._count_words(text)
        list_words = sum(len(item.split()) for item in ordered_items + unordered_items)
        list_ratio = list_words / word_count if word_count > 0 else 0

        # Calculate ordered/unordered ratio (AI tends ~0.2, humans more balanced)
        if len(unordered_items) > 0:
            ordered_ratio = len(ordered_items) / len(unordered_items)
        elif len(ordered_items) > 0:
            ordered_ratio = 999  # All ordered (unusual)
        else:
            ordered_ratio = 0  # No lists

        # Calculate list item length variance (AI more uniform)
        item_lengths = [len(item.split()) for item in ordered_items + unordered_items]
        if len(item_lengths) > 1:
            item_variance = statistics.variance(item_lengths)
        else:
            item_variance = 0.0

        return {
            "total_list_items": total_items,
            "ordered_items": len(ordered_items),
            "unordered_items": len(unordered_items),
            "list_to_text_ratio": round(list_ratio, 3),
            "ordered_to_unordered_ratio": round(ordered_ratio, 3),
            "list_item_variance": round(item_variance, 2),
        }

    def _analyze_punctuation_clustering(self, text: str) -> Dict:
        """
        Analyze punctuation patterns that distinguish AI from human writing.
        Key markers: em-dash cascading, Oxford comma consistency, semicolon usage.
        """
        word_count = self._count_words(text)
        paragraphs = [p.strip() for p in re.split(r"ns*n", text) if p.strip()]

        # Em-dash cascading analysis (AI shows declining frequency pattern)
        em_dash_positions = []
        for i, para in enumerate(paragraphs):
            dash_count = len(re.findall(r"—|--", para))
            if dash_count > 0:
                em_dash_positions.extend([i] * dash_count)

        # Calculate cascading score (correlation between position and frequency)
        # Negative correlation = cascading pattern (AI marker)
        if len(em_dash_positions) > 3:
            list(range(len(em_dash_positions)))
            # Count dashes per paragraph position
            dash_per_para = [em_dash_positions.count(i) for i in range(len(paragraphs))]
            # Calculate if early paragraphs have more dashes (AI pattern)
            if sum(dash_per_para[: len(dash_per_para) // 2]) > sum(
                dash_per_para[len(dash_per_para) // 2 :]
            ):
                cascading = 0.7 + (len(em_dash_positions) / (len(paragraphs) + 1)) * 0.3
            else:
                cascading = 0.3
        else:
            cascading = 0.0

        # Oxford comma analysis (AI strongly prefers Oxford comma)
        # Pattern: "word, word, and word" vs "word, word and word"
        oxford_pattern = r"\b\w+,\s+\w+,\s+(and|or)\s+\w+\b"
        non_oxford_pattern = r"\b\w+,\s+\w+\s+(and|or)\s+\w+\b"

        oxford_count = len(re.findall(oxford_pattern, text, re.IGNORECASE))
        non_oxford_count = len(re.findall(non_oxford_pattern, text, re.IGNORECASE))

        total_comma_lists = oxford_count + non_oxford_count
        if total_comma_lists > 0:
            oxford_consistency = oxford_count / total_comma_lists
        else:
            oxford_consistency = 0.5  # Neutral if no lists found

        # Semicolon analysis
        semicolons = len(re.findall(r";", text))
        semicolon_per_1k = (semicolons / word_count * 1000) if word_count > 0 else 0

        return {
            "em_dash_positions": em_dash_positions[:20],  # Limit for dataclass
            "em_dash_cascading": round(cascading, 3),
            "oxford_comma_count": oxford_count,
            "non_oxford_comma_count": non_oxford_count,
            "oxford_consistency": round(oxford_consistency, 3),
            "semicolon_count": semicolons,
            "semicolon_per_1k": round(semicolon_per_1k, 2),
        }

    def _analyze_whitespace_patterns(self, text: str) -> Dict:
        """
        Analyze whitespace and paragraph structure patterns.
        Humans vary paragraph length for pacing; AI produces uniform paragraphs.
        """
        paragraphs = [p.strip() for p in re.split(r"ns*n", text) if p.strip()]

        # Paragraph length variance (higher = more human)
        para_lengths = [len(p.split()) for p in paragraphs]
        if len(para_lengths) > 1:
            para_variance = statistics.variance(para_lengths)
            para_mean = statistics.mean(para_lengths)
            # Coefficient of variation as uniformity score (lower CV = more uniform = AI)
            cv = statistics.stdev(para_lengths) / para_mean if para_mean > 0 else 0
            uniformity = 1.0 - min(1.0, cv / 1.0)  # Normalize to 0-1
        else:
            para_variance = 0.0
            uniformity = 1.0  # Single paragraph = perfectly uniform

        # Blank line analysis
        lines = text.split("n")
        blank_lines = [i for i, line in enumerate(lines) if not line.strip()]
        blank_count = len(blank_lines)

        # Calculate spacing between blank lines (consistency)
        if len(blank_lines) > 1:
            spacings = [blank_lines[i + 1] - blank_lines[i] for i in range(len(blank_lines) - 1)]
            blank_variance = statistics.variance(spacings) if len(spacings) > 1 else 0.0
        else:
            blank_variance = 0.0

        # Text density (characters per non-blank line)
        non_blank_lines = [line for line in lines if line.strip()]
        if non_blank_lines:
            avg_line_length = sum(len(line) for line in non_blank_lines) / len(non_blank_lines)
        else:
            avg_line_length = 0.0

        return {
            "paragraph_variance": round(para_variance, 2),
            "paragraph_uniformity": round(uniformity, 3),
            "blank_lines": blank_count,
            "blank_line_variance": round(blank_variance, 2),
            "text_density": round(avg_line_length, 1),
        }

    def _analyze_punctuation_spacing_cv(self, text: str) -> Dict:
        """
        Analyze punctuation distribution via coefficient of variation.
        AI distributes uniformly (low CV), humans cluster naturally (high CV).

        Returns dict with keys: colon_spacing_cv, primary_cv, score, assessment,
        spacing_examples, colon_count, semicolon_count, emdash_count
        """
        # Find positions of key punctuation marks (word offsets)
        words = text.split()

        colon_positions = []
        semicolon_positions = []
        emdash_positions = []

        for i, word in enumerate(words):
            if ":" in word:
                colon_positions.append(i)
            if ";" in word:
                semicolon_positions.append(i)
            if "—" in word or "--" in word:
                emdash_positions.append(i)

        def calculate_spacing_cv(positions):
            """Calculate coefficient of variation for spacing between marks."""
            if len(positions) < 3:
                return None
            spacing = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
            if len(spacing) < 2:
                return None
            mean_spacing = statistics.mean(spacing)
            if mean_spacing == 0:
                return 0.0
            stddev = statistics.stdev(spacing)
            return stddev / mean_spacing

        colon_cv = calculate_spacing_cv(colon_positions)
        semicolon_cv = calculate_spacing_cv(semicolon_positions)
        emdash_cv = calculate_spacing_cv(emdash_positions)

        # Use colon CV as primary (most common in technical writing)
        # Check explicitly for None since 0.0 is a valid CV value
        if colon_cv is not None:
            primary_cv = colon_cv
        elif semicolon_cv is not None:
            primary_cv = semicolon_cv
        elif emdash_cv is not None:
            primary_cv = emdash_cv
        else:
            primary_cv = 1.0

        # Scoring based on CV (higher CV = more human-like clustering)
        if primary_cv >= 0.7:
            score, assessment = 6.0, "EXCELLENT"
        elif primary_cv >= 0.5:
            score, assessment = 4.0, "GOOD"
        elif primary_cv >= 0.3:
            score, assessment = 2.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        spacing_examples = {}
        if colon_positions and len(colon_positions) > 1:
            spacing_examples["colons"] = [
                colon_positions[i + 1] - colon_positions[i]
                for i in range(min(5, len(colon_positions) - 1))
            ]

        return {
            "colon_spacing_cv": round(colon_cv, 3) if colon_cv is not None else None,
            "semicolon_spacing_cv": round(semicolon_cv, 3) if semicolon_cv is not None else None,
            "emdash_spacing_cv": round(emdash_cv, 3) if emdash_cv is not None else None,
            "primary_cv": round(primary_cv, 3),
            "score": score,
            "assessment": assessment,
            "spacing_examples": spacing_examples,
            "colon_count": len(colon_positions),
            "semicolon_count": len(semicolon_positions),
            "emdash_count": len(emdash_positions),
        }


# Backward compatibility alias
FormattingAnalyzer = FormattingDimension

# Module-level singleton - triggers self-registration on module import
_instance = FormattingDimension()
