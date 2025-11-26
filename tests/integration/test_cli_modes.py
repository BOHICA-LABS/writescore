"""
Integration tests for CLI analysis modes.

Tests real CLI invocation with different modes and feature combinations.
Minimum 15 tests as per AC-22.

Note: After migration to src-layout, CLI is invoked via the installed
'writescore' entry point, not the legacy analyze_ai_patterns.py script.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# CLI command - using installed entry point from src-layout
CLI_CMD = ['writescore']


@pytest.fixture
def sample_document():
    """Create a sample markdown document for testing."""
    content = """# Sample Document

This is a sample document for testing the AI pattern analyzer with different analysis modes.
It contains several paragraphs to ensure we have enough content for meaningful analysis.

## Introduction

AI-powered tools have revolutionized content creation. However, maintaining authenticity
remains crucial. This document explores various aspects of writing quality and detection risk.

## Analysis Dimensions

The analyzer examines multiple dimensions:
- Perplexity and vocabulary patterns
- Burstiness and sentence variation
- Structural elements
- Formatting characteristics

## Conclusion

Understanding these patterns helps writers create more authentic content while leveraging
the benefits of modern tools.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        return f.name


@pytest.fixture
def batch_directory():
    """Create a temporary directory with multiple markdown files."""
    tmpdir = tempfile.mkdtemp()

    for i in range(3):
        file_path = Path(tmpdir) / f"doc{i+1}.md"
        with open(file_path, 'w') as f:
            f.write(f"""# Document {i+1}

This is document number {i+1} for batch testing.
It contains some sample content to analyze.

The analyzer should process all files in the directory.
""")

    return tmpdir


class TestSingleFileModes:
    """Test single file analysis with different modes."""

    def test_fast_mode_single_file(self, sample_document):
        """Test fast mode with single file."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document, '--mode', 'fast'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        assert 'Mode: FAST' in result.stdout or 'fast' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()

    def test_adaptive_mode_single_file(self, sample_document):
        """Test adaptive mode with single file."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document, '--mode', 'adaptive'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        assert 'Mode: ADAPTIVE' in result.stdout or 'adaptive' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()

    def test_sampling_mode_single_file(self, sample_document):
        """Test sampling mode with single file."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'sampling', '--samples', '3', '--sample-size', '1000'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        assert 'Mode: SAMPLING' in result.stdout or 'sampling' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()

    def test_full_mode_single_file(self, sample_document):
        """Test full mode with single file."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document, '--mode', 'full'],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        assert 'Mode: FULL' in result.stdout or 'full' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()


