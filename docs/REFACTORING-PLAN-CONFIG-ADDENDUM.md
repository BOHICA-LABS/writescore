# Configuration Management System - Refactoring Plan Addendum

**Document Version:** 1.1
**Date:** 2025-11-03
**Status:** Proposed - Addendum to Main Refactoring Plan
**Author:** Claude Code (with Sarah - PO)

---

## Overview

This addendum extends the main refactoring plan to include a **centralized configuration management system** that allows:

1. ✅ Dimensions pull weights/settings from central config
2. ✅ Dimensions register what config keys they need
3. ✅ Multiple preconfigured analysis profiles (strict, balanced, permissive, etc.)
4. ✅ Runtime profile switching
5. ✅ Default configuration with sensible defaults
6. ✅ Config validation and schema enforcement
7. ✅ **Qualitative bands for dimensions and metrics** (NEW)
8. ✅ **Profile-specific band interpretations** (NEW)

---

## Architecture Extension

### Updated Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DynamicAnalysisEngine                     │
│  - Orchestrates analysis across registered dimensions        │
│  - Loads configuration profile                               │
│  - Validates weights before execution                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─────────────────┬─────────────────┐
                  │                 │                 │
        ┌─────────▼────────┐  ┌────▼──────────┐ ┌───▼────────────┐
        │ DimensionRegistry │  │WeightMediator │ │ ConfigManager  │
        │   (Singleton)     │  │ - Validates   │ │ - Load profiles│
        │ - register()      │  │ - Balances    │ │ - Get settings │
        │ - get_all()       │  └───────────────┘ │ - Validate     │
        └─────────┬─────────┘                    └────┬───────────┘
                  │                                   │
     ┌────────────┴────────────┐                      │
     │  Self-registering       │                      │
     │  Pull config on init    │◄─────────────────────┘
     │                         │
┌────▼─────┐  ┌──────────┐  ┌──────────┐
│Perplexity│  │Burstiness│  │Structure │  ... (10 dimensions)
│Dimension │  │Dimension │  │Dimension │
│(config)  │  │(config)  │  │(config)  │
└──────────┘  └──────────┘  └──────────┘
     │             │              │
     └─────────────┴──────────────┘
              │
    ┌─────────▼──────────┐
    │ DimensionStrategy  │
    │  (Enhanced Base)   │
    │ + get_config_schema()│
    │ + load_config()     │
    └────────────────────┘
```

---

## Qualitative Bands System

### Overview

The configuration system includes **qualitative bands** that map quantitative scores/metrics to human-readable labels. This provides flexible interpretation across different profiles.

### Two Types of Bands

#### 1. Dimension-Level Bands
Map overall dimension scores (0-100) to qualitative assessments.

**Example:**
```yaml
perplexity:
  dimension_bands:
    excellent:
      min: 90
      max: 100
      label: "EXCELLENT"
      description: "Minimal AI vocabulary signatures"
      color: "green"
    good:
      min: 75
      max: 89
      label: "GOOD"
      description: "Natural vocabulary with minor AI tells"
      color: "blue"
```

**Benefits:**
- Same score (e.g., 85) interpreted differently across profiles
- Strict mode: 85 = "GOOD", Permissive mode: 85 = "EXCELLENT"
- Color-coded dashboard support
- Trend analysis: "Moved from ACCEPTABLE to GOOD"

#### 2. Metric-Level Bands
Map individual metric values to qualitative assessments.

**Example:**
```yaml
perplexity:
  metric_bands:
    ai_vocabulary_per_1k:
      excellent:
        min: 0.0
        max: 1.0
        label: "EXCELLENT"
        description: "Nearly zero AI vocabulary"
      good:
        min: 1.1
        max: 3.0
        label: "GOOD"
        description: "Minimal AI vocabulary"

    formulaic_transitions_count:
      excellent:
        min: 0
        max: 2
        label: "EXCELLENT"
      good:
        min: 3
        max: 5
        label: "GOOD"
```

**Benefits:**
- Granular feedback: "Your AI vocab is GOOD (2.5/1k), but transitions are POOR (8)"
- Metric-specific interpretation
- Profile-specific thresholds
- Better recommendations targeting

### Profile-Specific Interpretations

Different profiles can have different band definitions for the same dimension/metric:

**Strict Profile:**
```yaml
perplexity:
  dimension_bands:
    excellent: {min: 95, max: 100}  # Very high bar
    good: {min: 85, max: 94}
```

**Permissive Profile:**
```yaml
perplexity:
  dimension_bands:
    excellent: {min: 80, max: 100}  # Lower bar
    good: {min: 65, max: 79}
```

---

## Configuration File Structure

### YAML Configuration Schema

```yaml
# config/analyzer_profiles.yaml

# Metadata
version: "1.0"
schema_version: "1.0"

# Active profile selection
active_profile: "balanced"

