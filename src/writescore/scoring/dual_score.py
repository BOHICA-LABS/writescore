"""
Dual scoring system for AI pattern detection.

This module contains the dual scoring system that provides both:
1. Detection Risk Score (0-100, lower is better)
2. Quality Score (0-100, higher is better)

It also includes scoring thresholds and improvement action tracking.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# ============================================================================
# SCORING THRESHOLDS - Research-backed constants for AI pattern detection
# ============================================================================


@dataclass
class ScoringThresholds:
    """
    Research-backed thresholds for AI pattern detection.

    All thresholds based on research from:
    - GPTZero methodology (perplexity & burstiness)
    - Originality.AI pattern recognition
    - Academic NLP studies on AI detection
    - Stanford research on demographic bias
    - MIT/Northeastern research on syntactic templates

    Sources:
    - ai-detection-patterns.md
    - formatting-humanization-patterns.md
    - heading-humanization-patterns.md
    - humanization-techniques.md
    """

    # PERPLEXITY (Vocabulary Patterns)
    AI_VOCAB_VERY_LOW_THRESHOLD: float = 10.0  # per 1k words - extreme AI marker
    AI_VOCAB_LOW_THRESHOLD: float = 5.0  # per 1k words - needs improvement
    AI_VOCAB_MEDIUM_THRESHOLD: float = 2.0  # per 1k words - acceptable

    # BURSTINESS (Sentence Variation)
    SENTENCE_STDEV_HIGH: float = 10.0  # Strong variation (human-like)
    SENTENCE_STDEV_MEDIUM: float = 6.0  # Moderate variation
    SENTENCE_STDEV_LOW: float = 3.0  # Weak variation (AI-like)
    SHORT_SENTENCE_MIN_RATIO: float = 0.15  # Minimum 15% short sentences
    LONG_SENTENCE_MIN_RATIO: float = 0.15  # Minimum 15% long sentences

    # STRUCTURE (Organization)
    FORMULAIC_TRANSITIONS_MAX_PER_PAGE: int = 3
    HEADING_MAX_DEPTH: int = 3  # H1, H2, H3 maximum
    HEADING_PARALLELISM_HIGH: float = 0.7  # Mechanical parallelism
    HEADING_PARALLELISM_MEDIUM: float = 0.4
    HEADING_VERBOSE_RATIO: float = 0.3  # >30% verbose headings

    # VOICE & AUTHENTICITY
    CONTRACTION_RATIO_GOOD: float = 1.0  # >1% contraction use
    FIRST_PERSON_MIN_GOOD: int = 3  # Minimum for personal voice
    DIRECT_ADDRESS_MIN_GOOD: int = 5  # Minimum "you" usage

    # TECHNICAL DEPTH (Domain Expertise)
    DOMAIN_TERMS_HIGH_PER_1K: float = 20.0
    DOMAIN_TERMS_MEDIUM_PER_1K: float = 10.0
    DOMAIN_TERMS_LOW_PER_1K: float = 5.0
    DOMAIN_TERMS_VERY_LOW_PER_1K: float = 0.5

    # FORMATTING (Em-dashes) - STRONGEST AI SIGNAL
    EM_DASH_MAX_PER_PAGE: float = 2.0  # Maximum acceptable
    EM_DASH_MEDIUM_PER_PAGE: float = 4.0  # Moderate issue
    EM_DASH_AI_THRESHOLD_PER_PAGE: float = 3.0  # Above this = AI marker

    # BOLD/ITALIC FORMATTING PATTERNS (NEW)
    BOLD_HUMAN_MAX_PER_1K: float = 5.0  # Human baseline: 1-5 per 1k
    BOLD_AI_MIN_PER_1K: float = 10.0  # AI typical: 10-50 per 1k
    BOLD_EXTREME_AI_PER_1K: float = 20.0  # ChatGPT extreme overuse
    FORMATTING_CONSISTENCY_AI_THRESHOLD: float = 0.7  # Mechanical consistency
    FORMATTING_CONSISTENCY_MEDIUM: float = 0.5

    # LIST USAGE PATTERNS (NEW)
    LIST_RATIO_HIGH_THRESHOLD: float = 0.40  # >40% content in lists = AI
    LIST_RATIO_MEDIUM_THRESHOLD: float = 0.25  # >25% = moderate
    LIST_ORDERED_UNORDERED_AI_MIN: float = 0.15  # AI typical ratio range
    LIST_ORDERED_UNORDERED_AI_MAX: float = 0.25
    LIST_ITEM_VARIANCE_MIN: float = 5.0

    # PUNCTUATION CLUSTERING (NEW) - VERY HIGH VALUE
    EM_DASH_CASCADING_STRONG: float = 0.7  # >0.7 = strong AI marker (95% accuracy)
    EM_DASH_CASCADING_MODERATE: float = 0.5
    EM_DASH_CASCADING_WEAK: float = 0.3
    OXFORD_COMMA_ALWAYS: float = 0.9  # Perfect consistency = AI-like
    OXFORD_COMMA_USUALLY: float = 0.75
    OXFORD_COMMA_MIN_INSTANCES: int = 3  # Need 3+ for reliable signal

    # WHITESPACE & PARAGRAPH STRUCTURE (NEW)
    PARAGRAPH_UNIFORMITY_AI_THRESHOLD: float = 0.7  # >0.7 = uniform (AI-like)
    PARAGRAPH_UNIFORMITY_MEDIUM: float = 0.5
    PARAGRAPH_UNIFORMITY_LOW: float = 0.3  # High variance (human-like)

    # CODE STRUCTURE (NEW)
    CODE_LANG_PERFECT_CONSISTENCY: float = 1.0
    CODE_LANG_HIGH_CONSISTENCY: float = 0.8
    CODE_MIN_BLOCKS_FOR_PERFECT_FLAG: int = 3

    # HEADING HIERARCHY (NEW)
    HEADING_PERFECT_ADHERENCE: float = 1.0  # Never skips levels = AI-like
    HEADING_HIGH_ADHERENCE: float = 0.9
    HEADING_MIN_FOR_PERFECT_FLAG: int = 5  # Need 5+ headings for signal

    # GPT-2 PERPLEXITY (Optional - Transformers required)
    GPT2_PERPLEXITY_AI_LIKE: float = 50.0  # <50 = AI-like
    GPT2_PERPLEXITY_HUMAN_LIKE: float = 150.0  # >150 = human-like

    # ANALYSIS MINIMUMS (Quality Thresholds)
    MIN_WORDS_FOR_ANALYSIS: int = 50  # Minimum words required
    MIN_SENTENCES_FOR_BURSTINESS: int = 5  # Minimum for sentence variation


# Global instance of thresholds (can be customized per project)
THRESHOLDS = ScoringThresholds()


# ============================================================================
# DUAL SCORING SYSTEM
# ============================================================================


@dataclass
class ScoreDimension:
    """Individual dimension score"""

    name: str
    score: float  # 0-max
    max_score: float
    percentage: float  # 0-100
    impact: str  # 'NONE', 'LOW', 'MEDIUM', 'HIGH'
    gap: float  # Points below max
    raw_value: Optional[float] = None  # Original metric value
    recommendation: Optional[str] = None


@dataclass
class ScoreCategory:
    """Category score breakdown"""

    name: str
    total: float
    max_total: float
    percentage: float
    dimensions: List[ScoreDimension]


@dataclass
class ImprovementAction:
    """Recommended improvement with impact"""

    priority: int
    dimension: str
    current_score: float
    max_score: float
    potential_gain: float
    impact_level: str
    action: str
    effort_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    line_references: List[int] = field(default_factory=list)


@dataclass
class DualScore:
    """Dual scoring result with optimization path"""

    # Main scores
    detection_risk: float  # 0-100 (lower = better, less detectable)
    quality_score: float  # 0-100 (higher = better, more human-like)

    # Interpretations
    detection_interpretation: str
    quality_interpretation: str

    # Targets
    detection_target: float
    quality_target: float

    # Gaps
    detection_gap: float  # How far above target (negative = under target)
    quality_gap: float  # How far below target (positive = need improvement)

    # Breakdowns
    categories: List[ScoreCategory]

    # Optimization
    improvements: List[ImprovementAction]
    path_to_target: List[ImprovementAction]  # Sorted by ROI
    estimated_effort: str  # 'MINIMAL', 'LIGHT', 'MODERATE', 'SUBSTANTIAL', 'EXTENSIVE'

    # Metadata
    timestamp: str
    file_path: str
    total_words: int


# Placeholder for calculate_dual_score function (to be implemented from main file)
def calculate_dual_score(results):
    """
    Calculate dual scores from analysis results.

    This function will be extracted from the main analyze_ai_patterns.py file.
    """
    raise NotImplementedError("calculate_dual_score will be extracted during refactoring")
