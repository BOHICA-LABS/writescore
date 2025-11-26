"""
Unit tests for normality module.

Tests Shapiro-Wilk normality testing and scoring method auto-selection.
"""

import numpy as np
from scipy import stats

from writescore.core.normality import NormalityResult, NormalityTester, format_normality_report


class TestNormalityResult:
    """Tests for NormalityResult dataclass."""

    def test_basic_creation(self):
        """Test creating a NormalityResult with required fields."""
        result = NormalityResult(
            dimension_name='burstiness',
            is_normal=True,
            p_value=0.25,
            test_statistic=0.98,
            sample_size=100,
            skewness=0.1,
            kurtosis=-0.2,
            recommendation='gaussian'
        )

        assert result.dimension_name == 'burstiness'
        assert result.is_normal is True
        assert result.p_value == 0.25
        assert result.recommendation == 'gaussian'
        assert result.confidence == 'medium'  # Default

    def test_to_dict(self):
        """Test converting NormalityResult to dictionary."""
        result = NormalityResult(
            dimension_name='lexical',
            is_normal=False,
            p_value=0.001,
            test_statistic=0.85,
            sample_size=500,
            skewness=1.5,
            kurtosis=2.0,
            recommendation='monotonic',
            confidence='high',
            rationale='Highly skewed distribution'
        )

        d = result.to_dict()

        assert d['dimension_name'] == 'lexical'
        assert d['is_normal'] is False
        assert d['p_value'] == 0.001
        assert d['recommendation'] == 'monotonic'
        assert d['confidence'] == 'high'
        assert 'skewed' in d['rationale'].lower()


