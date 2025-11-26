"""
Unit tests for parameter validation and score shift analysis.

Tests Story 2.5 Task 6: Validation and Backward Compatibility.
"""

import tempfile
from pathlib import Path

from writescore.core.parameters import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    ParameterValue,
    PercentileParameters,
    PercentileSource,
    ScoringType,
)
from writescore.core.validation import (
    MAX_ACCEPTABLE_MEAN_SHIFT,
    SHIFT_ERROR_THRESHOLD,
    SHIFT_WARNING_THRESHOLD,
    DocumentScoreShift,
    ParameterValidator,
    ScoreShiftAnalyzer,
    ScoreShiftReport,
    validate_parameter_update,
)


class TestDocumentScoreShift:
    """Test DocumentScoreShift class."""

    def test_basic_shift_calculation(self):
        """Test basic shift calculation."""
        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0, "dim_b": 60.0},
            new_scores={"dim_a": 55.0, "dim_b": 65.0}
        )

        assert shift.dimension_shifts["dim_a"] == 5.0
        assert shift.dimension_shifts["dim_b"] == 5.0
        assert shift.total_shift == 5.0  # Average of abs shifts

    def test_negative_shift(self):
        """Test negative shift (score decrease)."""
        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 80.0},
            new_scores={"dim_a": 60.0}
        )

        assert shift.dimension_shifts["dim_a"] == -20.0
        assert shift.total_shift == 20.0  # Absolute value

    def test_no_warning_for_small_shift(self):
        """Test no warning for shifts below threshold."""
        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 55.0}  # 5 point shift
        )

        assert not shift.has_warning_shift()
        assert not shift.has_error_shift()
        assert len(shift.get_flagged_dimensions()) == 0

    def test_warning_for_moderate_shift(self):
        """Test warning for shifts above warning threshold."""
        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 66.0}  # 16 point shift (> ERROR_THRESHOLD of 15)
        )

        assert shift.has_warning_shift()
        assert shift.has_error_shift()  # 16 > ERROR_THRESHOLD (15)
        flagged = shift.get_flagged_dimensions()
        assert len(flagged) == 1
        assert flagged[0][0] == "dim_a"

    def test_mixed_dimensions(self):
        """Test with some dimensions shifted, some not."""
        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"stable": 50.0, "shifted": 30.0},
            new_scores={"stable": 51.0, "shifted": 50.0}  # 20 point shift on 'shifted'
        )

        assert shift.dimension_shifts["stable"] == 1.0
        assert shift.dimension_shifts["shifted"] == 20.0
        assert shift.has_error_shift()

        flagged = shift.get_flagged_dimensions()
        assert len(flagged) == 1
        assert flagged[0][0] == "shifted"


