"""
Tests for SemanticCoherenceDimension - semantic coherence analysis for AI detection.
Story 2.3 - Semantic coherence dimension with optional sentence-transformers dependency.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from writescore.dimensions.semantic_coherence import SemanticCoherenceDimension
from writescore.core.dimension_registry import DimensionRegistry


@pytest.fixture
def dimension():
    """Create SemanticCoherenceDimension instance with clean registry."""
    DimensionRegistry.clear()
    return SemanticCoherenceDimension()


@pytest.fixture
def text_high_coherence():
    """Text with high semantic coherence (consistent topic with smooth transitions)."""
    return """
    Neural networks are the foundation of modern deep learning systems. These artificial neural
    networks consist of interconnected layers of nodes that process information. Each layer learns
    increasingly complex features from the input data. The architecture enables powerful pattern
    recognition capabilities across many domains.

    Training these neural network models requires careful optimization of their parameters. The
    training process uses backpropagation to adjust weights based on prediction errors. Large
    datasets and computational resources are essential for effective model training. Modern GPUs
    accelerate the training process significantly through parallel computation.

    Once trained, neural networks can be applied to solve various real-world problems. Image
    classification systems use convolutional neural networks to recognize objects. Natural language
    processing models understand and generate human text. These applications demonstrate the
    versatility and power of neural network architectures in artificial intelligence.

    The continued development of neural network techniques drives progress in AI research.
    Researchers explore new architectures like transformers and attention mechanisms. These
    innovations improve model performance and enable new capabilities. The field continues to
    evolve rapidly with each breakthrough building on previous advances.
    """


@pytest.fixture
def text_low_coherence():
    """Text with low semantic coherence (topic drift and disconnected ideas)."""
    return """
    Machine learning algorithms process large amounts of data using statistical methods. The weather
    patterns in coastal regions vary significantly throughout the year. Quantum computing may
    revolutionize cryptography in the future. My grandmother's recipe for bread includes whole
    wheat flour and honey.

    Dogs have been domesticated for thousands of years as human companions. Stock market volatility
    affects retirement planning for millions of investors. Ocean currents play a crucial role in
    distributing heat around the planet. Basketball requires excellent hand-eye coordination and
    teamwork skills.

    Photosynthesis converts sunlight into chemical energy in plant cells. Renaissance art
    influenced European culture for centuries. Volcanic eruptions can impact global climate
    patterns temporarily. Mobile phone technology has transformed communication in developing
    nations.

    Ancient Egyptian pyramids demonstrate remarkable engineering capabilities. Jazz music
    originated in New Orleans during the early 20th century. Protein folding determines the
    function of biological molecules. Marathon running requires months of dedicated training
    and preparation.
    """


@pytest.fixture
def text_single_paragraph():
    """Text with only one paragraph (insufficient for analysis)."""
    return "This is a single paragraph. It has multiple sentences. But no paragraph breaks."


@pytest.fixture
def text_short():
    """Short text with minimal content."""
    return "Brief text.\n\nAnother line."


# ============================================================================
# DIMENSION METADATA TESTS
# ============================================================================


class TestDimensionMetadata:
    """Tests for dimension metadata and registration."""

    def test_dimension_name(self, dimension):
        """Test dimension name is 'semantic_coherence'."""
        assert dimension.dimension_name == "semantic_coherence"

    def test_dimension_weight(self, dimension):
        """Test dimension weight is 4.6% (rebalanced to 100% total)."""
        assert dimension.weight == 4.6

    def test_dimension_tier(self, dimension):
        """Test dimension tier is SUPPORTING."""
        assert dimension.tier == "SUPPORTING"

    def test_dimension_description(self, dimension):
        """Test dimension has meaningful description."""
        desc = dimension.description
        assert isinstance(desc, str)
        assert len(desc) > 20
        assert any(term in desc.lower() for term in ["semantic", "coherence", "embedding"])

    def test_dimension_registers_on_init(self):
        """Test dimension self-registers with registry on initialization."""
        DimensionRegistry.clear()
        dim = SemanticCoherenceDimension()

        registered = DimensionRegistry.get("semantic_coherence")
        assert registered is dim


# ============================================================================
# OPTIONAL DEPENDENCY TESTS
# ============================================================================


class TestOptionalDependency:
    """Tests for optional dependency handling."""

    def test_check_availability_returns_bool(self):
        """Test check_availability returns boolean."""
        # Clear cached state
        SemanticCoherenceDimension._model_available = None
        result = SemanticCoherenceDimension.check_availability()
        assert isinstance(result, bool)

    def test_check_availability_caches_result(self):
        """Test availability check is cached."""
        # Clear cache
        SemanticCoherenceDimension._model_available = None

        # First call
        first = SemanticCoherenceDimension.check_availability()
        # Second call should use cache
        second = SemanticCoherenceDimension.check_availability()

        assert first == second
        assert SemanticCoherenceDimension._model_available is not None

    def test_load_model_returns_none_when_unavailable(self):
        """Test load_model returns None when sentence-transformers unavailable."""
        with patch.object(
            SemanticCoherenceDimension,
            'check_availability',
            return_value=False
        ):
            # Clear LRU cache
            SemanticCoherenceDimension.load_model.cache_clear()
            model = SemanticCoherenceDimension.load_model()
            assert model is None

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_load_model_returns_model_when_available(self):
        """Test load_model returns model instance when available."""
        # Clear LRU cache
        SemanticCoherenceDimension.load_model.cache_clear()
        model = SemanticCoherenceDimension.load_model()
        assert model is not None

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_load_model_is_cached(self):
        """Test model loading uses LRU cache."""
        # Clear cache
        SemanticCoherenceDimension.load_model.cache_clear()

        # Load model twice
        model1 = SemanticCoherenceDimension.load_model()
        model2 = SemanticCoherenceDimension.load_model()

        # Should return same instance (cached)
        assert model1 is model2


# ============================================================================
# TEXT SPLITTING UTILITIES TESTS
# ============================================================================


class TestTextSplitting:
    """Tests for text splitting utilities."""

    def test_split_paragraphs(self, dimension):
        """Test paragraph splitting on double newlines."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        paragraphs = dimension._split_paragraphs(text)

        assert len(paragraphs) == 3
        assert paragraphs[0] == "Para 1."
        assert paragraphs[1] == "Para 2."
        assert paragraphs[2] == "Para 3."

    def test_split_paragraphs_filters_empty(self, dimension):
        """Test paragraph splitting filters empty paragraphs."""
        text = "Para 1.\n\n\n\nPara 2.\n\n"
        paragraphs = dimension._split_paragraphs(text)

        assert len(paragraphs) == 2
        assert all(p for p in paragraphs)  # No empty strings

    def test_split_sentences(self, dimension):
        """Test sentence splitting."""
        text = "Sentence one. Sentence two! Sentence three?"
        sentences = dimension._split_sentences(text)

        assert len(sentences) == 3
        assert "Sentence one" in sentences[0]
        assert "Sentence two" in sentences[1]
        assert "Sentence three" in sentences[2]

    def test_sample_sentences_returns_all_when_under_limit(self, dimension):
        """Test sentence sampling returns all sentences when under limit."""
        sentences = ["S1", "S2", "S3"]
        sampled = dimension._sample_sentences(sentences, max_count=10)

        assert len(sampled) == 3
        assert sampled == sentences

    def test_sample_sentences_reduces_when_over_limit(self, dimension):
        """Test sentence sampling reduces count when over limit."""
        sentences = [f"S{i}" for i in range(100)]
        sampled = dimension._sample_sentences(sentences, max_count=20)

        assert len(sampled) == 20
        assert len(sampled) < len(sentences)


