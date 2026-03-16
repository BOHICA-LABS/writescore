"""
Energy dimension analyzer.

Analyzes writing dynamism and engagement patterns:
- Active vs passive voice ratio
- Verb strength/dynamism (action verbs vs static verbs)
- Concrete vs abstract language ratio (using Brysbaert norms when available)
- Power words density (using Warriner dominance norms when available)
- Sentence rhythm contrast (adjacent sentence length variation)

AI writing tends toward passive, abstract, low-energy patterns.
Human writing shows active voice, concrete language, and dynamic pacing.

Created based on research into computational measures of writing engagement.
Uses research-backed lexicons (Brysbaert concreteness, Warriner dominance)
with curated fallbacks when datasets are unavailable.
"""

import re
import statistics
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.analysis_config import DEFAULT_CONFIG, AnalysisConfig
from writescore.core.dimension_registry import DimensionRegistry
from writescore.dimensions.base_strategy import DimensionStrategy, DimensionTier
from writescore.utils.lexicons import (
    get_abstract_words,
    get_dynamic_verbs,
    get_static_verbs,
    get_word_concreteness,
    is_power_word,
)

# Lazy load spacy
_nlp = None


def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        from writescore.utils.spacy_loader import load_spacy_model

        try:
            _nlp = load_spacy_model("en_core_web_sm")
        except OSError:
            # Model not installed, return None
            return None
    return _nlp


