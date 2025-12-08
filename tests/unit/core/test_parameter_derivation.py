"""
Unit tests for parameter derivation infrastructure.

Tests Story 2.5 Task 4: Parameter derivation from distribution analysis.
"""

import tempfile
from pathlib import Path

from writescore.core.distribution_analyzer import DimensionStatistics, DistributionAnalysis
from writescore.core.parameter_derivation import (
    DimensionParameters,
    GaussianParameters,
    MonotonicParameters,
    ParameterDeriver,
    ScoringMethod,
    ThresholdParameters,
)


class TestParameterDataclasses:
    """Test parameter dataclasses."""

    def test_gaussian_parameters(self):
        """Test GaussianParameters creation and dict conversion."""
        params = GaussianParameters(target=50.0, width=10.0, method="stdev")

        assert params.target == 50.0
        assert params.width == 10.0
        assert params.method == "stdev"

        data = params.to_dict()
        assert data["target"] == 50.0
        assert data["width"] == 10.0
        assert data["method"] == "stdev"

    def test_monotonic_parameters(self):
        """Test MonotonicParameters creation and dict conversion."""
        params = MonotonicParameters(threshold_low=25.0, threshold_high=75.0, inverted=False)

        assert params.threshold_low == 25.0
        assert params.threshold_high == 75.0
        assert not params.inverted

        data = params.to_dict()
        assert data["threshold_low"] == 25.0
        assert data["threshold_high"] == 75.0
        assert data["inverted"] is False

    def test_threshold_parameters(self):
        """Test ThresholdParameters creation and dict conversion."""
        params = ThresholdParameters(
            boundaries={"excellent_good": 75.0, "good_acceptable": 50.0, "acceptable_poor": 25.0}
        )

        assert params.boundaries["excellent_good"] == 75.0
        assert params.boundaries["good_acceptable"] == 50.0

        data = params.to_dict()
        assert data["boundaries"]["excellent_good"] == 75.0

    def test_dimension_parameters(self):
        """Test DimensionParameters with Gaussian params."""
        gaussian = GaussianParameters(target=50.0, width=10.0)
        dim_params = DimensionParameters(
            dimension_name="burstiness",
            scoring_method=ScoringMethod.GAUSSIAN,
            parameters=gaussian,
            metadata={"human_p50": 50.0},
        )

        assert dim_params.dimension_name == "burstiness"
        assert dim_params.scoring_method == ScoringMethod.GAUSSIAN
        assert dim_params.parameters.target == 50.0

        data = dim_params.to_dict()
        assert data["dimension_name"] == "burstiness"
        assert data["scoring_method"] == "gaussian"
        assert data["parameters"]["target"] == 50.0


