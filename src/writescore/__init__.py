"""
AI Pattern Analyzer - Modular implementation

Main exports for backward compatibility with the original monolithic version.

This package provides a modular architecture for AI pattern analysis while
maintaining backward compatibility with code that imported from the original
analyze_ai_patterns.py file.

Version: 5.0.0 (Breaking Changes - Deprecated Dimension Removal)
"""

# Core analyzer and result classes
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.results import (
    AnalysisResults,
    DetailedAnalysis,
    # Optional: individual issue types for detailed analysis
    VocabInstance,
    HeadingIssue,
    UniformParagraph,
    EmDashInstance,
    TransitionInstance,
    SentenceBurstinessIssue,
    SyntacticIssue,
    FormattingIssue,
    HighPredictabilitySegment
)

# Scoring system
from writescore.scoring.dual_score import (
    DualScore,
    ScoreCategory,
    ScoreDimension,
    ImprovementAction,
    THRESHOLDS
)
from writescore.scoring.dual_score_calculator import calculate_dual_score

# History tracking
from writescore.history.tracker import (
    HistoricalScore,
    ScoreHistory
)

# CLI formatters
from writescore.cli.formatters import (
    format_report,
    format_detailed_report,
    format_dual_score_report
)

__all__ = [
    # Core
    'AIPatternAnalyzer',
    'AnalysisResults',
    'DetailedAnalysis',
    # Result detail classes
    'VocabInstance',
    'HeadingIssue',
    'UniformParagraph',
    'EmDashInstance',
    'TransitionInstance',
    'SentenceBurstinessIssue',
    'SyntacticIssue',
    'FormattingIssue',
    'HighPredictabilitySegment',
    # Scoring
    'DualScore',
    'ScoreCategory',
    'ScoreDimension',
    'ImprovementAction',
    'calculate_dual_score',
    'THRESHOLDS',
    # History
    'HistoricalScore',
    'ScoreHistory',
    # Formatters
    'format_report',
    'format_detailed_report',
    'format_dual_score_report',
]

__version__ = '5.0.0'  # Major version bump - BREAKING CHANGES (Story 2.0)
