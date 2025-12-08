"""
WriteScore - Writing quality scoring tool with AI pattern detection

Main exports for backward compatibility with the original monolithic version.

This package provides a modular architecture for AI pattern analysis while
maintaining backward compatibility with code that imported from the original
analyze_ai_patterns.py file.
"""

from importlib.metadata import version as _get_version

# Core analyzer and result classes
# CLI formatters
from writescore.cli.formatters import (
    format_detailed_report,
    format_dual_score_report,
    format_report,
)
from writescore.core.analyzer import AIPatternAnalyzer
from writescore.core.results import (
    AnalysisResults,
    DetailedAnalysis,
    EmDashInstance,
    FormattingIssue,
    HeadingIssue,
    HighPredictabilitySegment,
    SentenceBurstinessIssue,
    SyntacticIssue,
    TransitionInstance,
    UniformParagraph,
    # Optional: individual issue types for detailed analysis
    VocabInstance,
)

# History tracking
from writescore.history.tracker import HistoricalScore, ScoreHistory

# Scoring system
from writescore.scoring.dual_score import (
    THRESHOLDS,
    DualScore,
    ImprovementAction,
    ScoreCategory,
    ScoreDimension,
)
from writescore.scoring.dual_score_calculator import calculate_dual_score

__all__ = [
    # Core
    "AIPatternAnalyzer",
    "AnalysisResults",
    "DetailedAnalysis",
    # Result detail classes
    "VocabInstance",
    "HeadingIssue",
    "UniformParagraph",
    "EmDashInstance",
    "TransitionInstance",
    "SentenceBurstinessIssue",
    "SyntacticIssue",
    "FormattingIssue",
    "HighPredictabilitySegment",
    # Scoring
    "DualScore",
    "ScoreCategory",
    "ScoreDimension",
    "ImprovementAction",
    "calculate_dual_score",
    "THRESHOLDS",
    # History
    "HistoricalScore",
    "ScoreHistory",
    # Formatters
    "format_report",
    "format_detailed_report",
    "format_dual_score_report",
]

try:
    __version__ = _get_version("writescore")
except Exception:
    __version__ = "0.0.0"  # Fallback for development installs