# Profile definitions
profiles:

  # ========================================================================
  # STRICT PROFILE - Maximum AI detection sensitivity
  # ========================================================================
  strict:
    name: "Strict Detection"
    description: "Maximum sensitivity to AI patterns, lowest false negatives"

    # Global settings
    global:
      detection_target: 20.0  # Target detection risk (lower = stricter)
      quality_target: 90.0    # Target quality score
      fail_on_weight_invalid: true
      parallel_execution: true
      max_workers: 10

    # Dimension configurations
    dimensions:

      perplexity:
        enabled: true
        weight: 7.0  # Increased from 5.0 for strict mode

        settings:
          ai_vocab_threshold_excellent: 0.5  # per 1k words (strict)
          ai_vocab_threshold_good: 1.5
          ai_vocab_threshold_acceptable: 3.0
          formulaic_transitions_penalty: 7  # Increased penalty
          custom_vocab_patterns: []  # Add custom patterns if needed

        # Dimension-level qualitative bands (for overall perplexity score 0-100)
        dimension_bands:
          excellent:
            min: 95
            max: 100
            label: "EXCELLENT"
            description: "Virtually no AI signatures in vocabulary"
            color: "green"
          good:
            min: 85
            max: 94
            label: "GOOD"
            description: "Minimal AI vocabulary with rare tells"
            color: "blue"
          acceptable:
            min: 70
            max: 84
            label: "ACCEPTABLE"
            description: "Some AI vocabulary present but manageable"
            color: "yellow"
          poor:
            min: 0
            max: 69
            label: "POOR"
            description: "Heavy AI vocabulary signatures"
            color: "red"

        # Metric-level qualitative bands (for individual metrics)
        metric_bands:
          ai_vocabulary_per_1k:
            excellent:
              min: 0.0
              max: 0.5
              label: "EXCELLENT"
              description: "Nearly zero AI vocabulary"
            good:
              min: 0.6
              max: 1.5
              label: "GOOD"
              description: "Minimal AI vocabulary"
            acceptable:
              min: 1.6
              max: 3.0
              label: "ACCEPTABLE"
              description: "Noticeable AI vocabulary"
            poor:
              min: 3.1
              max: 999.0
              label: "POOR"
              description: "Heavy AI vocabulary usage"

          formulaic_transitions_count:
            excellent:
              min: 0
              max: 1
              label: "EXCELLENT"
              description: "No formulaic transitions"
            good:
              min: 2
              max: 3
              label: "GOOD"
              description: "Rare formulaic transitions"
            acceptable:
              min: 4
              max: 6
              label: "ACCEPTABLE"
              description: "Some formulaic patterns"
            poor:
              min: 7
              max: 9999
              label: "POOR"
              description: "Frequent formulaic transitions"

      burstiness:
        enabled: true
        weight: 8.0  # Increased from 6.0

        settings:
          stdev_threshold_excellent: 12.0
          stdev_threshold_good: 8.0
          stdev_threshold_acceptable: 5.0
          cv_threshold_excellent: 0.45
          cv_threshold_good: 0.35
          cv_threshold_acceptable: 0.25

        # Dimension-level qualitative bands (for overall burstiness score 0-100)
        dimension_bands:
          excellent:
            min: 90
            max: 100
            label: "EXCELLENT"
            description: "Highly varied sentence structure with natural rhythm"
            color: "green"
          good:
            min: 75
            max: 89
            label: "GOOD"
            description: "Good sentence variation with minor uniformity"
            color: "blue"
          acceptable:
            min: 60
            max: 74
            label: "ACCEPTABLE"
            description: "Moderate sentence variation"
            color: "yellow"
          poor:
            min: 0
            max: 59
            label: "POOR"
            description: "Very uniform, AI-like sentence patterns"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          sentence_stdev:
            excellent:
              min: 12.0
              max: 999.0
              label: "EXCELLENT"
              description: "Highly varied sentence lengths"
            good:
              min: 8.0
              max: 11.9
              label: "GOOD"
              description: "Good sentence variation"
            acceptable:
              min: 5.0
              max: 7.9
              label: "ACCEPTABLE"
              description: "Moderate variation"
            poor:
              min: 0.0
              max: 4.9
              label: "POOR"
              description: "Very uniform sentence lengths"

          cv:
            excellent:
              min: 0.45
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent coefficient of variation"
            good:
              min: 0.35
              max: 0.44
              label: "GOOD"
              description: "Good variation coefficient"
            acceptable:
              min: 0.25
              max: 0.34
              label: "ACCEPTABLE"
              description: "Moderate variation coefficient"
            poor:
              min: 0.0
              max: 0.24
              label: "POOR"
              description: "Low variation coefficient"

      structure:
        enabled: true
        weight: 5.0

        settings:
          max_heading_depth: 4
          formulaic_threshold: 2
          parallelism_penalty: 5

        # Dimension-level qualitative bands (for overall structure score 0-100)
        dimension_bands:
          excellent:
            min: 92
            max: 100
            label: "EXCELLENT"
            description: "Natural, organic document structure"
            color: "green"
          good:
            min: 80
            max: 91
            label: "GOOD"
            description: "Well-structured with minor formulaic patterns"
            color: "blue"
          acceptable:
            min: 65
            max: 79
            label: "ACCEPTABLE"
            description: "Some formulaic structural patterns"
            color: "yellow"
          poor:
            min: 0
            max: 64
            label: "POOR"
            description: "Heavily formulaic or overly rigid structure"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          heading_depth:
            excellent:
              min: 0
              max: 3
              label: "EXCELLENT"
              description: "Shallow, natural hierarchy"
            good:
              min: 4
              max: 4
              label: "GOOD"
              description: "Acceptable heading depth"
            acceptable:
              min: 5
              max: 5
              label: "ACCEPTABLE"
              description: "Slightly deep hierarchy"
            poor:
              min: 6
              max: 999
              label: "POOR"
              description: "Overly deep heading hierarchy"

          formulaic_count:
            excellent:
              min: 0
              max: 1
              label: "EXCELLENT"
              description: "Minimal formulaic patterns"
            good:
              min: 2
              max: 2
              label: "GOOD"
              description: "Few formulaic patterns"
            acceptable:
              min: 3
              max: 4
              label: "ACCEPTABLE"
              description: "Some formulaic patterns"
            poor:
              min: 5
              max: 9999
              label: "POOR"
              description: "Many formulaic structural patterns"

          parallelism_score:
            excellent:
              min: 0
              max: 4
              label: "EXCELLENT"
              description: "Minimal heading parallelism"
            good:
              min: 5
              max: 9
              label: "GOOD"
              description: "Some heading parallelism"
            acceptable:
              min: 10
              max: 14
              label: "ACCEPTABLE"
              description: "Noticeable parallelism"
            poor:
              min: 15
              max: 9999
              label: "POOR"
              description: "Heavy heading parallelism"

      formatting:
        enabled: true
        weight: 5.0

        settings:
          em_dash_max_per_page: 1.5  # Strict
          bold_per_1k_max: 3.0
          italic_per_1k_max: 5.0

        # Dimension-level qualitative bands (for overall formatting score 0-100)
        dimension_bands:
          excellent:
            min: 93
            max: 100
            label: "EXCELLENT"
            description: "Natural, minimal formatting"
            color: "green"
          good:
            min: 82
            max: 92
            label: "GOOD"
            description: "Well-balanced formatting usage"
            color: "blue"
          acceptable:
            min: 68
            max: 81
            label: "ACCEPTABLE"
            description: "Slightly heavy formatting"
            color: "yellow"
          poor:
            min: 0
            max: 67
            label: "POOR"
            description: "Excessive formatting typical of AI"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          em_dash_per_page:
            excellent:
              min: 0.0
              max: 1.0
              label: "EXCELLENT"
              description: "Minimal em-dash usage"
            good:
              min: 1.1
              max: 1.5
              label: "GOOD"
              description: "Light em-dash usage"
            acceptable:
              min: 1.6
              max: 2.5
              label: "ACCEPTABLE"
              description: "Moderate em-dash usage"
            poor:
              min: 2.6
              max: 999.0
              label: "POOR"
              description: "Heavy em-dash usage"

          bold_per_1k:
            excellent:
              min: 0.0
              max: 2.0
              label: "EXCELLENT"
              description: "Minimal bold formatting"
            good:
              min: 2.1
              max: 3.0
              label: "GOOD"
              description: "Light bold usage"
            acceptable:
              min: 3.1
              max: 5.0
              label: "ACCEPTABLE"
              description: "Moderate bold usage"
            poor:
              min: 5.1
              max: 999.0
              label: "POOR"
              description: "Heavy bold formatting"

          italic_per_1k:
            excellent:
              min: 0.0
              max: 3.0
              label: "EXCELLENT"
              description: "Minimal italic usage"
            good:
              min: 3.1
              max: 5.0
              label: "GOOD"
              description: "Light italic usage"
            acceptable:
              min: 5.1
              max: 8.0
              label: "ACCEPTABLE"
              description: "Moderate italic usage"
            poor:
              min: 8.1
              max: 999.0
              label: "POOR"
              description: "Heavy italic formatting"

      voice:
        enabled: true
        weight: 6.0

        settings:
          first_person_weight: 2.0
          contractions_weight: 1.5
          direct_address_weight: 1.0

        # Dimension-level qualitative bands (for overall voice score 0-100)
        dimension_bands:
          excellent:
            min: 88
            max: 100
            label: "EXCELLENT"
            description: "Strong human voice with personal touches"
            color: "green"
          good:
            min: 72
            max: 87
            label: "GOOD"
            description: "Natural voice with some personality"
            color: "blue"
          acceptable:
            min: 55
            max: 71
            label: "ACCEPTABLE"
            description: "Somewhat impersonal voice"
            color: "yellow"
          poor:
            min: 0
            max: 54
            label: "POOR"
            description: "Very formal, AI-like voice"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          first_person_count:
            excellent:
              min: 8
              max: 9999
              label: "EXCELLENT"
              description: "Strong first-person presence"
            good:
              min: 4
              max: 7
              label: "GOOD"
              description: "Good first-person usage"
            acceptable:
              min: 2
              max: 3
              label: "ACCEPTABLE"
              description: "Minimal first-person"
            poor:
              min: 0
              max: 1
              label: "POOR"
              description: "No first-person voice"

          contractions_count:
            excellent:
              min: 6
              max: 9999
              label: "EXCELLENT"
              description: "Natural contraction usage"
            good:
              min: 3
              max: 5
              label: "GOOD"
              description: "Some contractions"
            acceptable:
              min: 1
              max: 2
              label: "ACCEPTABLE"
              description: "Few contractions"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No contractions (overly formal)"

          direct_address_count:
            excellent:
              min: 5
              max: 9999
              label: "EXCELLENT"
              description: "Engaging, reader-focused"
            good:
              min: 2
              max: 4
              label: "GOOD"
              description: "Some reader engagement"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Minimal reader address"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No direct address"

      syntactic:
        enabled: true
        weight: 3.0

        settings:
          subordination_threshold: 0.25
          dependency_depth_min: 2.5

        # Dimension-level qualitative bands (for overall syntactic score 0-100)
        dimension_bands:
          excellent:
            min: 90
            max: 100
            label: "EXCELLENT"
            description: "Complex, varied syntactic structures"
            color: "green"
          good:
            min: 75
            max: 89
            label: "GOOD"
            description: "Good syntactic complexity"
            color: "blue"
          acceptable:
            min: 60
            max: 74
            label: "ACCEPTABLE"
            description: "Moderate syntactic variation"
            color: "yellow"
          poor:
            min: 0
            max: 59
            label: "POOR"
            description: "Simple, repetitive syntax"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          subordination_index:
            excellent:
              min: 0.25
              max: 999.0
              label: "EXCELLENT"
              description: "High subordination complexity"
            good:
              min: 0.20
              max: 0.24
              label: "GOOD"
              description: "Good subordination"
            acceptable:
              min: 0.15
              max: 0.19
              label: "ACCEPTABLE"
              description: "Moderate subordination"
            poor:
              min: 0.0
              max: 0.14
              label: "POOR"
              description: "Low subordination (simple sentences)"

          dependency_depth:
            excellent:
              min: 2.5
              max: 999.0
              label: "EXCELLENT"
              description: "Deep, complex dependencies"
            good:
              min: 2.0
              max: 2.4
              label: "GOOD"
              description: "Good dependency depth"
            acceptable:
              min: 1.5
              max: 1.9
              label: "ACCEPTABLE"
              description: "Moderate dependency depth"
            poor:
              min: 0.0
              max: 1.4
              label: "POOR"
              description: "Shallow dependencies"

      lexical:
        enabled: true
        weight: 4.0

        settings:
          diversity_threshold_excellent: 0.55
          diversity_threshold_good: 0.45
          mtld_threshold_excellent: 180
          mtld_threshold_good: 140

        # Dimension-level qualitative bands (for overall lexical score 0-100)
        dimension_bands:
          excellent:
            min: 91
            max: 100
            label: "EXCELLENT"
            description: "Rich, diverse vocabulary"
            color: "green"
          good:
            min: 77
            max: 90
            label: "GOOD"
            description: "Good lexical diversity"
            color: "blue"
          acceptable:
            min: 62
            max: 76
            label: "ACCEPTABLE"
            description: "Moderate vocabulary range"
            color: "yellow"
          poor:
            min: 0
            max: 61
            label: "POOR"
            description: "Limited, repetitive vocabulary"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          diversity_score:
            excellent:
              min: 0.55
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent lexical diversity"
            good:
              min: 0.45
              max: 0.54
              label: "GOOD"
              description: "Good diversity"
            acceptable:
              min: 0.35
              max: 0.44
              label: "ACCEPTABLE"
              description: "Moderate diversity"
            poor:
              min: 0.0
              max: 0.34
              label: "POOR"
              description: "Low diversity (repetitive)"

          mtld_score:
            excellent:
              min: 180
              max: 9999
              label: "EXCELLENT"
              description: "Excellent MTLD (rich vocabulary)"
            good:
              min: 140
              max: 179
              label: "GOOD"
              description: "Good MTLD"
            acceptable:
              min: 100
              max: 139
              label: "ACCEPTABLE"
              description: "Moderate MTLD"
            poor:
              min: 0
              max: 99
              label: "POOR"
              description: "Low MTLD (limited vocabulary)"

      stylometric:
        enabled: true
        weight: 6.0

        settings:
          however_per_1k_max: 0.8  # Strict
          moreover_per_1k_max: 0.5
          passive_voice_max: 10  # percentage

        # Dimension-level qualitative bands (for overall stylometric score 0-100)
        dimension_bands:
          excellent:
            min: 94
            max: 100
            label: "EXCELLENT"
            description: "Natural style with minimal AI markers"
            color: "green"
          good:
            min: 83
            max: 93
            label: "GOOD"
            description: "Good style with rare AI tells"
            color: "blue"
          acceptable:
            min: 70
            max: 82
            label: "ACCEPTABLE"
            description: "Some AI stylistic patterns"
            color: "yellow"
          poor:
            min: 0
            max: 69
            label: "POOR"
            description: "Heavy AI stylistic markers"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          however_per_1k:
            excellent:
              min: 0.0
              max: 0.5
              label: "EXCELLENT"
              description: "Minimal 'however' usage"
            good:
              min: 0.6
              max: 0.8
              label: "GOOD"
              description: "Light 'however' usage"
            acceptable:
              min: 0.9
              max: 1.2
              label: "ACCEPTABLE"
              description: "Moderate 'however' usage"
            poor:
              min: 1.3
              max: 999.0
              label: "POOR"
              description: "Heavy 'however' usage"

          moreover_per_1k:
            excellent:
              min: 0.0
              max: 0.3
              label: "EXCELLENT"
              description: "Minimal 'moreover' usage"
            good:
              min: 0.4
              max: 0.5
              label: "GOOD"
              description: "Light 'moreover' usage"
            acceptable:
              min: 0.6
              max: 0.8
              label: "ACCEPTABLE"
              description: "Moderate 'moreover' usage"
            poor:
              min: 0.9
              max: 999.0
              label: "POOR"
              description: "Heavy 'moreover' usage"

          passive_voice_percent:
            excellent:
              min: 0.0
              max: 5.0
              label: "EXCELLENT"
              description: "Minimal passive voice"
            good:
              min: 5.1
              max: 10.0
              label: "GOOD"
              description: "Light passive voice"
            acceptable:
              min: 10.1
              max: 15.0
              label: "ACCEPTABLE"
              description: "Moderate passive voice"
            poor:
              min: 15.1
              max: 100.0
              label: "POOR"
              description: "Heavy passive voice usage"

      advanced:
        enabled: true
        weight: 35.0  # GLTR, MATTR, RTTR, etc.

        settings:
          gltr_top10_max: 55  # Strict threshold
          mattr_threshold_excellent: 0.75
          mattr_threshold_good: 0.68
          rttr_threshold_excellent: 8.5
          rttr_threshold_good: 7.0

        # Dimension-level qualitative bands (for overall advanced score 0-100)
        dimension_bands:
          excellent:
            min: 92
            max: 100
            label: "EXCELLENT"
            description: "Highly human-like statistical patterns"
            color: "green"
          good:
            min: 78
            max: 91
            label: "GOOD"
            description: "Good statistical patterns with minor AI signatures"
            color: "blue"
          acceptable:
            min: 63
            max: 77
            label: "ACCEPTABLE"
            description: "Moderate AI statistical patterns"
            color: "yellow"
          poor:
            min: 0
            max: 62
            label: "POOR"
            description: "Strong AI statistical signatures"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          gltr_top10_percent:
            excellent:
              min: 0.0
              max: 45.0
              label: "EXCELLENT"
              description: "Very low GLTR top-10 (unpredictable)"
            good:
              min: 45.1
              max: 55.0
              label: "GOOD"
              description: "Low GLTR top-10"
            acceptable:
              min: 55.1
              max: 65.0
              label: "ACCEPTABLE"
              description: "Moderate GLTR top-10"
            poor:
              min: 65.1
              max: 100.0
              label: "POOR"
              description: "High GLTR top-10 (predictable)"

          mattr_score:
            excellent:
              min: 0.75
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent MATTR (moving average TTR)"
            good:
              min: 0.68
              max: 0.74
              label: "GOOD"
              description: "Good MATTR"
            acceptable:
              min: 0.60
              max: 0.67
              label: "ACCEPTABLE"
              description: "Moderate MATTR"
            poor:
              min: 0.0
              max: 0.59
              label: "POOR"
              description: "Low MATTR (repetitive)"

          rttr_score:
            excellent:
              min: 8.5
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent RTTR (root TTR)"
            good:
              min: 7.0
              max: 8.4
              label: "GOOD"
              description: "Good RTTR"
            acceptable:
              min: 5.5
              max: 6.9
              label: "ACCEPTABLE"
              description: "Moderate RTTR"
            poor:
              min: 0.0
              max: 5.4
              label: "POOR"
              description: "Low RTTR"

      sentiment:
        enabled: true
        weight: 6.0

        settings:
          variance_threshold_excellent: 0.20
          variance_threshold_good: 0.15
          emotionally_flat_threshold: 0.10

        # Dimension-level qualitative bands (for overall sentiment score 0-100)
        dimension_bands:
          excellent:
            min: 89
            max: 100
            label: "EXCELLENT"
            description: "Rich, varied emotional content"
            color: "green"
          good:
            min: 74
            max: 88
            label: "GOOD"
            description: "Good emotional variation"
            color: "blue"
          acceptable:
            min: 58
            max: 73
            label: "ACCEPTABLE"
            description: "Moderate emotional range"
            color: "yellow"
          poor:
            min: 0
            max: 57
            label: "POOR"
            description: "Emotionally flat, AI-like affect"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          sentiment_variance:
            excellent:
              min: 0.20
              max: 999.0
              label: "EXCELLENT"
              description: "High emotional variance"
            good:
              min: 0.15
              max: 0.19
              label: "GOOD"
              description: "Good emotional variance"
            acceptable:
              min: 0.10
              max: 0.14
              label: "ACCEPTABLE"
              description: "Moderate variance"
            poor:
              min: 0.0
              max: 0.09
              label: "POOR"
              description: "Low variance (emotionally flat)"

          sentiment_mean:
            excellent:
              min: 0.15
              max: 0.45
              label: "EXCELLENT"
              description: "Balanced emotional tone"
            good:
              min: 0.10
              max: 0.14
              label: "GOOD"
              description: "Slightly positive tone"
            acceptable:
              min: 0.05
              max: 0.09
              label: "ACCEPTABLE"
              description: "Mostly neutral tone"
            poor:
              min: 0.0
              max: 0.04
              label: "POOR"
              description: "Excessively neutral"

          emotionally_flat_ratio:
            excellent:
              min: 0.0
              max: 0.05
              label: "EXCELLENT"
              description: "Minimal flat affect"
            good:
              min: 0.06
              max: 0.10
              label: "GOOD"
              description: "Low flat affect"
            acceptable:
              min: 0.11
              max: 0.15
              label: "ACCEPTABLE"
              description: "Some flat affect"
            poor:
              min: 0.16
              max: 1.0
              label: "POOR"
              description: "High flat affect (AI-like)"

      structural:
        enabled: true
        weight: 4.0

        settings:
          blockquote_clustering_max: 0.3
          link_anchor_generic_max: 0.2

        # Dimension-level qualitative bands (for overall structural score 0-100)
        dimension_bands:
          excellent:
            min: 91
            max: 100
            label: "EXCELLENT"
            description: "Natural structural patterns"
            color: "green"
          good:
            min: 76
            max: 90
            label: "GOOD"
            description: "Good structural variation"
            color: "blue"
          acceptable:
            min: 60
            max: 75
            label: "ACCEPTABLE"
            description: "Some structural patterns"
            color: "yellow"
          poor:
            min: 0
            max: 59
            label: "POOR"
            description: "Heavy AI structural signatures"
            color: "red"

        # Metric-level qualitative bands
        metric_bands:
          blockquote_clustering:
            excellent:
              min: 0.0
              max: 0.2
              label: "EXCELLENT"
              description: "Minimal blockquote clustering"
            good:
              min: 0.21
              max: 0.3
              label: "GOOD"
              description: "Low blockquote clustering"
            acceptable:
              min: 0.31
              max: 0.4
              label: "ACCEPTABLE"
              description: "Moderate clustering"
            poor:
              min: 0.41
              max: 1.0
              label: "POOR"
              description: "Heavy blockquote clustering"

          link_anchor_generic_ratio:
            excellent:
              min: 0.0
              max: 0.15
              label: "EXCELLENT"
              description: "Descriptive link anchors"
            good:
              min: 0.16
              max: 0.2
              label: "GOOD"
              description: "Mostly descriptive anchors"
            acceptable:
              min: 0.21
              max: 0.3
              label: "ACCEPTABLE"
              description: "Some generic anchors"
            poor:
              min: 0.31
              max: 1.0
              label: "POOR"
              description: "Many generic anchors (AI-like)"

  # ========================================================================
  # BALANCED PROFILE - Default recommended settings
  # ========================================================================
  balanced:
    name: "Balanced Analysis"
    description: "Recommended default with balanced sensitivity"

    global:
      detection_target: 30.0
      quality_target: 85.0
      fail_on_weight_invalid: true
      parallel_execution: true
      max_workers: 10

    dimensions:
      perplexity:
        enabled: true
        weight: 5.0  # Default weight

        settings:
          ai_vocab_threshold_excellent: 1.0
          ai_vocab_threshold_good: 3.0
          ai_vocab_threshold_acceptable: 5.0
          formulaic_transitions_penalty: 5
          custom_vocab_patterns: []

        dimension_bands:
          excellent:
            min: 90
            max: 100
            label: "EXCELLENT"
            description: "Minimal AI vocabulary signatures"
            color: "green"
          good:
            min: 78
            max: 89
            label: "GOOD"
            description: "Natural vocabulary with minor AI tells"
            color: "blue"
          acceptable:
            min: 65
            max: 77
            label: "ACCEPTABLE"
            description: "Some AI vocabulary present"
            color: "yellow"
          poor:
            min: 0
            max: 64
            label: "POOR"
            description: "Heavy AI vocabulary signatures"
            color: "red"

        metric_bands:
          ai_vocabulary_per_1k:
            excellent:
              min: 0.0
              max: 1.0
              label: "EXCELLENT"
              description: "Nearly zero AI vocabulary"
            good:
              min: 1.1
              max: 3.0
              label: "GOOD"
              description: "Minimal AI vocabulary"
            acceptable:
              min: 3.1
              max: 5.0
              label: "ACCEPTABLE"
              description: "Noticeable AI vocabulary"
            poor:
              min: 5.1
              max: 999.0
              label: "POOR"
              description: "Heavy AI vocabulary usage"

          formulaic_transitions_count:
            excellent:
              min: 0
              max: 2
              label: "EXCELLENT"
              description: "Minimal formulaic transitions"
            good:
              min: 3
              max: 4
              label: "GOOD"
              description: "Few formulaic transitions"
            acceptable:
              min: 5
              max: 7
              label: "ACCEPTABLE"
              description: "Some formulaic patterns"
            poor:
              min: 8
              max: 9999
              label: "POOR"
              description: "Frequent formulaic transitions"

      burstiness:
        enabled: true
        weight: 6.0

        settings:
          stdev_threshold_excellent: 10.0
          stdev_threshold_good: 7.0
          stdev_threshold_acceptable: 4.5
          cv_threshold_excellent: 0.40
          cv_threshold_good: 0.30
          cv_threshold_acceptable: 0.20

        dimension_bands:
          excellent:
            min: 88
            max: 100
            label: "EXCELLENT"
            description: "Highly varied sentence structure"
            color: "green"
          good:
            min: 72
            max: 87
            label: "GOOD"
            description: "Good sentence variation"
            color: "blue"
          acceptable:
            min: 55
            max: 71
            label: "ACCEPTABLE"
            description: "Moderate sentence variation"
            color: "yellow"
          poor:
            min: 0
            max: 54
            label: "POOR"
            description: "Uniform AI-like sentence patterns"
            color: "red"

        metric_bands:
          sentence_stdev:
            excellent:
              min: 10.0
              max: 999.0
              label: "EXCELLENT"
              description: "Highly varied sentence lengths"
            good:
              min: 7.0
              max: 9.9
              label: "GOOD"
              description: "Good sentence variation"
            acceptable:
              min: 4.5
              max: 6.9
              label: "ACCEPTABLE"
              description: "Moderate variation"
            poor:
              min: 0.0
              max: 4.4
              label: "POOR"
              description: "Uniform sentence lengths"

          cv:
            excellent:
              min: 0.40
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent coefficient of variation"
            good:
              min: 0.30
              max: 0.39
              label: "GOOD"
              description: "Good variation coefficient"
            acceptable:
              min: 0.20
              max: 0.29
              label: "ACCEPTABLE"
              description: "Moderate variation"
            poor:
              min: 0.0
              max: 0.19
              label: "POOR"
              description: "Low variation coefficient"

      structure:
        enabled: true
        weight: 4.0

        settings:
          max_heading_depth: 4
          formulaic_threshold: 3
          parallelism_penalty: 3

        dimension_bands:
          excellent:
            min: 88
            max: 100
            label: "EXCELLENT"
            description: "Natural document structure"
            color: "green"
          good:
            min: 74
            max: 87
            label: "GOOD"
            description: "Well-structured content"
            color: "blue"
          acceptable:
            min: 58
            max: 73
            label: "ACCEPTABLE"
            description: "Some formulaic patterns"
            color: "yellow"
          poor:
            min: 0
            max: 57
            label: "POOR"
            description: "Heavily formulaic structure"
            color: "red"

        metric_bands:
          heading_depth:
            excellent:
              min: 0
              max: 3
              label: "EXCELLENT"
              description: "Natural hierarchy"
            good:
              min: 4
              max: 4
              label: "GOOD"
              description: "Acceptable depth"
            acceptable:
              min: 5
              max: 5
              label: "ACCEPTABLE"
              description: "Slightly deep"
            poor:
              min: 6
              max: 999
              label: "POOR"
              description: "Overly deep hierarchy"

          formulaic_count:
            excellent:
              min: 0
              max: 2
              label: "EXCELLENT"
              description: "Minimal formulaic patterns"
            good:
              min: 3
              max: 3
              label: "GOOD"
              description: "Few formulaic patterns"
            acceptable:
              min: 4
              max: 5
              label: "ACCEPTABLE"
              description: "Some patterns"
            poor:
              min: 6
              max: 9999
              label: "POOR"
              description: "Many formulaic patterns"

          parallelism_score:
            excellent:
              min: 0
              max: 6
              label: "EXCELLENT"
              description: "Minimal parallelism"
            good:
              min: 7
              max: 11
              label: "GOOD"
              description: "Some parallelism"
            acceptable:
              min: 12
              max: 16
              label: "ACCEPTABLE"
              description: "Noticeable parallelism"
            poor:
              min: 17
              max: 9999
              label: "POOR"
              description: "Heavy parallelism"

      formatting:
        enabled: true
        weight: 4.0

        settings:
          em_dash_max_per_page: 2.5
          bold_per_1k_max: 5.0
          italic_per_1k_max: 8.0

        dimension_bands:
          excellent:
            min: 89
            max: 100
            label: "EXCELLENT"
            description: "Natural formatting"
            color: "green"
          good:
            min: 76
            max: 88
            label: "GOOD"
            description: "Balanced formatting"
            color: "blue"
          acceptable:
            min: 62
            max: 75
            label: "ACCEPTABLE"
            description: "Moderate formatting"
            color: "yellow"
          poor:
            min: 0
            max: 61
            label: "POOR"
            description: "Excessive formatting"
            color: "red"

        metric_bands:
          em_dash_per_page:
            excellent:
              min: 0.0
              max: 1.5
              label: "EXCELLENT"
              description: "Minimal em-dash usage"
            good:
              min: 1.6
              max: 2.5
              label: "GOOD"
              description: "Light em-dash usage"
            acceptable:
              min: 2.6
              max: 3.5
              label: "ACCEPTABLE"
              description: "Moderate usage"
            poor:
              min: 3.6
              max: 999.0
              label: "POOR"
              description: "Heavy em-dash usage"

          bold_per_1k:
            excellent:
              min: 0.0
              max: 3.0
              label: "EXCELLENT"
              description: "Minimal bold"
            good:
              min: 3.1
              max: 5.0
              label: "GOOD"
              description: "Light bold usage"
            acceptable:
              min: 5.1
              max: 7.0
              label: "ACCEPTABLE"
              description: "Moderate bold"
            poor:
              min: 7.1
              max: 999.0
              label: "POOR"
              description: "Heavy bold formatting"

          italic_per_1k:
            excellent:
              min: 0.0
              max: 5.0
              label: "EXCELLENT"
              description: "Minimal italic"
            good:
              min: 5.1
              max: 8.0
              label: "GOOD"
              description: "Light italic usage"
            acceptable:
              min: 8.1
              max: 11.0
              label: "ACCEPTABLE"
              description: "Moderate italic"
            poor:
              min: 11.1
              max: 999.0
              label: "POOR"
              description: "Heavy italic formatting"

      voice:
        enabled: true
        weight: 5.0

        settings:
          first_person_weight: 1.5
          contractions_weight: 1.0
          direct_address_weight: 0.5

        dimension_bands:
          excellent:
            min: 84
            max: 100
            label: "EXCELLENT"
            description: "Strong human voice"
            color: "green"
          good:
            min: 68
            max: 83
            label: "GOOD"
            description: "Natural voice"
            color: "blue"
          acceptable:
            min: 50
            max: 67
            label: "ACCEPTABLE"
            description: "Somewhat impersonal"
            color: "yellow"
          poor:
            min: 0
            max: 49
            label: "POOR"
            description: "Formal AI-like voice"
            color: "red"

        metric_bands:
          first_person_count:
            excellent:
              min: 6
              max: 9999
              label: "EXCELLENT"
              description: "Strong first-person presence"
            good:
              min: 3
              max: 5
              label: "GOOD"
              description: "Good first-person usage"
            acceptable:
              min: 1
              max: 2
              label: "ACCEPTABLE"
              description: "Minimal first-person"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No first-person voice"

          contractions_count:
            excellent:
              min: 4
              max: 9999
              label: "EXCELLENT"
              description: "Natural contractions"
            good:
              min: 2
              max: 3
              label: "GOOD"
              description: "Some contractions"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Few contractions"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No contractions"

          direct_address_count:
            excellent:
              min: 3
              max: 9999
              label: "EXCELLENT"
              description: "Engaging reader focus"
            good:
              min: 1
              max: 2
              label: "GOOD"
              description: "Some engagement"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Minimal engagement"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No direct address"

      syntactic:
        enabled: true
        weight: 2.0

        settings:
          subordination_threshold: 0.20
          dependency_depth_min: 2.0

        dimension_bands:
          excellent:
            min: 87
            max: 100
            label: "EXCELLENT"
            description: "Complex syntax"
            color: "green"
          good:
            min: 71
            max: 86
            label: "GOOD"
            description: "Good complexity"
            color: "blue"
          acceptable:
            min: 55
            max: 70
            label: "ACCEPTABLE"
            description: "Moderate complexity"
            color: "yellow"
          poor:
            min: 0
            max: 54
            label: "POOR"
            description: "Simple syntax"
            color: "red"

        metric_bands:
          subordination_index:
            excellent:
              min: 0.20
              max: 999.0
              label: "EXCELLENT"
              description: "High subordination"
            good:
              min: 0.15
              max: 0.19
              label: "GOOD"
              description: "Good subordination"
            acceptable:
              min: 0.10
              max: 0.14
              label: "ACCEPTABLE"
              description: "Moderate subordination"
            poor:
              min: 0.0
              max: 0.09
              label: "POOR"
              description: "Low subordination"

          dependency_depth:
            excellent:
              min: 2.0
              max: 999.0
              label: "EXCELLENT"
              description: "Deep dependencies"
            good:
              min: 1.5
              max: 1.9
              label: "GOOD"
              description: "Good depth"
            acceptable:
              min: 1.0
              max: 1.4
              label: "ACCEPTABLE"
              description: "Moderate depth"
            poor:
              min: 0.0
              max: 0.9
              label: "POOR"
              description: "Shallow dependencies"

      lexical:
        enabled: true
        weight: 3.0

        settings:
          diversity_threshold_excellent: 0.50
          diversity_threshold_good: 0.40
          mtld_threshold_excellent: 160
          mtld_threshold_good: 120

        dimension_bands:
          excellent:
            min: 88
            max: 100
            label: "EXCELLENT"
            description: "Rich vocabulary"
            color: "green"
          good:
            min: 73
            max: 87
            label: "GOOD"
            description: "Good diversity"
            color: "blue"
          acceptable:
            min: 57
            max: 72
            label: "ACCEPTABLE"
            description: "Moderate range"
            color: "yellow"
          poor:
            min: 0
            max: 56
            label: "POOR"
            description: "Limited vocabulary"
            color: "red"

        metric_bands:
          diversity_score:
            excellent:
              min: 0.50
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent diversity"
            good:
              min: 0.40
              max: 0.49
              label: "GOOD"
              description: "Good diversity"
            acceptable:
              min: 0.30
              max: 0.39
              label: "ACCEPTABLE"
              description: "Moderate diversity"
            poor:
              min: 0.0
              max: 0.29
              label: "POOR"
              description: "Low diversity"

          mtld_score:
            excellent:
              min: 160
              max: 9999
              label: "EXCELLENT"
              description: "Excellent MTLD"
            good:
              min: 120
              max: 159
              label: "GOOD"
              description: "Good MTLD"
            acceptable:
              min: 80
              max: 119
              label: "ACCEPTABLE"
              description: "Moderate MTLD"
            poor:
              min: 0
              max: 79
              label: "POOR"
              description: "Low MTLD"

      stylometric:
        enabled: true
        weight: 5.0

        settings:
          however_per_1k_max: 1.2
          moreover_per_1k_max: 0.8
          passive_voice_max: 15

        dimension_bands:
          excellent:
            min: 91
            max: 100
            label: "EXCELLENT"
            description: "Natural style"
            color: "green"
          good:
            min: 78
            max: 90
            label: "GOOD"
            description: "Good style"
            color: "blue"
          acceptable:
            min: 64
            max: 77
            label: "ACCEPTABLE"
            description: "Some AI patterns"
            color: "yellow"
          poor:
            min: 0
            max: 63
            label: "POOR"
            description: "Heavy AI markers"
            color: "red"

        metric_bands:
          however_per_1k:
            excellent:
              min: 0.0
              max: 0.8
              label: "EXCELLENT"
              description: "Minimal 'however'"
            good:
              min: 0.9
              max: 1.2
              label: "GOOD"
              description: "Light usage"
            acceptable:
              min: 1.3
              max: 1.6
              label: "ACCEPTABLE"
              description: "Moderate usage"
            poor:
              min: 1.7
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          moreover_per_1k:
            excellent:
              min: 0.0
              max: 0.5
              label: "EXCELLENT"
              description: "Minimal 'moreover'"
            good:
              min: 0.6
              max: 0.8
              label: "GOOD"
              description: "Light usage"
            acceptable:
              min: 0.9
              max: 1.1
              label: "ACCEPTABLE"
              description: "Moderate usage"
            poor:
              min: 1.2
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          passive_voice_percent:
            excellent:
              min: 0.0
              max: 8.0
              label: "EXCELLENT"
              description: "Minimal passive voice"
            good:
              min: 8.1
              max: 15.0
              label: "GOOD"
              description: "Light passive voice"
            acceptable:
              min: 15.1
              max: 20.0
              label: "ACCEPTABLE"
              description: "Moderate passive voice"
            poor:
              min: 20.1
              max: 100.0
              label: "POOR"
              description: "Heavy passive voice"

      advanced:
        enabled: true
        weight: 35.0

        settings:
          gltr_top10_max: 65
          mattr_threshold_excellent: 0.70
          mattr_threshold_good: 0.62
          rttr_threshold_excellent: 7.5
          rttr_threshold_good: 6.0

        dimension_bands:
          excellent:
            min: 89
            max: 100
            label: "EXCELLENT"
            description: "Human-like statistical patterns"
            color: "green"
          good:
            min: 74
            max: 88
            label: "GOOD"
            description: "Good statistical patterns"
            color: "blue"
          acceptable:
            min: 58
            max: 73
            label: "ACCEPTABLE"
            description: "Moderate AI patterns"
            color: "yellow"
          poor:
            min: 0
            max: 57
            label: "POOR"
            description: "Strong AI signatures"
            color: "red"

        metric_bands:
          gltr_top10_percent:
            excellent:
              min: 0.0
              max: 50.0
              label: "EXCELLENT"
              description: "Low GLTR top-10"
            good:
              min: 50.1
              max: 65.0
              label: "GOOD"
              description: "Moderate GLTR"
            acceptable:
              min: 65.1
              max: 75.0
              label: "ACCEPTABLE"
              description: "Higher GLTR"
            poor:
              min: 75.1
              max: 100.0
              label: "POOR"
              description: "High GLTR (predictable)"

          mattr_score:
            excellent:
              min: 0.70
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent MATTR"
            good:
              min: 0.62
              max: 0.69
              label: "GOOD"
              description: "Good MATTR"
            acceptable:
              min: 0.54
              max: 0.61
              label: "ACCEPTABLE"
              description: "Moderate MATTR"
            poor:
              min: 0.0
              max: 0.53
              label: "POOR"
              description: "Low MATTR"

          rttr_score:
            excellent:
              min: 7.5
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent RTTR"
            good:
              min: 6.0
              max: 7.4
              label: "GOOD"
              description: "Good RTTR"
            acceptable:
              min: 4.5
              max: 5.9
              label: "ACCEPTABLE"
              description: "Moderate RTTR"
            poor:
              min: 0.0
              max: 4.4
              label: "POOR"
              description: "Low RTTR"

      sentiment:
        enabled: true
        weight: 5.0

        settings:
          variance_threshold_excellent: 0.18
          variance_threshold_good: 0.13
          emotionally_flat_threshold: 0.12

        dimension_bands:
          excellent:
            min: 86
            max: 100
            label: "EXCELLENT"
            description: "Rich emotional content"
            color: "green"
          good:
            min: 70
            max: 85
            label: "GOOD"
            description: "Good emotional variation"
            color: "blue"
          acceptable:
            min: 53
            max: 69
            label: "ACCEPTABLE"
            description: "Moderate emotional range"
            color: "yellow"
          poor:
            min: 0
            max: 52
            label: "POOR"
            description: "Emotionally flat"
            color: "red"

        metric_bands:
          sentiment_variance:
            excellent:
              min: 0.18
              max: 999.0
              label: "EXCELLENT"
              description: "High variance"
            good:
              min: 0.13
              max: 0.17
              label: "GOOD"
              description: "Good variance"
            acceptable:
              min: 0.08
              max: 0.12
              label: "ACCEPTABLE"
              description: "Moderate variance"
            poor:
              min: 0.0
              max: 0.07
              label: "POOR"
              description: "Low variance"

          sentiment_mean:
            excellent:
              min: 0.12
              max: 0.40
              label: "EXCELLENT"
              description: "Balanced tone"
            good:
              min: 0.08
              max: 0.11
              label: "GOOD"
              description: "Slightly positive"
            acceptable:
              min: 0.04
              max: 0.07
              label: "ACCEPTABLE"
              description: "Mostly neutral"
            poor:
              min: 0.0
              max: 0.03
              label: "POOR"
              description: "Excessively neutral"

          emotionally_flat_ratio:
            excellent:
              min: 0.0
              max: 0.08
              label: "EXCELLENT"
              description: "Minimal flat affect"
            good:
              min: 0.09
              max: 0.12
              label: "GOOD"
              description: "Low flat affect"
            acceptable:
              min: 0.13
              max: 0.17
              label: "ACCEPTABLE"
              description: "Some flat affect"
            poor:
              min: 0.18
              max: 1.0
              label: "POOR"
              description: "High flat affect"

      structural:
        enabled: true
        weight: 1.5

        settings:
          blockquote_clustering_max: 0.4
          link_anchor_generic_max: 0.3

        dimension_bands:
          excellent:
            min: 88
            max: 100
            label: "EXCELLENT"
            description: "Natural structural patterns"
            color: "green"
          good:
            min: 72
            max: 87
            label: "GOOD"
            description: "Good structural variation"
            color: "blue"
          acceptable:
            min: 55
            max: 71
            label: "ACCEPTABLE"
            description: "Some patterns"
            color: "yellow"
          poor:
            min: 0
            max: 54
            label: "POOR"
            description: "AI structural signatures"
            color: "red"

        metric_bands:
          blockquote_clustering:
            excellent:
              min: 0.0
              max: 0.25
              label: "EXCELLENT"
              description: "Minimal clustering"
            good:
              min: 0.26
              max: 0.4
              label: "GOOD"
              description: "Low clustering"
            acceptable:
              min: 0.41
              max: 0.5
              label: "ACCEPTABLE"
              description: "Moderate clustering"
            poor:
              min: 0.51
              max: 1.0
              label: "POOR"
              description: "Heavy clustering"

          link_anchor_generic_ratio:
            excellent:
              min: 0.0
              max: 0.2
              label: "EXCELLENT"
              description: "Descriptive anchors"
            good:
              min: 0.21
              max: 0.3
              label: "GOOD"
              description: "Mostly descriptive"
            acceptable:
              min: 0.31
              max: 0.4
              label: "ACCEPTABLE"
              description: "Some generic anchors"
            poor:
              min: 0.41
              max: 1.0
              label: "POOR"
              description: "Many generic anchors"

  # ========================================================================
  # PERMISSIVE PROFILE - Lower sensitivity, fewer false positives
  # ========================================================================
  permissive:
    name: "Permissive Analysis"
    description: "Lower sensitivity, optimized for technical writing"

    global:
      detection_target: 40.0  # Higher acceptable risk
      quality_target: 75.0
      fail_on_weight_invalid: true
      parallel_execution: true
      max_workers: 10

    dimensions:
      perplexity:
        enabled: true
        weight: 4.0  # Reduced weight

        settings:
          ai_vocab_threshold_excellent: 2.0
          ai_vocab_threshold_good: 5.0
          ai_vocab_threshold_acceptable: 8.0
          formulaic_transitions_penalty: 3
          custom_vocab_patterns: []

        dimension_bands:
          excellent:
            min: 80
            max: 100
            label: "EXCELLENT"
            description: "Minimal AI vocabulary"
            color: "green"
          good:
            min: 65
            max: 79
            label: "GOOD"
            description: "Natural vocabulary"
            color: "blue"
          acceptable:
            min: 50
            max: 64
            label: "ACCEPTABLE"
            description: "Some AI vocabulary"
            color: "yellow"
          poor:
            min: 0
            max: 49
            label: "POOR"
            description: "Heavy AI vocabulary"
            color: "red"

        metric_bands:
          ai_vocabulary_per_1k:
            excellent:
              min: 0.0
              max: 2.0
              label: "EXCELLENT"
              description: "Minimal AI vocabulary"
            good:
              min: 2.1
              max: 5.0
              label: "GOOD"
              description: "Low AI vocabulary"
            acceptable:
              min: 5.1
              max: 8.0
              label: "ACCEPTABLE"
              description: "Moderate AI vocabulary"
            poor:
              min: 8.1
              max: 999.0
              label: "POOR"
              description: "Heavy AI vocabulary"

          formulaic_transitions_count:
            excellent:
              min: 0
              max: 3
              label: "EXCELLENT"
              description: "Minimal formulaic transitions"
            good:
              min: 4
              max: 6
              label: "GOOD"
              description: "Few formulaic transitions"
            acceptable:
              min: 7
              max: 10
              label: "ACCEPTABLE"
              description: "Some formulaic patterns"
            poor:
              min: 11
              max: 9999
              label: "POOR"
              description: "Many formulaic transitions"

      burstiness:
        enabled: true
        weight: 5.0

        settings:
          stdev_threshold_excellent: 8.0
          stdev_threshold_good: 5.5
          stdev_threshold_acceptable: 3.5
          cv_threshold_excellent: 0.35
          cv_threshold_good: 0.25
          cv_threshold_acceptable: 0.15

        dimension_bands:
          excellent:
            min: 82
            max: 100
            label: "EXCELLENT"
            description: "Varied sentence structure"
            color: "green"
          good:
            min: 66
            max: 81
            label: "GOOD"
            description: "Good variation"
            color: "blue"
          acceptable:
            min: 48
            max: 65
            label: "ACCEPTABLE"
            description: "Moderate variation"
            color: "yellow"
          poor:
            min: 0
            max: 47
            label: "POOR"
            description: "Uniform patterns"
            color: "red"

        metric_bands:
          sentence_stdev:
            excellent:
              min: 8.0
              max: 999.0
              label: "EXCELLENT"
              description: "High variation"
            good:
              min: 5.5
              max: 7.9
              label: "GOOD"
              description: "Good variation"
            acceptable:
              min: 3.5
              max: 5.4
              label: "ACCEPTABLE"
              description: "Moderate variation"
            poor:
              min: 0.0
              max: 3.4
              label: "POOR"
              description: "Uniform lengths"

          cv:
            excellent:
              min: 0.35
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent CV"
            good:
              min: 0.25
              max: 0.34
              label: "GOOD"
              description: "Good CV"
            acceptable:
              min: 0.15
              max: 0.24
              label: "ACCEPTABLE"
              description: "Moderate CV"
            poor:
              min: 0.0
              max: 0.14
              label: "POOR"
              description: "Low CV"

      structure:
        enabled: true
        weight: 3.0

        settings:
          max_heading_depth: 5  # Allow deeper
          formulaic_threshold: 5
          parallelism_penalty: 2

        dimension_bands:
          excellent:
            min: 84
            max: 100
            label: "EXCELLENT"
            description: "Natural structure"
            color: "green"
          good:
            min: 68
            max: 83
            label: "GOOD"
            description: "Well-structured"
            color: "blue"
          acceptable:
            min: 51
            max: 67
            label: "ACCEPTABLE"
            description: "Some patterns"
            color: "yellow"
          poor:
            min: 0
            max: 50
            label: "POOR"
            description: "Formulaic structure"
            color: "red"

        metric_bands:
          heading_depth:
            excellent:
              min: 0
              max: 4
              label: "EXCELLENT"
              description: "Good hierarchy"
            good:
              min: 5
              max: 5
              label: "GOOD"
              description: "Acceptable depth"
            acceptable:
              min: 6
              max: 6
              label: "ACCEPTABLE"
              description: "Slightly deep"
            poor:
              min: 7
              max: 999
              label: "POOR"
              description: "Very deep hierarchy"

          formulaic_count:
            excellent:
              min: 0
              max: 3
              label: "EXCELLENT"
              description: "Minimal patterns"
            good:
              min: 4
              max: 5
              label: "GOOD"
              description: "Few patterns"
            acceptable:
              min: 6
              max: 8
              label: "ACCEPTABLE"
              description: "Some patterns"
            poor:
              min: 9
              max: 9999
              label: "POOR"
              description: "Many patterns"

          parallelism_score:
            excellent:
              min: 0
              max: 8
              label: "EXCELLENT"
              description: "Low parallelism"
            good:
              min: 9
              max: 14
              label: "GOOD"
              description: "Moderate parallelism"
            acceptable:
              min: 15
              max: 20
              label: "ACCEPTABLE"
              description: "Noticeable parallelism"
            poor:
              min: 21
              max: 9999
              label: "POOR"
              description: "Heavy parallelism"

      formatting:
        enabled: true
        weight: 3.0

        settings:
          em_dash_max_per_page: 4.0  # More permissive
          bold_per_1k_max: 8.0
          italic_per_1k_max: 12.0

        dimension_bands:
          excellent:
            min: 85
            max: 100
            label: "EXCELLENT"
            description: "Natural formatting"
            color: "green"
          good:
            min: 70
            max: 84
            label: "GOOD"
            description: "Balanced formatting"
            color: "blue"
          acceptable:
            min: 54
            max: 69
            label: "ACCEPTABLE"
            description: "Moderate formatting"
            color: "yellow"
          poor:
            min: 0
            max: 53
            label: "POOR"
            description: "Excessive formatting"
            color: "red"

        metric_bands:
          em_dash_per_page:
            excellent:
              min: 0.0
              max: 2.5
              label: "EXCELLENT"
              description: "Light em-dash usage"
            good:
              min: 2.6
              max: 4.0
              label: "GOOD"
              description: "Moderate em-dash usage"
            acceptable:
              min: 4.1
              max: 5.5
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 5.6
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          bold_per_1k:
            excellent:
              min: 0.0
              max: 5.0
              label: "EXCELLENT"
              description: "Light bold"
            good:
              min: 5.1
              max: 8.0
              label: "GOOD"
              description: "Moderate bold"
            acceptable:
              min: 8.1
              max: 11.0
              label: "ACCEPTABLE"
              description: "Higher bold"
            poor:
              min: 11.1
              max: 999.0
              label: "POOR"
              description: "Heavy bold"

          italic_per_1k:
            excellent:
              min: 0.0
              max: 8.0
              label: "EXCELLENT"
              description: "Light italic"
            good:
              min: 8.1
              max: 12.0
              label: "GOOD"
              description: "Moderate italic"
            acceptable:
              min: 12.1
              max: 16.0
              label: "ACCEPTABLE"
              description: "Higher italic"
            poor:
              min: 16.1
              max: 999.0
              label: "POOR"
              description: "Heavy italic"

      voice:
        enabled: true
        weight: 4.0

        settings:
          first_person_weight: 1.0
          contractions_weight: 0.5
          direct_address_weight: 0.3

        dimension_bands:
          excellent:
            min: 80
            max: 100
            label: "EXCELLENT"
            description: "Human voice"
            color: "green"
          good:
            min: 63
            max: 79
            label: "GOOD"
            description: "Natural voice"
            color: "blue"
          acceptable:
            min: 45
            max: 62
            label: "ACCEPTABLE"
            description: "Somewhat impersonal"
            color: "yellow"
          poor:
            min: 0
            max: 44
            label: "POOR"
            description: "Formal voice"
            color: "red"

        metric_bands:
          first_person_count:
            excellent:
              min: 4
              max: 9999
              label: "EXCELLENT"
              description: "Good first-person presence"
            good:
              min: 2
              max: 3
              label: "GOOD"
              description: "Some first-person"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Minimal first-person"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No first-person"

          contractions_count:
            excellent:
              min: 3
              max: 9999
              label: "EXCELLENT"
              description: "Natural contractions"
            good:
              min: 1
              max: 2
              label: "GOOD"
              description: "Some contractions"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Few contractions"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No contractions"

          direct_address_count:
            excellent:
              min: 2
              max: 9999
              label: "EXCELLENT"
              description: "Good engagement"
            good:
              min: 1
              max: 1
              label: "GOOD"
              description: "Some engagement"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Minimal engagement"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No engagement"

      syntactic:
        enabled: true
        weight: 2.0

        settings:
          subordination_threshold: 0.15
          dependency_depth_min: 1.5

        dimension_bands:
          excellent:
            min: 82
            max: 100
            label: "EXCELLENT"
            description: "Complex syntax"
            color: "green"
          good:
            min: 65
            max: 81
            label: "GOOD"
            description: "Good complexity"
            color: "blue"
          acceptable:
            min: 48
            max: 64
            label: "ACCEPTABLE"
            description: "Moderate complexity"
            color: "yellow"
          poor:
            min: 0
            max: 47
            label: "POOR"
            description: "Simple syntax"
            color: "red"

        metric_bands:
          subordination_index:
            excellent:
              min: 0.15
              max: 999.0
              label: "EXCELLENT"
              description: "High subordination"
            good:
              min: 0.10
              max: 0.14
              label: "GOOD"
              description: "Good subordination"
            acceptable:
              min: 0.05
              max: 0.09
              label: "ACCEPTABLE"
              description: "Moderate subordination"
            poor:
              min: 0.0
              max: 0.04
              label: "POOR"
              description: "Low subordination"

          dependency_depth:
            excellent:
              min: 1.5
              max: 999.0
              label: "EXCELLENT"
              description: "Good depth"
            good:
              min: 1.0
              max: 1.4
              label: "GOOD"
              description: "Moderate depth"
            acceptable:
              min: 0.5
              max: 0.9
              label: "ACCEPTABLE"
              description: "Shallow depth"
            poor:
              min: 0.0
              max: 0.4
              label: "POOR"
              description: "Very shallow"

      lexical:
        enabled: true
        weight: 3.0

        settings:
          diversity_threshold_excellent: 0.45
          diversity_threshold_good: 0.35
          mtld_threshold_excellent: 140
          mtld_threshold_good: 100

        dimension_bands:
          excellent:
            min: 83
            max: 100
            label: "EXCELLENT"
            description: "Rich vocabulary"
            color: "green"
          good:
            min: 67
            max: 82
            label: "GOOD"
            description: "Good diversity"
            color: "blue"
          acceptable:
            min: 50
            max: 66
            label: "ACCEPTABLE"
            description: "Moderate range"
            color: "yellow"
          poor:
            min: 0
            max: 49
            label: "POOR"
            description: "Limited vocabulary"
            color: "red"

        metric_bands:
          diversity_score:
            excellent:
              min: 0.45
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent diversity"
            good:
              min: 0.35
              max: 0.44
              label: "GOOD"
              description: "Good diversity"
            acceptable:
              min: 0.25
              max: 0.34
              label: "ACCEPTABLE"
              description: "Moderate diversity"
            poor:
              min: 0.0
              max: 0.24
              label: "POOR"
              description: "Low diversity"

          mtld_score:
            excellent:
              min: 140
              max: 9999
              label: "EXCELLENT"
              description: "Excellent MTLD"
            good:
              min: 100
              max: 139
              label: "GOOD"
              description: "Good MTLD"
            acceptable:
              min: 60
              max: 99
              label: "ACCEPTABLE"
              description: "Moderate MTLD"
            poor:
              min: 0
              max: 59
              label: "POOR"
              description: "Low MTLD"

      stylometric:
        enabled: true
        weight: 4.0

        settings:
          however_per_1k_max: 2.0
          moreover_per_1k_max: 1.5
          passive_voice_max: 20

        dimension_bands:
          excellent:
            min: 87
            max: 100
            label: "EXCELLENT"
            description: "Natural style"
            color: "green"
          good:
            min: 72
            max: 86
            label: "GOOD"
            description: "Good style"
            color: "blue"
          acceptable:
            min: 56
            max: 71
            label: "ACCEPTABLE"
            description: "Some AI patterns"
            color: "yellow"
          poor:
            min: 0
            max: 55
            label: "POOR"
            description: "AI markers"
            color: "red"

        metric_bands:
          however_per_1k:
            excellent:
              min: 0.0
              max: 1.2
              label: "EXCELLENT"
              description: "Light 'however'"
            good:
              min: 1.3
              max: 2.0
              label: "GOOD"
              description: "Moderate usage"
            acceptable:
              min: 2.1
              max: 2.8
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 2.9
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          moreover_per_1k:
            excellent:
              min: 0.0
              max: 0.8
              label: "EXCELLENT"
              description: "Light 'moreover'"
            good:
              min: 0.9
              max: 1.5
              label: "GOOD"
              description: "Moderate usage"
            acceptable:
              min: 1.6
              max: 2.2
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 2.3
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          passive_voice_percent:
            excellent:
              min: 0.0
              max: 12.0
              label: "EXCELLENT"
              description: "Low passive voice"
            good:
              min: 12.1
              max: 20.0
              label: "GOOD"
              description: "Moderate passive voice"
            acceptable:
              min: 20.1
              max: 28.0
              label: "ACCEPTABLE"
              description: "Higher passive voice"
            poor:
              min: 28.1
              max: 100.0
              label: "POOR"
              description: "Heavy passive voice"

      advanced:
        enabled: true
        weight: 35.0

        settings:
          gltr_top10_max: 75  # More permissive
          mattr_threshold_excellent: 0.65
          mattr_threshold_good: 0.55
          rttr_threshold_excellent: 6.5
          rttr_threshold_good: 5.0

        dimension_bands:
          excellent:
            min: 84
            max: 100
            label: "EXCELLENT"
            description: "Human-like patterns"
            color: "green"
          good:
            min: 68
            max: 83
            label: "GOOD"
            description: "Good patterns"
            color: "blue"
          acceptable:
            min: 51
            max: 67
            label: "ACCEPTABLE"
            description: "Moderate AI patterns"
            color: "yellow"
          poor:
            min: 0
            max: 50
            label: "POOR"
            description: "AI signatures"
            color: "red"

        metric_bands:
          gltr_top10_percent:
            excellent:
              min: 0.0
              max: 60.0
              label: "EXCELLENT"
              description: "Low GLTR"
            good:
              min: 60.1
              max: 75.0
              label: "GOOD"
              description: "Moderate GLTR"
            acceptable:
              min: 75.1
              max: 85.0
              label: "ACCEPTABLE"
              description: "Higher GLTR"
            poor:
              min: 85.1
              max: 100.0
              label: "POOR"
              description: "High GLTR"

          mattr_score:
            excellent:
              min: 0.65
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent MATTR"
            good:
              min: 0.55
              max: 0.64
              label: "GOOD"
              description: "Good MATTR"
            acceptable:
              min: 0.45
              max: 0.54
              label: "ACCEPTABLE"
              description: "Moderate MATTR"
            poor:
              min: 0.0
              max: 0.44
              label: "POOR"
              description: "Low MATTR"

          rttr_score:
            excellent:
              min: 6.5
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent RTTR"
            good:
              min: 5.0
              max: 6.4
              label: "GOOD"
              description: "Good RTTR"
            acceptable:
              min: 3.5
              max: 4.9
              label: "ACCEPTABLE"
              description: "Moderate RTTR"
            poor:
              min: 0.0
              max: 3.4
              label: "POOR"
              description: "Low RTTR"

      sentiment:
        enabled: true
        weight: 4.0

        settings:
          variance_threshold_excellent: 0.15
          variance_threshold_good: 0.10
          emotionally_flat_threshold: 0.15

        dimension_bands:
          excellent:
            min: 81
            max: 100
            label: "EXCELLENT"
            description: "Rich emotional content"
            color: "green"
          good:
            min: 64
            max: 80
            label: "GOOD"
            description: "Good emotional variation"
            color: "blue"
          acceptable:
            min: 46
            max: 63
            label: "ACCEPTABLE"
            description: "Moderate range"
            color: "yellow"
          poor:
            min: 0
            max: 45
            label: "POOR"
            description: "Emotionally flat"
            color: "red"

        metric_bands:
          sentiment_variance:
            excellent:
              min: 0.15
              max: 999.0
              label: "EXCELLENT"
              description: "High variance"
            good:
              min: 0.10
              max: 0.14
              label: "GOOD"
              description: "Good variance"
            acceptable:
              min: 0.05
              max: 0.09
              label: "ACCEPTABLE"
              description: "Moderate variance"
            poor:
              min: 0.0
              max: 0.04
              label: "POOR"
              description: "Low variance"

          sentiment_mean:
            excellent:
              min: 0.10
              max: 0.35
              label: "EXCELLENT"
              description: "Balanced tone"
            good:
              min: 0.06
              max: 0.09
              label: "GOOD"
              description: "Slightly positive"
            acceptable:
              min: 0.03
              max: 0.05
              label: "ACCEPTABLE"
              description: "Mostly neutral"
            poor:
              min: 0.0
              max: 0.02
              label: "POOR"
              description: "Overly neutral"

          emotionally_flat_ratio:
            excellent:
              min: 0.0
              max: 0.10
              label: "EXCELLENT"
              description: "Minimal flat affect"
            good:
              min: 0.11
              max: 0.15
              label: "GOOD"
              description: "Low flat affect"
            acceptable:
              min: 0.16
              max: 0.22
              label: "ACCEPTABLE"
              description: "Some flat affect"
            poor:
              min: 0.23
              max: 1.0
              label: "POOR"
              description: "High flat affect"

      structural:
        enabled: true
        weight: 1.0

        settings:
          blockquote_clustering_max: 0.6
          link_anchor_generic_max: 0.5

        dimension_bands:
          excellent:
            min: 83
            max: 100
            label: "EXCELLENT"
            description: "Natural patterns"
            color: "green"
          good:
            min: 66
            max: 82
            label: "GOOD"
            description: "Good variation"
            color: "blue"
          acceptable:
            min: 48
            max: 65
            label: "ACCEPTABLE"
            description: "Some patterns"
            color: "yellow"
          poor:
            min: 0
            max: 47
            label: "POOR"
            description: "AI signatures"
            color: "red"

        metric_bands:
          blockquote_clustering:
            excellent:
              min: 0.0
              max: 0.35
              label: "EXCELLENT"
              description: "Low clustering"
            good:
              min: 0.36
              max: 0.6
              label: "GOOD"
              description: "Moderate clustering"
            acceptable:
              min: 0.61
              max: 0.75
              label: "ACCEPTABLE"
              description: "Higher clustering"
            poor:
              min: 0.76
              max: 1.0
              label: "POOR"
              description: "Heavy clustering"

          link_anchor_generic_ratio:
            excellent:
              min: 0.0
              max: 0.3
              label: "EXCELLENT"
              description: "Descriptive anchors"
            good:
              min: 0.31
              max: 0.5
              label: "GOOD"
              description: "Mostly descriptive"
            acceptable:
              min: 0.51
              max: 0.65
              label: "ACCEPTABLE"
              description: "Some generic"
            poor:
              min: 0.66
              max: 1.0
              label: "POOR"
              description: "Many generic anchors"

  # ========================================================================
  # TECHNICAL PROFILE - Optimized for technical documentation
  # ========================================================================
  technical:
    name: "Technical Documentation"
    description: "Optimized for technical writing, code docs, tutorials"

    global:
      detection_target: 35.0
      quality_target: 80.0
      fail_on_weight_invalid: true
      parallel_execution: true
      max_workers: 10

    dimensions:
      perplexity:
        enabled: true
        weight: 3.0  # Lower - technical writing uses different vocab

        settings:
          ai_vocab_threshold_excellent: 3.0
          ai_vocab_threshold_good: 6.0
          ai_vocab_threshold_acceptable: 10.0
          formulaic_transitions_penalty: 2
          # Allow technical terms that might seem AI-like
          custom_vocab_patterns: []

        dimension_bands:
          excellent:
            min: 75
            max: 100
            label: "EXCELLENT"
            description: "Natural technical vocabulary"
            color: "green"
          good:
            min: 58
            max: 74
            label: "GOOD"
            description: "Good technical language"
            color: "blue"
          acceptable:
            min: 40
            max: 57
            label: "ACCEPTABLE"
            description: "Acceptable for technical content"
            color: "yellow"
          poor:
            min: 0
            max: 39
            label: "POOR"
            description: "Heavy AI vocabulary"
            color: "red"

        metric_bands:
          ai_vocabulary_per_1k:
            excellent:
              min: 0.0
              max: 3.0
              label: "EXCELLENT"
              description: "Low AI vocabulary (technical terms OK)"
            good:
              min: 3.1
              max: 6.0
              label: "GOOD"
              description: "Acceptable technical vocabulary"
            acceptable:
              min: 6.1
              max: 10.0
              label: "ACCEPTABLE"
              description: "Moderate AI vocabulary"
            poor:
              min: 10.1
              max: 999.0
              label: "POOR"
              description: "Heavy AI vocabulary"

          formulaic_transitions_count:
            excellent:
              min: 0
              max: 4
              label: "EXCELLENT"
              description: "Minimal formulaic transitions"
            good:
              min: 5
              max: 8
              label: "GOOD"
              description: "Few formulaic transitions"
            acceptable:
              min: 9
              max: 12
              label: "ACCEPTABLE"
              description: "Some formulaic patterns"
            poor:
              min: 13
              max: 9999
              label: "POOR"
              description: "Many formulaic transitions"

      burstiness:
        enabled: true
        weight: 4.0  # Lower - technical writing more uniform

        settings:
          stdev_threshold_excellent: 7.0
          stdev_threshold_good: 5.0
          stdev_threshold_acceptable: 3.0
          cv_threshold_excellent: 0.30
          cv_threshold_good: 0.20
          cv_threshold_acceptable: 0.12

        dimension_bands:
          excellent:
            min: 78
            max: 100
            label: "EXCELLENT"
            description: "Good variation for technical writing"
            color: "green"
          good:
            min: 60
            max: 77
            label: "GOOD"
            description: "Acceptable variation"
            color: "blue"
          acceptable:
            min: 42
            max: 59
            label: "ACCEPTABLE"
            description: "Moderate variation (common in tech docs)"
            color: "yellow"
          poor:
            min: 0
            max: 41
            label: "POOR"
            description: "Very uniform patterns"
            color: "red"

        metric_bands:
          sentence_stdev:
            excellent:
              min: 7.0
              max: 999.0
              label: "EXCELLENT"
              description: "Good variation"
            good:
              min: 5.0
              max: 6.9
              label: "GOOD"
              description: "Moderate variation"
            acceptable:
              min: 3.0
              max: 4.9
              label: "ACCEPTABLE"
              description: "Lower variation (OK for tech)"
            poor:
              min: 0.0
              max: 2.9
              label: "POOR"
              description: "Very uniform"

          cv:
            excellent:
              min: 0.30
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent CV"
            good:
              min: 0.20
              max: 0.29
              label: "GOOD"
              description: "Good CV"
            acceptable:
              min: 0.12
              max: 0.19
              label: "ACCEPTABLE"
              description: "Acceptable CV for tech"
            poor:
              min: 0.0
              max: 0.11
              label: "POOR"
              description: "Low CV"

      structure:
        enabled: true
        weight: 6.0  # Higher - structure important in tech docs

        settings:
          max_heading_depth: 6  # Allow deep nesting for APIs
          formulaic_threshold: 8  # Allow more structure
          parallelism_penalty: 1  # Parallel headings OK in tech docs

        dimension_bands:
          excellent:
            min: 80
            max: 100
            label: "EXCELLENT"
            description: "Well-structured technical content"
            color: "green"
          good:
            min: 62
            max: 79
            label: "GOOD"
            description: "Good technical structure"
            color: "blue"
          acceptable:
            min: 44
            max: 61
            label: "ACCEPTABLE"
            description: "Acceptable structure (formulaic OK for tech)"
            color: "yellow"
          poor:
            min: 0
            max: 43
            label: "POOR"
            description: "Overly rigid structure"
            color: "red"

        metric_bands:
          heading_depth:
            excellent:
              min: 0
              max: 5
              label: "EXCELLENT"
              description: "Good hierarchy for tech docs"
            good:
              min: 6
              max: 6
              label: "GOOD"
              description: "Deep but acceptable (APIs, specs)"
            acceptable:
              min: 7
              max: 8
              label: "ACCEPTABLE"
              description: "Very deep (complex technical content)"
            poor:
              min: 9
              max: 999
              label: "POOR"
              description: "Excessively deep hierarchy"

          formulaic_count:
            excellent:
              min: 0
              max: 6
              label: "EXCELLENT"
              description: "Minimal formulaic patterns"
            good:
              min: 7
              max: 8
              label: "GOOD"
              description: "Few patterns (OK for tech)"
            acceptable:
              min: 9
              max: 12
              label: "ACCEPTABLE"
              description: "Some patterns (common in tech docs)"
            poor:
              min: 13
              max: 9999
              label: "POOR"
              description: "Too many formulaic patterns"

          parallelism_score:
            excellent:
              min: 0
              max: 15
              label: "EXCELLENT"
              description: "Low parallelism"
            good:
              min: 16
              max: 25
              label: "GOOD"
              description: "Moderate parallelism (OK for tech)"
            acceptable:
              min: 26
              max: 35
              label: "ACCEPTABLE"
              description: "Higher parallelism (common in APIs)"
            poor:
              min: 36
              max: 9999
              label: "POOR"
              description: "Excessive parallelism"

      formatting:
        enabled: true
        weight: 5.0

        settings:
          em_dash_max_per_page: 3.0
          bold_per_1k_max: 15.0  # Code/API names often bolded
          italic_per_1k_max: 10.0

        dimension_bands:
          excellent:
            min: 82
            max: 100
            label: "EXCELLENT"
            description: "Natural formatting for technical content"
            color: "green"
          good:
            min: 66
            max: 81
            label: "GOOD"
            description: "Good technical formatting"
            color: "blue"
          acceptable:
            min: 48
            max: 65
            label: "ACCEPTABLE"
            description: "Higher formatting (code emphasis OK)"
            color: "yellow"
          poor:
            min: 0
            max: 47
            label: "POOR"
            description: "Excessive formatting"
            color: "red"

        metric_bands:
          em_dash_per_page:
            excellent:
              min: 0.0
              max: 2.0
              label: "EXCELLENT"
              description: "Light em-dash usage"
            good:
              min: 2.1
              max: 3.0
              label: "GOOD"
              description: "Moderate em-dash"
            acceptable:
              min: 3.1
              max: 4.5
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 4.6
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          bold_per_1k:
            excellent:
              min: 0.0
              max: 10.0
              label: "EXCELLENT"
              description: "Good bold usage (code/API names)"
            good:
              min: 10.1
              max: 15.0
              label: "GOOD"
              description: "Moderate bold (OK for tech)"
            acceptable:
              min: 15.1
              max: 20.0
              label: "ACCEPTABLE"
              description: "Higher bold"
            poor:
              min: 20.1
              max: 999.0
              label: "POOR"
              description: "Excessive bold"

          italic_per_1k:
            excellent:
              min: 0.0
              max: 7.0
              label: "EXCELLENT"
              description: "Light italic"
            good:
              min: 7.1
              max: 10.0
              label: "GOOD"
              description: "Moderate italic"
            acceptable:
              min: 10.1
              max: 14.0
              label: "ACCEPTABLE"
              description: "Higher italic"
            poor:
              min: 14.1
              max: 999.0
              label: "POOR"
              description: "Heavy italic"

      voice:
        enabled: true
        weight: 3.0  # Lower - technical writing less personal

        settings:
          first_person_weight: 0.5
          contractions_weight: 0.3
          direct_address_weight: 1.0  # "You" common in tutorials

        dimension_bands:
          excellent:
            min: 76
            max: 100
            label: "EXCELLENT"
            description: "Good voice for technical content"
            color: "green"
          good:
            min: 58
            max: 75
            label: "GOOD"
            description: "Acceptable technical voice"
            color: "blue"
          acceptable:
            min: 38
            max: 57
            label: "ACCEPTABLE"
            description: "Formal (common in tech docs)"
            color: "yellow"
          poor:
            min: 0
            max: 37
            label: "POOR"
            description: "Very impersonal"
            color: "red"

        metric_bands:
          first_person_count:
            excellent:
              min: 3
              max: 9999
              label: "EXCELLENT"
              description: "Good first-person (tutorials)"
            good:
              min: 1
              max: 2
              label: "GOOD"
              description: "Some first-person"
            acceptable:
              min: 0
              max: 0
              label: "ACCEPTABLE"
              description: "No first-person (OK for tech)"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No first-person"

          contractions_count:
            excellent:
              min: 2
              max: 9999
              label: "EXCELLENT"
              description: "Some contractions"
            good:
              min: 1
              max: 1
              label: "GOOD"
              description: "Minimal contractions"
            acceptable:
              min: 0
              max: 0
              label: "ACCEPTABLE"
              description: "No contractions (OK for formal tech)"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No contractions"

          direct_address_count:
            excellent:
              min: 4
              max: 9999
              label: "EXCELLENT"
              description: "Good reader engagement (tutorials)"
            good:
              min: 2
              max: 3
              label: "GOOD"
              description: "Some engagement"
            acceptable:
              min: 1
              max: 1
              label: "ACCEPTABLE"
              description: "Minimal engagement"
            poor:
              min: 0
              max: 0
              label: "POOR"
              description: "No engagement"

      syntactic:
        enabled: true
        weight: 2.0

        settings:
          subordination_threshold: 0.18
          dependency_depth_min: 1.8

        dimension_bands:
          excellent:
            min: 80
            max: 100
            label: "EXCELLENT"
            description: "Complex syntax"
            color: "green"
          good:
            min: 62
            max: 79
            label: "GOOD"
            description: "Good complexity"
            color: "blue"
          acceptable:
            min: 43
            max: 61
            label: "ACCEPTABLE"
            description: "Moderate complexity (OK for tech)"
            color: "yellow"
          poor:
            min: 0
            max: 42
            label: "POOR"
            description: "Simple syntax"
            color: "red"

        metric_bands:
          subordination_index:
            excellent:
              min: 0.18
              max: 999.0
              label: "EXCELLENT"
              description: "High subordination"
            good:
              min: 0.12
              max: 0.17
              label: "GOOD"
              description: "Good subordination"
            acceptable:
              min: 0.06
              max: 0.11
              label: "ACCEPTABLE"
              description: "Moderate subordination"
            poor:
              min: 0.0
              max: 0.05
              label: "POOR"
              description: "Low subordination"

          dependency_depth:
            excellent:
              min: 1.8
              max: 999.0
              label: "EXCELLENT"
              description: "Good depth"
            good:
              min: 1.2
              max: 1.7
              label: "GOOD"
              description: "Moderate depth"
            acceptable:
              min: 0.6
              max: 1.1
              label: "ACCEPTABLE"
              description: "Lower depth (OK for tech)"
            poor:
              min: 0.0
              max: 0.5
              label: "POOR"
              description: "Very shallow"

      lexical:
        enabled: true
        weight: 5.0  # Higher - domain vocabulary important

        settings:
          diversity_threshold_excellent: 0.60  # Technical terms
          diversity_threshold_good: 0.50
          mtld_threshold_excellent: 200  # Rich technical vocabulary
          mtld_threshold_good: 150

        dimension_bands:
          excellent:
            min: 86
            max: 100
            label: "EXCELLENT"
            description: "Rich technical vocabulary"
            color: "green"
          good:
            min: 70
            max: 85
            label: "GOOD"
            description: "Good domain vocabulary"
            color: "blue"
          acceptable:
            min: 53
            max: 69
            label: "ACCEPTABLE"
            description: "Moderate vocabulary range"
            color: "yellow"
          poor:
            min: 0
            max: 52
            label: "POOR"
            description: "Limited vocabulary"
            color: "red"

        metric_bands:
          diversity_score:
            excellent:
              min: 0.60
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent diversity (technical terms)"
            good:
              min: 0.50
              max: 0.59
              label: "GOOD"
              description: "Good diversity"
            acceptable:
              min: 0.40
              max: 0.49
              label: "ACCEPTABLE"
              description: "Moderate diversity"
            poor:
              min: 0.0
              max: 0.39
              label: "POOR"
              description: "Low diversity"

          mtld_score:
            excellent:
              min: 200
              max: 9999
              label: "EXCELLENT"
              description: "Excellent MTLD (rich technical vocab)"
            good:
              min: 150
              max: 199
              label: "GOOD"
              description: "Good MTLD"
            acceptable:
              min: 100
              max: 149
              label: "ACCEPTABLE"
              description: "Moderate MTLD"
            poor:
              min: 0
              max: 99
              label: "POOR"
              description: "Low MTLD"

      stylometric:
        enabled: true
        weight: 3.0

        settings:
          however_per_1k_max: 2.5
          moreover_per_1k_max: 2.0
          passive_voice_max: 25  # Passive voice common in tech

        dimension_bands:
          excellent:
            min: 84
            max: 100
            label: "EXCELLENT"
            description: "Natural technical style"
            color: "green"
          good:
            min: 68
            max: 83
            label: "GOOD"
            description: "Good technical style"
            color: "blue"
          acceptable:
            min: 50
            max: 67
            label: "ACCEPTABLE"
            description: "Acceptable (formal tech OK)"
            color: "yellow"
          poor:
            min: 0
            max: 49
            label: "POOR"
            description: "Heavy AI markers"
            color: "red"

        metric_bands:
          however_per_1k:
            excellent:
              min: 0.0
              max: 1.5
              label: "EXCELLENT"
              description: "Light 'however'"
            good:
              min: 1.6
              max: 2.5
              label: "GOOD"
              description: "Moderate usage (OK for tech)"
            acceptable:
              min: 2.6
              max: 3.5
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 3.6
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          moreover_per_1k:
            excellent:
              min: 0.0
              max: 1.2
              label: "EXCELLENT"
              description: "Light 'moreover'"
            good:
              min: 1.3
              max: 2.0
              label: "GOOD"
              description: "Moderate usage"
            acceptable:
              min: 2.1
              max: 2.8
              label: "ACCEPTABLE"
              description: "Higher usage"
            poor:
              min: 2.9
              max: 999.0
              label: "POOR"
              description: "Heavy usage"

          passive_voice_percent:
            excellent:
              min: 0.0
              max: 15.0
              label: "EXCELLENT"
              description: "Low passive voice"
            good:
              min: 15.1
              max: 25.0
              label: "GOOD"
              description: "Moderate passive (OK for tech)"
            acceptable:
              min: 25.1
              max: 35.0
              label: "ACCEPTABLE"
              description: "Higher passive (common in tech)"
            poor:
              min: 35.1
              max: 100.0
              label: "POOR"
              description: "Very heavy passive voice"

      advanced:
        enabled: true
        weight: 30.0

        settings:
          gltr_top10_max: 70
          mattr_threshold_excellent: 0.68
          mattr_threshold_good: 0.58
          rttr_threshold_excellent: 7.0
          rttr_threshold_good: 5.5

        dimension_bands:
          excellent:
            min: 82
            max: 100
            label: "EXCELLENT"
            description: "Human-like technical patterns"
            color: "green"
          good:
            min: 66
            max: 81
            label: "GOOD"
            description: "Good statistical patterns"
            color: "blue"
          acceptable:
            min: 48
            max: 65
            label: "ACCEPTABLE"
            description: "Moderate AI patterns"
            color: "yellow"
          poor:
            min: 0
            max: 47
            label: "POOR"
            description: "AI signatures"
            color: "red"

        metric_bands:
          gltr_top10_percent:
            excellent:
              min: 0.0
              max: 55.0
              label: "EXCELLENT"
              description: "Low GLTR"
            good:
              min: 55.1
              max: 70.0
              label: "GOOD"
              description: "Moderate GLTR"
            acceptable:
              min: 70.1
              max: 80.0
              label: "ACCEPTABLE"
              description: "Higher GLTR"
            poor:
              min: 80.1
              max: 100.0
              label: "POOR"
              description: "High GLTR"

          mattr_score:
            excellent:
              min: 0.68
              max: 1.0
              label: "EXCELLENT"
              description: "Excellent MATTR"
            good:
              min: 0.58
              max: 0.67
              label: "GOOD"
              description: "Good MATTR"
            acceptable:
              min: 0.48
              max: 0.57
              label: "ACCEPTABLE"
              description: "Moderate MATTR"
            poor:
              min: 0.0
              max: 0.47
              label: "POOR"
              description: "Low MATTR"

          rttr_score:
            excellent:
              min: 7.0
              max: 999.0
              label: "EXCELLENT"
              description: "Excellent RTTR"
            good:
              min: 5.5
              max: 6.9
              label: "GOOD"
              description: "Good RTTR"
            acceptable:
              min: 4.0
              max: 5.4
              label: "ACCEPTABLE"
              description: "Moderate RTTR"
            poor:
              min: 0.0
              max: 3.9
              label: "POOR"
              description: "Low RTTR"

      sentiment:
        enabled: true
        weight: 3.0  # Lower - technical writing more neutral

        settings:
          variance_threshold_excellent: 0.12
          variance_threshold_good: 0.08
          emotionally_flat_threshold: 0.20  # Allow flat affect

        dimension_bands:
          excellent:
            min: 78
            max: 100
            label: "EXCELLENT"
            description: "Good emotional variation"
            color: "green"
          good:
            min: 60
            max: 77
            label: "GOOD"
            description: "Moderate variation"
            color: "blue"
          acceptable:
            min: 40
            max: 59
            label: "ACCEPTABLE"
            description: "Neutral tone (OK for tech)"
            color: "yellow"
          poor:
            min: 0
            max: 39
            label: "POOR"
            description: "Very flat affect"
            color: "red"

        metric_bands:
          sentiment_variance:
            excellent:
              min: 0.12
              max: 999.0
              label: "EXCELLENT"
              description: "Good variance"
            good:
              min: 0.08
              max: 0.11
              label: "GOOD"
              description: "Moderate variance"
            acceptable:
              min: 0.04
              max: 0.07
              label: "ACCEPTABLE"
              description: "Low variance (OK for tech)"
            poor:
              min: 0.0
              max: 0.03
              label: "POOR"
              description: "Very low variance"

          sentiment_mean:
            excellent:
              min: 0.08
              max: 0.30
              label: "EXCELLENT"
              description: "Balanced tone"
            good:
              min: 0.04
              max: 0.07
              label: "GOOD"
              description: "Slightly positive"
            acceptable:
              min: 0.01
              max: 0.03
              label: "ACCEPTABLE"
              description: "Mostly neutral (OK for tech)"
            poor:
              min: 0.0
              max: 0.0
              label: "POOR"
              description: "Completely neutral"

          emotionally_flat_ratio:
            excellent:
              min: 0.0
              max: 0.12
              label: "EXCELLENT"
              description: "Minimal flat affect"
            good:
              min: 0.13
              max: 0.20
              label: "GOOD"
              description: "Low flat affect (OK for tech)"
            acceptable:
              min: 0.21
              max: 0.30
              label: "ACCEPTABLE"
              description: "Higher flat affect (common in tech)"
            poor:
              min: 0.31
              max: 1.0
              label: "POOR"
              description: "Very flat affect"

      structural:
        enabled: true
        weight: 2.0

        settings:
          blockquote_clustering_max: 0.5
          link_anchor_generic_max: 0.4

        dimension_bands:
          excellent:
            min: 81
            max: 100
            label: "EXCELLENT"
            description: "Natural structural patterns"
            color: "green"
          good:
            min: 64
            max: 80
            label: "GOOD"
            description: "Good structural variation"
            color: "blue"
          acceptable:
            min: 45
            max: 63
            label: "ACCEPTABLE"
            description: "Some patterns (OK for tech)"
            color: "yellow"
          poor:
            min: 0
            max: 44
            label: "POOR"
            description: "AI structural signatures"
            color: "red"

        metric_bands:
          blockquote_clustering:
            excellent:
              min: 0.0
              max: 0.3
              label: "EXCELLENT"
              description: "Low clustering"
            good:
              min: 0.31
              max: 0.5
              label: "GOOD"
              description: "Moderate clustering"
            acceptable:
              min: 0.51
              max: 0.65
              label: "ACCEPTABLE"
              description: "Higher clustering (code examples)"
            poor:
              min: 0.66
              max: 1.0
              label: "POOR"
              description: "Heavy clustering"

          link_anchor_generic_ratio:
            excellent:
              min: 0.0
              max: 0.25
              label: "EXCELLENT"
              description: "Descriptive anchors"
            good:
              min: 0.26
              max: 0.4
              label: "GOOD"
              description: "Mostly descriptive"
            acceptable:
              min: 0.41
              max: 0.55
              label: "ACCEPTABLE"
              description: "Some generic (API docs OK)"
            poor:
              min: 0.56
              max: 1.0
              label: "POOR"
              description: "Many generic anchors"
