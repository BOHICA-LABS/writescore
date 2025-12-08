# Security

This section defines security considerations and requirements for WriteScore, a CLI tool for local text analysis.

---

## 16.1 Security Context

WriteScore operates as a **local CLI tool** with the following security profile:

| Aspect | Status | Notes |
|--------|--------|-------|
| Network Access | None | No external API calls during analysis |
| Authentication | N/A | Local tool, no user accounts |
| Data Storage | Local only | JSON files in user's directory |
| Remote Code Execution | None | No eval(), no dynamic imports |
| User Input | File paths, CLI args | Validated before processing |

---

## 16.2 Input Validation

### File Handling

```python
# REQUIRED: Validate file paths before processing
def validate_file_path(path: str) -> Path:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Not a file: {path}")
    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {resolved.suffix}")
    return resolved

ALLOWED_EXTENSIONS = {'.md', '.txt', '.markdown'}
```

### CLI Arguments

- All CLI arguments validated by Click framework
- File paths resolved and validated before processing
- Numeric arguments bounds-checked (e.g., `--samples` must be positive)

### Text Processing

- Maximum file size: 10MB (configurable)
- Text encoding: UTF-8 with fallback detection
- No execution of embedded code blocks (treated as plain text)

---

## 16.3 Dependency Security

### Scanning Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| **ggshield** | Secret detection | Pre-commit hook |
| **Dependabot** | Vulnerability alerts | GitHub integration |
| **ruff** | Security linting | Pre-commit + CI |

### ML Model Security

WriteScore uses pre-trained models from HuggingFace:

```
Models loaded:
- distilgpt2 (GLTR analysis)
- distilbert-base-uncased-finetuned-sst-2-english (sentiment)
- all-MiniLM-L6-v2 (semantic coherence, optional)
```

**Security measures:**
- Models loaded from official HuggingFace hub only
- Model checksums verified by transformers library
- No custom model fine-tuning or loading from arbitrary sources
- Models cached locally after first download

### Dependency Update Policy

| Category | Update Frequency | Approval |
|----------|-----------------|----------|
| Security patches | Immediate | Auto-merge if tests pass |
| Minor versions | Weekly review | Maintainer approval |
| Major versions | Quarterly | Breaking change review |

---

## 16.4 Data Protection

### No Sensitive Data Storage

WriteScore does **not** store:
- User credentials or tokens
- Personal identifiable information (PII)
- Analysis text content (only metrics)
- Network or system information

### Local File Access

```
Data written by WriteScore:
~/.writescore/
├── history/           # Score history (JSON)
│   └── <file_hash>.json
└── cache/             # Model cache (managed by transformers)
```

**Permissions:** Files created with user's default umask (typically 0644)

### History File Content

History files contain only:
- File path (user-provided)
- Timestamps
- Numeric scores and metrics
- No original text content

---

## 16.5 Code Security

### Prohibited Patterns

The following patterns are **prohibited** in WriteScore code:

```python
# NEVER use:
eval()              # Dynamic code execution
exec()              # Dynamic code execution
__import__()        # Dynamic imports
pickle.load()       # Unsafe deserialization (use json instead)
subprocess.shell=True  # Shell injection risk
```

### Safe Parsing

| Content Type | Parser | Security |
|--------------|--------|----------|
| Markdown | marko | No code execution |
| JSON | stdlib json | Safe by default |
| YAML | Not used | Avoided (complex attack surface) |
| Text | Plain read | No parsing risks |

### Error Messages

- Never include file contents in error messages
- Never include full stack traces in user-facing output
- Log detailed errors only in debug mode

---

## 16.6 Secret Scanning

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/gitguardian/ggshield
  hooks:
    - id: ggshield
      stages: [pre-commit]
```

### Ignored Patterns

See `.gitguardian.yaml` for:
- Test fixtures with fake credentials
- Documentation examples
- Known false positives

### CI Integration

- ggshield runs on all PRs
- Blocks merge if secrets detected
- Dashboard at GitGuardian for incident management

---

## 16.7 Security Testing

### Automated Checks

| Check | Tool | Frequency |
|-------|------|-----------|
| Secrets | ggshield | Every commit |
| Dependencies | Dependabot | Daily |
| Code patterns | ruff (bandit rules) | Every commit |
| Type safety | mypy | Every commit |

### Manual Review

For significant changes:
- Review file I/O operations
- Review any new dependencies
- Check for information disclosure in error handling

---

## 16.8 Future Considerations (MCP Server)

When WriteScore evolves to include MCP server functionality:

| Concern | Mitigation |
|---------|------------|
| Network exposure | Localhost-only binding by default |
| Authentication | API key or local socket auth |
| Rate limiting | Request throttling per client |
| Input validation | Schema validation for all requests |
| Timeout handling | Per-request timeout enforcement |

These will be detailed in a separate MCP Security addendum when that feature is implemented.
