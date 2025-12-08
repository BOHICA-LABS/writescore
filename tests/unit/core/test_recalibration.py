"""
Unit tests for recalibration workflow infrastructure.

Tests Story 2.5 Task 5: Parameter recalibration workflow, change tracking, and reporting.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from writescore.core.dataset import DatasetLoader, Document, ValidationDataset
from writescore.core.distribution_analyzer import DistributionAnalysis
from writescore.core.parameter_derivation import (
    DimensionParameters,
    GaussianParameters,
    ScoringMethod,
    ThresholdParameters,
)
from writescore.core.recalibration import (
    ParameterChange,
    RecalibrationReport,
    RecalibrationWorkflow,
)


class TestParameterChange:
    """Test ParameterChange class."""

    def test_create_parameter_change_new_dimension(self):
        """Test creating parameter change for new dimension."""
        new_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )

        change = ParameterChange("burstiness", None, new_params)

        assert change.dimension_name == "burstiness"
        assert change.old_params is None
        assert change.new_params == new_params
        assert change.is_new_dimension()

    def test_create_parameter_change_modified_dimension(self):
        """Test creating parameter change for modified dimension."""
        old_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )
        new_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=12.0, width=2.5),
        )

        change = ParameterChange("burstiness", old_params, new_params)

        assert not change.is_new_dimension()
        assert change.old_params == old_params
        assert change.new_params == new_params

    def test_get_change_summary_new_dimension(self):
        """Test getting change summary for new dimension."""
        new_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )

        change = ParameterChange("burstiness", None, new_params)
        summary = change.get_change_summary()

        assert summary["type"] == "new"
        assert summary["dimension"] == "burstiness"
        assert summary["scoring_method"] == "gaussian"
        assert "parameters" in summary
        assert summary["parameters"]["target"] == 10.0

    def test_get_change_summary_modified_dimension(self):
        """Test getting change summary for modified dimension."""
        old_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )
        new_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=12.0, width=2.5),
        )

        change = ParameterChange("burstiness", old_params, new_params)
        summary = change.get_change_summary()

        assert summary["type"] == "modified"
        assert summary["dimension"] == "burstiness"
        assert summary["scoring_method"] == "gaussian"
        assert "changes" in summary
        assert "target" in summary["changes"]
        assert summary["changes"]["target"]["old"] == 10.0
        assert summary["changes"]["target"]["new"] == 12.0

    def test_get_change_summary_no_changes(self):
        """Test getting change summary when parameters identical."""
        old_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )
        new_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=GaussianParameters(target=10.0, width=2.0),
        )

        change = ParameterChange("burstiness", old_params, new_params)
        summary = change.get_change_summary()

        assert summary["type"] == "modified"
        assert summary["changes"] == {}

    def test_get_change_summary_nested_changes(self):
        """Test getting change summary with nested parameter changes."""
        old_params = DimensionParameters(
            dimension_name="readability",
            scoring_method=ScoringMethod.THRESHOLD,
            parameters=ThresholdParameters(
                boundaries={
                    "excellent_good": 0.75,
                    "good_acceptable": 0.50,
                    "acceptable_poor": 0.25,
                }
            ),
        )
        new_params = DimensionParameters(
            dimension_name="readability",
            scoring_method=ScoringMethod.THRESHOLD,
            parameters=ThresholdParameters(
                boundaries={
                    "excellent_good": 0.80,
                    "good_acceptable": 0.50,
                    "acceptable_poor": 0.25,
                }
            ),
        )

        change = ParameterChange("readability", old_params, new_params)
        summary = change.get_change_summary()

        assert summary["type"] == "modified"
        assert "boundaries" in summary["changes"]
        assert "excellent_good" in summary["changes"]["boundaries"]


class TestRecalibrationReport:
    """Test RecalibrationReport class."""

    def test_create_report(self):
        """Test creating recalibration report."""
        dataset_info = {"version": "v1.0", "total_documents": 100}
        analysis_summary = {"dataset_version": "v1.0", "dimensions_analyzed": 5}
        changes = []

        report = RecalibrationReport(dataset_info, analysis_summary, changes)

        assert report.dataset_info == dataset_info
        assert report.analysis_summary == analysis_summary
        assert report.parameter_changes == changes
        assert report.timestamp is not None

    def test_get_summary(self):
        """Test getting report summary."""
        dataset_info = {
            "version": "v1.0",
            "total_documents": 100,
            "human_documents": 50,
            "ai_documents": 50,
        }
        analysis_summary = {"dataset_version": "v1.0", "dimensions_analyzed": 5}

        # Create mix of new and modified dimensions
        new_change = ParameterChange(
            "new_dim",
            None,
            DimensionParameters("new_dim", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)),
        )
        modified_change = ParameterChange(
            "modified_dim",
            DimensionParameters(
                "modified_dim", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
            ),
            DimensionParameters(
                "modified_dim", ScoringMethod.GAUSSIAN, GaussianParameters(12.0, 2.5)
            ),
        )

        report = RecalibrationReport(dataset_info, analysis_summary, [new_change, modified_change])

        summary = report.get_summary()

        assert summary["dataset_version"] == "v1.0"
        assert summary["total_documents"] == 100
        assert summary["dimensions_analyzed"] == 2
        assert summary["new_dimensions"] == 1
        assert summary["modified_dimensions"] == 1

    def test_format_text_report(self):
        """Test generating text report."""
        dataset_info = {
            "version": "v1.0",
            "total_documents": 100,
            "human_documents": 50,
            "ai_documents": 50,
        }
        analysis_summary = {"dataset_version": "v1.0"}

        change = ParameterChange(
            "burstiness",
            None,
            DimensionParameters(
                "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
            ),
        )

        report = RecalibrationReport(dataset_info, analysis_summary, [change])
        text = report.format_text_report()

        assert "PARAMETER RECALIBRATION REPORT" in text
        assert "v1.0" in text
        assert "Total Documents: 100" in text
        assert "[NEW] burstiness" in text
        assert "Scoring Method: gaussian" in text

    def test_save_report(self):
        """Test saving report to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"

            dataset_info = {"version": "v1.0", "total_documents": 100}
            analysis_summary = {"dataset_version": "v1.0"}
            change = ParameterChange(
                "test",
                None,
                DimensionParameters("test", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)),
            )

            report = RecalibrationReport(dataset_info, analysis_summary, [change])
            report.save(output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["summary"]["dataset_version"] == "v1.0"
            assert data["dataset_info"]["total_documents"] == 100
            assert len(data["parameter_changes"]) == 1
            assert data["parameter_changes"][0]["dimension"] == "test"


class TestRecalibrationWorkflow:
    """Test RecalibrationWorkflow class."""

    def test_create_workflow(self):
        """Test creating workflow instance."""
        workflow = RecalibrationWorkflow()

        assert workflow.analyzer is not None
        assert workflow.deriver is not None
        assert workflow.dataset is None
        assert workflow.analysis is None

    def test_load_dataset(self):
        """Test loading validation dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Note: DatasetLoader infers version from filename stem
            dataset_path = Path(tmpdir) / "v1.0.jsonl"

            # Create test dataset
            dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
            dataset.add_document(
                Document(id="h1", text="Human text here", label="human", word_count=3)
            )
            DatasetLoader.save_jsonl(dataset, dataset_path)

            # Load via workflow
            workflow = RecalibrationWorkflow()
            loaded = workflow.load_dataset(dataset_path)

            assert loaded is not None
            assert loaded.version == "v1.0"  # Version inferred from "v1.0.jsonl"
            assert len(loaded.documents) == 1
            assert workflow.dataset is not None

    def test_run_distribution_analysis(self):
        """Test running distribution analysis."""
        workflow = RecalibrationWorkflow()

        # Create dataset
        workflow.dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
        workflow.dataset.add_document(
            Document(id="h1", text="Human text", label="human", word_count=2)
        )

        # Mock the analyzer to avoid needing real dimensions
        with patch.object(workflow.analyzer, "analyze_dataset") as mock_analyze:
            mock_analysis = DistributionAnalysis(
                dataset_version="v1.0", timestamp=datetime.now().isoformat()
            )
            mock_analyze.return_value = mock_analysis

            analysis = workflow.run_distribution_analysis()

            assert analysis is not None
            assert workflow.analysis is not None
            mock_analyze.assert_called_once()

    def test_run_distribution_analysis_no_dataset(self):
        """Test running analysis without loading dataset first."""
        workflow = RecalibrationWorkflow()

        with pytest.raises(ValueError, match="No dataset loaded"):
            workflow.run_distribution_analysis()

    def test_derive_parameters(self):
        """Test deriving parameters from analysis."""
        workflow = RecalibrationWorkflow()

        # Create mock analysis
        workflow.analysis = DistributionAnalysis(
            dataset_version="v1.0", timestamp=datetime.now().isoformat()
        )

        # Mock the deriver
        with patch.object(workflow.deriver, "derive_all_parameters") as mock_derive:
            mock_params = {
                "burstiness": DimensionParameters(
                    "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                )
            }
            mock_derive.return_value = mock_params

            params = workflow.derive_parameters()

            assert params is not None
            assert "burstiness" in params
            assert workflow.derived_params is not None
            mock_derive.assert_called_once()

    def test_derive_parameters_no_analysis(self):
        """Test deriving parameters without running analysis first."""
        workflow = RecalibrationWorkflow()

        with pytest.raises(ValueError, match="No analysis available"):
            workflow.derive_parameters()

    def test_load_existing_parameters(self):
        """Test loading existing parameters from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_path = Path(tmpdir) / "params.json"

            # Create existing parameters file
            params = {
                "burstiness": DimensionParameters(
                    "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                )
            }

            from writescore.core.parameter_derivation import ParameterDeriver

            deriver = ParameterDeriver()
            deriver.save_parameters(params, params_path)

            # Load via workflow
            workflow = RecalibrationWorkflow()
            loaded = workflow.load_existing_parameters(params_path)

            assert loaded is not None
            assert "burstiness" in loaded
            assert workflow.old_params is not None

    def test_load_existing_parameters_missing_file(self):
        """Test loading parameters when file doesn't exist."""
        workflow = RecalibrationWorkflow()
        nonexistent = Path("/tmp/does_not_exist_12345.json")

        result = workflow.load_existing_parameters(nonexistent)

        assert result is None
        assert workflow.old_params is None

    def test_generate_comparison_report(self):
        """Test generating comparison report."""
        workflow = RecalibrationWorkflow()

        # Setup dataset
        workflow.dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")

        # Setup analysis
        workflow.analysis = DistributionAnalysis(
            dataset_version="v1.0", timestamp=datetime.now().isoformat()
        )

        # Setup derived params
        workflow.derived_params = {
            "burstiness": DimensionParameters(
                "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(12.0, 2.5)
            )
        }

        # Setup old params
        workflow.old_params = {
            "burstiness": DimensionParameters(
                "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
            )
        }

        report = workflow.generate_comparison_report()

        assert report is not None
        assert len(report.parameter_changes) == 1
        assert report.parameter_changes[0].dimension_name == "burstiness"
        assert not report.parameter_changes[0].is_new_dimension()

    def test_generate_comparison_report_no_derived_params(self):
        """Test generating report without derived parameters."""
        workflow = RecalibrationWorkflow()

        with pytest.raises(ValueError, match="No derived parameters"):
            workflow.generate_comparison_report()

    def test_save_parameters(self):
        """Test saving parameters to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "params.json"

            workflow = RecalibrationWorkflow()
            workflow.dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
            workflow.derived_params = {
                "burstiness": DimensionParameters(
                    "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                )
            }

            workflow.save_parameters(output_path, backup=False)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "parameters" in data
            assert "burstiness" in data["parameters"]

    def test_save_parameters_with_backup(self):
        """Test saving parameters with backup of existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "params.json"

            # Create existing file
            with open(output_path, "w") as f:
                json.dump({"old": "data"}, f)

            workflow = RecalibrationWorkflow()
            workflow.dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
            workflow.derived_params = {
                "burstiness": DimensionParameters(
                    "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                )
            }

            workflow.save_parameters(output_path, backup=True)

            # Check backup was created
            backup_files = list(Path(tmpdir).glob("params_backup_*.json"))
            assert len(backup_files) == 1

            # Check backup has old data
            with open(backup_files[0]) as f:
                backup_data = json.load(f)
            assert backup_data["old"] == "data"

            # Check new file has new data
            with open(output_path) as f:
                new_data = json.load(f)
            assert "parameters" in new_data
            assert "burstiness" in new_data["parameters"]

    def test_save_parameters_no_derived_params(self):
        """Test saving parameters when none exist."""
        workflow = RecalibrationWorkflow()

        with pytest.raises(ValueError, match="No derived parameters to save"):
            workflow.save_parameters(Path("/tmp/test.json"))

    def test_run_full_workflow_integration(self):
        """Test complete workflow integration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.jsonl"
            output_path = Path(tmpdir) / "params.json"

            # Create test dataset
            dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
            dataset.add_document(
                Document(id="h1", text="Human text sample", label="human", word_count=3)
            )
            DatasetLoader.save_jsonl(dataset, dataset_path)

            workflow = RecalibrationWorkflow()

            # Mock analysis and derivation to avoid needing real dimensions
            with (
                patch.object(workflow.analyzer, "analyze_dataset") as mock_analyze,
                patch.object(workflow.deriver, "derive_all_parameters") as mock_derive,
            ):
                mock_analysis = DistributionAnalysis(
                    dataset_version="v1.0", timestamp=datetime.now().isoformat()
                )
                mock_analyze.return_value = mock_analysis

                mock_params = {
                    "burstiness": DimensionParameters(
                        "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                    )
                }
                mock_derive.return_value = mock_params

                # Run workflow
                params, report = workflow.run_full_workflow(
                    dataset_path=dataset_path, output_params_path=output_path, backup=False
                )

                # Verify results
                assert params is not None
                assert "burstiness" in params
                assert report is not None
                assert len(report.parameter_changes) == 1
                assert output_path.exists()

    def test_run_full_workflow_with_existing_params(self):
        """Test workflow with existing parameters for comparison."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.jsonl"
            existing_path = Path(tmpdir) / "old_params.json"
            output_path = Path(tmpdir) / "new_params.json"

            # Create test dataset
            dataset = ValidationDataset(version="v1.0", created="2025-11-24T10:00:00Z")
            dataset.add_document(Document(id="h1", text="Human text", label="human", word_count=2))
            DatasetLoader.save_jsonl(dataset, dataset_path)

            # Create existing parameters
            from writescore.core.parameter_derivation import ParameterDeriver

            old_params = {
                "burstiness": DimensionParameters(
                    "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(8.0, 1.5)
                )
            }
            deriver = ParameterDeriver()
            deriver.save_parameters(old_params, existing_path)

            workflow = RecalibrationWorkflow()

            # Mock analysis and derivation
            with (
                patch.object(workflow.analyzer, "analyze_dataset") as mock_analyze,
                patch.object(workflow.deriver, "derive_all_parameters") as mock_derive,
            ):
                mock_analysis = DistributionAnalysis(
                    dataset_version="v1.0", timestamp=datetime.now().isoformat()
                )
                mock_analyze.return_value = mock_analysis

                new_params = {
                    "burstiness": DimensionParameters(
                        "burstiness", ScoringMethod.GAUSSIAN, GaussianParameters(10.0, 2.0)
                    )
                }
                mock_derive.return_value = new_params

                # Run workflow with existing params
                params, report = workflow.run_full_workflow(
                    dataset_path=dataset_path,
                    output_params_path=output_path,
                    existing_params_path=existing_path,
                    backup=False,
                )

                # Verify comparison was made
                assert report is not None
                assert len(report.parameter_changes) == 1
                change = report.parameter_changes[0]
                assert not change.is_new_dimension()
                assert change.old_params is not None
                assert change.new_params is not None
