"""
Unit tests for CLI main module mode integration (Click refactored).

Tests configuration creation, dry-run display, and mode integration
in single file and batch analysis functions.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
from pathlib import Path

from writescore.cli.main import (
    create_analysis_config,
    show_dry_run_config,
    show_coverage_stats,
    run_single_file_analysis,
    run_batch_analysis
)
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode


class TestCreateAnalysisConfig:
    """Test configuration creation from CLI arguments."""

    def test_create_config_fast_mode(self):
        """Test creating config for FAST mode."""
        config = create_analysis_config('fast', 5, 2000, 'even')

        assert config.mode == AnalysisMode.FAST
        assert config.sampling_sections == 5
        assert config.sampling_chars_per_section == 2000
        assert config.sampling_strategy == 'even'

    def test_create_config_adaptive_mode(self):
        """Test creating config for ADAPTIVE mode."""
        config = create_analysis_config('adaptive', 7, 3000, 'weighted')

        assert config.mode == AnalysisMode.ADAPTIVE
        assert config.sampling_sections == 7
        assert config.sampling_chars_per_section == 3000
        assert config.sampling_strategy == 'weighted'

    def test_create_config_sampling_mode(self):
        """Test creating config for SAMPLING mode."""
        config = create_analysis_config('sampling', 10, 5000, 'even')

        assert config.mode == AnalysisMode.SAMPLING
        assert config.sampling_sections == 10
        assert config.sampling_chars_per_section == 5000

    def test_create_config_full_mode(self):
        """Test creating config for FULL mode."""
        config = create_analysis_config('full', 5, 2000, 'even')

        assert config.mode == AnalysisMode.FULL


class TestShowDryRunConfig:
    """Test dry-run configuration display."""

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_fast_mode_small_file(self, mock_print, mock_getsize):
        """Test dry-run display for FAST mode with small file."""
        mock_getsize.return_value = 10000  # 10k chars (5 pages)

        config = AnalysisConfig(mode=AnalysisMode.FAST)

        show_dry_run_config('test.md', config, False, False)

        # Check that print was called with expected content
        assert mock_print.called
        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'FAST' in output
        assert '5-15 seconds' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_fast_mode_large_file_warning(self, mock_print, mock_getsize):
        """Test dry-run display for FAST mode with large file shows warning."""
        mock_getsize.return_value = 50000  # 50k chars (25 pages)

        config = AnalysisConfig(mode=AnalysisMode.FAST)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Warning' in output
        assert 'only analyzes first page' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_adaptive_mode_small_doc(self, mock_print, mock_getsize):
        """Test dry-run for ADAPTIVE mode with small document."""
        mock_getsize.return_value = 4000  # < 5k chars

        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Full analysis' in output
        assert '100%' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_adaptive_mode_medium_doc(self, mock_print, mock_getsize):
        """Test dry-run for ADAPTIVE mode with medium document."""
        mock_getsize.return_value = 25000  # 5k-50k chars

        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Sample 5 sections' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_adaptive_mode_large_doc(self, mock_print, mock_getsize):
        """Test dry-run for ADAPTIVE mode with large document."""
        mock_getsize.return_value = 100000  # > 50k chars

        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Sample 10 sections' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_sampling_mode(self, mock_print, mock_getsize):
        """Test dry-run for SAMPLING mode."""
        mock_getsize.return_value = 50000

        config = AnalysisConfig(
            mode=AnalysisMode.SAMPLING,
            sampling_sections=7,
            sampling_chars_per_section=3000,
            sampling_strategy='weighted'
        )

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Sample 7 sections' in output
        assert '3000 chars' in output
        assert 'weighted' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_full_mode_small_file(self, mock_print, mock_getsize):
        """Test dry-run for FULL mode with small file."""
        mock_getsize.return_value = 50000  # 25 pages

        config = AnalysisConfig(mode=AnalysisMode.FULL)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'FULL' in output
        assert '100%' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_full_mode_large_file_warning(self, mock_print, mock_getsize):
        """Test dry-run for FULL mode with large file shows warning."""
        mock_getsize.return_value = 300000  # 150 pages

        config = AnalysisConfig(mode=AnalysisMode.FULL)

        show_dry_run_config('test.md', config, False, False)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Warning' in output
        assert 'VERY SLOW' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_dry_run_shows_additional_features(self, mock_print, mock_getsize):
        """Test dry-run shows additional enabled features."""
        mock_getsize.return_value = 10000

        config = AnalysisConfig(mode=AnalysisMode.FAST)

        show_dry_run_config('test.md', config, detailed=True, show_scores=True)

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'Detailed diagnostics enabled' in output
        assert 'Dual score analysis enabled' in output


class TestShowCoverageStats:
    """Test coverage statistics display."""

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_coverage_stats_from_metadata(self, mock_print, mock_getsize):
        """Test coverage stats when result has metadata."""
        mock_getsize.return_value = 100000

        result = MagicMock()
        result.metadata = {
            'coverage': 15.5,
            'chars_analyzed': 15500
        }

        config = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)

        show_coverage_stats(result, config, 'test.md')

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert '15500' in output or '15,500' in output
        assert '100000' in output or '100,000' in output
        assert '15.5%' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_coverage_stats_estimated_fast_mode(self, mock_print, mock_getsize):
        """Test estimated coverage for FAST mode."""
        mock_getsize.return_value = 50000

        result = MagicMock()
        result.metadata = {}

        config = AnalysisConfig(mode=AnalysisMode.FAST)

        show_coverage_stats(result, config, 'test.md')

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'FAST' in output

    @patch('os.path.getsize')
    @patch('builtins.print')
    def test_coverage_stats_full_mode(self, mock_print, mock_getsize):
        """Test coverage stats for FULL mode."""
        mock_getsize.return_value = 50000

        result = MagicMock()
        result.metadata = {}

        config = AnalysisConfig(mode=AnalysisMode.FULL)

        show_coverage_stats(result, config, 'test.md')

        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'FULL' in output
        assert '100%' in output


class TestRunSingleFileAnalysis:
    """Test single file analysis with mode configuration."""

    @patch('writescore.cli.main.show_dry_run_config')
    @patch('writescore.cli.main.AIPatternAnalyzer')
    def test_single_file_dry_run(self, mock_analyzer_class, mock_show_dry_run):
        """Test single file analysis with dry-run flag."""
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        results, dual_score = run_single_file_analysis(
            file='test.md',
            mode='fast',
            profile='balanced',
            samples=5,
            sample_size=2000,
            sample_strategy='even',
            dry_run=True,
            show_coverage=False,
            detection_target=30.0,
            quality_target=85.0,
            history_notes="",
            no_track_history=False,
            no_score_summary=False,
            format='text'
        )

        # Dry run should show config and return empty results
        assert mock_show_dry_run.called
        assert results == []
        assert dual_score is None
        mock_analyzer.analyze_file.assert_not_called()

    @patch('time.time')
    @patch('writescore.cli.main.AIPatternAnalyzer')
    @patch('builtins.print')
    def test_single_file_analysis_with_config(self, mock_print, mock_analyzer_class, mock_time):
        """Test single file analysis passes config to analyzer."""
        mock_time.side_effect = [100.0, 105.5]  # Start and end time

        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        result = MagicMock()
        result.metadata = {}
        mock_analyzer.analyze_file.return_value = result

        results, dual_score = run_single_file_analysis(
            file='test.md',
            mode='fast',
            profile='balanced',
            samples=5,
            sample_size=2000,
            sample_strategy='even',
            dry_run=False,
            show_coverage=False,
            detection_target=30.0,
            quality_target=85.0,
            history_notes="",
            no_track_history=False,
            no_score_summary=True,
            format='text'
        )

        # Check config was passed to analyzer
        assert mock_analyzer.analyze_file.called
        call_args = mock_analyzer.analyze_file.call_args
        assert call_args[1]['config'].mode == AnalysisMode.FAST
        assert len(results) == 1
        assert results[0] == result

        # Check metadata was added
        assert result.metadata['analysis_mode'] == 'fast'
        assert result.metadata['analysis_time_seconds'] == 5.5

    @patch('time.time')
    @patch('writescore.cli.main.AIPatternAnalyzer')
    @patch('writescore.cli.main.show_coverage_stats')
    @patch('builtins.print')
    def test_single_file_with_coverage(self, mock_print, mock_show_coverage, mock_analyzer_class, mock_time):
        """Test single file analysis shows coverage when requested."""
        mock_time.side_effect = [100.0, 102.0]

        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        result = MagicMock()
        result.metadata = {}
        mock_analyzer.analyze_file.return_value = result

        results, dual_score = run_single_file_analysis(
            file='test.md',
            mode='adaptive',
            profile='balanced',
            samples=5,
            sample_size=2000,
            sample_strategy='even',
            dry_run=False,
            show_coverage=True,
            detection_target=30.0,
            quality_target=85.0,
            history_notes="",
            no_track_history=False,
            no_score_summary=True,
            format='text'
        )

        # Coverage should be displayed
        assert mock_show_coverage.called


class TestRunBatchAnalysis:
    """Test batch analysis with mode configuration."""

    @patch('writescore.cli.main.AIPatternAnalyzer')
    @patch('builtins.print')
    def test_batch_analysis_dry_run(self, mock_print, mock_analyzer_class):
        """Test batch analysis with dry-run flag."""
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        results, dual_score = run_batch_analysis(
            batch_dir='test_dir/',
            mode='fast',
            profile='balanced',
            samples=5,
            sample_size=2000,
            sample_strategy='even',
            dry_run=True
        )

        # Dry run should return empty results
        assert results == []
        assert dual_score is None
        mock_analyzer.analyze_file.assert_not_called()

        # Check dry-run output
        output = ' '.join([str(call.args[0]) if call.args else str(call.kwargs.get('', '')) for call in mock_print.call_args_list])
        assert 'DRY RUN' in output
        assert 'test_dir/' in output

    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.is_dir')
    @patch('writescore.cli.main.AIPatternAnalyzer')
    @patch('builtins.print')
    def test_batch_analysis_with_config(self, mock_print, mock_analyzer_class, mock_is_dir, mock_glob):
        """Test batch analysis passes config to all files."""
        mock_is_dir.return_value = True

        # Create proper mock Path objects with sortable comparison
        file1 = MagicMock(spec=Path)
        file1.name = 'file1.md'
        file1.__str__ = lambda self: 'test_dir/file1.md'
        file1.__lt__ = lambda self, other: str(self) < str(other)

        file2 = MagicMock(spec=Path)
        file2.name = 'file2.md'
        file2.__str__ = lambda self: 'test_dir/file2.md'
        file2.__lt__ = lambda self, other: str(self) < str(other)

        mock_files = [file1, file2]
        mock_glob.return_value = mock_files

        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        result1 = MagicMock()
        result2 = MagicMock()
        mock_analyzer.analyze_file.side_effect = [result1, result2]

        results, dual_score = run_batch_analysis(
            batch_dir='test_dir/',
            mode='sampling',
            profile='balanced',
            samples=5,
            sample_size=2000,
            sample_strategy='even',
            dry_run=False
        )

        # Check config was passed to all analyze_file calls
        assert mock_analyzer.analyze_file.call_count == 2
        for call in mock_analyzer.analyze_file.call_args_list:
            assert call[1]['config'].mode == AnalysisMode.SAMPLING

        assert len(results) == 2


# Coverage: These tests cover all major functionality of CLI refactoring
# - Configuration creation from individual parameters (Click style)
# - Dry-run display for all modes
# - Coverage stats display
# - Single file analysis with config integration
# - Batch analysis with config integration
# - Timing tracking
# - Metadata population