```

---

## New Stories for Configuration Management

### 📦 STORY 10: Configuration Schema & Base Infrastructure

**Priority:** P0 (Foundation - prerequisite for config system)
**Story Points:** 5
**Dependencies:** None

#### Description

**As a** system architect
**I want** a configuration schema and manager
**So that** dimensions can declare and retrieve their settings

#### Acceptance Criteria

1. Config schema defined (YAML format)
2. `ConfigManager` class for loading/managing configs
3. Support for multiple profiles
4. Config validation against schema
5. Default config file created
6. Environment variable override support

#### Implementation

```python
# core/config_manager.py

from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
from dataclasses import dataclass
import os

@dataclass
class DimensionConfig:
    """Configuration for a single dimension."""
    enabled: bool
    weight: float
    settings: Dict[str, Any]

@dataclass
class GlobalConfig:
    """Global analysis configuration."""
    detection_target: float
    quality_target: float
    fail_on_weight_invalid: bool
    parallel_execution: bool
    max_workers: int

@dataclass
class AnalysisProfile:
    """Complete analysis profile."""
    name: str
    description: str
    global_config: GlobalConfig
    dimension_configs: Dict[str, DimensionConfig]

class ConfigValidationError(Exception):
    """Raised when configuration is invalid."""
    pass

