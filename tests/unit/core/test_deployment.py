"""
Unit tests for parameter deployment, versioning, and rollback tools.

Tests Story 2.5 Task 8: Configuration and Deployment Tools.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from writescore.core.deployment import (
    ParameterChange,
    ParameterComparator,
    ParameterDiff,
    ParameterVersionManager,
    format_version_list,
    generate_deployment_checklist,
)
from writescore.core.parameter_loader import ParameterLoader
from writescore.core.parameters import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    ParameterValue,
    PercentileParameters,
    PercentileSource,
    ScoringType,
)


class TestParameterChange:
    """Test ParameterChange dataclass."""

    def test_basic_change(self):
        """Test basic change creation."""
        change = ParameterChange(
            dimension="burstiness",
            field="target",
            old_value=10.0,
            new_value=12.0,
            change_type="modified"
        )

        assert change.dimension == "burstiness"
        assert change.field == "target"
        assert change.old_value == 10.0
        assert change.new_value == 12.0
        assert change.change_type == "modified"

    def test_to_dict(self):
        """Test serialization to dict."""
        change = ParameterChange(
            dimension="lexical",
            field="threshold_low",
            old_value=0.5,
            new_value=0.55,
            change_type="modified"
        )

        d = change.to_dict()

        assert d["dimension"] == "lexical"
        assert d["field"] == "threshold_low"
        assert d["old_value"] == 0.5
        assert d["new_value"] == 0.55


class TestParameterDiff:
    """Test ParameterDiff dataclass."""

    def test_empty_diff(self):
        """Test diff with no changes."""
        diff = ParameterDiff(old_version="1.0", new_version="1.1")

        assert not diff.has_changes
        assert diff.total_changes == 0

    def test_with_added_dimensions(self):
        """Test diff with added dimensions."""
        diff = ParameterDiff(
            old_version="1.0",
            new_version="2.0",
            added_dimensions=["new_dim1", "new_dim2"]
        )

        assert diff.has_changes
        assert diff.total_changes == 2

    def test_with_removed_dimensions(self):
        """Test diff with removed dimensions."""
        diff = ParameterDiff(
            old_version="1.0",
            new_version="2.0",
            removed_dimensions=["old_dim"]
        )

        assert diff.has_changes
        assert diff.total_changes == 1

    def test_with_modified_dimensions(self):
        """Test diff with modified dimensions."""
        change = ParameterChange(
            dimension="burstiness",
            field="target",
            old_value=10.0,
            new_value=12.0,
            change_type="modified"
        )

        diff = ParameterDiff(
            old_version="1.0",
            new_version="2.0",
            changes=[change],
            modified_dimensions=["burstiness"]
        )

        assert diff.has_changes
        assert diff.total_changes == 1
        assert "burstiness" in diff.modified_dimensions

    def test_format_summary_empty(self):
        """Test formatting empty diff."""
        diff = ParameterDiff(old_version="1.0", new_version="1.0")
        summary = diff.format_summary()

        assert "No changes detected" in summary
        assert "1.0 → 1.0" in summary

    def test_format_summary_with_changes(self):
        """Test formatting diff with changes."""
        diff = ParameterDiff(
            old_version="1.0",
            new_version="2.0",
            added_dimensions=["new_dim"],
            removed_dimensions=["old_dim"],
            modified_dimensions=["changed_dim"]
        )
        diff.changes.append(ParameterChange(
            dimension="changed_dim",
            field="target",
            old_value=10.0,
            new_value=15.0,
            change_type="modified"
        ))

        summary = diff.format_summary()

        assert "Added dimensions" in summary
        assert "Removed dimensions" in summary
        assert "Modified dimensions" in summary
        assert "new_dim" in summary
        assert "old_dim" in summary
        assert "changed_dim" in summary

    def test_to_dict(self):
        """Test serialization to dict."""
        diff = ParameterDiff(
            old_version="1.0",
            new_version="2.0",
            added_dimensions=["new_dim"]
        )

        d = diff.to_dict()

        assert d["old_version"] == "1.0"
        assert d["new_version"] == "2.0"
        assert "new_dim" in d["added_dimensions"]


class TestParameterVersionManager:
    """Test ParameterVersionManager class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_dir = Path(tmpdir) / "parameters"
            archive_dir = Path(tmpdir) / "archive"
            active_file = Path(tmpdir) / "active.yaml"
            params_dir.mkdir()
            archive_dir.mkdir()
            yield params_dir, archive_dir, active_file

    @pytest.fixture
    def sample_params(self):
        """Create sample parameters."""
        params = PercentileParameters(
            version="1.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v1"
        )
        params.add_dimension(DimensionParameters(
            dimension_name="burstiness",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            )
        ))
        return params

    def test_list_versions_empty(self, temp_dirs):
        """Test listing versions with empty directory."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        versions = manager.list_versions()

        assert len(versions) == 0

    def test_list_versions_with_files(self, temp_dirs, sample_params):
        """Test listing versions with parameter files."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Save a version file
        ParameterLoader.save(sample_params, params_dir / "v1.0.yaml")

        versions = manager.list_versions()

        assert len(versions) == 1
        assert versions[0]["version"] == "1.0"

    def test_get_current_version_none(self, temp_dirs):
        """Test getting current version when none exists."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        current = manager.get_current_version()

        assert current is None

    def test_get_current_version(self, temp_dirs, sample_params):
        """Test getting current version."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Set active version
        ParameterLoader.save(sample_params, active_file)

        current = manager.get_current_version()

        assert current == "1.0"

    def test_get_version_path(self, temp_dirs, sample_params):
        """Test finding version path."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Save version file
        ParameterLoader.save(sample_params, params_dir / "v1.0.yaml")

        path = manager.get_version_path("1.0")

        assert path is not None
        assert path.exists()

    def test_get_version_path_not_found(self, temp_dirs):
        """Test finding non-existent version."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        path = manager.get_version_path("999.0")

        assert path is None

    def test_deploy(self, temp_dirs, sample_params):
        """Test deploying parameters."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        version = manager.deploy(sample_params, backup_current=False)

        assert version == "1.0"
        assert active_file.exists()

    def test_deploy_with_backup(self, temp_dirs, sample_params):
        """Test deploying with backup of existing."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Deploy first version
        manager.deploy(sample_params, backup_current=False)

        # Create new version
        sample_params.version = "2.0"

        # Deploy with backup
        manager.deploy(sample_params, backup_current=True)

        # Check archive has backup
        archive_files = list(archive_dir.glob("*.yaml"))
        assert len(archive_files) >= 1

    def test_rollback(self, temp_dirs, sample_params):
        """Test rolling back to previous version."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Deploy v1.0
        ParameterLoader.save(sample_params, params_dir / "v1.0.yaml")
        manager.deploy(sample_params, backup_current=False)

        # Deploy v2.0
        sample_params.version = "2.0"
        ParameterLoader.save(sample_params, params_dir / "v2.0.yaml")
        manager.deploy(sample_params, backup_current=True)

        # Verify current is 2.0
        assert manager.get_current_version() == "2.0"

        # Rollback to 1.0
        manager.rollback("1.0")

        # Verify current is 1.0
        assert manager.get_current_version() == "1.0"

    def test_rollback_version_not_found(self, temp_dirs):
        """Test rollback to non-existent version."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        with pytest.raises(ValueError) as exc:
            manager.rollback("999.0")

        assert "not found" in str(exc.value)

    def test_archive_version(self, temp_dirs, sample_params):
        """Test archiving a version."""
        params_dir, archive_dir, active_file = temp_dirs
        manager = ParameterVersionManager(params_dir, archive_dir, active_file)

        # Save version
        ParameterLoader.save(sample_params, params_dir / "v1.0.yaml")

        # Archive it
        manager.archive_version("1.0")

        # Check it's in archive
        archive_files = list(archive_dir.glob("*.yaml"))
        assert len(archive_files) == 1


