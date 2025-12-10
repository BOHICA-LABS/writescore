"""
Semantic Coherence dimension analyzer.

Analyzes semantic coherence patterns using sentence embeddings to detect
AI-generated text characteristics related to topic consistency and discourse flow.

Weight: 5.0%
Tier: SUPPORTING
Version: 1.0.0

Analyzes four coherence metrics:
- Paragraph cohesion: Sentence-level semantic similarity within paragraphs
- Topic consistency: Section-to-section semantic drift measurement
- Discourse flow: Paragraph transition quality assessment
- Conceptual depth: Paragraph-to-document semantic alignment

Optional dependency: sentence-transformers (>=2.0.0)
- When available: Uses transformer-based semantic embeddings (all-MiniLM-L6-v2)
- When unavailable: Falls back to basic lexical coherence (word overlap)

Performance optimizations:
- Sentence sampling for documents >500 sentences
- Batch processing for embedding generation (batch_size=32)
- Lazy model loading with LRU cache

Installation:
    pip install ai-pattern-analyzer[semantic]  # With semantic coherence
    # OR
    pip install sentence-transformers  # Manual installation

Research validation: Story 2.3.0 (GO decision)
Implementation: Story 2.3

Version History:
- v1.0.0 (v5.2.0): Initial implementation with 4 coherence metrics - Story 2.3
"""

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from writescore.core.analysis_config import AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier


class SemanticCoherenceDimension(DimensionStrategy):
    """
    Analyzes semantic coherence using sentence embeddings for AI detection.

    Weight: 5.0% of total score
    Tier: SUPPORTING (contextual quality indicator)

    Detects AI-specific coherence patterns:
    - Paragraph cohesion differences (sentence-level semantic similarity)
    - Topic consistency patterns (section-to-section drift)
    - Discourse flow characteristics (paragraph transition quality)
    - Conceptual depth variations (paragraph-to-document alignment)

    Uses transformer-based embeddings when sentence-transformers available,
    falls back to basic lexical analysis otherwise.
    """

    # ========================================================================
    # CLASS-LEVEL STATE FOR MODEL MANAGEMENT
    # ========================================================================

    _model = None
    _model_available = None  # Tri-state: None=unchecked, True/False=checked

    # Optimization thresholds (from Story 2.3.0 research)
    MAX_SENTENCES_BEFORE_SAMPLING = 500
    SAMPLE_SIZE = 50
    BATCH_SIZE = 32

    # Coherence thresholds (calibrated based on sentence-transformer research)
    # Research shows typical human writing has 0.40-0.60 sentence similarity within paragraphs
    # Adjusted from original 0.60-0.78 thresholds which were too high (Story 2.4.2)
    THRESHOLDS = {
        "general": {
            "paragraph_cohesion": {
                "excellent": 0.55,  # Well-connected ideas (research: 0.50-0.60 typical)
                "good": 0.45,
                "acceptable": 0.35,  # Typical human writing baseline
            },
            "topic_consistency": {
                "excellent": 0.72,
                "good": 0.65,
                "acceptable": 0.55,
            },
            "discourse_flow": {
                "ideal_min": 0.45,  # Ideal transition range (adjusted for realistic embeddings)
                "ideal_max": 0.65,
                "excellent": 0.65,
                "good": 0.55,
                "acceptable": 0.45,
            },
            "conceptual_depth": {
                "excellent": 0.68,
                "good": 0.60,
                "acceptable": 0.50,
            },
        },
        "technical": {
            # Technical writing: More lenient (technical terms may reduce similarity)
            "paragraph_cohesion": {
                "excellent": 0.50,  # Technical content has varied terminology
                "good": 0.40,
                "acceptable": 0.30,
            },
            "topic_consistency": {
                "excellent": 0.68,
                "good": 0.60,
                "acceptable": 0.50,
            },
            "discourse_flow": {
                "ideal_min": 0.40,  # Technical writing has more varied transitions
                "ideal_max": 0.60,
                "excellent": 0.60,
                "good": 0.50,
                "acceptable": 0.40,
            },
            "conceptual_depth": {
                "excellent": 0.64,
                "good": 0.56,
                "acceptable": 0.46,
            },
        },
        "creative": {
            # Creative writing: Lower thresholds (purposeful variation is normal)
            "paragraph_cohesion": {
                "excellent": 0.50,  # Creative prose varies more
                "good": 0.40,
                "acceptable": 0.30,
            },
            "topic_consistency": {
                "excellent": 0.70,
                "good": 0.62,
                "acceptable": 0.52,
            },
            "discourse_flow": {
                "ideal_min": 0.40,  # Creative writing varies significantly
                "ideal_max": 0.60,
                "excellent": 0.60,
                "good": 0.50,
                "acceptable": 0.40,
            },
            "conceptual_depth": {
                "excellent": 0.66,
                "good": 0.58,
                "acceptable": 0.48,
            },
        },
        "academic": {
            # Academic writing: Slightly higher than general (formal structure)
            "paragraph_cohesion": {
                "excellent": 0.58,  # Academic writing is more structured
                "good": 0.48,
                "acceptable": 0.38,
            },
            "topic_consistency": {
                "excellent": 0.73,
                "good": 0.66,
                "acceptable": 0.56,
            },
            "discourse_flow": {
                "ideal_min": 0.45,  # Academic writing similar to general
                "ideal_max": 0.65,
                "excellent": 0.65,
                "good": 0.55,
                "acceptable": 0.45,
            },
            "conceptual_depth": {
                "excellent": 0.69,
                "good": 0.61,
                "acceptable": 0.51,
            },
        },
    }

    # ========================================================================
    # INITIALIZATION AND REGISTRATION
    # ========================================================================

    def __init__(self):
        """Initialize dimension and register with DimensionRegistry."""
        super().__init__()
        # Self-register with dimension registry
        DimensionRegistry.register(self)

    # ========================================================================
    # DIMENSION METADATA (Required by DimensionStrategy)
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Unique dimension identifier."""
        return "semantic_coherence"

    @property
    def weight(self) -> float:
        """Contribution weight (5.0% of total score)."""
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        """Dimension tier classification."""
        return DimensionTier.SUPPORTING

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Analyzes semantic coherence patterns using sentence embeddings to detect "
            "AI-generated text characteristics related to topic consistency, paragraph "
            "cohesion, discourse flow, and conceptual depth. Uses transformer-based "
            "analysis when available, falls back to lexical coherence otherwise."
        )

    # ========================================================================
    # OPTIONAL DEPENDENCY MANAGEMENT
    # ========================================================================

    @classmethod
    def check_availability(cls) -> bool:
        """
        Check if sentence-transformers is installed.

        Returns:
            bool: True if sentence-transformers available, False otherwise
        """
        if cls._model_available is not None:
            return cls._model_available

        try:
            import importlib.util

            cls._model_available = importlib.util.find_spec("sentence_transformers") is not None
            return cls._model_available
        except (ImportError, ModuleNotFoundError):
            cls._model_available = False
            return False

    @classmethod
    @lru_cache(maxsize=1)
    def load_model(cls):
        """
        Lazy load sentence-transformers model (cached, loads only once).

        Returns:
            SentenceTransformer: Model instance if available, None otherwise
        """
        if not cls.check_availability():
            return None

        try:
            from sentence_transformers import SentenceTransformer

            # Use validated model from Story 2.3.0 research
            model = SentenceTransformer("all-MiniLM-L6-v2")
            cls._model = model
            return model
        except Exception:
            # Model loading failed (network, disk, etc.)
            return None

    # ========================================================================
    # TEXT SPLITTING UTILITIES
    # ========================================================================

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Full document text

        Returns:
            List of paragraph strings (non-empty)
        """
        # Split on double newlines, strip whitespace, filter empty
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text)]
        return [p for p in paragraphs if p]

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentence strings (non-empty)
        """
        # Simple sentence splitting on [.!?]+ with whitespace
        # More sophisticated: Use nltk.sent_tokenize if available
        sentences = re.split(r"[.!?]+\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _sample_sentences(self, sentences: List[str], max_count: Optional[int] = None) -> List[str]:
        """
        Sample sentences evenly from document for performance.

        Args:
            sentences: Full sentence list
            max_count: Maximum sentences to keep (default: SAMPLE_SIZE)

        Returns:
            Sampled sentence list (evenly distributed)
        """
        if max_count is None:
            max_count = self.SAMPLE_SIZE

        if len(sentences) <= max_count:
            return sentences

        # Sample evenly distributed sentences
        step = len(sentences) // max_count
        return sentences[::step][:max_count]

    # ========================================================================
    # FALLBACK: BASIC LEXICAL COHERENCE
    # ========================================================================

    def _analyze_basic_coherence(self, text: str) -> Dict[str, Any]:
        """
        Fallback analysis using word overlap (no sentence-transformers).

        Args:
            text: Full document text

        Returns:
            Dict with basic coherence metrics and neutral score
        """
        paragraphs = self._split_paragraphs(text)

        if len(paragraphs) < 2:
            return {
                "method": "basic",
                "available": False,
                "lexical_overlap": 0.0,
                "paragraph_count": len(paragraphs),
                "note": "Insufficient paragraphs for coherence analysis",
            }

        # Calculate word overlap between adjacent paragraphs
        overlap_scores = []
        for i in range(len(paragraphs) - 1):
            words_a = set(paragraphs[i].lower().split())
            words_b = set(paragraphs[i + 1].lower().split())
            if words_a and words_b:
                # Jaccard similarity
                overlap = len(words_a & words_b) / len(words_a | words_b)
                overlap_scores.append(overlap)

        avg_overlap = float(np.mean(overlap_scores)) if overlap_scores else 0.0

        return {
            "method": "basic",
            "available": False,
            "lexical_overlap": avg_overlap,
            "paragraph_count": len(paragraphs),
            "transitions_analyzed": len(overlap_scores),
        }

    # ========================================================================
    # EMBEDDING GENERATION
    # ========================================================================

    def _generate_embeddings(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings for text list using batch processing.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing (default: BATCH_SIZE)

        Returns:
            numpy array of shape (len(texts), 384) or None on error
        """
        model = self.load_model()
        if model is None:
            return None

        if batch_size is None:
            batch_size = self.BATCH_SIZE

        try:
            # Batch encode for performance (5-10× speedup)
            embeddings: np.ndarray = model.encode(
                texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True
            )
            return embeddings
        except Exception:
            # Encoding failed
            return None

    # ========================================================================
    # COHERENCE METRICS
    # ========================================================================

    def _calculate_paragraph_cohesion(
        self, paragraph_embeddings: np.ndarray, sentences_per_paragraph: List[int]
    ) -> float:
        """
        Calculate paragraph cohesion (sentence-level similarity within paragraphs).

        Args:
            paragraph_embeddings: Embeddings for each sentence
            sentences_per_paragraph: Sentence count per paragraph

        Returns:
            float: Mean cohesion score [0.0, 1.0]
        """
        cohesion_scores = []
        offset = 0

        for count in sentences_per_paragraph:
            if count < 2:
                offset += count
                continue

            # Get embeddings for this paragraph
            para_embeddings = paragraph_embeddings[offset : offset + count]

            # Calculate pairwise cosine similarities
            similarities = []
            for i in range(len(para_embeddings)):
                for j in range(i + 1, len(para_embeddings)):
                    vec_a = para_embeddings[i]
                    vec_b = para_embeddings[j]
                    # Cosine similarity
                    sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
                    similarities.append(sim)

            if similarities:
                cohesion_scores.append(np.mean(similarities))

            offset += count

        return float(np.mean(cohesion_scores)) if cohesion_scores else 0.0

    def _calculate_topic_consistency(self, paragraph_embeddings: List[np.ndarray]) -> float:
        """
        Calculate topic consistency (paragraph-to-paragraph similarity).

        Args:
            paragraph_embeddings: List of paragraph embedding vectors

        Returns:
            float: Weighted consistency score [0.0, 1.0]
        """
        if len(paragraph_embeddings) < 2:
            return 0.0

        # Calculate similarity between adjacent paragraphs
        similarities = []
        for i in range(len(paragraph_embeddings) - 1):
            vec_a = paragraph_embeddings[i]
            vec_b = paragraph_embeddings[i + 1]
            sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
            similarities.append(sim)

        # Guard against empty similarities
        if not similarities:
            return 0.0

        # Compute consistency (mean) and smoothness (inverse std)
        mean_sim = np.mean(similarities)
        std_sim = float(np.std(similarities))
        smoothness = 1.0 - min(std_sim, 1.0)  # Cap at 1.0

        # Weighted combination (from Story 2.3 research)
        score = (mean_sim * 0.7) + (smoothness * 0.3)
        return float(score)

    def _calculate_discourse_flow(self, paragraph_embeddings: List[np.ndarray]) -> float:
        """
        Calculate discourse flow (transitions in ideal similarity range).

        Args:
            paragraph_embeddings: List of paragraph embedding vectors

        Returns:
            float: Flow quality score [0.0, 1.0]
        """
        if len(paragraph_embeddings) < 2:
            return 0.0

        # Use general domain thresholds for metric calculation
        ideal_min = self.THRESHOLDS["general"]["discourse_flow"]["ideal_min"]
        ideal_max = self.THRESHOLDS["general"]["discourse_flow"]["ideal_max"]

        # Calculate transition similarities
        similarities = []
        for i in range(len(paragraph_embeddings) - 1):
            vec_a = paragraph_embeddings[i]
            vec_b = paragraph_embeddings[i + 1]
            sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
            similarities.append(sim)

        # Score based on ideal range
        in_range_count = sum(1 for s in similarities if ideal_min <= s <= ideal_max)
        proportion_in_range = in_range_count / len(similarities)

        return float(proportion_in_range)

    def _calculate_conceptual_depth(
        self, paragraph_embeddings: List[np.ndarray], document_embedding: np.ndarray
    ) -> float:
        """
        Calculate conceptual depth (paragraph-to-document alignment).

        Args:
            paragraph_embeddings: List of paragraph embedding vectors
            document_embedding: Overall document embedding

        Returns:
            float: Weighted depth score [0.0, 1.0]
        """
        if not paragraph_embeddings:
            return 0.0

        # Calculate paragraph-to-document similarities
        similarities = []
        for para_emb in paragraph_embeddings:
            sim = np.dot(para_emb, document_embedding) / (
                np.linalg.norm(para_emb) * np.linalg.norm(document_embedding)
            )
            similarities.append(sim)

        # Guard against empty similarities (shouldn't happen due to check above, but defensive)
        if not similarities:
            return 0.0

        # Compute depth (mean similarity) and consistency (inverse std)
        mean_sim = np.mean(similarities)
        std_sim = float(np.std(similarities))
        consistency = 1.0 - min(std_sim, 1.0)

        # Weighted combination (from Story 2.3 research)
        score = (mean_sim * 0.6) + (consistency * 0.4)
        return float(score)

    # ========================================================================
    # EVIDENCE COLLECTION
    # ========================================================================

    def _collect_evidence(
        self,
        paragraphs: List[str],
        paragraph_embeddings: List[np.ndarray],
        sentences_per_paragraph: List[int],
        paragraph_cohesion: float,
        topic_consistency: float,
        discourse_flow: float,
        conceptual_depth: float,
    ) -> Dict[str, List[str]]:
        """
        Collect evidence for low-scoring coherence areas.

        Args:
            paragraphs: List of paragraph texts
            paragraph_embeddings: List of paragraph embeddings
            sentences_per_paragraph: Sentence counts per paragraph
            paragraph_cohesion: Overall cohesion score
            topic_consistency: Overall consistency score
            discourse_flow: Overall flow score
            conceptual_depth: Overall depth score

        Returns:
            Dict with evidence lists (limited to first 10 examples each)
        """
        evidence: Dict[str, List[str]] = {
            "low_cohesion_paragraphs": [],
            "topic_shifts": [],
            "weak_transitions": [],
        }

        # Collect low cohesion paragraphs (paragraph_cohesion < 0.35)
        # Threshold adjusted based on research showing 0.40-0.60 is typical for human writing
        if paragraph_cohesion < 0.35:
            # Calculate per-paragraph cohesion scores
            # For simplicity, just collect first few paragraphs as examples
            # In production, would calculate individual paragraph cohesion scores
            for i, para in enumerate(paragraphs[:10]):
                if sentences_per_paragraph[i] >= 2:
                    # Truncate long paragraphs
                    preview = para[:100] + "..." if len(para) > 100 else para
                    evidence["low_cohesion_paragraphs"].append(f"Para {i+1}: {preview}")
                if len(evidence["low_cohesion_paragraphs"]) >= 5:
                    break

        # Collect topic shifts (adjacent paragraphs with low similarity)
        if topic_consistency < 0.55 and len(paragraph_embeddings) >= 2:
            for i in range(min(len(paragraph_embeddings) - 1, 10)):
                vec_a = paragraph_embeddings[i]
                vec_b = paragraph_embeddings[i + 1]
                sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

                # Identify significant topic shifts (similarity < 0.45)
                if sim < 0.45:
                    para_preview = (
                        paragraphs[i][:80] + "..." if len(paragraphs[i]) > 80 else paragraphs[i]
                    )
                    next_preview = (
                        paragraphs[i + 1][:80] + "..."
                        if len(paragraphs[i + 1]) > 80
                        else paragraphs[i + 1]
                    )
                    evidence["topic_shifts"].append(
                        f"Para {i+1}->{i+2} (sim={sim:.2f}): '{para_preview}' -> '{next_preview}'"
                    )
                if len(evidence["topic_shifts"]) >= 5:
                    break

        # Collect weak transitions (flow outside ideal range)
        if discourse_flow < 0.50 and len(paragraph_embeddings) >= 2:
            ideal_min = self.THRESHOLDS["general"]["discourse_flow"]["ideal_min"]
            ideal_max = self.THRESHOLDS["general"]["discourse_flow"]["ideal_max"]

            for i in range(min(len(paragraph_embeddings) - 1, 10)):
                vec_a = paragraph_embeddings[i]
                vec_b = paragraph_embeddings[i + 1]
                sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

                # Identify transitions outside ideal range
                if sim < ideal_min or sim > ideal_max:
                    issue_type = "too disconnected" if sim < ideal_min else "too repetitive"
                    evidence["weak_transitions"].append(
                        f"Para {i+1}->{i+2} ({issue_type}, sim={sim:.2f})"
                    )
                if len(evidence["weak_transitions"]) >= 5:
                    break

        return evidence

    # ========================================================================
    # MAIN ANALYSIS
    # ========================================================================

    def _analyze_semantic_coherence(self, text: str) -> Dict[str, Any]:
        """
        Full semantic coherence analysis using sentence embeddings.

        Args:
            text: Full document text

        Returns:
            Dict with all coherence metrics
        """
        # Split text
        paragraphs = self._split_paragraphs(text)
        if len(paragraphs) < 2:
            return {
                "method": "semantic",
                "available": True,
                "error": "Insufficient paragraphs",
                "paragraph_count": len(paragraphs),
            }

        # Split into sentences and track paragraph structure
        all_sentences = []
        sentences_per_paragraph = []
        for para in paragraphs:
            sentences = self._split_sentences(para)
            all_sentences.extend(sentences)
            sentences_per_paragraph.append(len(sentences))

        # Track if sampling was needed
        original_sentence_count = len(all_sentences)
        was_sampled = original_sentence_count > self.MAX_SENTENCES_BEFORE_SAMPLING

        # Sample sentences if too many (performance optimization)
        if was_sampled:
            all_sentences = self._sample_sentences(all_sentences)

        # Generate embeddings
        sentence_embeddings = self._generate_embeddings(all_sentences)
        if sentence_embeddings is None:
            # Fall back to basic analysis
            return self._analyze_basic_coherence(text)

        # Generate paragraph embeddings (mean of sentence embeddings)
        paragraph_embeddings = []
        offset = 0
        for count in sentences_per_paragraph:
            if count == 0:
                continue
            # Mean pooling of sentence embeddings for this paragraph
            para_emb = np.mean(sentence_embeddings[offset : offset + count], axis=0)
            paragraph_embeddings.append(para_emb)
            offset += count

        # Generate document embedding (mean of all paragraph embeddings)
        if not paragraph_embeddings:
            return {
                "method": "semantic",
                "available": True,
                "error": "No valid paragraph embeddings generated",
                "paragraph_count": len(paragraphs),
            }
        document_embedding = np.mean(paragraph_embeddings, axis=0)

        # Calculate all 4 metrics
        paragraph_cohesion = self._calculate_paragraph_cohesion(
            sentence_embeddings, sentences_per_paragraph
        )
        topic_consistency = self._calculate_topic_consistency(paragraph_embeddings)
        discourse_flow = self._calculate_discourse_flow(paragraph_embeddings)
        conceptual_depth = self._calculate_conceptual_depth(
            paragraph_embeddings, document_embedding
        )

        # Collect evidence for low-scoring areas
        evidence = self._collect_evidence(
            paragraphs,
            paragraph_embeddings,
            sentences_per_paragraph,
            paragraph_cohesion,
            topic_consistency,
            discourse_flow,
            conceptual_depth,
        )

        return {
            "method": "semantic",
            "available": True,
            "paragraph_count": len(paragraphs),
            "sentence_count": original_sentence_count,
            "sampled": was_sampled,
            "metrics": {
                "paragraph_cohesion": paragraph_cohesion,
                "topic_consistency": topic_consistency,
                "discourse_flow": discourse_flow,
                "conceptual_depth": conceptual_depth,
            },
            # Evidence for detailed reporting
            "low_cohesion_paragraphs": evidence["low_cohesion_paragraphs"],
            "topic_shifts": evidence["topic_shifts"],
            "weak_transitions": evidence["weak_transitions"],
        }

    def analyze(
        self,
        text: str,
        lines: Optional[List[str]] = None,
        config: Optional[AnalysisConfig] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Analyze text for semantic coherence patterns.

        Args:
            text: Full document text
            lines: Text split into lines (unused for this dimension)
            config: Analysis configuration for performance modes (FAST mode)
            **kwargs: Additional parameters (domain, word_count, etc.)

        Returns:
            Dict containing coherence metrics and metadata

        Note:
            Semantic coherence has its own internal sentence sampling (>500 sentences)
            to handle long documents. Config is only used for FAST mode truncation.
        """
        # Only apply config for FAST mode truncation (character limits)
        # Don't use config sampling since we have internal sentence sampling
        if config is not None:
            effective_limit = config.get_effective_limit(self.dimension_name, len(text))
            if effective_limit is not None:
                text = text[:effective_limit]

        # Check model availability and route to appropriate analysis
        if self.check_availability() and self.load_model() is not None:
            result = self._analyze_semantic_coherence(text)
        else:
            result = self._analyze_basic_coherence(text)

        # Calculate score
        score = self.calculate_score(result)
        result["score"] = score

        # Always include standard dimension metadata for consistent API contract
        result["tier"] = self.tier
        result["weight"] = self.weight
        result["tier_mapping"] = self._get_tier_mapping(score)
        result["recommendations"] = self.get_recommendations(score, result)

        return result

    def _get_tier_mapping(self, score: float) -> str:
        """Map score to tier label."""
        tiers = self.get_tiers()
        for tier_name, (min_score, max_score) in tiers.items():
            if min_score <= score <= max_score:
                return tier_name
        return "unknown"

    # ========================================================================
    # SCORING
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate score from coherence metrics using monotonic scoring.

        Migrated to monotonic scoring with domain-aware thresholds in Story 2.4.1 (Group D).

        Research parameters (Story 2.4.0 literature review):
        - Metric: Average semantic coherence (cosine similarity, bounded [0,1])
        - Thresholds adjusted by content type (technical/creative/academic/general)
        - Direction: Increasing (higher coherence = more human-like)
        - Confidence: Medium-High (embedding-based coherence detection)

        Algorithm:
        1. Calculate average of 4 coherence metrics (cohesion, consistency, flow, depth)
        2. Apply domain-specific threshold adjustments
        3. Use monotonic increasing scoring
        4. threshold_low varies by domain (0.50-0.60)
        5. threshold_high varies by domain (0.70-0.78)

        Research findings:
        - Human writing: 0.65-0.80 average coherence (well-connected ideas)
        - AI writing: 0.45-0.60 average coherence (topic drift, weak connections)
        - Technical content requires lower thresholds (domain-specific jargon)

        Args:
            metrics: Output from analyze(), may include 'content_type' key

        Returns:
            float: Score 0-100 (100 = most human-like)
        """
        method = metrics.get("method", "basic")

        # Handle fallback mode (return neutral score)
        if method == "basic" or not metrics.get("available", False):
            score = 50.0  # Neutral score when analysis unavailable
            self._validate_score(score)
            return score

        # Handle errors
        if "error" in metrics:
            score = 50.0
            self._validate_score(score)
            return score

        # Detect content type for domain-aware scoring
        content_type = metrics.get("content_type", "general")
        if content_type not in self.THRESHOLDS:
            content_type = "general"  # Fallback to general if unknown type

        # Get domain-specific thresholds
        domain_thresholds = self.THRESHOLDS[content_type]

        # Extract metrics
        coherence_metrics = metrics.get("metrics", {})
        paragraph_cohesion = coherence_metrics.get("paragraph_cohesion", 0.0)
        topic_consistency = coherence_metrics.get("topic_consistency", 0.0)
        discourse_flow = coherence_metrics.get("discourse_flow", 0.0)
        conceptual_depth = coherence_metrics.get("conceptual_depth", 0.0)

        # Calculate average coherence score
        avg_coherence = (
            paragraph_cohesion + topic_consistency + discourse_flow + conceptual_depth
        ) / 4.0

        # Domain-specific thresholds (using 'acceptable' and 'excellent' from domain config)
        # Average the thresholds across the 4 metrics for simplicity
        threshold_low = (
            domain_thresholds["paragraph_cohesion"]["acceptable"]
            + domain_thresholds["topic_consistency"]["acceptable"]
            + domain_thresholds["discourse_flow"]["acceptable"]
            + domain_thresholds["conceptual_depth"]["acceptable"]
        ) / 4.0

        threshold_high = (
            domain_thresholds["paragraph_cohesion"]["excellent"]
            + domain_thresholds["topic_consistency"]["excellent"]
            + domain_thresholds["discourse_flow"]["excellent"]
            + domain_thresholds["conceptual_depth"]["excellent"]
        ) / 4.0

        # Apply monotonic increasing scoring
        score = self._monotonic_score(
            value=avg_coherence,
            threshold_low=threshold_low,
            threshold_high=threshold_high,
            increasing=True,
        )

        self._validate_score(score)
        return score

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    def get_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on coherence analysis.

        Args:
            score: Calculated score
            metrics: Raw metrics from analyze()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        method = metrics.get("method", "basic")

        # No recommendations for fallback mode
        if method == "basic" or not metrics.get("available", False):
            recommendations.append(
                "Install sentence-transformers for detailed semantic coherence analysis: "
                "pip install ai-pattern-analyzer[semantic]"
            )
            return recommendations

        # Provide metric-specific recommendations
        coherence_metrics = metrics.get("metrics", {})

        if coherence_metrics.get("paragraph_cohesion", 1.0) < 0.35:
            recommendations.append(
                "Improve paragraph cohesion: Ensure sentences within each paragraph "
                "relate to a single topic or theme"
            )

        if coherence_metrics.get("topic_consistency", 1.0) < 0.55:
            recommendations.append(
                "Enhance topic consistency: Reduce abrupt topic changes between paragraphs, "
                "use transitional phrases to connect ideas"
            )

        if coherence_metrics.get("discourse_flow", 1.0) < 0.50:
            recommendations.append(
                "Strengthen discourse flow: Balance paragraph transitions - avoid both "
                "too-similar (repetitive) and too-different (disconnected) adjacent paragraphs"
            )

        if coherence_metrics.get("conceptual_depth", 1.0) < 0.50:
            recommendations.append(
                "Increase conceptual depth: Ensure paragraphs relate meaningfully to "
                "the document's central theme rather than introducing tangential topics"
            )

        if not recommendations:
            recommendations.append("Semantic coherence is strong across all metrics")

        return recommendations

    def format_display(self, metrics: Dict[str, Any]) -> str:
        """Format semantic coherence display for reports."""
        coherence_metrics = metrics.get("metrics", {})
        cohesion = coherence_metrics.get("paragraph_cohesion")
        consistency = coherence_metrics.get("topic_consistency")

        if cohesion is not None and consistency is not None:
            return f"(Cohesion: {cohesion:.2f}, Consistency: {consistency:.2f})"
        return "(N/A)"

    # ========================================================================
    # TIER DEFINITIONS
    # ========================================================================

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """
        Define score tier ranges.

        Returns:
            Dict mapping tier names to (min, max) score ranges
        """
        return {
            "excellent": (90.0, 100.0),
            "good": (75.0, 89.9),
            "acceptable": (60.0, 74.9),
            "poor": (0.0, 59.9),
        }


# Module-level singleton - triggers self-registration on module import
_instance = SemanticCoherenceDimension()
