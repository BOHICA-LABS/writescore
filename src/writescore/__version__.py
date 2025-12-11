"""Version information for WriteScore.

This module provides version info that works both when installed normally
and when bundled with PyInstaller.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

try:
    __version__ = get_version("writescore")
except PackageNotFoundError:
    # PyInstaller bundle - read from pyproject.toml if available
    import sys
    from pathlib import Path

    # Try to find pyproject.toml relative to the script
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        # Check if pyproject.toml was bundled
        bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        pyproject_path = bundle_dir / "pyproject.toml"
        if pyproject_path.exists():
            import tomllib

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            __version__ = data.get("project", {}).get("version", "unknown")
        else:
            # Fallback - version should be updated when bumping
            __version__ = "6.4.0"
    else:
        # Not frozen and package not installed - development mode?
        __version__ = "dev"