class ConfigManager:
    """
    Manages configuration profiles for the analyzer.

    Features:
    - Load profiles from YAML
    - Validate configuration
    - Support multiple profiles
    - Environment variable overrides
    - Default configuration fallback
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "analyzer_profiles.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Path to config file (uses default if None)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config_data: Optional[Dict] = None
        self._profiles: Dict[str, AnalysisProfile] = {}
        self._active_profile_name: Optional[str] = None

    def load(self) -> 'ConfigManager':
        """
        Load configuration from file.

        Returns:
            Self for chaining

        Raises:
            FileNotFoundError: If config file doesn't exist
            ConfigValidationError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config_data = yaml.safe_load(f)

        # Validate schema version
        schema_version = self._config_data.get('schema_version')
        if schema_version != "1.0":
            raise ConfigValidationError(f"Unsupported schema version: {schema_version}")

        # Load profiles
        profiles_data = self._config_data.get('profiles', {})
        for profile_name, profile_data in profiles_data.items():
            self._profiles[profile_name] = self._parse_profile(profile_name, profile_data)

        # Set active profile from config or env var
        active = os.environ.get('ANALYZER_PROFILE') or self._config_data.get('active_profile')
        if active not in self._profiles:
            raise ConfigValidationError(f"Active profile '{active}' not found in config")

        self._active_profile_name = active

        return self

    def _parse_profile(self, name: str, data: Dict) -> AnalysisProfile:
        """Parse profile data into AnalysisProfile object."""
        global_data = data.get('global', {})
        global_config = GlobalConfig(
            detection_target=global_data.get('detection_target', 30.0),
            quality_target=global_data.get('quality_target', 85.0),
            fail_on_weight_invalid=global_data.get('fail_on_weight_invalid', True),
            parallel_execution=global_data.get('parallel_execution', True),
            max_workers=global_data.get('max_workers', 10)
        )

        dimensions_data = data.get('dimensions', {})
        dimension_configs = {}

        for dim_name, dim_data in dimensions_data.items():
            dimension_configs[dim_name] = DimensionConfig(
                enabled=dim_data.get('enabled', True),
                weight=dim_data.get('weight', 1.0),
                settings=dim_data.get('settings', {})
            )

        return AnalysisProfile(
            name=data.get('name', name),
            description=data.get('description', ''),
            global_config=global_config,
            dimension_configs=dimension_configs
        )

    def get_active_profile(self) -> AnalysisProfile:
        """
        Get the currently active profile.

        Returns:
            Active AnalysisProfile

        Raises:
            ConfigValidationError: If no profile is active
        """
        if not self._active_profile_name:
            raise ConfigValidationError("No active profile set")

        return self._profiles[self._active_profile_name]

    def get_profile(self, profile_name: str) -> AnalysisProfile:
        """
        Get a specific profile by name.

        Args:
            profile_name: Name of profile to retrieve

        Returns:
            AnalysisProfile

        Raises:
            ConfigValidationError: If profile doesn't exist
        """
        if profile_name not in self._profiles:
            raise ConfigValidationError(f"Profile '{profile_name}' not found")

        return self._profiles[profile_name]

    def set_active_profile(self, profile_name: str):
        """
        Switch to a different profile.

        Args:
            profile_name: Name of profile to activate

        Raises:
            ConfigValidationError: If profile doesn't exist
        """
        if profile_name not in self._profiles:
            raise ConfigValidationError(f"Profile '{profile_name}' not found")

        self._active_profile_name = profile_name

    def list_profiles(self) -> List[str]:
        """
        Get list of available profile names.

        Returns:
            List of profile names
        """
        return list(self._profiles.keys())

    def get_dimension_config(self, dimension_name: str,
                            profile: Optional[str] = None) -> DimensionConfig:
        """
        Get configuration for a specific dimension.

        Args:
            dimension_name: Name of dimension
            profile: Profile name (uses active if None)

        Returns:
            DimensionConfig for the dimension

        Raises:
            ConfigValidationError: If dimension not in profile
        """
        profile_obj = self.get_profile(profile) if profile else self.get_active_profile()

        if dimension_name not in profile_obj.dimension_configs:
            raise ConfigValidationError(
                f"Dimension '{dimension_name}' not found in profile '{profile_obj.name}'"
            )

        return profile_obj.dimension_configs[dimension_name]

    def get_global_config(self, profile: Optional[str] = None) -> GlobalConfig:
        """
        Get global configuration.

        Args:
            profile: Profile name (uses active if None)

        Returns:
            GlobalConfig
        """
        profile_obj = self.get_profile(profile) if profile else self.get_active_profile()
        return profile_obj.global_config

    def validate_profile_weights(self, profile_name: Optional[str] = None) -> bool:
        """
        Validate that dimension weights in a profile sum to 100.

        Args:
            profile_name: Profile to validate (uses active if None)

        Returns:
            True if valid, False otherwise
        """
        profile = self.get_profile(profile_name) if profile_name else self.get_active_profile()

        total_weight = sum(
            dim_config.weight
            for dim_config in profile.dimension_configs.values()
            if dim_config.enabled
        )

        # Tolerance of ±0.1%
        return abs(total_weight - 100.0) <= 0.1

    @classmethod
    def create_default(cls) -> 'ConfigManager':
        """
        Create config manager with default configuration.

        Returns:
            Initialized ConfigManager with default config
        """
        manager = cls()

        if not manager.config_path.exists():
            # Create default config file
            manager._create_default_config_file()

        manager.load()
        return manager

    def _create_default_config_file(self):
        """Create default configuration file."""
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy from template (would be included in package)
        template_path = Path(__file__).parent.parent / "config" / "analyzer_profiles.template.yaml"

        if template_path.exists():
            import shutil
            shutil.copy(template_path, self.config_path)
        else:
            # Generate minimal default
            default_config = self._generate_minimal_default()
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)

    def _generate_minimal_default(self) -> Dict:
        """Generate minimal default configuration."""
        return {
            'version': '1.0',
            'schema_version': '1.0',
            'active_profile': 'balanced',
            'profiles': {
                'balanced': {
                    'name': 'Balanced Analysis',
                    'description': 'Default balanced profile',
                    'global': {
                        'detection_target': 30.0,
                        'quality_target': 85.0,
                        'fail_on_weight_invalid': True,
                        'parallel_execution': True,
                        'max_workers': 10
                    },
                    'dimensions': {}  # Would be populated by dimensions
                }
            }
        }