class TestScoreShiftReport:
    """Test ScoreShiftReport class."""

    def test_empty_report(self):
        """Test report with no documents."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )
        report.calculate_summary()

        assert report.summary_stats["total_documents"] == 0
        assert report.is_acceptable()

    def test_single_document_acceptable(self):
        """Test report with single acceptable document."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        shift = DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0, "dim_b": 60.0},
            new_scores={"dim_a": 52.0, "dim_b": 61.0}
        )
        report.add_document_shift(shift)
        report.calculate_summary()

        assert report.summary_stats["total_documents"] == 1
        assert report.summary_stats["warning_count"] == 0
        assert report.summary_stats["error_count"] == 0
        assert report.is_acceptable()

    def test_multiple_documents_with_errors(self):
        """Test report with multiple documents including errors."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        # Acceptable document
        report.add_document_shift(DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 52.0}
        ))

        # Document with error-level shift
        report.add_document_shift(DocumentScoreShift(
            document_id="doc_02",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 70.0}  # 20 point shift
        ))

        report.calculate_summary()

        assert report.summary_stats["total_documents"] == 2
        assert report.summary_stats["error_count"] == 1
        assert not report.is_acceptable()

    def test_dimension_mean_shifts(self):
        """Test per-dimension mean shift calculation."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        report.add_document_shift(DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 60.0}  # +10
        ))

        report.add_document_shift(DocumentScoreShift(
            document_id="doc_02",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 70.0}  # +20
        ))

        report.calculate_summary()

        # Mean shift should be (10 + 20) / 2 = 15
        assert report.summary_stats["dimension_mean_shifts"]["dim_a"] == 15.0

    def test_format_text_report(self):
        """Test text report generation."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        report.add_document_shift(DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 55.0}
        ))

        text = report.format_text_report()

        assert "SCORE SHIFT ANALYSIS REPORT" in text
        assert "Old Parameters: 1.0" in text
        assert "New Parameters: 2.0" in text
        assert "Total Documents Analyzed: 1" in text

    def test_save_and_load(self):
        """Test saving report to JSON."""
        report = ScoreShiftReport(
            old_params_version="1.0",
            new_params_version="2.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        report.add_document_shift(DocumentScoreShift(
            document_id="doc_01",
            old_scores={"dim_a": 50.0},
            new_scores={"dim_a": 55.0}
        ))
        report.calculate_summary()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            report.save(path)

            assert path.exists()

            # Verify JSON structure
            import json
            with open(path) as f:
                data = json.load(f)

            assert data["old_params_version"] == "1.0"
            assert data["new_params_version"] == "2.0"
            assert len(data["document_shifts"]) == 1


class TestParameterValidator:
    """Test ParameterValidator class."""

    def _make_gaussian_params(self, target=10.0, width=2.0) -> DimensionParameters:
        """Helper to create Gaussian dimension parameters."""
        return DimensionParameters(
            dimension_name="test_dim",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(target, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(width, PercentileSource.STDEV)
            )
        )

    def _make_monotonic_params(self, low=0.3, high=0.7) -> DimensionParameters:
        """Helper to create monotonic dimension parameters."""
        return DimensionParameters(
            dimension_name="test_dim",
            scoring_type=ScoringType.MONOTONIC,
            parameters=MonotonicParameters(
                threshold_low=ParameterValue(low, PercentileSource.PERCENTILE, "p25_human"),
                threshold_high=ParameterValue(high, PercentileSource.PERCENTILE, "p75_human")
            )
        )

    def test_valid_parameters(self):
        """Test validation of valid parameters."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )
        params.dimensions["burstiness"] = self._make_gaussian_params()
        params.dimensions["lexical"] = self._make_monotonic_params()

        validator = ParameterValidator()
        is_valid = validator.validate_parameters(params)

        assert is_valid
        assert len(validator.errors) == 0

    def test_invalid_gaussian_width(self):
        """Test validation rejects zero width."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )

        # Create params with zero width
        invalid_dim = DimensionParameters(
            dimension_name="bad_dim",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(0.0, PercentileSource.STDEV)  # Invalid!
            )
        )
        params.dimensions["bad_dim"] = invalid_dim

        validator = ParameterValidator()
        is_valid = validator.validate_parameters(params)

        assert not is_valid
        assert len(validator.errors) > 0
        assert "width must be > 0" in validator.errors[0]

    def test_invalid_monotonic_thresholds(self):
        """Test validation rejects inverted thresholds."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )

        # Create params with inverted thresholds
        invalid_dim = DimensionParameters(
            dimension_name="bad_dim",
            scoring_type=ScoringType.MONOTONIC,
            parameters=MonotonicParameters(
                threshold_low=ParameterValue(0.8, PercentileSource.PERCENTILE, "p75_human"),
                threshold_high=ParameterValue(0.3, PercentileSource.PERCENTILE, "p25_human")
            )
        )
        params.dimensions["bad_dim"] = invalid_dim

        validator = ParameterValidator()
        is_valid = validator.validate_parameters(params)

        assert not is_valid
        assert len(validator.errors) > 0
        assert "must be <" in validator.errors[0]

    def test_warning_for_high_cv(self):
        """Test warning for high coefficient of variation."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )

        # Width much larger than target (CV > 2)
        params.dimensions["high_cv"] = DimensionParameters(
            dimension_name="high_cv",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(1.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(5.0, PercentileSource.STDEV)  # CV = 5
            )
        )

        validator = ParameterValidator()
        validator.validate_parameters(params)

        assert len(validator.warnings) > 0
        assert "coefficient of variation" in validator.warnings[0]

    def test_warning_for_missing_dimensions(self):
        """Test warning for missing recommended dimensions."""
        params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )
        # Only add one dimension, missing many recommended ones
        params.dimensions["custom"] = self._make_gaussian_params()

        validator = ParameterValidator()
        validator.validate_parameters(params)

        # Should warn about missing burstiness, lexical, etc.
        missing_warnings = [w for w in validator.warnings if "Missing recommended" in w]
        assert len(missing_warnings) > 0


class TestScoreShiftAnalyzer:
    """Test ScoreShiftAnalyzer class."""

    def test_analyze_identical_scores(self):
        """Test analysis with identical scores (no shift)."""
        old_scores = {
            "doc_01": {"dim_a": 50.0, "dim_b": 60.0},
            "doc_02": {"dim_a": 70.0, "dim_b": 80.0}
        }
        new_scores = old_scores.copy()  # Identical

        analyzer = ScoreShiftAnalyzer()
        report = analyzer.analyze_shift(old_scores, new_scores, "1.0", "1.0")

        assert report.summary_stats["mean_total_shift"] == 0.0
        assert report.is_acceptable()

    def test_analyze_small_shifts(self):
        """Test analysis with small acceptable shifts."""
        old_scores = {
            "doc_01": {"dim_a": 50.0, "dim_b": 60.0}
        }
        new_scores = {
            "doc_01": {"dim_a": 52.0, "dim_b": 61.0}
        }

        analyzer = ScoreShiftAnalyzer()
        report = analyzer.analyze_shift(old_scores, new_scores, "1.0", "2.0")

        assert report.summary_stats["mean_total_shift"] < MAX_ACCEPTABLE_MEAN_SHIFT
        assert report.is_acceptable()

    def test_analyze_large_shifts(self):
        """Test analysis with large unacceptable shifts."""
        old_scores = {
            "doc_01": {"dim_a": 50.0}
        }
        new_scores = {
            "doc_01": {"dim_a": 80.0}  # 30 point shift
        }

        analyzer = ScoreShiftAnalyzer()
        report = analyzer.analyze_shift(old_scores, new_scores, "1.0", "2.0")

        assert not report.is_acceptable()
        assert report.summary_stats["error_count"] == 1

    def test_analyze_from_files(self):
        """Test analysis from JSON files."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            old_path = Path(tmpdir) / "old_scores.json"
            new_path = Path(tmpdir) / "new_scores.json"

            # Create test files
            old_data = {
                "version": "1.0",
                "baselines": {
                    "doc_01": {"dim_a": 50.0}
                }
            }
            new_data = {
                "version": "2.0",
                "baselines": {
                    "doc_01": {"dim_a": 55.0}
                }
            }

            with open(old_path, 'w') as f:
                json.dump(old_data, f)
            with open(new_path, 'w') as f:
                json.dump(new_data, f)

            analyzer = ScoreShiftAnalyzer()
            report = analyzer.analyze_from_files(old_path, new_path)

            assert report.old_params_version == "1.0"
            assert report.new_params_version == "2.0"
            assert len(report.document_shifts) == 1


