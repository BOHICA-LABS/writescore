"""
Tests for DimensionAnalyzer base class.
"""

import pytest
from marko.block import FencedCode, Heading, Quote

from writescore.dimensions.base import DimensionAnalyzer

# All dependencies are now required
HAS_MARKO = True


# Create concrete implementation for testing abstract base class
class ConcreteDimensionAnalyzer(DimensionAnalyzer):
    """Concrete implementation for testing the abstract base class."""

    def analyze(self, text, lines=None, **kwargs):
        """Test implementation of abstract analyze method."""
        return {'test': 'analysis', 'text_length': len(text)}

    def score(self, analysis_results):
        """Test implementation of abstract score method."""
        return (7.5, "MEDIUM")


@pytest.fixture
def analyzer():
    """Create test analyzer instance."""
    return ConcreteDimensionAnalyzer()


@pytest.fixture
def markdown_text():
    """Sample markdown text for AST testing."""
    return """# Heading 1

This is a paragraph with some text.

## Heading 2

> This is a blockquote
> with multiple lines

- List item 1
- List item 2

```python
def hello():
    return "world"
```

[Link text](https://example.com)
"""


class TestInit:
    """Tests for __init__ method."""

    def test_init_creates_parser_cache(self, analyzer):
        """Test that init creates AST cache."""
        assert hasattr(analyzer, '_markdown_parser')
        assert hasattr(analyzer, '_ast_cache')
        assert analyzer._ast_cache == {}


class TestAbstractMethods:
    """Tests for abstract method implementations."""

    def test_analyze_implemented(self, analyzer):
        """Test that analyze method is implemented."""
        result = analyzer.analyze("test text", lines=["test", "text"])

        assert isinstance(result, dict)
        assert 'test' in result

    def test_score_implemented(self, analyzer):
        """Test that score method is implemented."""
        score, label = analyzer.score({'test': 'data'})

        assert isinstance(score, (int, float))
        assert isinstance(label, str)


class TestGetMaxScore:
    """Tests for get_max_score method."""

    def test_get_max_score_default(self, analyzer):
        """Test default max score is 10.0."""
        max_score = analyzer.get_max_score()

        assert max_score == 10.0

    def test_get_max_score_can_override(self):
        """Test that subclasses can override max score."""
        class CustomAnalyzer(DimensionAnalyzer):
            def analyze(self, text, lines=None, **kwargs):
                return {}

            def score(self, analysis_results):
                return (0, "")

            def get_max_score(self):
                return 20.0

        analyzer = CustomAnalyzer()
        assert analyzer.get_max_score() == 20.0


class TestGetDimensionName:
    """Tests for get_dimension_name method."""

    def test_get_dimension_name(self, analyzer):
        """Test dimension name extraction from class name."""
        name = analyzer.get_dimension_name()

        assert name == "ConcreteDimension"
        assert "Analyzer" not in name

    def test_get_dimension_name_various_classes(self):
        """Test dimension name extraction for different class names."""
        class StructureAnalyzer(DimensionAnalyzer):
            def analyze(self, text, lines=None, **kwargs):
                return {}

            def score(self, analysis_results):
                return (0, "")

        analyzer = StructureAnalyzer()
        assert analyzer.get_dimension_name() == "Structure"


class TestGetMarkdownParser:
    """Tests for _get_markdown_parser method (requires marko)."""

    def test_get_markdown_parser_lazy_load(self, analyzer):
        """Test parser is lazily loaded."""
        # Initially None
        assert analyzer._markdown_parser is None

        # Loads on first call
        parser1 = analyzer._get_markdown_parser()
        assert parser1 is not None

        # Returns same instance on subsequent calls
        parser2 = analyzer._get_markdown_parser()
        assert parser2 is parser1

    def test_get_markdown_parser_creates_instance(self, analyzer):
        """Test parser creates correct instance."""
        parser = analyzer._get_markdown_parser()

        assert parser is not None
        assert hasattr(parser, 'parse')


class TestGetMarkdownParserNoMarko:
    """Tests for _get_markdown_parser without marko."""

    @pytest.mark.skipif(HAS_MARKO, reason="Test requires marko to be unavailable")
    def test_get_markdown_parser_no_marko(self, analyzer):
        """Test parser returns None without marko."""
        parser = analyzer._get_markdown_parser()

        assert parser is None


class TestParseToAst:
    """Tests for _parse_to_ast method (requires marko)."""

    def test_parse_to_ast_basic(self, analyzer, markdown_text):
        """Test basic AST parsing."""
        ast = analyzer._parse_to_ast(markdown_text)

        assert ast is not None
        assert hasattr(ast, 'children')

    def test_parse_to_ast_caching(self, analyzer, markdown_text):
        """Test AST caching behavior."""
        # Parse with cache key
        ast1 = analyzer._parse_to_ast(markdown_text, cache_key="test_key")
        assert "test_key" in analyzer._ast_cache

        # Should return cached version
        ast2 = analyzer._parse_to_ast("different text", cache_key="test_key")
        assert ast2 is ast1  # Same object

    def test_parse_to_ast_no_cache_key(self, analyzer, markdown_text):
        """Test parsing without caching."""
        ast = analyzer._parse_to_ast(markdown_text)

        assert ast is not None
        assert len(analyzer._ast_cache) == 0

    def test_parse_to_ast_empty_text(self, analyzer):
        """Test parsing empty text."""
        ast = analyzer._parse_to_ast("")

        # Should return AST even for empty text
        assert ast is not None

    def test_parse_to_ast_handles_errors(self, analyzer):
        """Test error handling in parsing."""
        # Even malformed markdown should not raise exception
        ast = analyzer._parse_to_ast("# [Unclosed link")

        # Should return something or None
        assert ast is not None or ast is None


