"""Configuration infrastructure for AI Pattern Analyzer.

This module provides configurable analysis modes and configuration options
for controlling how documents are analyzed, enabling speed/accuracy tradeoffs
for different use cases (short snippets vs. book chapters).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnalysisMode(str, Enum):
    """Analysis mode controlling document processing strategy."""

    FAST = "fast"  # Truncate to 2000 chars (current behavior)
    ADAPTIVE = "adaptive"  # Adapt to document length (recommended)
    SAMPLING = "sampling"  # Sample N sections, aggregate
    FULL = "full"  # Analyze entire document
    STREAMING = "streaming"  # Progressive analysis (future)


@dataclass
class AnalysisConfig:
    """Configuration for document analysis behavior.

    This class controls how documents are processed during analysis,
    including text truncation, sampling strategies, dimension-specific
    overrides, and dimension loading profiles.

    Attributes:
        mode: Analysis mode (FAST, ADAPTIVE, SAMPLING, FULL, STREAMING)
        sampling_sections: Number of sections to sample (default: 5)
        sampling_chars_per_section: Characters per sample (default: 2000)
        sampling_strategy: Strategy for sample selection (even, weighted, adaptive)
        max_text_length: Optional hard limit on text length
        max_analysis_time_seconds: Optional timeout for analysis
        dimension_overrides: Dict of dimension-specific config overrides
        enable_detailed_analysis: Enable detailed metrics (default: True)

        # Dimension loading configuration (Story 1.4.11)
        dimension_profile: Profile for dimension loading (fast/balanced/full/custom)
        dimensions_to_load: Explicit list of dimensions (overrides profile)
        custom_profiles: User-defined dimension profiles
    """

    # Document processing configuration
    mode: AnalysisMode = AnalysisMode.ADAPTIVE
    sampling_sections: int = 5
    sampling_chars_per_section: int = 2000
    sampling_strategy: str = "even"  # "even", "weighted", "adaptive"
    max_text_length: Optional[int] = None
    max_analysis_time_seconds: Optional[int] = 300
    dimension_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    enable_detailed_analysis: bool = True

    # Dimension loading configuration (Story 1.4.11)
    dimension_profile: str = "balanced"  # Profile: fast, balanced, full, or custom
    dimensions_to_load: Optional[List[str]] = None  # Override profile with explicit list
    custom_profiles: Optional[Dict[str, List[str]]] = None  # User-defined profiles

    # Score normalization configuration (Story 2.4.1, AC7)
    enable_score_normalization: bool = True  # Enable z-score normalization across dimensions

    def get_effective_limit(self, dimension_name: str, text_length: int) -> Optional[int]:
        """
        Calculate effective character limit based on mode.

        Args:
            dimension_name: Name of dimension (for override lookup)
            text_length: Total length of text to analyze

        Returns:
            Character limit (None = no limit)

        Algorithm:
            - FAST mode: Always return 2000 (current behavior)
            - ADAPTIVE mode:
                * text < 5000 chars: No limit (analyze all)
                * text 5000-50000 chars: 10000 char limit
                * text > 50000 chars: Use sampling (return None to trigger sampling)
            - SAMPLING mode: Return None (triggers extract_samples)
            - FULL mode: Return None (no limit)
            - STREAMING mode: Return None (future implementation)
            - Check dimension_overrides for custom limits
        """
        # Check for dimension-specific override
        if dimension_name in self.dimension_overrides:
            override = self.dimension_overrides[dimension_name]
            if "max_chars" in override:
                return int(override["max_chars"]) if override["max_chars"] is not None else None

        # Mode-based logic
        if self.mode == AnalysisMode.FAST:
            return 2000  # Current behavior - always truncate

        elif self.mode == AnalysisMode.ADAPTIVE:
            # Adaptive scaling based on document length
            if text_length < 5000:
                return None  # Small docs - analyze fully
            elif text_length < 50000:
                return 10000  # Medium docs - analyze first 10k
            else:
                return None  # Large docs - triggers sampling via should_use_sampling()

        elif self.mode == AnalysisMode.SAMPLING:
            return None  # Sampling mode uses extract_samples()

        elif self.mode == AnalysisMode.FULL:
            return None  # No limit - analyze entire document

        elif self.mode == AnalysisMode.STREAMING:
            return None  # Future: progressive analysis

        else:
            return 2000  # Fallback to safe default

    def should_use_sampling(self, text_length: int) -> bool:
        """
        Determine if sampling should be used.

        Args:
            text_length: Total length of text

        Returns:
            True if sampling should be used, False otherwise

        Algorithm:
            - FAST mode: Never sample (always truncate)
            - ADAPTIVE mode: Sample if text > 50,000 chars
            - SAMPLING mode: Always sample
            - FULL mode: Never sample
            - STREAMING mode: Never sample (progressive, not sampled)
        """
        if self.mode == AnalysisMode.FAST:
            return False  # FAST mode truncates, doesn't sample

        elif self.mode == AnalysisMode.ADAPTIVE:
            # Use sampling for large documents (>50k chars = ~25+ pages)
            return text_length > 50000

        elif self.mode == AnalysisMode.SAMPLING:
            return True  # Always sample in SAMPLING mode

        elif self.mode == AnalysisMode.FULL:
            return False  # FULL mode analyzes everything

        elif self.mode == AnalysisMode.STREAMING:
            return False  # STREAMING processes progressively

        else:
            return False  # Safe default

    def extract_samples(self, text: str) -> List[Tuple[int, str]]:
        """
        Extract representative samples from text.

        Args:
            text: Full text to sample from

        Returns:
            List of (start_position, sample_text) tuples

        Algorithm:
            1. Divide text into N sections (sampling_sections, default 5)
            2. Extract sample from each section based on strategy:
               - "even": Extract from evenly spaced positions
               - "weighted": Weight toward beginning/end (intro + conclusion important)
               - "adaptive": Detect section boundaries (headings), sample each
            3. Each sample is sampling_chars_per_section long (default 2000)

        Example:
            For 180,000 char document with 5 sections:
            - Section size = 180,000 / 5 = 36,000 chars
            - "even" strategy samples at: 0, 36k, 72k, 108k, 144k
            - Each sample is 2000 chars from that position
        """
        text_length = len(text)
        samples = []

        if text_length <= self.sampling_chars_per_section:
            # Text is smaller than one sample - return entire text
            return [(0, text)]

        if self.sampling_strategy == "even":
            # Evenly spaced samples
            section_size = text_length // self.sampling_sections
            for i in range(self.sampling_sections):
                start_pos = i * section_size
                end_pos = min(start_pos + self.sampling_chars_per_section, text_length)
                sample_text = text[start_pos:end_pos]
                samples.append((start_pos, sample_text))

        elif self.sampling_strategy == "weighted":
            # Weight toward beginning (40%) and end (30%), middle (30%)
            # Rationale: Intro and conclusion often contain key patterns
            positions = [
                0,  # Beginning
                int(text_length * 0.1),  # Early section
                int(text_length * 0.4),  # Middle
                int(text_length * 0.7),  # Late middle
                max(0, text_length - self.sampling_chars_per_section),  # End
            ]
            for start_pos in positions[: self.sampling_sections]:
                end_pos = min(start_pos + self.sampling_chars_per_section, text_length)
                sample_text = text[start_pos:end_pos]
                samples.append((start_pos, sample_text))

        elif self.sampling_strategy == "adaptive":
            # Detect section boundaries via headings (# in markdown)
            # Sample from each major section
            import re

            heading_pattern = re.compile(r"^#{1,3}\s", re.MULTILINE)
            heading_positions = [m.start() for m in heading_pattern.finditer(text)]

            if len(heading_positions) < 2:
                # No clear sections - fall back to even sampling
                return self._extract_even_samples(text)

            # Sample from each section
            section_starts = [0] + heading_positions + [text_length]
            sections_to_sample = min(self.sampling_sections, len(section_starts) - 1)

            for i in range(sections_to_sample):
                start_pos = section_starts[i]
                end_pos = min(
                    start_pos + self.sampling_chars_per_section,
                    section_starts[i + 1] if i + 1 < len(section_starts) else text_length,
                )
                sample_text = text[start_pos:end_pos]
                samples.append((start_pos, sample_text))
        else:
            # Unknown strategy - default to even
            return self._extract_even_samples(text)

        return samples

    def _extract_even_samples(self, text: str) -> List[Tuple[int, str]]:
        """Helper for even sampling (used as fallback)."""
        text_length = len(text)
        samples = []
        section_size = text_length // self.sampling_sections
        for i in range(self.sampling_sections):
            start_pos = i * section_size
            end_pos = min(start_pos + self.sampling_chars_per_section, text_length)
            sample_text = text[start_pos:end_pos]
            samples.append((start_pos, sample_text))
        return samples


# Default configuration using ADAPTIVE mode
DEFAULT_CONFIG = AnalysisConfig(mode=AnalysisMode.ADAPTIVE)
