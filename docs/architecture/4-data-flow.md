# 4. Data Flow

## 4.1 Analysis Pipeline

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Input File │────▶│  Text Extraction │────▶│  Preprocessing   │
│   (.md)     │     │  (marko parser)  │     │  (HTML comments) │
└─────────────┘     └─────────────────┘     └──────────────────┘
                                                      │
                                                      ▼
                    ┌─────────────────────────────────────────────────┐
                    │              DimensionLoader                     │
                    │  Load dimensions based on profile               │
                    │  (fast: 4, balanced: 8, full: 16)               │
                    └─────────────────────────────────────────────────┘
                                                      │
                                                      ▼
     ┌──────────────────────────────────────────────────────────────────┐
     │                     Dimension Analysis Loop                       │
     │  For each loaded dimension:                                       │
     │  1. Prepare text based on mode (FAST/ADAPTIVE/SAMPLING/FULL)     │
     │  2. Call dimension.analyze(prepared_text, config)                │
     │  3. Store metrics in dimension_results dict                       │
     └──────────────────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
     ┌──────────────────────────────────────────────────────────────────┐
     │                      Score Calculation                            │
     │  For each dimension:                                              │
     │  1. Call dimension.calculate_score(metrics)                       │
     │  2. Apply z-score normalization (if enabled)                      │
     │  3. Weight by dimension.weight                                    │
     │  4. Aggregate into tier categories                                │
     │  5. Sum for Quality Score, invert for Detection Risk              │
     └──────────────────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
     ┌──────────────────────────────────────────────────────────────────┐
     │                    Report Generation                              │
     │  • Format results based on --format option                        │
     │  • Generate recommendations if --show-scores                      │
     │  • Save to history if enabled                                     │
     │  • Output to stdout or --output file                              │
     └──────────────────────────────────────────────────────────────────┘
```

## 4.2 Scoring Flow Detail

```
┌────────────────────────────────────────────────────────────────────────┐
│                    DualScoreCalculator Flow                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. DISCOVER: DimensionRegistry.get_all()                              │
│       │                                                                 │
│       ▼                                                                 │
│  2. VALIDATE: WeightMediator.is_valid()                                │
│       │         (ensure weights sum to 100.0)                          │
│       ▼                                                                 │
│  3. SCORE: For each dimension                                          │
│       │     • Extract metrics from results.dimension_results           │
│       │     • Call dimension.calculate_score(metrics)                  │
│       │     • Apply z-score normalization                              │
│       │     • Weight: normalized_score = (score/100) * weight          │
│       ▼                                                                 │
│  4. CATEGORIZE: Group by tier                                          │
│       │     • ADVANCED: 30-40% of total                                │
│       │     • CORE: 35-45% of total                                    │
│       │     • SUPPORTING: 15-25% of total                              │
│       │     • STRUCTURAL: 5-10% of total                               │
│       ▼                                                                 │
│  5. AGGREGATE:                                                         │
│       │     • quality_score = sum(all tier totals)                     │
│       │     • detection_risk = 100 - quality_score                     │
│       ▼                                                                 │
│  6. RECOMMEND: Generate improvement actions                            │
│       │     • Sort by impact (HIGH > MEDIUM > LOW)                     │
│       │     • Build ROI-optimized path to target                       │
│       ▼                                                                 │
│  7. RETURN: DualScore dataclass                                        │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---