# ============================================================================
# FALLBACK ANALYSIS TESTS
# ============================================================================


class TestFallbackAnalysis:
    """Tests for fallback basic coherence analysis."""

    def test_fallback_returns_basic_method(self, dimension):
        """Test fallback analysis returns method='basic'."""
        text = "Para 1.\n\nPara 2."
        result = dimension._analyze_basic_coherence(text)

        assert result['method'] == 'basic'
        assert result['available'] == False

    def test_fallback_handles_insufficient_paragraphs(self, dimension):
        """Test fallback handles single paragraph gracefully."""
        text = "Single paragraph only."
        result = dimension._analyze_basic_coherence(text)

        assert result['method'] == 'basic'
        assert 'lexical_overlap' in result
        assert result['paragraph_count'] == 1

    def test_fallback_calculates_word_overlap(self, dimension):
        """Test fallback calculates lexical overlap between paragraphs."""
        text = "Dogs and cats are pets.\n\nCats and birds are animals."
        result = dimension._analyze_basic_coherence(text)

        assert 'lexical_overlap' in result
        assert isinstance(result['lexical_overlap'], float)
        assert 0.0 <= result['lexical_overlap'] <= 1.0

    def test_analyze_uses_fallback_when_model_unavailable(self, dimension):
        """Test analyze() uses fallback when model unavailable."""
        with patch.object(
            SemanticCoherenceDimension,
            'load_model',
            return_value=None
        ):
            text = "Para 1.\n\nPara 2."
            result = dimension.analyze(text)

            assert result['method'] == 'basic'
            assert result['available'] == False


# ============================================================================
# SEMANTIC ANALYSIS TESTS (with sentence-transformers)
# ============================================================================