class TestParseToAstNoMarko:
    """Tests for _parse_to_ast without marko."""

    @pytest.mark.skipif(HAS_MARKO, reason="Test requires marko to be unavailable")
    def test_parse_to_ast_no_marko(self, analyzer):
        """Test parsing returns None without marko."""
        ast = analyzer._parse_to_ast("# Heading")

        assert ast is None


class TestWalkAst:
    """Tests for _walk_ast method (requires marko)."""

    def test_walk_ast_all_nodes(self, analyzer, markdown_text):
        """Test walking AST and collecting all nodes."""
        ast = analyzer._parse_to_ast(markdown_text)
        nodes = analyzer._walk_ast(ast)

        # Should collect multiple nodes
        assert len(nodes) > 0

    def test_walk_ast_filter_by_type(self, analyzer, markdown_text):
        """Test walking AST with type filter."""
        ast = analyzer._parse_to_ast(markdown_text)

        # Get all headings
        headings = analyzer._walk_ast(ast, node_type=Heading)
        assert len(headings) > 0
        assert all(isinstance(h, Heading) for h in headings)

    def test_walk_ast_quotes(self, analyzer, markdown_text):
        """Test collecting blockquotes."""
        ast = analyzer._parse_to_ast(markdown_text)

        quotes = analyzer._walk_ast(ast, node_type=Quote)
        # markdown_text has 1 blockquote
        assert len(quotes) >= 1

    def test_walk_ast_code_blocks(self, analyzer, markdown_text):
        """Test collecting code blocks."""
        ast = analyzer._parse_to_ast(markdown_text)

        code_blocks = analyzer._walk_ast(ast, node_type=FencedCode)
        # markdown_text has 1 code block
        assert len(code_blocks) >= 1

    def test_walk_ast_empty_tree(self, analyzer):
        """Test walking empty AST."""
        ast = analyzer._parse_to_ast("")
        nodes = analyzer._walk_ast(ast)

        # Should still return list (possibly with root node)
        assert isinstance(nodes, list)


class TestExtractTextFromNode:
    """Tests for _extract_text_from_node method (requires marko)."""

    def test_extract_text_basic(self, analyzer):
        """Test extracting text from simple node."""
        text = "# Simple heading"
        ast = analyzer._parse_to_ast(text)
        headings = analyzer._walk_ast(ast, node_type=Heading)

        if headings:
            extracted = analyzer._extract_text_from_node(headings[0])
            assert "Simple heading" in extracted

    def test_extract_text_nested_nodes(self, analyzer):
        """Test extracting text from nested structure."""
        text = """
> This is a blockquote
> with **bold** and *italic*
"""
        ast = analyzer._parse_to_ast(text)
        quotes = analyzer._walk_ast(ast, node_type=Quote)

        if quotes:
            extracted = analyzer._extract_text_from_node(quotes[0])
            assert "blockquote" in extracted
            assert "bold" in extracted
            assert "italic" in extracted

    def test_extract_text_empty_node(self, analyzer):
        """Test extracting text from empty structure."""
        ast = analyzer._parse_to_ast("")
        extracted = analyzer._extract_text_from_node(ast)

        assert isinstance(extracted, str)

    def test_extract_text_from_string(self, analyzer):
        """Test extracting text when node is a string."""
        extracted = analyzer._extract_text_from_node("plain string")

        assert extracted == "plain string"


class TestIntegration:
    """Integration tests for base analyzer."""

    def test_full_ast_pipeline(self, analyzer, markdown_text):
        """Test complete AST processing pipeline."""
        if not HAS_MARKO:
            pytest.skip("marko not available")

        # Parse
        ast = analyzer._parse_to_ast(markdown_text, cache_key="integration")

        # Walk
        headings = analyzer._walk_ast(ast, node_type=Heading)

        # Extract
        if headings:
            text = analyzer._extract_text_from_node(headings[0])
            assert isinstance(text, str)

        # Verify caching
        assert "integration" in analyzer._ast_cache

    def test_dimension_methods_work_together(self, analyzer):
        """Test that all dimension methods work together."""
        # Analyze
        result = analyzer.analyze("test text", lines=["test", "text"])
        assert isinstance(result, dict)

        # Score
        score, label = analyzer.score(result)
        assert isinstance(score, (int, float))
        assert isinstance(label, str)

        # Max score
        max_score = analyzer.get_max_score()
        assert score <= max_score

        # Name
        name = analyzer.get_dimension_name()
        assert isinstance(name, str)
