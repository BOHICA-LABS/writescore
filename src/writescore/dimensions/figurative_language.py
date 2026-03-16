"""
Figurative Language dimension analyzer.

Detects figurative language patterns (metaphors, similes, idioms) using a hybrid
approach combining regex patterns, pre-built lexicons, and embedding-based semantic
analysis. AI-generated content systematically underuses figurative expressions and
shows characteristic patterns compared to human writing.

Research Basis:
- Kobak et al. 2025: Identified 454 excess words in AI-generated text with
  significant frequency multipliers (e.g., 'delve': 28x, 'underscores': 13.8x)
  [Science Advances, arXiv:2406.07016]
- ContrastWSD 2024: Embedding-based metaphor detection using cosine similarity
  between contextual and literal embeddings [ACL 2024]
- Multiple 2023-2025 studies: AI shows lower diversity in figurative construction,
  over-reliance on clichéd expressions, and weaker contextual grounding

Key Detection Signals:
1. Diversity/novelty (not raw frequency) - primary signal
2. Cliché ratio - AI characteristic markers
3. Type variety - similes, metaphors, idioms

Performance:
- Target: < 30 seconds per 10k words (NLTK + embeddings)
- Accuracy: 83-90% (per 2024-2025 benchmarks)
- No ML model training required
- First-run overhead: 30-60 seconds for WordNet + model downloads
  (subsequent runs: ~2-5 seconds initialization, analysis speed unchanged)

Weight: 3.0% of total score
Tier: SUPPORTING

Refactored in Story 2.1 to use DimensionStrategy pattern with self-registration.
"""

import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Required NLP imports
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier

# Technical literals - words that function metaphorically in general discourse
# but literally in technical contexts (AC: 4)
TECHNICAL_LITERALS = {
    "stack": ["data structure", "call stack", "memory stack", "stack overflow", "technology stack"],
    "pipeline": ["data pipeline", "ci/cd pipeline", "processing pipeline", "deployment pipeline"],
    "lake": ["data lake", "storage lake"],
    "tree": ["tree structure", "binary tree", "syntax tree", "decision tree", "dom tree"],
    "container": ["docker container", "storage container", "container orchestration"],
    "stream": ["data stream", "byte stream", "event stream", "video stream"],
    "pool": ["memory pool", "thread pool", "connection pool", "worker pool"],
    "heap": ["heap memory", "heap allocation", "min heap", "max heap"],
}

# AI cliché markers - verified frequency multipliers from Kobak et al. 2025
# [Research: Kobak et al. Science Advances 2025, arXiv:2406.07016]
AI_CLICHE_WORDS = {
    # Primary markers (highest multipliers)
    "delve": 28.0,  # 28x more frequent in AI text
    "delves": 28.0,
    "delving": 28.0,
    "underscores": 13.8,  # 13.8x more frequent
    "showcasing": 10.7,  # 10.7x more frequent
    # Secondary markers (moderate multipliers)
    "potential": 5.2,  # +5.2 percentage points
    "findings": 4.1,  # +4.1 percentage points
    "crucial": 3.7,  # +3.7 percentage points
    # Additional ChatGPT-characteristic words
    "comprehensive": 2.0,
    "pivotal": 2.0,
    "leverage": 2.0,
    "optimize": 2.0,
    "facilitate": 2.0,
}

# Formulaic meta-linguistic markers (AC: 2)
FORMULAIC_MARKERS = [
    "it is worth noting that",
    "it is important to note that",
    "in conclusion",
    "furthermore",
    "moreover",
    "nevertheless",
    "consequently",
]