class TestSemanticAnalysis:
    """Tests for full semantic coherence analysis."""

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_returns_semantic_method_when_available(self, dimension, text_high_coherence):
        """Test analyze returns method='semantic' when model available."""
        result = dimension.analyze(text_high_coherence)

        assert result['method'] == 'semantic'
        assert result['available'] == True

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_includes_all_metrics(self, dimension, text_high_coherence):
        """Test analyze includes all 4 coherence metrics."""
        result = dimension.analyze(text_high_coherence)

        assert 'metrics' in result
        metrics = result['metrics']
        assert 'paragraph_cohesion' in metrics
        assert 'topic_consistency' in metrics
        assert 'discourse_flow' in metrics
        assert 'conceptual_depth' in metrics

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_metrics_in_valid_range(self, dimension, text_high_coherence):
        """Test all metrics return values in [0.0, 1.0] range."""
        result = dimension.analyze(text_high_coherence)
        metrics = result['metrics']

        for metric_name, metric_value in metrics.items():
            assert isinstance(metric_value, float), f"{metric_name} is not float"
            assert 0.0 <= metric_value <= 1.0, f"{metric_name} out of range: {metric_value}"

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_high_coherence_scores_better(self, dimension, text_high_coherence, text_low_coherence):
        """Test high coherence text scores better than low coherence text."""
        result_high = dimension.analyze(text_high_coherence)
        result_low = dimension.analyze(text_low_coherence)

        score_high = dimension.calculate_score(result_high)
        score_low = dimension.calculate_score(result_low)

        # High coherence should score better (higher score = more human-like)
        assert score_high > score_low

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_handles_insufficient_paragraphs(self, dimension, text_single_paragraph):
        """Test analyze handles single paragraph gracefully."""
        result = dimension.analyze(text_single_paragraph)

        # Should return error or basic analysis
        assert 'error' in result or result['method'] == 'basic'

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_analyze_tracks_sampling(self, dimension):
        """Test analyze tracks if sentence sampling was used."""
        # Create text with many sentences (need >500 total sentences)
        # Create multiple paragraphs each with many sentences
        paragraphs = []
        for p in range(10):  # 10 paragraphs
            sentences = [f"This is sentence {i} in paragraph {p}." for i in range(60)]  # 60 sentences each
            paragraphs.append(" ".join(sentences))

        long_text = "\n\n".join(paragraphs)  # 600 sentences total

        result = dimension.analyze(long_text)

        assert 'sampled' in result
        # Should be True since >500 sentences
        assert result['sampled'] == True


# ============================================================================
# EMBEDDING GENERATION TESTS
# ============================================================================


class TestEmbeddingGeneration:
    """Tests for embedding generation."""

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_generate_embeddings_returns_numpy_array(self, dimension):
        """Test embedding generation returns numpy array."""
        texts = ["Text one", "Text two", "Text three"]
        embeddings = dimension._generate_embeddings(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        # all-MiniLM-L6-v2 uses 384 dimensions
        assert embeddings.shape[1] == 384

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_generate_embeddings_handles_batch_size(self, dimension):
        """Test embedding generation respects batch size."""
        texts = ["Text one", "Text two"]
        embeddings = dimension._generate_embeddings(texts, batch_size=1)

        assert embeddings is not None
        assert embeddings.shape[0] == 2

    def test_generate_embeddings_returns_none_when_unavailable(self, dimension):
        """Test embedding generation returns None when model unavailable."""
        with patch.object(
            SemanticCoherenceDimension,
            'load_model',
            return_value=None
        ):
            texts = ["Text one", "Text two"]
            embeddings = dimension._generate_embeddings(texts)

            assert embeddings is None


# ============================================================================
# COHERENCE METRICS TESTS
# ============================================================================


class TestCoherenceMetrics:
    """Tests for individual coherence metric calculations."""

    def test_paragraph_cohesion_metric(self, dimension):
        """Test paragraph cohesion calculation."""
        # Create mock embeddings (3 sentences in 1 paragraph)
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0]
        ])
        sentences_per_paragraph = [3]

        cohesion = dimension._calculate_paragraph_cohesion(embeddings, sentences_per_paragraph)

        assert isinstance(cohesion, float)
        assert 0.0 <= cohesion <= 1.0

    def test_topic_consistency_metric(self, dimension):
        """Test topic consistency calculation."""
        # Create mock paragraph embeddings
        paragraph_embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.9, 0.1, 0.0]),
            np.array([0.8, 0.2, 0.0])
        ]

        consistency = dimension._calculate_topic_consistency(paragraph_embeddings)

        assert isinstance(consistency, float)
        assert 0.0 <= consistency <= 1.0

    def test_discourse_flow_metric(self, dimension):
        """Test discourse flow calculation."""
        # Create mock paragraph embeddings
        paragraph_embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.7, 0.3, 0.0]),  # In ideal range
            np.array([0.6, 0.4, 0.0])
        ]

        flow = dimension._calculate_discourse_flow(paragraph_embeddings)

        assert isinstance(flow, float)
        assert 0.0 <= flow <= 1.0

    def test_conceptual_depth_metric(self, dimension):
        """Test conceptual depth calculation."""
        # Create mock paragraph and document embeddings
        paragraph_embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.9, 0.1, 0.0]),
            np.array([0.8, 0.2, 0.0])
        ]
        document_embedding = np.array([0.9, 0.1, 0.0])

        depth = dimension._calculate_conceptual_depth(paragraph_embeddings, document_embedding)

        assert isinstance(depth, float)
        assert 0.0 <= depth <= 1.0

    def test_metrics_handle_edge_cases(self, dimension):
        """Test metrics handle edge cases gracefully."""
        # Single paragraph
        single_para = [np.array([1.0, 0.0, 0.0])]
        consistency = dimension._calculate_topic_consistency(single_para)
        assert consistency == 0.0

        # Empty embeddings
        depth = dimension._calculate_conceptual_depth([], np.array([1.0, 0.0, 0.0]))
        assert depth == 0.0


