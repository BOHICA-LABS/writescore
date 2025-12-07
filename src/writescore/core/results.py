"""
Core result data structures for AI pattern analysis.

This module contains all dataclasses used to represent analysis results,
detailed findings, and exception types.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# EXCEPTIONS
# ============================================================================


class AnalysisError(Exception):
    """Base exception for analysis errors"""

    pass


class EmptyFileError(AnalysisError):
    """Raised when file has no analyzable content"""

    pass


class InsufficientDataError(AnalysisError):
    """Raised when not enough data for reliable analysis"""

    pass


# ============================================================================
# DETAILED MODE DATACLASSES
# ============================================================================


@dataclass
class VocabInstance:
    """Single AI vocabulary instance with location"""

    line_number: int
    word: str
    context: str
    full_line: str
    suggestions: List[str]


@dataclass
class HeadingIssue:
    """Heading issue with location"""

    line_number: int
    level: int
    text: str
    issue_type: str  # 'depth', 'parallelism', 'verbose'
    suggestion: str


@dataclass
class UniformParagraph:
    """Paragraph with uniform sentence lengths"""

    start_line: int
    end_line: int
    sentence_count: int
    mean_length: float
    stdev: float
    sentences: List[Tuple[int, str, int]]  # (line_num, text, word_count)
    problem: str
    suggestion: str


@dataclass
class EmDashInstance:
    """Em-dash instance with location"""

    line_number: int
    context: str
    suggestion: str
    problem: str = ""  # Optional problem description


@dataclass
class TransitionInstance:
    """Formulaic transition with location"""

    line_number: int
    transition: str
    context: str
    suggestions: List[str]


@dataclass
class SentenceBurstinessIssue:
    """Sentence uniformity problem with location"""

    start_line: int
    end_line: int
    sentence_count: int
    mean_length: float
    stdev: float
    problem: str
    sentences_preview: List[Tuple[int, str, int]]  # (line, text, word_count)
    suggestion: str


@dataclass
class SyntacticIssue:
    """Syntactic complexity issue with location"""

    line_number: int
    sentence: str
    issue_type: str  # 'passive', 'shallow', 'subordination'
    metric_value: float
    problem: str
    suggestion: str


@dataclass
class FormattingIssue:
    """Bold/italic overuse with location"""

    line_number: int
    issue_type: str  # 'bold_dense', 'italic_dense', 'consistent'
    context: str
    density: float
    problem: str
    suggestion: str


@dataclass
class HighPredictabilitySegment:
    """High GLTR score (AI-like) section"""

    start_line: int
    end_line: int
    segment_preview: str
    gltr_score: float
    problem: str
    suggestion: str


@dataclass
class DetailedAnalysis:
    """Comprehensive detailed analysis results"""

    file_path: str
    summary: Dict
    # Original detailed findings
    ai_vocabulary: List[VocabInstance] = field(default_factory=list)
    heading_issues: List[HeadingIssue] = field(default_factory=list)
    uniform_paragraphs: List[UniformParagraph] = field(default_factory=list)
    em_dashes: List[EmDashInstance] = field(default_factory=list)
    transitions: List[TransitionInstance] = field(default_factory=list)
    # ADVANCED: New detailed findings
    burstiness_issues: List[SentenceBurstinessIssue] = field(default_factory=list)
    syntactic_issues: List[SyntacticIssue] = field(default_factory=list)
    formatting_issues: List[FormattingIssue] = field(default_factory=list)
    high_predictability_segments: List[HighPredictabilitySegment] = field(default_factory=list)


# ============================================================================
# ANALYSIS RESULTS
# ============================================================================


@dataclass
class AnalysisResults:
    """Structured container for analysis results"""

    file_path: str

    # Basic metrics
    total_words: int
    total_sentences: int
    total_paragraphs: int

    # Perplexity dimension
    ai_vocabulary_count: int
    ai_vocabulary_per_1k: float
    ai_vocabulary_list: List[str]
    formulaic_transitions_count: int
    formulaic_transitions_list: List[str]

    # Burstiness dimension
    sentence_mean_length: float
    sentence_stdev: float
    sentence_min: int
    sentence_max: int
    sentence_range: Tuple[int, int]
    short_sentences_count: int  # <=10 words
    medium_sentences_count: int  # 11-25 words
    long_sentences_count: int  # >=30 words
    sentence_lengths: List[int]

    # Paragraph variation
    paragraph_mean_words: float
    paragraph_stdev: float
    paragraph_range: Tuple[int, int]

    # Lexical diversity
    unique_words: int
    lexical_diversity: float  # Type-Token Ratio

    # Structure dimension
    bullet_list_lines: int
    numbered_list_lines: int
    total_headings: int
    heading_depth: int  # Max heading level
    h1_count: int
    h2_count: int
    h3_count: int
    h4_plus_count: int
    headings_per_page: float

    # Heading patterns
    heading_parallelism_score: float  # 0-1, higher = more mechanical
    verbose_headings_count: int  # >8 words
    avg_heading_length: float

    # Voice dimension
    first_person_count: int
    direct_address_count: int
    contraction_count: int

    # Technical dimension
    domain_terms_count: int
    domain_terms_list: List[str]

    # Formatting dimension
    em_dash_count: int
    em_dashes_per_page: float
    bold_markdown_count: int
    italic_markdown_count: int

    # NEW: Enhanced formatting pattern analysis
    bold_per_1k_words: float = 0.0  # Bold density
    italic_per_1k_words: float = 0.0  # Italic density
    formatting_consistency_score: float = 0.0  # 0-1, higher = more mechanical

    # NEW: List usage analysis
    total_list_items: int = 0  # Total items in all lists
    ordered_list_items: int = 0  # Items in numbered lists
    unordered_list_items: int = 0  # Items in bullet lists
    list_to_text_ratio: float = 0.0  # Proportion of content in lists
    ordered_to_unordered_ratio: float = 0.0  # AI tends toward ~0.2 (61% unordered, 12% ordered)
    list_item_length_variance: float = 0.0  # Uniformity of list item lengths

    # NEW: Punctuation clustering analysis
    em_dash_positions: List[int] = field(default_factory=list)  # Paragraph positions
    em_dash_cascading_score: float = 0.0  # Detects declining pattern (AI marker)
    oxford_comma_count: int = 0  # "a, b, and c" pattern
    non_oxford_comma_count: int = 0  # "a, b and c" pattern
    oxford_comma_consistency: float = 0.0  # 1.0 = always Oxford (AI-like)
    semicolon_count: int = 0
    semicolon_per_1k_words: float = 0.0

    # NEW: Whitespace and paragraph structure analysis
    paragraph_length_variance: float = 0.0  # Higher variance = more human
    paragraph_uniformity_score: float = 0.0  # 0-1, higher = more uniform (AI-like)
    blank_lines_count: int = 0
    blank_lines_variance: float = 0.0  # Spacing pattern consistency
    text_density: float = 0.0  # Characters per line (lower = more whitespace)

    # NEW: Code block analysis (for technical writing)
    code_block_count: int = 0
    code_blocks_with_lang: int = 0  # Properly specified language
    code_lang_consistency: float = 0.0  # 1.0 = all specified (AI-like)
    avg_code_comment_density: float = 0.0  # Comments per line of code

    # NEW: Enhanced heading hierarchy analysis
    heading_hierarchy_skips: int = 0  # Count of skipped levels (humans do this, AI doesn't)
    heading_strict_adherence: float = 0.0  # 1.0 = never skips (AI-like)
    heading_length_variance: float = 0.0  # Variation in heading lengths

    # NEW: Structural pattern analysis (Phase 1 - High ROI patterns)
    paragraph_cv: float = 0.0  # Coefficient of variation for paragraph lengths (CV <0.3 = AI-like)
    paragraph_cv_mean: float = 0.0  # Mean paragraph length in words
    paragraph_cv_stddev: float = 0.0  # Standard deviation of paragraph lengths
    paragraph_cv_assessment: str = ""  # EXCELLENT/GOOD/FAIR/POOR
    paragraph_cv_score: float = 0.0  # Quality score contribution (0-10)
    paragraph_count: int = 0  # Number of paragraphs analyzed

    section_variance_pct: float = 0.0  # Variance in H2 section lengths (variance <15% = AI-like)
    section_count: int = 0  # Number of sections analyzed
    section_variance_assessment: str = ""  # EXCELLENT/GOOD/FAIR/POOR
    section_variance_score: float = 0.0  # Quality score contribution (0-8)
    section_uniform_clusters: int = 0  # Count of 3+ sections with similar lengths

    list_max_depth: int = 0  # Maximum nesting depth across all lists
    list_avg_depth: float = 0.0  # Average nesting depth
    list_total_items: int = 0  # Total list items analyzed
    list_depth_assessment: str = ""  # EXCELLENT/GOOD/FAIR/POOR
    list_depth_score: float = 0.0  # Quality score contribution (0-6)

    # Readability (optional - requires textstat)
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    gunning_fog: Optional[float] = None
    smog_index: Optional[float] = None

    # Enhanced lexical metrics (optional - requires NLTK)
    mtld_score: Optional[float] = None  # Moving Average Type-Token Ratio
    stemmed_diversity: Optional[float] = None  # Diversity after stemming

    # Sentiment metrics (optional - requires VADER/TextBlob)
    sentiment_variance: Optional[float] = None  # Paragraph sentiment variation
    sentiment_mean: Optional[float] = None  # Average sentiment
    sentiment_flatness_score: Optional[str] = None  # HIGH/MEDIUM/LOW

    # Syntactic metrics (optional - requires spaCy)
    syntactic_repetition_score: Optional[float] = None  # 0-1, higher = more repetitive
    pos_diversity: Optional[float] = None  # Part-of-speech tag diversity
    avg_dependency_depth: Optional[float] = None  # Syntactic complexity

    # Stylometric metrics (optional - requires Textacy)
    automated_readability: Optional[float] = None
    textacy_diversity: Optional[float] = None

    # True perplexity (optional - requires Transformers)
    gpt2_perplexity: Optional[float] = None  # Lower = more predictable (AI-like)
    distilgpt2_perplexity: Optional[float] = None  # DistilGPT-2 perplexity (faster, modern)

    # ADVANCED: GLTR token ranking (optional - requires Transformers)
    gltr_top10_percentage: Optional[float] = (
        None  # % tokens in top-10 predictions (AI: >70%, Human: <55%)
    )
    gltr_top100_percentage: Optional[float] = None  # % tokens in top-100 predictions
    gltr_mean_rank: Optional[float] = None  # Average token rank in model distribution
    gltr_rank_variance: Optional[float] = None  # Variance in token ranks
    gltr_likelihood: Optional[float] = None  # AI likelihood from GLTR (0-1)

    # ADVANCED: Advanced lexical diversity (optional - requires scipy)
    hdd_score: Optional[float] = (
        None  # Hypergeometric Distribution D (most robust, AI: 0.40-0.55, Human: 0.65-0.85)
    )
    yules_k: Optional[float] = None  # Yule's K vocabulary richness (AI: 100-150, Human: 60-90)
    maas_score: Optional[float] = None  # Maas length-corrected diversity
    vocab_concentration: Optional[float] = None  # Zipfian vocabulary concentration

    # Advanced lexical diversity - Textacy-based (optional - requires textacy+spacy)
    mattr: Optional[float] = (
        None  # Moving Average Type-Token Ratio (window=100, AI: <0.65, Human: ≥0.70)
    )
    rttr: Optional[float] = None  # Root Type-Token Ratio (AI: <7.5, Human: ≥7.5)
    mattr_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR
    rttr_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    # Enhanced heading length analysis
    heading_length_short_pct: Optional[float] = None  # % of headings ≤5 words
    heading_length_medium_pct: Optional[float] = None  # % of headings 6-8 words
    heading_length_long_pct: Optional[float] = None  # % of headings ≥9 words
    heading_length_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    # Subsection asymmetry analysis
    subsection_counts: Optional[List[int]] = None  # H3 counts under each H2
    subsection_cv: Optional[float] = (
        None  # Coefficient of variation (CV <0.3 = AI-like, ≥0.6 = human)
    )
    subsection_uniform_count: Optional[int] = (
        None  # Count of sections with 3-4 subsections (AI signature)
    )
    subsection_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    # H4 subsection asymmetry analysis (H4 counts under each H3)
    h4_counts: Optional[List[int]] = None  # H4 counts under each H3
    h4_subsection_cv: Optional[float] = None  # Coefficient of variation for H4 distribution
    h4_uniform_count: Optional[int] = None  # Count of H3 sections with 2-3 H4s (AI signature)
    h4_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR
    h4_h3_sections_analyzed: Optional[int] = (
        None  # Number of H3 sections analyzed for H4 distribution
    )

    # Multi-level combined structure score (research-backed domain-specific analysis)
    combined_structure_score: Optional[float] = None  # Combined weighted score (0-24 max)
    combined_structure_assessment: Optional[str] = None  # Overall assessment
    combined_structure_domain: Optional[str] = (
        None  # Domain used for thresholds (academic/technical/etc)
    )
    combined_structure_prob_human: Optional[float] = None  # Probability of human authorship (0-1)
    combined_h2_score: Optional[float] = None  # H2 section length score
    combined_h2_assessment: Optional[str] = None  # H2 assessment
    combined_h3_score: Optional[float] = None  # H3 subsection count score
    combined_h3_assessment: Optional[str] = None  # H3 assessment
    combined_h4_score: Optional[float] = None  # H4 subsection count score
    combined_h4_assessment: Optional[str] = None  # H4 assessment

    # Heading depth variance analysis
    heading_transitions: Optional[Dict[str, int]] = None  # Transition counts (e.g., H1→H2: 5)
    heading_depth_pattern: Optional[str] = None  # VARIED/SEQUENTIAL/RIGID
    heading_has_lateral: Optional[bool] = None  # Has H3→H3 lateral moves
    heading_has_jumps: Optional[bool] = None  # Has H3→H1 jumps
    heading_depth_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    # PHASE 3: AST-based structure analysis and advanced patterns (optional - requires marko)
    blockquote_total: Optional[int] = None  # Total blockquotes in document
    blockquote_per_page: Optional[float] = (
        None  # Blockquotes per 250-word page (AI: 4+, Human: 0-2)
    )
    blockquote_avg_length: Optional[float] = None  # Average blockquote length in words
    blockquote_section_start_clustering: Optional[float] = None  # % at section starts (AI: >50%)
    blockquote_score: Optional[float] = None  # Quality score contribution (0-10)
    blockquote_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    link_total: Optional[int] = None  # Total markdown links
    link_generic_count: Optional[int] = None  # Generic anchor text count
    link_generic_ratio: Optional[float] = None  # Generic/total ratio (AI: >40%, Human: <10%)
    link_generic_examples: Optional[List[str]] = None  # Example generic anchors
    link_density: Optional[float] = None  # Links per 1000 words
    link_anchor_score: Optional[float] = None  # Quality score contribution (0-8)
    link_anchor_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    punctuation_colon_cv: Optional[float] = None  # Colon spacing coefficient of variation
    punctuation_primary_cv: Optional[float] = (
        None  # Primary punctuation CV (AI: <0.35, Human: ≥0.7)
    )
    punctuation_spacing_score: Optional[float] = None  # Quality score contribution (0-6)
    punctuation_spacing_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    list_has_mixed_types: Optional[bool] = None  # Has both ordered and unordered lists
    list_symmetry_score: Optional[float] = None  # 0-1, higher = more symmetric (AI-like)
    list_ast_score: Optional[float] = None  # Quality score contribution (0-8)
    list_ast_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    code_total_blocks: Optional[int] = None  # Total fenced code blocks
    code_with_language: Optional[int] = None  # Blocks with language declarations
    code_lang_declaration_ratio: Optional[float] = None  # Declared/total (AI: <60%, Human: >90%)
    code_avg_length: Optional[float] = None  # Average code block length in lines
    code_ast_score: Optional[float] = None  # Quality score contribution (0-4)
    code_ast_assessment: Optional[str] = None  # EXCELLENT/GOOD/FAIR/POOR

    # ADVANCED: Enhanced syntactic analysis (optional - requires spaCy)
    avg_tree_depth: Optional[float] = None  # Dependency tree depth (AI: 2-3, Human: 4-6)
    subordination_index: Optional[float] = (
        None  # Subordinate clause frequency (AI: <0.1, Human: >0.15)
    )
    passive_constructions: Optional[int] = None  # Passive voice count
    morphological_richness: Optional[int] = None  # Unique morphological forms

    # ADVANCED: Comprehensive stylometrics
    function_word_ratio: Optional[float] = None  # Stop word density (most discriminative)
    hapax_percentage: Optional[float] = None  # Words appearing once (vocabulary richness)
    however_per_1k: Optional[float] = None  # AI marker: 5-10 per 1k (human: 1-3)
    moreover_per_1k: Optional[float] = None  # AI marker: 3-8 per 1k (human: 0-2)
    however_count: Optional[int] = None  # Total count of "however"
    moreover_count: Optional[int] = None  # Total count of "moreover"
    total_ai_markers_per_1k: Optional[float] = None  # Combined however+moreover per 1k
    punctuation_density: Optional[float] = None  # Punctuation frequency
    ttr_stability: Optional[float] = None  # TTR variance across sections

    # ADVANCED: RoBERTa sentiment analysis (replaces VADER)
    roberta_sentiment_variance: Optional[float] = None  # Emotional flatness detection
    roberta_sentiment_mean: Optional[float] = None  # Average sentiment intensity
    roberta_emotionally_flat: Optional[bool] = None  # True if variance < 0.1 (AI signature)
    roberta_avg_confidence: Optional[float] = None  # Average model confidence

    # ADVANCED: DetectGPT perturbation analysis (optional - requires Transformers)
    detectgpt_perturbation_variance: Optional[float] = None  # Loss variance after perturbations
    detectgpt_original_loss: Optional[float] = None  # Original text loss
    detectgpt_is_likely_ai: Optional[bool] = None  # True if variance < 0.05

    # ADVANCED: RoBERTa AI detection (optional - requires Transformers)
    roberta_ai_likelihood: Optional[float] = None  # Overall AI probability (0-1)
    roberta_prediction_variance: Optional[float] = None  # Consistency across chunks
    roberta_consistent_predictions: Optional[bool] = None  # All chunks agree

    # Story 1.4.11: Core dimension scores (12 total)
    perplexity_score: str = ""  # HIGH/MEDIUM/LOW/VERY LOW
    burstiness_score: str = ""
    structure_score: str = ""
    voice_score: str = ""
    formatting_score: str = ""
    readability_score: str = ""  # NEW: Readability metrics (Flesch, Gunning Fog)
    lexical_score: str = ""  # NEW: Basic lexical diversity (TTR, unique words)
    sentiment_score: str = ""  # Sentiment variation
    syntactic_score: str = ""  # Syntactic naturalness
    predictability_score: str = ""  # NEW: GLTR-based predictability (replaces gltr_score)
    advanced_lexical_score: str = ""  # HDD/Yule's K/MATTR/RTTR
    transition_marker_score: str = ""  # NEW: Transition marker patterns
    figurative_language_score: str = ""  # NEW: Figurative language patterns (Story 2.1)

    # Figurative language metrics (Story 2.1)
    figurative_simile_count: Optional[int] = None  # Total similes detected
    figurative_metaphor_count: Optional[int] = None  # Total metaphors detected
    figurative_idiom_count: Optional[int] = None  # Total idioms detected
    figurative_ai_cliche_count: Optional[int] = None  # AI clichés detected
    figurative_total_count: Optional[int] = None  # Total figurative expressions
    figurative_frequency_per_1k: Optional[float] = None  # Figurative expressions per 1k words
    figurative_types_detected: Optional[int] = None  # Number of different types found (0-3)

    # Sentiment distribution (only populated when 3+ idioms detected)
    figurative_sentiment_positive_pct: Optional[float] = None  # % positive sentiment idioms
    figurative_sentiment_negative_pct: Optional[float] = None  # % negative sentiment idioms
    figurative_sentiment_neutral_pct: Optional[float] = None  # % neutral sentiment idioms
    figurative_sentiment_deviation: Optional[float] = (
        None  # Deviation from optimal technical writing profile
    )

    # Semantic coherence metrics (Story 2.3)
    semantic_coherence_score: str = ""  # NEW: Semantic coherence patterns
    semantic_paragraph_cohesion: Optional[float] = None  # Paragraph cohesion score (0-1)
    semantic_topic_consistency: Optional[float] = None  # Topic consistency score (0-1)
    semantic_discourse_flow: Optional[float] = None  # Discourse flow score (0-1)
    semantic_conceptual_depth: Optional[float] = None  # Conceptual depth score (0-1)
    semantic_low_cohesion_paragraphs: Optional[List[str]] = (
        None  # Evidence: Paragraphs with low cohesion
    )
    semantic_topic_shifts: Optional[List[str]] = None  # Evidence: Locations of topic shifts
    semantic_weak_transitions: Optional[List[str]] = None  # Evidence: Weak paragraph transitions

    # Legacy/derived scores
    technical_score: str = ""  # Derived from voice dimension
    ai_detection_score: str = ""  # RoBERTa AI detector score (legacy)

    # Enhanced structural dimension scores (legacy, Phase 1 patterns)
    bold_italic_score: str = ""  # Bold/italic formatting patterns
    list_usage_score: str = ""  # List structure and distribution
    punctuation_score: str = ""  # Punctuation clustering patterns
    whitespace_score: str = ""  # Paragraph/whitespace distribution
    code_structure_score: str = ""  # Code block patterns (if applicable)
    heading_hierarchy_score: str = ""  # Heading level adherence
    structural_patterns_score: str = ""  # Phase 1: Paragraph CV, Section Variance, List Nesting

    overall_assessment: str = ""

    # Story 1.10: Dynamic Reporting System fields
    # These fields are populated by the dynamic reporter and must reflect exactly 12 dimensions in v5.0.0
    dimension_results: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )  # Should have 12 keys
    overall_score: float = 0.0  # Numeric overall score (0-100)
    execution_time: float = 0.0  # Analysis execution time in seconds
    dimension_count: int = 0  # Number of dimensions analyzed - MUST be 12 in v5.0.0
