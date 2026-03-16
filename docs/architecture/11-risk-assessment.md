# 11. Risk Assessment

| Risk Type | Risk | Mitigation |
|-----------|------|------------|
| **Technical** | Transformer models (GLTR) are slow on large documents | ADAPTIVE/SAMPLING modes limit analysis scope |
| **Technical** | spaCy/NLTK require model downloads on first run | Lazy loading with fallback handling |
| **Technical** | Memory usage with large documents + ML models | Sampling modes reduce memory footprint |
| **Dependency** | transformers/torch versions can conflict | Pinned minimum versions in pyproject.toml |
| **Compatibility** | Python 3.9 approaching EOL (Oct 2025) | Already supports 3.10-3.12 |

---
