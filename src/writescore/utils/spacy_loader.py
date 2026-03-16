"""
Utility for loading spacy models with automatic download.
"""

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import spacy

COMPAT_URL = "https://raw.githubusercontent.com/explosion/spacy-models/master/compatibility.json"


def load_spacy_model(model_name: str = "en_core_web_sm"):
    """
    Load a spacy model, downloading it automatically if not installed.

    Args:
        model_name: Name of the spacy model to load (default: en_core_web_sm)

    Returns:
        Loaded spacy Language model
    """
    # Check if running in PyInstaller bundle
    if getattr(sys, "frozen", False):
        return _load_frozen_model(model_name)

    try:
        return spacy.load(model_name)
    except OSError:
        _download_model(model_name)
        return spacy.load(model_name)


def _load_frozen_model(model_name: str):
    """Load spacy model from PyInstaller bundle."""
    bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]

    # Try to load the model package directly
    try:
        return spacy.load(model_name)
    except OSError:
        pass

    # Try to load from bundled path
    model_path = bundle_dir / model_name
    if model_path.exists():
        # Look for the versioned model directory inside
        for item in model_path.iterdir():
            if item.is_dir() and item.name.startswith(model_name):
                return spacy.load(str(item))
        # Try loading the model_path directly
        return spacy.load(str(model_path))

    raise OSError(
        f"[E050] Can't find model '{model_name}' in PyInstaller bundle. " f"Checked: {model_path}"
    )


def _get_model_url(model_name: str) -> str:
    """Get the download URL for a compatible spacy model version."""
    # Fetch compatibility data from spacy's GitHub
    with urllib.request.urlopen(COMPAT_URL, timeout=30) as response:
        compat_data = json.loads(response.read().decode())

    # Get spacy version (major.minor)
    spacy_version = ".".join(spacy.__version__.split(".")[:2])

    # Find compatible model version
    spacy_compat = compat_data.get("spacy", {})
    model_version = None

    for version_key, models in spacy_compat.items():
        # Version keys are like "3.8" or "3.7" (no "v" prefix)
        version_matches = version_key == spacy_version or version_key == f"v{spacy_version}"
        if version_matches and model_name in models:
            model_version = models[model_name][0]  # First (latest) compatible version
            break

    if not model_version:
        raise RuntimeError(
            f"Could not find compatible version of {model_name} for spacy {spacy_version}"
        )

    # Construct GitHub releases download URL
    base_url = "https://github.com/explosion/spacy-models/releases/download"
    wheel_name = f"{model_name}-{model_version}-py3-none-any.whl"
    return f"{base_url}/{model_name}-{model_version}/{wheel_name}"


def _download_model(model_name: str) -> None:
    """Download a spacy model using available tools (uv or pip)."""
    # Get the direct download URL for this model
    url = _get_model_url(model_name)

    # Try uv first (faster, works in uv environments)
    if shutil.which("uv"):
        subprocess.run(
            ["uv", "pip", "install", url],
            check=True,
            capture_output=True,
        )
    else:
        # Fall back to pip
        subprocess.run(
            [sys.executable, "-m", "pip", "install", url],
            check=True,
            capture_output=True,
        )
