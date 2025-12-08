"""
Scoring system module.
"""

from writescore.scoring.dual_score import (
    THRESHOLDS,
    DualScore,
    ImprovementAction,
    ScoreCategory,
    ScoreDimension,
)
from writescore.scoring.dual_score_calculator import calculate_dual_score

__all__ = [
    "DualScore",
    "ScoreCategory",
    "ScoreDimension",
    "ImprovementAction",
    "THRESHOLDS",
    "calculate_dual_score",
]
