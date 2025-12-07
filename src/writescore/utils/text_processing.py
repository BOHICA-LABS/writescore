"""
Text processing utilities.

This module contains helper functions for text analysis,
word counting, and basic text manipulation.
"""

import re
from typing import Dict, List, Tuple


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default for zero denominator.

    Args:
        numerator: Value to divide
        denominator: Value to divide by
        default: Value to return if denominator is zero

    Returns:
        numerator/denominator or default if denominator is 0
    """
    return numerator / denominator if denominator != 0 else default


def safe_ratio(count: int, total: int, default: float = 0.0) -> float:
    """
    Safe ratio calculation with default for zero total.

    Args:
        count: Numerator count
        total: Denominator total
        default: Value to return if total is zero

    Returns:
        count/total or default if total is 0
    """
    return count / total if total > 0 else default


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Text to count words in

    Returns:
        Number of words
    """
    # Simple word counting - matches word boundaries
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return len(words)


def clean_text(text: str, remove_code_blocks: bool = True) -> str:
    """
    Clean text by removing metadata and optionally code blocks.

    Args:
        text: Text to clean
        remove_code_blocks: Whether to remove fenced code blocks

    Returns:
        Cleaned text
    """
    # Remove HTML comments (metadata blocks)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove code blocks if requested
    if remove_code_blocks:
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    return text


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.

    Args:
        text: Text to extract sentences from

    Returns:
        List of sentences
    """
    # Simple sentence splitting - can be enhanced with NLTK
    # Handles common abbreviations
    text = re.sub(r"\b(Dr|Mr|Mrs|Ms|Prof)\.\s", r"\1<DOT> ", text)

    sentences = re.split(r"[.!?]+\s+", text)

    # Restore abbreviations
    sentences = [s.replace("<DOT>", ".") for s in sentences if s.strip()]

    return sentences


def extract_paragraphs(lines: List[str]) -> List[List[str]]:
    """
    Extract paragraphs from lines.

    Args:
        lines: List of text lines

    Returns:
        List of paragraphs (each paragraph is a list of lines)
    """
    paragraphs: List[List[str]] = []
    current_para: List[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and markdown structures
        if not stripped or stripped.startswith("#") or stripped.startswith("```"):
            if current_para:
                paragraphs.append(current_para)
                current_para = []
            continue

        current_para.append(line)

    if current_para:
        paragraphs.append(current_para)

    return paragraphs


def is_code_block_line(line: str) -> bool:
    """
    Check if line is part of a code block.

    Args:
        line: Line to check

    Returns:
        True if line is a code block fence
    """
    stripped = line.strip()
    return stripped.startswith("```")


def is_list_item(line: str) -> bool:
    """
    Check if line is a list item.

    Args:
        line: Line to check

    Returns:
        True if line is a list item
    """
    stripped = line.strip()
    # Bullet lists: -, *, +
    # Numbered lists: 1., 2., etc.
    return bool(re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+\.\s+", stripped))


def extract_heading_info(line: str) -> Tuple[int, str]:
    """
    Extract heading level and text from a markdown heading line.

    Args:
        line: Line to parse

    Returns:
        Tuple of (heading_level, heading_text) or (0, "") if not a heading
    """
    match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if match:
        level = len(match.group(1))
        text = match.group(2).strip()
        return level, text
    return 0, ""


def calculate_word_frequency(text: str) -> dict:
    """
    Calculate word frequency in text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary mapping words to their counts
    """
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    freq: Dict[str, int] = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return freq


def get_line_context(lines: List[str], line_num: int, context_size: int = 30) -> str:
    """
    Get context around a specific line.

    Args:
        lines: All lines
        line_num: Target line number (0-indexed)
        context_size: Number of characters to include on each side

    Returns:
        Context string
    """
    if line_num < 0 or line_num >= len(lines):
        return ""

    line = lines[line_num]
    if len(line) <= context_size * 2:
        return line

    # Find the middle of the line and extract context
    mid = len(line) // 2
    start = max(0, mid - context_size)
    end = min(len(line), mid + context_size)

    context = line[start:end]
    if start > 0:
        context = "..." + context
    if end < len(line):
        context = context + "..."

    return context
