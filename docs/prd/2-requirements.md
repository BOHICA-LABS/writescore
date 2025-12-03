# 2. Requirements

## 2.1 Functional Requirements

- **FR1:** The system shall analyze Markdown text documents and produce scores across multiple linguistic dimensions
- **FR2:** The system shall calculate a dual score: Detection Risk (0-100, lower=better) and Quality Score (0-100, higher=better)
- **FR3:** The system shall support four analysis modes: FAST (truncated), ADAPTIVE (smart sampling), SAMPLING (configurable), and FULL (complete)
- **FR4:** The system shall provide detailed line-by-line diagnostics with context, problem identification, and specific replacement suggestions
- **FR5:** The system shall detect AI vocabulary patterns including "delve," "robust," "leverage," "harness," and 30+ other AI-typical words
- **FR6:** The system shall detect formatting patterns including em-dash overuse (10x more common in AI text than human)
- **FR7:** The system shall measure sentence burstiness (variation in sentence length) as a key human-vs-AI discriminator
- **FR8:** The system shall track score history across multiple editing iterations for a single document
- **FR9:** The system shall support batch analysis of all .md files in a directory
- **FR10:** The system shall output results in text, JSON, or TSV formats
- **FR11:** The system shall allow recalibration of scoring parameters from validation datasets
- **FR12:** The system shall support parameter version management (deploy, rollback, diff, versions)
- **FR13:** The system shall provide dimension profiles (fast/balanced/full) to control which dimensions are loaded
- **FR14:** The system shall allow custom domain-specific terms to be configured for technical writing analysis
- **FR15:** The system shall strip HTML comments (metadata blocks) before analysis to avoid false positives

## 2.2 Non-Functional Requirements

- **NFR1:** FAST mode shall complete analysis in 5-15 seconds for any document size
- **NFR2:** ADAPTIVE mode shall complete analysis in 30-240 seconds for book-chapter-length documents (~90 pages)
- **NFR3:** FULL mode may take 5-20 minutes for large documents but shall analyze 100% of content
- **NFR4:** The system shall support Python 3.9, 3.10, 3.11, and 3.12
- **NFR5:** The system shall be installable via `pip install -e .` with optional dependency groups (dev, ml)
- **NFR6:** The scoring convention shall use 0-100 scale where 100 = most human-like consistently across all dimensions
- **NFR7:** The system shall provide meaningful results for documents as short as 50 characters
- **NFR8:** The system shall handle documents up to 500,000+ characters (book-length) via sampling modes
- **NFR9:** Dimension analyzers shall self-register via the DimensionRegistry pattern for extensibility
- **NFR10:** The CLI shall provide interactive confirmation for FULL mode on large documents (>500k chars)
- **NFR11:** The system shall maintain backward compatibility with existing `.ai-analysis-history` files
- **NFR12:** The system shall support existing parameter file formats (JSON and YAML)
- **NFR13:** CLI command structure shall remain stable (`writescore analyze`, `writescore recalibrate`)

---