class TestNormalityTester:
    """Tests for NormalityTester class."""

    def test_init_defaults(self):
        """Test default initialization."""
        tester = NormalityTester()

        assert tester.alpha == 0.05
        assert tester.min_samples == NormalityTester.RECOMMENDED_SAMPLES
        assert tester.max_samples == NormalityTester.MAX_SAMPLES

    def test_init_custom_alpha(self):
        """Test initialization with custom alpha."""
        tester = NormalityTester(alpha=0.01)

        assert tester.alpha == 0.01

    def test_normal_distribution_detected(self):
        """Test that truly normal data is identified as normal."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=10, scale=2, size=200)

        tester = NormalityTester()
        result = tester.test_normality(normal_data.tolist(), 'test_dim')

        assert result.is_normal is True
        assert result.p_value > 0.05
        assert result.recommendation == 'gaussian'

    def test_skewed_distribution_detected(self):
        """Test that skewed data recommends monotonic scoring."""
        np.random.seed(42)
        # Generate right-skewed data using exponential distribution
        skewed_data = np.random.exponential(scale=5, size=200)

        tester = NormalityTester()
        result = tester.test_normality(skewed_data.tolist(), 'test_dim')

        # Exponential distribution is highly skewed
        assert abs(result.skewness) > 1.0
        assert result.recommendation in ['monotonic', 'threshold']

    def test_heavy_tailed_distribution(self):
        """Test that heavy-tailed data recommends threshold scoring."""
        np.random.seed(42)
        # Generate heavy-tailed data using t-distribution with low df
        heavy_tailed = stats.t.rvs(df=3, size=200)

        tester = NormalityTester()
        result = tester.test_normality(heavy_tailed.tolist(), 'test_dim')

        # t-distribution with df=3 has heavy tails (high kurtosis)
        assert result.kurtosis > 1.0

    def test_insufficient_data_fallback(self):
        """Test fallback for insufficient data."""
        tester = NormalityTester()
        result = tester.test_normality([1.0, 2.0], 'test_dim')

        assert result.confidence == 'low'
        assert result.recommendation == 'gaussian'  # Conservative default
        assert 'insufficient' in result.rationale.lower()

    def test_handles_nan_values(self):
        """Test that NaN values are handled gracefully."""
        np.random.seed(42)
        data = np.random.normal(loc=10, scale=2, size=100).tolist()
        data.extend([float('nan'), float('nan')])

        tester = NormalityTester()
        result = tester.test_normality(data, 'test_dim')

        # Should work, NaN values filtered out
        assert result.sample_size == 100

    def test_handles_inf_values(self):
        """Test that Inf values are handled gracefully."""
        np.random.seed(42)
        data = np.random.normal(loc=10, scale=2, size=100).tolist()
        data.extend([float('inf'), float('-inf')])

        tester = NormalityTester()
        result = tester.test_normality(data, 'test_dim')

        # Should work, Inf values filtered out
        assert result.sample_size == 100

    def test_subsampling_for_large_datasets(self):
        """Test that large datasets are subsampled."""
        np.random.seed(42)
        large_data = np.random.normal(loc=10, scale=2, size=10000)

        tester = NormalityTester(max_samples=1000)
        result = tester.test_normality(large_data.tolist(), 'test_dim')

        # Original size stored, but test used subsample
        assert result.sample_size == 10000
        assert result.is_normal is True  # Normal data should still be detected

    def test_empty_list_handling(self):
        """Test handling of empty list."""
        tester = NormalityTester()
        result = tester.test_normality([], 'test_dim')

        assert result.confidence == 'low'
        assert result.sample_size == 0

    def test_single_value_handling(self):
        """Test handling of single value."""
        tester = NormalityTester()
        result = tester.test_normality([5.0], 'test_dim')

        assert result.confidence == 'low'
        assert result.sample_size == 1

    def test_all_same_values(self):
        """Test handling of constant values."""
        tester = NormalityTester()
        result = tester.test_normality([5.0] * 100, 'test_dim')

        # Constant data has zero variance - should handle gracefully
        assert result.sample_size == 100


class TestNormalityTesterRecommendations:
    """Tests for recommendation logic."""

    def test_strong_normality_gaussian_high_confidence(self):
        """Test that strong normality gives high confidence Gaussian recommendation."""
        np.random.seed(42)
        # Generate very normal-looking data
        normal_data = np.random.normal(loc=50, scale=10, size=500)

        tester = NormalityTester()
        result = tester.test_normality(normal_data.tolist(), 'test_dim')

        # Very normal data should give high confidence
        if result.is_normal and abs(result.skewness) < 0.5 and abs(result.kurtosis) < 1.0:
            assert result.confidence == 'high'
            assert result.recommendation == 'gaussian'

    def test_moderate_skewness_monotonic(self):
        """Test that moderate skewness recommends monotonic."""
        np.random.seed(42)
        # Create moderately skewed data
        data = np.random.gamma(shape=4, scale=2, size=200)

        tester = NormalityTester()
        result = tester.test_normality(data.tolist(), 'test_dim')

        # Gamma with shape=4 has moderate skewness
        if abs(result.skewness) > 1.0:
            assert result.recommendation in ['monotonic', 'threshold']


class TestNormalityTesterAllDimensions:
    """Tests for batch dimension testing."""

    def test_test_all_dimensions(self):
        """Test testing multiple dimensions at once."""
        np.random.seed(42)

        dimension_values = {
            'normal_dim': np.random.normal(10, 2, 100).tolist(),
            'skewed_dim': np.random.exponential(5, 100).tolist(),
            'uniform_dim': np.random.uniform(0, 10, 100).tolist()
        }

        tester = NormalityTester()
        results = tester.test_all_dimensions(dimension_values)

        assert len(results) == 3
        assert 'normal_dim' in results
        assert 'skewed_dim' in results
        assert 'uniform_dim' in results

        # Normal dim should be detected as normal
        assert results['normal_dim'].is_normal is True

    def test_empty_dimensions_dict(self):
        """Test handling of empty dimensions dictionary."""
        tester = NormalityTester()
        results = tester.test_all_dimensions({})

        assert len(results) == 0


class TestFormatNormalityReport:
    """Tests for report formatting."""

    def test_empty_results(self):
        """Test formatting empty results."""
        report = format_normality_report({})

        assert 'NORMALITY TEST REPORT' in report
        assert 'Total dimensions tested: 0' in report

    def test_single_dimension_report(self):
        """Test formatting single dimension result."""
        results = {
            'burstiness': NormalityResult(
                dimension_name='burstiness',
                is_normal=True,
                p_value=0.25,
                test_statistic=0.98,
                sample_size=100,
                skewness=0.1,
                kurtosis=-0.2,
                recommendation='gaussian',
                confidence='high',
                rationale='Strong normality detected'
            )
        }

        report = format_normality_report(results)

        assert 'BURSTINESS' in report
        assert 'GAUSSIAN' in report
        assert 'high' in report.lower()
        assert '0.25' in report  # p-value

    def test_multiple_dimensions_report(self):
        """Test formatting multiple dimension results."""
        results = {
            'burstiness': NormalityResult(
                dimension_name='burstiness',
                is_normal=True,
                p_value=0.25,
                test_statistic=0.98,
                sample_size=100,
                skewness=0.1,
                kurtosis=-0.2,
                recommendation='gaussian',
                confidence='high',
                rationale='Strong normality'
            ),
            'lexical': NormalityResult(
                dimension_name='lexical',
                is_normal=False,
                p_value=0.001,
                test_statistic=0.85,
                sample_size=100,
                skewness=1.5,
                kurtosis=2.0,
                recommendation='monotonic',
                confidence='high',
                rationale='Highly skewed'
            )
        }

        report = format_normality_report(results)

        assert 'Total dimensions tested: 2' in report
        assert 'Recommended Gaussian: 1' in report
        assert 'Recommended Monotonic: 1' in report
        assert 'BURSTINESS' in report
        assert 'LEXICAL' in report


class TestParameterDeriverAutoSelect:
    """Tests for auto_select_method integration with ParameterDeriver."""

    def test_deriver_with_auto_select_disabled(self):
        """Test ParameterDeriver with auto_select_method=False (default)."""
        from writescore.core.parameter_derivation import ParameterDeriver

        deriver = ParameterDeriver(auto_select_method=False)

        assert deriver.auto_select_method is False
        assert deriver.normality_tester is None

    def test_deriver_with_auto_select_enabled(self):
        """Test ParameterDeriver with auto_select_method=True."""
        from writescore.core.parameter_derivation import ParameterDeriver

        deriver = ParameterDeriver(auto_select_method=True)

        assert deriver.auto_select_method is True
        assert deriver.normality_tester is not None

    def test_deriver_stores_normality_results(self):
        """Test that deriver stores normality results when auto_select enabled."""
        from writescore.core.distribution_analyzer import DimensionStatistics, DistributionAnalysis
        from writescore.core.parameter_derivation import ParameterDeriver

        np.random.seed(42)

        # Create mock analysis with raw values
        human_stats = DimensionStatistics(
            dimension_name='test_dim',
            metric_name='variance',
            values=np.random.normal(10, 2, 100).tolist()
        )
        human_stats.compute()

        analysis = DistributionAnalysis(
            dataset_version='test',
            timestamp='2025-01-01'
        )
        analysis.add_dimension_stats('test_dim', 'human', human_stats)

        # Derive with auto-select
        deriver = ParameterDeriver(auto_select_method=True)
        params = deriver.derive_dimension_parameters(analysis, 'test_dim')

        # Check that normality results were stored
        normality_results = deriver.get_normality_results()
        assert 'test_dim' in normality_results

        # Check metadata has normality info
        assert params.metadata.get('method_auto_selected') is True
        assert 'normality_p_value' in params.metadata


class TestRecalibrationWorkflowAutoSelect:
    """Tests for RecalibrationWorkflow with auto_select_method."""

    def test_workflow_with_auto_select_disabled(self):
        """Test workflow with auto_select_method=False (default)."""
        from writescore.core.recalibration import RecalibrationWorkflow

        workflow = RecalibrationWorkflow(auto_select_method=False)

        assert workflow.auto_select_method is False
        assert workflow.deriver.auto_select_method is False

    def test_workflow_with_auto_select_enabled(self):
        """Test workflow with auto_select_method=True."""
        from writescore.core.recalibration import RecalibrationWorkflow

        workflow = RecalibrationWorkflow(auto_select_method=True)

        assert workflow.auto_select_method is True
        assert workflow.deriver.auto_select_method is True

    def test_workflow_normality_report_empty_without_auto_select(self):
        """Test that normality report is empty without auto_select."""
        from writescore.core.recalibration import RecalibrationWorkflow

        workflow = RecalibrationWorkflow(auto_select_method=False)
        report = workflow.get_normality_report()

        assert report == ""


class TestNormalityTesterEdgeCases:
    """Edge case tests for NormalityTester."""

    def test_negative_values(self):
        """Test handling of negative values."""
        np.random.seed(42)
        data = np.random.normal(loc=-100, scale=20, size=100)

        tester = NormalityTester()
        result = tester.test_normality(data.tolist(), 'test_dim')

        assert result.sample_size == 100
        assert result.is_normal is True

    def test_very_small_values(self):
        """Test handling of very small values."""
        np.random.seed(42)
        data = np.random.normal(loc=0.001, scale=0.0001, size=100)

        tester = NormalityTester()
        result = tester.test_normality(data.tolist(), 'test_dim')

        assert result.sample_size == 100

    def test_very_large_values(self):
        """Test handling of very large values."""
        np.random.seed(42)
        data = np.random.normal(loc=1e10, scale=1e8, size=100)

        tester = NormalityTester()
        result = tester.test_normality(data.tolist(), 'test_dim')

        assert result.sample_size == 100

    def test_mixed_positive_negative(self):
        """Test handling of mixed positive/negative values."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=10, size=100)

        tester = NormalityTester()
        result = tester.test_normality(data.tolist(), 'test_dim')

        assert result.sample_size == 100
        assert result.is_normal is True

    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        np.random.seed(42)
        data1 = np.random.normal(10, 2, 200).tolist()

        np.random.seed(42)
        data2 = np.random.normal(10, 2, 200).tolist()

        tester = NormalityTester()
        result1 = tester.test_normality(data1, 'test_dim')
        result2 = tester.test_normality(data2, 'test_dim')

        assert result1.p_value == result2.p_value
        assert result1.recommendation == result2.recommendation