```

#### Tasks

- [ ] Create `core/config_manager.py`
- [ ] Implement profile loading from YAML
- [ ] Add config validation
- [ ] Implement profile switching
- [ ] Add environment variable overrides
- [ ] Create default config generation
- [ ] Write comprehensive unit tests
- [ ] Add schema validation

---

### 📦 STORY 11: Dimension Config Schema Declaration

**Priority:** P0 (Foundation)
**Story Points:** 3
**Dependencies:** Story 1, Story 10

#### Description

**As a** dimension developer
**I want** dimensions to declare their config schema
**So that** the config system knows what settings are needed

#### Acceptance Criteria

1. Extend `DimensionStrategy` with config schema methods
2. Dimensions declare config keys and types
3. Dimensions declare default values
4. Config schema validation
5. Type checking for config values

#### Implementation

```python
# Update dimensions/base_strategy.py

from typing import Dict, Any, Type
from dataclasses import dataclass

@dataclass
class ConfigParam:
    """Configuration parameter definition."""
    name: str
    param_type: Type
    default: Any
    description: str
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None

class DimensionStrategy(ABC):
    """Enhanced base with config schema."""

    def __init__(self, config_manager: Optional['ConfigManager'] = None):
        """
        Initialize dimension with optional config manager.

        Args:
            config_manager: ConfigManager instance (uses default if None)
        """
        from writescore.core.config_manager import ConfigManager

        self._config_manager = config_manager or ConfigManager.create_default()
        self._config: Optional[DimensionConfig] = None

        # Load configuration for this dimension
        self._load_config()

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> List[ConfigParam]:
        """
        Declare configuration schema for this dimension.

        Returns:
            List of ConfigParam defining all config keys

        Example:
            return [
                ConfigParam(
                    name='ai_vocab_threshold_excellent',
                    param_type=float,
                    default=1.0,
                    description='AI vocab per 1k for excellent score',
                    min_value=0.0,
                    max_value=10.0
                ),
                ConfigParam(
                    name='formulaic_transitions_penalty',
                    param_type=int,
                    default=5,
                    description='Point penalty per formulaic transition',
                    min_value=0,
                    max_value=20
                )
            ]
        """
        pass

    def _load_config(self):
        """Load configuration from config manager."""
        try:
            self._config = self._config_manager.get_dimension_config(self.dimension_name)
        except Exception:
            # Dimension not in config, use defaults
            self._config = self._create_default_config()

    def _create_default_config(self) -> DimensionConfig:
        """Create default config from schema."""
        schema = self.get_config_schema()
        default_settings = {param.name: param.default for param in schema}

        return DimensionConfig(
            enabled=True,
            weight=self.weight,
            settings=default_settings
        )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Config key name
            default: Default value if key not found

        Returns:
            Config value
        """
        if not self._config:
            return default

        return self._config.settings.get(key, default)

    @property
    def weight(self) -> float:
        """
        Get dimension weight from config.

        Returns:
            Weight value from config, or default
        """
        if self._config:
            return self._config.weight

        return self._get_default_weight()

    @abstractmethod
    def _get_default_weight(self) -> float:
        """Return default weight if not in config."""
        pass
```

#### Example Dimension with Config

```python
# dimensions/perplexity.py

class PerplexityDimension(DimensionStrategy):

    @classmethod
    def get_config_schema(cls) -> List[ConfigParam]:
        """Declare configuration schema."""
        return [
            ConfigParam(
                name='ai_vocab_threshold_excellent',
                param_type=float,
                default=1.0,
                description='AI vocabulary per 1k words for excellent score',
                min_value=0.0,
                max_value=20.0
            ),
            ConfigParam(
                name='ai_vocab_threshold_good',
                param_type=float,
                default=3.0,
                description='AI vocabulary per 1k words for good score',
                min_value=0.0,
                max_value=20.0
            ),
            ConfigParam(
                name='ai_vocab_threshold_acceptable',
                param_type=float,
                default=5.0,
                description='AI vocabulary per 1k words for acceptable score',
                min_value=0.0,
                max_value=20.0
            ),
            ConfigParam(
                name='formulaic_transitions_penalty',
                param_type=int,
                default=5,
                description='Point penalty per formulaic transition',
                min_value=0,
                max_value=20
            ),
            ConfigParam(
                name='custom_vocab_patterns',
                param_type=list,
                default=[],
                description='Custom AI vocabulary patterns (regex)'
            )
        ]

    def _get_default_weight(self) -> float:
        return 5.0

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate score using config thresholds."""
        ai_vocab_per_1k = metrics.get('ai_vocabulary', {}).get('per_1k', 0)

        # Get thresholds from config
        excellent = self.get_config_value('ai_vocab_threshold_excellent', 1.0)
        good = self.get_config_value('ai_vocab_threshold_good', 3.0)
        acceptable = self.get_config_value('ai_vocab_threshold_acceptable', 5.0)

        if ai_vocab_per_1k < excellent:
            score = 100.0
        elif ai_vocab_per_1k < good:
            score = 75.0
        elif ai_vocab_per_1k < acceptable:
            score = 50.0
        else:
            score = 25.0

        # Apply transition penalty from config
        transition_count = metrics.get('formulaic_transitions', {}).get('count', 0)
        penalty_per = self.get_config_value('formulaic_transitions_penalty', 5)
        score -= min(transition_count * penalty_per, 50)

        return max(0.0, min(100.0, score))
