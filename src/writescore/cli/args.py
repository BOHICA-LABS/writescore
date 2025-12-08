"""
Command-line argument parsing.

This module handles all CLI argument definitions and parsing.
"""

import argparse
import os
import sys


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
│ Example:  analyze_ai_patterns.py chapter.md --mode fast                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ ADAPTIVE MODE - Smart Sampling (RECOMMENDED, DEFAULT)                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Speed:    30-240 seconds for 90-page chapters                           │
│ Coverage: 10-20% of document (adapts to length)                         │
│ Use When: Book chapters, long documents, regular analysis               │
│ Behavior: <5k chars = full, 5k-50k = 5 samples, >50k = 10 samples      │
│                                                                           │
│ Example:  analyze_ai_patterns.py chapter.md                             │
│           analyze_ai_patterns.py chapter.md --mode adaptive             │
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
│ Example:  analyze_ai_patterns.py chapter.md --mode sampling \\           │
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
│ Example:  analyze_ai_patterns.py chapter.md --mode full                 │
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
  analyze_ai_patterns.py --batch manuscript/ --mode adaptive

  # Detailed analysis with fast mode (quick iteration)
  analyze_ai_patterns.py chapter.md --mode fast --detailed

  # Dual scoring with full mode (publication check)
  analyze_ai_patterns.py chapter.md --mode full --show-scores

  # Check what mode would do
  analyze_ai_patterns.py chapter.md --mode adaptive --dry-run

