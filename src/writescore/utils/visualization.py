"""
Visualization utilities for terminal output.

This module contains functions for creating sparklines, progress bars,
and other ASCII-based visualizations for terminal output.
"""

import shutil
from typing import List, Optional


def generate_sparkline(
    values: List[float],
    width: int = 20,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> str:
    """
    Generate ASCII sparkline from values.

    Args:
        values: List of numeric values
        width: Target width of sparkline
        min_val: Optional minimum value for scaling
        max_val: Optional maximum value for scaling

    Returns:
        Sparkline string
    """
    if not values:
        return ""

    # Sparkline characters from low to high
    chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    # Determine range
    if min_val is None:
        min_val = min(values)
    if max_val is None:
        max_val = max(values)

    if max_val == min_val:
        # All values are the same
        return chars[len(chars) // 2] * min(width, len(values))

    # Scale values to character range
    sparkline = []
    for val in values[:width]:
        # Normalize to 0-1
        normalized = (val - min_val) / (max_val - min_val)
        # Map to character index
        char_idx = min(int(normalized * len(chars)), len(chars) - 1)
        sparkline.append(chars[char_idx])

    return "".join(sparkline)


def create_progress_bar(
    current: int, total: int, width: int = 50, show_percentage: bool = True
) -> str:
    """
    Create ASCII progress bar.

    Args:
        current: Current progress value
        total: Total value
        width: Width of progress bar in characters
        show_percentage: Whether to show percentage

    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + " " * width + "] 0%"

    percentage = min(100, int((current / total) * 100))
    filled = int((current / total) * width)
    bar = "█" * filled + "░" * (width - filled)

    if show_percentage:
        return f"[{bar}] {percentage}%"
    else:
        return f"[{bar}]"


def create_horizontal_bar(value: float, max_value: float, width: int = 30, label: str = "") -> str:
    """
    Create horizontal bar chart.

    Args:
        value: Current value
        max_value: Maximum value
        width: Width of bar
        label: Optional label

    Returns:
        Horizontal bar string
    """
    if max_value == 0:
        filled = 0
    else:
        filled = int((value / max_value) * width)

    bar = "█" * filled + "░" * (width - filled)

    if label:
        return f"{label:20s} [{bar}] {value:.1f}/{max_value:.1f}"
    else:
        return f"[{bar}] {value:.1f}/{max_value:.1f}"


def get_terminal_width() -> int:
    """
    Get terminal width.

    Returns:
        Terminal width in characters (default 80 if unable to determine)
    """
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def create_box(text: str, width: Optional[int] = None, padding: int = 1) -> str:
    """
    Create a boxed text display.

    Args:
        text: Text to display in box
        width: Width of box (auto if None)
        padding: Padding inside box

    Returns:
        Boxed text string
    """
    lines = text.split("\n")

    if width is None:
        width = max(len(line) for line in lines) + (padding * 2) + 2

    inner_width = width - 2

    box_lines = []
    box_lines.append("┌" + "─" * inner_width + "┐")

    for line in lines:
        padded_line = " " * padding + line + " " * (inner_width - len(line) - padding)
        box_lines.append("│" + padded_line + "│")

    box_lines.append("└" + "─" * inner_width + "┘")

    return "\n".join(box_lines)


def create_table(
    headers: List[str], rows: List[List[str]], column_widths: Optional[List[int]] = None
) -> str:
    """
    Create ASCII table.

    Args:
        headers: List of column headers
        rows: List of rows (each row is a list of cell values)
        column_widths: Optional list of column widths

    Returns:
        Table string
    """
    if not headers or not rows:
        return ""

    # Calculate column widths if not provided
    if column_widths is None:
        column_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(column_widths):
                    column_widths[i] = max(column_widths[i], len(str(cell)))

    # Create header
    header_line = "│ " + " │ ".join(h.ljust(column_widths[i]) for i, h in enumerate(headers)) + " │"
    separator = "├─" + "─┼─".join("─" * w for w in column_widths) + "─┤"
    top_border = "┌─" + "─┬─".join("─" * w for w in column_widths) + "─┐"
    bottom_border = "└─" + "─┴─".join("─" * w for w in column_widths) + "─┘"

    table_lines = [top_border, header_line, separator]

    # Create rows
    for row in rows:
        row_line = (
            "│ "
            + " │ ".join(str(cell).ljust(column_widths[i]) for i, cell in enumerate(row))
            + " │"
        )
        table_lines.append(row_line)

    table_lines.append(bottom_border)

    return "\n".join(table_lines)


def colorize(text: str, color: str) -> str:
    """
    Add ANSI color to text.

    Args:
        text: Text to colorize
        color: Color name (red, green, yellow, blue, magenta, cyan, white)

    Returns:
        Colorized text with ANSI codes
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }

    color_code = colors.get(color.lower(), colors["reset"])
    reset_code = colors["reset"]

    return f"{color_code}{text}{reset_code}"
