"""
Parameter deployment, versioning, and rollback tools.

Provides infrastructure for:
- Managing versioned parameter files
- Rolling back to previous parameter versions
- Comparing parameter changes between versions
- Deployment validation and safety checks

Created in Story 2.5 Task 8: Configuration and Deployment Tools.
"""

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from writescore.core.parameter_loader import ParameterLoader
from writescore.core.parameters import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    PercentileParameters,
    ThresholdParameters,
)

logger = logging.getLogger(__name__)


# Default paths for parameter management
DEFAULT_PARAMS_DIR = Path("config/parameters")
DEFAULT_ARCHIVE_DIR = Path("config/parameters/archive")
DEFAULT_ACTIVE_FILE = Path("config/scoring_parameters.yaml")


@dataclass
class ParameterChange:
    """Represents a single parameter change between versions."""

    dimension: str
    field: str
    old_value: Any
    new_value: Any
    change_type: str  # 'modified', 'added', 'removed'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_type": self.change_type,
        }


@dataclass
class ParameterDiff:
    """
    Comparison result between two parameter versions.

    Attributes:
        old_version: Version string of old parameters
        new_version: Version string of new parameters
        changes: List of individual parameter changes
        added_dimensions: Dimensions added in new version
        removed_dimensions: Dimensions removed in new version
        modified_dimensions: Dimensions with changed parameters
    """

    old_version: str
    new_version: str
    changes: List[ParameterChange] = field(default_factory=list)
    added_dimensions: List[str] = field(default_factory=list)
    removed_dimensions: List[str] = field(default_factory=list)
    modified_dimensions: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.changes or self.added_dimensions or self.removed_dimensions)

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.changes) + len(self.added_dimensions) + len(self.removed_dimensions)

    def format_summary(self) -> str:
        """Format a summary of changes."""
        lines = [f"Parameter Diff: {self.old_version} → {self.new_version}", "=" * 50]

        if not self.has_changes:
            lines.append("No changes detected.")
            return "\n".join(lines)

        lines.append(f"Total changes: {self.total_changes}")
        lines.append("")

        if self.added_dimensions:
            lines.append(f"Added dimensions ({len(self.added_dimensions)}):")
            for dim in self.added_dimensions:
                lines.append(f"  + {dim}")
            lines.append("")

        if self.removed_dimensions:
            lines.append(f"Removed dimensions ({len(self.removed_dimensions)}):")
            for dim in self.removed_dimensions:
                lines.append(f"  - {dim}")
            lines.append("")

        if self.modified_dimensions:
            lines.append(f"Modified dimensions ({len(self.modified_dimensions)}):")
            for dim in self.modified_dimensions:
                dim_changes = [c for c in self.changes if c.dimension == dim]
                lines.append(f"  ~ {dim}:")
                for change in dim_changes:
                    lines.append(f"      {change.field}: {change.old_value} → {change.new_value}")
            lines.append("")

        return "\n".join(lines)

    def format_detailed(self) -> str:
        """Format detailed change report."""
        lines = [self.format_summary()]

        if self.changes:
            lines.append("\n" + "=" * 50)
            lines.append("DETAILED CHANGES")
            lines.append("=" * 50 + "\n")

            for change in self.changes:
                lines.append(f"Dimension: {change.dimension}")
                lines.append(f"  Field: {change.field}")
                lines.append(f"  Type: {change.change_type}")
                lines.append(f"  Old: {change.old_value}")
                lines.append(f"  New: {change.new_value}")
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "added_dimensions": self.added_dimensions,
            "removed_dimensions": self.removed_dimensions,
            "modified_dimensions": self.modified_dimensions,
            "changes": [c.to_dict() for c in self.changes],
            "total_changes": self.total_changes,
        }