class TestParameterDeriver:
    """Test ParameterDeriver class."""

    def test_create_deriver(self):
        """Test creating parameter deriver."""
        deriver = ParameterDeriver()

        assert deriver is not None
        assert "burstiness" in deriver.default_scoring_methods
        assert deriver.default_scoring_methods["burstiness"] == ScoringMethod.GAUSSIAN

    def test_derive_gaussian_parameters_with_stdev(self):
        """Test deriving Gaussian parameters using stdev."""
        deriver = ParameterDeriver()

        stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[10.0, 15.0, 20.0, 25.0, 30.0],
        )
        stats.compute()

        params = deriver._derive_gaussian_parameters(stats)

        assert isinstance(params, GaussianParameters)
        assert params.target == stats.median
        assert params.width == stats.stdev
        assert params.method == "stdev"

    def test_derive_gaussian_parameters_with_iqr_fallback(self):
        """Test Gaussian derivation with IQR fallback when stdev=0."""
        deriver = ParameterDeriver()

        # Single value = stdev of 0
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[50.0, 50.0, 50.0],  # No variation
        )
        stats.compute()

        params = deriver._derive_gaussian_parameters(stats)

        assert isinstance(params, GaussianParameters)
        # Should use fallback logic since stdev = 0
        assert params.width > 0

    def test_derive_monotonic_parameters(self):
        """Test deriving monotonic parameters."""
        deriver = ParameterDeriver()

        human_stats = DimensionStatistics(
            dimension_name="lexical",
            metric_name="type_token_ratio",
            values=[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        )
        human_stats.compute()

        ai_stats = DimensionStatistics(
            dimension_name="lexical",
            metric_name="type_token_ratio",
            values=[0.1, 0.2, 0.3, 0.4, 0.5],
        )
        ai_stats.compute()

        params = deriver._derive_monotonic_parameters(human_stats, ai_stats)

        assert isinstance(params, MonotonicParameters)
        assert params.threshold_low == human_stats.percentiles["p25"]
        assert params.threshold_high == human_stats.percentiles["p75"]
        assert params.threshold_low < params.threshold_high

    def test_derive_monotonic_parameters_inverted(self):
        """Test monotonic parameters with inverted flag."""
        deriver = ParameterDeriver()

        # Human has low values
        human_stats = DimensionStatistics(
            dimension_name="test", metric_name="test", values=[1.0, 2.0, 3.0, 4.0, 5.0]
        )
        human_stats.compute()

        # AI has high values (median > human median)
        ai_stats = DimensionStatistics(
            dimension_name="test", metric_name="test", values=[6.0, 7.0, 8.0, 9.0, 10.0]
        )
        ai_stats.compute()

        params = deriver._derive_monotonic_parameters(human_stats, ai_stats)

        # Should be inverted since AI median > human median
        assert params.inverted is True

    def test_derive_monotonic_parameters_sanity_check(self):
        """Test monotonic parameters with invalid ordering."""
        deriver = ParameterDeriver()

        # Create stats where p25 >= p75 (shouldn't happen in real data)
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[50.0, 50.0, 50.0],  # All same value
        )
        stats.compute()

        params = deriver._derive_monotonic_parameters(stats)

        # Should apply fallback logic
        assert params.threshold_low < params.threshold_high

    def test_derive_threshold_parameters(self):
        """Test deriving threshold parameters."""
        deriver = ParameterDeriver()

        human_stats = DimensionStatistics(
            dimension_name="readability",
            metric_name="flesch_reading_ease",
            values=[60.0, 65.0, 70.0, 75.0, 80.0],
        )
        human_stats.compute()

        ai_stats = DimensionStatistics(
            dimension_name="readability",
            metric_name="flesch_reading_ease",
            values=[40.0, 45.0, 50.0, 55.0, 60.0],
        )
        ai_stats.compute()

        combined_stats = DimensionStatistics(
            dimension_name="readability",
            metric_name="flesch_reading_ease",
            values=[40.0, 50.0, 60.0, 70.0, 80.0],
        )
        combined_stats.compute()

        params = deriver._derive_threshold_parameters(human_stats, ai_stats, combined_stats)

        assert isinstance(params, ThresholdParameters)
        assert "excellent_good" in params.boundaries
        assert "good_acceptable" in params.boundaries
        assert "acceptable_poor" in params.boundaries

        # Check ordering: excellent > good > acceptable > poor
        assert params.boundaries["excellent_good"] > params.boundaries["good_acceptable"]
        assert params.boundaries["good_acceptable"] > params.boundaries["acceptable_poor"]

    def test_derive_dimension_parameters_gaussian(self):
        """Test deriving full dimension parameters with Gaussian method."""
        deriver = ParameterDeriver()

        # Create analysis with human stats
        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        human_stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[10.0, 15.0, 20.0, 25.0, 30.0],
        )
        human_stats.compute()
        analysis.add_dimension_stats("burstiness", "human", human_stats)

        # Derive parameters
        dim_params = deriver.derive_dimension_parameters(
            analysis, "burstiness", scoring_method=ScoringMethod.GAUSSIAN
        )

        assert dim_params is not None
        assert dim_params.dimension_name == "burstiness"
        assert dim_params.scoring_method == ScoringMethod.GAUSSIAN
        assert isinstance(dim_params.parameters, GaussianParameters)
        assert "human_p50" in dim_params.metadata
        assert "human_stdev" in dim_params.metadata

    def test_derive_dimension_parameters_monotonic(self):
        """Test deriving dimension parameters with Monotonic method."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        human_stats = DimensionStatistics(
            dimension_name="lexical",
            metric_name="type_token_ratio",
            values=[0.4, 0.5, 0.6, 0.7, 0.8],
        )
        human_stats.compute()
        analysis.add_dimension_stats("lexical", "human", human_stats)

        ai_stats = DimensionStatistics(
            dimension_name="lexical",
            metric_name="type_token_ratio",
            values=[0.2, 0.3, 0.4, 0.5, 0.6],
        )
        ai_stats.compute()
        analysis.add_dimension_stats("lexical", "ai", ai_stats)

        # Derive parameters
        dim_params = deriver.derive_dimension_parameters(
            analysis, "lexical", scoring_method=ScoringMethod.MONOTONIC
        )

        assert dim_params is not None
        assert dim_params.scoring_method == ScoringMethod.MONOTONIC
        assert isinstance(dim_params.parameters, MonotonicParameters)
        assert "ai_p50" in dim_params.metadata

    def test_derive_dimension_parameters_threshold(self):
        """Test deriving dimension parameters with Threshold method."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        for label in ["human", "ai", "combined"]:
            stats = DimensionStatistics(
                dimension_name="readability",
                metric_name="flesch_reading_ease",
                values=[40.0 + i * 5 for i in range(10)],
            )
            stats.compute()
            analysis.add_dimension_stats("readability", label, stats)

        # Derive parameters
        dim_params = deriver.derive_dimension_parameters(
            analysis, "readability", scoring_method=ScoringMethod.THRESHOLD
        )

        assert dim_params is not None
        assert dim_params.scoring_method == ScoringMethod.THRESHOLD
        assert isinstance(dim_params.parameters, ThresholdParameters)
        assert len(dim_params.parameters.boundaries) == 3

    def test_derive_dimension_parameters_missing_stats(self):
        """Test that derivation returns None when stats missing."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        # No stats added for 'test_dimension'
        result = deriver.derive_dimension_parameters(analysis, "test_dimension")

        assert result is None

    def test_derive_dimension_parameters_uses_default_method(self):
        """Test that default scoring method is used when not specified."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        human_stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[10.0, 15.0, 20.0, 25.0, 30.0],
        )
        human_stats.compute()
        analysis.add_dimension_stats("burstiness", "human", human_stats)

        # Don't specify scoring_method - should use default (GAUSSIAN for burstiness)
        dim_params = deriver.derive_dimension_parameters(analysis, "burstiness")

        assert dim_params.scoring_method == ScoringMethod.GAUSSIAN

    def test_derive_all_parameters(self):
        """Test deriving parameters for multiple dimensions."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        # Add stats for multiple dimensions
        for dim_name in ["burstiness", "lexical", "readability"]:
            human_stats = DimensionStatistics(
                dimension_name=dim_name,
                metric_name="test",
                values=[10.0 + i * 5 for i in range(10)],
            )
            human_stats.compute()
            analysis.add_dimension_stats(dim_name, "human", human_stats)

        # Derive all
        all_params = deriver.derive_all_parameters(analysis)

        assert len(all_params) == 3
        assert "burstiness" in all_params
        assert "lexical" in all_params
        assert "readability" in all_params

    def test_derive_all_parameters_subset(self):
        """Test deriving parameters for subset of dimensions."""
        deriver = ParameterDeriver()

        analysis = DistributionAnalysis(dataset_version="v1.0", timestamp="2025-11-24T10:00:00Z")

        # Add stats for multiple dimensions
        for dim_name in ["burstiness", "lexical", "readability"]:
            human_stats = DimensionStatistics(
                dimension_name=dim_name,
                metric_name="test",
                values=[10.0 + i * 5 for i in range(10)],
            )
            human_stats.compute()
            analysis.add_dimension_stats(dim_name, "human", human_stats)

        # Derive only burstiness and lexical
        all_params = deriver.derive_all_parameters(
            analysis, dimension_names=["burstiness", "lexical"]
        )

        assert len(all_params) == 2
        assert "burstiness" in all_params
        assert "lexical" in all_params
        assert "readability" not in all_params

    def test_save_and_load_parameters(self):
        """Test saving and loading parameters to/from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "parameters.json"

            # Create parameters
            gaussian = GaussianParameters(target=50.0, width=10.0)
            monotonic = MonotonicParameters(threshold_low=25.0, threshold_high=75.0)

            params = {
                "burstiness": DimensionParameters(
                    dimension_name="burstiness",
                    scoring_method=ScoringMethod.GAUSSIAN,
                    parameters=gaussian,
                    metadata={"human_p50": 50.0},
                ),
                "lexical": DimensionParameters(
                    dimension_name="lexical",
                    scoring_method=ScoringMethod.MONOTONIC,
                    parameters=monotonic,
                    metadata={"human_p25": 25.0},
                ),
            }

            # Save
            deriver = ParameterDeriver()
            deriver.save_parameters(params, file_path, metadata={"test": "value"})

            assert file_path.exists()

            # Load
            loaded = ParameterDeriver.load_parameters(file_path)

            assert len(loaded) == 2
            assert "burstiness" in loaded
            assert "lexical" in loaded

            # Check Gaussian params
            burst_params = loaded["burstiness"]
            assert burst_params.scoring_method == ScoringMethod.GAUSSIAN
            assert burst_params.parameters.target == 50.0
            assert burst_params.parameters.width == 10.0

            # Check Monotonic params
            lex_params = loaded["lexical"]
            assert lex_params.scoring_method == ScoringMethod.MONOTONIC
            assert lex_params.parameters.threshold_low == 25.0
            assert lex_params.parameters.threshold_high == 75.0

    def test_roundtrip_preserves_data(self):
        """Test that save/load roundtrip preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "params.json"

            # Create comprehensive parameters with all types
            threshold = ThresholdParameters(
                boundaries={
                    "excellent_good": 85.0,
                    "good_acceptable": 65.0,
                    "acceptable_poor": 45.0,
                }
            )

            params = {
                "readability": DimensionParameters(
                    dimension_name="readability",
                    scoring_method=ScoringMethod.THRESHOLD,
                    parameters=threshold,
                    metadata={"human_p50": 70.0, "human_p75": 85.0, "ai_count": 100},
                )
            }

            # Save and load
            deriver = ParameterDeriver()
            deriver.save_parameters(
                params, file_path, metadata={"version": "2.5", "created": "2025-11-24"}
            )
            loaded = ParameterDeriver.load_parameters(file_path)

            # Verify
            read_params = loaded["readability"]
            assert read_params.dimension_name == "readability"
            assert read_params.scoring_method == ScoringMethod.THRESHOLD
            assert len(read_params.parameters.boundaries) == 3
            assert read_params.parameters.boundaries["excellent_good"] == 85.0
            assert read_params.metadata["human_p50"] == 70.0
            assert read_params.metadata["ai_count"] == 100

    def test_integration_full_workflow(self):
        """Test complete workflow: analysis -> derivation -> save -> load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_file = Path(tmpdir) / "derived_params.json"

            # Step 1: Create distribution analysis
            analysis = DistributionAnalysis(
                dataset_version="v1.0",
                timestamp="2025-11-24T10:00:00Z",
                metadata={"total_documents": 20},
            )

            # Add statistics for 3 dimensions
            for dim_name in ["burstiness", "lexical", "sentiment"]:
                human_stats = DimensionStatistics(
                    dimension_name=dim_name,
                    metric_name="test_metric",
                    values=[10.0 + i * 2 for i in range(20)],
                )
                human_stats.compute()
                analysis.add_dimension_stats(dim_name, "human", human_stats)

            # Step 2: Derive parameters
            deriver = ParameterDeriver()
            derived_params = deriver.derive_all_parameters(analysis)

            assert len(derived_params) == 3

            # Step 3: Save
            deriver.save_parameters(
                derived_params, params_file, metadata={"dataset_version": "v1.0"}
            )

            # Step 4: Load
            loaded_params = ParameterDeriver.load_parameters(params_file)

            # Step 5: Verify
            assert len(loaded_params) == 3
            for dim_name in ["burstiness", "lexical", "sentiment"]:
                assert dim_name in loaded_params
                assert loaded_params[dim_name].dimension_name == dim_name
                assert "human_p50" in loaded_params[dim_name].metadata
