# 7. Next Steps

## 7.1 Architect Prompt

> Review the WriteScore PRD and `docs/technical-reference.md`. Design the architecture for Epic 3 (Content-Aware Analysis), focusing on: (1) ContentTypeDetector module design with feature extractors, (2) Weight/threshold adjustment mechanism integrated with existing DimensionRegistry, (3) CLI integration with AnalysisConfig. Produce architecture document with component diagrams and interface specifications.

## 7.2 Developer Prompt

> Implement Story 3.1 (Content Type Detection) following the architecture document. Create `core/content_type_detector.py` with multi-feature voting ensemble. Add CLI `--content-type` flag. Ensure 85%+ test coverage.