class TestParameterComparator:
    """Test ParameterComparator class."""

    @pytest.fixture
    def base_params(self):
        """Create base parameters."""
        params = PercentileParameters(
            version="1.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v1"
        )
        params.add_dimension(DimensionParameters(
            dimension_name="burstiness",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            )
        ))
        params.add_dimension(DimensionParameters(
            dimension_name="lexical",
            scoring_type=ScoringType.MONOTONIC,
            parameters=MonotonicParameters(
                threshold_low=ParameterValue(0.5, PercentileSource.PERCENTILE, "p25_human"),
                threshold_high=ParameterValue(0.7, PercentileSource.PERCENTILE, "p75_human")
            )
        ))
        return params

    def test_compare_identical(self, base_params):
        """Test comparing identical parameters."""
        comparator = ParameterComparator()

        diff = comparator.compare(base_params, base_params)

        assert not diff.has_changes
        assert diff.total_changes == 0

    def test_compare_added_dimension(self, base_params):
        """Test comparing with added dimension."""
        comparator = ParameterComparator()

        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )
        # Copy existing dimensions
        for _name, dim in base_params.dimensions.items():
            new_params.add_dimension(dim)

        # Add new dimension
        new_params.add_dimension(DimensionParameters(
            dimension_name="sentiment",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(0.1, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(0.05, PercentileSource.STDEV)
            )
        ))

        diff = comparator.compare(base_params, new_params)

        assert diff.has_changes
        assert "sentiment" in diff.added_dimensions
        assert len(diff.removed_dimensions) == 0

    def test_compare_removed_dimension(self, base_params):
        """Test comparing with removed dimension."""
        comparator = ParameterComparator()

        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )
        # Only copy one dimension
        new_params.add_dimension(base_params.dimensions["burstiness"])

        diff = comparator.compare(base_params, new_params)

        assert diff.has_changes
        assert "lexical" in diff.removed_dimensions

    def test_compare_modified_gaussian(self, base_params):
        """Test comparing modified Gaussian parameters."""
        comparator = ParameterComparator()

        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )
        # Copy lexical unchanged
        new_params.add_dimension(base_params.dimensions["lexical"])

        # Modify burstiness
        new_params.add_dimension(DimensionParameters(
            dimension_name="burstiness",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(12.0, PercentileSource.PERCENTILE, "p50_human"),  # Changed
                width=ParameterValue(2.5, PercentileSource.STDEV)  # Changed
            )
        ))

        diff = comparator.compare(base_params, new_params)

        assert diff.has_changes
        assert "burstiness" in diff.modified_dimensions
        assert len(diff.changes) == 2  # target and width

    def test_compare_modified_monotonic(self, base_params):
        """Test comparing modified monotonic parameters."""
        comparator = ParameterComparator()

        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )
        # Copy burstiness unchanged
        new_params.add_dimension(base_params.dimensions["burstiness"])

        # Modify lexical
        new_params.add_dimension(DimensionParameters(
            dimension_name="lexical",
            scoring_type=ScoringType.MONOTONIC,
            parameters=MonotonicParameters(
                threshold_low=ParameterValue(0.55, PercentileSource.PERCENTILE, "p25_human"),  # Changed
                threshold_high=ParameterValue(0.7, PercentileSource.PERCENTILE, "p75_human")
            )
        ))

        diff = comparator.compare(base_params, new_params)

        assert diff.has_changes
        assert "lexical" in diff.modified_dimensions


