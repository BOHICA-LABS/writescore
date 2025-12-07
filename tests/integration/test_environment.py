"""
Environment-aware tests for development setup.
Tests automatically skip based on detected environment.
"""

import os
import shutil
import subprocess

import pytest

# Environment detection
IN_CONTAINER = os.path.exists("/.dockerenv") or os.environ.get("REMOTE_CONTAINERS")
HAS_JUST = shutil.which("just") is not None
HAS_DOCKER = shutil.which("docker") is not None
HAS_DEVCONTAINER_CLI = shutil.which("devcontainer") is not None


class TestJustfile:
    """Justfile validation tests. Run if just is available."""

    @pytest.mark.skipif(not HAS_JUST, reason="just not installed")
    def test_justfile_syntax(self):
        """Verify Justfile has valid syntax and formatting."""
        result = subprocess.run(["just", "--fmt", "--check", "--unstable"], capture_output=True)
        assert result.returncode == 0, f"Justfile format error: {result.stderr.decode()}"

    @pytest.mark.skipif(not HAS_JUST, reason="just not installed")
    def test_justfile_recipes_parse(self):
        """Verify all recipes parse correctly."""
        result = subprocess.run(["just", "--list"], capture_output=True)
        assert result.returncode == 0, f"Justfile parse error: {result.stderr.decode()}"

    @pytest.mark.skipif(not HAS_JUST, reason="just not installed")
    @pytest.mark.parametrize(
        "recipe",
        ["install", "dev", "test", "test-all", "test-fast", "lint", "format", "coverage", "clean"],
    )
    def test_recipe_dry_run(self, recipe):
        """Verify each recipe can dry-run without errors."""
        result = subprocess.run(["just", "--dry-run", recipe], capture_output=True)
        assert result.returncode == 0, f"Recipe '{recipe}' failed: {result.stderr.decode()}"


class TestDevcontainer:
    """Devcontainer tests. Skip if in container or Docker unavailable."""

    @pytest.mark.skipif(IN_CONTAINER, reason="already in container")
    @pytest.mark.skipif(not HAS_DOCKER, reason="docker not installed")
    @pytest.mark.skipif(not HAS_DEVCONTAINER_CLI, reason="devcontainer CLI not installed")
    @pytest.mark.slow
    def test_devcontainer_builds(self):
        """Verify devcontainer builds successfully."""
        result = subprocess.run(
            ["devcontainer", "build", "--workspace-folder", "."], capture_output=True, timeout=300
        )
        assert result.returncode == 0, f"Devcontainer build failed: {result.stderr.decode()}"

    @pytest.mark.skipif(IN_CONTAINER, reason="already in container")
    @pytest.mark.skipif(not HAS_DOCKER, reason="docker not installed")
    @pytest.mark.skipif(not HAS_DEVCONTAINER_CLI, reason="devcontainer CLI not installed")
    @pytest.mark.slow
    def test_just_works_in_container(self):
        """Verify just commands work inside devcontainer."""
        # First ensure container is up
        subprocess.run(
            ["devcontainer", "up", "--workspace-folder", "."], capture_output=True, timeout=300
        )
        # Then test just works
        result = subprocess.run(
            ["devcontainer", "exec", "--workspace-folder", ".", "just", "--list"],
            capture_output=True,
            timeout=60,
        )
        assert result.returncode == 0, f"just failed in container: {result.stderr.decode()}"