# ============================================================================
# SCORING TESTS
# ============================================================================


class TestScoring:
    """Tests for scoring logic."""

    def test_calculate_score_returns_float(self, dimension):
        """Test calculate_score returns float in 0-100 range."""
        metrics = {
            'method': 'semantic',
            'available': True,
            'metrics': {
                'paragraph_cohesion': 0.75,
                'topic_consistency': 0.70,
                'discourse_flow': 0.65,
                'conceptual_depth': 0.68
            }
        }

        score = dimension.calculate_score(metrics)

        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_calculate_score_fallback_returns_neutral(self, dimension):
        """Test calculate_score returns 50.0 for fallback mode."""
        metrics = {
            'method': 'basic',
            'available': False,
            'lexical_overlap': 0.3
        }

        score = dimension.calculate_score(metrics)

        assert score == 50.0

    def test_calculate_score_handles_errors(self, dimension):
        """Test calculate_score handles error conditions."""
        metrics = {
            'method': 'semantic',
            'available': True,
            'error': 'Insufficient paragraphs'
        }

        score = dimension.calculate_score(metrics)

        assert score == 50.0

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_calculate_score_high_coherence_scores_high(self, dimension, text_high_coherence, text_low_coherence):
        """Test high coherence text scores better than low coherence."""
        result_high = dimension.analyze(text_high_coherence)
        score_high = dimension.calculate_score(result_high)

        result_low = dimension.analyze(text_low_coherence)
        score_low = dimension.calculate_score(result_low)

        # High coherence should score higher than low coherence
        assert score_high > score_low
        # Score should be reasonable (not neutral fallback)
        assert score_high > 0.0 and score_high < 100.0

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_calculate_score_low_coherence_scores_low(self, dimension, text_low_coherence):
        """Test low coherence text scores lower."""
        result = dimension.analyze(text_low_coherence)
        score = dimension.calculate_score(result)

        # Low coherence should score POOR or ACCEPTABLE
        assert score <= 75.0


# ============================================================================
# DOMAIN-AWARE SCORING TESTS (AC5)
# ============================================================================


