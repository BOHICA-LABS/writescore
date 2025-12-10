"""
Pragmatic Markers dimension analyzer.

Analyzes epistemic stance and pragmatic communication patterns across 9 categories:
- Epistemic hedging patterns (43 patterns: might, may, could, seem, appear, etc.)
- Frequency hedges (6 patterns: frequently, occasionally, sometimes, often, rarely, seldom)
- Epistemic verbs (8 patterns: assume, estimate, indicate, speculate, propose, claim, argue, suggest)
- Strong certainty markers (18 patterns: definitely, certainly, always, never, etc.)
- Subjective certainty (8 patterns: I believe, We know, It is clear, etc.)
- Assertion acts (10 patterns: demonstrate, show, prove, confirm, etc.)
- Formulaic AI acts (4 patterns: it can be argued, one might argue, etc.)
- Attitude markers (18 patterns: surprisingly, unfortunately, importantly, etc.) - NEW in v6.1.0
- Likelihood adverbials (11 patterns: probably, apparently, seemingly, etc.) - NEW in v6.1.0

Total: 126 patterns (expanded from 52 in Story 2.6)

Extracted from transition_marker.py in Story 2.4.0.5, expanded in Story 2.6.

Weight: 4.0%
Tier: ADVANCED

Human writers: Moderate epistemic hedging (5-9/1k), balanced certainty (2-5/1k), personal speech acts (3-6/1k)
AI writers: Excessive hedging (12-18/1k), imbalanced certainty (<1 or >8/1k), formulaic speech acts (>60%)

Requires dependencies: re (standard library)

Version History:
- v1.0.0 (v6.0.0): Initial extraction from transition_marker.py - Story 2.4.0.5
- v2.0.0 (v6.1.0): Expanded from 52 to 126 patterns - Story 2.6
  - Added 23 epistemic hedges (Hyland, BioScope)
  - Added 12 strong certainty markers (LIWC, Hyland)
  - Added 4 subjective certainty patterns
  - Added 6 assertion act verbs
  - NEW: ATTITUDE_MARKERS category (18 patterns)
  - NEW: LIKELIHOOD_ADVERBIALS category (11 patterns)
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier


class PragmaticMarkersDimension(DimensionStrategy):
    """
    Analyzes pragmatic marker patterns: hedging, certainty, speech acts, attitude, likelihood.

    Weight: 4.0% of total score
    Tier: ADVANCED (specialized AI detection pattern)

    Version History:
    - v1.0.0 (v6.0.0): Extracted from transition_marker.py (Story 2.4.0.5)
    - v2.0.0 (v6.1.0): Expanded to 126 patterns (Story 2.6)

    Detects (126 total patterns across 9 categories):
    - Epistemic hedging: 43 patterns (might, may, could, seem, appear, possible, etc.)
    - Frequency hedges: 6 patterns (frequently, occasionally, sometimes, etc.)
    - Epistemic verbs: 8 patterns (assume, estimate, indicate, speculate, etc.)
    - Strong certainty: 18 patterns (definitely, certainly, always, never, etc.)
    - Subjective certainty: 8 patterns (I believe, We know, It is clear, etc.)
    - Assertion acts: 10 patterns (demonstrate, show, prove, confirm, etc.)
    - Formulaic AI acts: 4 patterns (it can be argued, one might argue, etc.)
    - Attitude markers: 18 patterns (surprisingly, unfortunately, importantly, etc.)
    - Likelihood adverbials: 11 patterns (probably, apparently, seemingly, etc.)

    Sources: Hyland (2005), LIWC2015, Biber et al. (1999), BioScope Corpus
    """

    # ========================================================================
    # PRAGMATIC PATTERN DICTIONARIES
    # ========================================================================

    # Epistemic hedging patterns (43 patterns) - Expanded in Story 2.6
    # Sources: Hyland (2005), BioScope Corpus, LIWC2015, Biber et al. (1999)
    EPISTEMIC_HEDGES = {
        # Modal hedges (7 patterns)
        "might": re.compile(r"\bmight\b", re.IGNORECASE),
        "may": re.compile(r"\bmay\b", re.IGNORECASE),
        "could": re.compile(r"\bcould\b", re.IGNORECASE),
        "would": re.compile(r"\bwould\b", re.IGNORECASE),  # Story 2.6
        "should": re.compile(r"\bshould\b", re.IGNORECASE),  # Story 2.6
        "possibly": re.compile(r"\bpossibly\b", re.IGNORECASE),
        "perhaps": re.compile(r"\bperhaps\b", re.IGNORECASE),
        # Epistemic adverbs (4 patterns)
        "presumably": re.compile(r"\bpresumably\b", re.IGNORECASE),
        "conceivably": re.compile(r"\bconceivably\b", re.IGNORECASE),
        "potentially": re.compile(r"\bpotentially\b", re.IGNORECASE),
        # Lexical verb hedges (8 patterns)
        "it_seems": re.compile(r"\bit\s+seems\b", re.IGNORECASE),
        "it_appears": re.compile(r"\bit\s+appears\b", re.IGNORECASE),
        "suggests_that": re.compile(r"\bsuggests\s+that\b", re.IGNORECASE),
        "tends_to": re.compile(r"\btends\s+to\b", re.IGNORECASE),
        "likely_to": re.compile(r"\b(?:is|are)\s+likely\s+to\b", re.IGNORECASE),
        "seem": re.compile(r"\bseems?\b", re.IGNORECASE),  # Story 2.6
        "appear": re.compile(r"\bappears?\b", re.IGNORECASE),  # Story 2.6
        "believe": re.compile(r"\bbelieves?\b", re.IGNORECASE),  # Story 2.6
        "think": re.compile(r"\bthinks?\b", re.IGNORECASE),  # Story 2.6
        "suspect": re.compile(r"\bsuspects?\b", re.IGNORECASE),  # Story 2.6
        "suppose": re.compile(r"\bsupposes?\b", re.IGNORECASE),  # Story 2.6
        # Adjective hedges (5 patterns) - Story 2.6
        "possible": re.compile(r"\bpossible\b", re.IGNORECASE),
        "probable": re.compile(r"\bprobable\b", re.IGNORECASE),
        "unlikely": re.compile(r"\bunlikely\b", re.IGNORECASE),
        "uncertain": re.compile(r"\buncertain\b", re.IGNORECASE),
        "unclear": re.compile(r"\bunclear\b", re.IGNORECASE),
        # Approximators (14 patterns)
        "about": re.compile(r"\babout\b", re.IGNORECASE),
        "almost": re.compile(r"\balmost\b", re.IGNORECASE),
        "approximately": re.compile(r"\bapproximately\b", re.IGNORECASE),
        "around": re.compile(r"\baround\b", re.IGNORECASE),
        "roughly": re.compile(r"\broughly\b", re.IGNORECASE),
        "generally": re.compile(r"\bgenerally\b", re.IGNORECASE),
        "largely": re.compile(r"\blargely\b", re.IGNORECASE),
        "nearly": re.compile(r"\bnearly\b", re.IGNORECASE),  # Story 2.6
        "essentially": re.compile(r"\bessentially\b", re.IGNORECASE),  # Story 2.6
        "relatively": re.compile(r"\brelatively\b", re.IGNORECASE),  # Story 2.6
        "somewhat": re.compile(r"\bsomewhat\b", re.IGNORECASE),  # Story 2.6
        "fairly": re.compile(r"\bfairly\b", re.IGNORECASE),  # Story 2.6
        "quite": re.compile(r"\bquite\b", re.IGNORECASE),  # Story 2.6
        "typically": re.compile(r"\btypically\b", re.IGNORECASE),  # Story 2.6
        "usually": re.compile(r"\busually\b", re.IGNORECASE),  # Story 2.6
        # Multi-word hedges (2 patterns) - Story 2.6
        "to_some_extent": re.compile(r"\bto\s+some\s+extent\b", re.IGNORECASE),
        "in_general": re.compile(r"\bin\s+general\b", re.IGNORECASE),
    }

    # Frequency hedge patterns (6 patterns)
    FREQUENCY_HEDGES = {
        "frequently": re.compile(r"\bfrequently\b", re.IGNORECASE),
        "occasionally": re.compile(r"\boccasionally\b", re.IGNORECASE),
        "sometimes": re.compile(r"\bsometimes\b", re.IGNORECASE),
        "often": re.compile(r"\boften\b", re.IGNORECASE),
        "rarely": re.compile(r"\brarely\b", re.IGNORECASE),
        "seldom": re.compile(r"\bseldom\b", re.IGNORECASE),
    }

    # Epistemic verb patterns (8 patterns with inflections)
    EPISTEMIC_VERBS = {
        "assume": re.compile(r"\bassume[sd]?\b", re.IGNORECASE),
        "estimate": re.compile(r"\bestimate[sd]?\b", re.IGNORECASE),
        "indicate": re.compile(r"\bindicate[sd]?\b", re.IGNORECASE),
        "speculate": re.compile(r"\bspeculate[sd]?\b", re.IGNORECASE),
        "propose": re.compile(r"\bpropose[sd]?\b", re.IGNORECASE),
        "claim": re.compile(r"\bclaim(?:ed|s)?\b", re.IGNORECASE),
        "argue": re.compile(r"\bargue[sd]?\b", re.IGNORECASE),
        "suggest": re.compile(r"\bsuggest(?:ed|s)?\b", re.IGNORECASE),
    }

    # Strong certainty patterns (18 patterns) - Expanded in Story 2.6
    # Sources: LIWC2015, Hyland (2005), Biber et al. (1999)
    STRONG_CERTAINTY = {
        # Original patterns (6)
        "definitely": re.compile(r"\bdefinitely\b", re.IGNORECASE),
        "certainly": re.compile(r"\bcertainly\b", re.IGNORECASE),
        "absolutely": re.compile(r"\babsolutely\b", re.IGNORECASE),
        "undoubtedly": re.compile(r"\bundoubtedly\b", re.IGNORECASE),
        "clearly": re.compile(r"\bclearly\b", re.IGNORECASE),
        "obviously": re.compile(r"\bobviously\b", re.IGNORECASE),
        # Absolute certainty markers (4 patterns) - Story 2.6
        "always": re.compile(r"\balways\b", re.IGNORECASE),
        "never": re.compile(r"\bnever\b", re.IGNORECASE),
        "completely": re.compile(r"\bcompletely\b", re.IGNORECASE),
        "entirely": re.compile(r"\bentirely\b", re.IGNORECASE),
        # Emphatic certainty markers (4 patterns) - Story 2.6
        "totally": re.compile(r"\btotally\b", re.IGNORECASE),
        "surely": re.compile(r"\bsurely\b", re.IGNORECASE),
        "truly": re.compile(r"\btruly\b", re.IGNORECASE),
        "indeed": re.compile(r"\bindeed\b", re.IGNORECASE),
        # Confirmatory boosters (4 patterns) - Story 2.6
        "in_fact": re.compile(r"\bin\s+fact\b", re.IGNORECASE),
        "of_course": re.compile(r"\bof\s+course\b", re.IGNORECASE),
        "unquestionably": re.compile(r"\bunquestionably\b", re.IGNORECASE),
        "undeniably": re.compile(r"\bundeniably\b", re.IGNORECASE),
    }

    # Subjective certainty patterns (8 patterns) - Expanded in Story 2.6
    SUBJECTIVE_CERTAINTY = {
        # Original patterns (4)
        "i_believe": re.compile(r"\bI\s+believe\b"),
        "i_think": re.compile(r"\bI\s+think\b"),
        "we_believe": re.compile(r"\bWe\s+believe\b"),
        "in_my_view": re.compile(r"\bin\s+my\s+view\b", re.IGNORECASE),
        # New patterns (4) - Story 2.6
        "we_know": re.compile(r"\b[Ww]e\s+know\b"),
        "i_am_certain": re.compile(r"\bI\s+am\s+certain\b"),
        "we_are_confident": re.compile(r"\b[Ww]e\s+are\s+confident\b"),
        "it_is_clear": re.compile(r"\b[Ii]t\s+is\s+clear\b"),
    }

    # Assertion speech act patterns (10 patterns) - Expanded in Story 2.6
    # Sources: Hyland (2005)
    ASSERTION_ACTS = {
        # Original patterns (4)
        "i_argue": re.compile(r"\bI\s+argue\s+that\b"),
        "we_propose": re.compile(r"\bWe\s+propose\s+that\b"),
        "this_shows": re.compile(r"\bThis\s+shows\b"),
        "this_demonstrates": re.compile(r"\bThis\s+demonstrates\b"),
        # New assertion verbs (6 patterns) - Story 2.6
        "demonstrate": re.compile(r"\bdemonstrates?\b", re.IGNORECASE),
        "show": re.compile(r"\bshows?\b", re.IGNORECASE),
        "prove": re.compile(r"\bproves?\b", re.IGNORECASE),
        "establish": re.compile(r"\bestablish(?:es)?\b", re.IGNORECASE),
        "confirm": re.compile(r"\bconfirms?\b", re.IGNORECASE),
        "find": re.compile(r"\bfinds?\b", re.IGNORECASE),
    }

    # Formulaic AI speech act patterns (4 patterns)
    FORMULAIC_AI_ACTS = {
        "it_can_be_argued": re.compile(r"\bit\s+can\s+be\s+argued\s+that\b", re.IGNORECASE),
        "one_might_argue": re.compile(r"\bone\s+might\s+argue\s+that\b", re.IGNORECASE),
        "it_should_be_noted": re.compile(r"\bit\s+should\s+be\s+noted\s+that\b", re.IGNORECASE),
        "it_is_worth_noting": re.compile(r"\bit\s+is\s+worth\s+noting\s+that\b", re.IGNORECASE),
    }

    # ========================================================================
    # NEW PATTERN CATEGORIES - Added in Story 2.6
    # ========================================================================

    # Attitude markers (18 patterns) - Story 2.6
    # Sources: Hyland (2005), Biber et al. (1999)
    # These express writer's affective evaluation of propositional content
    ATTITUDE_MARKERS = {
        # Evaluative - unexpected/notable (6 patterns)
        "surprisingly": re.compile(r"\bsurprisingly\b", re.IGNORECASE),
        "unexpectedly": re.compile(r"\bunexpectedly\b", re.IGNORECASE),
        "interestingly": re.compile(r"\binterestingly\b", re.IGNORECASE),
        "remarkably": re.compile(r"\bremarkably\b", re.IGNORECASE),
        "curiously": re.compile(r"\bcuriously\b", re.IGNORECASE),
        "strangely": re.compile(r"\bstrangely\b", re.IGNORECASE),
        # Evaluative - positive/negative (4 patterns)
        "unfortunately": re.compile(r"\bunfortunately\b", re.IGNORECASE),
        "fortunately": re.compile(r"\bfortunately\b", re.IGNORECASE),
        "regrettably": re.compile(r"\bregrettably\b", re.IGNORECASE),
        "hopefully": re.compile(r"\bhopefully\b", re.IGNORECASE),
        # Evaluative - importance/salience (4 patterns)
        "importantly": re.compile(r"\bimportantly\b", re.IGNORECASE),
        "significantly": re.compile(r"\bsignificantly\b", re.IGNORECASE),
        "notably": re.compile(r"\bnotably\b", re.IGNORECASE),
        "admittedly": re.compile(r"\badmittedly\b", re.IGNORECASE),
        # Evaluative - expectation (4 patterns)
        "oddly": re.compile(r"\boddly\b", re.IGNORECASE),
        "predictably": re.compile(r"\bpredictably\b", re.IGNORECASE),
        "inevitably": re.compile(r"\binevitably\b", re.IGNORECASE),
        "understandably": re.compile(r"\bunderstandably\b", re.IGNORECASE),
    }

    # Likelihood adverbials (11 patterns) - Story 2.6
    # Sources: Biber et al. (1999), Hyland (2005)
    # These express probability or evidential likelihood
    LIKELIHOOD_ADVERBIALS = {
        # Core probability (3 patterns)
        "probably": re.compile(r"\bprobably\b", re.IGNORECASE),
        "arguably": re.compile(r"\barguably\b", re.IGNORECASE),
        "plausibly": re.compile(r"\bplausibly\b", re.IGNORECASE),
        # Evidential likelihood (4 patterns)
        "apparently": re.compile(r"\bapparently\b", re.IGNORECASE),
        "evidently": re.compile(r"\bevidently\b", re.IGNORECASE),
        "seemingly": re.compile(r"\bseemingly\b", re.IGNORECASE),
        "ostensibly": re.compile(r"\bostensibly\b", re.IGNORECASE),
        # Reported likelihood (4 patterns)
        "supposedly": re.compile(r"\bsupposedly\b", re.IGNORECASE),
        "reportedly": re.compile(r"\breportedly\b", re.IGNORECASE),
        "allegedly": re.compile(r"\ballegedly\b", re.IGNORECASE),
        "purportedly": re.compile(r"\bpurportedly\b", re.IGNORECASE),
    }

    # ========================================================================
    # SCORING THRESHOLDS - Research-backed baselines
    # Updated in Story 2.6 for expanded 126-pattern lexicon
    # ========================================================================

    # Hedging scoring thresholds (per 1k words)
    # Story 2.6: Expanded from 52 to 126 patterns - thresholds adjusted
    # Research baseline (pre-expansion): Human 4-7, AI 10-15
    # Post-expansion estimate: Human 5-9, AI 12-18
    HEDGING_THRESHOLD_EXCELLENT = 9.0  # Was 7.0 (Story 2.6)
    HEDGING_THRESHOLD_GOOD = 11.0  # Was 9.0 (Story 2.6)
    HEDGING_THRESHOLD_CONCERNING = 15.0  # Was 12.0 (Story 2.6)
    HEDGING_VARIETY_TARGET = 0.4  # Reduced from 0.6 for larger pattern set
    HEDGING_VARIETY_OPTIMAL = 0.5  # Reduced from 0.7 for larger pattern set

    # Certainty scoring thresholds (per 1k words)
    # Story 2.6: Expanded from 10 to 26 patterns - thresholds adjusted
    # Research: Human 2-5, ratio 0.5-1.0
    # Post-expansion estimate: Human 3-7, ratio maintained
    CERTAINTY_THRESHOLD_MIN = 3.0  # Was 2.0 (Story 2.6)
    CERTAINTY_THRESHOLD_MAX = 7.0  # Was 5.0 (Story 2.6)
    CERTAINTY_THRESHOLD_GOOD = 9.0  # Was 7.0 (Story 2.6)
    CERTAINTY_THRESHOLD_CONCERNING = 12.0  # Was 10.0 (Story 2.6)
    CERTAINTY_RATIO_MIN = 0.5
    CERTAINTY_RATIO_MAX = 1.0
    CERTAINTY_RATIO_IDEAL = 0.75
    CERTAINTY_RATIO_THRESHOLD = 0.3
    CERTAINTY_SUBJECTIVE_TARGET = 40.0  # Percentage

    # Speech acts scoring thresholds (per 1k words)
    # Story 2.6: Expanded from 8 to 14 patterns
    # Research: Human 3-6, <30% formulaic
    SPEECH_ACTS_THRESHOLD_MIN = 3.0
    SPEECH_ACTS_THRESHOLD_MAX = 8.0  # Was 6.0 (Story 2.6)
    SPEECH_ACTS_THRESHOLD_GOOD = 2.0
    SPEECH_ACTS_FORMULAIC_TARGET = 0.3  # Maximum for excellent
    SPEECH_ACTS_FORMULAIC_ACCEPTABLE = 0.5
    SPEECH_ACTS_FORMULAIC_CONCERNING = 0.7
    SPEECH_ACTS_PERSONAL_TARGET = 50.0  # Percentage

    # Composite scoring weights
    WEIGHT_HEDGING = 0.25  # Epistemic hedging patterns
    WEIGHT_CERTAINTY = 0.20  # Certainty markers
    WEIGHT_SPEECH_ACTS = 0.15  # Speech act patterns
    WEIGHT_FREQUENCY = 0.20  # Frequency hedges
    WEIGHT_EPISTEMIC_VERBS = 0.20  # Epistemic verbs

    # Component scoring weights (internal to scoring methods)
    HEDGING_WEIGHT_FREQUENCY = 0.6
    HEDGING_WEIGHT_VARIETY = 0.4

    CERTAINTY_WEIGHT_FREQUENCY = 0.4
    CERTAINTY_WEIGHT_BALANCE = 0.4
    CERTAINTY_WEIGHT_PERSONAL = 0.2

    SPEECH_ACTS_WEIGHT_FREQUENCY = 0.3
    SPEECH_ACTS_WEIGHT_FORMULAIC = 0.4
    SPEECH_ACTS_WEIGHT_PERSONAL = 0.3

    # Pragmatic balance targets (adjusted for expanded lexicon in Story 2.6)
    PRAGMATIC_HEDGE_TARGET = 7.0  # Was 6.0 (Story 2.6)
    PRAGMATIC_CERTAINTY_TARGET = 5.0  # Was 3.5 (Story 2.6)
    PRAGMATIC_SPEECH_TARGET = 5.5  # Was 4.5 (Story 2.6)

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
        return "pragmatic_markers"

    @property
    def weight(self) -> float:
        """Return dimension weight (5.0% of total score)."""
        return 5.0

    @property
    def tier(self) -> DimensionTier:
        """Return dimension tier."""
        return DimensionTier.ADVANCED

    @property
    def description(self) -> str:
        """Return dimension description."""
        return "Analyzes epistemic stance markers: hedging, certainty, speech acts"

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
        Analyze text for pragmatic marker patterns.

        Analyzes epistemic hedging, certainty markers, frequency hedges,
        epistemic verbs, and speech acts.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters (word_count if pre-calculated)

        Returns:
            Dict with pragmatic marker analysis results:
            - hedging: Dict with epistemic hedging analysis
            - certainty: Dict with certainty marker analysis
            - speech_acts: Dict with speech act analysis
            - frequency_hedges: Dict with frequency hedge analysis
            - epistemic_verbs: Dict with epistemic verb analysis
            - certainty_hedge_ratio: Composite metric
            - formulaic_ratio: Composite metric
            - pragmatic_balance: Composite metric
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
                pragmatic_analysis = self._analyze_pragmatic_markers(sample_text, **kwargs)
                sample_results.append(pragmatic_analysis)

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            aggregated = self._analyze_pragmatic_markers(analyzed_text, **kwargs)
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

    # ========================================================================
    # SCORING METHODS - DimensionStrategy Contract
    # ========================================================================

    def _score_hedging(self, hedging: Dict[str, Any]) -> float:
        """
        Score hedging patterns using threshold-based approach.

        Human-like: 4-7 per 1k, variety 0.6+
        AI-like: 10-15+ per 1k, variety 0.3-0.5

        Args:
            hedging: Hedging analysis dict from analyze()

        Returns:
            Score 0-100 (higher = more human-like)
        """
        freq = hedging["per_1k"]
        variety = hedging["variety_score"]

        # Frequency score (threshold-based)
        # Research: Human 4-7, AI 10-15
        if freq <= self.HEDGING_THRESHOLD_EXCELLENT and variety >= self.HEDGING_VARIETY_TARGET:
            freq_score = 100.0  # Excellent - human range with good variety
        elif freq <= self.HEDGING_THRESHOLD_GOOD:
            freq_score = 75.0  # Good - upper human range
        elif freq <= self.HEDGING_THRESHOLD_CONCERNING:
            freq_score = 50.0  # Concerning - lower AI range
        else:
            freq_score = 25.0  # Strong AI signature

        # Variety score (higher is better, up to optimal)
        variety_score = min(variety / self.HEDGING_VARIETY_OPTIMAL, 1.0) * 100

        # Composite
        score = (freq_score * self.HEDGING_WEIGHT_FREQUENCY) + (
            variety_score * self.HEDGING_WEIGHT_VARIETY
        )

        return float(score)

    def _score_certainty(self, certainty: Dict[str, Any], certainty_hedge_ratio: float) -> float:
        """
        Score certainty markers using threshold-based approach.

        Human-like: 2-5 per 1k, ratio 0.5-1.0, subjective 40%+
        AI-like: 0-1 or 8+, ratio <0.3 or >2.0, subjective <20%

        Args:
            certainty: Certainty analysis dict from analyze()
            certainty_hedge_ratio: Ratio from composite metrics

        Returns:
            Score 0-100 (higher = more human-like)
        """
        freq = certainty["per_1k"]
        ratio = certainty_hedge_ratio
        subjective_pct = certainty["subjective_percentage"]

        # Frequency score (threshold-based)
        # Research: Human 2-5, ratio 0.5-1.0
        if (
            freq >= self.CERTAINTY_THRESHOLD_MIN
            and freq <= self.CERTAINTY_THRESHOLD_MAX
            and self.CERTAINTY_RATIO_MIN <= ratio <= self.CERTAINTY_RATIO_MAX
        ):
            freq_score = 100.0  # Excellent - human range with balanced ratio
        elif freq <= self.CERTAINTY_THRESHOLD_GOOD and ratio >= self.CERTAINTY_RATIO_THRESHOLD:
            freq_score = 75.0  # Good
        elif freq <= self.CERTAINTY_THRESHOLD_CONCERNING:
            freq_score = 50.0  # Concerning
        else:
            freq_score = 25.0  # Poor - too many or too few

        # Balance score (ratio should be within optimal range)
        if self.CERTAINTY_RATIO_MIN <= ratio <= self.CERTAINTY_RATIO_MAX:
            balance_score = 100.0
        else:
            balance_score = max(0.0, 100.0 - abs(ratio - self.CERTAINTY_RATIO_IDEAL) * 50.0)

        # Personal score (higher is better, target subjective percentage)
        personal_score = min(subjective_pct / self.CERTAINTY_SUBJECTIVE_TARGET, 1.0) * 100

        # Composite
        score = (
            freq_score * self.CERTAINTY_WEIGHT_FREQUENCY
            + balance_score * self.CERTAINTY_WEIGHT_BALANCE
            + personal_score * self.CERTAINTY_WEIGHT_PERSONAL
        )

        return float(score)

    def _score_speech_acts(self, speech_acts: Dict[str, Any]) -> float:
        """
        Score speech act patterns using threshold-based approach.

        Human-like: 3-6 per 1k, <30% formulaic, 50%+ personal
        AI-like: 1-3 per 1k, >60% formulaic, <20% personal

        Args:
            speech_acts: Speech acts analysis dict from analyze()

        Returns:
            Score 0-100 (higher = more human-like)
        """
        freq = speech_acts["per_1k"]
        formulaic_pct = speech_acts["formulaic_ratio"]
        personal_pct = speech_acts["personal_percentage"]

        # Frequency score (threshold-based)
        # Research: Human 3-6, <30% formulaic
        if (
            freq >= self.SPEECH_ACTS_THRESHOLD_MIN
            and freq <= self.SPEECH_ACTS_THRESHOLD_MAX
            and formulaic_pct <= self.SPEECH_ACTS_FORMULAIC_TARGET
        ):
            freq_score = 100.0  # Excellent - human range with low formulaic
        elif (
            freq >= self.SPEECH_ACTS_THRESHOLD_GOOD
            and formulaic_pct <= self.SPEECH_ACTS_FORMULAIC_ACCEPTABLE
        ):
            freq_score = 75.0  # Good
        elif formulaic_pct <= self.SPEECH_ACTS_FORMULAIC_CONCERNING:
            freq_score = 50.0  # Concerning
        else:
            freq_score = 25.0  # Strong AI signature - high formulaic ratio

        # Formulaic penalty (lower is better, target threshold)
        if formulaic_pct <= self.SPEECH_ACTS_FORMULAIC_TARGET:
            formulaic_score = 100.0
        else:
            formulaic_score = max(
                0.0, 100.0 - (formulaic_pct - self.SPEECH_ACTS_FORMULAIC_TARGET) * 200.0
            )

        # Personal score (higher is better, target percentage)
        personal_score = min(personal_pct / self.SPEECH_ACTS_PERSONAL_TARGET, 1.0) * 100

        # Composite
        score = (
            freq_score * self.SPEECH_ACTS_WEIGHT_FREQUENCY
            + formulaic_score * self.SPEECH_ACTS_WEIGHT_FORMULAIC
            + personal_score * self.SPEECH_ACTS_WEIGHT_PERSONAL
        )

        return float(score)

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score using weighted composite of pragmatic components.

        Weighted Components:
        - Hedging: 25% (epistemic hedging patterns)
        - Certainty: 20% (certainty markers and balance)
        - Speech acts: 15% (personal vs formulaic)
        - Frequency hedges: 20%
        - Epistemic verbs: 20%

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like) to 100.0 (human-like)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        # Enhanced pragmatic scoring
        hedging_score = self._score_hedging(metrics["hedging"])
        certainty_score = self._score_certainty(
            metrics["certainty"], metrics["certainty_hedge_ratio"]
        )
        speech_acts_score = self._score_speech_acts(metrics["speech_acts"])

        # Weighted composite
        score = (
            hedging_score * self.WEIGHT_HEDGING
            + certainty_score * self.WEIGHT_CERTAINTY
            + speech_acts_score * self.WEIGHT_SPEECH_ACTS
            + hedging_score * self.WEIGHT_FREQUENCY  # Use hedging score for frequency component
            + hedging_score * self.WEIGHT_EPISTEMIC_VERBS  # Use hedging score for epistemic verbs
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
            recommendations.append("Pragmatic marker analysis unavailable.")
            return recommendations

        hedging = metrics.get("hedging", {})
        certainty = metrics.get("certainty", {})
        speech_acts = metrics.get("speech_acts", {})

        if hedging.get("per_1k", 0) > self.HEDGING_THRESHOLD_GOOD:
            recommendations.append(
                f"Reduce epistemic hedging ({hedging['per_1k']:.1f} per 1k words, target ≤{self.HEDGING_THRESHOLD_EXCELLENT}). "
                f"Use direct, confident language when appropriate."
            )

        if certainty.get("per_1k", 0) > self.CERTAINTY_THRESHOLD_GOOD:
            recommendations.append(
                f"High certainty marker usage ({certainty['per_1k']:.1f} per 1k, target {self.CERTAINTY_THRESHOLD_MIN}-{self.CERTAINTY_THRESHOLD_MAX}). "
                f"Balance confidence with appropriate hedging."
            )

        if speech_acts.get("formulaic_ratio", 0) > self.SPEECH_ACTS_FORMULAIC_ACCEPTABLE:
            recommendations.append(
                f"Reduce formulaic speech acts ({speech_acts['formulaic_ratio']*100:.0f}% formulaic, target <{self.SPEECH_ACTS_FORMULAIC_TARGET*100:.0f}%). "
                f"Use more personal, direct assertions."
            )

        if score >= 75:
            recommendations.append(
                "Good pragmatic marker balance. Text shows natural epistemic stance patterns."
            )
        elif score >= 45 and len(recommendations) == 0:
            # Provide neutral feedback for acceptable scores when no specific issues found
            recommendations.append(
                "Acceptable pragmatic marker usage. Consider varying epistemic stance patterns for more natural flow."
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

    def _analyze_pragmatic_markers(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Comprehensive pragmatic marker analysis.

        Orchestrates all individual analysis methods and calculates composite metrics.
        Expanded in Story 2.6 to include attitude markers and likelihood adverbials.

        Args:
            text: Text to analyze
            **kwargs: Additional parameters (word_count if pre-calculated)

        Returns:
            Dict with complete pragmatic analysis:
            - hedging: Hedging analysis dict
            - certainty: Certainty analysis dict
            - speech_acts: Speech act analysis dict
            - attitude_markers: Attitude marker analysis dict (Story 2.6)
            - likelihood_adverbials: Likelihood adverbial analysis dict (Story 2.6)
            - certainty_hedge_ratio: Composite metric
            - formulaic_ratio: Composite metric
            - pragmatic_balance: Composite metric
        """
        # Calculate word count once (used by all methods)
        total_words = kwargs.get("word_count")
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        # Run all individual analyses
        hedging = self._analyze_hedging(text, total_words=total_words)
        certainty = self._analyze_certainty(text, total_words=total_words)
        speech_acts = self._analyze_speech_acts(text, total_words=total_words)
        # New categories added in Story 2.6
        attitude_markers = self._analyze_attitude_markers(text, total_words=total_words)
        likelihood_adverbials = self._analyze_likelihood_adverbials(text, total_words=total_words)

        # Calculate composite metrics
        certainty_hedge_ratio = self._calculate_certainty_hedge_ratio(
            certainty["total_count"], hedging["total_count"]
        )

        formulaic_ratio = speech_acts["formulaic_ratio"]

        pragmatic_balance = self._calculate_pragmatic_balance(
            hedging["per_1k"], certainty["per_1k"], speech_acts["per_1k"]
        )

        # Build comprehensive result
        return {
            "hedging": hedging,
            "certainty": certainty,
            "speech_acts": speech_acts,
            "attitude_markers": attitude_markers,  # Story 2.6
            "likelihood_adverbials": likelihood_adverbials,  # Story 2.6
            "certainty_hedge_ratio": certainty_hedge_ratio,
            "formulaic_ratio": formulaic_ratio,
            "pragmatic_balance": pragmatic_balance,
        }

    def _analyze_hedging(self, text: str, total_words: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze epistemic hedging patterns.

        Detects 57 pragmatic patterns across multiple categories (expanded in Story 2.6):
        - 43 epistemic hedges (modals, lexical verbs, adjectives, approximators)
        - 6 frequency hedges
        - 8 epistemic verbs

        Human writers: 5-9 hedges per 1k words, variety 0.6+
        AI writers: 12-18 hedges per 1k words, variety 0.3-0.5

        Args:
            text: Text to analyze
            total_words: Pre-calculated word count (optional)

        Returns:
            Dict with:
            - total_count: Total hedge occurrences (all categories)
            - per_1k: Hedges per 1000 words
            - variety_score: Unique hedges / total hedge types (0-1)
            - counts_by_type: Dict mapping hedge type to count
            - approximators_count: Count of approximator matches
            - frequency_hedges_count: Count of frequency hedge matches
            - epistemic_verbs_count: Count of epistemic verb matches
        """
        # Calculate total words if not provided
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        # Count each epistemic hedging pattern (43 patterns in Story 2.6)
        counts_by_type = {}
        epistemic_hedge_count = 0
        approximators_count = 0

        # Approximator pattern names (expanded in Story 2.6)
        approximator_patterns = {
            "about",
            "almost",
            "approximately",
            "around",
            "roughly",
            "generally",
            "largely",
            "nearly",
            "essentially",
            "relatively",
            "somewhat",
            "fairly",
            "quite",
            "typically",
            "usually",
            "to_some_extent",
            "in_general",
        }

        for hedge_type, pattern in self.EPISTEMIC_HEDGES.items():
            count = len(pattern.findall(text))
            counts_by_type[hedge_type] = count
            epistemic_hedge_count += count
            # Track approximators separately
            if hedge_type in approximator_patterns:
                approximators_count += count

        # Count frequency hedge patterns (6 patterns)
        frequency_hedges_count = 0
        for hedge_type, pattern in self.FREQUENCY_HEDGES.items():
            count = len(pattern.findall(text))
            counts_by_type[hedge_type] = count
            frequency_hedges_count += count

        # Count epistemic verb patterns (8 patterns)
        epistemic_verbs_count = 0
        for verb_type, pattern in self.EPISTEMIC_VERBS.items():
            count = len(pattern.findall(text))
            counts_by_type[verb_type] = count
            epistemic_verbs_count += count

        # Calculate total count (all categories)
        total_count = epistemic_hedge_count + frequency_hedges_count + epistemic_verbs_count

        # Calculate variety score (unique hedges / total hedge types across all categories)
        unique_hedges = sum(1 for count in counts_by_type.values() if count > 0)
        total_hedge_types = (
            len(self.EPISTEMIC_HEDGES) + len(self.FREQUENCY_HEDGES) + len(self.EPISTEMIC_VERBS)
        )
        variety_score = unique_hedges / total_hedge_types if total_hedge_types > 0 else 0.0

        return {
            "total_count": total_count,
            "per_1k": total_count / words_in_thousands if words_in_thousands > 0 else 0.0,
            "variety_score": variety_score,
            "counts_by_type": counts_by_type,
            "approximators_count": approximators_count,
            "frequency_hedges_count": frequency_hedges_count,
            "epistemic_verbs_count": epistemic_verbs_count,
        }

    def _analyze_certainty(self, text: str, total_words: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze certainty marker patterns.

        Detects 10 certainty patterns (6 strong + 4 subjective).
        Human writers: 2-5 per 1k, ratio 0.5-1.0 (certainty/hedge), subjective 40%+
        AI writers: 0-1 or 8+ per 1k, ratio <0.3 or >2.0, subjective <20%

        Args:
            text: Text to analyze
            total_words: Pre-calculated word count (optional)

        Returns:
            Dict with:
            - total_count: Total certainty markers
            - per_1k: Certainty markers per 1000 words
            - strong_counts: Dict mapping strong certainty type to count
            - subjective_counts: Dict mapping subjective certainty type to count
            - subjective_percentage: Subjective markers / total markers (0-100)
        """
        # Calculate total words if not provided
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        # Count strong certainty patterns
        strong_counts = {}
        strong_total = 0

        for certainty_type, pattern in self.STRONG_CERTAINTY.items():
            count = len(pattern.findall(text))
            strong_counts[certainty_type] = count
            strong_total += count

        # Count subjective certainty patterns
        subjective_counts = {}
        subjective_total = 0

        for certainty_type, pattern in self.SUBJECTIVE_CERTAINTY.items():
            count = len(pattern.findall(text))
            subjective_counts[certainty_type] = count
            subjective_total += count

        # Calculate totals and percentages
        total_count = strong_total + subjective_total
        subjective_percentage = (subjective_total / total_count * 100.0) if total_count > 0 else 0.0

        return {
            "total_count": total_count,
            "per_1k": total_count / words_in_thousands if words_in_thousands > 0 else 0.0,
            "strong_counts": strong_counts,
            "subjective_counts": subjective_counts,
            "subjective_percentage": subjective_percentage,
        }

    def _analyze_speech_acts(self, text: str, total_words: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze speech act patterns.

        Detects 8 speech act patterns (4 assertion + 4 formulaic AI).
        Human writers: 3-6 per 1k, <30% formulaic, 50%+ personal
        AI writers: 1-3 per 1k, >60% formulaic, <20% personal

        Args:
            text: Text to analyze
            total_words: Pre-calculated word count (optional)

        Returns:
            Dict with:
            - total_count: Total speech acts
            - per_1k: Speech acts per 1000 words
            - assertion_count: Personal assertion acts (I argue, We propose, etc.)
            - formulaic_count: Formulaic AI acts (it can be argued, etc.)
            - formulaic_ratio: formulaic_count / total_count (0-1)
            - personal_percentage: assertion_count / total_count (0-100)
        """
        # Calculate total words if not provided
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        # Count assertion speech acts
        assertion_count = 0
        for pattern in self.ASSERTION_ACTS.values():
            assertion_count += len(pattern.findall(text))

        # Count formulaic AI speech acts
        formulaic_count = 0
        for pattern in self.FORMULAIC_AI_ACTS.values():
            formulaic_count += len(pattern.findall(text))

        # Calculate totals and ratios
        total_count = assertion_count + formulaic_count
        formulaic_ratio = (formulaic_count / total_count) if total_count > 0 else 0.0
        personal_percentage = (assertion_count / total_count * 100.0) if total_count > 0 else 0.0

        return {
            "total_count": total_count,
            "per_1k": total_count / words_in_thousands if words_in_thousands > 0 else 0.0,
            "assertion_count": assertion_count,
            "formulaic_count": formulaic_count,
            "formulaic_ratio": formulaic_ratio,
            "personal_percentage": personal_percentage,
        }

    def _analyze_attitude_markers(
        self, text: str, total_words: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze attitude marker patterns.

        Added in Story 2.6. Detects 18 attitude marker patterns expressing
        writer's affective evaluation of propositional content.

        Categories:
        - Evaluative unexpected: surprisingly, unexpectedly, interestingly, etc.
        - Evaluative positive/negative: fortunately, unfortunately, regrettably, etc.
        - Evaluative importance: importantly, significantly, notably, etc.

        Human writers: Use attitude markers to express personal stance
        AI writers: May overuse certain attitude markers or use them formulaically

        Args:
            text: Text to analyze
            total_words: Pre-calculated word count (optional)

        Returns:
            Dict with:
            - total_count: Total attitude marker occurrences
            - per_1k: Attitude markers per 1000 words
            - counts_by_type: Dict mapping marker type to count
            - variety_score: Unique markers used / total marker types
        """
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        counts_by_type = {}
        total_count = 0

        for marker_type, pattern in self.ATTITUDE_MARKERS.items():
            count = len(pattern.findall(text))
            counts_by_type[marker_type] = count
            total_count += count

        # Calculate variety score
        unique_markers = sum(1 for count in counts_by_type.values() if count > 0)
        total_marker_types = len(self.ATTITUDE_MARKERS)
        variety_score = unique_markers / total_marker_types if total_marker_types > 0 else 0.0

        return {
            "total_count": total_count,
            "per_1k": total_count / words_in_thousands if words_in_thousands > 0 else 0.0,
            "counts_by_type": counts_by_type,
            "variety_score": variety_score,
        }

    def _analyze_likelihood_adverbials(
        self, text: str, total_words: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze likelihood adverbial patterns.

        Added in Story 2.6. Detects 11 likelihood adverbial patterns expressing
        probability or evidential likelihood.

        Categories:
        - Core probability: probably, arguably, plausibly
        - Evidential likelihood: apparently, evidently, seemingly, ostensibly
        - Reported likelihood: supposedly, reportedly, allegedly, purportedly

        Human writers: Use varied likelihood expressions
        AI writers: May overuse certain likelihood markers

        Args:
            text: Text to analyze
            total_words: Pre-calculated word count (optional)

        Returns:
            Dict with:
            - total_count: Total likelihood adverbial occurrences
            - per_1k: Likelihood adverbials per 1000 words
            - counts_by_type: Dict mapping adverbial type to count
            - variety_score: Unique adverbials used / total adverbial types
        """
        if total_words is None:
            total_words = len(re.findall(r"\b\w+\b", text))

        words_in_thousands = total_words / 1000 if total_words > 0 else 1

        counts_by_type = {}
        total_count = 0

        for adverbial_type, pattern in self.LIKELIHOOD_ADVERBIALS.items():
            count = len(pattern.findall(text))
            counts_by_type[adverbial_type] = count
            total_count += count

        # Calculate variety score
        unique_adverbials = sum(1 for count in counts_by_type.values() if count > 0)
        total_adverbial_types = len(self.LIKELIHOOD_ADVERBIALS)
        variety_score = (
            unique_adverbials / total_adverbial_types if total_adverbial_types > 0 else 0.0
        )

        return {
            "total_count": total_count,
            "per_1k": total_count / words_in_thousands if words_in_thousands > 0 else 0.0,
            "counts_by_type": counts_by_type,
            "variety_score": variety_score,
        }

    def _calculate_certainty_hedge_ratio(self, certainty_count: int, hedge_count: int) -> float:
        """
        Calculate certainty to hedge ratio.

        Human: 0.5-1.0 (balanced use of certainty and hedging)
        AI: <0.3 (over-hedged) or >2.0 (over-certain)

        Args:
            certainty_count: Total certainty markers
            hedge_count: Total hedging markers

        Returns:
            Ratio of certainty to hedging (0 if no hedges)
        """
        return (certainty_count / hedge_count) if hedge_count > 0 else 0.0

    def _calculate_pragmatic_balance(
        self, hedging_per_1k: float, certainty_per_1k: float, speech_acts_per_1k: float
    ) -> float:
        """
        Calculate overall pragmatic balance score.

        Balanced pragmatics (human-like): 0.5-0.8
        - Moderate use of all three marker types
        - No extreme over-use or under-use

        Unbalanced (AI-like): <0.3 or >0.9
        - Excessive hedging with minimal certainty/speech acts
        - Or excessive certainty with minimal hedging

        Args:
            hedging_per_1k: Hedges per 1k words
            certainty_per_1k: Certainty markers per 1k words
            speech_acts_per_1k: Speech acts per 1k words

        Returns:
            Balance score 0-1 (1 = perfect balance)
        """
        # Target ranges (human-like)

        # Calculate deviation from targets
        total_markers = hedging_per_1k + certainty_per_1k + speech_acts_per_1k

        if total_markers == 0:
            return 0.0

        # Balance = diversity of marker usage (closer to equal distribution = higher score)
        hedge_ratio = hedging_per_1k / total_markers
        certainty_ratio = certainty_per_1k / total_markers
        speech_ratio = speech_acts_per_1k / total_markers

        # Ideal distribution would be roughly equal (0.33, 0.33, 0.33)
        # Calculate variance from equal distribution
        ideal = 0.333
        variance = (
            abs(hedge_ratio - ideal) + abs(certainty_ratio - ideal) + abs(speech_ratio - ideal)
        ) / 3.0

        # Convert variance to balance score (lower variance = higher balance)
        balance = max(0.0, 1.0 - (variance * 3.0))

        return balance


# Backward compatibility alias
PragmaticMarkersAnalyzer = PragmaticMarkersDimension

# Module-level singleton - triggers self-registration on module import
_instance = PragmaticMarkersDimension()
