"""
Tests for text_processing utilities.

Tests cover all helper functions for text analysis, word counting,
and text manipulation.
"""

import pytest
from writescore.utils.text_processing import (
    safe_divide,
    safe_ratio,
    count_words,
    clean_text,
    extract_sentences,
    extract_paragraphs,
    is_code_block_line,
    is_list_item,
    extract_heading_info,
    calculate_word_frequency,
    get_line_context
)


class TestSafeDivide:
    """Tests for safe_divide function."""

    def test_safe_divide_normal(self):
        """Test normal division."""
        result = safe_divide(10.0, 2.0)
        assert result == 5.0

    def test_safe_divide_zero_denominator(self):
        """Test division by zero returns default."""
        result = safe_divide(10.0, 0.0)
        assert result == 0.0

    def test_safe_divide_custom_default(self):
        """Test custom default value."""
        result = safe_divide(10.0, 0.0, default=99.0)
        assert result == 99.0

    def test_safe_divide_negative(self):
        """Test division with negative numbers."""
        result = safe_divide(-10.0, 2.0)
        assert result == -5.0

    def test_safe_divide_float_result(self):
        """Test division with float result."""
        result = safe_divide(7.0, 2.0)
        assert result == 3.5


class TestSafeRatio:
    """Tests for safe_ratio function."""

    def test_safe_ratio_normal(self):
        """Test normal ratio calculation."""
        result = safe_ratio(5, 10)
        assert result == 0.5

    def test_safe_ratio_zero_total(self):
        """Test ratio with zero total returns default."""
        result = safe_ratio(5, 0)
        assert result == 0.0

    def test_safe_ratio_custom_default(self):
        """Test custom default value."""
        result = safe_ratio(5, 0, default=1.0)
        assert result == 1.0

    def test_safe_ratio_full_ratio(self):
        """Test ratio of 100%."""
        result = safe_ratio(10, 10)
        assert result == 1.0

    def test_safe_ratio_zero_count(self):
        """Test ratio with zero count."""
        result = safe_ratio(0, 10)
        assert result == 0.0


class TestCountWords:
    """Tests for count_words function."""

    def test_count_words_basic(self):
        """Test basic word counting."""
        text = "This is a test with five words."
        count = count_words(text)
        assert count == 7  # "This is a test with five words"

    def test_count_words_empty(self):
        """Test counting words in empty string."""
        count = count_words("")
        assert count == 0

    def test_count_words_numbers_excluded(self):
        """Test that numbers are excluded."""
        text = "Test 123 456 words"
        count = count_words(text)
        assert count == 2  # Only "Test" and "words"

    def test_count_words_special_chars(self):
        """Test word counting with special characters."""
        text = "Hello, world! How are you?"
        count = count_words(text)
        assert count == 5

    def test_count_words_multiline(self):
        """Test word counting across lines."""
        text = "Line one\nLine two\nLine three"
        count = count_words(text)
        assert count == 6


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_text_html_comments(self):
        """Test removing HTML comments."""
        text = "Before <!-- comment --> After"
        cleaned = clean_text(text)
        assert "comment" not in cleaned
        assert "Before" in cleaned
        assert "After" in cleaned

    def test_clean_text_multiline_html_comments(self):
        """Test removing multiline HTML comments."""
        text = """Before
<!--
Multi-line
comment
-->
After"""
        cleaned = clean_text(text)
        assert "Multi-line" not in cleaned
        assert "Before" in cleaned
        assert "After" in cleaned

    def test_clean_text_code_blocks_default(self):
        """Test removing code blocks by default."""
        text = """Text
```python
code here
```
More text"""
        cleaned = clean_text(text)
        assert "code here" not in cleaned
        assert "Text" in cleaned
        assert "More text" in cleaned

    def test_clean_text_keep_code_blocks(self):
        """Test keeping code blocks when specified."""
        text = """Text
```python
code here
```
More text"""
        cleaned = clean_text(text, remove_code_blocks=False)
        assert "code here" in cleaned

    def test_clean_text_both(self):
        """Test removing both HTML comments and code blocks."""
        text = """Before
<!-- comment -->
```
code
```
After"""
        cleaned = clean_text(text)
        assert "comment" not in cleaned
        assert "code" not in cleaned
        assert "Before" in cleaned
        assert "After" in cleaned


