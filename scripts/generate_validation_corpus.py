#!/usr/bin/env python3
"""
Validation Corpus Generator for Story 2.4.1 (AC8)

Purpose:
    Generate a 500+ document validation corpus (250 human, 250 AI) across multiple
    domains for computing dimension statistics and validating scoring optimization.

Usage:
    python scripts/generate_validation_corpus.py --output validation_corpus/

Requirements:
    - Internet connection for fetching human-written content
    - API keys for AI generation (set in environment)
    - At least 5GB disk space for corpus storage

Created: 2025-11-24
Story: 2.4.1 (Dimension Scoring Optimization)
"""

import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationCorpusGenerator:
    """
    Generates a validation corpus for WriteScore dimension scoring optimization.

    Corpus Structure:
        validation_corpus/
          human/
            academic/        (50 docs: research papers, essays)
            social/          (50 docs: blog posts, social media)
            business/        (50 docs: reports, emails, presentations)
            technical/       (50 docs: documentation, tutorials)
            creative/        (50 docs: articles, narratives, editorials)
          ai/
            academic/        (50 docs: ChatGPT, Claude, etc.)
            social/          (50 docs)
            business/        (50 docs)
            technical/       (50 docs)
            creative/        (50 docs)
          metadata.json      (corpus metadata and statistics)
    """

    DOMAINS = ['academic', 'social', 'business', 'technical', 'creative']
    DOCS_PER_DOMAIN = 50
    MIN_WORD_COUNT = 200
    MAX_WORD_COUNT = 1000

    def __init__(self, output_dir: Path, use_mock: bool = False):
        """
        Initialize corpus generator.

        Args:
            output_dir: Base directory for corpus storage
            use_mock: If True, generate mock/placeholder content for testing
        """
        self.output_dir = Path(output_dir)
        self.use_mock = use_mock
        self.metadata: Dict = {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'story': '2.4.1',
            'purpose': 'Validation corpus for dimension scoring optimization',
            'total_documents': 0,
            'human_documents': 0,
            'ai_documents': 0,
            'domains': {},
            'sources': []
        }

        # Create directory structure
        self._create_directories()

    def _create_directories(self) -> None:
        """Create corpus directory structure."""
        for author_type in ['human', 'ai']:
            for domain in self.DOMAINS:
                dir_path = self.output_dir / author_type / domain
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")

    def generate_corpus(self) -> None:
        """Generate complete validation corpus (500+ documents)."""
        logger.info("Starting validation corpus generation...")
        logger.info(f"Target: {len(self.DOMAINS) * self.DOCS_PER_DOMAIN * 2} documents")

        # Generate human-written documents
        logger.info("\n=== Generating Human-Written Documents ===")
        for domain in self.DOMAINS:
            self._generate_human_documents(domain, self.DOCS_PER_DOMAIN)

        # Generate AI-written documents
        logger.info("\n=== Generating AI-Written Documents ===")
        for domain in self.DOMAINS:
            self._generate_ai_documents(domain, self.DOCS_PER_DOMAIN)

        # Save metadata
        self._save_metadata()

        logger.info(f"\n✅ Corpus generation complete!")
        logger.info(f"   Total documents: {self.metadata['total_documents']}")
        logger.info(f"   Human: {self.metadata['human_documents']}")
        logger.info(f"   AI: {self.metadata['ai_documents']}")
        logger.info(f"   Output: {self.output_dir}")

    def _generate_human_documents(self, domain: str, count: int) -> None:
        """
        Generate human-written documents for a domain.

        Strategy:
            - Academic: Research paper excerpts, educational essays
            - Social: Blog posts, forum discussions, social media threads
            - Business: Reports, memos, case studies
            - Technical: Documentation, tutorials, code explanations
            - Creative: Articles, narratives, opinion pieces

        Sources:
            - Wikipedia articles (CC-BY-SA)
            - Project Gutenberg books (public domain)
            - ArXiv papers (open access)
            - Stack Overflow posts (CC-BY-SA)
            - News articles via APIs
        """
        logger.info(f"Generating {count} human {domain} documents...")

        for i in range(count):
            try:
                if self.use_mock:
                    # Generate mock content for testing
                    content, source = self._generate_mock_human_content(domain, i)
                else:
                    # Fetch real human-written content
                    content, source = self._fetch_human_content(domain)

                # Save document
                doc_id = self._save_document('human', domain, i, content, source)

                if (i + 1) % 10 == 0:
                    logger.info(f"  Generated {i + 1}/{count} human {domain} documents")

            except Exception as e:
                logger.error(f"Failed to generate human {domain} document {i}: {e}")
                continue

        self.metadata['human_documents'] += count

    def _generate_ai_documents(self, domain: str, count: int) -> None:
        """
        Generate AI-written documents for a domain.

        Strategy:
            Use multiple AI models to generate diverse content:
            - OpenAI GPT-4 (if API key available)
            - Claude (if API key available)
            - Local models (if available)
            - Fallback to mock generation for testing

        Prompts tailored per domain to match human document style.
        """
        logger.info(f"Generating {count} AI {domain} documents...")

        for i in range(count):
            try:
                if self.use_mock:
                    # Generate mock AI content
                    content, source = self._generate_mock_ai_content(domain, i)
                else:
                    # Generate AI content using available APIs
                    content, source = self._generate_ai_content(domain)

                # Save document
                doc_id = self._save_document('ai', domain, i, content, source)

                if (i + 1) % 10 == 0:
                    logger.info(f"  Generated {i + 1}/{count} AI {domain} documents")

            except Exception as e:
                logger.error(f"Failed to generate AI {domain} document {i}: {e}")
                continue

        self.metadata['ai_documents'] += count

    def _fetch_human_content(self, domain: str) -> Tuple[str, str]:
        """
        Fetch real human-written content from appropriate sources.

        Returns:
            (content, source_name) tuple
        """
        # This would implement actual fetching from various sources
        # For now, return mock content with a note
        logger.warning("Real human content fetching not yet implemented - using mock")
        return self._generate_mock_human_content(domain, 0)

    def _generate_ai_content(self, domain: str) -> Tuple[str, str]:
        """
        Generate AI content using available AI APIs.

        Returns:
            (content, model_name) tuple
        """
        # This would implement actual AI generation
        # For now, return mock content with a note
        logger.warning("Real AI content generation not yet implemented - using mock")
        return self._generate_mock_ai_content(domain, 0)

    def _generate_mock_human_content(self, domain: str, index: int) -> Tuple[str, str]:
        """Generate mock human-written content for testing."""
        templates = {
            'academic': self._mock_academic_human,
            'social': self._mock_social_human,
            'business': self._mock_business_human,
            'technical': self._mock_technical_human,
            'creative': self._mock_creative_human
        }

        # Get base content
        base_content = templates[domain](index)
        content = base_content
        word_count = len(content.split())

        # Ensure meets word count requirements
        while word_count < self.MIN_WORD_COUNT:
            content += " " + base_content
            word_count = len(content.split())

        # Truncate to max limit
        final_content = content[:self._calculate_char_limit()]
        return final_content, "mock_human_generator"

    def _generate_mock_ai_content(self, domain: str, index: int) -> Tuple[str, str]:
        """Generate mock AI-written content with typical AI characteristics."""
        templates = {
            'academic': self._mock_academic_ai,
            'social': self._mock_social_ai,
            'business': self._mock_business_ai,
            'technical': self._mock_technical_ai,
            'creative': self._mock_creative_ai
        }

        # Get base content
        base_content = templates[domain](index)
        content = base_content
        word_count = len(content.split())

        # Ensure meets word count requirements
        while word_count < self.MIN_WORD_COUNT:
            content += " " + base_content
            word_count = len(content.split())

        # Truncate to max limit
        final_content = content[:self._calculate_char_limit()]
        return final_content, "mock_ai_generator"

    def _calculate_char_limit(self) -> int:
        """Calculate character limit to approximate MAX_WORD_COUNT."""
        # Average English word is ~5 characters + 1 space
        return self.MAX_WORD_COUNT * 6

    # Mock content generators (human-like)

    def _mock_academic_human(self, index: int) -> str:
        """Generate mock human academic text."""
        return f"""This research examines the relationship between cognitive load and learning
outcomes in digital environments. Prior studies have shown mixed results, with some
researchers finding positive correlations while others report no significant effect.
Our study addresses these inconsistencies by controlling for multiple confounding
variables that previous work overlooked. We recruited 120 participants and randomly
assigned them to three experimental conditions. The results suggest that moderate
cognitive load enhances retention, but excessive load impairs performance. These
findings have implications for instructional design in online education."""

    def _mock_social_human(self, index: int) -> str:
        """Generate mock human social media style text."""
        return f"""Just finished reading this incredible book and I can't stop thinking
about it! The author's writing style is so unique - it's like she gets inside your head
and makes you question everything you thought you knew. Has anyone else read it? I'd
love to hear your thoughts! The ending totally blindsided me (no spoilers though).
Honestly, it's one of those rare books that stays with you long after you've turned
the last page. Already recommended it to all my friends. What are you all reading
these days? Need some new recommendations!"""

    def _mock_business_human(self, index: int) -> str:
        """Generate mock human business writing."""
        return f"""Following up on our discussion from yesterday's meeting, I wanted to
share some thoughts on the Q4 strategy. Looking at the numbers, we're seeing stronger
than expected growth in the EMEA region, which is great news. However, the APAC
numbers are a bit concerning - down 12% from last quarter. I think we need to
reconsider our pricing strategy there. Can we schedule a call next week to dive
deeper into this? I'd like to get Sarah's input too since she's been working closely
with the regional teams. Let me know what times work for everyone."""

    def _mock_technical_human(self, index: int) -> str:
        """Generate mock human technical writing."""
        return f"""To set up the development environment, first clone the repository and
install the dependencies. You'll need Python 3.8 or higher. Run 'pip install -r
requirements.txt' to get everything set up. The config file is in the root directory
- you'll want to update the API keys and database credentials. If you run into issues
with the database connection, check that PostgreSQL is running on port 5432. Common
gotcha: make sure your virtual environment is activated before installing packages.
Once everything's configured, run the test suite to verify your setup."""

    def _mock_creative_human(self, index: int) -> str:
        """Generate mock human creative writing."""
        return f"""The rain had been falling for three days straight. Sarah watched the
droplets race down the window, each one following its own unpredictable path. She
thought about calling him, but what would she say? The words had all been spoken
already, hadn't they? Sometimes silence speaks louder than any explanation ever could.
She picked up her phone, set it down again. Outside, a car splashed through a puddle,
sending up a spray of water that caught the streetlight. Beautiful, in a melancholy
sort of way. Everything felt melancholy these days."""

    # Mock content generators (AI-like - with typical AI characteristics)

    def _mock_academic_ai(self, index: int) -> str:
        """Generate mock AI academic text with typical AI patterns."""
        return f"""It is important to note that the field of cognitive psychology has
demonstrated significant advances in recent years. Researchers have increasingly
focused on understanding the complex interplay between various cognitive processes.
This comprehensive approach allows for a more nuanced understanding of how learning
occurs in digital environments. Furthermore, it is worth mentioning that multiple
factors contribute to learning outcomes, including but not limited to cognitive load,
motivation, and prior knowledge. By carefully examining these variables, we can
better optimize educational interventions to enhance student success."""

    def _mock_social_ai(self, index: int) -> str:
        """Generate mock AI social media style text."""
        return f"""I recently had the pleasure of reading an absolutely fascinating book
that truly changed my perspective on this important topic. The author skillfully
weaves together compelling narratives that resonate deeply with readers. It is clear
that this work represents a significant contribution to the field. I would highly
recommend this book to anyone interested in exploring these themes. The insights
presented are both thought-provoking and accessible. Overall, it is a must-read that
offers valuable perspectives on contemporary issues. I look forward to engaging in
discussions about this important work."""

    def _mock_business_ai(self, index: int) -> str:
        """Generate mock AI business writing."""
        return f"""Upon careful review of the quarterly performance metrics, several key
insights emerge that warrant further discussion. It is important to note that the
EMEA region has demonstrated strong growth patterns, which is certainly encouraging.
However, it is also worth noting that the APAC region presents certain challenges
that require our attention. Moving forward, it would be beneficial to conduct a
comprehensive analysis of our pricing strategies in order to optimize our market
position. Additionally, collaboration with regional teams will be essential for
developing effective solutions."""

    def _mock_technical_ai(self, index: int) -> str:
        """Generate mock AI technical writing."""
        return f"""To successfully configure the development environment, it is important
to follow these comprehensive steps. First, you will need to clone the repository
from the version control system. Next, ensure that all necessary dependencies are
properly installed by executing the package manager commands. It is worth noting that
the configuration file contains important parameters that must be updated according
to your specific environment requirements. Furthermore, it is essential to verify
that all services are running correctly before proceeding with development activities.
By following these guidelines, you can ensure a smooth setup process."""

    def _mock_creative_ai(self, index: int) -> str:
        """Generate mock AI creative writing."""
        return f"""The persistent rainfall had continued unabated for a considerable
duration. As Sarah observed the window, she contemplated the various droplets as
they descended along the glass surface. She found herself considering the possibility
of reaching out, yet uncertainty clouded her judgment regarding the appropriate words
to express. It seemed that all meaningful communication had already transpired. In
certain situations, the absence of sound can convey more profound messages than any
verbal articulation. The sight of the streetlight illuminating the water created an
aesthetically pleasing, albeit somewhat melancholic, visual experience."""

    def _save_document(
        self,
        author_type: str,
        domain: str,
        index: int,
        content: str,
        source: str
    ) -> str:
        """
        Save document to corpus with metadata.

        Returns:
            Document ID (hash)
        """
        # Generate unique document ID
        doc_id = hashlib.md5(
            f"{author_type}_{domain}_{index}_{source}".encode()
        ).hexdigest()[:12]

        # Create document metadata
        doc_metadata = {
            'id': doc_id,
            'author_type': author_type,
            'domain': domain,
            'source': source,
            'word_count': len(content.split()),
            'char_count': len(content),
            'created': datetime.now().isoformat()
        }

        # Save content
        filename = f"{doc_id}.txt"
        filepath = self.output_dir / author_type / domain / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Save metadata
        metadata_filename = f"{doc_id}.json"
        metadata_filepath = self.output_dir / author_type / domain / metadata_filename

        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_metadata, f, indent=2)

        # Update corpus metadata
        if domain not in self.metadata['domains']:
            self.metadata['domains'][domain] = {'human': 0, 'ai': 0}

        self.metadata['domains'][domain][author_type] += 1
        self.metadata['total_documents'] += 1

        if source not in self.metadata['sources']:
            self.metadata['sources'].append(source)

        return doc_id

    def _save_metadata(self) -> None:
        """Save corpus metadata."""
        metadata_path = self.output_dir / 'metadata.json'

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Saved corpus metadata to {metadata_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate validation corpus for WriteScore dimension scoring optimization'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('validation_corpus'),
        help='Output directory for corpus (default: validation_corpus/)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock/placeholder content for testing (default: False)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Generate corpus
    generator = ValidationCorpusGenerator(
        output_dir=args.output,
        use_mock=args.mock
    )

    try:
        generator.generate_corpus()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Corpus generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Corpus generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