class TestValidateParameterUpdate:
    """Test validate_parameter_update function."""

    def test_validate_new_params_only(self):
        """Test validation of new params without old params."""
        new_params = PercentileParameters(
            version="1.0",
            timestamp="2025-11-24T10:00:00Z",
            validation_dataset_version="v2.0"
        )
        new_params.dimensions["test"] = DimensionParameters(
            dimension_name="test",
            scoring_type=ScoringType.GAUSSIAN,
            parameters=GaussianParameters(
                target=ParameterValue(10.0, PercentileSource.PERCENTILE, "p50_human"),
                width=ParameterValue(2.0, PercentileSource.STDEV)
            )
        )

        is_valid, report = validate_parameter_update(None, new_params)

        assert is_valid
        assert "No issues found" in report or "warnings" in report.lower()


class TestThresholdConstants:
    """Test threshold constant values."""

    def test_warning_less_than_error(self):
        """Ensure warning threshold is less than error threshold."""
        assert SHIFT_WARNING_THRESHOLD <= SHIFT_ERROR_THRESHOLD

    def test_thresholds_positive(self):
        """Ensure thresholds are positive."""
        assert SHIFT_WARNING_THRESHOLD > 0
        assert SHIFT_ERROR_THRESHOLD > 0
        assert MAX_ACCEPTABLE_MEAN_SHIFT > 0