class TestExtractSentences:
    """Tests for extract_sentences function."""

    def test_extract_sentences_basic(self):
        """Test basic sentence extraction."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = extract_sentences(text)
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]

    def test_extract_sentences_abbreviations(self):
        """Test handling of abbreviations."""
        text = "Dr. Smith works here. He is great."
        sentences = extract_sentences(text)
        # Should not split on "Dr."
        assert any("Dr." in s for s in sentences)
        assert len(sentences) == 2

    def test_extract_sentences_empty(self):
        """Test extraction from empty text."""
        sentences = extract_sentences("")
        assert len(sentences) == 0

    def test_extract_sentences_no_punctuation(self):
        """Test extraction from text without ending punctuation."""
        text = "Single sentence without ending"
        sentences = extract_sentences(text)
        assert len(sentences) >= 1

    def test_extract_sentences_multiple_abbreviations(self):
        """Test multiple abbreviation types."""
        text = "Dr. Jones and Mrs. Smith work with Prof. Brown."
        sentences = extract_sentences(text)
        # Should keep abbreviations intact
        result = ' '.join(sentences)
        assert "Dr." in result
        assert "Mrs." in result
        assert "Prof." in result


class TestExtractParagraphs:
    """Tests for extract_paragraphs function."""

    def test_extract_paragraphs_basic(self):
        """Test basic paragraph extraction."""
        lines = [
            "Line 1",
            "Line 2",
            "",
            "Line 3",
            "Line 4"
        ]
        paragraphs = extract_paragraphs(lines)
        assert len(paragraphs) == 2
        assert len(paragraphs[0]) == 2  # Lines 1-2
        assert len(paragraphs[1]) == 2  # Lines 3-4

    def test_extract_paragraphs_with_headings(self):
        """Test that headings are excluded."""
        lines = [
            "# Heading",
            "Para line 1",
            "Para line 2"
        ]
        paragraphs = extract_paragraphs(lines)
        # Heading should not be in paragraph
        assert len(paragraphs) == 1
        assert "# Heading" not in paragraphs[0]

    def test_extract_paragraphs_with_code_blocks(self):
        """Test that code block markers are excluded."""
        lines = [
            "Text before",
            "```python",
            "code",
            "```",
            "Text after"
        ]
        paragraphs = extract_paragraphs(lines)
        # Should have 2 paragraphs (before and after code)
        assert len(paragraphs) >= 2

    def test_extract_paragraphs_empty_lines(self):
        """Test handling of multiple empty lines."""
        lines = [
            "Para 1",
            "",
            "",
            "Para 2"
        ]
        paragraphs = extract_paragraphs(lines)
        assert len(paragraphs) == 2

    def test_extract_paragraphs_single_paragraph(self):
        """Test extraction of single continuous paragraph."""
        lines = ["Line 1", "Line 2", "Line 3"]
        paragraphs = extract_paragraphs(lines)
        assert len(paragraphs) == 1
        assert len(paragraphs[0]) == 3


class TestIsCodeBlockLine:
    """Tests for is_code_block_line function."""

    def test_is_code_block_line_basic(self):
        """Test detection of code block fence."""
        assert is_code_block_line("```") is True

    def test_is_code_block_line_with_language(self):
        """Test detection with language specifier."""
        assert is_code_block_line("```python") is True

    def test_is_code_block_line_with_whitespace(self):
        """Test detection with leading/trailing whitespace."""
        assert is_code_block_line("  ```  ") is True

    def test_is_code_block_line_regular_text(self):
        """Test that regular text is not detected."""
        assert is_code_block_line("Regular text") is False

    def test_is_code_block_line_partial(self):
        """Test that partial fence is not detected."""
        assert is_code_block_line("``") is False


class TestIsListItem:
    """Tests for is_list_item function."""

    def test_is_list_item_bullet_dash(self):
        """Test detection of dash bullet list."""
        assert is_list_item("- Item") is True

    def test_is_list_item_bullet_asterisk(self):
        """Test detection of asterisk bullet list."""
        assert is_list_item("* Item") is True

    def test_is_list_item_bullet_plus(self):
        """Test detection of plus bullet list."""
        assert is_list_item("+ Item") is True

    def test_is_list_item_numbered(self):
        """Test detection of numbered list."""
        assert is_list_item("1. Item") is True
        assert is_list_item("42. Item") is True

    def test_is_list_item_with_whitespace(self):
        """Test detection with leading whitespace."""
        assert is_list_item("  - Item") is True

    def test_is_list_item_regular_text(self):
        """Test that regular text is not detected."""
        assert is_list_item("Regular text") is False

    def test_is_list_item_no_space_after_marker(self):
        """Test that marker without space is not detected."""
        assert is_list_item("-Item") is False


class TestExtractHeadingInfo:
    """Tests for extract_heading_info function."""

    def test_extract_heading_h1(self):
        """Test H1 heading extraction."""
        level, text = extract_heading_info("# Heading 1")
        assert level == 1
        assert text == "Heading 1"

    def test_extract_heading_h2(self):
        """Test H2 heading extraction."""
        level, text = extract_heading_info("## Heading 2")
        assert level == 2
        assert text == "Heading 2"

    def test_extract_heading_h6(self):
        """Test H6 heading extraction."""
        level, text = extract_heading_info("###### Heading 6")
        assert level == 6
        assert text == "Heading 6"

    def test_extract_heading_not_heading(self):
        """Test that non-heading returns (0, '')."""
        level, text = extract_heading_info("Regular text")
        assert level == 0
        assert text == ""

    def test_extract_heading_with_whitespace(self):
        """Test heading with extra whitespace."""
        level, text = extract_heading_info("  ## Heading  ")
        assert level == 2
        assert text == "Heading"

    def test_extract_heading_no_space_after_hash(self):
        """Test that heading without space is not detected."""
        level, text = extract_heading_info("#Heading")
        assert level == 0
        assert text == ""


class TestCalculateWordFrequency:
    """Tests for calculate_word_frequency function."""

    def test_calculate_word_frequency_basic(self):
        """Test basic word frequency calculation."""
        text = "the cat and the dog"
        freq = calculate_word_frequency(text)
        assert freq['the'] == 2
        assert freq['cat'] == 1
        assert freq['dog'] == 1

    def test_calculate_word_frequency_case_insensitive(self):
        """Test that frequency is case-insensitive."""
        text = "Word word WORD"
        freq = calculate_word_frequency(text)
        assert freq['word'] == 3

    def test_calculate_word_frequency_empty(self):
        """Test frequency of empty text."""
        freq = calculate_word_frequency("")
        assert len(freq) == 0

    def test_calculate_word_frequency_numbers_excluded(self):
        """Test that numbers are excluded."""
        text = "test 123 test"
        freq = calculate_word_frequency(text)
        assert '123' not in freq
        assert freq['test'] == 2

    def test_calculate_word_frequency_special_chars(self):
        """Test handling of special characters."""
        text = "hello, world! hello!"
        freq = calculate_word_frequency(text)
        assert freq['hello'] == 2
        assert freq['world'] == 1


class TestGetLineContext:
    """Tests for get_line_context function."""

    def test_get_line_context_short_line(self):
        """Test context for short line (returns whole line)."""
        lines = ["Short line"]
        context = get_line_context(lines, 0, context_size=30)
        assert context == "Short line"

    def test_get_line_context_long_line(self):
        """Test context extraction from long line."""
        long_line = "This is a very long line that should be truncated to show context around the middle"
        lines = [long_line]
        context = get_line_context(lines, 0, context_size=20)
        # Should be truncated
        assert len(context) <= 60  # 20*2 + "..."
        assert context.startswith("...")
        assert context.endswith("...")

    def test_get_line_context_invalid_line_num(self):
        """Test context for invalid line number."""
        lines = ["Line 1"]
        context = get_line_context(lines, 5, context_size=30)
        assert context == ""

    def test_get_line_context_negative_line_num(self):
        """Test context for negative line number."""
        lines = ["Line 1"]
        context = get_line_context(lines, -1, context_size=30)
        assert context == ""

    def test_get_line_context_multiple_lines(self):
        """Test context extraction from multiple lines."""
        lines = ["Line 1", "Line 2 is very long and should be truncated properly", "Line 3"]
        context = get_line_context(lines, 1, context_size=15)
        # Should extract context from line 1 (index 1)
        assert isinstance(context, str)
        assert len(context) > 0


class TestIntegration:
    """Integration tests for text processing utilities."""

    def test_full_text_processing_pipeline(self):
        """Test complete text processing workflow."""
        text = """# Introduction

This is a paragraph with multiple sentences. It has several words.

<!-- HTML comment to remove -->

```python
# Code to remove
print("hello")
```

Final paragraph here.
"""
        # Clean text
        cleaned = clean_text(text)
        assert "HTML comment" not in cleaned
        assert "Code to remove" not in cleaned

        # Count words
        word_count = count_words(cleaned)
        assert word_count > 0

        # Extract sentences
        sentences = extract_sentences(cleaned)
        assert len(sentences) > 0

    def test_markdown_structure_analysis(self):
        """Test analyzing markdown structure."""
        lines = [
            "# Main Heading",
            "",
            "Paragraph text here.",
            "",
            "- List item 1",
            "- List item 2",
            "",
            "```python",
            "code",
            "```"
        ]

        # Extract paragraphs
        paragraphs = extract_paragraphs(lines)
        assert len(paragraphs) > 0

        # Check heading
        level, text = extract_heading_info(lines[0])
        assert level == 1
        assert text == "Main Heading"

        # Check list items
        assert is_list_item(lines[4]) is True

        # Check code block
        assert is_code_block_line(lines[7]) is True