class TestFormatFunctions:
    """Test formatting utility functions."""

    def test_format_version_list_empty(self):
        """Test formatting empty version list."""
        result = format_version_list([], None)

        assert "AVAILABLE PARAMETER VERSIONS" in result
        assert "No parameter versions found" in result

    def test_format_version_list_with_versions(self):
        """Test formatting version list with entries."""
        versions = [
            {"version": "2.0", "timestamp": "2025-11-24T10:00:00", "validation_dataset": "v2"},
            {"version": "1.0", "timestamp": "2025-11-23T10:00:00", "validation_dataset": "v1"}
        ]

        result = format_version_list(versions, "2.0")

        assert "2.0" in result
        assert "1.0" in result
        assert "ACTIVE" in result
        assert "Total: 2 version(s)" in result

    def test_generate_deployment_checklist(self):
        """Test generating deployment checklist."""
        params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )

        checklist = generate_deployment_checklist(params)

        assert "PARAMETER DEPLOYMENT CHECKLIST" in checklist
        assert "New Version: 2.0" in checklist
        assert "PRE-DEPLOYMENT CHECKLIST" in checklist
        assert "DEPLOYMENT STEPS" in checklist
        assert "ROLLBACK PROCEDURE" in checklist

    def test_generate_deployment_checklist_with_current(self):
        """Test generating deployment checklist with current params."""
        old_params = PercentileParameters(
            version="1.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v1"
        )
        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="test_v2"
        )

        checklist = generate_deployment_checklist(new_params, old_params)

        assert "Current Version: 1.0" in checklist
        assert "New Version: 2.0" in checklist
        assert "rollback --version 1.0" in checklist


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_params_comparison(self):
        """Test comparing empty parameter sets."""
        comparator = ParameterComparator()

        old_params = PercentileParameters(
            version="1.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="v1"
        )
        new_params = PercentileParameters(
            version="2.0",
            timestamp=datetime.now().isoformat(),
            validation_dataset_version="v2"
        )

        diff = comparator.compare(old_params, new_params)

        assert not diff.has_changes

    def test_manager_creates_directories(self):
        """Test manager creates directories if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_dir = Path(tmpdir) / "new_params"
            archive_dir = Path(tmpdir) / "new_archive"

            # Directories don't exist yet
            assert not params_dir.exists()
            assert not archive_dir.exists()

            # Creating manager should create them
            ParameterVersionManager(params_dir, archive_dir)

            assert params_dir.exists()
            assert archive_dir.exists()
