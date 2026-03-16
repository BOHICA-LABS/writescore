"""
Lexicon loader for research-backed psycholinguistic word lists.

Provides access to:
- Brysbaert concreteness norms (37k+ words, 1-5 scale)
- Warriner affective norms (valence, arousal, dominance)
- Dynamic/action verb classifications
- Abstract concept word lists

Uses lazy loading with caching for performance.
Falls back to curated subset if full datasets unavailable.
"""

import csv
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Set

# Package data directory
DATA_DIR = Path(__file__).parent.parent / "data"

# Lazy-loaded lexicon caches
_concreteness_cache: Optional[Dict[str, float]] = None
_dominance_cache: Optional[Dict[str, float]] = None


def get_data_dir() -> Path:
    """Get or create the data directory for lexicon files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


@lru_cache(maxsize=1)
def load_concreteness_norms() -> Dict[str, float]:
    """
    Load Brysbaert concreteness norms.

    Returns dict mapping lowercase word -> concreteness score (1.0-5.0).
    Higher scores = more concrete (e.g., "apple" ~4.8).
    Lower scores = more abstract (e.g., "freedom" ~1.9).

    Falls back to curated abstract words list if CSV unavailable.
    """
    csv_path = get_data_dir() / "brysbaert_concreteness.csv"

    if csv_path.exists():
        norms = {}
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get("Word", "").lower().strip()
                try:
                    conc = float(row.get("Conc.M", 3.0))
                    if word:
                        norms[word] = conc
                except (ValueError, TypeError):
                    continue
        return norms

    # Fallback: return empty dict, use hardcoded abstract words
    return {}


@lru_cache(maxsize=1)
def load_dominance_norms() -> Dict[str, float]:
    """
    Load Warriner dominance norms for power word detection.

    Returns dict mapping lowercase word -> dominance score (1.0-9.0).
    Higher scores = more dominant/powerful (e.g., "conquer" ~7.0).
    Lower scores = more submissive (e.g., "surrender" ~3.0).

    Falls back to curated power words list if CSV unavailable.
    """
    csv_path = get_data_dir() / "warriner_affective.csv"

    if csv_path.exists():
        norms = {}
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get("Word", "").lower().strip()
                try:
                    dom = float(row.get("D.Mean.Sum", 5.0))
                    if word:
                        norms[word] = dom
                except (ValueError, TypeError):
                    continue
        return norms

    # Fallback: return empty dict, use hardcoded power words
    return {}


def get_abstract_words(threshold: float = 2.5) -> Set[str]:
    """
    Get set of abstract words (low concreteness).

    Args:
        threshold: Concreteness score below which words are considered abstract.
                  Default 2.5 (mid-point of 1-5 scale).

    Returns:
        Set of abstract words (lowercase).
    """
    norms = load_concreteness_norms()

    if norms:
        return {word for word, score in norms.items() if score < threshold}

    # Fallback: curated abstract words from research
    return {
        # Conceptual terms
        "concept",
        "idea",
        "theory",
        "principle",
        "notion",
        "aspect",
        "approach",
        "perspective",
        "framework",
        "paradigm",
        "methodology",
        "strategy",
        "process",
        "system",
        "structure",
        "mechanism",
        # Relational terms
        "factor",
        "element",
        "component",
        "dimension",
        "context",
        "relationship",
        "connection",
        "correlation",
        "association",
        "implication",
        "significance",
        "importance",
        "relevance",
        # Capability terms
        "capability",
        "capacity",
        "potential",
        "possibility",
        "opportunity",
        "challenge",
        "issue",
        "problem",
        "situation",
        "circumstance",
        # Epistemic terms
        "consideration",
        "assumption",
        "hypothesis",
        "proposition",
        "characteristic",
        "attribute",
        "property",
        "quality",
        "nature",
        # Modal terms
        "manner",
        "fashion",
        "way",
        "means",
        "method",
        "technique",
        "basis",
        "foundation",
        "premise",
        "rationale",
        "justification",
    }


def get_power_words(threshold: float = 6.5) -> Set[str]:
    """
    Get set of power words (high dominance).

    Args:
        threshold: Dominance score above which words are considered powerful.
                  Default 6.5 (upper third of 1-9 scale).

    Returns:
        Set of power words (lowercase).
    """
    norms = load_dominance_norms()

    if norms:
        return {word for word, score in norms.items() if score > threshold}

    # Fallback: curated power words from marketing/psychology research
    return {
        # Urgency
        "now",
        "immediately",
        "instant",
        "urgent",
        "critical",
        "essential",
        "deadline",
        "limited",
        "hurry",
        "fast",
        "quick",
        "rapid",
        # Fear/Danger
        "dangerous",
        "threat",
        "risk",
        "warning",
        "alert",
        "beware",
        "catastrophe",
        "crisis",
        "devastating",
        "fatal",
        "severe",
        # Exclusivity
        "exclusive",
        "secret",
        "hidden",
        "insider",
        "confidential",
        "private",
        "rare",
        "unique",
        "special",
        "premium",
        "elite",
        # Power/Strength
        "powerful",
        "strong",
        "force",
        "dominant",
        "unstoppable",
        "invincible",
        "mighty",
        "fierce",
        "bold",
        "fearless",
        "brave",
        # Discovery
        "discover",
        "reveal",
        "uncover",
        "expose",
        "breakthrough",
        "revolutionary",
        "innovative",
        "cutting-edge",
        "pioneering",
        "groundbreaking",
        # Emotion
        "amazing",
        "incredible",
        "astonishing",
        "stunning",
        "remarkable",
        "extraordinary",
        "shocking",
        "surprising",
        "unexpected",
        # Trust
        "proven",
        "guaranteed",
        "certified",
        "authentic",
        "genuine",
        "reliable",
        "trusted",
        "verified",
        "official",
        "secure",
    }


def get_dynamic_verbs() -> Set[str]:
    """
    Get set of dynamic/action verbs (high energy).

    Based on verb semantics research - verbs implying motion,
    force, change, or impact.

    Returns:
        Set of dynamic verb lemmas (lowercase).
    """
    # These are based on VerbNet motion/force classes
    # and psycholinguistic research on verb imageability
    return {
        # Motion verbs
        "accelerate",
        "bolt",
        "charge",
        "chase",
        "climb",
        "crash",
        "dart",
        "dash",
        "dive",
        "dodge",
        "drop",
        "escape",
        "flee",
        "fly",
        "gallop",
        "hurtle",
        "jump",
        "launch",
        "leap",
        "lunge",
        "plunge",
        "race",
        "rocket",
        "rush",
        "soar",
        "speed",
        "sprint",
        "storm",
        "surge",
        "sweep",
        "zoom",
        # Force/impact verbs
        "attack",
        "blast",
        "break",
        "burst",
        "capture",
        "clash",
        "collapse",
        "collide",
        "conquer",
        "crush",
        "demolish",
        "destroy",
        "devour",
        "erupt",
        "explode",
        "fight",
        "fire",
        "force",
        "grab",
        "grasp",
        "grip",
        "hammer",
        "hit",
        "hurl",
        "ignite",
        "impact",
        "invade",
        "jolt",
        "kill",
        "pierce",
        "power",
        "propel",
        "punch",
        "push",
        "rip",
        "seize",
        "shatter",
        "shoot",
        "slam",
        "slash",
        "smash",
        "snatch",
        "squeeze",
        "strike",
        "tackle",
        "tear",
        "thrust",
        "wreck",
        # Transformation verbs
        "achieve",
        "build",
        "catapult",
        "challenge",
        "command",
        "create",
        "cut",
        "dominate",
        "drive",
        "execute",
        "lead",
        "master",
        "outpace",
        "overcome",
        "overpower",
        "spark",
        "transform",
        "trigger",
        "triumph",
        "unleash",
        "win",
    }


def get_static_verbs() -> Set[str]:
    """
    Get set of static/stative verbs (low energy).

    Verbs that describe states rather than actions.

    Returns:
        Set of static verb lemmas (lowercase).
    """
    return {
        # Be verbs
        "be",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        "am",
        # Have verbs
        "have",
        "has",
        "had",
        "having",
        # Do verbs (auxiliary)
        "do",
        "does",
        "did",
        # Linking/state verbs
        "seem",
        "appear",
        "become",
        "remain",
        "stay",
        "exist",
        "contain",
        "consist",
        "comprise",
        "include",
        "belong",
        "own",
        "possess",
        # Mental state verbs
        "know",
        "understand",
        "believe",
        "think",
        "feel",
        "want",
        "need",
        "like",
        "love",
        "hate",
        "prefer",
        # Relational verbs
        "mean",
        "represent",
        "signify",
        "indicate",
        "resemble",
        "equal",
        "involve",
        "require",
    }


def get_word_concreteness(word: str) -> Optional[float]:
    """
    Get concreteness score for a single word.

    Args:
        word: Word to look up (case-insensitive)

    Returns:
        Concreteness score (1.0-5.0) or None if not in lexicon.
    """
    norms = load_concreteness_norms()
    return norms.get(word.lower().strip())


def get_word_dominance(word: str) -> Optional[float]:
    """
    Get dominance score for a single word.

    Args:
        word: Word to look up (case-insensitive)

    Returns:
        Dominance score (1.0-9.0) or None if not in lexicon.
    """
    norms = load_dominance_norms()
    return norms.get(word.lower().strip())


def is_abstract(word: str, threshold: float = 2.5) -> bool:
    """
    Check if a word is abstract.

    Args:
        word: Word to check (case-insensitive)
        threshold: Concreteness score threshold

    Returns:
        True if word is abstract (below threshold or in fallback set)
    """
    score = get_word_concreteness(word)
    if score is not None:
        return score < threshold

    # Fallback: check hardcoded set
    return word.lower().strip() in get_abstract_words()


def is_power_word(word: str, threshold: float = 6.5) -> bool:
    """
    Check if a word is a power word.

    Args:
        word: Word to check (case-insensitive)
        threshold: Dominance score threshold

    Returns:
        True if word is powerful (above threshold or in fallback set)
    """
    score = get_word_dominance(word)
    if score is not None:
        return score > threshold

    # Fallback: check hardcoded set
    return word.lower().strip() in get_power_words()