class TestDomainAwareScoring:
    """Tests for domain-aware scoring functionality (AC5)."""

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_technical_content_uses_lenient_thresholds(self, dimension):
        """Test technical content gets more lenient thresholds."""
        # Create technical text fixture
        text_technical = """
        Machine learning models utilize neural networks for pattern recognition.
        The convolutional layers process feature extraction hierarchically.
        Backpropagation algorithms optimize gradient descent procedures.

        TensorFlow and PyTorch frameworks implement automatic differentiation.
        CUDA acceleration enables GPU-based parallel computation.
        Model architectures incorporate attention mechanisms for sequence processing.
        """

        # Analyze and score with technical domain
        result = dimension.analyze(text_technical)
        result['content_type'] = 'technical'  # Set domain
        score_technical = dimension.calculate_score(result)

        # Analyze and score with general domain (same metrics)
        result_general = result.copy()
        result_general['content_type'] = 'general'
        score_general = dimension.calculate_score(result_general)

        # Technical should score higher (more lenient thresholds)
        assert score_technical >= score_general, \
            f"Technical domain ({score_technical:.1f}) should score >= general ({score_general:.1f})"

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_creative_content_uses_moderate_thresholds(self, dimension):
        """Test creative content gets moderate thresholds."""
        # Create creative text fixture
        text_creative = """
        The autumn wind whispered through golden leaves. Sarah remembered
        her grandmother's stories about the old oak tree. Time had a way
        of blurring memories into soft watercolors.

        Downtown, the coffee shop buzzed with morning energy. Each customer
        carried their own invisible burdens and dreams. Steam rose from
        ceramic mugs like small prayers.
        """

        # Analyze with creative domain
        result = dimension.analyze(text_creative)
        result['content_type'] = 'creative'
        score_creative = dimension.calculate_score(result)

        # Should return valid score
        assert 0.0 <= score_creative <= 100.0
        assert score_creative > 0.0  # Not a fallback score

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_academic_content_uses_standard_thresholds(self, dimension):
        """Test academic content gets standard thresholds."""
        # Create academic text fixture
        text_academic = """
        Previous research has demonstrated the efficacy of cognitive behavioral
        therapy for anxiety disorders. Smith et al. (2020) found significant
        improvements in patient outcomes across multiple clinical trials.

        The methodology employed a randomized controlled design with 200
        participants. Results indicated a 65% reduction in symptom severity
        compared to control groups. These findings support the hypothesis that
        structured interventions yield measurable therapeutic benefits.
        """

        # Analyze with academic domain
        result = dimension.analyze(text_academic)
        result['content_type'] = 'academic'
        score_academic = dimension.calculate_score(result)

        # Should return valid score with standard thresholds
        assert 0.0 <= score_academic <= 100.0

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_unknown_domain_defaults_to_general(self, dimension):
        """Test unknown content types default to general thresholds."""
        text = "Test paragraph one.\n\nTest paragraph two."
        result = dimension.analyze(text)

        # Set unknown content type
        result['content_type'] = 'unknown_type'
        score_unknown = dimension.calculate_score(result)

        # Set general content type
        result['content_type'] = 'general'
        score_general = dimension.calculate_score(result)

        # Should use same thresholds (both general)
        assert score_unknown == score_general

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_missing_content_type_defaults_to_general(self, dimension):
        """Test missing content_type key defaults to general thresholds."""
        text = "Test paragraph one.\n\nTest paragraph two."
        result = dimension.analyze(text)

        # Remove content_type if present
        if 'content_type' in result:
            del result['content_type']

        score = dimension.calculate_score(result)

        # Should return valid score (using general thresholds)
        assert 0.0 <= score <= 100.0

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_domain_thresholds_affect_scoring(self, dimension):
        """Test domain-specific thresholds produce different scores."""
        # Create text with moderate coherence
        text = """
        Modern software development relies on agile methodologies. Teams
        collaborate using version control systems. Code review processes
        ensure quality standards.

        Continuous integration pipelines automate testing workflows. Deployment
        strategies minimize downtime during updates. Monitoring tools track
        system performance metrics.
        """

        result = dimension.analyze(text)

        # Score with each domain
        scores = {}
        for domain in ['general', 'technical', 'creative', 'academic']:
            result['content_type'] = domain
            scores[domain] = dimension.calculate_score(result)

        # Technical should be most lenient (highest score for same metrics)
        assert scores['technical'] >= scores['general'], "Technical should be >= general"
        assert scores['technical'] >= scores['creative'], "Technical should be >= creative"

        # All scores should be valid
        for domain, score in scores.items():
            assert 0.0 <= score <= 100.0, f"{domain} score out of range"

    def test_domain_aware_scoring_with_fallback_mode(self, dimension):
        """Test domain-aware scoring works in fallback mode."""
        # Fallback mode should ignore content_type
        text = "Short text."
        result = dimension._analyze_basic_coherence(text)
        result['content_type'] = 'technical'

        score = dimension.calculate_score(result)

        # Should return neutral fallback score regardless of domain
        assert score == 50.0

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_all_domain_thresholds_defined(self, dimension):
        """Test all expected domains have complete threshold definitions."""
        expected_domains = ['general', 'technical', 'creative', 'academic']
        expected_metrics = ['paragraph_cohesion', 'topic_consistency',
                          'discourse_flow', 'conceptual_depth']
        expected_levels = ['excellent', 'good', 'acceptable']

        for domain in expected_domains:
            assert domain in dimension.THRESHOLDS, f"Missing domain: {domain}"

            for metric in expected_metrics:
                assert metric in dimension.THRESHOLDS[domain], \
                    f"Missing metric {metric} in {domain}"

                for level in expected_levels:
                    assert level in dimension.THRESHOLDS[domain][metric], \
                        f"Missing level {level} for {metric} in {domain}"


# ============================================================================
# RECOMMENDATIONS TESTS
# ============================================================================


class TestRecommendations:
    """Tests for recommendation generation."""

    def test_get_recommendations_returns_list(self, dimension):
        """Test get_recommendations returns list of strings."""
        metrics = {
            'method': 'semantic',
            'available': True,
            'metrics': {
                'paragraph_cohesion': 0.50,
                'topic_consistency': 0.50,
                'discourse_flow': 0.50,
                'conceptual_depth': 0.50
            }
        }

        recommendations = dimension.get_recommendations(60.0, metrics)

        assert isinstance(recommendations, list)
        assert all(isinstance(r, str) for r in recommendations)

    def test_get_recommendations_fallback_suggests_installation(self, dimension):
        """Test fallback mode recommends installing sentence-transformers."""
        metrics = {
            'method': 'basic',
            'available': False
        }

        recommendations = dimension.get_recommendations(50.0, metrics)

        assert len(recommendations) > 0
        assert any('sentence-transformers' in r.lower() for r in recommendations)

    def test_get_recommendations_provides_metric_specific_advice(self, dimension):
        """Test recommendations address specific low metrics."""
        metrics = {
            'method': 'semantic',
            'available': True,
            'metrics': {
                'paragraph_cohesion': 0.40,  # Low
                'topic_consistency': 0.80,    # Good
                'discourse_flow': 0.80,       # Good
                'conceptual_depth': 0.80      # Good
            }
        }

        recommendations = dimension.get_recommendations(70.0, metrics)

        # Should mention paragraph cohesion
        assert any('cohesion' in r.lower() for r in recommendations)

    def test_get_recommendations_positive_for_good_scores(self, dimension):
        """Test recommendations are positive for good scores."""
        metrics = {
            'method': 'semantic',
            'available': True,
            'metrics': {
                'paragraph_cohesion': 0.85,
                'topic_consistency': 0.82,
                'discourse_flow': 0.78,
                'conceptual_depth': 0.80
            }
        }

        recommendations = dimension.get_recommendations(90.0, metrics)

        # Should have positive message
        assert len(recommendations) > 0
        assert any('strong' in r.lower() for r in recommendations)