class EnergyDimension(DimensionStrategy):
    """
    Analyzes energy dimension - writing dynamism and engagement.

    Weight: 5.0% of total score
    Tier: SUPPORTING

    Detects:
    - Passive voice overuse (AI signature)
    - Weak/static verb dominance (AI signature)
    - Abstract language dominance (AI signature)
    - Low power word density (AI signature)
    - Monotonous sentence rhythm (AI signature)
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
        return "energy"

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
        return (
            "Analyzes writing dynamism: active voice, verb strength, concrete language, power words"
        )

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
        Analyze text for energy/dynamism patterns.

        Args:
            text: Full text content
            lines: Text split into lines (optional)
            config: Analysis configuration (None = current behavior)
            **kwargs: Additional parameters

        Returns:
            Dict with energy analysis results
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
                energy_metrics = self._analyze_energy(sample_text)
                sample_results.append({"energy": energy_metrics})

            # Aggregate metrics from all samples
            aggregated = self._aggregate_sampled_metrics(sample_results)
            analyzed_length = sum(len(sample_text) for _, sample_text in samples)
            samples_analyzed = len(samples)

        # Handle direct analysis (returns string - truncated or full text)
        else:
            analyzed_text = prepared
            energy_metrics = self._analyze_energy(analyzed_text)
            aggregated = {"energy": energy_metrics}
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

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate 0-100 score based on energy metrics.

        Combines multiple sub-metrics:
        - Active voice ratio (30% weight)
        - Verb dynamism ratio (25% weight)
        - Concrete language ratio (20% weight)
        - Power words density (15% weight)
        - Rhythm contrast (10% weight)

        Args:
            metrics: Output from analyze() method

        Returns:
            Score from 0.0 (AI-like/flat) to 100.0 (human-like/dynamic)
        """
        if not metrics.get("available", False):
            return 50.0  # Neutral score for unavailable data

        energy = metrics.get("energy", {})

        # Sub-scores with weights
        # 1. Active voice ratio (target: >0.85 active, meaning <0.15 passive)
        passive_ratio = energy.get("passive_ratio", 0.15)
        active_ratio = 1.0 - passive_ratio
        # Monotonic increasing: higher active ratio = higher score
        active_score = self._monotonic_score(
            value=active_ratio, threshold_low=0.70, threshold_high=0.90, increasing=True
        )

        # 2. Verb dynamism (target: >0.15 dynamic verbs of all verbs)
        dynamic_ratio = energy.get("dynamic_verb_ratio", 0.0)
        dynamic_score = self._monotonic_score(
            value=dynamic_ratio, threshold_low=0.05, threshold_high=0.20, increasing=True
        )

        # 3. Concrete language ratio (target: <0.10 abstract ratio)
        abstract_ratio = energy.get("abstract_ratio", 0.10)
        concrete_ratio = 1.0 - abstract_ratio
        concrete_score = self._monotonic_score(
            value=concrete_ratio, threshold_low=0.85, threshold_high=0.95, increasing=True
        )

        # 4. Power words density (target: >0.02 = 2%)
        power_density = energy.get("power_word_density", 0.0)
        power_score = self._monotonic_score(
            value=power_density, threshold_low=0.005, threshold_high=0.025, increasing=True
        )

        # 5. Rhythm contrast (adjacent sentence length variation)
        rhythm_contrast = energy.get("rhythm_contrast", 0.0)
        # Gaussian: optimal around 0.4-0.5 (moderate contrast)
        rhythm_score = self._gaussian_score(value=rhythm_contrast, target=0.45, width=0.20)

        # Weighted combination
        score = (
            active_score * 0.30
            + dynamic_score * 0.25
            + concrete_score * 0.20
            + power_score * 0.15
            + rhythm_score * 0.10
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

        energy = metrics.get("energy", {})
        passive_ratio = energy.get("passive_ratio", 0.0)
        dynamic_ratio = energy.get("dynamic_verb_ratio", 0.0)
        abstract_ratio = energy.get("abstract_ratio", 0.0)
        power_density = energy.get("power_word_density", 0.0)
        rhythm_contrast = energy.get("rhythm_contrast", 0.0)

        if passive_ratio > 0.20:
            recommendations.append(
                f"High passive voice usage ({passive_ratio:.1%}, target <15%). "
                f"Convert passive constructions to active voice for more dynamic writing. "
                f"Example: 'The report was written by the team' → 'The team wrote the report'."
            )

        if dynamic_ratio < 0.10:
            recommendations.append(
                f"Low verb dynamism ({dynamic_ratio:.1%}, target >15%). "
                f"Replace static verbs (is, was, has, seems) with action verbs "
                f"(drives, transforms, accelerates, ignites)."
            )

        if abstract_ratio > 0.15:
            recommendations.append(
                f"High abstract language ({abstract_ratio:.1%}, target <10%). "
                f"Replace abstract terms (concept, methodology, framework) with "
                f"concrete, specific language readers can visualize."
            )

        if power_density < 0.01:
            recommendations.append(
                f"Low power word density ({power_density:.1%}, target >2%). "
                f"Add impactful words that evoke emotion or urgency: "
                f"critical, breakthrough, proven, essential, transform."
            )

        if rhythm_contrast < 0.25:
            recommendations.append(
                f"Monotonous sentence rhythm (contrast={rhythm_contrast:.2f}, target 0.35-0.55). "
                f"Vary sentence lengths more dramatically. Mix short punchy sentences "
                f"with longer flowing ones."
            )
        elif rhythm_contrast > 0.65:
            recommendations.append(
                f"Erratic sentence rhythm (contrast={rhythm_contrast:.2f}, target 0.35-0.55). "
                f"Smooth transitions between very short and very long sentences."
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
            "good": (65.0, 84.9),
            "acceptable": (45.0, 64.9),
            "poor": (0.0, 44.9),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _analyze_energy(self, text: str) -> Dict[str, Any]:
        """
        Analyze all energy metrics for a text sample.

        Uses research-backed lexicons (Brysbaert, Warriner) when available,
        falls back to curated word lists otherwise.

        Args:
            text: Text to analyze

        Returns:
            Dict with energy metrics
        """
        nlp = get_nlp()

        # Fallback metrics if spaCy unavailable
        if nlp is None:
            return self._analyze_energy_regex_fallback(text)

        doc = nlp(text)

        # Load lexicons (cached after first call)
        dynamic_verbs = get_dynamic_verbs()
        static_verbs = get_static_verbs()
        abstract_words = get_abstract_words()

        # 1. Passive voice detection
        passive_count = 0
        clause_count = 0
        for sent in doc.sents:
            clause_count += 1
            for token in sent:
                if token.dep_ == "nsubjpass" or token.dep_ == "auxpass":
                    passive_count += 1
                    break  # Count sentence once

        passive_ratio = passive_count / clause_count if clause_count > 0 else 0.0

        # 2. Verb dynamism
        verbs = [token.lemma_.lower() for token in doc if token.pos_ == "VERB"]
        total_verbs = len(verbs)
        dynamic_count = sum(1 for v in verbs if v in dynamic_verbs)
        static_count = sum(1 for v in verbs if v in static_verbs)

        dynamic_ratio = dynamic_count / total_verbs if total_verbs > 0 else 0.0
        static_ratio = static_count / total_verbs if total_verbs > 0 else 0.0

        # 3. Abstract language ratio
        # Uses Brysbaert concreteness norms when available, fallback to curated list
        words = [token.text.lower() for token in doc if token.is_alpha]
        total_words = len(words)

        # Try lexicon-based concreteness scoring first
        concreteness_scores = []
        abstract_count = 0
        for w in words:
            conc_score = get_word_concreteness(w)
            if conc_score is not None:
                concreteness_scores.append(conc_score)
                if conc_score < 2.5:  # Below mid-point = abstract
                    abstract_count += 1
            elif w in abstract_words:  # Fallback to curated list
                abstract_count += 1

        abstract_ratio = abstract_count / total_words if total_words > 0 else 0.0

        # Calculate mean concreteness if we have scores
        mean_concreteness = statistics.mean(concreteness_scores) if concreteness_scores else None

        # 4. Power words density
        # Uses Warriner dominance norms when available, fallback to curated list
        power_count = sum(1 for w in words if is_power_word(w))
        power_density = power_count / total_words if total_words > 0 else 0.0

        # 5. Rhythm contrast (adjacent sentence length coefficient of variation)
        sent_lengths = [len(list(sent)) for sent in doc.sents]
        rhythm_contrast = self._calculate_rhythm_contrast(sent_lengths)

        result = {
            "passive_ratio": round(passive_ratio, 4),
            "passive_count": passive_count,
            "clause_count": clause_count,
            "dynamic_verb_ratio": round(dynamic_ratio, 4),
            "static_verb_ratio": round(static_ratio, 4),
            "dynamic_verb_count": dynamic_count,
            "total_verbs": total_verbs,
            "abstract_ratio": round(abstract_ratio, 4),
            "abstract_count": abstract_count,
            "power_word_density": round(power_density, 4),
            "power_word_count": power_count,
            "total_words": total_words,
            "rhythm_contrast": round(rhythm_contrast, 4),
            "sentence_count": len(sent_lengths),
            "spacy_available": True,
        }

        # Add concreteness score if available from Brysbaert norms
        if mean_concreteness is not None:
            result["mean_concreteness"] = round(mean_concreteness, 3)
            result["concreteness_coverage"] = (
                round(len(concreteness_scores) / total_words, 3) if total_words > 0 else 0.0
            )

        return result

    def _analyze_energy_regex_fallback(self, text: str) -> Dict[str, Any]:
        """
        Regex-based fallback when spaCy is unavailable.

        Args:
            text: Text to analyze

        Returns:
            Dict with energy metrics (less accurate than spaCy version)
        """
        # Load lexicons (cached after first call)
        dynamic_verbs = get_dynamic_verbs()
        static_verbs = get_static_verbs()
        abstract_words = get_abstract_words()

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Passive voice detection (simplified: look for "was/were/been + past participle patterns")
        passive_pattern = r"\b(was|were|been|being|is|are)\s+\w+ed\b"
        passive_count = len(re.findall(passive_pattern, text, re.IGNORECASE))
        clause_count = len(sentences)
        passive_ratio = min(passive_count / clause_count, 1.0) if clause_count > 0 else 0.0

        # Word analysis
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        total_words = len(words)

        # Verb approximation (words ending in common verb patterns)
        verb_endings = r"\b\w+(ing|ed|ize|ify|ate)\b"
        approx_verbs = re.findall(verb_endings, text.lower())

        # Dynamic/static verb detection
        dynamic_count = sum(1 for w in words if w in dynamic_verbs)
        static_count = sum(1 for w in words if w in static_verbs)
        total_verbs = max(len(approx_verbs) + static_count, 1)

        dynamic_ratio = dynamic_count / total_verbs if total_verbs > 0 else 0.0

        # Abstract language - check lexicon first, then fallback
        abstract_count = 0
        concreteness_scores = []
        for w in words:
            conc_score = get_word_concreteness(w)
            if conc_score is not None:
                concreteness_scores.append(conc_score)
                if conc_score < 2.5:
                    abstract_count += 1
            elif w in abstract_words:
                abstract_count += 1

        abstract_ratio = abstract_count / total_words if total_words > 0 else 0.0

        # Power words - uses lexicon with fallback
        power_count = sum(1 for w in words if is_power_word(w))
        power_density = power_count / total_words if total_words > 0 else 0.0

        # Rhythm contrast
        sent_lengths = [len(s.split()) for s in sentences]
        rhythm_contrast = self._calculate_rhythm_contrast(sent_lengths)

        result = {
            "passive_ratio": round(passive_ratio, 4),
            "passive_count": passive_count,
            "clause_count": clause_count,
            "dynamic_verb_ratio": round(dynamic_ratio, 4),
            "static_verb_ratio": round(static_count / total_verbs if total_verbs > 0 else 0.0, 4),
            "dynamic_verb_count": dynamic_count,
            "total_verbs": total_verbs,
            "abstract_ratio": round(abstract_ratio, 4),
            "abstract_count": abstract_count,
            "power_word_density": round(power_density, 4),
            "power_word_count": power_count,
            "total_words": total_words,
            "rhythm_contrast": round(rhythm_contrast, 4),
            "sentence_count": len(sent_lengths),
            "spacy_available": False,
        }

        # Add concreteness score if available from Brysbaert norms
        if concreteness_scores:
            result["mean_concreteness"] = round(statistics.mean(concreteness_scores), 3)
            result["concreteness_coverage"] = (
                round(len(concreteness_scores) / total_words, 3) if total_words > 0 else 0.0
            )

        return result

    def _calculate_rhythm_contrast(self, sent_lengths: List[int]) -> float:
        """
        Calculate rhythm contrast as normalized mean absolute difference
        between adjacent sentence lengths.

        Args:
            sent_lengths: List of sentence lengths (in words or tokens)

        Returns:
            Rhythm contrast score (0.0 = monotonous, 1.0 = highly varied)
        """
        if len(sent_lengths) < 2:
            return 0.0

        # Calculate adjacent differences
        diffs = []
        for i in range(1, len(sent_lengths)):
            prev_len = sent_lengths[i - 1]
            curr_len = sent_lengths[i]
            avg_len = (prev_len + curr_len) / 2
            if avg_len > 0:
                # Normalized difference
                diff = abs(curr_len - prev_len) / avg_len
                diffs.append(diff)

        if not diffs:
            return 0.0

        # Mean normalized difference, capped at 1.0
        contrast = min(statistics.mean(diffs), 1.0)
        return contrast


# Backward compatibility alias
EnergyAnalyzer = EnergyDimension

# Module-level singleton - triggers self-registration on module import
_instance = EnergyDimension()
