"""
CLI main entry point using Click framework.

This module provides the command-line interface for WriteScore (AI Pattern Analyzer).
After installation, it's accessible via the `writescore` command.

Usage:
    writescore analyze FILE [OPTIONS]
    writescore recalibrate DATASET [OPTIONS]

Extension Points:
    - Refactored from argparse to Click for better UX (Story 1.4.10)
    - Converted to Click groups for multiple commands (Story 2.5 Task 5)
    - BREAKING CHANGE: Users must now use 'analyze' subcommand
"""

import contextlib
import os
import sys
from pathlib import Path

import click

# Suppress tokenizers parallelism warning when forking
# (common with pytest, multiprocessing, or CLI usage)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from writescore.__version__ import __version__  # noqa: E402
from writescore.cli.formatters import (  # noqa: E402
    format_detailed_report,
    format_report,
)
from writescore.core.analysis_config import AnalysisConfig, AnalysisMode  # noqa: E402
from writescore.core.analyzer import AIPatternAnalyzer  # noqa: E402
from writescore.core.deployment import (  # noqa: E402
    ParameterComparator,
    ParameterVersionManager,
    format_version_list,
    generate_deployment_checklist,
)
from writescore.core.interpretability import (  # noqa: E402
    ScoreInterpretation,
    ScoreInterpreter,
    format_percentile_report,
)


def parse_domain_terms(domain_terms_str: str):
    """
    Parse domain terms from comma-separated string.

    Args:
        domain_terms_str: Comma-separated domain terms

    Returns:
        List of regex patterns for domain terms
    """
    if not domain_terms_str:
        return None

    return [rf"\b{term.strip()}\b" for term in domain_terms_str.split(",")]


def generate_percentile_interpretation(result, dual_score=None):
    """
    Generate percentile-based interpretation from analysis results.

    Uses hardcoded baseline percentile ranges derived from typical
    human/AI distributions. For more accurate percentiles, use the
    recalibrate command to derive parameters from a validation dataset.

    Args:
        result: Analysis result with dimension scores
        dual_score: Optional dual score for overall percentiles

    Returns:
        Formatted percentile report string
    """
    # Baseline human distribution statistics (derived from typical ranges)
    # These are approximate - for accurate values, use recalibrated parameters
    baseline_human_stats = {
        "burstiness": {
            "percentiles": {"p10": 5.0, "p25": 8.0, "p50": 12.0, "p75": 18.0, "p90": 25.0},
            "min_val": 2.0,
            "max_val": 35.0,
        },
        "lexical": {
            "percentiles": {"p10": 0.45, "p25": 0.52, "p50": 0.60, "p75": 0.68, "p90": 0.75},
            "min_val": 0.35,
            "max_val": 0.85,
        },
        "readability": {
            "percentiles": {"p10": 8.0, "p25": 10.0, "p50": 12.0, "p75": 14.0, "p90": 16.0},
            "min_val": 5.0,
            "max_val": 20.0,
        },
        "sentiment": {
            "percentiles": {"p10": 0.02, "p25": 0.05, "p50": 0.10, "p75": 0.18, "p90": 0.30},
            "min_val": 0.0,
            "max_val": 0.50,
        },
        "voice": {
            "percentiles": {"p10": 0.15, "p25": 0.25, "p50": 0.40, "p75": 0.55, "p90": 0.70},
            "min_val": 0.05,
            "max_val": 0.85,
        },
        "transition_marker": {
            "percentiles": {"p10": 1.0, "p25": 2.0, "p50": 4.0, "p75": 6.0, "p90": 9.0},
            "min_val": 0.0,
            "max_val": 15.0,
        },
        "syntactic": {
            "percentiles": {"p10": 12.0, "p25": 15.0, "p50": 18.0, "p75": 22.0, "p90": 28.0},
            "min_val": 8.0,
            "max_val": 35.0,
        },
        "structure": {
            "percentiles": {"p10": 0.6, "p25": 0.7, "p50": 0.8, "p75": 0.88, "p90": 0.95},
            "min_val": 0.4,
            "max_val": 1.0,
        },
    }

    # Baseline AI distribution statistics (AI tends to be more uniform)
    baseline_ai_stats = {
        "burstiness": {
            "percentiles": {"p10": 3.0, "p25": 5.0, "p50": 7.0, "p75": 9.0, "p90": 12.0},
            "min_val": 1.0,
            "max_val": 18.0,
        },
        "lexical": {
            "percentiles": {"p10": 0.55, "p25": 0.58, "p50": 0.62, "p75": 0.66, "p90": 0.70},
            "min_val": 0.50,
            "max_val": 0.75,
        },
        "sentiment": {
            "percentiles": {"p10": 0.01, "p25": 0.02, "p50": 0.04, "p75": 0.06, "p90": 0.10},
            "min_val": 0.0,
            "max_val": 0.15,
        },
        "voice": {
            "percentiles": {"p10": 0.05, "p25": 0.08, "p50": 0.12, "p75": 0.18, "p90": 0.25},
            "min_val": 0.02,
            "max_val": 0.35,
        },
    }

    # Create interpreter with baseline stats
    interpreter = ScoreInterpreter(human_stats=baseline_human_stats, ai_stats=baseline_ai_stats)

    # Build interpretation
    interp = ScoreInterpretation()

    # Add overall percentiles from dual score if available
    if dual_score:
        # Quality score: higher percentile = better
        quality = dual_score.quality_score if hasattr(dual_score, "quality_score") else None
        detection = dual_score.detection_risk if hasattr(dual_score, "detection_risk") else None

        if quality is not None:
            interp.overall_quality_percentile = quality  # Score 0-100 maps roughly to percentile
        if detection is not None:
            # For detection, lower is better, so invert for "good" percentile
            interp.overall_detection_percentile = 100 - detection

    # Process each dimension from the result
    if hasattr(result, "dimension_results"):
        for dim_name, dim_result in result.dimension_results.items():
            # Get raw metric value
            raw_value = None
            if (
                hasattr(dim_result, "raw_metrics")
                and dim_result.raw_metrics
                and isinstance(dim_result.raw_metrics, dict)
            ):
                # Get first metric or specific known metric
                for key in ["variance", "ratio", "score", "value", "density"]:
                    if key in dim_result.raw_metrics:
                        raw_value = dim_result.raw_metrics[key]
                        break
                if raw_value is None and dim_result.raw_metrics:
                    raw_value = list(dim_result.raw_metrics.values())[0]

            if raw_value is not None and dim_name in baseline_human_stats:
                context = interpreter.interpret_dimension(dim_name, raw_value)
                interp.dimension_contexts[dim_name] = context

                # Generate recommendation if needed
                if context.gap_to_target and abs(context.gap_to_target) > 10:
                    rec = interpreter.generate_recommendation(dim_name, context)
                    interp.recommendations.append(rec)

    # Format and return report
    return format_percentile_report(interp)


