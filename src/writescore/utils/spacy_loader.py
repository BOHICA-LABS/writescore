"""
Utility for loading spacy models with automatic download.
"""

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
        subprocess.check_call(
            [sys.executable, "-m", "spacy", "download", model_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return spacy.load(model_name)