```

---

### 📦 STORY 12: CLI Profile Selection

**Priority:** P1 (User-Facing)
**Story Points:** 3
**Dependencies:** Stories 10, 11

#### Description

**As a** user
**I want** to select analysis profiles via CLI
**So that** I can easily switch between strict/balanced/permissive modes

#### Implementation

```python
# cli/args.py - Add profile argument

parser.add_argument(
    '--profile',
    type=str,
    default=None,
    choices=['strict', 'balanced', 'permissive', 'technical'],
    help='Analysis profile to use (overrides config file)'
)

parser.add_argument(
    '--list-profiles',
    action='store_true',
    help='List available analysis profiles and exit'
)

parser.add_argument(
    '--config',
    type=str,
    default=None,
    help='Path to custom config file'
)
```

#### Usage Examples

```bash
# Use balanced profile (default)
python analyze_ai_patterns.py document.md

# Use strict profile
python analyze_ai_patterns.py document.md --profile strict

# Use permissive profile
python analyze_ai_patterns.py document.md --profile permissive

# Use custom config file
python analyze_ai_patterns.py document.md --config my_config.yaml

# List available profiles
python analyze_ai_patterns.py --list-profiles

# Output:
# Available profiles:
#   - strict: Maximum AI detection sensitivity
#   - balanced: Recommended default (ACTIVE)
#   - permissive: Lower sensitivity for technical writing
#   - technical: Optimized for technical documentation
```

---

### 📦 STORY 13: Config Validation & Auto-generation

**Priority:** P2 (Quality)
**Story Points:** 5
**Dependencies:** Stories 10, 11

#### Description

**As a** user
**I want** config validation and auto-generation
**So that** I can ensure my config is valid and get help creating custom profiles

#### Features

1. Validate config against dimension schemas
2. Check weight totals per profile
3. Detect missing required config keys
4. Generate config template from registered dimensions
5. Merge custom config with defaults

#### Implementation

```python
# core/config_validator.py