def show_mode_help():
    """Display detailed information about analysis modes."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                        ANALYSIS MODES - QUICK REFERENCE                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ FAST MODE - Quick Preview                                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Speed:    5-15 seconds for any document size                            │
│ Coverage: ~1-5% of document (first 2000 chars per dimension)            │
│ Use When: Quick preview, interactive editing, draft checks              │
│ Note:     Inaccurate for long documents, only analyzes first page       │
│                                                                           │
│ Example:  writescore chapter.md --mode fast                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ ADAPTIVE MODE - Smart Sampling (RECOMMENDED, DEFAULT)                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Speed:    30-240 seconds for 90-page chapters                           │
│ Coverage: 10-20% of document (adapts to length)                         │
│ Use When: Book chapters, long documents, regular analysis               │
│ Behavior: <5k chars = full, 5k-50k = 5 samples, >50k = 10 samples      │
│                                                                           │
│ Example:  writescore chapter.md                                │
│           writescore chapter.md --mode adaptive                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ SAMPLING MODE - Custom Configuration                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Speed:    60-300 seconds (depends on configuration)                     │
│ Coverage: Configurable (samples × sample-size)                          │
│ Use When: Specific requirements, testing, research                      │
│ Options:  --samples N (1-20, default: 5)                                │
│           --sample-size CHARS (500-10000, default: 2000)                │
│           --sample-strategy even|weighted|adaptive (default: even)      │
│                                                                           │
│ Example:  writescore chapter.md --mode sampling \\              │
│             --samples 7 --sample-size 3000 --sample-strategy weighted   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ FULL MODE - Maximum Accuracy                                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Speed:    5-20 minutes for 90-page chapters (VERY SLOW)                 │
│ Coverage: 100% of document (analyzes every word)                        │
│ Use When: Final validation, publication-ready, research                 │
│ Warning:  Very slow for long documents, consider adaptive for most use  │
│                                                                           │
│ Example:  writescore chapter.md --mode full                    │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                         PERFORMANCE COMPARISON                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

For a 90-page chapter (~180,000 characters):

┌──────────────┬─────────────┬────────────┬─────────────────────────────┐
│ Mode         │ Time        │ Coverage   │ Best For                    │
├──────────────┼─────────────┼────────────┼─────────────────────────────┤
│ FAST         │   5-15s     │    1-5%    │ Quick drafts, previews      │
│ ADAPTIVE     │  30-240s    │   10-20%   │ Book chapters (RECOMMENDED) │
│ SAMPLING     │  60-300s    │  Custom    │ Custom requirements         │
│ FULL         │ 5-20 min    │   100%     │ Final validation            │
└──────────────┴─────────────┴────────────┴─────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                          INTEGRATION WITH FEATURES                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

Mode works with ALL existing features:

  --batch DIR          Mode applies to all files in batch
  --detailed           Detailed diagnostics with mode info
  --show-scores        Dual scoring with mode in report
  --show-history-full  History shows mode for each iteration
  --format json        Mode included in JSON output

Examples:
  # Batch analysis with adaptive mode
  writescore --batch manuscript/ --mode adaptive

  # Detailed analysis with fast mode (quick iteration)
  writescore chapter.md --mode fast --detailed

  # Dual scoring with full mode (publication check)
  writescore chapter.md --mode full --show-scores

  # Check what mode would do
  writescore chapter.md --mode adaptive --dry-run

For complete documentation: docs/analysis-modes-guide.md
    """)


def create_analysis_config(mode, samples, sample_size, sample_strategy, profile="balanced"):
    """
    Create AnalysisConfig from CLI arguments.

    Args:
        mode: Analysis mode string
        samples: Number of sampling sections
        sample_size: Characters per sample section
        sample_strategy: Sampling strategy
        profile: Dimension profile (fast/balanced/full)

    Returns:
        AnalysisConfig instance
    """
    return AnalysisConfig(
        mode=AnalysisMode(mode),
        sampling_sections=samples,
        sampling_chars_per_section=sample_size,
        sampling_strategy=sample_strategy,
        dimension_profile=profile,
    )


