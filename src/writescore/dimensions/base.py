"""
Base dimension analyzer interface.

All dimension analyzers should inherit from this base class
to ensure consistent interface across the analysis system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Required AST parsing support
from marko import Markdown


class DimensionAnalyzer(ABC):
    """Base class for all dimension analyzers."""

    def __init__(self):
        """Initialize the dimension analyzer with AST support."""
        # AST parser and cache (marko)
        self._markdown_parser = None
        self._ast_cache = {}

    @abstractmethod
    def analyze(self, text: str, lines: List[str], **kwargs) -> Dict[str, Any]:
        """
        Analyze text for this dimension.

        Args:
            text: Full text content
            lines: Text split into lines
            **kwargs: Additional analysis parameters

        Returns:
            Dict with analysis results specific to this dimension
        """
        pass

    @abstractmethod
    def score(self, analysis_results: Dict[str, Any]) -> tuple:
        """
        Calculate score for this dimension.

        Args:
            analysis_results: Results from analyze()

        Returns:
            Tuple of (score_value, score_label) where:
                - score_value is a float (0.0 to max_score for this dimension)
                - score_label is a string like 'HIGH', 'MEDIUM', 'LOW', etc.
        """
        pass

    def get_max_score(self) -> float:
        """
        Get maximum possible score for this dimension.

        Returns:
            Maximum score value
        """
        return 10.0  # Default, can be overridden

    def get_dimension_name(self) -> str:
        """
        Get the name of this dimension.

        Returns:
            Dimension name
        """
        return self.__class__.__name__.replace("Analyzer", "")

    # ========================================================================
    # AST HELPER METHODS (for Phase 3 structure analysis)
    # ========================================================================

    def _get_markdown_parser(self):
        """Lazy load marko parser."""
        if self._markdown_parser is None:
            self._markdown_parser = Markdown()
        return self._markdown_parser

    def _parse_to_ast(self, text: str, cache_key: Optional[str] = None):
        """Parse markdown to AST with caching.

        Args:
            text: Markdown text to parse
            cache_key: Optional cache key for reusing parsed AST

        Returns:
            Parsed AST node or None if parsing fails
        """
        if cache_key and cache_key in self._ast_cache:
            return self._ast_cache[cache_key]

        parser = self._get_markdown_parser()
        if parser is None:
            return None

        try:
            ast = parser.parse(text)
            if cache_key:
                self._ast_cache[cache_key] = ast
            return ast
        except Exception:
            return None

    def _walk_ast(self, node, node_type=None):
        """Recursively walk AST and collect nodes of specified type.

        Args:
            node: AST node to walk
            node_type: Optional type to filter (e.g., Quote)

        Returns:
            List of nodes matching node_type, or all nodes if node_type is None
        """
        nodes = []

        if node_type is None or isinstance(node, node_type):
            nodes.append(node)

        # Recursively process children
        if hasattr(node, "children") and node.children:
            for child in node.children:
                nodes.extend(self._walk_ast(child, node_type))

        return nodes

    def _extract_text_from_node(self, node) -> str:
        """Extract plain text from AST node recursively.

        Args:
            node: AST node to extract text from

        Returns:
            Plain text string
        """
        if hasattr(node, "children") and node.children:
            return "".join([self._extract_text_from_node(child) for child in node.children])
        elif hasattr(node, "children") and isinstance(node.children, str):
            return node.children
        elif hasattr(node, "dest"):  # Link destination
            return ""
        elif isinstance(node, str):
            return node
        else:
            return ""