class ParameterVersionManager:
    """
    Manages versioned parameter files for deployment and rollback.

    Provides:
    - Listing available parameter versions
    - Deploying new parameter versions
    - Rolling back to previous versions
    - Archiving old versions
    """

    def __init__(
        self,
        params_dir: Optional[Path] = None,
        archive_dir: Optional[Path] = None,
        active_file: Optional[Path] = None,
    ):
        """
        Initialize version manager.

        Args:
            params_dir: Directory for versioned parameter files
            archive_dir: Directory for archived old versions
            active_file: Path to active parameter file
        """
        self.params_dir = params_dir or DEFAULT_PARAMS_DIR
        self.archive_dir = archive_dir or DEFAULT_ARCHIVE_DIR
        self.active_file = active_file or DEFAULT_ACTIVE_FILE

        # Ensure directories exist
        self.params_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def list_versions(self) -> List[Dict[str, Any]]:
        """
        List all available parameter versions.

        Returns:
            List of version info dictionaries with version, timestamp, path
        """
        versions = []

        # Check params directory for version files
        for yaml_file in sorted(self.params_dir.glob("*.yaml")):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                versions.append(
                    {
                        "version": data.get("version", "unknown"),
                        "timestamp": data.get("timestamp", "unknown"),
                        "path": str(yaml_file),
                        "filename": yaml_file.name,
                        "validation_dataset": data.get("validation_dataset_version", "unknown"),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not read version info from {yaml_file}: {e}")

        # Check archive directory
        for yaml_file in sorted(self.archive_dir.glob("*.yaml")):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                versions.append(
                    {
                        "version": data.get("version", "unknown"),
                        "timestamp": data.get("timestamp", "unknown"),
                        "path": str(yaml_file),
                        "filename": yaml_file.name,
                        "validation_dataset": data.get("validation_dataset_version", "unknown"),
                        "archived": True,
                    }
                )
            except Exception as e:
                logger.warning(f"Could not read version info from {yaml_file}: {e}")

        # Sort by version
        versions.sort(key=lambda v: v.get("version", ""), reverse=True)

        return versions

    def get_current_version(self) -> Optional[str]:
        """Get the currently active parameter version."""
        if not self.active_file.exists():
            return None

        try:
            with open(self.active_file) as f:
                data = yaml.safe_load(f)
            version = data.get("version")
            return str(version) if version is not None else None
        except Exception as e:
            logger.error(f"Could not read current version: {e}")
            return None

    def get_version_path(self, version: str) -> Optional[Path]:
        """
        Find the path to a specific version file.

        Args:
            version: Version string to find

        Returns:
            Path to version file, or None if not found
        """
        # Check params directory first
        for yaml_file in self.params_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if data.get("version") == version:
                    return yaml_file
            except Exception:
                continue

        # Check archive directory
        for yaml_file in self.archive_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if data.get("version") == version:
                    return yaml_file
            except Exception:
                continue

        return None

    def deploy(self, params: PercentileParameters, backup_current: bool = True) -> str:
        """
        Deploy new parameters as the active version.

        Args:
            params: Parameters to deploy
            backup_current: If True, backup current active parameters

        Returns:
            Deployed version string
        """
        # Validate before deployment
        params.validate()

        # Backup current if exists and requested
        if backup_current and self.active_file.exists():
            self._backup_current()

        # Save to versioned file
        version_filename = f"parameters_v{params.version}.yaml"
        version_path = self.params_dir / version_filename

        ParameterLoader.save(params, version_path)

        # Copy to active file
        shutil.copy(version_path, self.active_file)

        logger.info(f"Deployed parameters version {params.version}")

        return params.version

    def rollback(self, version: str) -> bool:
        """
        Rollback to a previous parameter version.

        Args:
            version: Version to rollback to

        Returns:
            True if rollback successful

        Raises:
            ValueError: If version not found
        """
        version_path = self.get_version_path(version)

        if version_path is None:
            available = [v["version"] for v in self.list_versions()]
            raise ValueError(f"Version '{version}' not found. Available versions: {available}")

        # Backup current before rollback
        if self.active_file.exists():
            self._backup_current()

        # Copy version file to active
        shutil.copy(version_path, self.active_file)

        logger.info(f"Rolled back to parameters version {version}")

        return True

    def _backup_current(self) -> Optional[Path]:
        """Backup current active parameters to archive."""
        if not self.active_file.exists():
            return None

        # Get current version for filename
        current_version = self.get_current_version() or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_filename = f"parameters_v{current_version}_{timestamp}.yaml"
        backup_path = self.archive_dir / backup_filename

        shutil.copy(self.active_file, backup_path)
        logger.info(f"Backed up current parameters to {backup_path}")

        return backup_path

    def archive_version(self, version: str) -> bool:
        """
        Move a version to the archive directory.

        Args:
            version: Version to archive

        Returns:
            True if archived successfully
        """
        version_path = self.get_version_path(version)

        if version_path is None:
            raise ValueError(f"Version '{version}' not found")

        if version_path.parent == self.archive_dir:
            logger.info(f"Version {version} is already archived")
            return True

        # Move to archive
        archive_path = self.archive_dir / version_path.name
        shutil.move(version_path, archive_path)

        logger.info(f"Archived version {version} to {archive_path}")

        return True


class ParameterComparator:
    """
    Compares two parameter versions to identify differences.
    """

    def compare(
        self, old_params: PercentileParameters, new_params: PercentileParameters
    ) -> ParameterDiff:
        """
        Compare two parameter sets.

        Args:
            old_params: Original parameters
            new_params: New parameters

        Returns:
            ParameterDiff with all changes
        """
        diff = ParameterDiff(old_version=old_params.version, new_version=new_params.version)

        old_dims = set(old_params.dimensions.keys())
        new_dims = set(new_params.dimensions.keys())

        # Identify added and removed dimensions
        diff.added_dimensions = list(new_dims - old_dims)
        diff.removed_dimensions = list(old_dims - new_dims)

        # Compare common dimensions
        common_dims = old_dims & new_dims

        for dim_name in common_dims:
            old_dim = old_params.dimensions[dim_name]
            new_dim = new_params.dimensions[dim_name]

            dim_changes = self._compare_dimension(dim_name, old_dim, new_dim)

            if dim_changes:
                diff.modified_dimensions.append(dim_name)
                diff.changes.extend(dim_changes)

        return diff

    def compare_versions(
        self, old_version: str, new_version: str, version_manager: ParameterVersionManager
    ) -> ParameterDiff:
        """
        Compare two versions by version string.

        Args:
            old_version: Old version string
            new_version: New version string
            version_manager: Version manager to locate files

        Returns:
            ParameterDiff with all changes
        """
        old_path = version_manager.get_version_path(old_version)
        new_path = version_manager.get_version_path(new_version)

        if old_path is None:
            raise ValueError(f"Old version '{old_version}' not found")
        if new_path is None:
            raise ValueError(f"New version '{new_version}' not found")

        old_params = ParameterLoader.load(old_path)
        new_params = ParameterLoader.load(new_path)

        return self.compare(old_params, new_params)

    def _compare_dimension(
        self, dim_name: str, old_dim: DimensionParameters, new_dim: DimensionParameters
    ) -> List[ParameterChange]:
        """Compare parameters for a single dimension."""
        changes = []

        # Check scoring type change
        if old_dim.scoring_type != new_dim.scoring_type:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="scoring_type",
                    old_value=old_dim.scoring_type.value,
                    new_value=new_dim.scoring_type.value,
                    change_type="modified",
                )
            )

        # Compare parameter values based on type
        if isinstance(old_dim.parameters, GaussianParameters) and isinstance(
            new_dim.parameters, GaussianParameters
        ):
            changes.extend(self._compare_gaussian(dim_name, old_dim.parameters, new_dim.parameters))

        elif isinstance(old_dim.parameters, MonotonicParameters) and isinstance(
            new_dim.parameters, MonotonicParameters
        ):
            changes.extend(
                self._compare_monotonic(dim_name, old_dim.parameters, new_dim.parameters)
            )

        elif isinstance(old_dim.parameters, ThresholdParameters) and isinstance(
            new_dim.parameters, ThresholdParameters
        ):
            changes.extend(
                self._compare_threshold(dim_name, old_dim.parameters, new_dim.parameters)
            )

        return changes

    def _compare_gaussian(
        self, dim_name: str, old_params: GaussianParameters, new_params: GaussianParameters
    ) -> List[ParameterChange]:
        """Compare Gaussian parameters."""
        changes = []

        if old_params.target.value != new_params.target.value:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="target",
                    old_value=old_params.target.value,
                    new_value=new_params.target.value,
                    change_type="modified",
                )
            )

        if old_params.width.value != new_params.width.value:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="width",
                    old_value=old_params.width.value,
                    new_value=new_params.width.value,
                    change_type="modified",
                )
            )

        return changes

    def _compare_monotonic(
        self, dim_name: str, old_params: MonotonicParameters, new_params: MonotonicParameters
    ) -> List[ParameterChange]:
        """Compare monotonic parameters."""
        changes = []

        if old_params.threshold_low.value != new_params.threshold_low.value:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="threshold_low",
                    old_value=old_params.threshold_low.value,
                    new_value=new_params.threshold_low.value,
                    change_type="modified",
                )
            )

        if old_params.threshold_high.value != new_params.threshold_high.value:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="threshold_high",
                    old_value=old_params.threshold_high.value,
                    new_value=new_params.threshold_high.value,
                    change_type="modified",
                )
            )

        if old_params.direction != new_params.direction:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="direction",
                    old_value=old_params.direction,
                    new_value=new_params.direction,
                    change_type="modified",
                )
            )

        return changes

    def _compare_threshold(
        self, dim_name: str, old_params: ThresholdParameters, new_params: ThresholdParameters
    ) -> List[ParameterChange]:
        """Compare threshold parameters."""
        changes = []

        # Compare threshold values
        old_thresholds = [t.value for t in old_params.thresholds]
        new_thresholds = [t.value for t in new_params.thresholds]

        if old_thresholds != new_thresholds:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="thresholds",
                    old_value=old_thresholds,
                    new_value=new_thresholds,
                    change_type="modified",
                )
            )

        if old_params.labels != new_params.labels:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="labels",
                    old_value=old_params.labels,
                    new_value=new_params.labels,
                    change_type="modified",
                )
            )

        if old_params.scores != new_params.scores:
            changes.append(
                ParameterChange(
                    dimension=dim_name,
                    field="scores",
                    old_value=old_params.scores,
                    new_value=new_params.scores,
                    change_type="modified",
                )
            )

        return changes


