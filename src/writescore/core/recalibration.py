"""
Parameter recalibration workflow.

Orchestrates the end-to-end process of recalibrating scoring parameters
based on validation dataset analysis.

Created in Story 2.5 Task 5.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from writescore.core.dataset import DatasetLoader, ValidationDataset
from writescore.core.distribution_analyzer import DistributionAnalysis, DistributionAnalyzer
from writescore.core.normality import NormalityResult, format_normality_report
from writescore.core.parameter_derivation import (
    DimensionParameters,
    ParameterDeriver,
)

logger = logging.getLogger(__name__)


class ParameterChange:
    """Represents a change in parameter values."""

    def __init__(
        self,
        dimension_name: str,
        old_params: Optional[DimensionParameters],
        new_params: DimensionParameters,
    ):
        """Initialize parameter change."""
        self.dimension_name = dimension_name
        self.old_params = old_params
        self.new_params = new_params

    def is_new_dimension(self) -> bool:
        """Check if this is a new dimension (no old params)."""
        return self.old_params is None

    def get_change_summary(self) -> Dict[str, Any]:
        """Get summary of parameter changes."""
        if self.is_new_dimension():
            return {
                "type": "new",
                "dimension": self.dimension_name,
                "scoring_method": self.new_params.scoring_method.value,
                "parameters": self.new_params.parameters.to_dict(),
            }

        # Compare old and new parameters
        assert self.old_params is not None  # Guaranteed by is_new_dimension() check above
        old_dict = self.old_params.parameters.to_dict()
        new_dict = self.new_params.parameters.to_dict()

        changes: Dict[str, Any] = {}
        for key in new_dict:
            if key not in old_dict:
                changes[key] = {"old": None, "new": new_dict[key]}
            elif old_dict[key] != new_dict[key]:
                if isinstance(new_dict[key], dict):
                    # Handle nested dicts (e.g., boundaries)
                    nested_changes = {}
                    for nested_key in new_dict[key]:
                        if (
                            nested_key not in old_dict[key]
                            or old_dict[key][nested_key] != new_dict[key][nested_key]
                        ):
                            nested_changes[nested_key] = {
                                "old": old_dict[key].get(nested_key),
                                "new": new_dict[key][nested_key],
                            }
                    if nested_changes:
                        changes[key] = nested_changes
                else:
                    changes[key] = {"old": old_dict[key], "new": new_dict[key]}

        return {
            "type": "modified",
            "dimension": self.dimension_name,
            "scoring_method": self.new_params.scoring_method.value,
            "changes": changes,
        }


class RecalibrationReport:
    """
    Comprehensive recalibration report.

    Attributes:
        dataset_info: Dataset metadata
        analysis_summary: Distribution analysis summary
        parameter_changes: List of ParameterChange objects
        timestamp: When recalibration was performed
        metadata: Additional metadata
    """

    def __init__(
        self,
        dataset_info: Dict[str, Any],
        analysis_summary: Dict[str, Any],
        parameter_changes: List[ParameterChange],
    ):
        """Initialize recalibration report."""
        self.dataset_info = dataset_info
        self.analysis_summary = analysis_summary
        self.parameter_changes = parameter_changes
        self.timestamp = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    def get_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        new_dims = [c for c in self.parameter_changes if c.is_new_dimension()]
        modified_dims = [c for c in self.parameter_changes if not c.is_new_dimension()]

        return {
            "timestamp": self.timestamp,
            "dataset_version": self.dataset_info.get("version"),
            "total_documents": self.dataset_info.get("total_documents", 0),
            "dimensions_analyzed": len(self.parameter_changes),
            "new_dimensions": len(new_dims),
            "modified_dimensions": len(modified_dims),
            "metadata": self.metadata,
        }

    def format_text_report(self) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("PARAMETER RECALIBRATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {self.timestamp}")
        lines.append(f"Dataset Version: {self.dataset_info.get('version')}")
        lines.append(f"Total Documents: {self.dataset_info.get('total_documents', 0)}")
        lines.append(f"  - Human: {self.dataset_info.get('human_documents', 0)}")
        lines.append(f"  - AI: {self.dataset_info.get('ai_documents', 0)}")
        lines.append("")

        # Summary statistics
        summary = self.get_summary()
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Dimensions Analyzed: {summary['dimensions_analyzed']}")
        lines.append(f"New Dimensions: {summary['new_dimensions']}")
        lines.append(f"Modified Dimensions: {summary['modified_dimensions']}")
        lines.append("")

        # Parameter changes
        lines.append("PARAMETER CHANGES")
        lines.append("-" * 80)

        for change in self.parameter_changes:
            change_summary = change.get_change_summary()

            if change_summary["type"] == "new":
                lines.append(f"\n[NEW] {change.dimension_name}")
                lines.append(f"  Scoring Method: {change_summary['scoring_method']}")
                lines.append(f"  Parameters: {json.dumps(change_summary['parameters'], indent=4)}")
            else:
                lines.append(f"\n[MODIFIED] {change.dimension_name}")
                lines.append(f"  Scoring Method: {change_summary['scoring_method']}")
                if change_summary["changes"]:
                    lines.append("  Changes:")
                    for key, value in change_summary["changes"].items():
                        if isinstance(value, dict) and "old" in value:
                            lines.append(f"    {key}: {value['old']} → {value['new']}")
                        else:
                            lines.append(f"    {key}: {json.dumps(value, indent=6)}")
                else:
                    lines.append("  No changes")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def save(self, output_path: Path) -> None:
        """Save report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "summary": self.get_summary(),
            "dataset_info": self.dataset_info,
            "analysis_summary": self.analysis_summary,
            "parameter_changes": [c.get_change_summary() for c in self.parameter_changes],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved recalibration report to {output_path}")


