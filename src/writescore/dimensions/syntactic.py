"""
Syntactic dimension analyzer.

Analyzes syntactic complexity and patterns:
- Dependency tree depth (AI: 2-3, Human: 4-6)
- Subordination index (AI: <0.1, Human: >0.15)
- Passive voice constructions
- POS diversity
- Syntactic repetition (structural patterns)

Requires optional dependency: spaCy

Research: +10% accuracy improvement with enhanced syntactic features

Refactored in Story 1.4 to use DimensionStrategy pattern with self-registration.
"""

import re
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.results import SyntacticIssue
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils import load_spacy_model

nlp_spacy = load_spacy_model("en_core_web_sm")


class SyntacticDimension(DimensionStrategy):
    """
    Analyzes syntactic dimension - sentence structure complexity.

    Weight: 2.0% of total score
    Tier: ADVANCED

    Detects:
    - Low syntactic complexity (AI signature)
    - Mechanical sentence structure repetition
    - Shallow dependency trees
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
        return "syntactic"

    @property
    def weight(self) -> float:
        """Return dimension weight (2.0% of total score)."""
        return 2.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes syntactic complexity, dependency depth, and structural patterns"

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
        Analyze syntactic patterns with configurable modes.

        Modes:
        - FAST: Analyze first 100k chars (current behavior)
        - ADAPTIVE: Sample for >100k chars (5-7 sections)
        - SAMPLING: User-configured sampling
        - FULL: Analyze entire document (slow for very long docs)

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = ADAPTIVE)
            **kwargs: Additional parameters

        Returns:
            Dict with syntactic analysis results + metadata:
            - syntactic_repetition_score: Structural repetition (0-1)
            - pos_diversity: POS tag diversity (0-1)
            - avg_dependency_depth: Avg tree depth (AI: 2-3, Human: 4-6)
            - subordination_index: Subordinate clauses ratio
            - passive_constructions: Count of passive voice
            - morphological_richness: Unique lemma count
            - available: Whether analysis succeeded
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
                syntactic_metrics = self._analyze_syntactic_patterns(sample_text)
                sample_results.append(syntactic_metrics)

            # Aggregate metrics from all samples
            aggregated = self._aggregate_syntactic_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            syntactic_metrics = self._analyze_syntactic_patterns(analyzed_text)
            aggregated = syntactic_metrics
            analyzed_length = len(analyzed_text)
            samples_analyzed = 1

        # Add consistent metadata
        return {
            "syntactic": aggregated,
            **aggregated,  # Flatten for backward compatibility
            "available": True,
            "analysis_mode": config.mode.value,
            "samples_analyzed": samples_analyzed,
            "total_text_length": total_text_length,
            "analyzed_text_length": analyzed_length,
            "coverage_percentage": (analyzed_length / total_text_length * 100.0)
            if total_text_length > 0
            else 0.0,
        }

    def analyze_detailed(self, lines: List[str], html_comment_checker=None) -> List[SyntacticIssue]:
        """
        Detailed analysis with line numbers and suggestions.

        Args:
            lines: Text split into lines
            html_comment_checker: Function to check if line is in HTML comment

        Returns:
            List of SyntacticIssue objects
        """
        return self._analyze_syntactic_issues_detailed(lines, html_comment_checker)

    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate syntactic score.

        Args:
            analysis_results: Results dict with syntactic metrics

        Returns:
            Tuple of (score_value, score_label)
        """
        if not analysis_results.get("syntactic"):
            return (5.0, "UNKNOWN")

        repetition = analysis_results.get("syntactic_repetition_score", 0.5)

        # Lower repetition = more varied (better)
        if repetition <= 0.3:
            return (10.0, "HIGH")  # Varied structures
        elif repetition <= 0.5:
            return (7.0, "MEDIUM")
        elif repetition <= 0.7:
            return (4.0, "LOW")
        else:
            return (2.0, "VERY LOW")  # Mechanical repetition (AI-like)

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on syntactic repetition using monotonic scoring.

        Research basis (2024 literature review):
        - Human text: ~38% syntactic template repetition rate
        - AI text: ~95% syntactic template repetition rate
        - Source: ComplexDiscovery analysis of POS tag sequences

        Scoring approach:
        - Monotonic: Lower repetition = higher score (more human-like)
        - threshold_low=0.30: Good human baseline (25th percentile)
        - threshold_high=0.70: AI-like territory (75th percentile)

        Lower repetition = more varied syntax = higher score (human-like).
        Higher repetition = mechanical patterns = lower score (AI-like).

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        syntactic = metrics.get("syntactic")
        if not syntactic or not syntactic.get("available", True):
            return 50.0  # Neutral score for missing/unavailable data

        repetition = syntactic.get("syntactic_repetition_score", 0.5)

        # Monotonic scoring: lower repetition = higher score (more human-like)
        # Research shows AI has ~95% template rate vs ~38% for humans
        score = self._monotonic_score(
            value=repetition,
            threshold_low=0.30,  # Good human baseline
            threshold_high=0.70,  # AI-like territory
            increasing=False,  # Lower is better
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

        syntactic = metrics.get("syntactic", {})
        repetition = syntactic.get("syntactic_repetition_score", 0.5)
        avg_depth = syntactic.get("avg_dependency_depth", 0)
        subordination = syntactic.get("subordination_index", 0)

        if repetition > 0.5:
            recommendations.append(
                f"Reduce syntactic repetition (score={repetition:.2f}, target ≤0.3). "
                f"Vary sentence structures: use different clause orderings, mix simple/complex/compound sentences."
            )

        if avg_depth < 3:
            recommendations.append(
                f"Increase sentence complexity (depth={avg_depth:.1f}, target ≥4). "
                f"Use subordinate clauses, relative clauses, and embedded structures."
            )

        if subordination < 0.15:
            recommendations.append(
                f"Add more subordination (index={subordination:.2f}, target ≥0.15). "
                f"Use 'because', 'although', 'while', 'when' to create complex relationships."
            )

        if repetition > 0.7:
            recommendations.append(
                "Very high structural repetition detected (strong AI signal). "
                "This suggests mechanical sentence generation. Thoroughly rewrite with varied syntax."
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

    def _analyze_syntactic_patterns(self, text: str) -> Dict:
        """
        Enhanced syntactic analysis using spaCy.

        NOTE: This method no longer truncates text - truncation/sampling
        is handled by caller via _prepare_text().

        Metrics:
        - Dependency tree depth (AI: 2-3, Human: 4-6)
        - Subordination index (AI: <0.1, Human: >0.15)
        - Passive constructions (AI tends to overuse)
        - Morphological richness (unique lemmas)

        Args:
            text: Text to analyze (pre-truncated/sampled by caller)

        Returns:
            Dict with syntactic metrics
        """
        try:
            # Remove code blocks
            text = re.sub(r"```[\s\S]*?```", "", text)

            # Process with spaCy (now processes full text, pre-truncated/sampled by caller)
            doc = nlp_spacy(text)

            # Extract sentence structures (POS patterns)
            sentence_structures = []
            pos_tags = []
            dependency_depths = []
            subordinate_clauses = 0
            total_clauses = 0
            passive_constructions = 0
            lemmas = set()

            for sent in doc.sents:
                # Get POS pattern
                pos_pattern = " ".join([token.pos_ for token in sent])
                sentence_structures.append(pos_pattern)

                # Collect POS tags
                pos_tags.extend([token.pos_ for token in sent])

                # Calculate dependency depth
                max_depth = 0
                for token in sent:
                    depth = len(list(token.ancestors))
                    max_depth = max(max_depth, depth)

                    # Count subordinate clauses (advcl, ccomp, xcomp, acl, relcl)
                    if token.dep_ in ["advcl", "ccomp", "xcomp", "acl", "relcl"]:
                        subordinate_clauses += 1

                    # Count passive constructions (nsubjpass or auxpass dependencies)
                    if token.dep_ in ["nsubjpass", "auxpass"]:
                        passive_constructions += 1

                    # Collect unique lemmas for morphological richness
                    if token.is_alpha and len(token.text) > 2:
                        lemmas.add(token.lemma_.lower())

                dependency_depths.append(max_depth)
                total_clauses += 1

            if not sentence_structures:
                return {"available": False}

            # Calculate syntactic repetition (how many unique patterns)
            unique_structures = len(set(sentence_structures))
            total_structures = len(sentence_structures)
            repetition_score = (
                1 - (unique_structures / total_structures) if total_structures > 0 else 0
            )

            # Calculate POS diversity
            unique_pos = len(set(pos_tags))
            total_pos = len(pos_tags)
            pos_diversity = unique_pos / total_pos if total_pos > 0 else 0

            # Average dependency depth (complexity)
            # AI: 2-3, Human: 4-6
            avg_depth = statistics.mean(dependency_depths) if dependency_depths else 0

            # Subordination index (subordinate clauses per clause)
            # AI: <0.1, Human: >0.15
            subordination_index = subordinate_clauses / total_clauses if total_clauses > 0 else 0

            # Morphological richness (unique lemmas)
            morphological_richness = len(lemmas)

            return {
                "available": True,
                "syntactic_repetition_score": round(repetition_score, 3),
                "pos_diversity": round(pos_diversity, 3),
                "avg_dependency_depth": round(avg_depth, 2),
                "avg_tree_depth": round(avg_depth, 2),  # Alias for new field name
                "subordination_index": round(subordination_index, 3),
                "passive_constructions": passive_constructions,
                "morphological_richness": morphological_richness,
            }
        except Exception as e:
            print(f"Warning: Syntactic analysis failed: {e}", file=sys.stderr)
            return {"available": False}

    def _aggregate_syntactic_metrics(self, sample_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate syntactic metrics from multiple samples.

        Strategy:
        - Repetition score, POS diversity, subordination index: Mean across samples
        - Avg dependency depth: Mean across samples (all samples contribute equally)
        - Passive constructions: Sum across samples
        - Morphological richness: Sum of unique lemmas (union, not sum of counts)

        NOTE: For simplicity, we use unweighted means for most metrics.
        Future enhancement: weight by sentence count or text length.

        Args:
            sample_metrics: List of syntactic metric dicts from each sample

        Returns:
            Aggregated syntactic metrics dict
        """
        if not sample_metrics:
            return {"available": False}

        if len(sample_metrics) == 1:
            return sample_metrics[0]

        # Extract values for each metric (handle missing keys gracefully)
        repetition_scores = [m.get("syntactic_repetition_score", 0) for m in sample_metrics]
        pos_diversities = [m.get("pos_diversity", 0) for m in sample_metrics]
        avg_depths = [m.get("avg_dependency_depth", 0) for m in sample_metrics]
        subordination_indices = [m.get("subordination_index", 0) for m in sample_metrics]

        # Counts to sum
        passive_counts = [m.get("passive_constructions", 0) for m in sample_metrics]
        morphological_counts = [m.get("morphological_richness", 0) for m in sample_metrics]

        # Calculate means
        return {
            "available": True,
            "syntactic_repetition_score": round(sum(repetition_scores) / len(repetition_scores), 3),
            "pos_diversity": round(sum(pos_diversities) / len(pos_diversities), 3),
            "avg_dependency_depth": round(sum(avg_depths) / len(avg_depths), 2),
            "avg_tree_depth": round(sum(avg_depths) / len(avg_depths), 2),  # Alias
            "subordination_index": round(
                sum(subordination_indices) / len(subordination_indices), 3
            ),
            "passive_constructions": sum(passive_counts),
            "morphological_richness": sum(
                morphological_counts
            ),  # Sum of unique lemmas from each sample
        }

    def _analyze_syntactic_issues_detailed(
        self, lines: List[str], html_comment_checker=None
    ) -> List[SyntacticIssue]:
        """Detect syntactic complexity issues (passive voice, shallow trees, low subordination)."""
        issues = []

        try:
            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Skip HTML comments (metadata), headings, code blocks, and short lines
                if html_comment_checker and html_comment_checker(line):
                    continue
                if (
                    not stripped
                    or stripped.startswith("#")
                    or stripped.startswith("```")
                    or len(stripped) < 20
                ):
                    continue

                # Parse sentences on this line
                doc = nlp_spacy(stripped)

                for sent in doc.sents:
                    sent_text = sent.text.strip()
                    if len(sent_text) < 10:
                        continue

                    # Check for passive constructions
                    has_passive = any(token.dep_ in ["nsubjpass", "auxpass"] for token in sent)
                    if has_passive:
                        issues.append(
                            SyntacticIssue(
                                line_number=line_num,
                                sentence=sent_text[:100] + "..."
                                if len(sent_text) > 100
                                else sent_text,
                                issue_type="passive",
                                metric_value=1.0,
                                problem="Passive voice construction (AI tends to overuse)",
                                suggestion="Convert to active voice - identify actor and make them the subject",
                            )
                        )

                    # Check for shallow dependency trees (depth < 3)
                    max_depth = 0
                    for token in sent:
                        depth = 1
                        current = token
                        while current.head != current:
                            depth += 1
                            current = current.head
                        max_depth = max(max_depth, depth)

                    if max_depth < 3 and len(sent) > 10:
                        issues.append(
                            SyntacticIssue(
                                line_number=line_num,
                                sentence=sent_text[:100] + "..."
                                if len(sent_text) > 100
                                else sent_text,
                                issue_type="shallow",
                                metric_value=max_depth,
                                problem=f"Shallow syntax (depth={max_depth}, human avg=4-6)",
                                suggestion="Add subordinate clauses, relative clauses, or prepositional phrases",
                            )
                        )

                    # Check for low subordination (no subordinate clauses)
                    subordinate_count = sum(
                        1
                        for token in sent
                        if token.dep_ in ["advcl", "ccomp", "xcomp", "acl", "relcl"]
                    )
                    if subordinate_count == 0 and len(sent) > 15:
                        issues.append(
                            SyntacticIssue(
                                line_number=line_num,
                                sentence=sent_text[:100] + "..."
                                if len(sent_text) > 100
                                else sent_text,
                                issue_type="subordination",
                                metric_value=0.0,
                                problem="No subordinate clauses (simple construction)",
                                suggestion='Add "because", "while", "although", or "when" clauses for complexity',
                            )
                        )

        except Exception as e:
            print(f"Warning: Syntactic analysis failed: {e}", file=sys.stderr)

        return issues


# Backward compatibility alias
SyntacticAnalyzer = SyntacticDimension

# Module-level singleton - triggers self-registration on module import
_instance = SyntacticDimension()