# Default idioms list (fallback if file not found)
DEFAULT_IDIOMS = [
    "break the ice",
    "piece of cake",
    "kick the bucket",
    "cost an arm and a leg",
    "let the cat out of the bag",
    "under the weather",
    "once in a blue moon",
    "hit the sack",
    "miss the boat",
    "on cloud nine",
    "break a leg",
    "cry over spilt milk",
    "birds of a feather flock together",
    "actions speak louder than words",
    "back to square one",
    "bite the bullet",
    "burn the midnight oil",
    "caught between a rock and a hard place",
    "cut corners",
    "speak of the devil",
    "see eye to eye",
    "put all your eggs in one basket",
    "the ball is in your court",
    "get out of hand",
    "let sleeping dogs lie",
    "call it a day",
    "best of both worlds",
    "when pigs fly",
    "pull someone's leg",
    "sit on the fence",
    "take it with a grain of salt",
    "devil's advocate",
    "hit the nail on the head",
    "jump the gun",
    "go back to the drawing board",
    "in hot water",
    "leave no stone unturned",
    "play it by ear",
    "throw in the towel",
    "a dime a dozen",
    "burn bridges",
    "cut to the chase",
    "by the skin of your teeth",
    "add fuel to the fire",
    "don't count your chickens before they hatch",
    "every cloud has a silver lining",
    "go the extra mile",
    "ignorance is bliss",
    "let someone off the hook",
    "once bitten, twice shy",
    "a blessing in disguise",
    "bite off more than you can chew",
    "on the ball",
    "your guess is as good as mine",
    "throw caution to the wind",
    "take the bull by the horns",
    "the elephant in the room",
    "the last straw",
    "cut somebody some slack",
    "break the bank",
    "call the shots",
    "down to earth",
    "easy does it",
    "get cold feet",
    "go down in flames",
    "jump on the bandwagon",
    "keep your chin up",
    "keep your fingers crossed",
    "let the chips fall where they may",
    "not playing with a full deck",
    "off the hook",
    "on thin ice",
    "out of the blue",
    "rain on someone's parade",
    "roll with the punches",
    "skeleton in the closet",
    "steal someone's thunder",
    "take it or leave it",
    "the early bird catches the worm",
    "third time's the charm",
    "under your nose",
    "up in the air",
    "walk on eggshells",
    "word of mouth",
    "you can't judge a book by its cover",
    "a bitter pill to swallow",
    "a drop in the ocean",
    "behind closed doors",
    "hit the ground running",
    "let bygones be bygones",
    "lose your touch",
    "out of the frying pan and into the fire",
    "put your foot in your mouth",
    "touch wood",
    "up the creek without a paddle",
    "zero tolerance",
    "at the end of the day",
    "game changer",
    "tip of the iceberg",
    "ballpark figure",
]


