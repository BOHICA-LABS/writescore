"""
Tests for mode tracking in history (Story 1.4.9 Task 3).

Tests cover:
- analysis_mode field in HistoricalScore
- analysis_time_seconds field in HistoricalScore
- Serialization (to_dict) of mode and time
- Deserialization (from_dict) of mode and time
- Backward compatibility with history files missing mode fields
- Mode display in full history report
- Mode display in comparison report
"""

import pytest
import json
import tempfile
from pathlib import Path

from writescore.history.tracker import (
    DimensionScore, HistoricalScore, ScoreHistory,
    load_score_history, save_score_history
)
from writescore.history.trends import (
    generate_full_history_report, generate_comparison_report
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_historical_score_with_mode():
    """Create a HistoricalScore with mode tracking."""
    return HistoricalScore(
        timestamp="2025-01-15T10:30:00",
        total_words=3847,
        total_sentences=156,
        total_paragraphs=42,
        notes="Test with mode tracking",
        history_version="2.0",
        analysis_mode="adaptive",
        analysis_time_seconds=45.3,
        detection_risk=35.0,
        quality_score=72.0,
        detection_interpretation="MODERATE",
        quality_interpretation="GOOD",
        tier1_score=17.5,
        tier2_score=14.6,
        tier3_score=9.6,
        tier4_score=6.0,
        dimensions={},
        raw_metrics={}
    )


@pytest.fixture
def sample_historical_score_fast_mode():
    """Create a HistoricalScore with fast mode."""
    return HistoricalScore(
        timestamp="2025-01-15T11:45:00",
        total_words=3900,
        total_sentences=160,
        total_paragraphs=44,
        notes="Fast mode analysis",
        history_version="2.0",
        analysis_mode="fast",
        analysis_time_seconds=12.8,
        detection_risk=32.0,
        quality_score=75.0,
        detection_interpretation="MODERATE",
        quality_interpretation="GOOD",
        tier1_score=18.0,
        tier2_score=15.0,
        tier3_score=10.0,
        tier4_score=6.5,
        dimensions={},
        raw_metrics={}
    )


# ============================================================================
# Core Mode Tracking Tests
# ============================================================================

def test_historical_score_has_mode_fields(sample_historical_score_with_mode):
    """Test that HistoricalScore includes mode tracking fields."""
    score = sample_historical_score_with_mode

    assert hasattr(score, 'analysis_mode')
    assert hasattr(score, 'analysis_time_seconds')
    assert score.analysis_mode == "adaptive"
    assert score.analysis_time_seconds == 45.3


def test_historical_score_mode_serialization(sample_historical_score_with_mode):
    """Test that to_dict() includes mode and time fields."""
    score = sample_historical_score_with_mode
    data = score.to_dict()

    assert 'analysis_mode' in data
    assert 'analysis_time_seconds' in data
    assert data['analysis_mode'] == "adaptive"
    assert data['analysis_time_seconds'] == 45.3


def test_historical_score_mode_deserialization():
    """Test that from_dict() correctly deserializes mode and time."""
    data = {
        'timestamp': '2025-01-15T10:30:00',
        'total_words': 3847,
        'total_sentences': 156,
        'total_paragraphs': 42,
        'notes': 'Test',
        'history_version': '2.0',
        'analysis_mode': 'full',
        'analysis_time_seconds': 120.5,
        'detection_risk': 35.0,
        'quality_score': 72.0,
        'detection_interpretation': 'MODERATE',
        'quality_interpretation': 'GOOD',
        'tier1_score': 17.5,
        'tier2_score': 14.6,
        'tier3_score': 9.6,
        'tier4_score': 6.0,
        'dimensions': {},
        'raw_metrics': {}
    }

    score = HistoricalScore.from_dict(data)

    assert score.analysis_mode == 'full'
    assert score.analysis_time_seconds == 120.5


def test_backward_compatibility_missing_mode_fields():
    """Test that old history without mode fields loads with defaults."""
    # Simulate old v2.0 history without mode fields
    data = {
        'timestamp': '2025-01-15T10:30:00',
        'total_words': 3847,
        'history_version': '2.0',
        'detection_risk': 35.0,
        'quality_score': 72.0,
        'detection_interpretation': 'MODERATE',
        'quality_interpretation': 'GOOD',
        'tier1_score': 17.5,
        'tier2_score': 14.6,
        'tier3_score': 9.6,
        'tier4_score': 6.0,
        'dimensions': {},
        'raw_metrics': {}
    }

    score = HistoricalScore.from_dict(data)

    # Should use defaults
    assert score.analysis_mode == 'adaptive'
    assert score.analysis_time_seconds == 0.0


def test_mode_roundtrip_serialization(sample_historical_score_with_mode):
    """Test full serialization roundtrip preserves mode data."""
    score = sample_historical_score_with_mode

    # Serialize
    data = score.to_dict()

    # Deserialize
    restored = HistoricalScore.from_dict(data)

    assert restored.analysis_mode == score.analysis_mode
    assert restored.analysis_time_seconds == score.analysis_time_seconds


# ============================================================================
# History File Save/Load Tests
# ============================================================================

def test_mode_saved_in_history_file(sample_historical_score_with_mode):
    """Test that mode data is saved to history JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        history_file = Path(tmpdir) / ".test.md.history.json"

        # Create and save history
        history = ScoreHistory(file_path=str(test_file))
        history.scores.append(sample_historical_score_with_mode)
        save_score_history(history)

        # Load raw JSON to verify mode fields are present
        with open(history_file, 'r') as f:
            data = json.load(f)

        assert len(data['scores']) == 1
        assert data['scores'][0]['analysis_mode'] == 'adaptive'
        assert data['scores'][0]['analysis_time_seconds'] == 45.3


def test_mode_loaded_from_history_file(sample_historical_score_with_mode):
    """Test that mode data is loaded from history JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        history_file = Path(tmpdir) / ".test.md.history.json"

        # Create and save history
        history = ScoreHistory(file_path=str(test_file))
        history.scores.append(sample_historical_score_with_mode)
        save_score_history(history)

        # Load history
        loaded_history = load_score_history(test_file)

        assert len(loaded_history.scores) == 1
        score = loaded_history.scores[0]
        assert score.analysis_mode == 'adaptive'
        assert score.analysis_time_seconds == 45.3


# ============================================================================
# Display Tests
# ============================================================================

def test_full_history_report_shows_mode(sample_historical_score_with_mode):
    """Test that full history report displays mode information."""
    history = ScoreHistory(file_path="/path/to/test.md")
    history.scores.append(sample_historical_score_with_mode)

    report = generate_full_history_report(history)

    # Should contain mode display
    assert 'Mode:' in report
    assert 'ADAPTIVE' in report
    assert 'Analysis Time:' in report
    assert '45.3s' in report


def test_comparison_report_shows_mode(
    sample_historical_score_with_mode,
    sample_historical_score_fast_mode
):
    """Test that comparison report displays mode for both iterations."""
    history = ScoreHistory(file_path="/path/to/test.md")
    history.scores.append(sample_historical_score_with_mode)
    history.scores.append(sample_historical_score_fast_mode)

    report = generate_comparison_report(history, 0, 1)

    # Should show mode for both iterations
    assert 'Mode: ADAPTIVE' in report
    assert 'Mode: FAST' in report
    assert '45.3s' in report
    assert '12.8s' in report


def test_comparison_report_backward_compatibility():
    """Test that comparison report handles old scores without mode fields."""
    # Create old-style score (no mode)
    old_score_data = {
        'timestamp': '2025-01-14T10:00:00',
        'total_words': 3500,
        'history_version': '2.0',
        'detection_risk': 40.0,
        'quality_score': 70.0,
        'detection_interpretation': 'MODERATE',
        'quality_interpretation': 'GOOD',
        'tier1_score': 16.0,
        'tier2_score': 14.0,
        'tier3_score': 9.0,
        'tier4_score': 5.5,
        'dimensions': {},
        'raw_metrics': {}
    }
    old_score = HistoricalScore.from_dict(old_score_data)

    # Create new-style score (with mode)
    new_score = HistoricalScore(
        timestamp="2025-01-15T10:30:00",
        total_words=3847,
        history_version="2.0",
        analysis_mode="adaptive",
        analysis_time_seconds=45.3,
        detection_risk=35.0,
        quality_score=72.0,
        detection_interpretation="MODERATE",
        quality_interpretation="GOOD",
        tier1_score=17.5,
        tier2_score=14.6,
        tier3_score=9.6,
        tier4_score=6.0,
        dimensions={},
        raw_metrics={}
    )

    history = ScoreHistory(file_path="/path/to/test.md")
    history.scores.append(old_score)
    history.scores.append(new_score)

    # Should not crash with mixed old/new scores
    report = generate_comparison_report(history, 0, 1)

    # Old score will show default "ADAPTIVE" value (from from_dict default)
    # This is correct - old scores without mode field get the default
    assert 'Mode: ADAPTIVE' in report
    # Time should show N/A for old score (since analysis_time_seconds defaults to 0.0)
    assert 'Time: N/A' in report


def test_different_mode_types_in_history():
    """Test that all mode types are properly tracked and displayed."""
    modes = ['fast', 'adaptive', 'sampling', 'full']
    history = ScoreHistory(file_path="/path/to/test.md")

    for i, mode in enumerate(modes):
        score = HistoricalScore(
            timestamp=f"2025-01-15T{10+i}:00:00",
            total_words=3800 + i*50,
            history_version="2.0",
            analysis_mode=mode,
            analysis_time_seconds=10.0 * (i+1),
            detection_risk=35.0,
            quality_score=72.0,
            detection_interpretation="MODERATE",
            quality_interpretation="GOOD",
            tier1_score=17.5,
            tier2_score=14.6,
            tier3_score=9.6,
            tier4_score=6.0,
            dimensions={},
            raw_metrics={}
        )
        history.scores.append(score)

    report = generate_full_history_report(history)

    # All modes should appear in uppercase
    for mode in modes:
        assert mode.upper() in report