For complete documentation: docs/analysis-modes-guide.md
    """)


def validate_mode_arguments(args):
    """
    Validate mode-related argument combinations.

    Args:
        args: Parsed arguments

    Raises:
        ValueError: If arguments are invalid

    Prints warnings for suboptimal configurations.
    """
    # Validate sample count
    if hasattr(args, "samples") and not 1 <= args.samples <= 20:
        raise ValueError(f"Invalid sample count: {args.samples} (must be between 1-20)")

    # Validate sample size
    if hasattr(args, "sample_size") and not 500 <= args.sample_size <= 10000:
        raise ValueError(f"Invalid sample size: {args.sample_size} (must be between 500-10000)")

    # Warning: sampling args with fast mode
    if (
        hasattr(args, "mode")
        and args.mode == "fast"
        and (args.samples != 5 or args.sample_size != 2000)
    ):
        print("Warning: --samples and --sample-size are ignored in 'fast' mode", file=sys.stderr)

    # Warning: FULL mode with large files
    if hasattr(args, "mode") and args.mode == "full" and args.file and os.path.exists(args.file):
        file_size = os.path.getsize(args.file)
        if file_size > 500000:  # >500k chars (~250 pages)
            pages = file_size / 2000
            print(
                f"\n⚠ Warning: FULL mode with {pages:.0f}-page document may take 20+ minutes.",
                file=sys.stderr,
            )
            print(
                "           Consider using --mode adaptive for faster results (30-240s).\n",
                file=sys.stderr,
            )

            # Interactive confirmation (skip if --quiet or in batch or dry-run)
            if not hasattr(args, "quiet") or (
                not args.quiet and not args.batch and not args.dry_run
            ):
                try:
                    response = input("Continue with FULL mode? (y/n): ")
                    if response.lower() != "y":
                        print("Canceled. Use --mode adaptive for faster analysis.", file=sys.stderr)
                        sys.exit(0)
                except (EOFError, KeyboardInterrupt):
                    print("\nCanceled.", file=sys.stderr)
                    sys.exit(0)


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Analyze manuscripts for AI-generated content patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file (default: adaptive mode)
  %(prog)s chapter-01.md

  # Quick preview with fast mode (5-15 seconds)
  %(prog)s chapter-01.md --mode fast

  # Full accuracy analysis (5-20 minutes for large files)
  %(prog)s chapter-01.md --mode full

  # Custom sampling configuration
  %(prog)s chapter-01.md --mode sampling --samples 10 --sample-size 3000

  # Detailed analysis with line numbers and suggestions (for LLM-driven humanization)
  %(prog)s chapter-01.md --detailed

  # Dual score analysis with optimization path (recommended for LLM optimization)
  %(prog)s chapter-01.md --show-scores

  # Dual score with custom targets
  %(prog)s chapter-01.md --show-scores --quality-target 90 --detection-target 20

  # Dual score JSON output (for programmatic use)
  %(prog)s chapter-01.md --show-scores --format json

  # Analyze with custom domain terms
  %(prog)s chapter-01.md --domain-terms "Docker,Kubernetes,PostgreSQL"

  # Batch analyze directory, output TSV
  %(prog)s --batch manuscript/sections --format tsv > analysis.tsv

  # Save detailed analysis to file
  %(prog)s chapter-01.md --detailed -o humanization-report.txt

For detailed mode information: %(prog)s --help-modes
        """,
    )

    parser.add_argument("file", nargs="?", help="Markdown file to analyze")
    parser.add_argument("--batch", metavar="DIR", help="Analyze all .md files in directory")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Provide detailed line-by-line diagnostics with context and suggestions (for LLM cleanup)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "tsv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--domain-terms",
        metavar="TERMS",
        help="Comma-separated domain-specific terms to detect (overrides defaults)",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE", help="Write output to file instead of stdout"
    )

    # Dual scoring options
    parser.add_argument(
        "--show-scores",
        action="store_true",
        help="Calculate and display dual scores (Detection Risk + Quality Score) with optimization path",
    )
    parser.add_argument(
        "--detection-target",
        type=float,
        default=30.0,
        metavar="N",
        help="Target detection risk score (0-100, lower=better, default: 30.0)",
    )
    parser.add_argument(
        "--quality-target",
        type=float,
        default=85.0,
        metavar="N",
        help="Target quality score (0-100, higher=better, default: 85.0)",
    )

    # History tracking and visualization (v2.0)
    parser.add_argument(
        "--show-history",
        action="store_true",
        help="Show aggregate score trends (quality/detection)",
    )
    parser.add_argument(
        "--show-history-full",
        action="store_true",
        help="Show complete optimization journey with all iterations",
    )
    parser.add_argument(
        "--show-dimension-trends",
        action="store_true",
        help="Show trends for all dimensions (v2.0 data required)",
    )
    parser.add_argument(
        "--show-raw-metric-trends",
        action="store_true",
        help="Show raw metric trends with sparklines (v2.0 data required)",
    )
    parser.add_argument(
        "--compare-history",
        type=str,
        metavar="I1,I2",
        help='Compare two iterations (e.g., "first,last" or "1,5")',
    )
    parser.add_argument(
        "--export-history",
        type=str,
        choices=["csv", "json"],
        metavar="FORMAT",
        help="Export history to CSV or JSON format",
    )
    parser.add_argument(
        "--history-notes",
        type=str,
        default="",
        metavar="NOTES",
        help='Add notes for this iteration (e.g., "Fixed AI vocabulary")',
    )

    # Output control
    parser.add_argument(
        "--no-score-summary", action="store_true", help="Suppress score summary display in output"
    )

    # Analysis mode arguments
    mode_group = parser.add_argument_group(
        "Analysis Mode Options", "Control speed vs accuracy tradeoff for dimension analysis"
    )

    mode_group.add_argument(
        "--mode",
        "-m",
        choices=["fast", "adaptive", "sampling", "full"],
        default="adaptive",
        help="""Analysis mode (default: adaptive)

  fast     - Quick preview, first 2000 chars/dimension (5-15s)
  adaptive - Smart sampling, adapts to length (30-240s, RECOMMENDED)
  sampling - Custom sampling configuration (60-300s)
  full     - Complete analysis, no limits (5-20min for 90-page chapters)

Use --help-modes for detailed mode information.
        """,
    )

    mode_group.add_argument(
        "--samples",
        type=int,
        default=5,
        metavar="N",
        help="Number of sections to sample (default: 5, range: 1-20). Used in sampling/adaptive modes.",
    )

    mode_group.add_argument(
        "--sample-size",
        type=int,
        default=2000,
        metavar="CHARS",
        help="Characters per sample section (default: 2000, range: 500-10000).",
    )

    mode_group.add_argument(
        "--sample-strategy",
        choices=["even", "weighted", "adaptive"],
        default="even",
        help="""Sampling distribution (default: even)
  even     - Evenly distributed throughout document
  weighted - 40%% beginning, 20%% middle, 40%% end
  adaptive - Smart sampling based on content (future)
        """,
    )

    # Utility flags for mode configuration
    parser.add_argument(
        "--dry-run", action="store_true", help="Show configuration without running analysis"
    )

    parser.add_argument(
        "--show-coverage",
        action="store_true",
        help="Display coverage statistics (samples, chars analyzed, coverage %%)",
    )

    parser.add_argument(
        "--help-modes",
        action="store_true",
        help="Show detailed information about analysis modes and exit",
    )

    # Handle --help-modes before parsing
    if "--help-modes" in sys.argv:
        show_mode_help()
        sys.exit(0)

    args = parser.parse_args()

    # Validate inputs
    if not args.file and not args.batch:
        parser.error("Either FILE or --batch DIR must be specified")

    # Detailed mode limitations
    if args.detailed and args.batch:
        print(
            "Warning: --detailed mode not supported for batch analysis. Using standard mode.",
            file=sys.stderr,
        )
        args.detailed = False

    if args.detailed and args.format == "tsv":
        print(
            "Warning: --detailed mode not compatible with TSV format. Using JSON format.",
            file=sys.stderr,
        )
        args.format = "json"

    # Show scores validation
    if args.show_scores and args.batch:
        print(
            "Warning: --show-scores mode not supported for batch analysis. Using standard mode.",
            file=sys.stderr,
        )
        args.show_scores = False

    # Validate mode arguments
    validate_mode_arguments(args)

    return args


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