# ============================================================================
# TIER DEFINITIONS TESTS
# ============================================================================


class TestTierDefinitions:
    """Tests for score tier definitions."""

    def test_get_tiers_returns_dict(self, dimension):
        """Test get_tiers returns dict with tier ranges."""
        tiers = dimension.get_tiers()

        assert isinstance(tiers, dict)
        assert 'excellent' in tiers
        assert 'good' in tiers
        assert 'acceptable' in tiers
        assert 'poor' in tiers

    def test_get_tiers_ranges_are_valid(self, dimension):
        """Test tier ranges are valid tuples."""
        tiers = dimension.get_tiers()

        for tier_name, tier_range in tiers.items():
            assert isinstance(tier_range, tuple)
            assert len(tier_range) == 2
            min_score, max_score = tier_range
            assert min_score < max_score
            assert 0.0 <= min_score <= 100.0
            assert 0.0 <= max_score <= 100.0

    def test_get_tiers_covers_full_range(self, dimension):
        """Test tier ranges cover 0-100 range."""
        tiers = dimension.get_tiers()

        # Find min and max across all tiers
        all_mins = [t[0] for t in tiers.values()]
        all_maxs = [t[1] for t in tiers.values()]

        assert min(all_mins) == 0.0
        assert max(all_maxs) == 100.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_full_workflow_fallback_mode(self, dimension, text_high_coherence):
        """Test full workflow in fallback mode."""
        with patch.object(
            SemanticCoherenceDimension,
            'load_model',
            return_value=None
        ):
            # Analyze
            result = dimension.analyze(text_high_coherence)
            assert result['method'] == 'basic'

            # Score
            score = dimension.calculate_score(result)
            assert score == 50.0  # Neutral in fallback

            # Recommendations
            recommendations = dimension.get_recommendations(score, result)
            assert len(recommendations) > 0

            # Tiers
            tiers = dimension.get_tiers()
            assert 'acceptable' in tiers

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_full_workflow_semantic_mode(self, dimension, text_high_coherence):
        """Test full workflow with semantic analysis."""
        # Analyze
        result = dimension.analyze(text_high_coherence)
        assert result['method'] == 'semantic'
        assert 'metrics' in result

        # Score
        score = dimension.calculate_score(result)
        assert 0.0 <= score <= 100.0

        # Recommendations
        recommendations = dimension.get_recommendations(score, result)
        assert isinstance(recommendations, list)

        # Tiers
        tiers = dimension.get_tiers()
        assert len(tiers) == 4

    def test_dimension_works_in_registry(self):
        """Test dimension integrates with DimensionRegistry."""
        DimensionRegistry.clear()
        dim = SemanticCoherenceDimension()

        # Check registration
        assert DimensionRegistry.get("semantic_coherence") is dim

        # Check in get_all (returns list of dimensions)
        all_dims = DimensionRegistry.get_all()
        assert dim in all_dims
        assert any(d.dimension_name == "semantic_coherence" for d in all_dims)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Tests for performance requirements validation (AC4)."""

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_processing_time_10k_words(self, dimension):
        """Test processing time meets <2s per 10k words target."""
        import time

        # Create ~10k word document (average 5 chars per word = 50k chars)
        # Use realistic paragraph structure
        paragraphs = []
        for p in range(20):  # 20 paragraphs
            sentences = []
            for s in range(25):  # 25 sentences per paragraph = 500 total sentences
                # Each sentence ~10 words
                sentences.append(
                    f"This is sentence {s} in paragraph {p} discussing semantic coherence patterns "
                    f"and topic consistency."
                )
            paragraphs.append(" ".join(sentences))

        text = "\n\n".join(paragraphs)
        word_count = len(text.split())

        # Measure processing time
        start = time.time()
        result = dimension.analyze(text)
        elapsed = time.time() - start

        # Validate result
        assert result['method'] == 'semantic'
        assert 'metrics' in result

        # Validate performance target (<2s per 10k words)
        # Scale target based on actual word count
        target_time = (word_count / 10000) * 2.0
        assert elapsed < target_time, f"Processing took {elapsed:.2f}s, expected <{target_time:.2f}s for {word_count} words"

        # Log performance for monitoring
        print(f"\nPerformance: {word_count} words processed in {elapsed:.2f}s ({word_count/elapsed:.0f} words/sec)")

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_memory_usage_inference(self, dimension):
        """Test memory usage during model load and inference."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not installed - cannot measure memory")

        process = psutil.Process(os.getpid())

        # Measure baseline memory
        baseline_mb = process.memory_info().rss / 1024 / 1024

        # Load model (if not already loaded)
        model = dimension.load_model()
        assert model is not None

        # Measure memory after model load
        after_load_mb = process.memory_info().rss / 1024 / 1024
        load_increase_mb = after_load_mb - baseline_mb

        # Run inference
        text = "Test paragraph one with semantic content.\n\nTest paragraph two with related content."
        result = dimension.analyze(text)

        # Measure memory after inference
        after_inference_mb = process.memory_info().rss / 1024 / 1024
        total_increase_mb = after_inference_mb - baseline_mb

        # Validate memory target (<5GB = 5120 MB increase)
        # Note: This is process increase, not absolute usage
        assert total_increase_mb < 5120, f"Memory increased by {total_increase_mb:.0f}MB, expected <5120MB"

        # Log memory usage for monitoring
        print(f"\nMemory: Baseline={baseline_mb:.0f}MB, After load={after_load_mb:.0f}MB (+{load_increase_mb:.0f}MB), "
              f"After inference={after_inference_mb:.0f}MB (+{total_increase_mb:.0f}MB total)")

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_sampling_optimization_speedup(self, dimension):
        """Test sentence sampling reduces processing time."""
        import time

        # Create long document that triggers sampling (>500 sentences)
        paragraphs = []
        for p in range(15):  # 15 paragraphs
            sentences = [f"Sentence {s} in paragraph {p}." for s in range(50)]  # 50 each = 750 total
            paragraphs.append(" ".join(sentences))

        long_text = "\n\n".join(paragraphs)

        # Measure time with sampling (should trigger at >500 sentences)
        start = time.time()
        result = dimension.analyze(long_text)
        sampled_time = time.time() - start

        # Verify sampling was used
        assert result.get('sampled', False) == True, "Sampling should be triggered for >500 sentences"

        # Create shorter document that doesn't trigger sampling
        short_paragraphs = []
        for p in range(5):  # 5 paragraphs
            sentences = [f"Sentence {s} in paragraph {p}." for s in range(20)]  # 20 each = 100 total
            short_paragraphs.append(" ".join(sentences))

        short_text = "\n\n".join(short_paragraphs)

        # Measure time without sampling
        start = time.time()
        short_result = dimension.analyze(short_text)
        unsampled_time = time.time() - start

        # Verify no sampling
        assert short_result.get('sampled', True) == False, "Sampling should not trigger for <500 sentences"

        # Sampling should result in faster processing per sentence
        # (Not necessarily faster absolute time since long doc has more sentences,
        # but should be comparable despite having 7.5x more sentences)
        long_sentence_count = result['sentence_count']
        short_sentence_count = short_result['sentence_count']

        time_per_sentence_sampled = sampled_time / long_sentence_count
        time_per_sentence_unsampled = unsampled_time / short_sentence_count

        # With sampling, time per sentence should be lower (more efficient)
        # Allow some variance due to overhead
        assert time_per_sentence_sampled < time_per_sentence_unsampled * 2, \
            f"Sampling efficiency: {time_per_sentence_sampled:.6f}s/sentence vs {time_per_sentence_unsampled:.6f}s/sentence"

        print(f"\nSampling: Long doc ({long_sentence_count} sentences) = {sampled_time:.2f}s, "
              f"Short doc ({short_sentence_count} sentences) = {unsampled_time:.2f}s")

    @pytest.mark.skipif(
        not SemanticCoherenceDimension.check_availability(),
        reason="sentence-transformers not installed"
    )
    def test_performance_targets_met(self, dimension):
        """Test all Story 2.3.0 performance targets are met."""
        import time

        # Target 1: Processing time <2s per 10k words
        # Create exactly 10k word document
        words_per_sentence = 10
        sentences_per_paragraph = 25
        words_per_paragraph = words_per_sentence * sentences_per_paragraph  # 250

        paragraphs_needed = 10000 // words_per_paragraph  # 40 paragraphs

        paragraphs = []
        for p in range(paragraphs_needed):
            sentences = []
            for s in range(sentences_per_paragraph):
                sentences.append(
                    f"Sentence {s} paragraph {p} semantic coherence topic consistency discourse flow."
                )
            paragraphs.append(" ".join(sentences))

        text = "\n\n".join(paragraphs)
        actual_words = len(text.split())

        # Measure processing
        start = time.time()
        result = dimension.analyze(text)
        elapsed = time.time() - start

        # Validate targets
        assert result['method'] == 'semantic', "Should use semantic analysis"
        assert elapsed < 2.0, f"Processing {actual_words} words took {elapsed:.2f}s, expected <2.0s"

        # Target 2: Model size ~90MB, RAM ~2-4GB (informational - can't easily test)
        # Target 3: Batch size 32 (verify in code)
        assert dimension.BATCH_SIZE == 32, "Batch size should be 32"

        # Target 4: Sampling at >500 sentences
        assert dimension.MAX_SENTENCES_BEFORE_SAMPLING == 500, "Sampling threshold should be 500"

        print(f"\nAll performance targets met: {actual_words} words in {elapsed:.2f}s")