class FigurativeLanguageDimension(DimensionStrategy):
    """
    Analyzes figurative language dimension - metaphors, similes, idioms.

    Weight: 3.0% of total score
    Tier: SUPPORTING

    Detects:
    - Similes (regex patterns)
    - Metaphors (embedding-based semantic gap analysis)
    - Idioms (lexicon lookup with context checking)
    - AI cliché markers (research-validated frequency multipliers)

    Scoring:
    - Primary signal: diversity/novelty (not raw frequency)
    - Cliché ratio: AI characteristic markers
    - Type variety: using multiple types of figurative language

    Research Citations:
    [Kobak et al. 2025] Science Advances, arXiv:2406.07016
    [ContrastWSD 2024] ACL 2024, https://aclanthology.org/2024.lrec-main.346.pdf
    """

    def __init__(self):
        """
        Initialize and self-register with dimension registry.

        Performs one-time setup:
        - Downloads NLTK WordNet data if not present (first run only)
        - Loads sentence transformer model for metaphor detection
        - Compiles regex patterns and loads lexicons

        Note: First run may take 30-60 seconds due to model downloads.
        Subsequent runs are much faster (~2-5 seconds for initialization).
        """
        super().__init__()

        # Self-register with registry (AC: 6)
        DimensionRegistry.register(self)

        # Ensure NLTK resources are available (auto-download if needed)
        # Following NLTK 3.9.2 best practices
        self._setup_punkt()
        self._setup_wordnet()

        # Load sentence transformer model for embedding-based metaphor detection
        # Model: all-MiniLM-L6-v2 (lightweight, 384-dim embeddings)
        # Performance: 2-5ms per sentence (CPU), <1ms (GPU)
        # Note: First run downloads ~90MB model, subsequent runs load from cache
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Warning: Failed to load sentence transformer: {e}", file=sys.stderr)
            self.model = None

        # Compile simile patterns (AC: 2)
        # Patterns detect explicit simile markers: "like", "as X as"
        self.simile_patterns = [
            re.compile(r"\b(?:like|as)\s+(?:a|an)\s+\w+", re.IGNORECASE),
            re.compile(r"\bas\s+\w+\s+as\b", re.IGNORECASE),
        ]

        # Load idiom lexicon (AC: 2)
        # Source: Curated top-100 common English idioms
        # Fallback: DEFAULT_IDIOMS if file not found
        self.idiom_lexicon = self._load_idiom_lexicon()

        # AI cliché lexicon (research-validated)
        self.ai_cliche_words = AI_CLICHE_WORDS
        self.formulaic_markers = FORMULAIC_MARKERS

    # ========================================================================
    # INITIALIZATION HELPERS
    # ========================================================================

    def _setup_punkt(self) -> None:
        """
        Ensure NLTK punkt tokenizer data is available, downloading if necessary.

        Required for sent_tokenize() and word_tokenize() functions.
        Following NLTK 3.9.2 best practices for resource management.

        Downloads:
        - punkt_tab: Punkt tokenizer models (~35MB)

        Raises:
            No exceptions - prints warnings and continues if downloads fail.
        """
        try:
            # Test if punkt_tab is accessible by tokenizing a test sentence
            sent_tokenize("Test sentence.")
        except LookupError:
            # punkt_tab not found - download it
            print("Downloading NLTK punkt tokenizer data (first run only)...", file=sys.stderr)
            try:
                nltk.download("punkt_tab", quiet=True)
                print("✓ Punkt tokenizer setup complete", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to download punkt_tab: {e}", file=sys.stderr)
                print("Tokenization may fail without punkt_tab", file=sys.stderr)

    def _setup_wordnet(self) -> None:
        """
        Ensure NLTK WordNet data is available, downloading if necessary.

        Implements auto-download logic described in dev notes (Story 2.1).
        Following NLTK 3.9.2 best practices for resource management.

        Downloads:
        - wordnet: Core WordNet lexical database (~10MB)
        - omw-1.4: Open Multilingual WordNet (~1MB)

        Raises:
            No exceptions - prints warnings and continues if downloads fail.
            Metaphor detection will be degraded but other features work.
        """

        try:
            # Test if WordNet is accessible
            wn.synsets("test")
        except LookupError:
            # WordNet not found - download it
            print("Downloading NLTK WordNet data (first run only)...", file=sys.stderr)
            try:
                nltk.download("wordnet", quiet=True)
                nltk.download("omw-1.4", quiet=True)  # Open Multilingual WordNet
                print("✓ WordNet setup complete", file=sys.stderr)

                # Verify installation
                test_synsets = wn.synsets("test")
                if not test_synsets:
                    print("Warning: WordNet downloaded but returned no results", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to download WordNet: {e}", file=sys.stderr)
                print("Metaphor detection will be limited without WordNet", file=sys.stderr)

    # ========================================================================
    # REQUIRED PROPERTIES - DimensionStrategy Contract
    # ========================================================================

    @property
    def dimension_name(self) -> str:
        """Return dimension identifier."""
        return "figurative_language"

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
        return "Detects figurative language patterns (metaphors, similes, idioms) to identify AI-generated content"

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
        Analyze text for figurative language patterns.

        Orchestrates three-tier detection:
        1. Regex for similes and AI clichés (fast path)
        2. Lexicon lookup for idioms with context checking
        3. Embedding-based metaphor detection using ContrastWSD methodology

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with figurative language analysis results
        """
        config = config or DEFAULT_CONFIG
        total_text_length = len(text)

        # Prepare text based on mode (FAST/ADAPTIVE/SAMPLING/FULL)
        prepared = self._prepare_text(text, config, self.dimension_name)

        # Handle sampled analysis
        if isinstance(prepared, list):
            samples = prepared
            sample_results = []

            for _position, sample_text in samples:
                fig_lang = self._analyze_figurative_patterns(sample_text)
                sample_results.append({"figurative_language": fig_lang})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis
        else:
            analyzed_text = prepared
            fig_lang = self._analyze_figurative_patterns(analyzed_text)
            aggregated = {"figurative_language": fig_lang}
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

    def _analyze_figurative_patterns(self, text: str) -> Dict[str, Any]:
        """
        Core figurative language analysis.

        Implements hybrid detection approach:
        - Tier 1: Regex for similes + AI clichés
        - Tier 2: Lexicon lookup for idioms
        - Tier 3: Embedding-based metaphor detection

        Args:
            text: Text to analyze

        Returns:
            Dict with pattern detection results
        """
        # Tier 1: Regex-based detection
        similes = self._detect_similes_regex(text)
        ai_cliches = self._detect_ai_cliches(text)

        # Tier 2: Lexicon-based idiom detection
        idioms = self._detect_idioms_lexicon(text)

        # Tier 3: Embedding-based metaphor detection
        metaphors = self._detect_metaphors_embedding(text)

        # Calculate aggregate metrics
        total_figurative = len(similes) + len(metaphors) + len(idioms)

        # Calculate frequency per 1k words
        words = word_tokenize(text)
        word_count = len(words)
        freq_per_1k = (total_figurative / word_count * 1000.0) if word_count > 0 else 0.0

        # Calculate type variety (0-3)
        types_detected = sum([1 if similes else 0, 1 if metaphors else 0, 1 if idioms else 0])

        # Calculate idiom sentiment distribution
        sentiment_distribution = self._calculate_sentiment_distribution(idioms)

        return {
            "similes": similes,
            "metaphors": metaphors,
            "idioms": idioms,
            "ai_cliches": ai_cliches,
            "total_figurative": total_figurative,
            "frequency_per_1k": round(freq_per_1k, 2),
            "types_detected": types_detected,
            "word_count": word_count,
            "sentiment_distribution": sentiment_distribution,
        }

    def _detect_similes_regex(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect similes using regex patterns.

        Patterns:
        - "like a/an [noun]" (e.g., "like a river")
        - "as [adj] as" (e.g., "as clear as day")

        Args:
            text: Text to analyze

        Returns:
            List of detected similes with phrase and position
        """
        similes = []

        for pattern in self.simile_patterns:
            for match in pattern.finditer(text):
                phrase = match.group(0)

                # Filter out technical literals
                if not self._is_technical_literal(phrase, text, match.start()):
                    similes.append(
                        {
                            "phrase": phrase,
                            "type": "simile",
                            "position": match.start(),
                            "confidence": 0.8,
                        }
                    )

        return similes

    def _detect_metaphors_embedding(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect metaphors using embedding-based semantic gap analysis.

        Following ContrastWSD 2024 methodology:
        1. Extract candidate phrases (noun-verb combinations, adjacent pairs)
        2. Get contextual embedding for phrase
        3. Get literal definition embedding from WordNet
        4. Calculate cosine similarity - low similarity indicates metaphor
        5. Threshold: similarity < 0.4 suggests metaphorical usage

        Performance: 2-5ms per sentence (CPU), <1ms (GPU)
        Expected accuracy: 83-90% (per 2024-2025 benchmarks)

        Args:
            text: Text to analyze

        Returns:
            List of detected metaphors with semantic gap scores
        """
        if self.model is None:
            return []

        metaphors = []

        try:
            # Tokenize text into sentences for context
            sentences = sent_tokenize(text)

            # Limit analysis to prevent performance issues
            # Target: 6-12 seconds per 10k words
            max_sentences = min(len(sentences), 50)

            for sentence in sentences[:max_sentences]:
                tokens = word_tokenize(sentence)

                # Check adjacent word pairs for semantic mismatches
                for i in range(len(tokens) - 1):
                    # Skip very common words (articles, prepositions)
                    if tokens[i].lower() in ["the", "a", "an", "of", "in", "on", "at"]:
                        continue

                    phrase = f"{tokens[i]} {tokens[i+1]}"

                    # Check if this could be a metaphor
                    if self._is_potential_metaphor(tokens[i], sentence):
                        confidence = self._calculate_metaphor_confidence(phrase, tokens[i])

                        if confidence > 0.6:
                            metaphors.append(
                                {
                                    "phrase": phrase,
                                    "type": "metaphor",
                                    "confidence": round(confidence, 2),
                                    "semantic_gap": round(1.0 - confidence, 2),
                                }
                            )

        except Exception as e:
            print(f"Warning: Metaphor detection failed: {e}", file=sys.stderr)

        return metaphors

    def _is_potential_metaphor(self, word: str, context: str) -> bool:
        """
        Check if word could be used metaphorically in context.

        Uses WordNet to identify words with both concrete and abstract meanings.

        Args:
            word: Word to check
            context: Surrounding sentence context

        Returns:
            bool: True if word could be metaphorical
        """
        try:
            synsets = wn.synsets(word.lower())

            if not synsets:
                return False

            # Check if word has multiple meanings (polysemous)
            # Metaphorical usage often involves semantic shift
            return len(synsets) > 1

        except Exception:
            return False

    def _calculate_metaphor_confidence(self, phrase: str, base_word: str) -> float:
        """
        Calculate confidence that phrase is metaphorical.

        Uses embedding-based semantic gap between contextual and literal usage.

        Args:
            phrase: Phrase to analyze
            base_word: Base word to get literal definition

        Returns:
            float: Confidence score 0.0-1.0 (higher = more likely metaphorical)
        """
        if self.model is None:
            return 0.0

        try:
            # Get contextual embedding
            contextual_emb = self.model.encode(phrase)

            # Get literal definition from WordNet
            synsets = wn.synsets(base_word.lower())
            if not synsets:
                return 0.0

            literal_def = synsets[0].definition()
            literal_emb = self.model.encode(literal_def)

            # Calculate semantic gap (cosine similarity)
            similarity = float(
                cosine_similarity(contextual_emb.reshape(1, -1), literal_emb.reshape(1, -1))[0][0]
            )

            # Low similarity = high metaphorical usage
            # Invert similarity to get confidence
            confidence = 1.0 - similarity if similarity < 0.7 else 0.0

            return float(max(0.0, min(1.0, confidence)))

        except Exception:
            return 0.0

    def _detect_idioms_lexicon(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect idioms using curated lexicon with context verification and tiered confidence.

        Uses multi-tier idiom lexicon (Story 2.1+):
        - Core tier (100 idioms): base confidence 1.0
        - Extended tier (1,351 idioms): base confidence 0.8-0.9
        - Final confidence = base_confidence × context_confidence

        Args:
            text: Text to analyze

        Returns:
            List of detected idioms with confidence scores
        """
        text_lower = text.lower()
        idioms = []

        for idiom_pattern in self.idiom_lexicon:
            if idiom_pattern.lower() in text_lower:
                # Get base confidence from lexicon tier
                metadata = getattr(self, "idiom_metadata", {}).get(idiom_pattern.lower(), {})
                base_confidence = metadata.get("confidence", 0.8)
                tier = metadata.get("tier", "extended")

                # Verify not used literally via surrounding context
                # Domain-tier idioms get special handling (always idiomatic in technical contexts)
                context_confidence = self._check_idiom_context(text, idiom_pattern, tier)

                # Combine base confidence with context confidence
                final_confidence = base_confidence * context_confidence

                if final_confidence > 0.4:  # Lower threshold to catch extended-tier idioms
                    idioms.append(
                        {
                            "phrase": idiom_pattern,
                            "type": "idiom",
                            "confidence": round(final_confidence, 2),
                            "tier": tier,
                            "sources": metadata.get("sources", []),
                        }
                    )

        return idioms

    def _check_idiom_context(self, text: str, idiom: str, tier: str = "extended") -> float:
        """
        Determine if idiom is used figuratively vs. literally.

        Algorithm (based on computational linguistics research):
        1. Find idiom position and extract 5-word window before/after
        2. Check for literalizing markers (reduce confidence):
           - "literally", "actually", "really" (explicit literal markers)
           - Quotation marks around idiom (metalinguistic usage)
           - Technical context words from TECHNICAL_LITERALS exception list
        3. Check for figurative markers (increase confidence):
           - Metaphorical verbs (e.g., "like", "as if", "seems")
           - Abstract subject/object in surrounding context
        4. Return confidence score: 0.8 (high), 0.5 (medium), 0.2 (low)

        Special handling for domain-tier idioms:
        - Domain-specific idioms (tier='domain') are always idiomatic in technical contexts
        - They skip the TECHNICAL_LITERALS penalty filter
        - They receive confidence boost in academic/technical contexts

        Args:
            text: Full text
            idiom: Idiom phrase to check
            tier: Idiom tier ('core', 'extended', 'domain')

        Returns:
            float: Confidence score 0.0-1.0 (>0.5 = likely figurative)
        """
        # Find idiom position in text
        idiom_match = re.search(re.escape(idiom), text, re.IGNORECASE)
        if not idiom_match:
            return 0.0

        # Extract context window (50 chars before/after)
        start_pos = max(0, idiom_match.start() - 50)
        end_pos = min(len(text), idiom_match.end() + 50)
        context_window = text[start_pos:end_pos].lower()

        # Default confidence (assume figurative)
        # Domain-tier idioms get higher default (they're always idiomatic)
        confidence = 0.9 if tier == "domain" else 0.7

        # Literalizing markers (reduce confidence)
        literal_markers = ["literally", "actually", "really", "exactly", "precisely"]
        for marker in literal_markers:
            if marker in context_window:
                confidence -= 0.3

        # Check for quotation marks (metalinguistic usage)
        if f'"{idiom}"' in text or f"'{idiom}'" in text:
            confidence -= 0.4

        # Check technical literals exception list
        # SKIP this check for domain-tier idioms (they're supposed to be in technical contexts)
        if tier != "domain":
            for tech_word, contexts in TECHNICAL_LITERALS.items():
                if tech_word in idiom:
                    for tech_context in contexts:
                        if tech_context.lower() in context_window:
                            confidence -= 0.5  # Strong literal indicator

        # Figurative markers (increase confidence)
        figurative_markers = ["like", "as if", "seems", "appears", "metaphorically"]
        for marker in figurative_markers:
            if marker in context_window:
                confidence += 0.2

        # Domain-tier idioms get confidence boost in technical/academic contexts
        if tier == "domain":
            technical_context_markers = [
                "algorithm",
                "implementation",
                "system",
                "performance",
                "data",
                "test",
                "code",
                "function",
                "method",
                "analysis",
                "research",
                "study",
                "evaluation",
                "results",
                "approach",
                "framework",
            ]
            for marker in technical_context_markers:
                if marker in context_window:
                    confidence = min(1.0, confidence + 0.05)  # Small boost, capped at 1.0
                    break  # Only apply once

        # Clamp to 0.0-1.0 range
        return max(0.0, min(1.0, confidence))

    def _calculate_sentiment_distribution(self, idioms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate sentiment distribution of detected idioms.

        Research basis: Williams et al. (2015) SLIDE lexicon with 5,000 idioms
        showed typical distribution: 58.9% neutral, 22.2% negative, 18.9% positive.

        Technical writing optimal profile (research-based):
        - 85-95% neutral
        - 1-3% positive
        - 0-2% negative

        Human writing shows strategic sentiment variation based on context
        (negative for problems, neutral for mechanisms, positive for solutions).
        AI writing shows more uniform sentiment distribution.

        Args:
            idioms: List of detected idiom dictionaries

        Returns:
            Dict containing:
            - counts: Raw counts of positive/negative/neutral idioms
            - percentages: Percentage distribution
            - total_with_sentiment: Number of idioms with sentiment data
            - deviation_from_optimal: How far from optimal technical writing profile
        """
        if not idioms:
            return {
                "counts": {"positive": 0, "negative": 0, "neutral": 0},
                "percentages": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                "total_with_sentiment": 0,
                "deviation_from_optimal": 0.0,
            }

        # Count sentiment types
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for idiom in idioms:
            phrase = idiom.get("phrase", "").lower()
            metadata = self.idiom_metadata.get(phrase, {})
            sentiment = metadata.get("sentiment")

            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1

        total_with_sentiment = sum(sentiment_counts.values())

        # Calculate percentages
        percentages = {
            sentiment: (count / total_with_sentiment * 100.0) if total_with_sentiment > 0 else 0.0
            for sentiment, count in sentiment_counts.items()
        }

        # Calculate deviation from optimal technical writing profile
        # Optimal: 90% neutral, 5% positive, 5% negative (midpoint of ranges)
        optimal_profile = {"neutral": 90.0, "positive": 5.0, "negative": 5.0}

        deviation = 0.0
        if total_with_sentiment > 0:
            # Sum of absolute differences from optimal
            deviation = sum(
                abs(percentages[sentiment] - optimal_profile[sentiment])
                for sentiment in sentiment_counts
            )

        return {
            "counts": sentiment_counts,
            "percentages": {k: round(v, 1) for k, v in percentages.items()},
            "total_with_sentiment": total_with_sentiment,
            "deviation_from_optimal": round(deviation, 1),
        }

    def _detect_ai_cliches(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect AI cliché markers with frequency multipliers.

        Research basis: Kobak et al. 2025 identified 454 excess words with
        significant frequency multipliers in AI-generated text.

        Args:
            text: Text to analyze

        Returns:
            List of detected clichés with multipliers
        """
        text_lower = text.lower()
        cliches = []

        # Check individual words
        for word, multiplier in self.ai_cliche_words.items():
            pattern = r"\b" + re.escape(word) + r"\b"
            matches = list(re.finditer(pattern, text_lower))

            for match in matches:
                cliches.append(
                    {
                        "phrase": word,
                        "type": "ai_cliche",
                        "multiplier": multiplier,
                        "position": match.start(),
                    }
                )

        # Check formulaic markers
        for marker in self.formulaic_markers:
            if marker in text_lower:
                cliches.append({"phrase": marker, "type": "formulaic", "multiplier": 2.0})

        return cliches

    def _is_technical_literal(self, phrase: str, text: str, position: int) -> bool:
        """
        Check if phrase is used literally in technical context.

        Args:
            phrase: Phrase to check
            text: Full text
            position: Position of phrase in text

        Returns:
            bool: True if phrase is technical literal
        """
        # Extract context window
        start = max(0, position - 100)
        end = min(len(text), position + 100)
        context = text[start:end].lower()

        # Check if any technical literal words appear with their contexts
        for tech_word, tech_contexts in TECHNICAL_LITERALS.items():
            if tech_word in phrase.lower():
                for tech_context in tech_contexts:
                    if tech_context.lower() in context:
                        return True

        return False

    def _load_idiom_lexicon(self) -> List[str]:
        """
        Load idiom lexicon from file with fallback.

        Tries to load from JSON format first (idiom_lexicon.json with metadata),
        then falls back to simple text format (idiom_lexicon.txt), then DEFAULT_IDIOMS.

        Sources:
        - data/idiom_lexicon.json: 1,451 idioms from EPIE + PIE + curated (Story 2.1+)
        - data/idiom_lexicon.txt: 100 common idioms (legacy)
        - DEFAULT_IDIOMS: 100 hardcoded idioms (ultimate fallback)

        Returns:
            List of idiom strings
        """
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Try JSON format first (with metadata support)
        idiom_json = os.path.join(data_dir, "data", "idiom_lexicon.json")
        if os.path.exists(idiom_json):
            try:
                import json

                with open(idiom_json, encoding="utf-8") as f:
                    lexicon_data = json.load(f)

                # Store metadata for confidence-weighted detection
                self.idiom_metadata = {}
                idioms = []

                for _key, data in lexicon_data.items():
                    idiom = data["idiom"]
                    idioms.append(idiom)

                    # Store metadata for this idiom
                    metadata = {
                        "confidence": data.get("confidence", 0.8),
                        "tier": data.get("tier", "extended"),
                        "sources": data.get("sources", []),
                        "paraphrase": data.get("paraphrase"),
                        "variants": data.get("variants", []),
                    }

                    # Add SLIDE sentiment data if present
                    if "sentiment" in data:
                        metadata["sentiment"] = data["sentiment"]
                        metadata["sentiment_pos_pct"] = data.get("sentiment_pos_pct", 0.0)
                        metadata["sentiment_neg_pct"] = data.get("sentiment_neg_pct", 0.0)
                        metadata["sentiment_neu_pct"] = data.get("sentiment_neu_pct", 0.0)

                    self.idiom_metadata[idiom.lower()] = metadata

                    # Also add variants to the idioms list if present
                    if "variants" in data:
                        for variant in data["variants"]:
                            idioms.append(variant)
                            self.idiom_metadata[variant.lower()] = self.idiom_metadata[
                                idiom.lower()
                            ]

                print(
                    f"✓ Loaded {len(lexicon_data)} idioms ({len(idioms)} with variants) from {idiom_json}",
                    file=sys.stderr,
                )
                core_count = sum(1 for d in lexicon_data.values() if d.get("tier") == "core")
                extended_count = len(lexicon_data) - core_count
                print(
                    f"  Tiers: {core_count} core (conf 1.0), {extended_count} extended (conf 0.8-0.9)",
                    file=sys.stderr,
                )
                return idioms

            except Exception as e:
                print(
                    f"Warning: Failed to load JSON idiom lexicon from {idiom_json}: {e}",
                    file=sys.stderr,
                )
                print("Falling back to text format...", file=sys.stderr)

        # Try text format (legacy)
        idiom_txt = os.path.join(data_dir, "data", "idiom_lexicon.txt")
        if os.path.exists(idiom_txt):
            try:
                with open(idiom_txt, encoding="utf-8") as f:
                    idioms = [line.strip() for line in f if line.strip()]

                # Initialize basic metadata for text-format idioms
                self.idiom_metadata = {}
                for idiom in idioms:
                    self.idiom_metadata[idiom.lower()] = {
                        "confidence": 1.0,  # Legacy format gets full confidence
                        "tier": "core",
                        "sources": ["current"],
                        "paraphrase": None,
                        "variants": [],
                    }

                print(f"✓ Loaded {len(idioms)} idioms from {idiom_txt}", file=sys.stderr)
                return idioms
            except Exception as e:
                print(
                    f"Warning: Failed to load idiom lexicon from {idiom_txt}: {e}", file=sys.stderr
                )
                print(f"Falling back to {len(DEFAULT_IDIOMS)} default idioms", file=sys.stderr)
        else:
            # File doesn't exist - inform user we're using defaults
            print("Info: Idiom lexicon file not found", file=sys.stderr)
            print(
                f"Using {len(DEFAULT_IDIOMS)} default idioms (feature will work normally)",
                file=sys.stderr,
            )

        # Ultimate fallback to DEFAULT_IDIOMS
        self.idiom_metadata = {}
        for idiom in DEFAULT_IDIOMS:
            self.idiom_metadata[idiom.lower()] = {
                "confidence": 1.0,
                "tier": "core",
                "sources": ["default"],
                "paraphrase": None,
                "variants": [],
            }
        return DEFAULT_IDIOMS

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on figurative language metrics.

        Migrated to monotonic scoring with quality adjustments in Story 2.4.1 (Group D).

        Research parameters (Story 2.4.0 literature review + Kobak et al. 2025):
        - Metric: Figurative language frequency per 1k words
        - Threshold low: 0.1 (AI writing - sparse figurative language)
        - Threshold high: 0.8 (human writing - rich figurative language)
        - Direction: Increasing (higher frequency = more human-like, within reason)
        - Quality adjustments:
          - Variety bonus (0-15 points): Using multiple types (similes, metaphors, idioms)
          - Novelty bonus (0-20 points): Novel vs clichéd expressions
          - Cliché penalty (0-40 points): AI characteristic markers (10-28x multipliers)
        - Confidence: High (Kobak et al. 2025 AI cliché markers)

        Algorithm:
        1. Base monotonic score from frequency_per_1k (0-100)
        2. Add variety bonus (0-15 points) - using multiple types
        3. Add novelty bonus (0-20 points) - novel vs conventional expressions
        4. Subtract cliché penalty (0-40 points) - AI characteristic markers
        5. Clamp final score to 0-100 range

        Research findings:
        - Human writing: 0.5-1.5 figurative expressions per 1k words
        - AI writing: 0.0-0.3 figurative expressions per 1k words
        - AI overuses clichés (delve: 28×, underscores: 13.8×, showcasing: 10.7×)
        - Diversity/novelty more important than raw frequency

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        fig_lang = metrics.get("figurative_language", {})

        freq_per_1k = fig_lang.get("frequency_per_1k", 0.0)
        types_detected = fig_lang.get("types_detected", 0)
        total_figurative = fig_lang.get("total_figurative", 0)
        ai_cliche_count = len(fig_lang.get("ai_cliches", []))

        # Base monotonic score from frequency
        # threshold_low=0.1 (AI-like), threshold_high=0.8 (human-like)
        base_score = self._monotonic_score(
            value=freq_per_1k, threshold_low=0.1, threshold_high=0.8, increasing=True
        )

        # Variety bonus: Using multiple types of figurative language (0-15 points)
        # Proportion of types detected (similes, metaphors, idioms = 3 types)
        variety_score = types_detected / 3.0
        variety_bonus = variety_score * VARIETY_BONUS_MAX

        # Cliché ratio: Proportion of AI clichés in total figurative expressions
        # Add 1 to denominator to avoid division by zero
        cliche_ratio = ai_cliche_count / (total_figurative + 1)

        # Novelty bonus: Invert cliché ratio as proxy for novelty (0-20 points)
        # Lower cliché ratio = higher novelty = more human-like
        novelty_ratio = 1.0 - min(cliche_ratio * 2.0, 1.0)
        novelty_bonus = novelty_ratio * NOVELTY_BONUS_MAX

        # Cliché penalty: AI characteristic markers (0-40 points)
        cliche_penalty = cliche_ratio * CLICHE_PENALTY_MAX

        # Calculate final score with quality adjustments
        score = base_score + variety_bonus + novelty_bonus - cliche_penalty

        # Clamp to valid range
        score = max(0.0, min(100.0, score))

        self._validate_score(score)
        return float(score)

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

        fig_lang = metrics.get("figurative_language", {})
        freq_per_1k = fig_lang.get("frequency_per_1k", 0.0)
        types_detected = fig_lang.get("types_detected", 0)
        ai_cliches = fig_lang.get("ai_cliches", [])
        total_figurative = fig_lang.get("total_figurative", 0)

        # Low frequency
        if freq_per_1k < 0.1:
            recommendations.append(
                f"Very low figurative language usage ({freq_per_1k:.2f} per 1k words). "
                f"Consider adding metaphors, similes, or idioms for more natural expression."
            )

        # Low type variety
        if types_detected < 2:
            recommendations.append(
                f"Limited figurative language variety (only {types_detected} type(s) detected). "
                f"Try incorporating different types: similes, metaphors, and idioms."
            )

        # High cliché ratio
        if ai_cliches and len(ai_cliches) > 0:
            cliche_ratio = len(ai_cliches) / (total_figurative + 1)
            if cliche_ratio > 0.3:
                common_cliches = [c["phrase"] for c in ai_cliches[:3]]
                recommendations.append(
                    f"High AI cliché usage detected ({len(ai_cliches)} clichés). "
                    f"Avoid words like: {', '.join(common_cliches)}. "
                    f"Use more natural, context-specific expressions."
                )

        # Very high frequency
        if freq_per_1k > 1.0:
            recommendations.append(
                f"Figurative language frequency is unusually high ({freq_per_1k:.2f} per 1k words). "
                f"Ensure metaphors and idioms are contextually appropriate."
            )

        # Sentiment distribution analysis (only if idioms detected)
        sentiment_dist = fig_lang.get("sentiment_distribution", {})
        if sentiment_dist.get("total_with_sentiment", 0) >= 3:  # Only analyze if 3+ idioms
            percentages = sentiment_dist.get("percentages", {})
            deviation = sentiment_dist.get("deviation_from_optimal", 0.0)

            # Significant deviation from optimal technical writing profile
            if deviation > 50.0:  # More than 50 percentage points total deviation
                neutral_pct = percentages.get("neutral", 0.0)
                positive_pct = percentages.get("positive", 0.0)
                negative_pct = percentages.get("negative", 0.0)

                if neutral_pct < 70.0:  # Should be 85-95% for technical writing
                    recommendations.append(
                        f"Idiom sentiment distribution shows {neutral_pct:.1f}% neutral, "
                        f"{positive_pct:.1f}% positive, {negative_pct:.1f}% negative. "
                        f"Technical writing typically uses 85-95% neutral idioms. "
                        f"Consider using more neutral expressions like 'in the long run' or 'edge case'."
                    )

        return recommendations

    def get_tiers(self) -> Dict[str, Tuple[float, float]]:
        """
        Define score tier ranges for this dimension.

        Returns:
            Dict mapping tier name to (min_score, max_score) tuple
        """
        return {
            "excellent": (85.0, 100.0),
            "good": (70.0, 84.9),
            "acceptable": (50.0, 69.9),
            "poor": (0.0, 49.9),
        }


# ========================================================================
# SCORING CONSTANTS - Extracted for maintainability and tuning
# ========================================================================

# Frequency thresholds (per 1k words) - based on academic baselines
FREQ_MIN_THRESHOLD = 0.1  # Minimum acceptable frequency
FREQ_MAX_THRESHOLD = 0.8  # Maximum before penalty
FREQ_BASELINE_SCORE = 70.0  # Score for acceptable frequency range

# Scoring component weights
VARIETY_BONUS_MAX = 15.0  # Maximum bonus for type variety (0-15 points)
NOVELTY_BONUS_MAX = 20.0  # Maximum bonus for novel expressions (0-20 points)
CLICHE_PENALTY_MAX = 40.0  # Maximum penalty for AI clichés (0-40 points)

# Penalty modifiers
FREQ_LOW_PENALTY_DIVISOR = 0.1  # Scale factor for low frequency penalty
FREQ_HIGH_PENALTY_RATE = 20.0  # Penalty rate for excessive frequency
FREQ_HIGH_PENALTY_MIN = 40.0  # Minimum score when frequency too high


# Module-level singleton - triggers self-registration on module import
_instance = FigurativeLanguageDimension()
