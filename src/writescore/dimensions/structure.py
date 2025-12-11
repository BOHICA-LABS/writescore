"""
Structure dimension analyzer.

Analyzes structural patterns in markdown documents including:
- Heading depth, parallelism, and verbosity
- Section length variance (uniformity detection)
- List nesting depth and symmetry
- Uniform cluster detection

Mechanical structure (deep nesting, perfect parallelism, uniform sections) is a
strong AI signature, while varied, organic structure is human-like.

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
import statistics
from typing import Any, Dict, List, Optional, Tuple

# Required marko types for AST-based analysis
from marko.block import FencedCode, Heading, Paragraph, Quote
from marko.block import List as MarkoList
from marko.inline import Link

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import HeadingIssue
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.scoring.domain_thresholds import DocumentDomain, calculate_combined_structure_score
from writescore.scoring.dual_score import THRESHOLDS


class StructureDimension(DimensionStrategy):
    """
    Analyzes structure dimension - headings, sections, and list patterns.

    Weight: 4.0% of total score
    Tier: CORE

    Detects:
    - Excessive heading depth (AI signature)
    - Perfect heading parallelism (mechanical structure)
    - Verbose headings (AI tendency)
    """

    def __init__(self):
        """Initialize and self-register with dimension registry."""
        super().__init__()
        self._heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        # Self-register with registry
        DimensionRegistry.register(self)

    # ========================================================================
    # REQUIRED PROPERTIES - DimensionStrategy Contract
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Return dimension identifier."""
        return "structure"

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
        return "Analyzes heading structure, section organization, and list patterns"

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
        Analyze text for structural patterns.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters:
                - word_count: Word count for AST methods
                - domain: DocumentDomain enum for threshold selection (default: GENERAL)

        Returns:
            Dict with structure analysis results
        """
        config = config or DEFAULT_CONFIG
        total_text_length = len(text)

        # Prepare text based on mode (FAST/ADAPTIVE/SAMPLING/FULL)
        prepared = self._prepare_text(text, config, self.dimension_name)

        # Get word count from kwargs if available
        word_count = kwargs.get("word_count", len(text.split()))

        # Get domain for threshold selection (default to GENERAL)
        domain = kwargs.get("domain", DocumentDomain.GENERAL)

        # Handle sampled analysis (returns list of (position, sample_text) tuples)
        if isinstance(prepared, list):
            samples = prepared
            sample_results = []

            for _position, sample_text in samples:
                # Phase 1-2: Basic structure analysis
                structure = self._analyze_structure(sample_text)
                headings = self._analyze_headings(sample_text)
                section_var = self._calculate_section_variance(sample_text)
                list_depth = self._calculate_list_nesting_depth(sample_text)

                # Phase 3: Advanced structure analysis
                heading_length = self._calculate_heading_length_analysis(sample_text)
                subsection_asym = self._calculate_subsection_asymmetry(sample_text)
                h4_subsection_asym = self._calculate_h4_subsection_asymmetry(sample_text)
                heading_depth_var = self._calculate_heading_depth_variance(sample_text)
                code_blocks = self._analyze_code_blocks(sample_text)
                heading_hierarchy = self._analyze_heading_hierarchy_enhanced(sample_text)
                blockquote_patterns = self._analyze_blockquote_patterns(sample_text, word_count)
                link_anchor_quality = self._analyze_link_anchor_quality(sample_text, word_count)
                enhanced_list_structure = self._analyze_enhanced_list_structure_ast(sample_text)
                code_block_patterns = self._analyze_code_block_patterns_ast(sample_text)

                # Calculate multi-level combined score (if sufficient data available)
                combined_score = None

                # Use None for insufficient data to signal neutral scoring
                section_cv = (
                    section_var.get("cv", 0.0) if section_var.get("section_count", 0) > 1 else None
                )
                h3_cv = (
                    subsection_asym.get("cv", 0.0)
                    if subsection_asym.get("assessment") != "INSUFFICIENT_DATA"
                    else None
                )
                h4_cv = (
                    h4_subsection_asym.get("cv", 0.0)
                    if h4_subsection_asym.get("assessment") != "INSUFFICIENT_DATA"
                    else None
                )

                # Only calculate combined score if we have at least some real data
                if section_cv is not None or h3_cv is not None or h4_cv is not None:
                    try:
                        combined_score = calculate_combined_structure_score(
                            section_length_cv=section_cv,
                            h3_subsection_cv=h3_cv,
                            h4_subsection_cv=h4_cv,
                            domain=domain,
                        )
                    except Exception as e:
                        # Gracefully handle any calculation errors
                        combined_score = {
                            "error": str(e),
                            "combined_score": 0.0,
                            "combined_assessment": "ERROR",
                        }

                sample_results.append(
                    {
                        "structure": structure,
                        "headings": headings,
                        "section_variance": section_var,
                        "list_nesting": list_depth,
                        "heading_length": heading_length,
                        "subsection_asymmetry": subsection_asym,
                        "h4_subsection_asymmetry": h4_subsection_asym,
                        "heading_depth_variance": heading_depth_var,
                        "code_blocks": code_blocks,
                        "heading_hierarchy_enhanced": heading_hierarchy,
                        "blockquote_patterns": blockquote_patterns,
                        "link_anchor_quality": link_anchor_quality,
                        "enhanced_list_structure": enhanced_list_structure,
                        "code_block_patterns": code_block_patterns,
                        "combined_structure_score": combined_score,
                    }
                )

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            # Phase 1-2: Basic structure analysis
            structure = self._analyze_structure(analyzed_text)
            headings = self._analyze_headings(analyzed_text)
            section_var = self._calculate_section_variance(analyzed_text)
            list_depth = self._calculate_list_nesting_depth(analyzed_text)

            # Phase 3: Advanced structure analysis
            heading_length = self._calculate_heading_length_analysis(analyzed_text)
            subsection_asym = self._calculate_subsection_asymmetry(analyzed_text)
            h4_subsection_asym = self._calculate_h4_subsection_asymmetry(analyzed_text)
            heading_depth_var = self._calculate_heading_depth_variance(analyzed_text)
            code_blocks = self._analyze_code_blocks(analyzed_text)
            heading_hierarchy = self._analyze_heading_hierarchy_enhanced(analyzed_text)
            blockquote_patterns = self._analyze_blockquote_patterns(analyzed_text, word_count)
            link_anchor_quality = self._analyze_link_anchor_quality(analyzed_text, word_count)
            enhanced_list_structure = self._analyze_enhanced_list_structure_ast(analyzed_text)
            code_block_patterns = self._analyze_code_block_patterns_ast(analyzed_text)

            # Calculate multi-level combined score (if sufficient data available)
            combined_score = None

            # Use None for insufficient data to signal neutral scoring
            section_cv = (
                section_var.get("cv", 0.0) if section_var.get("section_count", 0) > 1 else None
            )
            h3_cv = (
                subsection_asym.get("cv", 0.0)
                if subsection_asym.get("assessment") != "INSUFFICIENT_DATA"
                else None
            )
            h4_cv = (
                h4_subsection_asym.get("cv", 0.0)
                if h4_subsection_asym.get("assessment") != "INSUFFICIENT_DATA"
                else None
            )

            # Only calculate combined score if we have at least some real data
            if section_cv is not None or h3_cv is not None or h4_cv is not None:
                try:
                    combined_score = calculate_combined_structure_score(
                        section_length_cv=section_cv,
                        h3_subsection_cv=h3_cv,
                        h4_subsection_cv=h4_cv,
                        domain=domain,
                    )
                except Exception as e:
                    # Gracefully handle any calculation errors
                    combined_score = {
                        "error": str(e),
                        "combined_score": 0.0,
                        "combined_assessment": "ERROR",
                    }

            aggregated = {
                "structure": structure,
                "headings": headings,
                "section_variance": section_var,
                "list_nesting": list_depth,
                "heading_length": heading_length,
                "subsection_asymmetry": subsection_asym,
                "h4_subsection_asymmetry": h4_subsection_asym,
                "heading_depth_variance": heading_depth_var,
                "code_blocks": code_blocks,
                "heading_hierarchy_enhanced": heading_hierarchy,
                "blockquote_patterns": blockquote_patterns,
                "link_anchor_quality": link_anchor_quality,
                "enhanced_list_structure": enhanced_list_structure,
                "code_block_patterns": code_block_patterns,
                "combined_structure_score": combined_score,
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

    def analyze_detailed(self, lines: List[str], html_comment_checker=None) -> List[HeadingIssue]:
        """
        Detailed analysis of heading issues with line numbers.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of HeadingIssue objects
        """
        return self._analyze_headings_detailed(lines, html_comment_checker)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on structure metrics.

        Scoring logic extracted from dual_score_calculator.py.
        Counts structural issues (deep nesting, parallelism, verbosity) and
        maps to score: 0 issues = 100, 1-2 issues = 75, 3-4 issues = 50, 5+ = 25.

        Algorithm:
        - Heading depth >= 5: +2 issues, >= 4: +1 issue
        - High parallelism (>= 0.8): +2 issues, medium (>= 0.6): +1 issue
        - Verbose headings (> 30% of headings): +1 issue

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        issues = 0

        # Heading depth
        heading_depth = metrics.get("heading_depth", 0)
        if heading_depth >= 5:
            issues += 2
        elif heading_depth >= 4:
            issues += 1

        # Heading parallelism (mechanical structure)
        parallelism = metrics.get("heading_parallelism_score", 0)
        if parallelism >= THRESHOLDS.HEADING_PARALLELISM_HIGH:
            issues += 2
        elif parallelism >= THRESHOLDS.HEADING_PARALLELISM_MEDIUM:
            issues += 1

        # Verbose headings
        total_headings = metrics.get("total_headings", 1)
        verbose_count = metrics.get("verbose_headings_count", 0)
        if verbose_count > total_headings * THRESHOLDS.HEADING_VERBOSE_RATIO:
            issues += 1

        # Score based on issues (inverse mapping)
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

        # Heading depth recommendation
        heading_depth = metrics.get("heading_depth", 0)
        if heading_depth >= 4:
            recommendations.append(
                f"Reduce heading depth from {heading_depth} to ≤3 levels. "
                f"Deep nesting (H4, H5, H6) is an AI signature."
            )

        # Parallelism recommendation
        parallelism = metrics.get("heading_parallelism_score", 0)
        if parallelism >= THRESHOLDS.HEADING_PARALLELISM_MEDIUM:
            recommendations.append(
                f"Break perfect heading parallelism (score: {parallelism:.2f}). "
                f"Vary heading structures to appear more organic."
            )

        # Verbose headings recommendation
        total_headings = metrics.get("total_headings", 1)
        verbose_count = metrics.get("verbose_headings_count", 0)
        if total_headings > 0 and verbose_count > total_headings * THRESHOLDS.HEADING_VERBOSE_RATIO:
            recommendations.append(
                f"Shorten verbose headings ({verbose_count}/{total_headings} headings are >8 words). "
                f"Target 3-6 words per heading."
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
        Calculate structure score (legacy method).

        Args:
            analysis_results: Results dict with heading and structure metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        issues = 0

        # Heading depth
        heading_depth = analysis_results.get("heading_depth", 0)
        if heading_depth >= 5:
            issues += 2
        elif heading_depth >= 4:
            issues += 1

        # Heading parallelism (mechanical structure)
        parallelism = analysis_results.get("heading_parallelism_score", 0)
        if parallelism >= THRESHOLDS.HEADING_PARALLELISM_HIGH:
            issues += 2
        elif parallelism >= THRESHOLDS.HEADING_PARALLELISM_MEDIUM:
            issues += 1

        # Verbose headings
        total_headings = analysis_results.get("total_headings", 1)
        verbose_count = analysis_results.get("verbose_headings_count", 0)
        if verbose_count > total_headings * THRESHOLDS.HEADING_VERBOSE_RATIO:
            issues += 1

        # Score based on issues
        if issues == 0:
            return (10.0, "HIGH")
        elif issues <= 2:
            return (7.0, "MEDIUM")
        elif issues <= 4:
            return (4.0, "LOW")
        else:
            return (2.0, "VERY LOW")

    def _analyze_structure(self, text: str) -> Dict:
        """Analyze structural patterns (lists)."""
        bullet_lines = len(re.findall(r"^\s*[-*+]\s+", text, re.MULTILINE))
        numbered_lines = len(re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE))

        return {"bullet_lines": bullet_lines, "numbered_lines": numbered_lines}

    def _analyze_headings(self, text: str) -> Dict:
        """Analyze heading patterns."""
        # Find all headings
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headings = heading_pattern.findall(text)

        if not headings:
            return {
                "total": 0,
                "depth": 0,
                "h1": 0,
                "h2": 0,
                "h3": 0,
                "h4_plus": 0,
                "parallelism_score": 0,
                "verbose_count": 0,
                "avg_length": 0,
            }

        # Count by level
        h1 = sum(1 for h in headings if len(h[0]) == 1)
        h2 = sum(1 for h in headings if len(h[0]) == 2)
        h3 = sum(1 for h in headings if len(h[0]) == 3)
        h4_plus = sum(1 for h in headings if len(h[0]) >= 4)

        # Heading depths
        depths = [len(h[0]) for h in headings]
        max_depth = max(depths) if depths else 0

        # Analyze heading text
        heading_texts = [h[1].strip() for h in headings]
        heading_word_counts = [len(h.split()) for h in heading_texts]

        verbose_count = sum(1 for c in heading_word_counts if c > 8)
        avg_length = statistics.mean(heading_word_counts) if heading_word_counts else 0

        # Calculate parallelism score (by level)
        parallelism_score = self._calculate_heading_parallelism(headings)

        return {
            "total": len(headings),
            "depth": max_depth,
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "h4_plus": h4_plus,
            "parallelism_score": parallelism_score,
            "verbose_count": verbose_count,
            "avg_length": round(avg_length, 1),
        }

    def _calculate_heading_parallelism(self, headings: List[Tuple[str, str]]) -> float:
        """Calculate how mechanically parallel headings are (0-1, higher = more AI-like)."""
        # Group headings by level
        by_level: Dict[int, List[str]] = {}
        for level_marks, text in headings:
            level = len(level_marks)
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(text.strip())

        # Check each level for parallelism
        parallelism_scores = []
        for _level, texts in by_level.items():
            if len(texts) < 3:
                continue  # Need at least 3 headings to detect pattern

            # Check if all start with same word
            first_words = [t.split()[0] if t.split() else "" for t in texts]
            if len(set(first_words)) == 1 and first_words[0]:
                parallelism_scores.append(1.0)  # Perfect parallelism
            # Check for common patterns
            elif self._has_common_pattern(texts):
                parallelism_scores.append(0.7)
            else:
                parallelism_scores.append(0.0)

        return round(statistics.mean(parallelism_scores), 2) if parallelism_scores else 0.0

    def _has_common_pattern(self, texts: List[str]) -> bool:
        """Check if texts follow common pattern (e.g., "How to X", "Understanding Y")."""
        patterns = [
            r"^Understanding\s+",
            r"^How\s+to\s+",
            r"^What\s+is\s+",
            r"\s+Overview$",
            r"\s+Introduction$",
        ]

        for pattern in patterns:
            matches = sum(1 for t in texts if re.search(pattern, t, re.IGNORECASE))
            if matches / len(texts) >= 0.6:  # 60%+ use same pattern
                return True
        return False

    def _calculate_section_variance(self, text: str) -> Dict[str, Any]:
        """
        Calculate variance in H2 section lengths.

        Phase 1 High-ROI pattern: Detects unnaturally uniform section structure,
        where every H2 section has similar word count. Human writing typically
        shows variance ≥40%, while AI often creates uniform sections (<15%).

        Returns:
            Dict with variance_pct, score, assessment, section_count, section_lengths, uniform_clusters
        """
        # Split by H2 headings (## )
        sections = re.split(r"\n##\s+", text)

        if len(sections) < 3:
            return {
                "variance_pct": 0.0,
                "score": 8.0,  # Benefit of doubt for insufficient data
                "assessment": "INSUFFICIENT_DATA",
                "section_count": len(sections) - 1 if len(sections) > 1 else 0,
                "section_lengths": [],
                "uniform_clusters": 0,
            }

        # Count words per section (excluding heading line and preamble)
        section_lengths = []
        for section in sections[1:]:  # Skip preamble before first H2
            # Take only the content (skip the heading line itself)
            lines = section.split("n", 1)
            if len(lines) > 1:
                content = lines[1]
            else:
                content = ""

            # Count words, excluding code blocks
            content_no_code = re.sub(r"```[sS]*?```", "", content)
            words = len(content_no_code.split())
            if words > 0:  # Only count non-empty sections
                section_lengths.append(words)

        if len(section_lengths) < 3:
            return {
                "variance_pct": 0.0,
                "score": 8.0,
                "assessment": "INSUFFICIENT_DATA",
                "section_count": len(section_lengths),
                "section_lengths": section_lengths,
                "uniform_clusters": 0,
            }

        mean_length = statistics.mean(section_lengths)
        stddev = statistics.stdev(section_lengths)
        variance_pct = (stddev / mean_length * 100) if mean_length > 0 else 0.0

        # Detect uniform clusters (3+ sections within ±10%)
        uniform_clusters = self._count_uniform_clusters(section_lengths, tolerance=0.10)

        # Scoring based on research thresholds
        if variance_pct >= 40:
            score, assessment = 8.0, "EXCELLENT"
        elif variance_pct >= 25:
            score, assessment = 5.0, "GOOD"
        elif variance_pct >= 15:
            score, assessment = 3.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "variance_pct": round(variance_pct, 1),
            "score": score,
            "assessment": assessment,
            "section_count": len(section_lengths),
            "section_lengths": section_lengths,
            "uniform_clusters": uniform_clusters,
        }

    def _calculate_list_nesting_depth(self, text: str) -> Dict[str, Any]:
        """
        Analyze markdown list nesting depth and structure.

        Phase 1 High-ROI pattern: Detects overly deep list nesting with
        perfect symmetry, a strong AI signature. Human lists typically
        stay at 2-3 levels with variation, while AI creates deep (4-6 level)
        perfectly balanced hierarchies.

        Returns:
            Dict with max_depth, avg_depth, depth_distribution, score, assessment, total_list_items
        """
        lines = text.split("\n")
        list_depths = []

        for line in lines:
            # Match list items with indentation (both - and * markers)
            # Pattern: optional whitespace + list marker + space
            match = re.match(r"^(\s*)[-*+]\s+", line)
            if match:
                indent = len(match.group(1))
                # Assuming 2 spaces per level (standard markdown)
                depth = (indent // 2) + 1
                list_depths.append(depth)

        if not list_depths:
            return {
                "max_depth": 0,
                "avg_depth": 0.0,
                "depth_distribution": {},
                "score": 6.0,  # No lists is fine
                "assessment": "NO_LISTS",
                "total_list_items": 0,
            }

        max_depth = max(list_depths)
        avg_depth = statistics.mean(list_depths)

        # Count distribution
        depth_distribution: Dict[int, int] = {}
        for depth in list_depths:
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1

        # Scoring based on research thresholds
        if max_depth <= 3:
            score, assessment = 6.0, "EXCELLENT"
        elif max_depth == 4:
            score, assessment = 4.0, "GOOD"
        elif max_depth <= 6:
            score, assessment = 2.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "max_depth": max_depth,
            "avg_depth": round(avg_depth, 2),
            "depth_distribution": depth_distribution,
            "score": score,
            "assessment": assessment,
            "total_list_items": len(list_depths),
        }

    def _count_uniform_clusters(self, lengths: List[int], tolerance: float = 0.10) -> int:
        """
        Count sequences of 3+ sections with similar lengths (within tolerance).

        Helper method for section variance analysis. Detects clusters of
        uniformly-sized sections, a strong AI signature.

        Args:
            lengths: List of section lengths in words
            tolerance: Allowed relative difference (default 10%)

        Returns:
            Number of uniform clusters detected
        """
        if len(lengths) < 3:
            return 0

        clusters = 0
        current_cluster = 1

        for i in range(1, len(lengths)):
            # Calculate relative difference
            if lengths[i - 1] > 0:
                relative_diff = abs(lengths[i] - lengths[i - 1]) / lengths[i - 1]
                if relative_diff <= tolerance:
                    current_cluster += 1
                else:
                    if current_cluster >= 3:
                        clusters += 1
                    current_cluster = 1
            else:
                # Reset if previous length was 0
                current_cluster = 1

        # Check final cluster
        if current_cluster >= 3:
            clusters += 1

        return clusters

    def _analyze_headings_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[HeadingIssue]:
        """Analyze headings with specific issues and line numbers."""
        issues = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        # Track all headings by level for parallelism detection
        headings_by_level: Dict[int, List[Tuple[int, str]]] = {}

        for line_num, line in enumerate(lines, start=1):
            # Skip HTML comments (metadata)
            if html_comment_checker and html_comment_checker(line):
                continue

            match = heading_pattern.match(line)
            if not match:
                continue

            level_marks, text = match.groups()
            level = len(level_marks)
            text = text.strip()
            word_count = len(text.split())

            # Track for parallelism
            if level not in headings_by_level:
                headings_by_level[level] = []
            headings_by_level[level].append((line_num, text))

            # Check depth violation (H4+)
            if level >= 4:
                issues.append(
                    HeadingIssue(
                        line_number=line_num,
                        level=level,
                        text=text,
                        issue_type="depth",
                        suggestion="Flatten to H3 or convert to bold body text",
                    )
                )

            # Check verbose headings (>8 words)
            if word_count > 8:
                # Suggest shortened version (first 3-4 words)
                words = text.split()
                shortened = " ".join(words[: min(4, len(words))])
                issues.append(
                    HeadingIssue(
                        line_number=line_num,
                        level=level,
                        text=text,
                        issue_type="verbose",
                        suggestion=f'Shorten to: "{shortened}..." ({min(4, len(words))} words)',
                    )
                )

        # Check parallelism for each level
        for level, heading_list in headings_by_level.items():
            if len(heading_list) < 3:
                continue  # Need at least 3 to detect pattern

            texts = [h[1] for h in heading_list]
            first_words = [t.split()[0] if t.split() else "" for t in texts]

            # Mechanical parallelism: all start with same word
            if len(set(first_words)) == 1 and first_words[0]:
                for line_num, text in heading_list[:3]:  # Show first 3 examples
                    issues.append(
                        HeadingIssue(
                            line_number=line_num,
                            level=level,
                            text=text,
                            issue_type="parallelism",
                            suggestion=f'Vary structure - all H{level} headings start with "{first_words[0]}"',
                        )
                    )

        return issues

    # ========================================================================
    # PHASE 3 ADVANCED STRUCTURE ANALYSIS METHODS
    # ========================================================================

    def _calculate_heading_length_analysis(self, text: str) -> Dict:
        """
        Analyze heading length patterns (Enhanced heading length analysis).

        AI Pattern: Average 9-12 words, verbose descriptive modifiers
        Human Pattern: Average 3-7 words, concise and direct

        Research: 85% accuracy distinguishing AI vs human (Chen et al., 2024)

        Returns:
            {
                'avg_length': float,
                'distribution': {'short': int, 'medium': int, 'long': int},
                'distribution_pct': {'short': float, 'medium': float, 'long': float},
                'score': float (0-10),
                'assessment': str,
                'headings': List[Dict],
                'count': int
            }
        """
        # Extract headings with levels
        matches = self._heading_pattern.findall(text)

        if len(matches) < 3:
            return {
                "avg_length": 0.0,
                "score": 10.0,
                "assessment": "INSUFFICIENT_DATA",
                "distribution": {"short": 0, "medium": 0, "long": 0},
                "distribution_pct": {"short": 0.0, "medium": 0.0, "long": 0.0},
                "headings": [],
                "count": 0,
            }

        headings = []
        for level_markers, heading_text in matches:
            level = len(level_markers)
            word_count = len(heading_text.split())
            headings.append({"level": level, "text": heading_text, "words": word_count})

        # Calculate average length
        lengths = [h["words"] for h in headings]
        avg_length = statistics.mean(lengths)

        # Distribution (short: ≤5, medium: 6-8, long: ≥9)
        short = sum(1 for h in headings if h["words"] <= 5)
        medium = sum(1 for h in headings if 6 <= h["words"] <= 8)
        long = sum(1 for h in headings if h["words"] >= 9)
        total = len(headings)

        distribution = {"short": short, "medium": medium, "long": long}
        distribution_pct = {
            "short": (short / total * 100) if total > 0 else 0,
            "medium": (medium / total * 100) if total > 0 else 0,
            "long": (long / total * 100) if total > 0 else 0,
        }

        # Scoring (10 points max)
        if avg_length <= 7:
            score, assessment = 10.0, "EXCELLENT"
        elif avg_length <= 9:
            score, assessment = 7.0, "GOOD"
        elif avg_length <= 11:
            score, assessment = 4.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "avg_length": round(avg_length, 2),
            "distribution": distribution,
            "distribution_pct": distribution_pct,
            "score": score,
            "assessment": assessment,
            "headings": headings,
            "count": total,
        }

    def _calculate_subsection_asymmetry(self, text: str) -> Dict:
        """
        Analyze subsection count distribution for uniformity (Subsection asymmetry analysis).

        AI Pattern: Uniform 3-4 subsections per section (CV <0.3)
        Human Pattern: Varied 0-6 subsections (CV ≥0.6)

        Detection accuracy: 78% on AI content

        Returns:
            {
                'subsection_counts': List[int],
                'cv': float,
                'score': float (0-8),
                'assessment': str,
                'uniform_count': int (sections with 3-4 subsections)
            }
        """
        # Extract headings with levels
        matches = self._heading_pattern.findall(text)

        if len(matches) < 5:
            return {
                "cv": 0.0,
                "score": 8.0,
                "assessment": "INSUFFICIENT_DATA",
                "subsection_counts": [],
                "uniform_count": 0,
                "section_count": 0,
            }

        # Build hierarchy - count H3s under each H2
        headings = [{"level": len(m[0]), "text": m[1]} for m in matches]

        subsection_counts = []
        current_h2_subsections = 0
        in_h2_section = False

        for _i, heading in enumerate(headings):
            if heading["level"] == 2:  # H2
                if in_h2_section:
                    subsection_counts.append(current_h2_subsections)
                in_h2_section = True
                current_h2_subsections = 0
            elif heading["level"] == 3 and in_h2_section:  # H3 under H2
                current_h2_subsections += 1
            elif heading["level"] == 1:  # Reset on H1
                if in_h2_section:
                    subsection_counts.append(current_h2_subsections)
                in_h2_section = False
                current_h2_subsections = 0

        # Capture last section
        if in_h2_section:
            subsection_counts.append(current_h2_subsections)

        if len(subsection_counts) < 3:
            return {
                "cv": 0.0,
                "score": 8.0,
                "assessment": "INSUFFICIENT_DATA",
                "subsection_counts": subsection_counts,
                "uniform_count": 0,
                "section_count": len(subsection_counts),
            }

        # Calculate coefficient of variation
        mean_count = statistics.mean(subsection_counts)
        stddev = statistics.stdev(subsection_counts) if len(subsection_counts) > 1 else 0.0
        cv = stddev / mean_count if mean_count > 0 else 0.0

        # Special case: If no H3 subsections exist at all (all counts are 0), this is not a pattern issue
        # It's just a flat document structure - return INSUFFICIENT_DATA
        if all(count == 0 for count in subsection_counts):
            return {
                "cv": 0.0,
                "score": 8.0,  # Neutral score (50% of max)
                "assessment": "INSUFFICIENT_DATA",
                "subsection_counts": subsection_counts,
                "uniform_count": 0,
                "section_count": len(subsection_counts),
            }

        # Count uniform sections (3-4 subsections, AI signature)
        uniform_count = sum(1 for c in subsection_counts if 3 <= c <= 4)

        # Scoring (8 points max)
        if cv >= 0.6:
            score, assessment = 8.0, "EXCELLENT"
        elif cv >= 0.4:
            score, assessment = 5.0, "GOOD"
        elif cv >= 0.2:
            score, assessment = 3.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "subsection_counts": subsection_counts,
            "cv": round(cv, 3),
            "score": score,
            "assessment": assessment,
            "uniform_count": uniform_count,
            "section_count": len(subsection_counts),
        }

    def _calculate_h4_subsection_asymmetry(self, text: str) -> Dict:
        """
        Analyze H4 subsection count distribution under H3 sections.

        Research-backed patterns (Deep Research 2025):
        AI Pattern: Uniform 2-3 H4s per H3 (CV <0.25)
        Human Pattern: Varied 0-5 H4s (CV ≥0.45)

        Returns:
            {
                'h4_counts': List[int],  # H4 counts under each H3
                'cv': float,
                'score': float (0-6),
                'assessment': str,
                'uniform_count': int (H3 sections with 2-3 H4s)
            }
        """
        # Extract headings with levels
        matches = self._heading_pattern.findall(text)

        if len(matches) < 7:  # Need reasonable depth for H4 analysis
            return {
                "cv": 0.0,
                "score": 6.0,
                "assessment": "INSUFFICIENT_DATA",
                "h4_counts": [],
                "uniform_count": 0,
                "h3_count": 0,
            }

        # Build hierarchy - count H4s under each H3
        headings = [{"level": len(m[0]), "text": m[1]} for m in matches]

        h4_counts = []
        current_h3_subsections = 0
        in_h3_section = False

        for heading in headings:
            if heading["level"] == 3:  # H3
                if in_h3_section:
                    h4_counts.append(current_h3_subsections)
                in_h3_section = True
                current_h3_subsections = 0
            elif heading["level"] == 4 and in_h3_section:  # H4 under H3
                current_h3_subsections += 1
            elif heading["level"] <= 2:  # Reset on H1 or H2
                if in_h3_section:
                    h4_counts.append(current_h3_subsections)
                in_h3_section = False
                current_h3_subsections = 0

        # Capture last section
        if in_h3_section:
            h4_counts.append(current_h3_subsections)

        if len(h4_counts) < 3:
            return {
                "cv": 0.0,
                "score": 6.0,
                "assessment": "INSUFFICIENT_DATA",
                "h4_counts": h4_counts,
                "uniform_count": 0,
                "h3_count": len(h4_counts),
            }

        # Calculate coefficient of variation
        mean_count = statistics.mean(h4_counts)
        stddev = statistics.stdev(h4_counts) if len(h4_counts) > 1 else 0.0
        cv = stddev / mean_count if mean_count > 0 else 0.0

        # Special case: If no H4s exist at all (all counts are 0), this is not a pattern issue
        # It's just a document structure choice - return INSUFFICIENT_DATA
        if all(count == 0 for count in h4_counts):
            return {
                "cv": 0.0,
                "score": 6.0,  # Neutral score (50% of max)
                "assessment": "INSUFFICIENT_DATA",
                "h4_counts": h4_counts,
                "uniform_count": 0,
                "h3_count": len(h4_counts),
            }

        # Count uniform sections (2-3 H4s per H3, AI signature)
        uniform_count = sum(1 for c in h4_counts if 2 <= c <= 3)

        # Scoring (6 points max - H4 less weighted than H3)
        # Research shows H4 should be weighted ~0.15-0.20 vs H3's 0.35-0.50
        if cv >= 0.45:
            score, assessment = 6.0, "EXCELLENT"
        elif cv >= 0.30:
            score, assessment = 4.0, "GOOD"
        elif cv >= 0.15:
            score, assessment = 2.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "h4_counts": h4_counts,
            "cv": round(cv, 3),
            "score": score,
            "assessment": assessment,
            "uniform_count": uniform_count,
            "h3_count": len(h4_counts),
        }

    def _calculate_heading_depth_variance(self, text: str) -> Dict:
        """
        Analyze heading depth transition patterns (Heading depth variance analysis).

        AI Pattern: Rigid H1→H2→H3 sequential only
        Human Pattern: Varied transitions with lateral moves and jumps

        Returns:
            {
                'transitions': Dict[str, int],
                'pattern': str ('VARIED', 'SEQUENTIAL', 'RIGID'),
                'score': float (0-6),
                'assessment': str,
                'max_depth': int
            }
        """
        matches = self._heading_pattern.findall(text)

        if len(matches) < 5:
            return {
                "score": 6.0,
                "assessment": "INSUFFICIENT_DATA",
                "pattern": "UNKNOWN",
                "transitions": {},
                "max_depth": 0,
                "has_lateral": False,
                "has_jumps": False,
            }

        levels = [len(m[0]) for m in matches]
        max_depth = max(levels)

        # Track transitions
        transitions: Dict[str, int] = {}
        for i in range(len(levels) - 1):
            transition = f"H{levels[i]}→H{levels[i+1]}"
            transitions[transition] = transitions.get(transition, 0) + 1

        # Analyze pattern
        has_lateral = any(f"H{level}→H{level}" in transitions for level in range(1, 7))
        has_jumps = any(
            f"H{level}→H{j}" in transitions for level in range(2, 7) for j in range(1, level - 1)
        )
        only_sequential = len(transitions) <= 4 and not has_lateral and not has_jumps

        # Scoring (6 points max)
        if has_lateral and has_jumps:
            pattern, score, assessment = "VARIED", 6.0, "EXCELLENT"
        elif has_lateral or has_jumps or max_depth <= 3:
            pattern, score, assessment = "SEQUENTIAL", 4.0, "GOOD"
        elif only_sequential and max_depth >= 4:
            pattern, score, assessment = "RIGID", 2.0, "FAIR"
        else:
            pattern, score, assessment = "RIGID", 0.0, "POOR"

        return {
            "transitions": transitions,
            "pattern": pattern,
            "score": score,
            "assessment": assessment,
            "max_depth": max_depth,
            "has_lateral": has_lateral,
            "has_jumps": has_jumps,
        }

    def _analyze_code_blocks(self, text: str) -> Dict:
        """
        Analyze code block patterns in technical writing.
        AI generates complete code with consistent language specs; humans use snippets.
        """
        # Find code blocks (markdown triple backticks)
        code_blocks = re.findall(r"```(\w+)?\s*\n(.*?)\n```", text, re.DOTALL)
        total_blocks = len(code_blocks)

        # Count blocks with language specification
        blocks_with_lang = sum(1 for lang, _ in code_blocks if lang)

        # Language consistency (AI = 1.0, always specifies)
        lang_consistency = blocks_with_lang / total_blocks if total_blocks > 0 else 0.0

        # Comment density in code blocks
        comment_densities = []
        for _lang, code in code_blocks:
            lines = code.strip().split("\n")
            if len(lines) == 0:
                continue

            # Count comment lines (simple heuristics for common languages)
            comment_lines = 0
            for line in lines:
                stripped = line.strip()
                if (
                    stripped.startswith("//")
                    or stripped.startswith("#")
                    or stripped.startswith("/*")
                ):
                    comment_lines += 1

            density = comment_lines / len(lines) if len(lines) > 0 else 0
            comment_densities.append(density)

        avg_comment_density = statistics.mean(comment_densities) if comment_densities else 0.0

        return {
            "code_blocks": total_blocks,
            "code_with_lang": blocks_with_lang,
            "code_lang_consistency": round(lang_consistency, 3),
            "code_comment_density": round(avg_comment_density, 3),
        }

    def _analyze_heading_hierarchy_enhanced(self, text: str) -> Dict:
        """
        Enhanced heading hierarchy analysis.
        AI never skips levels (strict H1→H2→H3); humans occasionally do.
        """
        # Extract all headings with levels
        headings = []
        for line in text.split("\n"):
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((level, title))

        if len(headings) < 2:
            return {
                "hierarchy_skips": 0,
                "hierarchy_adherence": 1.0,  # Perfect adherence (trivial)
                "heading_length_variance": 0.0,
            }

        # Check for hierarchy skips (e.g., H1 directly to H3)
        skips = 0
        for i in range(len(headings) - 1):
            curr_level, _ = headings[i]
            next_level, _ = headings[i + 1]

            # Skip detected if level jumps by more than 1 downward
            if next_level > curr_level + 1:
                skips += 1

        # Strict adherence score (1.0 = never skips = AI-like)
        adherence = 1.0 - (skips / len(headings)) if len(headings) > 0 else 1.0

        # Heading length variance (AI tends toward uniform verbose headings)
        heading_lengths = [len(title.split()) for _, title in headings]
        if len(heading_lengths) > 1:
            length_variance = statistics.variance(heading_lengths)
        else:
            length_variance = 0.0

        return {
            "hierarchy_skips": skips,
            "hierarchy_adherence": round(adherence, 3),
            "heading_length_variance": round(length_variance, 2),
        }

    def _analyze_blockquote_patterns(self, text: str, word_count: int) -> Dict:
        """
        Analyze blockquote usage patterns via AST.
        AI uses 2.7x more blockquotes than humans, often clustered at section starts.

        Returns dict with keys: total_blockquotes, per_page, avg_length,
        section_start_clustering, score, assessment
        """
        ast = self._parse_to_ast(text, cache_key="blockquote")
        if ast is None:
            # Fallback: basic count without AST
            bq_count = len(re.findall(r"^>\s+", text, re.MULTILINE))
            pages = word_count / 250.0
            per_page = bq_count / pages if pages > 0 else 0
            if per_page <= 2:
                return {
                    "total_blockquotes": bq_count,
                    "per_page": per_page,
                    "score": 10.0,
                    "assessment": "EXCELLENT",
                }
            elif per_page <= 3:
                return {
                    "total_blockquotes": bq_count,
                    "per_page": per_page,
                    "score": 7.0,
                    "assessment": "GOOD",
                }
            elif per_page <= 4:
                return {
                    "total_blockquotes": bq_count,
                    "per_page": per_page,
                    "score": 4.0,
                    "assessment": "FAIR",
                }
            else:
                return {
                    "total_blockquotes": bq_count,
                    "per_page": per_page,
                    "score": 0.0,
                    "assessment": "POOR",
                }

        # Extract blockquotes via AST
        blockquotes = self._walk_ast(ast, Quote)

        if len(blockquotes) == 0:
            return {
                "total_blockquotes": 0,
                "per_page": 0.0,
                "score": 10.0,
                "assessment": "EXCELLENT",
                "section_start_clustering": 0.0,
            }

        # Calculate metrics
        pages = word_count / 250.0
        per_page = len(blockquotes) / pages if pages > 0 else 0

        # Calculate blockquote lengths
        lengths = []
        for bq in blockquotes:
            bq_text = self._extract_text_from_node(bq)
            lengths.append(len(bq_text.split()))

        avg_length = statistics.mean(lengths) if lengths else 0

        # Detect section-start clustering
        section_start_count = self._count_section_start_blockquotes(ast)
        section_start_clustering = (
            section_start_count / len(blockquotes) if len(blockquotes) > 0 else 0
        )

        # Scoring based on density and clustering
        if per_page <= 2 and section_start_clustering < 0.3:
            score, assessment = 10.0, "EXCELLENT"
        elif per_page <= 3 and section_start_clustering < 0.5:
            score, assessment = 7.0, "GOOD"
        elif per_page <= 4:
            score, assessment = 4.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "total_blockquotes": len(blockquotes),
            "per_page": round(per_page, 2),
            "avg_length": round(avg_length, 1),
            "lengths": lengths[:10],  # Limit for storage
            "section_start_clustering": round(section_start_clustering, 3),
            "section_start_count": section_start_count,
            "score": score,
            "assessment": assessment,
        }

    def _count_section_start_blockquotes(self, ast) -> int:
        """Count blockquotes appearing within first 100 words of H2 sections."""
        count = 0
        current_section_words = 0
        in_h2_section = False

        # Walk all nodes in order
        for node in self._walk_ast(ast):
            if isinstance(node, Heading) and node.level == 2:
                in_h2_section = True
                current_section_words = 0
            elif isinstance(node, Quote):
                if in_h2_section and current_section_words < 100:
                    count += 1
                in_h2_section = False  # Reset after finding blockquote
            elif isinstance(node, Paragraph):
                text = self._extract_text_from_node(node)
                current_section_words += len(text.split())
                if current_section_words >= 100:
                    in_h2_section = False

        return count

    def _analyze_link_anchor_quality(self, text: str, word_count: int) -> Dict:
        """
        Analyze link anchor text quality.
        AI defaults to generic CTAs, humans write descriptive anchors.

        Returns dict with keys: total_links, generic_count, generic_ratio,
        generic_examples, link_density, score, assessment
        """
        ast = self._parse_to_ast(text, cache_key="links")
        if ast is None:
            # Fallback to regex
            return self._analyze_link_anchor_quality_regex(text, word_count)

        # Extract links via AST
        links = self._walk_ast(ast, Link)

        if len(links) == 0:
            return {"total_links": 0, "score": 8.0, "assessment": "EXCELLENT"}

        # Analyze anchor text
        generic_patterns = [
            r"\bclick here\b",
            r"\bread more\b",
            r"\blearn more\b",
            r"\bsee here\b",
            r"\bcheck (this|it) out\b",
            r"\b(this|that) link\b",
            r"^here$",
            r"^this$",
            r"^link$",
            r"https?://",
        ]

        generic_links: List[Any] = []
        generic_examples: List[str] = []

        for link in links:
            anchor_text = self._extract_text_from_node(link).strip()
            if not anchor_text:
                continue

            # Check against generic patterns
            is_generic = any(
                re.search(pattern, anchor_text, re.IGNORECASE) for pattern in generic_patterns
            )

            if is_generic:
                generic_links.append(link)
                if len(generic_examples) < 10:
                    generic_examples.append(f'"{anchor_text}"')

        generic_ratio = len(generic_links) / len(links) if len(links) > 0 else 0
        link_density = (len(links) / word_count * 1000) if word_count > 0 else 0

        # Scoring
        if generic_ratio < 0.10:
            score, assessment = 8.0, "EXCELLENT"
        elif generic_ratio < 0.25:
            score, assessment = 6.0, "GOOD"
        elif generic_ratio < 0.50:
            score, assessment = 3.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "total_links": len(links),
            "generic_count": len(generic_links),
            "generic_ratio": round(generic_ratio, 3),
            "generic_examples": generic_examples,
            "link_density": round(link_density, 2),
            "score": score,
            "assessment": assessment,
        }

    def _analyze_link_anchor_quality_regex(self, text: str, word_count: int) -> Dict:
        """Fallback regex-based link anchor analysis when AST unavailable."""
        # Extract markdown links: [anchor](url)
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        matches = re.findall(link_pattern, text)

        if len(matches) == 0:
            return {"total_links": 0, "score": 8.0, "assessment": "EXCELLENT"}

        generic_patterns = [
            r"\bclick here\b",
            r"\bread more\b",
            r"\blearn more\b",
            r"\bsee here\b",
            r"\bcheck (this|it) out\b",
            r"\b(this|that) link\b",
            r"^here$",
            r"^this$",
            r"^link$",
            r"https?://",
        ]

        generic_count = 0
        generic_examples: List[str] = []

        for anchor, _url in matches:
            is_generic = any(
                re.search(pattern, anchor, re.IGNORECASE) for pattern in generic_patterns
            )
            if is_generic:
                generic_count += 1
                if len(generic_examples) < 10:
                    generic_examples.append(f'"{anchor}"')

        generic_ratio = generic_count / len(matches)
        link_density = (len(matches) / word_count * 1000) if word_count > 0 else 0

        if generic_ratio < 0.10:
            score, assessment = 8.0, "EXCELLENT"
        elif generic_ratio < 0.25:
            score, assessment = 6.0, "GOOD"
        elif generic_ratio < 0.50:
            score, assessment = 3.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "total_links": len(matches),
            "generic_count": generic_count,
            "generic_ratio": round(generic_ratio, 3),
            "generic_examples": generic_examples,
            "link_density": round(link_density, 2),
            "score": score,
            "assessment": assessment,
        }

    def _analyze_enhanced_list_structure_ast(self, text: str) -> Dict:
        """
        Analyze list structure patterns via AST.
        AI creates symmetric lists, humans create asymmetric varied structures.

        Returns dict with keys: has_mixed_types, symmetry_score, avg_item_length,
        item_length_cv, score, assessment
        """
        ast = self._parse_to_ast(text, cache_key="lists")
        if ast is None:
            # Fallback: assume good if AST unavailable
            return {"score": 8.0, "assessment": "AST_UNAVAILABLE"}

        lists = self._walk_ast(ast, MarkoList)

        if len(lists) == 0:
            return {"score": 8.0, "assessment": "NO_LISTS"}

        # Check for mixed ordered/unordered
        ordered_count = sum(1 for lst in lists if lst.ordered)
        unordered_count = len(lists) - ordered_count
        has_mixed_types = ordered_count > 0 and unordered_count > 0

        # Analyze sublist counts for symmetry
        sublist_counts = []
        for lst in lists:
            if hasattr(lst, "children") and lst.children:
                child_lists = [child for child in lst.children if isinstance(child, MarkoList)]
                sublist_counts.append(len(child_lists))

        # Calculate symmetry (low CV = high symmetry = AI-like)
        if len(sublist_counts) >= 3:
            mean_sublists = statistics.mean(sublist_counts)
            if mean_sublists > 0:
                symmetry_cv = statistics.stdev(sublist_counts) / mean_sublists
                symmetry_score = 1.0 - min(symmetry_cv, 1.0)  # 1.0 = perfect symmetry
            else:
                symmetry_score = 0.0
        else:
            symmetry_score = 0.0  # Assume good if insufficient data

        # Analyze item lengths
        item_lengths = []
        for lst in lists:
            if hasattr(lst, "children") and lst.children:
                for item in lst.children:
                    if not isinstance(item, MarkoList):  # Skip nested lists
                        text_content = self._extract_text_from_node(item)
                        item_lengths.append(len(text_content.split()))

        avg_item_length = statistics.mean(item_lengths) if item_lengths else 0
        item_length_cv = (
            statistics.stdev(item_lengths) / avg_item_length
            if avg_item_length > 0 and len(item_lengths) > 1
            else 0
        )

        # Scoring
        if has_mixed_types and symmetry_score < 0.2 and item_length_cv > 0.4:
            score, assessment = 8.0, "EXCELLENT"
        elif has_mixed_types or symmetry_score < 0.4:
            score, assessment = 5.0, "GOOD"
        elif symmetry_score < 0.7:
            score, assessment = 3.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "has_mixed_types": has_mixed_types,
            "symmetry_score": round(symmetry_score, 3),
            "avg_item_length": round(avg_item_length, 1),
            "item_length_cv": round(item_length_cv, 3),
            "ordered_count": ordered_count,
            "unordered_count": unordered_count,
            "score": score,
            "assessment": assessment,
        }

    def _analyze_code_block_patterns_ast(self, text: str) -> Dict:
        """
        Analyze code block patterns via AST.
        AI often omits language declarations, uses uniform lengths.

        Returns dict with keys: total_blocks, with_language,
        language_declaration_ratio, avg_length, length_cv, score, assessment
        """
        ast = self._parse_to_ast(text, cache_key="code")
        if ast is None:
            # Fallback to regex
            return self._analyze_code_block_patterns_regex(text)

        code_blocks = self._walk_ast(ast, FencedCode)

        if len(code_blocks) == 0:
            return {
                "total_blocks": 0,
                "with_language": 0,
                "language_declaration_ratio": 0.0,
                "avg_length": 0.0,
                "length_cv": 0.0,
                "score": 4.0,
                "assessment": "NO_CODE_BLOCKS",
            }

        # Count language declarations
        with_language = sum(1 for block in code_blocks if hasattr(block, "lang") and block.lang)
        language_ratio = with_language / len(code_blocks)

        # Calculate lengths
        lengths = []
        for block in code_blocks:
            if hasattr(block, "children") and isinstance(block.children, str):
                lines = block.children.strip().split("\n")
                lengths.append(len(lines))
            elif hasattr(block, "children") and block.children:
                # Extract text from children
                code_text = self._extract_text_from_node(block)
                lines = code_text.strip().split("\n")
                lengths.append(len(lines))

        avg_length = statistics.mean(lengths) if lengths else 0
        length_cv = (
            statistics.stdev(lengths) / avg_length if avg_length > 0 and len(lengths) > 1 else 0
        )

        # Scoring
        if language_ratio >= 0.9 and length_cv > 0.4:
            score, assessment = 4.0, "EXCELLENT"
        elif language_ratio >= 0.7:
            score, assessment = 3.0, "GOOD"
        elif language_ratio >= 0.5:
            score, assessment = 2.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "total_blocks": len(code_blocks),
            "with_language": with_language,
            "language_declaration_ratio": round(language_ratio, 3),
            "avg_length": round(avg_length, 1),
            "length_cv": round(length_cv, 3),
            "score": score,
            "assessment": assessment,
        }

    def _analyze_code_block_patterns_regex(self, text: str) -> Dict:
        """Fallback regex-based code block analysis when AST unavailable."""
        # Match fenced code blocks with optional language
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        if len(matches) == 0:
            return {
                "total_blocks": 0,
                "with_language": 0,
                "language_declaration_ratio": 0.0,
                "avg_length": 0.0,
                "length_cv": 0.0,
                "score": 4.0,
                "assessment": "NO_CODE_BLOCKS",
            }

        with_language = sum(1 for lang, _ in matches if lang)
        language_ratio = with_language / len(matches)

        lengths = [len(code.strip().split("\n")) for _, code in matches]
        avg_length = statistics.mean(lengths) if lengths else 0
        length_cv = (
            statistics.stdev(lengths) / avg_length if avg_length > 0 and len(lengths) > 1 else 0
        )

        if language_ratio >= 0.9 and length_cv > 0.4:
            score, assessment = 4.0, "EXCELLENT"
        elif language_ratio >= 0.7:
            score, assessment = 3.0, "GOOD"
        elif language_ratio >= 0.5:
            score, assessment = 2.0, "FAIR"
        else:
            score, assessment = 0.0, "POOR"

        return {
            "total_blocks": len(matches),
            "with_language": with_language,
            "language_declaration_ratio": round(language_ratio, 3),
            "avg_length": round(avg_length, 1),
            "length_cv": round(length_cv, 3),
            "score": score,
            "assessment": assessment,
        }


# Backward compatibility alias
StructureAnalyzer = StructureDimension

# Module-level singleton - triggers self-registration on module import
_instance = StructureDimension()