class TestMonotonicScoringWithDomainAwareness:
    """Tests for monotonic scoring with domain-aware thresholds (Story 2.4.1, Group D)."""

    def test_calculate_score_general_domain_low_coherence(self, dimension):
        """Test general domain with low coherence."""
        metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'general',
            'metrics': {
                'paragraph_cohesion': 0.50,
                'topic_consistency': 0.50,
                'discourse_flow': 0.45,
                'conceptual_depth': 0.45
            }
        }
        score = dimension.calculate_score(metrics)

        # Low coherence (avg ~0.475) should score low
        assert 0 <= score <= 50, f"Low coherence scored {score}, expected ≤50"

    def test_calculate_score_general_domain_high_coherence(self, dimension):
        """Test general domain with high coherence."""
        metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'general',
            'metrics': {
                'paragraph_cohesion': 0.80,
                'topic_consistency': 0.75,
                'discourse_flow': 0.78,
                'conceptual_depth': 0.72
            }
        }
        score = dimension.calculate_score(metrics)

        # High coherence (avg ~0.76) should score high
        assert 75 <= score <= 100, f"High coherence scored {score}, expected ≥75"

    def test_calculate_score_technical_domain_adjustments(self, dimension):
        """Test that technical domain uses lower thresholds."""
        # Same coherence value in both domains
        coherence_value = 0.60

        general_metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'general',
            'metrics': {
                'paragraph_cohesion': coherence_value,
                'topic_consistency': coherence_value,
                'discourse_flow': coherence_value,
                'conceptual_depth': coherence_value
            }
        }
        general_score = dimension.calculate_score(general_metrics)

        technical_metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'technical',
            'metrics': {
                'paragraph_cohesion': coherence_value,
                'topic_consistency': coherence_value,
                'discourse_flow': coherence_value,
                'conceptual_depth': coherence_value
            }
        }
        technical_score = dimension.calculate_score(technical_metrics)

        # Technical should score higher with same coherence (lower thresholds)
        assert technical_score >= general_score, \
            f"Technical {technical_score} should score ≥ general {general_score}"

    def test_calculate_score_monotonic_increasing(self, dimension):
        """Test that score increases with coherence."""
        coherence_levels = [0.40, 0.55, 0.65, 0.75, 0.85]
        scores = []

        for coherence in coherence_levels:
            metrics = {
                'available': True,
                'method': 'semantic',
                'content_type': 'general',
                'metrics': {
                    'paragraph_cohesion': coherence,
                    'topic_consistency': coherence,
                    'discourse_flow': coherence,
                    'conceptual_depth': coherence
                }
            }
            scores.append(dimension.calculate_score(metrics))

        # Scores should increase monotonically
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], \
                f"Score decreased: {scores[i]} -> {scores[i + 1]} at coherence {coherence_levels[i]} -> {coherence_levels[i+1]}"

    def test_calculate_score_unavailable_fallback(self, dimension):
        """Test fallback to neutral score when unavailable."""
        metrics = {'available': False}
        score = dimension.calculate_score(metrics)

        assert score == 50.0, f"Unavailable should return 50.0, got {score}"

    def test_calculate_score_basic_fallback(self, dimension):
        """Test fallback to neutral score with basic method."""
        metrics = {'method': 'basic'}
        score = dimension.calculate_score(metrics)

        assert score == 50.0, f"Basic method should return 50.0, got {score}"

    def test_calculate_score_validates_range(self, dimension):
        """Test that all scores are in valid 0-100 range."""
        test_cases = [
            # Very low
            {'paragraph_cohesion': 0.0, 'topic_consistency': 0.0, 'discourse_flow': 0.0, 'conceptual_depth': 0.0},
            # Very high
            {'paragraph_cohesion': 1.0, 'topic_consistency': 1.0, 'discourse_flow': 1.0, 'conceptual_depth': 1.0},
            # Mixed
            {'paragraph_cohesion': 0.3, 'topic_consistency': 0.8, 'discourse_flow': 0.5, 'conceptual_depth': 0.7},
        ]

        for coherence_metrics in test_cases:
            metrics = {
                'available': True,
                'method': 'semantic',
                'content_type': 'general',
                'metrics': coherence_metrics
            }
            score = dimension.calculate_score(metrics)

            assert 0 <= score <= 100, f"Score {score} out of range for metrics {coherence_metrics}"

    def test_calculate_score_creative_domain(self, dimension):
        """Test score calculation for creative domain (higher thresholds)."""
        # Creative content has higher coherence thresholds (more narrative freedom)
        metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'creative',
            'metrics': {
                'paragraph_cohesion': 0.70,
                'topic_consistency': 0.68,
                'discourse_flow': 0.72,
                'conceptual_depth': 0.66
            }
        }
        score = dimension.calculate_score(metrics)

        # Average coherence = 0.69, should score reasonably well in creative domain
        assert 50 <= score <= 80, f"Creative domain score {score} unexpected for avg coherence 0.69"

    def test_calculate_score_academic_domain(self, dimension):
        """Test score calculation for academic domain (stricter thresholds)."""
        # Academic content has stricter thresholds (expects strong coherence)
        metrics = {
            'available': True,
            'method': 'semantic',
            'content_type': 'academic',
            'metrics': {
                'paragraph_cohesion': 0.75,
                'topic_consistency': 0.73,
                'discourse_flow': 0.76,
                'conceptual_depth': 0.74
            }
        }
        score = dimension.calculate_score(metrics)

        # Average coherence = 0.745, should score well in academic domain
        assert 60 <= score <= 90, f"Academic domain score {score} unexpected for avg coherence 0.745"
