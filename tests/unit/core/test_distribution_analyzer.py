"""
Unit tests for distribution analysis infrastructure.

Tests Story 2.5 Task 3: Distribution analysis, statistics computation, and reporting.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from writescore.core.dataset import Document, ValidationDataset
from writescore.core.dimension_registry import DimensionRegistry
from writescore.core.distribution_analyzer import (
    DimensionStatistics,
    DistributionAnalysis,
    DistributionAnalyzer,
)
from writescore.dimensions.base_strategy import DimensionTier


class TestDimensionStatistics:
    """Test DimensionStatistics dataclass."""

    def test_compute_basic_statistics(self):
        """Test computing basic statistics from values."""
        stats = DimensionStatistics(
            dimension_name="test_dim",
            metric_name="test_metric",
            values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        )

        stats.compute()

        assert stats.mean == 5.5
        assert stats.median == 5.5
        assert stats.count == 10
        assert stats.min_val == 1.0
        assert stats.max_val == 10.0
        assert 'p50' in stats.percentiles
        assert stats.percentiles['p50'] == 5.5

    def test_compute_percentiles(self):
        """Test percentile computation."""
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=list(range(1, 101))  # 1-100
        )

        stats.compute()

        assert stats.percentiles['p10'] == pytest.approx(10.9, rel=1e-1)
        assert stats.percentiles['p25'] == pytest.approx(25.75, rel=1e-1)
        assert stats.percentiles['p50'] == pytest.approx(50.5, rel=1e-1)
        assert stats.percentiles['p75'] == pytest.approx(75.25, rel=1e-1)
        assert stats.percentiles['p90'] == pytest.approx(90.1, rel=1e-1)

    def test_compute_iqr(self):
        """Test IQR computation."""
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        )

        stats.compute()

        # IQR = p75 - p25
        iqr = stats.percentiles['p75'] - stats.percentiles['p25']
        assert stats.iqr == pytest.approx(iqr, rel=1e-2)

    def test_compute_higher_order_statistics(self):
        """Test skewness and kurtosis computation."""
        # Right-skewed distribution
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[1, 1, 1, 2, 2, 3, 10]  # Right-skewed
        )

        stats.compute()

        assert stats.skewness is not None
        assert stats.skewness > 0  # Positive skew
        assert stats.kurtosis is not None

    def test_empty_values(self):
        """Test handling empty values list."""
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[]
        )

        stats.compute()

        assert stats.count == 0
        assert stats.mean == 0.0
        assert stats.stdev == 0.0

    def test_single_value(self):
        """Test statistics with single value."""
        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[42.0]
        )

        stats.compute()

        assert stats.mean == 42.0
        assert stats.median == 42.0
        assert stats.stdev == 0.0
        assert stats.count == 1

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[1.0, 2.0, 3.0, 4.0, 5.0]
        )
        stats.compute()

        data = stats.to_dict()

        assert data['dimension_name'] == "burstiness"
        assert data['metric_name'] == "variance"
        assert data['count'] == 5
        assert 'mean' in data
        assert 'percentiles' in data
        assert 'p50' in data['percentiles']


class TestDistributionAnalysis:
    """Test DistributionAnalysis container."""

    def test_create_empty_analysis(self):
        """Test creating empty analysis."""
        analysis = DistributionAnalysis(
            dataset_version="v1.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        assert analysis.dataset_version == "v1.0"
        assert len(analysis.dimensions) == 0

    def test_add_dimension_stats(self):
        """Test adding dimension statistics."""
        analysis = DistributionAnalysis(
            dataset_version="v1.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[1.0, 2.0, 3.0]
        )
        stats.compute()

        analysis.add_dimension_stats("burstiness", "human", stats)

        assert "burstiness" in analysis.dimensions
        assert "human" in analysis.dimensions["burstiness"]

    def test_get_dimension_stats(self):
        """Test retrieving dimension statistics."""
        analysis = DistributionAnalysis(
            dataset_version="v1.0",
            timestamp="2025-11-24T10:00:00Z"
        )

        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[1, 2, 3]
        )
        stats.compute()

        analysis.add_dimension_stats("test", "ai", stats)

        retrieved = analysis.get_dimension_stats("test", "ai")
        assert retrieved is not None
        assert retrieved.dimension_name == "test"

        missing = analysis.get_dimension_stats("nonexistent", "human")
        assert missing is None

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        analysis = DistributionAnalysis(
            dataset_version="v1.0",
            timestamp="2025-11-24T10:00:00Z",
            metadata={"test": "value"}
        )

        stats = DimensionStatistics(
            dimension_name="test",
            metric_name="test",
            values=[1, 2, 3]
        )
        stats.compute()
        analysis.add_dimension_stats("test", "human", stats)

        data = analysis.to_dict()

        assert data['dataset_version'] == "v1.0"
        assert data['timestamp'] == "2025-11-24T10:00:00Z"
        assert 'dimensions' in data
        assert 'test' in data['dimensions']
        assert 'human' in data['dimensions']['test']
        assert data['metadata']['test'] == "value"

    def test_save_and_load_json(self):
        """Test saving and loading analysis as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "analysis.json"

            # Create analysis
            original = DistributionAnalysis(
                dataset_version="v1.0",
                timestamp="2025-11-24T10:00:00Z",
                metadata={"docs": 100}
            )

            stats = DimensionStatistics(
                dimension_name="burstiness",
                metric_name="variance",
                values=[1.0, 2.0, 3.0, 4.0, 5.0]
            )
            stats.compute()
            original.add_dimension_stats("burstiness", "human", stats)

            # Save
            original.save_json(file_path)
            assert file_path.exists()

            # Load
            loaded = DistributionAnalysis.load_json(file_path)

            assert loaded.dataset_version == original.dataset_version
            assert loaded.timestamp == original.timestamp
            assert "burstiness" in loaded.dimensions
            assert "human" in loaded.dimensions["burstiness"]

            loaded_stats = loaded.get_dimension_stats("burstiness", "human")
            assert loaded_stats.dimension_name == "burstiness"
            assert loaded_stats.metric_name == "variance"
            assert loaded_stats.count == 5


