"""
Unit tests for CLI mode argument parsing.

Tests all mode argument parsing, validation logic, and configuration creation.
Minimum 25 tests as per AC-21.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from writescore.cli.args import parse_arguments, validate_mode_arguments, show_mode_help


class TestModeArgumentParsing:
    """Test mode argument parsing."""

    def test_default_mode_is_adaptive(self):
        """Test that default mode is 'adaptive'."""
        with patch.object(sys, 'argv', ['prog', 'test.md']):
            args = parse_arguments()
            assert args.mode == 'adaptive'

    def test_fast_mode_parsing(self):
        """Test parsing --mode fast."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'fast']):
            args = parse_arguments()
            assert args.mode == 'fast'

    def test_adaptive_mode_parsing(self):
        """Test parsing --mode adaptive."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'adaptive']):
            args = parse_arguments()
            assert args.mode == 'adaptive'

    def test_sampling_mode_parsing(self):
        """Test parsing --mode sampling."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'sampling']):
            args = parse_arguments()
            assert args.mode == 'sampling'

    def test_full_mode_parsing(self):
        """Test parsing --mode full."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'full']):
            args = parse_arguments()
            assert args.mode == 'full'

    def test_mode_short_flag(self):
        """Test parsing -m short flag."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '-m', 'fast']):
            args = parse_arguments()
            assert args.mode == 'fast'

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises error."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'invalid']):
            with pytest.raises(SystemExit):
                parse_arguments()