def generate_deployment_checklist(
    new_params: PercentileParameters, current_params: Optional[PercentileParameters] = None
) -> str:
    """
    Generate a deployment checklist for parameter updates.

    Args:
        new_params: Parameters being deployed
        current_params: Currently active parameters (for comparison)

    Returns:
        Formatted deployment checklist
    """
    lines = [
        "=" * 60,
        "PARAMETER DEPLOYMENT CHECKLIST",
        "=" * 60,
        "",
        f"New Version: {new_params.version}",
        f"Timestamp: {new_params.timestamp}",
        f"Validation Dataset: {new_params.validation_dataset_version}",
        "",
    ]

    # Version comparison
    if current_params:
        lines.append(f"Current Version: {current_params.version}")
        comparator = ParameterComparator()
        diff = comparator.compare(current_params, new_params)
        lines.append(f"Total Changes: {diff.total_changes}")
        lines.append("")

    lines.extend(
        [
            "PRE-DEPLOYMENT CHECKLIST:",
            "-" * 40,
            "[ ] Parameters validated against schema",
            "[ ] Score shift analysis completed",
            "    - Mean shift < 5 points",
            "    - Max shift < 15 points",
            "[ ] Validation dataset version confirmed",
            "[ ] Backup of current parameters created",
            "",
            "DEPLOYMENT STEPS:",
            "-" * 40,
            "[ ] 1. Run score shift analysis on test corpus",
            "       writescore analyze --validate-params NEW_PARAMS.yaml",
            "",
            "[ ] 2. Review shift report for anomalies",
            "       - Check per-dimension shifts",
            "       - Verify no regressions on known examples",
            "",
            "[ ] 3. Deploy to staging environment",
            "       writescore deploy --staging NEW_PARAMS.yaml",
            "",
            "[ ] 4. Run integration tests",
            "       pytest tests/integration/",
            "",
            "[ ] 5. Deploy to production",
            "       writescore deploy NEW_PARAMS.yaml",
            "",
            "POST-DEPLOYMENT VERIFICATION:",
            "-" * 40,
            "[ ] Verify active version matches deployed version",
            "[ ] Run smoke tests on representative documents",
            "[ ] Monitor for unexpected score distributions",
            "",
            "ROLLBACK PROCEDURE (if needed):",
            "-" * 40,
        ]
    )

    if current_params:
        lines.append(f"    writescore rollback --version {current_params.version}")
    else:
        lines.append("    writescore rollback --version PREVIOUS_VERSION")

    lines.extend(["", "=" * 60])

    return "\n".join(lines)


def format_version_list(
    versions: List[Dict[str, Any]], current_version: Optional[str] = None
) -> str:
    """
    Format version list for display.

    Args:
        versions: List of version info dicts
        current_version: Currently active version (will be marked)

    Returns:
        Formatted version list string
    """
    lines = ["AVAILABLE PARAMETER VERSIONS", "=" * 60, ""]

    if not versions:
        lines.append("No parameter versions found.")
        return "\n".join(lines)

    # Header
    lines.append(f"{'Version':<15} {'Timestamp':<25} {'Dataset':<15} {'Status'}")
    lines.append("-" * 70)

    for v in versions:
        version = v.get("version", "unknown")
        timestamp = v.get("timestamp", "unknown")[:19]  # Truncate to readable
        dataset = v.get("validation_dataset", "unknown")[:12]

        status_parts = []
        if version == current_version:
            status_parts.append("ACTIVE")
        if v.get("archived"):
            status_parts.append("archived")
        status = ", ".join(status_parts) if status_parts else ""

        lines.append(f"{version:<15} {timestamp:<25} {dataset:<15} {status}")

    lines.append("")
    lines.append(f"Total: {len(versions)} version(s)")

    return "\n".join(lines)
