"""
Test utility to capture baseline scores for regression testing.

This script analyzes all samples in the regression corpus with all 13 dimensions
and saves the baseline scores for future regression testing.

Usage:
    python tests/utils/capture_baselines.py

Output:
    tests/fixtures/baseline_scores.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from writescore.dimensions.advanced_lexical import AdvancedLexicalDimension
from writescore.dimensions.burstiness import BurstinessDimension
from writescore.dimensions.figurative_language import FigurativeLanguageDimension
from writescore.dimensions.formatting import FormattingDimension
from writescore.dimensions.lexical import LexicalDimension
from writescore.dimensions.perplexity import PerplexityDimension
from writescore.dimensions.predictability import PredictabilityDimension
from writescore.dimensions.readability import ReadabilityDimension
from writescore.dimensions.sentiment import SentimentDimension
from writescore.dimensions.structure import StructureDimension
from writescore.dimensions.syntactic import SyntacticDimension
from writescore.dimensions.transition_marker import TransitionMarkerDimension
from writescore.dimensions.voice import VoiceDimension


def get_package_version():
    """Get package version from setup.py or pyproject.toml."""
    try:
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        if setup_path.exists():
            with open(setup_path) as f:
                for line in f:
                    if "version=" in line:
                        # Extract version string
                        version = (
                            line.split("version=")[1].split(",")[0].strip().strip('"').strip("'")
                        )
                        return version
        return "unknown"
    except Exception:
        return "unknown"


def capture_baselines():
    """Capture baseline scores for all corpus samples."""

    print("=" * 80)
    print("BASELINE SCORE CAPTURE")
    print("=" * 80)

    # Load corpus
    corpus_path = Path(__file__).parent.parent / "fixtures" / "regression_corpus.json"
    print(f"\nLoading corpus from: {corpus_path}")

    with open(corpus_path) as f:
        corpus_data = json.load(f)

    print(f"Loaded {len(corpus_data['samples'])} samples")

    # Initialize dimensions
    print("\nInitializing 13 dimensions...")
    dimensions = {
        "predictability": PredictabilityDimension(),
        "advanced_lexical": AdvancedLexicalDimension(),
        "readability": ReadabilityDimension(),
        "transition_marker": TransitionMarkerDimension(),
        "perplexity": PerplexityDimension(),
        "burstiness": BurstinessDimension(),
        "structure": StructureDimension(),
        "formatting": FormattingDimension(),
        "voice": VoiceDimension(),
        "lexical": LexicalDimension(),
        "sentiment": SentimentDimension(),
        "syntactic": SyntacticDimension(),
        "figurative_language": FigurativeLanguageDimension(),
    }

    print(f"Initialized: {', '.join(dimensions.keys())}")

    # Capture scores
    print("\n" + "=" * 80)
    print("ANALYZING SAMPLES")
    print("=" * 80)

    baselines = {}

    for i, sample in enumerate(corpus_data["samples"], 1):
        sample_id = sample["id"]
        text = sample["text"]
        category = sample["category"]

        print(f"\n[{i}/{len(corpus_data['samples'])}] Analyzing {sample_id} ({category})...")

        scores = {}
        for dim_name, dimension in dimensions.items():
            try:
                metrics = dimension.analyze(text)
                score = dimension.calculate_score(metrics)
                scores[dim_name] = round(score, 1)
                print(f"  ✓ {dim_name:20s} {score:5.1f}")
            except Exception as e:
                print(f"  ✗ {dim_name:20s} ERROR: {e}")
                scores[dim_name] = 0.0

        baselines[sample_id] = scores

    # Save baselines
    print("\n" + "=" * 80)
    print("SAVING BASELINES")
    print("=" * 80)

    output_data = {
        "version": "1.0",
        "captured": datetime.utcnow().isoformat() + "Z",
        "model_versions": {
            "writescore": get_package_version(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "baselines": baselines,
    }

    output_path = Path(__file__).parent.parent / "fixtures" / "baseline_scores.json"
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Baselines saved to: {output_path}")
    print(f"   Total samples: {len(baselines)}")
    print(f"   Dimensions per sample: {len(dimensions)}")
    print(f"   Total baseline scores: {len(baselines) * len(dimensions)}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    capture_baselines()
