"""
Core AIPatternAnalyzer orchestration class.

This is the main analysis engine that coordinates all dimension analyzers,
calculates scores, manages history, and produces final results.

Extracted from monolithic analyze_ai_patterns.py (7,079 lines) as part of
modularization effort (Phase 3).
"""

import json
import re
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Required dependencies
from marko import Markdown

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_loader import DimensionLoader

# Registry-based dimension loading (Story 1.4.11)
from writescore.core.dimension_registry import DimensionRegistry

# Core results
from writescore.core.results import (
    AnalysisResults,
    DetailedAnalysis,
    EmDashInstance,
    HeadingIssue,
    TransitionInstance,
    UniformParagraph,
    VocabInstance,
)
from writescore.history.tracker import ScoreHistory

# Scoring and history
from writescore.scoring.dual_score import (
    DualScore,
)

# Dual score calculator
from writescore.scoring.dual_score_calculator import calculate_dual_score as _calculate_dual_score


class AIPatternAnalyzer:
    """
    Main analyzer class that orchestrates all dimension analyzers.

    This class coordinates the analysis workflow:
    1. Load and preprocess text
    2. Run dimension-specific analyses
    3. Calculate scores across all dimensions
    4. Generate comprehensive results
    5. Track history over time
    """

    # Replacement suggestions for AI vocabulary (for detailed mode)
    AI_VOCAB_REPLACEMENTS = {
        r"\bdelv(e|es|ing)\b": ["explore", "examine", "investigate", "look at", "dig into"],
        r"\brobust(ness)?\b": ["reliable", "powerful", "solid", "effective", "well-designed"],
        r"\bleverag(e|es|ing)\b": ["use", "apply", "take advantage of", "employ", "work with"],
        r"\bharness(es|ing)?\b": ["use", "apply", "employ", "tap into", "utilize"],
        r"\bfacilitat(e|es|ing)\b": ["enable", "help", "make easier", "allow", "support"],
        r"\bunderscore(s|d|ing)?\b": ["emphasize", "highlight", "stress", "point out", "show"],
        r"\bpivotal\b": ["key", "important", "critical", "essential", "crucial"],
        r"\bseamless(ly)?\b": ["smooth", "easy", "straightforward", "effortless", "natural"],
        r"\bholistic(ally)?\b": ["complete", "comprehensive", "full", "thorough", "whole"],
        r"\bcomprehensive(ly)?\b": ["thorough", "complete", "detailed", "full", "extensive"],
        r"\boptimiz(e|es|ing|ation)\b": [
            "improve",
            "enhance",
            "fine-tune",
            "make better",
            "refine",
        ],
        r"\bstreamlin(e|ed|ing)\b": ["simplify", "improve", "make efficient", "refine", "enhance"],
        r"\butiliz(e|es|ation|ing)\b": ["use", "employ", "apply", "work with"],
        r"\bunpack(s|ing)?\b": ["explain", "explore", "break down", "examine", "analyze"],
        r"\bmyriad\b": ["many", "countless", "numerous", "various", "multiple"],
        r"\bplethora\b": ["many", "abundance", "wealth", "plenty", "lots"],
        r"\bparamount\b": ["critical", "essential", "crucial", "vital", "key"],
        r"\bquintessential\b": ["typical", "classic", "perfect example", "ideal", "archetypal"],
        r"\binnovative\b": ["new", "creative", "novel", "original", "fresh"],
        r"\bcutting-edge\b": ["advanced", "modern", "latest", "state-of-the-art", "new"],
        r"\brevolutionary\b": [
            "groundbreaking",
            "major",
            "significant",
            "transformative",
            "game-changing",
        ],
        r"\bgame-changing\b": ["significant", "major", "important", "transformative", "impactful"],
        r"\btransformative\b": ["significant", "major", "powerful", "game-changing", "impactful"],
        r"\bdive deep\b": [
            "explore thoroughly",
            "examine closely",
            "investigate",
            "look closely at",
            "study",
        ],
        r"\bdeep dive\b": [
            "thorough look",
            "detailed examination",
            "close look",
            "in-depth analysis",
            "careful study",
        ],
        r"\becosystem\b": ["environment", "system", "network", "platform", "framework"],
        r"\blandscape\b": ["field", "area", "space", "domain", "world"],
        r"\bparadigm\s+shift\b": [
            "major change",
            "fundamental shift",
            "big change",
            "transformation",
            "sea change",
        ],
        r"\bsynerg(y|istic)\b": [
            "cooperation",
            "collaboration",
            "combined effect",
            "teamwork",
            "partnership",
        ],
        r"\bcommence(s|d)?\b": ["start", "begin", "initiate", "launch", "kick off"],
        r"\bendeavor(s)?\b": ["effort", "project", "attempt", "undertaking", "initiative"],
    }

    # Transition replacements (for detailed mode)
    TRANSITION_REPLACEMENTS = {
        "Furthermore,": [
            "Plus,",
            "What's more,",
            "Beyond that,",
            "And here's the thing,",
            "On top of that,",
        ],
        "Moreover,": ["Plus,", "On top of that,", "And,", "What's more,", "Beyond that,"],
        "Additionally,": ["Also,", "Plus,", "And,", "What's more,", "On top of that,"],
        "In addition,": ["Also,", "Plus,", "What's more,", "Beyond that,", "And,"],
        "First and foremost,": [
            "First,",
            "To start,",
            "Most importantly,",
            "Above all,",
            "First off,",
        ],
        "It is important to note that": [
            "Note that",
            "Keep in mind",
            "Remember",
            "Worth noting:",
            "Key point:",
        ],
        "It is worth mentioning that": [
            "Worth noting",
            "Keep in mind",
            "Note that",
            "Also",
            "Interestingly,",
        ],
        "When it comes to": ["For", "With", "Regarding", "As for", "Looking at"],
        "In conclusion,": ["Finally,", "To sum up,", "In short,", "Bottom line:", "To wrap up,"],
        "To summarize,": ["In short,", "Briefly,", "To sum up,", "Bottom line:", "In a nutshell,"],
        "In summary,": ["In short,", "Briefly,", "To recap,", "Bottom line:", "To sum up,"],
        "As mentioned earlier,": [
            "Earlier,",
            "As noted,",
            "Remember,",
            "Recall that",
            "As we saw,",
        ],
        "It should be noted that": [
            "Note that",
            "Keep in mind",
            "Remember",
            "Worth noting:",
            "Important:",
        ],
        "With that said,": ["That said,", "Still,", "Even so,", "But", "However,"],
        "Having said that,": ["That said,", "Still,", "Even so,", "But", "However,"],
    }

    # Domain-specific technical terms (customizable per project)
    DOMAIN_TERMS_DEFAULT = [
        # Example cybersecurity terms - customize for your domain
        r"\bTriton\b",
        r"\bTrisis\b",
        r"\bSIS\b",
        r"\bPLC\b",
        r"\bSCADA\b",
        r"\bDCS\b",
        r"\bICS\b",
        r"\bOT\b",
        r"\bransomware\b",
        r"\bmalware\b",
        r"\bNIST\b",
        r"\bISA\b",
        r"\bIEC\b",
        r"\bMITRE\b",
        r"\bSOC\b",
        r"\bSIEM\b",
        r"\bIDS\b",
        r"\bIPS\b",
    ]

    def __init__(
        self, domain_terms: Optional[List[str]] = None, config: Optional[AnalysisConfig] = None
    ):
        """
        Initialize analyzer with config-driven dimension loading.

        Args:
            domain_terms: Optional technical terms for voice analysis
            config: Optional AnalysisConfig (uses DEFAULT_CONFIG if not provided)
        """
        self.domain_terms = domain_terms or self.DOMAIN_TERMS_DEFAULT
        self.lines: List[str] = []  # Will store line-by-line content for detailed mode
        self.config = config or DEFAULT_CONFIG

        # HTML comment pattern (metadata blocks to ignore)
        self._html_comment_pattern = re.compile(r"<!--.*?-->", re.DOTALL)

        # Phase 3: AST parser and cache (marko)
        self._markdown_parser = None
        self._ast_cache: Dict[str, Any] = {}

        # Story 1.4.11: Config-driven dimension loading via DimensionLoader
        # Register custom profiles from config if provided
        if self.config.custom_profiles:
            for profile_name, dimensions in self.config.custom_profiles.items():
                DimensionLoader.register_custom_profile(profile_name, dimensions)
                print(
                    f"Registered custom profile '{profile_name}' with dimensions: {dimensions}",
                    file=sys.stderr,
                )

        # Load ONLY configured dimensions (lazy, selective loading)
        loader = DimensionLoader()
        load_results = loader.load_from_config(self.config)

        # Validate load results
        if load_results["failed"]:
            failed_str = ", ".join(f"{k}: {v}" for k, v in load_results["failed"].items())
            raise RuntimeError(f"Failed to load dimensions: {failed_str}")

        # Build dimensions dict from ONLY the dimensions loaded in this session
        self.dimensions = {}
        for dim_name in load_results["loaded"]:
            if DimensionRegistry.has(dim_name):
                self.dimensions[dim_name] = DimensionRegistry.get(dim_name)

        # Log what was loaded
        loaded_count = len(load_results["loaded"])
        profile = self.config.dimension_profile
        print(
            f"Loaded {loaded_count} dimensions from profile '{profile}': {load_results['loaded']}",
            file=sys.stderr,
        )

        # Validate expected dimensions loaded
        if loaded_count == 0:
            raise RuntimeError("No dimensions loaded - cannot perform analysis")

    # ========================================================================
    # AST PARSING HELPERS (marko)
    # ========================================================================

    def _get_markdown_parser(self):
        """Lazy load marko parser."""
        if self._markdown_parser is None:
            self._markdown_parser = Markdown()
        return self._markdown_parser

    def _parse_to_ast(self, text: str, cache_key: Optional[str] = None):
        """Parse markdown to AST with caching."""

        if cache_key and cache_key in self._ast_cache:
            return self._ast_cache[cache_key]

        parser = self._get_markdown_parser()
        if parser is None:
            return None

        try:
            ast = parser.parse(text)
            if cache_key:
                self._ast_cache[cache_key] = ast
            return ast
        except Exception as e:
            import warnings

            warnings.warn(
                f"Markdown parsing failed: {e}. Falling back to regex analysis.",
                UserWarning,
                stacklevel=2,
            )
            return None

    def _walk_ast(self, node, node_type=None):
        """Recursively walk AST and collect nodes of specified type."""
        nodes = []

        if node_type is None or isinstance(node, node_type):
            nodes.append(node)

        # Recursively process children
        if hasattr(node, "children") and node.children:
            for child in node.children:
                nodes.extend(self._walk_ast(child, node_type))

        return nodes

    def _extract_text_from_node(self, node) -> str:
        """Extract plain text from AST node recursively."""
        if hasattr(node, "children") and node.children:
            return "".join([self._extract_text_from_node(child) for child in node.children])
        elif hasattr(node, "children") and isinstance(node.children, str):
            return node.children
        elif hasattr(node, "dest"):  # Link destination
            return ""
        elif isinstance(node, str):
            return node
        else:
            return ""

    # ========================================================================
    # PREPROCESSING
    # ========================================================================

    def _strip_html_comments(self, text: str) -> str:
        """Remove HTML comment blocks (metadata) from text for analysis."""
        return self._html_comment_pattern.sub("", text)

    def _is_line_in_html_comment(self, line: str) -> bool:
        """Check if a line is inside or is an HTML comment."""
        # Line contains complete comment
        if "<!--" in line and "-->" in line:
            return True
        # Line is start or middle of comment
        return bool("<!--" in line or "-->" in line)

    # ========================================================================
    # MAIN ANALYSIS METHOD
    # ========================================================================

    def analyze_file(
        self, file_path: str, config: Optional[AnalysisConfig] = None
    ) -> AnalysisResults:
        """
        Analyze a single markdown file for AI patterns.

        This is the main entry point that orchestrates all dimension analyses,
        calculates scores, and produces comprehensive results.

        Args:
            file_path: Path to markdown file to analyze
            config: Analysis configuration (None = current behavior, uses DEFAULT_CONFIG)

        Returns:
            AnalysisResults object with complete analysis

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Story 1.4.6: Infrastructure only - config parameter added, threaded to all dimensions
        config = config or DEFAULT_CONFIG

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            text = f.read()

        # Strip HTML comments (metadata blocks) before analysis
        text = self._strip_html_comments(text)

        # Split into lines for detailed analysis
        lines = text.splitlines()

        # Run all dimension analyses (Story 1.4.11: Registry-based analysis)
        word_count = self._count_words(text)

        # Registry-based dimension analysis loop
        dimension_results = {}
        for dim_name, dim in self.dimensions.items():
            try:
                # Prepare kwargs based on dimension needs
                kwargs: Dict[str, Any] = {"config": config}

                # Dimension-specific kwargs
                if dim_name in ["structure", "formatting"]:
                    kwargs["word_count"] = word_count

                # Execute analysis
                result = dim.analyze(text, lines, **kwargs)
                dimension_results[dim_name] = result

            except Exception as e:
                print(f"Warning: {dim_name} analysis failed: {e}", file=sys.stderr)
                dimension_results[dim_name] = {"available": False, "error": str(e)}

        # Story 1.10.1: Enrich dimension results with tier/weight/score metadata
        dimension_results = self._enrich_dimension_results(dimension_results)

        # Extract dimension results for backward compatibility with result building
        # These may be empty dicts if dimension not loaded
        perplexity_results = dimension_results.get("perplexity", {})
        burstiness_results = dimension_results.get("burstiness", {})
        structure_results = dimension_results.get("structure", {})
        formatting_results = dimension_results.get("formatting", {})
        voice_results = dimension_results.get("voice", {})
        syntactic_results = dimension_results.get("syntactic", {})
        sentiment_results = dimension_results.get("sentiment", {})
        lexical_results = dimension_results.get("lexical", {})

        # New dimensions from Story 1.4.5
        dimension_results.get("predictability", {})
        readability_results = dimension_results.get("readability", {})
        dimension_results.get("advanced_lexical", {})
        dimension_results.get("transition_marker", {})

        # Story 2.1: Figurative language dimension
        figurative_language_results = dimension_results.get("figurative_language", {})

        # Calculate pages (estimate: 750 words per page)
        estimated_pages = max(1, word_count / 750)

        # Build results object
        # Extract values from dimension analysis results
        ai_vocab = perplexity_results.get("ai_vocabulary", {})
        formulaic = perplexity_results.get("formulaic_transitions", {})
        burstiness = burstiness_results.get("sentence_burstiness", {})
        paragraphs = burstiness_results.get("paragraph_variation", {})
        lexical = lexical_results.get("lexical_diversity", {})
        structure = structure_results.get("structure", {})
        headings = structure_results.get("headings", {})
        voice = voice_results.get("voice", {})
        technical = voice_results.get("technical_depth", {})
        formatting = formatting_results.get("formatting", {})
        sentiment = sentiment_results.get("sentiment", {})

        # Story 2.1: Extract figurative language metrics
        # Unwrap the nested 'figurative_language' key (dimension returns {'figurative_language': {...data...}})
        figurative = (
            figurative_language_results.get("figurative_language", {})
            if figurative_language_results
            else {}
        )

        results = AnalysisResults(
            file_path=file_path,
            total_words=word_count,
            total_sentences=burstiness.get("total_sentences", 0),
            total_paragraphs=paragraphs.get("total_paragraphs", 0),
            ai_vocabulary_count=ai_vocab.get("count", 0),
            ai_vocabulary_per_1k=ai_vocab.get("per_1k", 0.0),
            ai_vocabulary_list=ai_vocab.get("words", []),
            formulaic_transitions_count=formulaic.get("count", 0),
            formulaic_transitions_list=formulaic.get("transitions", []),
            sentence_mean_length=burstiness.get("mean", 0.0),
            sentence_stdev=burstiness.get("stdev", 0.0),
            sentence_min=burstiness.get("min", 0),
            sentence_max=burstiness.get("max", 0),
            sentence_range=(burstiness.get("min", 0), burstiness.get("max", 0)),
            short_sentences_count=burstiness.get("short", 0),
            medium_sentences_count=burstiness.get("medium", 0),
            long_sentences_count=burstiness.get("long", 0),
            sentence_lengths=burstiness.get("lengths", []),
            paragraph_mean_words=paragraphs.get("mean", 0.0),
            paragraph_stdev=paragraphs.get("stdev", 0.0),
            paragraph_range=(paragraphs.get("min", 0), paragraphs.get("max", 0)),
            unique_words=lexical.get("unique", 0),
            lexical_diversity=lexical.get("diversity", 0.0),
            bullet_list_lines=structure.get("bullet_lines", 0),
            numbered_list_lines=structure.get("numbered_lines", 0),
            total_headings=headings.get("total", 0),
            heading_depth=headings.get("depth", 0),
            h1_count=headings.get("h1", 0),
            h2_count=headings.get("h2", 0),
            h3_count=headings.get("h3", 0),
            h4_plus_count=headings.get("h4_plus", 0),
            headings_per_page=headings.get("total", 0) / estimated_pages,
            heading_parallelism_score=headings.get("parallelism_score", 0.0),
            verbose_headings_count=headings.get("verbose_count", 0),
            avg_heading_length=headings.get("avg_length", 0.0),
            first_person_count=voice.get("first_person", 0),
            direct_address_count=voice.get("direct_address", 0),
            contraction_count=voice.get("contractions", 0),
            # Sentiment / AI Detection Ensemble
            roberta_sentiment_variance=sentiment.get("variance"),
            roberta_sentiment_mean=sentiment.get("mean"),
            roberta_emotionally_flat=sentiment.get("emotionally_flat"),
            # Readability metrics (Story 1.4.5)
            flesch_reading_ease=readability_results.get("flesch_reading_ease"),
            flesch_kincaid_grade=readability_results.get("flesch_kincaid_grade"),
            gunning_fog=readability_results.get("gunning_fog"),
            smog_index=readability_results.get("smog_index"),
            # Domain terms (from voice analyzer technical_depth)
            domain_terms_count=technical.get("count", 0),
            domain_terms_list=technical.get("terms", []),
            em_dash_count=formatting.get("em_dashes", 0),
            em_dashes_per_page=formatting.get("em_dashes", 0) / estimated_pages,
            bold_markdown_count=formatting.get("bold", 0),
            italic_markdown_count=formatting.get("italics", 0),
            # Story 2.1: Figurative language metrics
            figurative_simile_count=len(figurative.get("similes", [])),
            figurative_metaphor_count=len(figurative.get("metaphors", [])),
            figurative_idiom_count=len(figurative.get("idioms", [])),
            figurative_ai_cliche_count=len(figurative.get("ai_cliches", [])),
            figurative_total_count=figurative.get("total_figurative", 0),
            figurative_frequency_per_1k=figurative.get("frequency_per_1k", 0.0),
            figurative_types_detected=figurative.get("types_detected", 0),
            # Enhanced metrics from dimension analyzers
            # Story 2.0: Removed deprecated stylometric_results, advanced_results parameters
            **self._flatten_optional_metrics(
                syntactic_results,
                lexical_results,
                formatting_results,
                burstiness_results,
                structure_results,
            ),
        )

        # Populate sentiment distribution (only when 3+ idioms detected)
        sentiment_dist = figurative.get("sentiment_distribution", {})
        if sentiment_dist.get("total_with_sentiment", 0) >= 3:
            percentages = sentiment_dist.get("percentages", {})
            results.figurative_sentiment_positive_pct = percentages.get("positive", 0.0)
            results.figurative_sentiment_negative_pct = percentages.get("negative", 0.0)
            results.figurative_sentiment_neutral_pct = percentages.get("neutral", 0.0)
            results.figurative_sentiment_deviation = sentiment_dist.get(
                "deviation_from_optimal", 0.0
            )

        # Story 2.3: Populate semantic coherence metrics
        semantic_coherence = dimension_results.get("semantic_coherence", {})
        semantic_metrics = semantic_coherence.get("metrics", {})
        if semantic_metrics:
            results.semantic_paragraph_cohesion = semantic_metrics.get("paragraph_cohesion")
            results.semantic_topic_consistency = semantic_metrics.get("topic_consistency")
            results.semantic_discourse_flow = semantic_metrics.get("discourse_flow")
            results.semantic_conceptual_depth = semantic_metrics.get("conceptual_depth")

        # Populate semantic coherence evidence
        if semantic_coherence:
            results.semantic_low_cohesion_paragraphs = semantic_coherence.get(
                "low_cohesion_paragraphs", []
            )
            results.semantic_topic_shifts = semantic_coherence.get("topic_shifts", [])
            results.semantic_weak_transitions = semantic_coherence.get("weak_transitions", [])

        # Story 1.4.11: Registry-based dimension scoring
        # Story 2.3: v5.2.0 has 14 dimensions (added semantic_coherence)
        # Initialize all known score fields to UNKNOWN (for dimensions not loaded)
        all_dimensions = [
            "perplexity",
            "burstiness",
            "structure",
            "formatting",
            "voice",
            "readability",
            "lexical",
            "sentiment",
            "syntactic",
            "predictability",
            "advanced_lexical",
            "transition_marker",
            "figurative_language",
            "semantic_coherence",
        ]
        for dim_name in all_dimensions:
            score_field = f"{dim_name}_score"
            setattr(results, score_field, "UNKNOWN")

        # Calculate scores for all loaded dimensions dynamically
        for dim_name, dim in self.dimensions.items():
            dim_result = dimension_results.get(dim_name, {})

            # Skip if dimension analysis failed or unavailable
            if not dim_result or not dim_result.get("available", True):
                score_field = f"{dim_name}_score"
                setattr(results, score_field, "UNKNOWN")
                continue

            try:
                # Prepare metrics for calculate_score()
                # Each dimension expects different metric structure
                if dim_name == "burstiness":
                    metrics = dim_result.get("sentence_burstiness", {})
                elif dim_name == "voice":
                    # Voice expects full dim_result with 'voice' key
                    # The voice dict already contains total_words from analyze()
                    metrics = dim_result
                else:
                    metrics = dim_result

                # Calculate score using dimension's calculate_score method
                raw_score = dim.calculate_score(metrics)

                # Convert to category
                category = self._convert_score_to_category(raw_score)

                # Set score field dynamically
                score_field = f"{dim_name}_score"
                setattr(results, score_field, category)

            except Exception as e:
                print(f"Warning: Failed to score {dim_name}: {e}", file=sys.stderr)
                score_field = f"{dim_name}_score"
                setattr(results, score_field, "UNKNOWN")

        # Special handling for legacy field names
        # ai_detection_score is from sentiment dimension
        if "sentiment" in self.dimensions and hasattr(results, "sentiment_score"):
            results.ai_detection_score = results.sentiment_score

        # Technical score (TODO: implement domain term detection in voice dimension)
        if not hasattr(results, "technical_score"):
            results.technical_score = "MEDIUM"

        # Overall assessment
        results.overall_assessment = self._assess_overall(results)

        # Store dimension results for dynamic reporting (Story 1.10)
        results.dimension_results = dimension_results
        results.dimension_count = len(dimension_results)  # Number of dimensions analyzed

        return results

    def analyze_text(self, text: str, config: Optional[AnalysisConfig] = None) -> AnalysisResults:
        """
        Analyze text directly for AI patterns (without file I/O).

        This method provides the same analysis as analyze_file but operates on
        text strings directly. Useful for testing and integration scenarios.

        Args:
            text: Text content to analyze
            config: Analysis configuration (None = current behavior, uses DEFAULT_CONFIG)

        Returns:
            AnalysisResults object with complete analysis
        """
        import tempfile
        from pathlib import Path

        # Create a temporary file and delegate to analyze_file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            temp_file = f.name

        try:
            results = self.analyze_file(temp_file, config=config)
            return results
        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)

    def _enrich_dimension_results(self, dimension_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich raw dimension outputs with tier/weight/score metadata.

        Transforms raw dimension analysis outputs into enriched structure expected
        by DynamicReporter, adding tier classification, weights, scores, and
        tier mapping thresholds while preserving all original raw outputs.

        Args:
            dimension_results: Raw dimension analysis outputs from analyze loop
                Example input:
                {
                    'perplexity': {
                        'ai_vocabulary': {'count': 5, 'percentage': 2.1},
                        'formulaic_transitions': {'count': 3}
                    },
                    'burstiness': {
                        'sentence_burstiness': {'cv': 0.15, 'score': 45.0}
                    }
                }

        Returns:
            Enriched dimension_results with added metadata:
            {
                'perplexity': {
                    'tier': 'CORE',
                    'score': 80.0,
                    'weight': 0.20,
                    'tier_mapping': {'low': [0, 40], 'medium': [40, 70], 'high': [70, 100]},
                    # Original raw outputs preserved:
                    'ai_vocabulary': {'count': 5, 'percentage': 2.1},
                    'formulaic_transitions': {'count': 3}
                },
                'burstiness': {
                    'tier': 'CORE',
                    'score': 45.0,
                    'weight': 0.20,
                    'tier_mapping': {'low': [0, 40], 'medium': [40, 70], 'high': [70, 100]},
                    # Original raw outputs preserved:
                    'sentence_burstiness': {'cv': 0.15, 'score': 45.0}
                }
            }
        """
        # Input validation (AC11)
        if not isinstance(dimension_results, dict):
            print("Warning: dimension_results is not a dict, returning as-is", file=sys.stderr)
            return dimension_results

        enriched = {}

        for dim_name, raw_output in dimension_results.items():
            # Input validation: check raw_output is dict
            if not isinstance(raw_output, dict):
                print(
                    f"Warning: {dim_name} output is not a dict, skipping enrichment",
                    file=sys.stderr,
                )
                enriched[dim_name] = raw_output
                continue

            # Skip failed dimensions (have 'error' field and 'available': False)
            if raw_output.get("error") or raw_output.get("available") is False:
                enriched[dim_name] = raw_output  # Keep error info, don't enrich
                continue

            # Get dimension metadata from registry
            tier = self._get_dimension_tier(dim_name)
            weight = self._get_dimension_weight(tier)

            # Extract normalized score from raw output
            score = self._extract_dimension_score(dim_name, raw_output)

            # Bounds check score (AC11)
            if score < 0.0 or score > 100.0:
                print(
                    f"Warning: {dim_name} score {score} out of bounds, clamping to [0, 100]",
                    file=sys.stderr,
                )
                score = max(0.0, min(100.0, score))

            # Get tier mapping/thresholds
            tier_mapping = self._get_tier_mapping(dim_name)

            # Get recommendations from dimension (AC1)
            recommendations = []
            try:
                dimension = self.dimensions.get(dim_name)
                if dimension:
                    recommendations = dimension.get_recommendations(score, raw_output)
                    if not isinstance(recommendations, list):
                        print(
                            f"Warning: {dim_name}.get_recommendations() returned non-list: {type(recommendations)}",
                            file=sys.stderr,
                        )
                        recommendations = []
            except Exception as e:
                print(
                    f"Warning: Failed to get recommendations for {dim_name}: {e}", file=sys.stderr
                )
                recommendations = []

            # Create enriched entry (preserves all raw outputs via spread)
            enriched[dim_name] = {
                "tier": tier,
                "score": score,
                "weight": weight,
                "tier_mapping": tier_mapping,
                "recommendations": recommendations,  # NEW: Include recommendations
                **raw_output,  # Preserve all original outputs
            }

        return enriched

    def _get_dimension_tier(self, dim_name: str) -> str:
        """
        Get tier classification for dimension from registry.

        Args:
            dim_name: Dimension name (e.g., 'perplexity', 'burstiness')

        Returns:
            Tier string: 'CORE', 'ADVANCED', 'STRUCTURAL', 'SUPPORTING', or 'UNKNOWN'
        """
        try:
            dimensions = DimensionRegistry.get_all()
            for dim in dimensions:
                if dim.dimension_name == dim_name:
                    return dim.tier
            print(
                f"Warning: Dimension {dim_name} not found in registry, using 'UNKNOWN'",
                file=sys.stderr,
            )
            return "UNKNOWN"
        except Exception as e:
            print(f"Error: Getting tier for {dim_name}: {e}", file=sys.stderr)
            return "UNKNOWN"

    def _get_dimension_weight(self, tier: str) -> float:
        """
        Get weight based on tier.

        Weight Assignment by Tier:
        - CORE: 0.20 (highest priority)
        - ADVANCED: 0.10 (medium-high priority)
        - STRUCTURAL: 0.10 (medium priority)
        - SUPPORTING: 0.05 (lower priority)
        - UNKNOWN: 0.05 (default)

        Args:
            tier: Tier string from registry

        Returns:
            Weight as float
        """
        tier_weights = {
            "CORE": 0.20,
            "ADVANCED": 0.10,
            "STRUCTURAL": 0.10,
            "SUPPORTING": 0.05,
            "UNKNOWN": 0.05,
        }
        weight = tier_weights.get(tier, 0.05)

        # Bounds check (AC11)
        if weight < 0.0:
            print(
                f"Warning: Weight {weight} for tier {tier} is negative, using 0.05", file=sys.stderr
            )
            return 0.05

        return weight

    def _extract_dimension_score(self, dim_name: str, raw_output: Dict) -> float:
        """
        Extract normalized score (0-100) from dimension's raw output.

        Dimensions store scores in different formats. This method handles
        the variations and provides a consistent 0-100 score.

        Extraction Strategy:
        1. Check for 'overall_score' field (preferred)
        2. Check for 'score' field
        3. Check for dimension-specific score fields
        4. Calculate from metrics if possible
        5. Default to 50.0 (neutral) if no score found

        Args:
            dim_name: Dimension name for dimension-specific logic
            raw_output: Raw dimension analysis output dict

        Returns:
            Normalized score 0-100
        """
        # Strategy 1: Direct overall_score
        if "overall_score" in raw_output:
            try:
                return float(raw_output["overall_score"])
            except (TypeError, ValueError) as e:
                print(
                    f"Warning: Error converting overall_score for {dim_name}: {e}", file=sys.stderr
                )

        # Strategy 2: Direct score field
        if "score" in raw_output:
            try:
                return float(raw_output["score"])
            except (TypeError, ValueError) as e:
                print(f"Warning: Error converting score for {dim_name}: {e}", file=sys.stderr)

        # Strategy 3: Dimension-specific extraction
        try:
            if dim_name == "burstiness":
                # Burstiness stores score in sentence_burstiness.score
                if "sentence_burstiness" in raw_output:
                    sb = raw_output["sentence_burstiness"]
                    if isinstance(sb, dict) and "score" in sb:
                        return float(sb["score"])

            elif dim_name == "perplexity":
                # Perplexity might store in metrics or calculate from sub-metrics
                if "metrics" in raw_output:
                    metrics = raw_output["metrics"]
                    if isinstance(metrics, dict) and "overall_score" in metrics:
                        return float(metrics["overall_score"])

            elif dim_name == "structure" and "structural_score" in raw_output:
                # Structure might have structural_score
                return float(raw_output["structural_score"])

            # Add other dimension-specific extractions as needed
            # For dimensions following standard format, this section can be minimal

        except (KeyError, TypeError, ValueError) as e:
            print(
                f"Warning: Error extracting score for {dim_name}: {e}, using default 50.0",
                file=sys.stderr,
            )

        # Strategy 4: Call dimension's calculate_score() method if available
        if dim_name in self.dimensions:
            dimension = self.dimensions[dim_name]
            if hasattr(dimension, "calculate_score") and callable(dimension.calculate_score):
                try:
                    score = dimension.calculate_score(raw_output)
                    # Bounds check
                    if 0.0 <= score <= 100.0:
                        return float(score)
                    else:
                        print(
                            f"Warning: {dim_name}.calculate_score() returned {score} (out of bounds), clamping",
                            file=sys.stderr,
                        )
                        return max(0.0, min(100.0, float(score)))
                except Exception as e:
                    print(
                        f"Warning: Error calling {dim_name}.calculate_score(): {e}", file=sys.stderr
                    )

        # Strategy 5: Default to neutral score
        print(
            f"Warning: No score found for dimension {dim_name}, defaulting to 50.0 (neutral)",
            file=sys.stderr,
        )
        return 50.0

    def _get_tier_mapping(self, dim_name: str) -> Dict:
        """
        Get tier thresholds for dimension.

        Standard Tier Thresholds:
        - low: [0, 40] - AI-likely, needs attention
        - medium: [40, 70] - Mixed characteristics
        - high: [70, 100] - Human-like, acceptable

        Args:
            dim_name: Dimension name (for future custom thresholds)

        Returns:
            Dict with tier ranges
        """
        # Standard thresholds for all dimensions
        # Future enhancement: allow dimension-specific overrides
        return {"low": [0, 40], "medium": [40, 70], "high": [70, 100]}

    def _count_words(self, text: str) -> int:
        """Count total words in text, excluding code blocks."""
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Count words
        words = re.findall(r"\b[\w'-]+\b", text)
        return len(words)

    def _convert_score_to_category(self, raw_score: float, available: bool = True) -> str:
        """
        Convert 0-100 score to quality category with positive labeling.

        Scoring Convention:
        - 100.0 = most human-like (perfect score, no AI patterns)
        - 0.0 = most AI-like (worst score, strong AI patterns)
        Higher scores are better.

        Args:
            raw_score: Raw score from 0-100 (higher = more human-like)
            available: Whether the metric is available

        Returns:
            Category string: EXCELLENT, GOOD, NEEDS WORK, POOR, or UNKNOWN
        """
        if not available:
            return "UNKNOWN"

        # Positive labeling - higher scores get better labels
        if raw_score >= 85:
            return "EXCELLENT"  # 85-100: Minimal AI patterns detected
        elif raw_score >= 70:
            return "GOOD"  # 70-84: Some AI patterns, mostly human-like
        elif raw_score >= 50:
            return "NEEDS WORK"  # 50-69: Noticeable AI patterns
        else:
            return "POOR"  # 0-49: Strong AI patterns detected

    def _flatten_optional_metrics(
        self,
        syntactic_results,
        lexical_results,
        formatting_results=None,
        burstiness_results=None,
        structure_results=None,
    ) -> Dict:
        """
        Flatten optional metrics from dimension analyzers into flat dict for AnalysisResults.

        Story 2.0: Removed deprecated stylometric_results and advanced_results parameters.
        """
        metrics = {}

        # Syntactic metrics
        if syntactic_results.get("syntactic"):
            synt = syntactic_results["syntactic"]
            metrics["syntactic_repetition_score"] = synt.get("syntactic_repetition_score")
            metrics["pos_diversity"] = synt.get("pos_diversity")
            metrics["avg_dependency_depth"] = synt.get("avg_dependency_depth")
            metrics["subordination_index"] = synt.get("subordination_index")

        # Lexical metrics
        if lexical_results.get("lexical_diversity"):
            metrics["mtld_score"] = lexical_results["lexical_diversity"].get("mtld_score")
            metrics["stemmed_diversity"] = lexical_results["lexical_diversity"].get(
                "stemmed_diversity"
            )

        # Story 2.0: Removed deprecated stylometric and advanced metrics extraction
        # These metrics are now provided by the new dimension system:
        # - Stylometric metrics → ReadabilityDimension, TransitionMarkerDimension
        # - GLTR metrics → PredictabilityDimension
        # - Advanced lexical metrics → AdvancedLexicalDimension

        # Formatting metrics (Phase 3 enhancements)
        if formatting_results:
            # Bold/italic patterns
            if formatting_results.get("bold_italic"):
                bold_italic = formatting_results["bold_italic"]
                metrics["bold_per_1k_words"] = bold_italic.get("bold_per_1k", 0.0)
                metrics["italic_per_1k_words"] = bold_italic.get("italic_per_1k", 0.0)
                metrics["formatting_consistency_score"] = bold_italic.get(
                    "formatting_consistency", 0.0
                )

                # Calculate bold_italic_score based on metrics
                bold_issues = 0
                bold_val = bold_italic.get("bold_per_1k", 0.0)
                if bold_val > 50:  # Extreme AI
                    bold_issues += 2
                elif bold_val > 10:  # AI-like
                    bold_issues += 1

                consistency = bold_italic.get("formatting_consistency", 0.0)
                if consistency > 0.6:  # Mechanical
                    bold_issues += 1

                metrics["bold_italic_score"] = (
                    "HIGH" if bold_issues == 0 else ("MEDIUM" if bold_issues == 1 else "LOW")
                )

            # List usage patterns
            if formatting_results.get("list_usage"):
                list_usage = formatting_results["list_usage"]
                metrics["total_list_items"] = list_usage.get("total_list_items", 0)
                metrics["ordered_list_items"] = list_usage.get("ordered_items", 0)
                metrics["unordered_list_items"] = list_usage.get("unordered_items", 0)
                metrics["list_to_text_ratio"] = list_usage.get("list_to_text_ratio", 0.0)
                metrics["ordered_to_unordered_ratio"] = list_usage.get(
                    "ordered_to_unordered_ratio", 0.0
                )
                metrics["list_item_length_variance"] = list_usage.get("list_item_variance", 0.0)

                # Calculate list_usage_score based on metrics
                list_issues = 0
                list_ratio = list_usage.get("list_to_text_ratio", 0.0)
                if list_ratio > 0.25:  # AI tends >25%
                    list_issues += 2
                elif list_ratio > 0.15:
                    list_issues += 1

                ordered_ratio = list_usage.get("ordered_to_unordered_ratio", 0.0)
                if 0.15 <= ordered_ratio <= 0.25:  # AI typical range
                    list_issues += 1

                metrics["list_usage_score"] = (
                    "HIGH" if list_issues == 0 else ("MEDIUM" if list_issues == 1 else "LOW")
                )

            # Punctuation clustering
            if formatting_results.get("punctuation_clustering"):
                punct = formatting_results["punctuation_clustering"]
                metrics["em_dash_cascading_score"] = punct.get("em_dash_cascading", 0.0)
                metrics["oxford_comma_count"] = punct.get("oxford_comma_count", 0)
                metrics["oxford_comma_consistency"] = punct.get("oxford_consistency", 0.0)

                # Calculate punctuation_score based on metrics
                punct_issues = 0
                oxford_consistency = punct.get("oxford_consistency", 0.0)
                if oxford_consistency > 0.95:  # Always Oxford = AI-like
                    punct_issues += 1

                em_cascade = punct.get("em_dash_cascading", 0.0)
                if em_cascade > 0.7:  # AI declining pattern
                    punct_issues += 1

                metrics["punctuation_score"] = (
                    "HIGH" if punct_issues == 0 else ("MEDIUM" if punct_issues == 1 else "LOW")
                )

            # Whitespace patterns
            if formatting_results.get("whitespace_patterns"):
                whitespace = formatting_results["whitespace_patterns"]
                metrics["paragraph_length_variance"] = whitespace.get("paragraph_variance", 0.0)
                metrics["paragraph_uniformity_score"] = whitespace.get("paragraph_uniformity", 0.0)
                metrics["blank_lines_count"] = whitespace.get("blank_lines", 0)
                metrics["text_density"] = whitespace.get("text_density", 0.0)

                # Calculate whitespace_score based on metrics
                ws_issues = 0
                para_uniformity = whitespace.get("paragraph_uniformity", 0.0)
                if para_uniformity > 0.6:  # High uniformity = AI-like
                    ws_issues += 2
                elif para_uniformity > 0.4:
                    ws_issues += 1

                metrics["whitespace_score"] = (
                    "HIGH" if ws_issues == 0 else ("MEDIUM" if ws_issues == 1 else "LOW")
                )

        # Burstiness metrics (paragraph CV from Phase 1)
        if burstiness_results and burstiness_results.get("paragraph_cv"):
            para_cv = burstiness_results["paragraph_cv"]
            metrics["paragraph_cv"] = para_cv.get("cv", 0.0)
            metrics["paragraph_cv_mean"] = para_cv.get("mean_length", 0.0)
            metrics["paragraph_cv_stddev"] = para_cv.get("stddev", 0.0)
            metrics["paragraph_cv_score"] = para_cv.get("score", 0.0)
            metrics["paragraph_cv_assessment"] = para_cv.get("assessment", "UNKNOWN")
            metrics["paragraph_count"] = para_cv.get("paragraph_count", 0)

        # Structure metrics (Phase 1 & 3)
        if structure_results:
            # Section variance
            if structure_results.get("section_variance"):
                sec_var = structure_results["section_variance"]
                metrics["section_variance_pct"] = sec_var.get("variance_pct", 0.0)
                metrics["section_variance_score"] = sec_var.get("score", 0.0)
                metrics["section_variance_assessment"] = sec_var.get("assessment", "UNKNOWN")
                metrics["section_count"] = sec_var.get("section_count", 0)
                metrics["section_uniform_clusters"] = sec_var.get("uniform_clusters", 0)

            # List nesting depth
            if structure_results.get("list_nesting"):
                list_nest = structure_results["list_nesting"]
                metrics["list_max_depth"] = list_nest.get("max_depth", 0)
                metrics["list_avg_depth"] = list_nest.get("avg_depth", 0.0)
                metrics["list_total_items"] = list_nest.get("total_list_items", 0)
                metrics["list_depth_assessment"] = list_nest.get("assessment", "UNKNOWN")
                metrics["list_depth_score"] = list_nest.get("score", 0.0)

            # Heading hierarchy enhanced (includes length variance)
            if structure_results.get("heading_hierarchy_enhanced"):
                head_hier = structure_results["heading_hierarchy_enhanced"]
                metrics["heading_hierarchy_skips"] = head_hier.get("hierarchy_skips", 0)
                metrics["heading_length_variance"] = head_hier.get("heading_length_variance", 0.0)
                metrics["heading_strict_adherence"] = head_hier.get("hierarchy_adherence", 0.0)

                # Calculate heading_hierarchy_score based on metrics
                hier_issues = 0
                adherence = head_hier.get("hierarchy_adherence", 0.0)
                if adherence >= 1.0:  # Perfect = AI-like
                    hier_issues += 2
                elif adherence >= 0.95:
                    hier_issues += 1

                length_variance = head_hier.get("heading_length_variance", 0.0)
                if length_variance < 2.0:  # Low variance = AI-like
                    hier_issues += 1

                metrics["heading_hierarchy_score"] = (
                    "HIGH" if hier_issues == 0 else ("MEDIUM" if hier_issues <= 1 else "LOW")
                )

            # Subsection asymmetry (H3 counts under H2 sections)
            if structure_results.get("subsection_asymmetry"):
                subsec = structure_results["subsection_asymmetry"]
                metrics["subsection_counts"] = subsec.get("subsection_counts", [])
                metrics["subsection_cv"] = subsec.get("cv", 0.0)
                metrics["subsection_uniform_count"] = subsec.get("uniform_count", 0)
                metrics["subsection_assessment"] = subsec.get("assessment", "UNKNOWN")

            # H4 subsection asymmetry (H4 counts under H3 sections)
            if structure_results.get("h4_subsection_asymmetry"):
                h4_subsec = structure_results["h4_subsection_asymmetry"]
                metrics["h4_counts"] = h4_subsec.get("h4_counts", [])
                metrics["h4_subsection_cv"] = h4_subsec.get("cv", 0.0)
                metrics["h4_uniform_count"] = h4_subsec.get("uniform_count", 0)
                metrics["h4_assessment"] = h4_subsec.get("assessment", "UNKNOWN")
                metrics["h4_h3_sections_analyzed"] = h4_subsec.get("h3_count", 0)

            # Multi-level combined structure score (domain-specific)
            if structure_results.get("combined_structure_score"):
                combined = structure_results["combined_structure_score"]
                if combined and not combined.get("error"):
                    metrics["combined_structure_score"] = combined.get("combined_score", 0.0)
                    metrics["combined_structure_assessment"] = combined.get(
                        "combined_assessment", "UNKNOWN"
                    )
                    metrics["combined_structure_domain"] = combined.get("domain", "general")
                    metrics["combined_structure_prob_human"] = combined.get("prob_human", 0.0)

                    # Breakdown details
                    breakdown = combined.get("breakdown", {})
                    metrics["combined_h2_score"] = breakdown.get("h2_score", 0.0)
                    metrics["combined_h2_assessment"] = breakdown.get("h2_assessment", "UNKNOWN")
                    metrics["combined_h3_score"] = breakdown.get("h3_score", 0.0)
                    metrics["combined_h3_assessment"] = breakdown.get("h3_assessment", "UNKNOWN")
                    metrics["combined_h4_score"] = breakdown.get("h4_score", 0.0)
                    metrics["combined_h4_assessment"] = breakdown.get("h4_assessment", "UNKNOWN")

        return metrics

    def _assess_overall(self, results: AnalysisResults) -> str:
        """Calculate overall assessment based on all dimension scores."""
        score_map = {"EXCELLENT": 3, "GOOD": 2, "NEEDS WORK": 1, "POOR": 0, "UNKNOWN": 2}

        scores = [
            score_map[results.perplexity_score],
            score_map[results.burstiness_score],
            score_map[results.structure_score],
            score_map[results.voice_score],
            score_map[results.formatting_score],
        ]

        avg = sum(scores) / len(scores)

        if avg >= 2.5:
            return "HUMAN-LIKE"
        elif avg >= 1.5:
            return "MIXED"
        else:
            return "AI-LIKELY"

    # ========================================================================
    # DUAL SCORE CALCULATION
    # ========================================================================

    def calculate_dual_score(
        self, results: AnalysisResults, detection_target: float = 30.0, quality_target: float = 85.0
    ) -> DualScore:
        """
        Calculate dual scores: Detection Risk (0-100, lower=better) and Quality Score (0-100, higher=better).

        Delegates to the dual_score_calculator module for the actual calculation.

        Args:
            results: AnalysisResults from analysis
            detection_target: Target detection risk (default 30 = low risk)
            quality_target: Target quality score (default 85 = excellent)

        Returns:
            DualScore with comprehensive breakdown and optimization path
        """
        return _calculate_dual_score(results, detection_target, quality_target, self.config)

    # ========================================================================
    # HISTORY TRACKING
    # ========================================================================

    def _get_history_file_path(self, file_path: str) -> Path:
        """Get path to history JSON file for a document."""
        doc_path = Path(file_path)
        history_dir = doc_path.parent / ".ai-analysis-history"
        history_dir.mkdir(exist_ok=True)
        return history_dir / f"{doc_path.stem}.history.json"

    def load_score_history(self, file_path: str) -> ScoreHistory:
        """Load score history for a document."""
        history_file = self._get_history_file_path(file_path)

        if not history_file.exists():
            return ScoreHistory(file_path=file_path, scores=[])

        try:
            with open(history_file, encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct ScoreHistory from JSON using from_dict() to properly restore DimensionScore objects
            return ScoreHistory.from_dict(data)

        except Exception as e:
            print(f"Warning: Could not load history from {history_file}: {e}", file=sys.stderr)
            return ScoreHistory(file_path=file_path, scores=[])

    def save_score_history(self, history: ScoreHistory):
        """Save score history for a document."""
        history_file = self._get_history_file_path(history.file_path)

        try:
            # Convert to dict for JSON serialization
            data = {
                "file_path": history.file_path,
                "scores": [asdict(score) for score in history.scores],
            }

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save history to {history_file}: {e}", file=sys.stderr)

    # ========================================================================
    # DETAILED ANALYSIS (LINE-BY-LINE)
    # ========================================================================

    def analyze_file_detailed(self, file_path: str) -> DetailedAnalysis:
        """
        Analyze file with detailed line-by-line diagnostics.

        This method provides actionable feedback for each AI pattern detected,
        including line numbers, context, and specific suggestions for improvement.

        Args:
            file_path: Path to markdown file to analyze

        Returns:
            DetailedAnalysis object with line-by-line findings

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            text = f.read()
            self.lines = text.splitlines()

        # Run standard analysis for summary
        standard_results = self.analyze_file(file_path)

        # Run detailed analyses using dimension analyzers
        html_checker = self._is_line_in_html_comment

        # Call dimension analyzers' analyze_detailed methods
        vocab_instances = self._analyze_ai_vocabulary_detailed()
        heading_issues = self._analyze_headings_detailed()
        uniform_paras = self._analyze_sentence_uniformity_detailed()
        em_dash_instances = self._analyze_em_dashes_detailed()
        transition_instances = self._analyze_transitions_detailed()

        # Advanced detailed analyses (using new dimensions dict pattern)
        burstiness_dim = self.dimensions.get("burstiness")
        burstiness_issues = (
            burstiness_dim.analyze_detailed(self.lines, html_checker)
            if burstiness_dim and hasattr(burstiness_dim, "analyze_detailed")
            else []
        )

        syntactic_dim = self.dimensions.get("syntactic")
        syntactic_issues = (
            syntactic_dim.analyze_detailed(self.lines, html_checker)
            if syntactic_dim and hasattr(syntactic_dim, "analyze_detailed")
            else []
        )

        # Story 2.0: Removed deprecated 'stylometric' dimension
        # Stylometric functionality replaced by ReadabilityDimension and TransitionMarkerDimension

        formatting_dim = self.dimensions.get("formatting")
        formatting_issues = (
            formatting_dim.analyze_detailed(self.lines, html_checker)
            if formatting_dim and hasattr(formatting_dim, "analyze_detailed")
            else []
        )

        # Story 2.0: High predictability segments come from PredictabilityDimension (GLTR analysis)
        # Removed fallback to 'advanced_lexical' (deprecated AdvancedDimension split in Story 1.4.5)
        predictability_dim = self.dimensions.get("predictability")
        high_pred_segments = (
            predictability_dim.analyze_detailed(self.lines, html_checker)
            if predictability_dim and hasattr(predictability_dim, "analyze_detailed")
            else []
        )

        # Build summary dict from standard results
        summary = {
            "overall_assessment": standard_results.overall_assessment,
            "perplexity_score": standard_results.perplexity_score,
            "burstiness_score": standard_results.burstiness_score,
            "structure_score": standard_results.structure_score,
            "voice_score": standard_results.voice_score,
            "technical_score": standard_results.technical_score,
            "formatting_score": standard_results.formatting_score,
            "total_words": standard_results.total_words,
            "total_sentences": standard_results.total_sentences,
            "ai_vocab_per_1k": standard_results.ai_vocabulary_per_1k,
            "sentence_stdev": standard_results.sentence_stdev,
            "em_dashes_per_page": standard_results.em_dashes_per_page,
            "heading_depth": standard_results.heading_depth,
            "heading_parallelism": standard_results.heading_parallelism_score,
            # Advanced metrics
            # Story 2.0: Removed deprecated 'gltr_score' and 'stylometric_score' fields
            # gltr_score → predictability_score (PredictabilityDimension)
            # stylometric_score → readability_score + transition_marker_score
            "advanced_lexical_score": getattr(standard_results, "advanced_lexical_score", "N/A"),
            "ai_detection_score": getattr(standard_results, "ai_detection_score", "N/A"),
        }

        return DetailedAnalysis(
            file_path=file_path,
            summary=summary,
            # Original detailed findings
            ai_vocabulary=vocab_instances[:15],  # Limit to top 15
            heading_issues=heading_issues,
            uniform_paragraphs=uniform_paras,
            em_dashes=em_dash_instances[:20],  # Limit to top 20
            transitions=transition_instances[:15],  # Limit to top 15
            # Advanced detailed findings
            burstiness_issues=burstiness_issues[:10] if isinstance(burstiness_issues, list) else [],
            syntactic_issues=syntactic_issues[:20] if isinstance(syntactic_issues, list) else [],
            # Story 2.0: Removed stylometric_issues (deprecated StylometricDimension)
            formatting_issues=formatting_issues[:15] if isinstance(formatting_issues, list) else [],
            high_predictability_segments=high_pred_segments[:10]
            if isinstance(high_pred_segments, list)
            else [],
        )

    def _analyze_ai_vocabulary_detailed(self) -> List[VocabInstance]:
        """Detect AI vocabulary with line numbers and context."""
        instances = []

        for line_num, line in enumerate(self.lines, start=1):
            # Skip HTML comments (metadata), headings, and code blocks
            if self._is_line_in_html_comment(line):
                continue
            if line.strip().startswith("#") or line.strip().startswith("```"):
                continue

            for pattern, suggestions in self.AI_VOCAB_REPLACEMENTS.items():
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    word = match.group()
                    # Extract context (20 chars each side)
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = f"...{line[start:end]}..."

                    instances.append(
                        VocabInstance(
                            line_number=line_num,
                            word=word,
                            context=context,
                            full_line=line.strip(),
                            suggestions=suggestions[:5],  # Top 5 suggestions
                        )
                    )

        return instances

    def _analyze_headings_detailed(self) -> List[HeadingIssue]:
        """Analyze headings with specific issues and line numbers."""
        issues = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line_num, line in enumerate(self.lines, start=1):
            match = heading_pattern.match(line.strip())
            if not match:
                continue

            level_marks, text = match.groups()
            level = len(level_marks)
            words = text.split()
            word_count = len(words)

            # Check for issues
            issue_type = None
            suggestion = None

            # Verbose headings (>8 words)
            if word_count > 8:
                issue_type = "verbose"
                suggestion = "Shorten to key concept: focus on 3-6 impactful words"

            # Deep hierarchy (H5, H6)
            elif level >= 5:
                issue_type = "deep_hierarchy"
                suggestion = "Restructure content to use H1-H4 only"

            # Parallel structure detection (all starting with same word at this level)
            # This is simplified - full implementation would track all headings at each level
            elif text.split()[0] in [
                "How",
                "What",
                "Why",
                "Understanding",
                "Exploring",
                "Introduction",
            ]:
                issue_type = "parallel"
                suggestion = "Vary heading styles: mix questions, statements, and imperatives"

            if issue_type:
                issues.append(
                    HeadingIssue(
                        line_number=line_num,
                        level=level,
                        text=text,
                        issue_type=issue_type,
                        suggestion=suggestion or "",
                    )
                )

        return issues

    def _analyze_sentence_uniformity_detailed(self) -> List[UniformParagraph]:
        """Detect unnaturally uniform paragraphs."""
        uniform_paragraphs = []

        # Split into paragraphs
        paragraphs: List[Tuple[int, str]] = []
        current_para: List[str] = []
        current_start_line = 1

        for line_num, line in enumerate(self.lines, start=1):
            stripped = line.strip()

            # Skip headings and code blocks
            if stripped.startswith("#") or stripped.startswith("```"):
                if current_para:
                    paragraphs.append((current_start_line, "\n".join(current_para)))
                    current_para = []
                continue

            # Blank line = end of paragraph
            if not stripped:
                if current_para:
                    paragraphs.append((current_start_line, "\n".join(current_para)))
                    current_para = []
                    current_start_line = line_num + 1
            else:
                if not current_para:
                    current_start_line = line_num
                current_para.append(line)

        # Add final paragraph
        if current_para:
            paragraphs.append((current_start_line, "\n".join(current_para)))

        # Analyze sentence uniformity within each paragraph
        for start_line, para_text in paragraphs:
            if len(para_text) < 50:  # Skip short paragraphs
                continue

            # Split into sentences
            sent_pattern = re.compile(r"(?<=[.!?])\s+")
            sentences = [s.strip() for s in sent_pattern.split(para_text) if s.strip()]

            if len(sentences) < 3:
                continue

            # Count words per sentence
            sent_lengths = [len(re.findall(r"[\w'-]+", sent)) for sent in sentences]

            if not sent_lengths:
                continue

            # Calculate coefficient of variation
            mean_len = statistics.mean(sent_lengths)
            if mean_len == 0:
                continue
            stdev = statistics.stdev(sent_lengths) if len(sent_lengths) > 1 else 0
            cv = stdev / mean_len

            # Flag if too uniform (CV < 0.3 is AI-like)
            if cv < 0.3:
                # Create sentence details list (line_num, text, word_count)
                sentence_details = [
                    (start_line, sent[:100], sent_lengths[i])
                    for i, sent in enumerate(sentences[:5])
                ]  # First 5 sentences

                uniform_paragraphs.append(
                    UniformParagraph(
                        start_line=start_line,
                        end_line=start_line,  # Approximate - same line for now
                        sentence_count=len(sentences),
                        mean_length=round(mean_len, 1),
                        stdev=round(stdev, 1),
                        sentences=sentence_details,
                        problem=f"Uniform sentence lengths (CV={cv:.2f}, typical human: >0.4)",
                        suggestion="Vary sentence length: mix short (5-10w), medium (15-25w), and long (30-45w) sentences",
                    )
                )

        return uniform_paragraphs

    def _analyze_em_dashes_detailed(self) -> List[EmDashInstance]:
        """Detect em-dash usage with line numbers."""
        instances = []
        em_dash_pattern = re.compile(r"—|--")

        for line_num, line in enumerate(self.lines, start=1):
            # Skip HTML comments, headings, code blocks
            if self._is_line_in_html_comment(line):
                continue
            if line.strip().startswith("#") or line.strip().startswith("```"):
                continue

            for match in em_dash_pattern.finditer(line):
                # Extract context (40 chars each side)
                start = max(0, match.start() - 40)
                end = min(len(line), match.end() + 40)
                context = f"...{line[start:end]}..."

                instances.append(
                    EmDashInstance(
                        line_number=line_num,
                        context=context,
                        problem="Em-dash overuse (ChatGPT uses 10x more than humans)",
                        suggestion="Replace with: comma, semicolon, period (new sentence), or parentheses",
                    )
                )

        return instances

    def _analyze_transitions_detailed(self) -> List[TransitionInstance]:
        """Detect formulaic transitions with line numbers."""
        instances = []

        formulaic_patterns = [
            r"\bFurthermore,\b",
            r"\bMoreover,\b",
            r"\bAdditionally,\b",
            r"\bIn addition,\b",
            r"\bIt is important to note that\b",
            r"\bIt is worth mentioning that\b",
            r"\bWhen it comes to\b",
            r"\bOne of the key aspects\b",
            r"\bFirst and foremost,\b",
        ]

        for line_num, line in enumerate(self.lines, start=1):
            # Skip HTML comments, headings, code blocks
            if self._is_line_in_html_comment(line):
                continue
            if line.strip().startswith("#") or line.strip().startswith("```"):
                continue

            for pattern in formulaic_patterns:
                for match in re.finditer(pattern, line):
                    phrase = match.group()
                    # Extract context
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 60)
                    context = f"...{line[start:end]}..."

                    # Get suggestions from TRANSITION_REPLACEMENTS
                    suggestions = self.TRANSITION_REPLACEMENTS.get(phrase, ["Rephrase naturally"])

                    instances.append(
                        TransitionInstance(
                            line_number=line_num,
                            transition=phrase,
                            context=context,
                            suggestions=suggestions[:5],
                        )
                    )

        return instances