def show_dry_run_config(file_path: str, config: AnalysisConfig, detailed, show_scores):
    """Display configuration for dry-run mode."""
    file_size = os.path.getsize(file_path)
    pages = file_size / 2000

    print("=" * 75)
    print("ANALYSIS CONFIGURATION (DRY RUN)")
    print("=" * 75)
    print(f"File: {file_path}")
    print(f"Size: {file_size:,} characters (~{pages:.0f} pages)")
    print()
    print(f"Mode: {config.mode.value.upper()}")
    print()

    if config.mode == AnalysisMode.FAST:
        print("Behavior: Truncate to 2000 chars per dimension")
        print("Expected time: 5-15 seconds")
        print("Coverage: ~1-5% of document")
        if pages > 10:
            print()
            print("⚠  Warning: FAST mode only analyzes first page.")
            print("   For accurate results on long documents, use --mode adaptive")

    elif config.mode == AnalysisMode.ADAPTIVE:
        if file_size < 5000:
            print("Behavior: Full analysis (document < 5k chars)")
            print("Expected time: 10-30 seconds")
            print("Coverage: 100%")
        elif file_size < 50000:
            samples = 5
            print(f"Behavior: Sample {samples} sections throughout document")
            print("Expected time: 30-90 seconds")
            print(f"Coverage: ~{(samples * 2000 / file_size * 100):.1f}%")
        else:
            samples = 10
            print(f"Behavior: Sample {samples} sections throughout document")
            print("Expected time: 60-240 seconds")
            print(f"Coverage: ~{(samples * 2000 / file_size * 100):.1f}%")

    elif config.mode == AnalysisMode.SAMPLING:
        print(f"Behavior: Sample {config.sampling_sections} sections")
        print(f"          {config.sampling_chars_per_section} chars per section")
        print(f"          Strategy: {config.sampling_strategy}")
        total = config.sampling_sections * config.sampling_chars_per_section
        print(
            f"Expected time: {30 + config.sampling_sections * 10}-{60 + config.sampling_sections * 20} seconds"
        )
        print(f"Coverage: ~{(total / file_size * 100):.1f}%")

    elif config.mode == AnalysisMode.FULL:
        print("Behavior: Analyze entire document, no truncation")
        print(f"Expected time: {pages * 2:.0f}-{pages * 10:.0f} seconds")
        print("Coverage: 100%")
        if pages > 100:
            print()
            print("⚠  Warning: FULL mode on large documents is VERY SLOW")
            print("   Consider --mode adaptive for faster results (30-240s)")

    print()

    # Show integration with other features
    if detailed:
        print("Additional: Detailed diagnostics enabled")
    if show_scores:
        print("Additional: Dual score analysis enabled")

    print()
    print("To run analysis: Remove --dry-run flag")
    print("=" * 75)


def show_coverage_stats(result, config: AnalysisConfig, file_path: str):
    """Display coverage statistics after analysis."""
    file_size = os.path.getsize(file_path)

    print()
    print("=" * 75)
    print("COVERAGE STATISTICS")
    print("=" * 75)

    # Calculate actual coverage from metadata if available
    if hasattr(result, "metadata") and "coverage" in result.metadata:
        actual_coverage = result.metadata["coverage"]
        chars_analyzed = result.metadata.get("chars_analyzed", 0)
        print(f"Characters analyzed: {chars_analyzed:,} of {file_size:,} ({actual_coverage:.1f}%)")
    else:
        # Estimate based on mode
        if config.mode == AnalysisMode.FAST:
            est_coverage = min(2000 * 12 / file_size * 100, 100)  # 12 dimensions × 2000 chars
            print(f"Mode: FAST (estimated ~{est_coverage:.1f}% coverage)")
        elif config.mode == AnalysisMode.FULL:
            print("Mode: FULL (100% coverage)")
        elif config.mode in [AnalysisMode.SAMPLING, AnalysisMode.ADAPTIVE]:
            total = config.sampling_sections * config.sampling_chars_per_section
            est_coverage = min(total / file_size * 100, 100)
            print(f"Mode: {config.mode.value.upper()}")
            print(f"Sections sampled: {config.sampling_sections}")
            print(f"Characters per section: {config.sampling_chars_per_section:,}")
            print(f"Estimated coverage: ~{est_coverage:.1f}%")

    print("=" * 75)
    print()


def handle_history_commands(
    file,
    show_history_full,
    compare_history,
    show_dimension_trends,
    show_raw_metric_trends,
    export_history,
):
    """
    Handle history viewing commands (--show-history-full, --compare-history, etc.).

    Args:
        file: File path
        show_history_full: Show full history flag
        compare_history: Compare iterations string
        show_dimension_trends: Show dimension trends flag
        show_raw_metric_trends: Show raw metric trends flag
        export_history: Export format (csv or json)

    Returns:
        Exit code (0 for success)
    """
    from writescore.history.trends import (
        generate_comparison_report,
        generate_dimension_trend_report,
        generate_full_history_report,
        generate_raw_metric_trends,
    )

    analyzer = AIPatternAnalyzer()
    history = analyzer.load_score_history(file)

    if len(history.scores) == 0:
        print(f"No history found for {file}", file=sys.stderr)
        print("Run analysis with --show-scores first to create history.", file=sys.stderr)
        return 1

    # Generate and print requested report
    if show_history_full:
        print(generate_full_history_report(history))

    elif compare_history:
        # Parse iteration specifiers (e.g., "first,last" or "1,5")
        parts = compare_history.split(",")
        if len(parts) != 2:
            print(
                "Error: --compare-history requires two iterations separated by comma",
                file=sys.stderr,
            )
            return 1

        # Convert to indices
        def parse_iteration(spec: str, history_len: int) -> int:
            spec = spec.strip().lower()
            if spec == "first":
                return 0
            elif spec == "last":
                return history_len - 1
            else:
                try:
                    idx = int(spec)
                    if idx < 0 or idx >= history_len:
                        raise ValueError(f"Iteration {idx} out of range (0-{history_len-1})")
                    return idx
                except ValueError as e:
                    raise ValueError(f"Invalid iteration specifier: {spec}") from e

        try:
            idx1 = parse_iteration(parts[0], len(history.scores))
            idx2 = parse_iteration(parts[1], len(history.scores))
            print(generate_comparison_report(history, idx1, idx2))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif show_dimension_trends:
        print(generate_dimension_trend_report(history))

    elif show_raw_metric_trends:
        print(generate_raw_metric_trends(history))

    elif export_history:
        if export_history == "csv":
            output_file = file.replace(".md", "-history.csv")
            history.export_to_csv(output_file)
            print(f"History exported to: {output_file}")
        elif export_history == "json":
            output_file = file.replace(".md", "-history.json")
            import json

            with open(output_file, "w") as f:
                json.dump(history.to_dict(), f, indent=2)
            print(f"History exported to: {output_file}")

    return 0