class TestDistributionAnalyzer:
    """Test DistributionAnalyzer class."""

    def test_create_analyzer(self):
        """Test creating analyzer with registry."""
        analyzer = DistributionAnalyzer(registry=DimensionRegistry)

        assert analyzer.registry is not None

    def test_extract_metrics_burstiness(self):
        """Test extracting burstiness metrics."""
        analyzer = DistributionAnalyzer()

        metrics = {'variance': 12.5, 'other': 'value'}
        result = analyzer._extract_metrics('burstiness', metrics)

        assert 'variance' in result
        assert result['variance'] == 12.5

    def test_extract_metrics_lexical(self):
        """Test extracting lexical metrics."""
        analyzer = DistributionAnalyzer()

        metrics = {'type_token_ratio': 0.75, 'unique_words': 100}
        result = analyzer._extract_metrics('lexical', metrics)

        assert 'type_token_ratio' in result
        assert result['type_token_ratio'] == 0.75

    def test_extract_metrics_fallback(self):
        """Test extracting metrics with no specific mapping."""
        analyzer = DistributionAnalyzer()

        metrics = {'some_metric': 42.0, 'other': 'text'}
        result = analyzer._extract_metrics('unknown_dimension', metrics)

        # Should extract first numeric value
        assert len(result) > 0
        assert 'some_metric' in result or len(result) == 0

    def test_compute_statistics(self):
        """Test computing statistics from collected values."""
        analyzer = DistributionAnalyzer()

        metric_values = {'variance': [1.0, 2.0, 3.0, 4.0, 5.0]}
        stats = analyzer._compute_statistics(
            "burstiness",
            "human",
            metric_values
        )

        assert stats.dimension_name == "burstiness"
        assert stats.metric_name == "variance"
        assert stats.count == 5
        assert stats.mean == 3.0

    def test_analyze_dataset_mock(self):
        """Test analyzing dataset with mocked dimensions."""
        # Create mock dimension
        mock_dimension = Mock()
        mock_dimension.dimension_name = "test_dim"
        mock_dimension.tier = DimensionTier.CORE
        mock_dimension.weight = 5.0
        mock_dimension.analyze = Mock(return_value={'variance': 10.0})

        # Register with class registry
        DimensionRegistry.register(mock_dimension, allow_overwrite=True)

        analyzer = DistributionAnalyzer(registry=DimensionRegistry)

        # Create small test dataset
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="human_1",
            text="This is human-written text with natural variance.",
            label="human",
            word_count=7
        ))

        dataset.add_document(Document(
            id="ai_1",
            text="This is AI-generated text with consistent patterns.",
            label="ai",
            ai_model="gpt-4",
            word_count=7
        ))

        # Run analysis
        analysis = analyzer.analyze_dataset(dataset, dimension_names=["test_dim"])

        assert analysis.dataset_version == "v1.0"
        assert "test_dim" in analysis.dimensions
        assert "human" in analysis.dimensions["test_dim"]
        assert "ai" in analysis.dimensions["test_dim"]

        # Check that dimension was called
        assert mock_dimension.analyze.call_count == 2

    def test_generate_summary_report(self):
        """Test generating summary report."""
        analyzer = DistributionAnalyzer()

        # Create analysis with some data
        analysis = DistributionAnalysis(
            dataset_version="v1.0",
            timestamp="2025-11-24T10:00:00Z",
            metadata={'total_documents': 10, 'dimensions_analyzed': 2}
        )

        stats = DimensionStatistics(
            dimension_name="burstiness",
            metric_name="variance",
            values=[1.0, 2.0, 3.0, 4.0, 5.0]
        )
        stats.compute()
        analysis.add_dimension_stats("burstiness", "human", stats)

        # Generate report
        report = analyzer.generate_summary_report(analysis)

        assert "DISTRIBUTION ANALYSIS SUMMARY" in report
        assert "v1.0" in report
        assert "BURSTINESS" in report
        assert "Human Distribution" in report
        assert "Mean:" in report
        assert "Percentiles:" in report

    def test_generate_summary_report_save_to_file(self):
        """Test saving summary report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.txt"

            analyzer = DistributionAnalyzer()
            analysis = DistributionAnalysis(
                dataset_version="v1.0",
                timestamp="2025-11-24T10:00:00Z"
            )

            stats = DimensionStatistics(
                dimension_name="test",
                metric_name="test",
                values=[1, 2, 3]
            )
            stats.compute()
            analysis.add_dimension_stats("test", "human", stats)

            analyzer.generate_summary_report(analysis, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                content = f.read()
                assert "DISTRIBUTION ANALYSIS SUMMARY" in content

    def test_analyze_dataset_split_by_label(self):
        """Test that metrics are correctly split by label."""
        mock_dimension = Mock()
        mock_dimension.dimension_name = "test"
        mock_dimension.tier = DimensionTier.CORE
        mock_dimension.weight = 5.0
        # Return different values for human vs AI
        mock_dimension.analyze = Mock(side_effect=lambda text, lines: {
            'metric': 10.0 if 'human' in text else 5.0
        })

        DimensionRegistry.register(mock_dimension, allow_overwrite=True)

        analyzer = DistributionAnalyzer(registry=DimensionRegistry)

        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="h1",
            text="human text here",
            label="human",
            word_count=3
        ))

        dataset.add_document(Document(
            id="a1",
            text="ai text here",
            label="ai",
            ai_model="gpt-4",
            word_count=3
        ))

        analysis = analyzer.analyze_dataset(dataset, dimension_names=["test"])

        # Check that human and AI have separate distributions
        human_stats = analysis.get_dimension_stats("test", "human")
        ai_stats = analysis.get_dimension_stats("test", "ai")
        combined_stats = analysis.get_dimension_stats("test", "combined")

        assert human_stats is not None
        assert ai_stats is not None
        assert combined_stats is not None

        assert human_stats.count == 1
        assert ai_stats.count == 1
        assert combined_stats.count == 2