class TestBatchWithModes:
    """Test batch analysis with different modes."""

    def test_batch_with_fast_mode(self, batch_directory):
        """Test batch analysis with fast mode."""
        result = subprocess.run(
            CLI_CMD + ['analyze', '--batch', batch_directory, '--mode', 'fast'],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        # Should process multiple files
        assert 'doc1.md' in result.stdout or 'doc2.md' in result.stdout

        # Cleanup
        import shutil
        shutil.rmtree(batch_directory)

    def test_batch_with_adaptive_mode_tsv(self, batch_directory):
        """Test batch analysis with adaptive mode and TSV output."""
        result = subprocess.run(
            CLI_CMD + ['analyze', '--batch', batch_directory,
             '--mode', 'adaptive', '--format', 'tsv'],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        # TSV should have headers and mode column
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 4  # Header + 3 files

        # Cleanup
        import shutil
        shutil.rmtree(batch_directory)


class TestModeWithOtherFeatures:
    """Test analysis modes combined with other CLI features."""

    def test_detailed_with_mode(self, sample_document):
        """Test --detailed flag with analysis mode."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'fast', '--detailed'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        # Detailed output should contain findings
        assert 'Findings:' in result.stdout or 'DETAILED' in result.stdout

        # Cleanup
        Path(sample_document).unlink()

    def test_dual_score_with_mode(self, sample_document):
        """Test --show-scores with analysis mode."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'adaptive', '--show-scores'],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        # Should show dual scores
        assert 'Detection Risk' in result.stdout or 'Quality Score' in result.stdout

        # Cleanup
        Path(sample_document).unlink()

    def test_json_output_with_mode(self, sample_document):
        """Test JSON output includes mode information."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'sampling', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0

        # Parse JSON
        try:
            data = json.loads(result.stdout)
            # Mode should be in output
            assert 'analysis_mode' in data or 'mode' in str(data).lower()
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

        # Cleanup
        Path(sample_document).unlink()


class TestHistoryWithModes:
    """Test history tracking with analysis modes."""

    def test_history_tracking_with_mode(self, sample_document):
        """Test that mode is saved in history."""
        # Run analysis with --save-to-history (if implemented)
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'adaptive', '--history-notes', 'Test with adaptive mode'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0

        # Check that history file was created
        history_file = Path(sample_document).parent / f".{Path(sample_document).name}.history.json"

        if history_file.exists():
            with open(history_file) as f:
                history_data = json.load(f)

            # Verify mode is in history
            if 'scores' in history_data and len(history_data['scores']) > 0:
                latest_score = history_data['scores'][-1]
                # Mode should be tracked
                assert 'analysis_mode' in latest_score

            # Cleanup
            history_file.unlink()

        # Cleanup
        Path(sample_document).unlink()


class TestUtilityFlags:
    """Test utility flags (dry-run, show-coverage)."""

    def test_dry_run_mode(self, sample_document):
        """Test --dry-run flag."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'sampling', '--samples', '5', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        # Dry-run should show configuration without analyzing
        assert 'dry' in result.stdout.lower() or 'preview' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()

    def test_show_coverage_flag(self, sample_document):
        """Test --show-coverage flag."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--mode', 'adaptive', '--show-coverage'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        # Coverage info should be displayed
        assert 'coverage' in result.stdout.lower() or 'chars' in result.stdout.lower()

        # Cleanup
        Path(sample_document).unlink()


class TestBackwardCompatibility:
    """Test backward compatibility - existing commands work without mode.

    Note: After CLI refactoring (Story 2.5 Task 5), the 'analyze' subcommand
    is required. These tests verify compatibility within the new structure.
    """

    def test_basic_analysis_no_mode_specified(self, sample_document):
        """Test that basic analysis works without specifying mode."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        # Should complete successfully with default mode
        assert len(result.stdout) > 0

        # Cleanup
        Path(sample_document).unlink()

    def test_existing_flags_work_without_mode(self, sample_document):
        """Test that existing flags work without mode specification."""
        result = subprocess.run(
            CLI_CMD + ['analyze', sample_document,
             '--detailed', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0

        # Should be valid JSON
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

        # Cleanup
        Path(sample_document).unlink()

    def test_batch_without_mode_specified(self, batch_directory):
        """Test batch analysis without mode specification."""
        result = subprocess.run(
            CLI_CMD + ['analyze', '--batch', batch_directory],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        # Should process files successfully
        assert len(result.stdout) > 0

        # Cleanup
        import shutil
        shutil.rmtree(batch_directory)


class TestHelpOutput:
    """Test help output and --help-modes."""

    def test_help_modes_display(self):
        """Test --help-modes displays mode information."""
        result = subprocess.run(
            CLI_CMD + ['analyze', '--help-modes'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        # Should display mode information
        assert 'FAST' in result.stdout or 'fast' in result.stdout.lower()
        assert 'ADAPTIVE' in result.stdout or 'adaptive' in result.stdout.lower()
        assert 'SAMPLING' in result.stdout or 'sampling' in result.stdout.lower()
        assert 'FULL' in result.stdout or 'full' in result.stdout.lower()

    def test_main_help_references_modes(self):
        """Test that analyze --help references --mode."""
        result = subprocess.run(
            CLI_CMD + ['analyze', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        # Should mention modes or --mode
        assert '--mode' in result.stdout or '--help-modes' in result.stdout
