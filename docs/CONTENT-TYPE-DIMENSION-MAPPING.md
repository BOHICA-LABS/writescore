# Content Type Dimension Mapping

**Version:** 1.0.0
**Status:** Research-Based Framework
**Purpose:** Map AI pattern analyzer dimensions to content types with expected ranges and recommendations

## Executive Summary

Different content types have inherently different linguistic characteristics. A professional bio *should* be factually neutral (low sentiment variance), while a personal statement *should* have emotional variation (high sentiment variance). This document maps our 13 dimensions to 9 content types with expected ranges, dimension relevance weighting, and recommendations for new dimensions.

**Key Findings:**
- Current analyzer penalizes professional bios for characteristics that are actually genre-appropriate (e.g., POOR sentiment score for 0.000 variance, when bios should be neutral)
- Technical books (Manning, Packt, O'Reilly) are distinct from technical documentation - they require accessibility (Flesch 50-70), engagement (sentiment variance 0.100-0.250), and conversational elements that would be inappropriate for API docs

---

## Content Type Taxonomy

Based on multidimensional analysis research (Biber et al.), we identify 9 primary content types:

1. **Academic Writing** - Scholarly papers, research articles, dissertations
2. **Professional Bios** - Third-person professional descriptions, author bios
3. **Personal Statements** - First-person narrative, application essays
4. **Blog Posts** - Informal, conversational, consumer-oriented
5. **Technical Documentation** - User manuals, API docs, specifications
6. **Technical Books** - Instructional technical books (Manning, Packt, O'Reilly)
7. **Business Writing** - Memos, reports, proposals, emails
8. **Creative Writing** - Fiction, narrative journalism, storytelling
9. **News/Journalism** - Objective reporting, inverted pyramid structure

### Technical Books vs Technical Documentation

**Technical Books** (Manning, Packt, O'Reilly) are distinct from **Technical Documentation**:

| Characteristic | Technical Docs (API/Manual) | Technical Books (Manning/Packt) |
|----------------|----------------------------|--------------------------------|
| **Purpose** | Reference, quick lookup | Learning, comprehensive understanding |
| **Length** | 10-100 pages | 300-800 pages |
| **Tone** | Imperative, definitive | Conversational, engaging |
| **Examples** | Minimal code snippets | War stories, real-world scenarios |
| **Voice** | 2nd person only | Mixed 1st (examples) + 2nd (instructions) |
| **Emotion** | None (neutral) | Enthusiasm appropriate |
| **Structure** | Formulaic OK (scannable) | Formulaic BAD (repetitive) |

Technical books blend characteristics from multiple genres:
- **40%** Technical Documentation (precision, accuracy)
- **25%** Blog Posts (accessibility, engagement)
- **20%** Academic Writing (depth, expertise)
- **15%** Instructional Design (learning progression)

---

## Dimension-to-Content-Type Mapping

### 1. Perplexity (Vocabulary Complexity)

**Current Implementation:** Detects AI vocabulary (leverage, optimize, delve, etc.)

| Content Type | Expected Range | Importance | Notes |
|-------------|----------------|------------|-------|
| Academic | 0-2 AI words/1k | HIGH | Should use discipline-specific terminology, not AI buzzwords |
| Professional Bio | 0-1 AI words/1k | MEDIUM | Avoid corporate jargon like "optimization" |
| Personal Statement | 0 AI words/1k | HIGH | Should be authentic, conversational |
| Blog Posts | 0 AI words/1k | HIGH | Deliberate accessibility, avoiding jargon |
| Technical Docs | 0-1 AI words/1k | MEDIUM | Use precise technical terms, not AI vocabulary |
| **Technical Books** | **0-1 AI words/1k** | **HIGH** | **Accessible explanation, avoid "optimize/leverage/delve"** |
| Business Writing | 0-3 AI words/1k | LOW | May appropriately use "strategic," "leverage" |
| Creative Writing | 0 AI words/1k | HIGH | Natural language, avoiding buzzwords |
| News/Journalism | 0 AI words/1k | HIGH | Plain language, AP style |

**Recommendation:** KEEP dimension as-is. Works well across all content types.

---

### 2. Burstiness (Sentence Variation)

**Current Implementation:** Measures sentence length variance (σ/μ ratio)

| Content Type | Expected σ (StdDev) | Expected μ (Mean) | Burstiness Target | Importance |
|-------------|---------------------|-------------------|-------------------|------------|
| Academic | 6-10 | 20-25 | MODERATE | MEDIUM |
| Professional Bio | 5-9 | 15-20 | MODERATE | MEDIUM |
| Personal Statement | 8-12 | 10-18 | **HIGH** | **HIGH** |
| Blog Posts | 6-10 | 12-18 | MODERATE-HIGH | HIGH |
| Technical Docs | 3-5 | 10-15 | **LOW** | LOW |
| **Technical Books** | **6-10** | **12-18** | **MODERATE-HIGH** | **HIGH** |
| Business Writing | 5-8 | 15-20 | MODERATE | MEDIUM |
| Creative Writing | 10-15 | 12-20 | **VERY HIGH** | **HIGH** |
| News/Journalism | 4-7 | 15-22 | LOW-MODERATE | LOW |

**Issue:** Current implementation penalizes technical docs and news for appropriate uniformity.

**Recommendation:** ADD content-type parameter to adjust scoring thresholds. Technical books need variation for engagement over 300+ pages.

---

### 3. Sentiment (Emotional Variation)

**Current Implementation:** RoBERTa sentiment variance and mean

| Content Type | Expected Variance | Expected Mean | Importance | Notes |
|-------------|-------------------|---------------|------------|-------|
| Academic | 0.000-0.100 | 0.90-1.00 | **LOW** | Should be neutral/objective |
| Professional Bio | 0.000-0.050 | 0.95-1.00 | **LOW** | Should be factual/neutral |
| Personal Statement | 0.500-0.950 | 0.00-0.50 | **CRITICAL** | Must show emotional authenticity |
| Blog Posts | 0.200-0.600 | 0.20-0.80 | HIGH | Conversational, emotionally engaging |
| Technical Docs | 0.000-0.020 | 0.98-1.00 | **IRRELEVANT** | Should be completely neutral |
| **Technical Books** | **0.100-0.250** | **0.70-0.90** | **MEDIUM** | **Enthusiasm appropriate, not flat** |
| Business Writing | 0.050-0.300 | 0.70-0.95 | MEDIUM | Professional but may include urgency |
| Creative Writing | 0.600-0.950 | 0.00-0.60 | **CRITICAL** | Emotional arcs essential |
| News/Journalism | 0.000-0.100 | 0.90-1.00 | LOW | Objective reporting |

**CRITICAL ISSUE:** Current analyzer scores Professional Bio with 0.000 variance as POOR (12.8 pt penalty), when this is **genre-appropriate**.

**Recommendation:**
1. ADD content-type weighting: sentiment dimension should have ZERO weight for Professional Bios, Technical Docs, Academic Writing
2. INCREASE weight to 20% for Personal Statements and Creative Writing
3. CREATE "neutrality score" for fact-based content types (inverse of sentiment variance)
4. Technical books SHOULD show some enthusiasm (0.100-0.250) to maintain reader engagement over 300+ pages

---

### 4. Readability (Flesch-Kincaid)

**Current Implementation:** Flesch Reading Ease, Grade Level, Gunning Fog, SMOG

| Content Type | Target Flesch | Target Grade | Gunning Fog | Importance | Notes |
|-------------|---------------|--------------|-------------|------------|-------|
| Academic | -5 to 30 | 15-18+ | 18-22 | MEDIUM | Post-graduate level appropriate |
| Professional Bio | 40-60 | 10-14 | 14-18 | MEDIUM | Accessible to professional audience |
| Personal Statement | 50-70 | 8-12 | 10-14 | HIGH | Should be clear, engaging |
| Blog Posts | 60-80 | 6-8 | 8-12 | **CRITICAL** | 8th-grade level target |
| Technical Docs | 40-60 | 10-14 | 12-16 | MEDIUM | Clear despite technical content |
| **Technical Books** | **50-70** | **9-12** | **12-16** | **CRITICAL** | **Must be accessible for learning** |
| Business Writing | 50-70 | 8-12 | 10-14 | HIGH | Accessible to general business audience |
| Creative Writing | 60-90 | 6-10 | 8-14 | MEDIUM | Varies by target audience |
| News/Journalism | 60-70 | 8-10 | 10-12 | HIGH | General public accessibility |

**Issue:** Current implementation penalizes Academic (Flesch: -5.29) and Professional Bios (Flesch: 12.48) for genre-appropriate complexity.

**Recommendation:**
1. ADD content-type thresholds with different scoring curves
2. Academic writing should score HIGH for Flesch 20-40, POOR for Flesch >60
3. Blog posts should score HIGH for Flesch 60-80, POOR for Flesch <40
4. Technical books CRITICAL for accessibility - readers must comprehend to learn, not just reference

---

### 5. Structure (Organization)

**Current Implementation:** Detects formulaic transitions, heading depth

| Content Type | Formulaic OK? | Heading Depth | Importance | Notes |
|-------------|---------------|---------------|------------|-------|
| Academic | YES | 3-4 | MEDIUM | IMRAD structure is conventional |
| Professional Bio | NO | 0-1 | LOW | Typically no headings |
| Personal Statement | NO | 0-1 | LOW | Narrative flow, no headings |
| Blog Posts | MAYBE | 2-3 | MEDIUM | Subheadings for scannability |
| Technical Docs | **YES** | 4-6 | **LOW** | Standard templates EXPECTED |
| **Technical Books** | **NO** | **3-4** | **MEDIUM** | **Repetitive chapter patterns = AI-like** |
| Business Writing | SOMETIMES | 2-3 | LOW | Depends on document type |
| Creative Writing | NO | 0-2 | LOW | Narrative structure |
| News/Journalism | YES | 1-2 | LOW | Inverted pyramid is standard |

**Issue:** Penalizes technical docs for appropriate formulaic structure.

**Recommendation:** Make formulaic transitions POSITIVE for Technical Docs and Academic Writing, NEGATIVE for Personal/Creative/Technical Books. Books need varied chapter structures to avoid monotony.

---

### 6. Voice (Authenticity)

**Current Implementation:** First-person count, contractions, direct address

| Content Type | 1st Person | Contractions | Direct Address | Importance |
|-------------|------------|--------------|----------------|------------|
| Academic | 0-5 | 0-2 | NO | MEDIUM |
| Professional Bio | 10-20 (1st) or 0 (3rd) | 0-5 | NO | MEDIUM |
| Personal Statement | 20-40 | 10-20 | MAYBE | **CRITICAL** |
| Blog Posts | 15-30 | 15-30 | **YES** | **HIGH** |
| Technical Docs | 0-2 | 0-5 | YES (imperative) | LOW |
| **Technical Books** | **15-30 (mixed)** | **10-20** | **YES (you)** | **HIGH** |
| Business Writing | 10-25 | 5-15 | **YES** | HIGH |
| Creative Writing | VARIES | 10-40 | VARIES | MEDIUM |
| News/Journalism | 0-2 | 0-5 | NO | MEDIUM |

**Issue:** First-person and contractions have opposite expectations across genres.

**Recommendation:**
1. SPLIT voice dimension into "Academic Voice" and "Personal Voice" subdimensions
2. Score based on genre-appropriate usage
3. ADD "person consistency" metric (mixing 1st/3rd is AI tell)
4. Technical books SHOULD mix 1st person (examples/war stories) + 2nd person (instructions) appropriately

---

### 7. Advanced Lexical (Diversity)

**Current Implementation:** HDD, Yule's K, MATTR (requires 500+ words)

| Content Type | Expected HDD | Expected Yule's K | Importance | Notes |
|-------------|--------------|-------------------|------------|-------|
| Academic | 0.75-0.90 | 80-150 | HIGH | Specialized vocabulary |
| Professional Bio | 0.70-0.85 | 100-200 | MEDIUM | Varied accomplishment descriptions |
| Personal Statement | 0.65-0.80 | 120-180 | MEDIUM | Authentic vocabulary variation |
| Blog Posts | 0.60-0.75 | 150-250 | LOW | Conversational repetition OK |
| Technical Docs | 0.65-0.80 | 100-180 | MEDIUM | Precise terminology repetition |
| **Technical Books** | **0.75-0.85** | **100-180** | **HIGH** | **Rich explanations, varied examples** |
| Business Writing | 0.70-0.85 | 120-200 | MEDIUM | Professional vocabulary |
| Creative Writing | 0.75-0.90 | 80-150 | **HIGH** | Rich descriptive language |
| News/Journalism | 0.65-0.80 | 130-200 | MEDIUM | Clear, varied reporting |

**Issue:** N/A for documents <500 words (affects bios, personal statements).

**Recommendation:** IMPLEMENT Story 2.7 TTR-based approximations for short content.

---

### 8. Transition Markers (Pragmatic Discourse)

**Current Implementation:** Detects 31 pragmatic patterns (I think, might, could, etc.)

| Content Type | Expected Count | Importance | Notes |
|-------------|----------------|------------|-------|
| Academic | 0-2 | LOW | Hedging inappropriate in formal writing |
| Professional Bio | 0-1 | LOW | Should be confident, factual |
| Personal Statement | 3-8 | **CRITICAL** | Shows authentic thought process |
| Blog Posts | 5-12 | **HIGH** | Conversational engagement |
| Technical Docs | 0-1 | **IRRELEVANT** | Instructions should be definitive |
| **Technical Books** | **3-7** | **MEDIUM** | **Conversational scaffolding, relatability** |
| Business Writing | 2-6 | MEDIUM | Strategic hedging acceptable |
| Creative Writing | 4-10 | MEDIUM | Character voice, internal dialogue |
| News/Journalism | 0-2 | LOW | Objective reporting |

**Recommendation:** ADJUST weighting by content type. Essential for personal writing, irrelevant for technical docs. Technical books benefit from conversational markers for engagement.

---

### 9. Figurative Language

**Current Implementation:** Detects idioms, metaphors, similes from 6030-idiom lexicon

| Content Type | Expected Frequency | Importance | Notes |
|-------------|-------------------|------------|-------|
| Academic | 50-150/1k | LOW | Minimal metaphorical language |
| Professional Bio | 100-250/1k | LOW | Some idiomatic expressions |
| Personal Statement | 200-400/1k | MEDIUM | Vivid imagery expected |
| Blog Posts | 250-450/1k | **HIGH** | Engaging, relatable language |
| Technical Docs | 20-100/1k | **IRRELEVANT** | Literal precision required |
| **Technical Books** | **150-300/1k** | **HIGH** | **Metaphors aid learning, relatability** |
| Business Writing | 150-350/1k | MEDIUM | Persuasive metaphors |
| Creative Writing | 300-600/1k | **CRITICAL** | Rich figurative language |
| News/Journalism | 100-250/1k | MEDIUM | Narrative journalism uses more |

**Recommendation:** Current implementation is good. Adjust importance weighting by content type. Technical books rely on metaphors/analogies for teaching complex concepts.

---

## Proposed New Dimensions by Content Type

### 1. Register Consistency Dimension

**Rationale:** Research shows register shifts are major AI tell across all content types.

**Measurement:**
- Track formality level across sentences
- Detect inappropriate register shifts (formal→informal→formal)
- Measure vocabulary formality consistency

**Expected by Content Type:**
- Academic: HIGH consistency (formal throughout)
- Professional Bio: HIGH consistency (formal or semi-formal)
- Personal Statement: MODERATE consistency (authentic voice may vary)
- Blog Posts: MODERATE-HIGH consistency (conversational throughout)
- Technical Docs: **VERY HIGH** consistency (formal, imperative)
- Creative Writing: LOW consistency (intentional variation for effect)

**Implementation Priority:** HIGH (universal applicability)

---

### 2. Person Consistency Dimension

**Rationale:** Mixing first-person and third-person is strong AI indicator.

**Measurement:**
- Detect switches between 1st/2nd/3rd person
- Flag inappropriate passive voice usage
- Measure perspective consistency

**Expected by Content Type:**
- Professional Bio: EITHER 1st OR 3rd, never mixed
- Academic: Consistent 3rd person
- Personal Statement: Consistent 1st person
- Technical Docs: Consistent 2nd person (imperative) or 3rd

**Implementation Priority:** MEDIUM-HIGH

---

### 3. Paragraph Purpose Dimension

**Rationale:** AI often creates "decorative" paragraphs that don't advance argument.

**Measurement:**
- Classify paragraphs as: introduction, evidence, analysis, transition, conclusion
- Detect sequences of purely transitional paragraphs
- Measure information density per paragraph

**Expected by Content Type:**
- Academic: Clear IMRAD structure with distinct paragraph purposes
- Blog Posts: Short intro → body → call-to-action pattern
- News: Inverted pyramid (most important first)

**Implementation Priority:** MEDIUM (computationally expensive)

---

### 4. Citation/Evidence Patterns

**Rationale:** Academic and professional writing should cite sources appropriately.

**Measurement:**
- Detect citation markers ([1], footnotes, author-year)
- Measure claim-to-evidence ratio
- Flag unsupported assertions

**Content Type Applicability:**
- Academic: CRITICAL (should have citations)
- Professional Bio: IRRELEVANT (no citations expected)
- Personal Statement: IRRELEVANT
- News/Journalism: MEDIUM (should attribute sources)

**Implementation Priority:** LOW (narrow applicability)

---

### 5. Lexical Inflation Dimension

**Rationale:** AI uses more difficult vocabulary than humans (26% higher difficulty).

**Measurement:**
- Average word difficulty rating
- Ratio of complex to simple synonyms
- Inappropriate vocabulary sophistication for audience

**Expected by Content Type:**
- Academic: HIGH difficulty appropriate
- Professional Bio: MEDIUM difficulty
- Blog Posts: **LOW** difficulty (8th-grade target)
- Personal Statement: MEDIUM difficulty
- Technical Docs: HIGH *precision*, not complexity

**Implementation Priority:** HIGH (research-proven AI marker)

---

### 6. Content vs Function Word Ratio

**Rationale:** AI uses 15% more content words than humans.

**Measurement:**
- Ratio of nouns/verbs/adjectives (content) to articles/prepositions/conjunctions (function)
- Expected ratios vary by genre

**Expected Ranges:**
- Academic: 0.55-0.65 (higher content words)
- Creative Writing: 0.45-0.55 (more descriptive function words)
- Technical Docs: 0.60-0.70 (precise content words)

**Implementation Priority:** MEDIUM (good discriminator)

---

### 7. Formulaic Language Appropriateness

**Rationale:** Some genres REQUIRE formulaic language (technical docs), others forbid it (creative).

**Measurement:**
- Detect template phrases by content type
- Score appropriateness contextually

**Examples:**
- Technical Docs: "Click the button" = GOOD (standard)
- Personal Statement: "Throughout my career" = POOR (cliché)
- Academic: "The results suggest that" = GOOD (conventional)

**Implementation Priority:** HIGH (context-dependent scoring critical)

---

## Implementation Recommendations

### Phase 1: Content Type Detection (Story 3.1)

**Priority:** CRITICAL
**Effort:** 2-3 days

Create content type classifier that:
1. Accepts user-specified content type via CLI flag: `--content-type academic`
2. Auto-detects content type using features:
   - First-person pronoun frequency
   - Citation markers presence
   - Heading structure
   - Formality indicators
   - Average Flesch score
3. Returns confidence score for classification

**Example:**
```python
def detect_content_type(text: str) -> Tuple[str, float]:
    """
    Detect content type from text features.

    Returns:
        (content_type, confidence_score)

    Content types: academic, bio, personal_statement, blog,
                   technical_docs, technical_book, business,
                   creative, journalism
    """
```

---

### Phase 2: Content-Aware Dimension Weighting (Story 3.2)

**Priority:** CRITICAL
**Effort:** 3-4 days

Implement dimension weight adjustment by content type:

```python
CONTENT_TYPE_WEIGHTS = {
    'academic': {
        'sentiment': 0.0,  # Irrelevant
        'readability': 0.05,  # Low complexity is BAD
        'advanced_lexical': 0.15,  # Important
        'structure': 0.10,  # Formulaic is GOOD
    },
    'professional_bio': {
        'sentiment': 0.0,  # Should be neutral
        'readability': 0.10,
        'burstiness': 0.08,
        'voice': 0.12,
    },
    'personal_statement': {
        'sentiment': 0.20,  # CRITICAL
        'voice': 0.15,  # CRITICAL
        'transition_marker': 0.12,  # Important
        'readability': 0.10,
    },
    'technical_book': {
        'readability': 0.15,  # CRITICAL - must be accessible for learning
        'burstiness': 0.12,  # HIGH - varied for engagement
        'perplexity': 0.10,  # HIGH - avoid AI buzzwords
        'advanced_lexical': 0.12,  # HIGH - rich explanations
        'figurative_language': 0.12,  # HIGH - metaphors aid learning
        'voice': 0.10,  # HIGH - mixed 1st/2nd appropriate
        'sentiment': 0.08,  # MEDIUM - enthusiasm OK
        'transition_marker': 0.08,  # MEDIUM - conversational scaffolding
        'structure': 0.10,  # MEDIUM - avoid formulaic chapters
        'syntactic': 0.03,  # LOW
    },
    # ... etc
}
```

---

### Phase 3: Content-Aware Scoring Thresholds (Story 3.3)

**Priority:** HIGH
**Effort:** 2-3 days

Create content-type-specific scoring curves:

```python
CONTENT_TYPE_THRESHOLDS = {
    'academic': {
        'readability': {
            'flesch_reading_ease': {
                'EXCELLENT': (20, 40),   # Low score is GOOD
                'GOOD': (10, 50),
                'POOR': (60, 100),       # High score is BAD
            }
        },
        'sentiment': {
            'variance': {
                'EXCELLENT': (0.000, 0.050),  # Neutrality is GOOD
                'POOR': (0.300, 1.000),       # Emotion is BAD
            }
        }
    },
    'technical_book': {
        'readability': {
            'flesch_reading_ease': {
                'EXCELLENT': (55, 70),   # Must be accessible
                'GOOD': (50, 75),
                'POOR': (0, 45),         # Too complex for learning
            },
            'flesch_kincaid_grade': {
                'EXCELLENT': (9, 12),    # High school to freshman
                'GOOD': (8, 13),
                'POOR': (14, 20),        # Too academic
            }
        },
        'sentiment': {
            'variance': {
                'EXCELLENT': (0.100, 0.250),  # Enthusiasm appropriate
                'GOOD': (0.050, 0.300),
                'POOR': (0.000, 0.030),       # Too dry for 300 pages
            }
        },
        'burstiness': {
            'stdev': {
                'EXCELLENT': (6, 10),    # Varied for engagement
                'GOOD': (5, 11),
                'POOR': (0, 4),          # Too uniform/boring
            }
        }
    },
    'blog': {
        'readability': {
            'flesch_reading_ease': {
                'EXCELLENT': (60, 80),   # High score is GOOD
                'POOR': (0, 40),          # Low score is BAD
            }
        }
    },
    # ... etc
}
```

---

### Phase 4: Implement New Dimensions (Stories 3.4-3.10)

**Priority:** MEDIUM-HIGH
**Estimated Total Effort:** 10-14 days

1. **Story 3.4:** Register Consistency Dimension (2-3 days)
2. **Story 3.5:** Person Consistency Dimension (1-2 days)
3. **Story 3.6:** Lexical Inflation Dimension (2 days)
4. **Story 3.7:** Content vs Function Word Ratio (1 day)
5. **Story 3.8:** Formulaic Language Appropriateness (2-3 days)
6. **Story 3.9:** Paragraph Purpose Dimension (3-4 days) - LOW PRIORITY
7. **Story 3.10:** Citation/Evidence Patterns (2 days) - LOW PRIORITY

---

## Usage Examples

### Example 1: Analyzing Academic Paper

```bash
python analyze_ai_patterns.py dissertation.pdf \
    --content-type academic \
    --profile full
```

**Expected Output:**
```
Content Type: ACADEMIC (confidence: 0.95)

Dimension Scores (Academic-Weighted):
  Sentiment (Neutrality):     EXCELLENT  (Variance: 0.001 - appropriate neutrality)
  Readability (Complexity):   EXCELLENT  (Flesch: 25.3 - post-graduate level)
  Structure (Organization):   GOOD       (Formulaic transitions: 12 - expected in academic)
  Advanced Lexical:           EXCELLENT  (HDD: 0.87 - specialized vocabulary)

Quality Score: 88.5/100 (Target: ≥85.0) ✓
Detection Risk: 12.3% (Target: ≤30.0) ✓
```

---

### Example 2: Analyzing Professional Bio

```bash
python analyze_ai_patterns.py bio.txt \
    --content-type bio \
    --profile full
```

**Expected Output:**
```
Content Type: PROFESSIONAL_BIO (confidence: 0.92)

Dimension Scores (Bio-Weighted):
  Sentiment (Neutrality):     EXCELLENT  (Variance: 0.000 - factual tone appropriate)
  Readability (Accessibility): GOOD      (Flesch: 52.1 - professional audience)
  Voice (Consistency):        EXCELLENT  (3rd person maintained throughout)
  Burstiness (Variation):     FAIR       (σ: 5.7 - could vary sentence length more)

Quality Score: 75.2/100 (Target: ≥70.0 for bios) ✓
Detection Risk: 24.8% (Target: ≤30.0) ✓
```

---

### Example 3: Analyzing Personal Statement

```bash
python analyze_ai_patterns.py statement.txt \
    --content-type personal_statement \
    --profile full
```

**Expected Output:**
```
Content Type: PERSONAL_STATEMENT (confidence: 0.98)

Dimension Scores (Personal-Weighted):
  Sentiment (Authenticity):   EXCELLENT  (Variance: 0.940 - emotional range)
  Voice (Personal):           EXCELLENT  (1st person: 26, contractions: 18)
  Transition Markers:         GOOD       (Pragmatic markers: 5 - shows thought process)
  Readability (Clarity):      EXCELLENT  (Flesch: 43.4 - engaging complexity)

Quality Score: 85.3/100 (Target: ≥85.0) ✓
Detection Risk: 14.7% (Target: ≤30.0) ✓
```

---

### Example 4: Analyzing Technical Book Chapter

```bash
python analyze_ai_patterns.py chapter-01.md \
    --content-type technical_book \
    --profile full
```

**Expected Output:**
```
Content Type: TECHNICAL_BOOK (confidence: 0.89)

Dimension Scores (Technical-Book-Weighted):
  Readability (Accessibility): EXCELLENT  (Flesch: 62.4 - clear for learning)
  Burstiness (Engagement):     GOOD       (σ: 7.2 - varied sentence length)
  Figurative Language:         EXCELLENT  (245/1k - metaphors aid understanding)
  Voice (Conversational):      EXCELLENT  (1st person: 24, 2nd person: 18, contractions: 15)
  Advanced Lexical:            GOOD       (HDD: 0.78 - rich explanations)
  Sentiment (Enthusiasm):      GOOD       (Variance: 0.185 - appropriate energy)
  Transition Markers:          EXCELLENT  (5 instances - conversational scaffolding)
  Structure (Variety):         GOOD       (Not formulaic - varied chapter structure)
  Perplexity (Authenticity):   EXCELLENT  (0 AI words - natural technical writing)

Quality Score: 86.2/100 (Target: ≥85.0) ✓
Detection Risk: 13.8% (Target: ≤30.0) ✓

Recommendations:
  ✓ Accessibility excellent for learning audience
  ✓ Conversational tone maintains engagement
  ✓ Effective use of metaphors/analogies
  → Consider adding 1-2 more varied sentence lengths (target σ: 8-10)
```

**Why Technical Books Differ from Technical Docs:**
- Docs: Flesch 40-60 (reference), Sentiment 0.000 (neutral), Formulaic OK
- Books: Flesch 50-70 (learning), Sentiment 0.100-0.250 (enthusiasm), Formulaic BAD

---

## Research Sources

This framework integrates findings from:

1. **Biber's Multidimensional Analysis** - Genre-specific linguistic feature clustering
2. **Flesch-Kincaid Research** - Readability expectations by audience
3. **AI Detection Studies (2024)** - Lexical inflation, content word ratios, difficulty patterns
4. **Genre Theory** - Register, formality, and purpose distinctions
5. **Academic Writing Standards** - Discipline-specific conventions
6. **Technical Writing Guidelines** - Clarity and precision requirements

---

## Future Enhancements

### Content Type Profiles

Create comprehensive profiles including:
- Expected dimension ranges (min, optimal, max)
- Critical vs nice-to-have dimensions
- Genre-specific vocabulary lists
- Structural conventions

### Machine Learning Classification

Train classifier on labeled corpus:
- 1000+ examples per content type
- Feature extraction from dimension scores
- Confidence intervals for auto-detection

### Hybrid Content Types

Support detection of:
- Technical blog posts (technical + blog)
- Narrative journalism (creative + journalism)
- Academic blog posts (academic + blog)
- Research-based business writing (academic + business)

---

## Conclusion

Content type awareness fundamentally changes how we should evaluate writing quality. A professional bio with 0.000 sentiment variance is **excellent** (appropriate neutrality), not poor (emotionally flat). By implementing content-type-specific weighting, thresholds, and new dimensions, we can provide contextually appropriate feedback that helps writers achieve their genre-specific goals.

**Next Steps:**
1. Create Story 3.1 (Content Type Detection)
2. Update DualScoreCalculator to accept content_type parameter
3. Implement content-aware dimension weighting
4. Begin new dimension development (Register Consistency, Lexical Inflation)
