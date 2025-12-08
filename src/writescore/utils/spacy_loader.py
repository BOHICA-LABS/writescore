"""
Utility for loading spacy models with automatic download.
"""

import shutil
import subprocess
import sys

import spacy


def load_spacy_model(model_name: str = "en_core_web_sm"):
    """
    Load a spacy model, downloading it automatically if not installed.

    Args:
        model_name: Name of the spacy model to load (default: en_core_web_sm)

    Returns:
        Loaded spacy Language model
    """
    try:
        return spacy.load(model_name)
    except OSError:
        _download_model(model_name)
        return spacy.load(model_name)


def _download_model(model_name: str) -> None:
    """Download a spacy model using available tools (uv or pip)."""
    # Try uv first (faster, works in uv environments)
    if shutil.which("uv"):
        subprocess.run(
            ["uv", "pip", "install", model_name],
            check=True,
            capture_output=True,
        )
    else:
        # Fall back to pip via spacy's CLI
        subprocess.run(
            [sys.executable, "-m", "pip", "install", model_name],
            check=True,
            capture_output=True,
        )