def run_single_file_analysis(
    file,
    mode,
    samples,
    sample_size,
    sample_strategy,
    profile,
    dry_run,
    show_coverage,
    detection_target,
    quality_target,
    history_notes,
    no_track_history,
    no_score_summary,
    format,
):
    """
    Run analysis on a single file.

    Args:
        file: File path
        mode: Analysis mode
        samples: Number of samples
        sample_size: Sample size in characters
        sample_strategy: Sampling strategy
        dry_run: Dry run flag
        show_coverage: Show coverage flag
        detection_target: Detection target score
        quality_target: Quality target score
        history_notes: Notes for this iteration
        no_track_history: Disable history tracking flag
        no_score_summary: Suppress score summary flag
        format: Output format

    Returns:
        List of results and calculated dual score
    """
    import time

    try:
        # Create config
        config = create_analysis_config(mode, samples, sample_size, sample_strategy, profile)

        # Parse domain terms if needed (handled in main function)
        analyzer = AIPatternAnalyzer(config=config)

        # Dry run
        if dry_run:
            show_dry_run_config(file, config, False, False)
            return [], None

        # Display mode info (only for text format, to avoid breaking JSON/TSV output)
        if format == "text":
            print(f"\nAnalyzing: {file}")
            print(f"Mode: {config.mode.value.upper()}", end="")

            if config.mode in [AnalysisMode.SAMPLING, AnalysisMode.ADAPTIVE]:
                print(
                    f" (sampling: {config.sampling_sections} × {config.sampling_chars_per_section} chars, {config.sampling_strategy})"
                )
            else:
                print()

            if show_coverage:
                print("Coverage statistics will be shown after analysis")
            print()

        # Run analysis with timing
        start_time = time.time()
        result = analyzer.analyze_file(file, config=config)
        elapsed = time.time() - start_time

        # Add mode info to results metadata (for history tracking)
        if not hasattr(result, "metadata"):
            result.metadata = {}
        result.metadata["analysis_mode"] = config.mode.value
        result.metadata["analysis_time_seconds"] = elapsed

        # Calculate dual score for history and optimization (if score summary shown)
        calculated_dual_score = None
        if not no_score_summary and format == "text":
            try:
                calculated_dual_score = analyzer.calculate_dual_score(
                    result, detection_target=detection_target, quality_target=quality_target
                )

                # Save to history (unless disabled)
                if not no_track_history:
                    history = analyzer.load_score_history(file)
                    history.add_score(calculated_dual_score, notes=history_notes)
                    analyzer.save_score_history(history)

            except Exception as e:
                # Don't fail if history tracking fails
                print(f"Warning: Could not calculate/save score history: {e}", file=sys.stderr)

        # Show coverage if requested
        if show_coverage:
            show_coverage_stats(result, config, file)

        # Display elapsed time (only for text format, to avoid breaking JSON/TSV output)
        if format == "text":
            print(f"\nCompleted in {elapsed:.1f} seconds")

        return [result], calculated_dual_score

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_batch_analysis(batch_dir, mode, samples, sample_size, sample_strategy, profile, dry_run):
    """
    Run batch analysis on directory.

    Args:
        batch_dir: Directory path
        mode: Analysis mode
        samples: Number of samples
        sample_size: Sample size in characters
        sample_strategy: Sampling strategy
        dry_run: Dry run flag

    Returns:
        List of results and None for dual_score
    """
    # Create config once (applies to all files)
    config = create_analysis_config(mode, samples, sample_size, sample_strategy, profile)

    # Parse domain terms if needed (handled in main function)
    analyzer = AIPatternAnalyzer(config=config)

    # Dry run for batch
    if dry_run:
        print("\nBatch Analysis Configuration (DRY RUN)")
        print(f"Directory: {batch_dir}")
        print(f"Mode: {config.mode.value.upper()}")
        if config.mode in [AnalysisMode.SAMPLING, AnalysisMode.ADAPTIVE]:
            print(
                f"Sampling: {config.sampling_sections} × {config.sampling_chars_per_section} chars ({config.sampling_strategy})"
            )
        print("\nMode will be applied to all .md files in directory")
        return [], None

    batch_path = Path(batch_dir)
    if not batch_path.is_dir():
        print(f"Error: {batch_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(batch_path.glob("**/*.md"))
    if not md_files:
        print(f"Error: No .md files found in {batch_dir}", file=sys.stderr)
        sys.exit(1)

    # Display batch mode info
    print(f"\nBatch Analysis Mode: {config.mode.value.upper()}")
    if config.mode in [AnalysisMode.SAMPLING, AnalysisMode.ADAPTIVE]:
        print(f"Sampling: {config.sampling_sections} × {config.sampling_chars_per_section} chars")
    print(f"Files to analyze: {len(md_files)}")
    print()

    results = []
    for md_file in md_files:
        try:
            print(f"Analyzing: {md_file.name}...", end=" ", flush=True)

            result = analyzer.analyze_file(str(md_file), config=config)
            results.append(result)

            print("✓")
        except Exception as e:
            print(f"Error analyzing {md_file}: {e}", file=sys.stderr)

    print(f"\nCompleted {len(results)} of {len(md_files)} files")

    return results, None


# Click group for multiple commands
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="writescore")
def cli():
    """WriteScore - AI Pattern Analysis and Parameter Calibration.

    Use 'analyze' to check documents for AI patterns.
    Use 'recalibrate' to derive scoring parameters from validation data.
    """
    pass


# Analyze command (main analysis functionality)
@cli.command(name="analyze")
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option(
    "--batch",
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Analyze all .md files in directory",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Provide detailed line-by-line diagnostics with context and suggestions (for LLM cleanup)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json", "tsv"]),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--domain-terms",
    metavar="TERMS",
    help="Comma-separated domain-specific terms to detect (overrides defaults)",
)
@click.option(
    "--output",
    "-o",
    metavar="FILE",
    type=click.File("w"),
    help="Write output to file instead of stdout",
)
@click.option(
    "--show-scores",
    is_flag=True,
    help="Calculate and display dual scores (Detection Risk + Quality Score) with optimization path",
)
@click.option(
    "--detection-target",
    type=float,
    default=30.0,
    metavar="N",
    help="Target detection risk score (0-100, lower=better, default: 30.0)",
)
@click.option(
    "--quality-target",
    type=float,
    default=85.0,
    metavar="N",
    help="Target quality score (0-100, higher=better, default: 85.0)",
)
@click.option(
    "--show-history", is_flag=True, help="Show aggregate score trends (quality/detection)"
)
@click.option(
    "--show-history-full",
    is_flag=True,
    help="Show complete optimization journey with all iterations",
)
@click.option(
    "--show-dimension-trends",
    is_flag=True,
    help="Show trends for all dimensions (v2.0 data required)",
)
@click.option(
    "--show-raw-metric-trends",
    is_flag=True,
    help="Show raw metric trends with sparklines (v2.0 data required)",
)
@click.option(
    "--compare-history",
    type=str,
    metavar="I1,I2",
    help='Compare two iterations (e.g., "first,last" or "1,5")',
)
@click.option(
    "--export-history",
    type=click.Choice(["csv", "json"]),
    metavar="FORMAT",
    help="Export history to CSV or JSON format",
)
@click.option(
    "--history-notes",
    type=str,
    default="",
    metavar="NOTES",
    help='Add notes for this iteration (e.g., "Fixed AI vocabulary")',
)
@click.option("--no-score-summary", is_flag=True, help="Suppress score summary display in output")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["fast", "adaptive", "sampling", "full"]),
    default="adaptive",
    help="Analysis mode: fast (5-15s), adaptive (30-240s, RECOMMENDED), sampling (60-300s), full (5-20min)",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(["fast", "balanced", "full"]),
    default="balanced",
    help="Dimension profile: fast (4 dims, ~100ms), balanced (8 dims, ~200ms, DEFAULT), full (12 dims, ~4-6s)",
)
@click.option(
    "--samples",
    type=click.IntRange(1, 20),
    default=5,
    metavar="N",
    help="Number of sections to sample (default: 5, range: 1-20)",
)
@click.option(
    "--sample-size",
    type=click.IntRange(500, 10000),
    default=2000,
    metavar="CHARS",
    help="Characters per sample section (default: 2000, range: 500-10000)",
)
@click.option(
    "--sample-strategy",
    type=click.Choice(["even", "weighted", "adaptive"]),
    default="even",
    help="Sampling distribution: even, weighted (40%% begin/40%% end), adaptive",
)
@click.option("--dry-run", is_flag=True, help="Show configuration without running analysis")
@click.option(
    "--show-coverage",
    is_flag=True,
    help="Display coverage statistics (samples, chars analyzed, coverage %%)",
)
@click.option(
    "--show-percentiles",
    is_flag=True,
    help="Show percentile-based interpretation (where scores fall in human/AI distributions)",
)
@click.option(
    "--help-modes",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: (show_mode_help(), ctx.exit()) if value else None,
    help="Show detailed information about analysis modes and exit",
)
@click.option(
    "--no-track-history", is_flag=True, hidden=True, help="Disable history tracking (internal use)"
)
def analyze_command(
    file,
    batch,
    detailed,
    format,
    domain_terms,
    output,
    show_scores,
    detection_target,
    quality_target,
    show_history,
    show_history_full,
    show_dimension_trends,
    show_raw_metric_trends,
    compare_history,
    export_history,
    history_notes,
    no_score_summary,
    mode,
    profile,
    samples,
    sample_size,
    sample_strategy,
    dry_run,
    show_coverage,
    show_percentiles,
    no_track_history,
):
    """Analyze manuscripts for AI-generated content patterns.

    Examples:

      # Analyze single file (default: adaptive mode)
      writescore chapter-01.md

      # Quick preview with fast mode (5-15 seconds)
      writescore chapter-01.md --mode fast

      # Full accuracy analysis (5-20 minutes for large files)
      writescore chapter-01.md --mode full

      # Custom sampling configuration
      writescore chapter-01.md --mode sampling --samples 10 --sample-size 3000

      # Detailed analysis with line numbers and suggestions
      writescore chapter-01.md --detailed

      # Dual score analysis with optimization path
      writescore chapter-01.md --show-scores

      # Batch analyze directory
      writescore --batch manuscript/sections --format tsv

    For detailed mode information: writescore --help-modes
    """
    # Validate inputs
    if not file and not batch:
        raise click.UsageError("Either FILE or --batch DIR must be specified")

    # Handle history viewing commands (don't run analysis)
    if any(
        [
            show_history_full,
            compare_history,
            show_dimension_trends,
            show_raw_metric_trends,
            export_history,
        ]
    ):
        if not file:
            raise click.UsageError("History viewing commands require a FILE argument")
        sys.exit(
            handle_history_commands(
                file,
                show_history_full,
                compare_history,
                show_dimension_trends,
                show_raw_metric_trends,
                export_history,
            )
        )

    # Detailed mode limitations
    if detailed and batch:
        click.echo(
            "Warning: --detailed mode not supported for batch analysis. Using standard mode.",
            err=True,
        )
        detailed = False

    if detailed and format == "tsv":
        click.echo(
            "Warning: --detailed mode not compatible with TSV format. Using JSON format.", err=True
        )
        format = "json"

    # Show scores validation
    if show_scores and batch:
        click.echo(
            "Warning: --show-scores mode not supported for batch analysis. Using standard mode.",
            err=True,
        )
        show_scores = False

    # Validate mode arguments
    if mode == "fast" and (samples != 5 or sample_size != 2000):
        click.echo("Warning: --samples and --sample-size are ignored in 'fast' mode", err=True)

    # Warning: FULL mode with large files
    if mode == "full" and file and os.path.exists(file):
        file_size = os.path.getsize(file)
        if file_size > 500000:  # >500k chars (~250 pages)
            pages = file_size / 2000
            click.echo(
                f"\n⚠ Warning: FULL mode with {pages:.0f}-page document may take 20+ minutes.",
                err=True,
            )
            click.echo(
                "           Consider using --mode adaptive for faster results (30-240s).\n",
                err=True,
            )

            # Interactive confirmation (skip if in batch or dry-run)
            if not batch and not dry_run:
                try:
                    if not click.confirm("Continue with FULL mode?"):
                        click.echo("Canceled. Use --mode adaptive for faster analysis.", err=True)
                        sys.exit(0)
                except (EOFError, KeyboardInterrupt):
                    click.echo("\nCanceled.", err=True)
                    sys.exit(0)

    # Parse domain terms
    domain_patterns = parse_domain_terms(domain_terms) if domain_terms else None

    # Create config for analyzer (used by all modes)
    config = create_analysis_config(mode, samples, sample_size, sample_strategy, profile)

    # Initialize analyzer
    analyzer = AIPatternAnalyzer(domain_terms=domain_patterns, config=config)

    # Detailed analysis mode
    if detailed:
        try:
            detailed_result = analyzer.analyze_file_detailed(file)
            output_text = format_detailed_report(detailed_result, format)

            if output:
                output.write(output_text)
                click.echo(f"Detailed analysis written to {output.name}", err=True)
            else:
                click.echo(output_text)
            sys.exit(0)

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    # Standard analysis mode
    if batch:
        results, calculated_dual_score = run_batch_analysis(
            batch, mode, samples, sample_size, sample_strategy, profile, dry_run
        )
    else:
        results, calculated_dual_score = run_single_file_analysis(
            file,
            mode,
            samples,
            sample_size,
            sample_strategy,
            profile,
            dry_run,
            show_coverage,
            detection_target,
            quality_target,
            history_notes,
            no_track_history,
            no_score_summary,
            format,
        )

    # Format and output
    output_lines = []

    if format == "tsv" and len(results) > 1:
        # TSV batch output with header
        output_lines.append(format_report(results[0], "tsv").split("\n")[0])  # Header
        for r in results:
            output_lines.append(format_report(r, "tsv").split("\n")[1])  # Data row
    else:
        # Individual reports
        for r in results:
            dual_score_param = calculated_dual_score if (len(results) == 1 and not batch) else None

            output_lines.append(
                format_report(
                    r,
                    format,
                    include_score_summary=not no_score_summary,
                    detection_target=detection_target,
                    quality_target=quality_target,
                    dual_score=dual_score_param,
                    mode=mode,
                )
            )

    output_text = "\n".join(output_lines)

    # Add percentile interpretation if requested (single file only, text format)
    if show_percentiles and len(results) == 1 and format == "text" and not batch:
        try:
            percentile_report = generate_percentile_interpretation(
                results[0], dual_score=calculated_dual_score
            )
            output_text += "\n\n" + percentile_report
        except Exception as e:
            click.echo(f"Warning: Could not generate percentile report: {e}", err=True)

    # Write output
    if output:
        output.write(output_text)
        click.echo(f"Analysis written to {output.name}", err=True)
    else:
        click.echo(output_text)


# Recalibrate command (parameter derivation from validation data)
@cli.command(name="recalibrate")
@click.argument("dataset", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="config/scoring_parameters.json",
    help="Output path for derived parameters (default: config/scoring_parameters.json)",
)
@click.option(
    "-e",
    "--existing",
    type=click.Path(exists=True),
    help="Path to existing parameters for comparison",
)
@click.option(
    "-r", "--report", type=click.Path(), help="Path to save detailed recalibration report (JSON)"
)
@click.option("--text-report", type=click.Path(), help="Path to save human-readable text report")
@click.option(
    "-d", "--dimensions", multiple=True, help="Specific dimensions to recalibrate (default: all)"
)
@click.option("--no-backup", is_flag=True, help="Do not create backup of existing parameters")
@click.option(
    "--dry-run", is_flag=True, help="Run analysis without saving parameters (preview only)"
)
@click.option(
    "--auto-select-method",
    is_flag=True,
    help="Use Shapiro-Wilk normality testing to auto-select scoring method for each dimension",
)
@click.option(
    "--normality-report",
    type=click.Path(),
    help="Path to save normality test report (only with --auto-select-method)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def recalibrate_command(
    dataset,
    output,
    existing,
    report,
    text_report,
    dimensions,
    no_backup,
    dry_run,
    auto_select_method,
    normality_report,
    verbose,
):
    """Recalibrate scoring parameters from validation dataset.

    Derives optimal scoring parameters by analyzing distribution statistics
    from a validation dataset. Parameters are anchored to empirical percentiles
    from human and AI-written samples.

    Examples:

      # Basic recalibration
      writescore recalibrate validation_data/v2.0.jsonl

      # With existing parameters for comparison
      writescore recalibrate validation_data/v2.0.jsonl \\
        --existing config/parameters.json

      # Specify output location
      writescore recalibrate validation_data/v2.0.jsonl \\
        --output config/parameters_v2.json

      # Dry-run mode (no changes)
      writescore recalibrate validation_data/v2.0.jsonl --dry-run

      # Recalibrate specific dimensions
      writescore recalibrate validation_data/v2.0.jsonl \\
        --dimensions burstiness --dimensions lexical

      # Save detailed report
      writescore recalibrate validation_data/v2.0.jsonl \\
        --report reports/recalibration_2025-11-24.json

      # Auto-select scoring method using Shapiro-Wilk normality testing
      writescore recalibrate validation_data/v2.0.jsonl \\
        --auto-select-method --normality-report reports/normality.txt
    """
    import logging

    from writescore.core.recalibration import RecalibrationWorkflow

    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(levelname)s - %(name)s - %(message)s", stream=sys.stdout
    )
    logging.getLogger(__name__)

    try:
        # Convert paths
        dataset_path = Path(dataset)
        output_path = Path(output)
        existing_path = Path(existing) if existing else None
        report_path = Path(report) if report else None
        text_report_path = Path(text_report) if text_report else None

        # Convert dimensions tuple to list
        dimension_list = list(dimensions) if dimensions else None
        normality_report_path = Path(normality_report) if normality_report else None

        # Create workflow with auto_select_method flag
        workflow = RecalibrationWorkflow(auto_select_method=auto_select_method)

        click.echo("=" * 80)
        click.echo("PARAMETER RECALIBRATION")
        click.echo("=" * 80)
        click.echo(f"Dataset: {dataset_path}")
        click.echo(f"Output: {output_path}")

        if existing_path:
            click.echo(f"Comparing with: {existing_path}")

        if dimension_list:
            click.echo(f"Dimensions: {', '.join(dimension_list)}")
        else:
            click.echo("Dimensions: all")

        if auto_select_method:
            click.echo("Method Selection: AUTO (Shapiro-Wilk normality testing)")
        else:
            click.echo("Method Selection: FIXED (hardcoded defaults)")

        if dry_run:
            click.echo("Mode: DRY-RUN (no changes will be saved)")

        click.echo()

        # Run recalibration workflow
        derived_params, recal_report = workflow.run_full_workflow(
            dataset_path=dataset_path,
            output_params_path=output_path,
            existing_params_path=existing_path,
            dimension_names=dimension_list,
            backup=not no_backup,
        )

        # Print summary to console
        click.echo()
        click.echo("=" * 80)
        click.echo("RECALIBRATION SUMMARY")
        click.echo("=" * 80)

        summary = recal_report.get_summary()
        click.echo(f"Dataset Version: {summary['dataset_version']}")
        click.echo(f"Total Documents: {summary['total_documents']}")
        click.echo(f"Dimensions Analyzed: {summary['dimensions_analyzed']}")
        click.echo(f"  - New: {summary['new_dimensions']}")
        click.echo(f"  - Modified: {summary['modified_dimensions']}")

        # Print parameter changes
        click.echo()
        click.echo("Parameter Changes:")
        for change in recal_report.parameter_changes:
            if change.is_new_dimension():
                click.echo(f"  [NEW] {change.dimension_name}")
            else:
                change_summary = change.get_change_summary()
                if change_summary.get("changes"):
                    click.echo(f"  [MODIFIED] {change.dimension_name}")
                else:
                    click.echo(f"  [NO CHANGE] {change.dimension_name}")

        # Save reports if requested
        if report_path:
            recal_report.save(report_path)
            click.echo(f"\nDetailed report saved to: {report_path}")

        if text_report_path:
            text = recal_report.format_text_report()
            text_report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(text_report_path, "w") as f:
                f.write(text)
            click.echo(f"Text report saved to: {text_report_path}")

        # Save normality report if requested and auto-select was used
        if normality_report_path and auto_select_method:
            norm_report = workflow.get_normality_report()
            if norm_report:
                normality_report_path.parent.mkdir(parents=True, exist_ok=True)
                with open(normality_report_path, "w") as f:
                    f.write(norm_report)
                click.echo(f"Normality report saved to: {normality_report_path}")
        elif normality_report_path and not auto_select_method:
            click.echo("Warning: --normality-report requires --auto-select-method", err=True)

        # Dry-run handling
        if dry_run:
            click.echo()
            click.echo("=" * 80)
            click.echo("DRY-RUN MODE: No parameters were saved")
            click.echo("Remove --dry-run flag to save parameters")
            click.echo("=" * 80)
            # Remove the saved file since this was dry-run
            if output_path.exists():
                output_path.unlink()
            sys.exit(0)

        click.echo()
        click.echo("=" * 80)
        click.echo("RECALIBRATION COMPLETE")
        click.echo("=" * 80)
        click.echo(f"Parameters saved to: {output_path}")

    except KeyboardInterrupt:
        click.echo("\n\nRecalibration interrupted by user", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"Recalibration failed: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


# Versions command (list parameter versions)
@cli.command(name="versions")
@click.option(
    "--params-dir",
    type=click.Path(),
    default="config/parameters",
    help="Directory containing parameter files (default: config/parameters)",
)
@click.option(
    "--archive-dir",
    type=click.Path(),
    default="config/parameters/archive",
    help="Directory for archived versions (default: config/parameters/archive)",
)
@click.option(
    "--active-file",
    type=click.Path(),
    default="config/scoring_parameters.yaml",
    help="Path to active parameter file (default: config/scoring_parameters.yaml)",
)
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def versions_command(params_dir, archive_dir, active_file, output_json):
    """List available parameter versions.

    Shows all parameter versions available in the params directory and archive,
    including the currently active version.

    Examples:

      # List all versions
      writescore versions

      # Custom directories
      writescore versions --params-dir /path/to/params

      # JSON output for scripting
      writescore versions --json
    """
    import json

    manager = ParameterVersionManager(
        params_dir=Path(params_dir), archive_dir=Path(archive_dir), active_file=Path(active_file)
    )

    versions = manager.list_versions()
    current = manager.get_current_version()

    if output_json:
        click.echo(json.dumps({"current_version": current, "versions": versions}, indent=2))
    else:
        click.echo(format_version_list(versions, current))


# Rollback command (restore previous version)
@cli.command(name="rollback")
@click.option("--version", "-v", "target_version", required=True, help="Version to rollback to")
@click.option(
    "--params-dir",
    type=click.Path(),
    default="config/parameters",
    help="Directory containing parameter files",
)
@click.option(
    "--archive-dir",
    type=click.Path(),
    default="config/parameters/archive",
    help="Directory for archived versions",
)
@click.option(
    "--active-file",
    type=click.Path(),
    default="config/scoring_parameters.yaml",
    help="Path to active parameter file",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be rolled back without making changes"
)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
def rollback_command(target_version, params_dir, archive_dir, active_file, dry_run, yes):
    """Rollback to a previous parameter version.

    Restores the active parameter file to a previous version. The current
    version is automatically backed up to the archive before rollback.

    Examples:

      # Rollback to specific version
      writescore rollback --version 1.0

      # Dry-run to see what would happen
      writescore rollback --version 1.0 --dry-run

      # Skip confirmation
      writescore rollback --version 1.0 --yes
    """
    manager = ParameterVersionManager(
        params_dir=Path(params_dir), archive_dir=Path(archive_dir), active_file=Path(active_file)
    )

    # Get current version for display
    current = manager.get_current_version()

    # Check if target version exists
    target_path = manager.get_version_path(target_version)
    if target_path is None:
        available = [v["version"] for v in manager.list_versions()]
        click.echo(f"Error: Version '{target_version}' not found.", err=True)
        click.echo(f"Available versions: {', '.join(available)}", err=True)
        sys.exit(1)

    # Display rollback info
    click.echo("=" * 60)
    click.echo("PARAMETER ROLLBACK")
    click.echo("=" * 60)
    click.echo(f"Current version: {current or 'none'}")
    click.echo(f"Target version:  {target_version}")
    click.echo(f"Source file:     {target_path}")
    click.echo()

    if dry_run:
        click.echo("DRY-RUN MODE: No changes will be made")
        click.echo()
        click.echo("Actions that would be performed:")
        click.echo(f"  1. Backup current parameters to {archive_dir}/")
        click.echo(f"  2. Copy {target_path} to {active_file}")
        click.echo()
        click.echo("Remove --dry-run flag to execute rollback")
        sys.exit(0)

    # Confirm unless --yes
    if not yes and not click.confirm(f"Roll back from {current or 'none'} to {target_version}?"):
        click.echo("Rollback cancelled.", err=True)
        sys.exit(0)

    # Execute rollback
    try:
        manager.rollback(target_version)
        click.echo()
        click.echo("=" * 60)
        click.echo("ROLLBACK COMPLETE")
        click.echo("=" * 60)
        click.echo(f"Active parameters: {target_version}")
        click.echo(f"Previous version backed up to: {archive_dir}/")
    except Exception as e:
        click.echo(f"Rollback failed: {e}", err=True)
        sys.exit(1)


# Diff command (compare parameter versions)
@cli.command(name="diff")
@click.argument("old_version")
@click.argument("new_version")
@click.option(
    "--params-dir",
    type=click.Path(),
    default="config/parameters",
    help="Directory containing parameter files",
)
@click.option(
    "--archive-dir",
    type=click.Path(),
    default="config/parameters/archive",
    help="Directory for archived versions",
)
@click.option("--detailed", is_flag=True, help="Show detailed per-field changes")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def diff_command(old_version, new_version, params_dir, archive_dir, detailed, output_json):
    """Compare two parameter versions.

    Shows differences between two parameter versions including added,
    removed, and modified dimensions with their specific parameter changes.

    Examples:

      # Compare two versions
      writescore diff 1.0 2.0

      # Detailed comparison
      writescore diff 1.0 2.0 --detailed

      # JSON output
      writescore diff 1.0 2.0 --json
    """
    import json

    manager = ParameterVersionManager(params_dir=Path(params_dir), archive_dir=Path(archive_dir))

    comparator = ParameterComparator()

    try:
        diff = comparator.compare_versions(old_version, new_version, manager)

        if output_json:
            click.echo(json.dumps(diff.to_dict(), indent=2))
        else:
            if detailed:
                click.echo(diff.format_detailed())
            else:
                click.echo(diff.format_summary())

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Deploy command (deploy new parameters)
@cli.command(name="deploy")
@click.argument("params_file", type=click.Path(exists=True))
@click.option(
    "--params-dir",
    type=click.Path(),
    default="config/parameters",
    help="Directory for versioned parameter files",
)
@click.option(
    "--archive-dir",
    type=click.Path(),
    default="config/parameters/archive",
    help="Directory for archived versions",
)
@click.option(
    "--active-file",
    type=click.Path(),
    default="config/scoring_parameters.yaml",
    help="Path to active parameter file",
)
@click.option(
    "--no-backup", is_flag=True, help="Do not backup current parameters before deployment"
)
@click.option("--dry-run", is_flag=True, help="Show deployment checklist without deploying")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
def deploy_command(params_file, params_dir, archive_dir, active_file, no_backup, dry_run, yes):
    """Deploy new parameters as the active version.

    Deploys a parameter file as the active scoring parameters. The current
    parameters are automatically backed up unless --no-backup is specified.

    Examples:

      # Deploy new parameters
      writescore deploy config/parameters_v2.yaml

      # Dry-run to see deployment checklist
      writescore deploy config/parameters_v2.yaml --dry-run

      # Skip confirmation
      writescore deploy config/parameters_v2.yaml --yes

      # Deploy without backup
      writescore deploy config/parameters_v2.yaml --no-backup
    """
    from writescore.core.parameter_loader import ParameterLoader

    manager = ParameterVersionManager(
        params_dir=Path(params_dir), archive_dir=Path(archive_dir), active_file=Path(active_file)
    )

    # Load new parameters
    try:
        new_params = ParameterLoader.load(Path(params_file))
    except Exception as e:
        click.echo(f"Error loading parameters: {e}", err=True)
        sys.exit(1)

    # Load current parameters for comparison
    current_params = None
    current_version = manager.get_current_version()
    if current_version:
        with contextlib.suppress(Exception):
            current_params = ParameterLoader.load(Path(active_file))

    # Dry-run: show checklist
    if dry_run:
        click.echo(generate_deployment_checklist(new_params, current_params))
        sys.exit(0)

    # Display deployment info
    click.echo("=" * 60)
    click.echo("PARAMETER DEPLOYMENT")
    click.echo("=" * 60)
    click.echo(f"Source file:     {params_file}")
    click.echo(f"New version:     {new_params.version}")
    click.echo(f"Current version: {current_version or 'none'}")
    click.echo(f"Dimensions:      {len(new_params.dimensions)}")
    click.echo()

    # Show changes if upgrading
    if current_params:
        comparator = ParameterComparator()
        diff = comparator.compare(current_params, new_params)
        click.echo(f"Changes: {diff.total_changes}")
        if diff.added_dimensions:
            click.echo(f"  Added:    {', '.join(diff.added_dimensions)}")
        if diff.removed_dimensions:
            click.echo(f"  Removed:  {', '.join(diff.removed_dimensions)}")
        if diff.modified_dimensions:
            click.echo(f"  Modified: {', '.join(diff.modified_dimensions)}")
        click.echo()

    # Confirm unless --yes
    if not yes and not click.confirm(f"Deploy version {new_params.version}?"):
        click.echo("Deployment cancelled.", err=True)
        sys.exit(0)

    # Execute deployment
    try:
        deployed_version = manager.deploy(new_params, backup_current=not no_backup)
        click.echo()
        click.echo("=" * 60)
        click.echo("DEPLOYMENT COMPLETE")
        click.echo("=" * 60)
        click.echo(f"Active version: {deployed_version}")
        if not no_backup and current_version:
            click.echo(f"Previous version backed up to: {archive_dir}/")
    except Exception as e:
        click.echo(f"Deployment failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
