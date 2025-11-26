"""
Shared pytest fixtures for AI Pattern Analyzer test suite.

This module provides:
- Sample text fixtures (AI-generated, human-written, mixed, edge cases)
- Mock fixtures for optional dependencies (marko, NLTK, spaCy, etc.)
- Utility fixtures for testing
"""


import pytest

# ============================================================================
# Sample Document Fixtures
# ============================================================================

@pytest.fixture
def sample_ai_text():
    """
    AI-generated text with typical AI patterns:
    - AI vocabulary (leverage, robust, delve, facilitate, etc.)
    - Formulaic transitions (Furthermore, Moreover)
    - Em-dashes
    - Verbose headings
    - Uniform structure
    - High bold/italic usage
    """
    return """# Leveraging Robust Solutions for Comprehensive Optimization

Furthermore, it is important to note that delving into holistic approaches
can facilitate seamless optimization. Moreover, harnessing innovative paradigms
provides a comprehensive framework for transformation — enabling organizations
to streamline processes effectively.

## Key Benefits of the Comprehensive Framework

The implementation of this robust solution facilitates several key advantages:

- **Streamline** critical processes
- **Optimize** existing workflows
- **Facilitate** desired outcomes
- **Leverage** strategic synergies

Furthermore, these benefits represent a holistic approach to organizational transformation.

## Advanced Implementation Strategies

Moreover, the strategic implementation of these solutions requires careful consideration
of various factors. It is important to *delve into* the nuances of each approach — ensuring
that every aspect is thoroughly optimized.

### Detailed Optimization Procedures

1. **Analyze** current state comprehensively
2. **Implement** robust solutions systematically
3. **Monitor** performance metrics continuously
4. **Refine** processes iteratively

## Comprehensive Conclusion

In conclusion, leveraging these comprehensive strategies facilitates optimal outcomes.
Furthermore, the holistic nature of this approach ensures robust implementation — ultimately
driving transformative results across all organizational levels.
"""


@pytest.fixture
def sample_human_text():
    """
    Human-written text with natural variation:
    - First-person pronouns
    - Contractions
    - Variable sentence lengths
    - Asymmetric structure
    - Lower bold/italic usage
    - Natural voice
    """
    return """# Getting Started

I've spent years working on this problem. You'll find the solution
surprisingly simple once you understand the core concept.

## What We Learned

Some sections were longer than others. We made mistakes. Short wins helped.

The first attempt didn't work. We tried three different approaches before
finding something that actually made sense. Here's what happened:

- Quick tests showed promise
- Longer analysis
- Brief validation

## The Real Challenge

You know what? The hardest part wasn't the technical stuff. It was convincing
people to try something new.

I remember sitting in that meeting, thinking "this'll never fly." But then
Sarah mentioned her team's experience. Game changer.

### Unexpected Results

Short section here.

### What Actually Worked

This section's much longer because there's more to say. We found that when
you combine the quick tests with the longer validation process, you get
something interesting. Not perfect, but interesting.

The results varied wildly. Some days we'd see 20% improvement. Other days? Nothing.
That's real data for you.

## Takeaways

- Try stuff
- Some things work, most don't
- Keep iterating

That's it. No magic formula.
"""


@pytest.fixture
def sample_mixed_text():
    """
    Mixed AI and human content showing both patterns.
    """
    return """# Project Overview

I've been working on this for three months now. Let me walk you through what we've learned.

## Comprehensive Framework Analysis

Furthermore, it is essential to delve into the holistic framework that facilitates
optimal outcomes. Moreover, leveraging robust methodologies ensures seamless integration
across all organizational touchpoints — providing comprehensive solutions for complex challenges.

### Key Implementation Strategies

- **Streamline** operational processes
- **Optimize** resource allocation
- **Facilitate** stakeholder engagement

## Real-World Experience

But here's the thing: none of that corporate speak actually worked in practice.

We tried the "comprehensive framework" approach. Total disaster. The team hated it,
customers were confused, and I spent two weeks undoing the mess.

What actually worked? Simple stuff:

- Quick daily check-ins
- Clear priorities (just three, max)
- Let people make decisions

Some days were great. Others? Not so much. That's how it goes.

## Conclusion

Furthermore, while theoretical frameworks facilitate understanding, practical experience
demonstrates that authentic, human-centered approaches ultimately yield superior results.

You'll figure it out. Just start.
"""