class TestSamplingArguments:
    """Test sampling-related arguments."""

    def test_default_samples_is_5(self):
        """Test default samples is 5."""
        with patch.object(sys, 'argv', ['prog', 'test.md']):
            args = parse_arguments()
            assert args.samples == 5

    def test_custom_samples_parsing(self):
        """Test parsing custom --samples."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--samples', '10']):
            args = parse_arguments()
            assert args.samples == 10

    def test_default_sample_size_is_2000(self):
        """Test default sample-size is 2000."""
        with patch.object(sys, 'argv', ['prog', 'test.md']):
            args = parse_arguments()
            assert args.sample_size == 2000

    def test_custom_sample_size_parsing(self):
        """Test parsing custom --sample-size."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--sample-size', '5000']):
            args = parse_arguments()
            assert args.sample_size == 5000

    def test_default_sample_strategy_is_even(self):
        """Test default sample-strategy is even."""
        with patch.object(sys, 'argv', ['prog', 'test.md']):
            args = parse_arguments()
            assert args.sample_strategy == 'even'

    def test_weighted_sample_strategy_parsing(self):
        """Test parsing --sample-strategy weighted."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--sample-strategy', 'weighted']):
            args = parse_arguments()
            assert args.sample_strategy == 'weighted'

    def test_adaptive_sample_strategy_parsing(self):
        """Test parsing --sample-strategy adaptive."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--sample-strategy', 'adaptive']):
            args = parse_arguments()
            assert args.sample_strategy == 'adaptive'

    def test_invalid_sample_strategy_raises_error(self):
        """Test that invalid sample-strategy raises error."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--sample-strategy', 'invalid']):
            with pytest.raises(SystemExit):
                parse_arguments()


class TestUtilityFlags:
    """Test utility flags."""

    def test_dry_run_flag(self):
        """Test parsing --dry-run flag."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--dry-run']):
            args = parse_arguments()
            assert args.dry_run is True

    def test_show_coverage_flag(self):
        """Test parsing --show-coverage flag."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--show-coverage']):
            args = parse_arguments()
            assert args.show_coverage is True

    def test_help_modes_exits(self):
        """Test that --help-modes exits with code 0."""
        with patch.object(sys, 'argv', ['prog', '--help-modes']):
            with patch('writescore.cli.args.show_mode_help') as mock_help:
                with pytest.raises(SystemExit) as exc:
                    parse_arguments()
                assert exc.value.code == 0
                mock_help.assert_called_once()


class TestValidationLogic:
    """Test argument validation logic."""

    def test_validate_sample_count_too_low(self):
        """Test validation fails when sample count < 1."""
        args = MagicMock()
        args.samples = 0
        args.sample_size = 2000
        args.mode = 'sampling'
        args.file = None

        with pytest.raises(ValueError, match="Invalid sample count"):
            validate_mode_arguments(args)

    def test_validate_sample_count_too_high(self):
        """Test validation fails when sample count > 20."""
        args = MagicMock()
        args.samples = 21
        args.sample_size = 2000
        args.mode = 'sampling'
        args.file = None

        with pytest.raises(ValueError, match="Invalid sample count"):
            validate_mode_arguments(args)

    def test_validate_sample_count_valid_range(self):
        """Test validation passes for valid sample count."""
        args = MagicMock()
        args.samples = 10
        args.sample_size = 2000
        args.mode = 'sampling'
        args.file = None

        # Should not raise
        validate_mode_arguments(args)

    def test_validate_sample_size_too_low(self):
        """Test validation fails when sample size < 500."""
        args = MagicMock()
        args.samples = 5
        args.sample_size = 400
        args.mode = 'sampling'
        args.file = None

        with pytest.raises(ValueError, match="Invalid sample size"):
            validate_mode_arguments(args)

    def test_validate_sample_size_too_high(self):
        """Test validation fails when sample size > 10000."""
        args = MagicMock()
        args.samples = 5
        args.sample_size = 11000
        args.mode = 'sampling'
        args.file = None

        with pytest.raises(ValueError, match="Invalid sample size"):
            validate_mode_arguments(args)

    def test_validate_sample_size_valid_range(self):
        """Test validation passes for valid sample size."""
        args = MagicMock()
        args.samples = 5
        args.sample_size = 5000
        args.mode = 'sampling'
        args.file = None

        # Should not raise
        validate_mode_arguments(args)

    @patch('sys.stderr')
    def test_warning_for_samples_with_fast_mode(self, mock_stderr):
        """Test warning when using --samples with fast mode."""
        args = MagicMock()
        args.samples = 10
        args.sample_size = 2000
        args.mode = 'fast'
        args.file = None

        with patch('builtins.print') as mock_print:
            validate_mode_arguments(args)
            # Check that warning was printed
            assert mock_print.called

    @patch('sys.stderr')
    def test_warning_for_sample_size_with_fast_mode(self, mock_stderr):
        """Test warning when using --sample-size with fast mode."""
        args = MagicMock()
        args.samples = 5
        args.sample_size = 5000
        args.mode = 'fast'
        args.file = None

        with patch('builtins.print') as mock_print:
            validate_mode_arguments(args)
            # Check that warning was printed
            assert mock_print.called

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.input')
    def test_full_mode_large_file_warning(self, mock_input, mock_getsize, mock_exists):
        """Test warning and confirmation for FULL mode with large files."""
        mock_exists.return_value = True
        mock_getsize.return_value = 600000  # 600k chars
        mock_input.return_value = 'y'

        args = MagicMock()
        args.samples = 5
        args.sample_size = 2000
        args.mode = 'full'
        args.file = 'large_file.md'
        args.quiet = False
        args.batch = False
        args.dry_run = False

        with patch('builtins.print') as mock_print:
            validate_mode_arguments(args)
            # Check that warning was printed
            assert mock_print.called
            # Check that input was called
            assert mock_input.called

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.input')
    def test_full_mode_large_file_cancel(self, mock_input, mock_getsize, mock_exists):
        """Test canceling FULL mode with large files."""
        mock_exists.return_value = True
        mock_getsize.return_value = 600000  # 600k chars
        mock_input.return_value = 'n'

        args = MagicMock()
        args.samples = 5
        args.sample_size = 2000
        args.mode = 'full'
        args.file = 'large_file.md'
        args.quiet = False
        args.batch = False
        args.dry_run = False

        with pytest.raises(SystemExit):
            validate_mode_arguments(args)


class TestModeIntegrationWithExistingFeatures:
    """Test mode arguments work with existing features."""

    def test_mode_with_batch(self):
        """Test mode works with --batch."""
        with patch.object(sys, 'argv', ['prog', '--batch', 'dir/', '--mode', 'fast']):
            args = parse_arguments()
            assert args.mode == 'fast'
            assert args.batch == 'dir/'

    def test_mode_with_detailed(self):
        """Test mode works with --detailed."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'adaptive', '--detailed']):
            args = parse_arguments()
            assert args.mode == 'adaptive'
            assert args.detailed is True

    def test_mode_with_show_scores(self):
        """Test mode works with --show-scores."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'full', '--show-scores']):
            args = parse_arguments()
            assert args.mode == 'full'
            assert args.show_scores is True

    def test_mode_with_format_json(self):
        """Test mode works with --format json."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'sampling', '--format', 'json']):
            args = parse_arguments()
            assert args.mode == 'sampling'
            assert args.format == 'json'

    def test_mode_with_history_notes(self):
        """Test mode works with --history-notes."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--mode', 'adaptive', '--history-notes', 'Test run']):
            args = parse_arguments()
            assert args.mode == 'adaptive'
            assert args.history_notes == 'Test run'

    def test_complex_combination(self):
        """Test complex combination of mode and other arguments."""
        with patch.object(sys, 'argv', [
            'prog', 'test.md', '--mode', 'sampling',
            '--samples', '7', '--sample-size', '3000',
            '--sample-strategy', 'weighted',
            '--detailed', '--show-coverage',
            '--format', 'json', '-o', 'output.json'
        ]):
            args = parse_arguments()
            assert args.mode == 'sampling'
            assert args.samples == 7
            assert args.sample_size == 3000
            assert args.sample_strategy == 'weighted'
            assert args.detailed is True
            assert args.show_coverage is True
            assert args.format == 'json'
            assert args.output == 'output.json'


class TestBackwardCompatibility:
    """Test backward compatibility - existing commands work without mode."""

    def test_basic_analysis_without_mode(self):
        """Test basic analysis without mode (should default to adaptive)."""
        with patch.object(sys, 'argv', ['prog', 'test.md']):
            args = parse_arguments()
            assert args.mode == 'adaptive'  # Default
            assert hasattr(args, 'mode')

    def test_batch_without_mode(self):
        """Test batch analysis without mode."""
        with patch.object(sys, 'argv', ['prog', '--batch', 'dir/']):
            args = parse_arguments()
            assert args.mode == 'adaptive'  # Default
            assert args.batch == 'dir/'

    def test_detailed_without_mode(self):
        """Test detailed analysis without mode."""
        with patch.object(sys, 'argv', ['prog', 'test.md', '--detailed']):
            args = parse_arguments()
            assert args.mode == 'adaptive'  # Default
            assert args.detailed is True

    def test_existing_args_preserved(self):
        """Test all existing arguments still work."""
        with patch.object(sys, 'argv', [
            'prog', 'test.md',
            '--detailed',
            '--format', 'json',
            '--domain-terms', 'Docker,Kubernetes',
            '--output', 'output.json',
            '--show-scores',
            '--detection-target', '25.0',
            '--quality-target', '90.0',
            '--history-notes', 'Test'
        ]):
            args = parse_arguments()
            assert args.detailed is True
            assert args.format == 'json'
            assert args.domain_terms == 'Docker,Kubernetes'
            assert args.output == 'output.json'
            assert args.show_scores is True
            assert args.detection_target == 25.0
            assert args.quality_target == 90.0
            assert args.history_notes == 'Test'