class RecalibrationWorkflow:
    """
    Orchestrates parameter recalibration workflow.

    Workflow steps:
    1. Load validation dataset
    2. Run distribution analysis
    3. Derive new parameters (with optional Shapiro-Wilk normality testing)
    4. Load existing parameters (if any)
    5. Generate comparison report
    6. Save parameters (with backup)
    7. Generate summary report
    """

    def __init__(self, auto_select_method: bool = False):
        """
        Initialize recalibration workflow.

        Args:
            auto_select_method: If True, use Shapiro-Wilk normality testing to
                              automatically select scoring method for each dimension.
                              Default: False (uses hardcoded method mapping).
        """
        self.auto_select_method = auto_select_method
        self.analyzer = DistributionAnalyzer()
        self.deriver = ParameterDeriver(auto_select_method=auto_select_method)
        self.dataset: Optional[ValidationDataset] = None
        self.analysis: Optional[DistributionAnalysis] = None
        self.derived_params: Optional[Dict[str, DimensionParameters]] = None
        self.old_params: Optional[Dict[str, DimensionParameters]] = None
        self.normality_results: Dict[str, NormalityResult] = {}

    def load_dataset(self, dataset_path: Path) -> ValidationDataset:
        """
        Load validation dataset.

        Args:
            dataset_path: Path to dataset file or directory

        Returns:
            ValidationDataset instance
        """
        logger.info(f"Loading validation dataset from {dataset_path}")
        dataset = DatasetLoader.load_jsonl(dataset_path)
        self.dataset = dataset
        logger.info(f"Loaded {len(dataset.documents)} documents " f"(version: {dataset.version})")
        return dataset

    def run_distribution_analysis(
        self, dimension_names: Optional[List[str]] = None
    ) -> DistributionAnalysis:
        """
        Run distribution analysis on loaded dataset.

        Args:
            dimension_names: Optional list of dimensions to analyze

        Returns:
            DistributionAnalysis results
        """
        if not self.dataset:
            raise ValueError("No dataset loaded. Call load_dataset() first.")

        logger.info("Running distribution analysis...")
        self.analysis = self.analyzer.analyze_dataset(self.dataset, dimension_names=dimension_names)
        logger.info(
            f"Analyzed {len(self.analysis.dimensions)} dimensions "
            f"across {self.dataset.get_statistics()['total_documents']} documents"
        )
        return self.analysis

    def derive_parameters(
        self, dimension_names: Optional[List[str]] = None
    ) -> Dict[str, DimensionParameters]:
        """
        Derive parameters from distribution analysis.

        Args:
            dimension_names: Optional list of dimensions to derive

        Returns:
            Dictionary of derived parameters
        """
        if not self.analysis:
            raise ValueError("No analysis available. Call run_distribution_analysis() first.")

        logger.info("Deriving parameters from distribution analysis...")
        if self.auto_select_method:
            logger.info("Using Shapiro-Wilk normality testing for method auto-selection")

        self.derived_params = self.deriver.derive_all_parameters(
            self.analysis, dimension_names=dimension_names
        )

        # Capture normality results if auto-selection was used
        if self.auto_select_method:
            self.normality_results = self.deriver.get_normality_results()
            logger.info(f"Normality tests completed for {len(self.normality_results)} dimensions")

        logger.info(f"Derived parameters for {len(self.derived_params)} dimensions")
        return self.derived_params

    def get_normality_report(self) -> str:
        """
        Get formatted normality test report.

        Returns:
            Formatted report string, or empty string if normality testing wasn't used.
        """
        if not self.normality_results:
            return ""
        return format_normality_report(self.normality_results)

    def get_normality_results(self) -> Dict[str, NormalityResult]:
        """
        Get raw normality test results.

        Returns:
            Dictionary mapping dimension names to NormalityResult objects.
        """
        return self.normality_results

    def load_existing_parameters(
        self, params_path: Path
    ) -> Optional[Dict[str, DimensionParameters]]:
        """
        Load existing parameters from file.

        Args:
            params_path: Path to existing parameters JSON file

        Returns:
            Dictionary of parameters, or None if file doesn't exist
        """
        if not params_path.exists():
            logger.info("No existing parameters file found")
            return None

        logger.info(f"Loading existing parameters from {params_path}")
        params = ParameterDeriver.load_parameters(params_path)
        self.old_params = params
        logger.info(f"Loaded parameters for {len(params)} dimensions")
        return params

    def generate_comparison_report(self) -> RecalibrationReport:
        """
        Generate comparison report between old and new parameters.

        Returns:
            RecalibrationReport instance
        """
        if not self.derived_params:
            raise ValueError("No derived parameters. Call derive_parameters() first.")

        logger.info("Generating comparison report...")

        # Build parameter changes list
        changes = []
        for dim_name, new_params in self.derived_params.items():
            old_params = self.old_params.get(dim_name) if self.old_params else None
            changes.append(ParameterChange(dim_name, old_params, new_params))

        # Build report
        dataset_info = self.dataset.get_statistics() if self.dataset else {}
        analysis_summary = (
            {
                "dataset_version": self.analysis.dataset_version,
                "dimensions_analyzed": len(self.analysis.dimensions),
            }
            if self.analysis
            else {}
        )

        report = RecalibrationReport(
            dataset_info=dataset_info, analysis_summary=analysis_summary, parameter_changes=changes
        )

        logger.info(
            f"Generated report: {report.get_summary()['new_dimensions']} new, "
            f"{report.get_summary()['modified_dimensions']} modified"
        )

        return report

    def save_parameters(self, output_path: Path, backup: bool = True) -> None:
        """
        Save derived parameters to file.

        Args:
            output_path: Path to save parameters
            backup: Whether to create backup of existing file
        """
        if not self.derived_params:
            raise ValueError("No derived parameters to save")

        # Create backup if requested and file exists
        if backup and output_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = output_path.parent / f"{output_path.stem}_backup_{timestamp}.json"
            shutil.copy2(output_path, backup_path)
            logger.info(f"Created backup at {backup_path}")

        # Save parameters
        metadata = {
            "recalibrated_at": datetime.now().isoformat(),
            "dataset_version": self.dataset.version if self.dataset else "unknown",
            "dimensions_count": len(self.derived_params),
        }

        self.deriver.save_parameters(self.derived_params, output_path, metadata=metadata)
        logger.info(f"Saved parameters to {output_path}")

    def run_full_workflow(
        self,
        dataset_path: Path,
        output_params_path: Path,
        existing_params_path: Optional[Path] = None,
        dimension_names: Optional[List[str]] = None,
        backup: bool = True,
    ) -> Tuple[Dict[str, DimensionParameters], RecalibrationReport]:
        """
        Run complete recalibration workflow.

        Args:
            dataset_path: Path to validation dataset
            output_params_path: Where to save derived parameters
            existing_params_path: Path to existing parameters (for comparison)
            dimension_names: Optional list of dimensions to process
            backup: Whether to backup existing parameters

        Returns:
            Tuple of (derived_parameters, report)
        """
        logger.info("=" * 80)
        logger.info("STARTING PARAMETER RECALIBRATION WORKFLOW")
        logger.info("=" * 80)

        # Step 1: Load dataset
        self.load_dataset(dataset_path)

        # Step 2: Run distribution analysis
        self.run_distribution_analysis(dimension_names=dimension_names)

        # Step 3: Derive parameters
        self.derive_parameters(dimension_names=dimension_names)

        # Step 4: Load existing parameters (if provided)
        if existing_params_path:
            self.load_existing_parameters(existing_params_path)

        # Step 5: Generate comparison report
        report = self.generate_comparison_report()

        # Step 6: Save parameters
        self.save_parameters(output_params_path, backup=backup)

        logger.info("=" * 80)
        logger.info("RECALIBRATION WORKFLOW COMPLETE")
        logger.info("=" * 80)

        assert self.derived_params is not None  # Set by derive_parameters()
        return self.derived_params, report