@pytest.fixture
def sample_edge_cases():
    """
    Edge case documents for testing robustness.
    """
    return {
        'empty': '',
        'single_sentence': 'This is one sentence.',
        'no_punctuation': 'word word word word word',
        'only_code': '```python\nprint("hello")\nprint("world")\n```',
        'only_headings': '# H1\n## H2\n### H3\n#### H4',
        'very_long': 'word ' * 10000,
        'only_lists': '- item 1\n- item 2\n- item 3',
        'malformed_markdown': '## No H1\n#### Skipped H3\n# H1 after H4',
        'unicode_text': 'Hello 世界 🌍 Привет мир',
        'excessive_formatting': '**bold** *italic* **bold** *italic* ' * 50,
        'single_paragraph': 'This is a single paragraph with multiple sentences. It has no structure. Just text. More text here. And here. Keep going. Almost done. Final sentence.',
    }


@pytest.fixture
def sample_text_with_em_dashes():
    """
    Text specifically designed to test em-dash detection.
    """
    return """# Testing Em-Dashes

This text uses em-dashes — the hallmark of AI-generated content — to show
how the analyzer detects them.

## More Em-Dashes

Furthermore, em-dashes can appear in various forms:
- The standard em-dash — like this
- The double-hyphen version -- like this
- Multiple uses — one after — another

Regular hyphens-like-this should not be counted.
"""


@pytest.fixture
def sample_text_with_headings():
    """
    Text with various heading structures for testing hierarchy analysis.
    """
    return """# Main Title

## First Section

### Subsection 1A

### Subsection 1B

### Subsection 1C

### Subsection 1D

## Second Section

### Subsection 2A

### Subsection 2B

## Third Section

### Only One Subsection Here

## Fourth Section

### Subsection 4A

### Subsection 4B

### Subsection 4C
"""


@pytest.fixture
def sample_text_with_lists():
    """
    Text with various list structures for testing list analysis.
    """
    return """# Lists Example

## Unordered Lists

- Item 1
- Item 2
  - Nested item 2a
  - Nested item 2b
    - Double nested item
- Item 3

## Ordered Lists

1. First item
2. Second item
3. Third item
   1. Nested ordered item
   2. Another nested item
4. Fourth item

## Mixed Lists

- Unordered item
- Another unordered item

1. Ordered item
2. Another ordered item

- Back to unordered
"""


# ============================================================================
# Note: All dependencies are now required (marko, nltk, spacy, textstat,
# transformers, scipy, textacy). Mock fixtures for unavailable dependencies
# have been removed.
# ============================================================================


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_analysis_result():
    """
    Provide a sample analysis result structure for testing scoring and visualization.
    """
    from writescore.core.results import (
        AnalysisResult,
        BurstinessResult,
        FormattingResult,
        PerplexityResult,
        StructureResult,
        VoiceResult,
    )

    return AnalysisResult(
        perplexity=PerplexityResult(
            ai_vocab_count=5,
            ai_vocab_per_1k=10.0,
            tier1_count=2,
            tier2_count=2,
            tier3_count=1,
            formulaic_transitions=3,
            domain_terms=1
        ),
        burstiness=BurstinessResult(
            sentence_length_std=5.5,
            avg_sentence_length=15.0,
            short_sentence_ratio=0.3,
            long_sentence_ratio=0.2
        ),
        formatting=FormattingResult(
            em_dash_count=4,
            bold_count=8,
            italic_count=6
        ),
        structure=StructureResult(
            heading_count=5,
            list_item_count=10,
            bullet_list_count=2,
            numbered_list_count=1
        ),
        voice=VoiceResult(
            first_person_count=2,
            contraction_count=3,
            direct_address_count=4
        ),
        lexical=None,
        syntactic=None,
        stylometric=None,
        advanced=None
    )


@pytest.fixture
def word_count():
    """Standard word count for testing."""
    return 500


@pytest.fixture
def page_count():
    """Standard page count for testing (250 words per page)."""
    return 2


# ============================================================================
# Test Isolation Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clear_dimension_registry():
    """
    Clear DimensionRegistry before each test to ensure test isolation.

    This fixture automatically runs before every test function to prevent
    cross-test contamination. Required when running full test suite.
    """
    from writescore.core.dimension_registry import DimensionRegistry
    DimensionRegistry.clear()
    yield
    # Optional: cleanup after test as well
    DimensionRegistry.clear()