class ConfigValidator:
    """Validate configuration against dimension schemas."""

    def __init__(self, registry: DimensionRegistry):
        self.registry = registry

    def validate_profile(self, profile: AnalysisProfile) -> List[str]:
        """
        Validate a profile against dimension schemas.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check weight total
        total_weight = sum(
            dim.weight for dim in profile.dimension_configs.values()
            if dim.enabled
        )

        if abs(total_weight - 100.0) > 0.1:
            errors.append(
                f"Total weight {total_weight:.2f}% != 100.0% "
                f"(difference: {total_weight - 100.0:+.2f}%)"
            )

        # Validate each dimension config
        for dim in self.registry.get_all():
            dim_name = dim.dimension_name

            if dim_name not in profile.dimension_configs:
                errors.append(f"Missing config for dimension '{dim_name}'")
                continue

            dim_config = profile.dimension_configs[dim_name]
            schema = dim.get_config_schema()

            # Check all schema params present
            for param in schema:
                if param.name not in dim_config.settings:
                    errors.append(
                        f"{dim_name}.{param.name}: Missing required config key"
                    )
                    continue

                value = dim_config.settings[param.name]

                # Type check
                if not isinstance(value, param.param_type):
                    errors.append(
                        f"{dim_name}.{param.name}: Expected {param.param_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

                # Range check
                if param.min_value is not None and value < param.min_value:
                    errors.append(
                        f"{dim_name}.{param.name}: Value {value} < minimum {param.min_value}"
                    )

                if param.max_value is not None and value > param.max_value:
                    errors.append(
                        f"{dim_name}.{param.name}: Value {value} > maximum {param.max_value}"
                    )

        return errors

# core/config_generator.py

class ConfigGenerator:
    """Generate configuration templates."""

    def __init__(self, registry: DimensionRegistry):
        self.registry = registry

    def generate_profile_template(self, profile_name: str = "custom") -> Dict:
        """
        Generate config template from registered dimensions.

        Returns:
            Dict representing YAML config structure
        """
        dimensions_config = {}

        for dim in self.registry.get_all():
            schema = dim.get_config_schema()
            settings = {param.name: param.default for param in schema}

            dimensions_config[dim.dimension_name] = {
                'enabled': True,
                'weight': dim._get_default_weight(),
                'settings': settings
            }

        return {
            profile_name: {
                'name': f'{profile_name.title()} Profile',
                'description': 'Custom analysis profile',
                'global': {
                    'detection_target': 30.0,
                    'quality_target': 85.0,
                    'fail_on_weight_invalid': True,
                    'parallel_execution': True,
                    'max_workers': 10
                },
                'dimensions': dimensions_config
            }
        }
```

#### CLI Commands

```bash
# Validate current config
python analyze_ai_patterns.py --validate-config

# Generate config template
python analyze_ai_patterns.py --generate-config > my_config.yaml

# Validate custom config
python analyze_ai_patterns.py --validate-config --config my_config.yaml
```

---

## Updated Epic Summary

### Total Story Points: 94 (was 73 + 21 new)

| Story | Points | Focus |
|-------|--------|-------|
| 1. Enhanced Dimension Base Contract | 3 | Foundation |
| 2. Dimension Registry | 5 | Infrastructure |
| 3. Weight Validation Mediator | 5 | Safety |
| 4. Refactor All 10 Dimensions | 21 | Enablement |
| 5. Dynamic Analysis Engine | 8 | Core Functionality |
| 6. Dynamic Reporting System | 8 | User-Facing |
| 7. Refactor Dual Score Calculator | 13 | Cleanup |
| 8. Auto-loading Dimensions | 5 | Convenience |
| 9. Development Guide | 5 | Documentation |
| **10. Config Schema & Infrastructure** ⭐ | **5** | **Config Foundation** |
| **11. Dimension Config Declaration** ⭐ | **3** | **Config Integration** |
| **12. CLI Profile Selection** ⭐ | **3** | **User Experience** |
| **13. Config Validation & Generation** ⭐ | **5** | **Quality & DevEx** |

**New Timeline:** 5-7 sprints (10-14 weeks)

---

## Configuration Benefits

✅ **Multiple preconfigured profiles** (strict, balanced, permissive, technical)
✅ **Runtime profile switching** via CLI or environment variable
✅ **Dimension settings centralized** in one config file
✅ **Type-safe configuration** with validation
✅ **Auto-generation** of config templates
✅ **Easy customization** without code changes
✅ **Environment-specific configs** (dev, staging, prod)

---

## Updated Success Metrics

### Configuration-Specific Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Profile switch time | <100ms | Performance test |
| Config validation coverage | 100% | Unit tests |
| Default config validity | 100% | Automated check |
| Config template generation | All dimensions | Integration test |

---

## Approval & Next Steps

This addendum extends the original refactoring plan with comprehensive configuration management. The configuration system enables:

1. Multiple analysis profiles for different use cases
2. Easy customization without code changes
3. Runtime profile switching
4. Dimension config schema declaration
5. Automatic validation and template generation

**Recommended Implementation Order:**

1. Stories 1-3 (Foundation)
2. **Story 10 (Config Infrastructure)** ⭐
3. **Story 11 (Config Schema)** ⭐
4. Story 4 (Refactor Dimensions with config support)
5. Stories 5-9 (Core functionality)
6. **Stories 12-13 (CLI & Validation)** ⭐

---

**Ready to proceed with implementation?**
