# WriteScore

<!-- Project Info -->
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- CI/Build Status -->
[![CI](https://github.com/BOHICA-LABS/writescore/actions/workflows/ci.yml/badge.svg)](https://github.com/BOHICA-LABS/writescore/actions/workflows/ci.yml)
[![CodeQL](https://github.com/BOHICA-LABS/writescore/actions/workflows/codeql.yml/badge.svg)](https://github.com/BOHICA-LABS/writescore/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/BOHICA-LABS/writescore/graph/badge.svg)](https://codecov.io/gh/BOHICA-LABS/writescore)

<!-- Code Quality & Security -->
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Security Policy](https://img.shields.io/badge/security-policy-blue.svg)](SECURITY.md)

<!-- Maintenance -->
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **Identify AI patterns in your writing and get actionable feedback to sound more human.**

![WriteScore CLI demo showing terminal output with analysis scores and recommendations](docs/assets/demo.gif)

## Quick Start

```bash
pip install -e .
python -m spacy download en_core_web_sm
writescore analyze README.md
```

That's it! You'll see a detailed analysis with scores and improvement suggestions.

## Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Python | 3.9 | 3.11+ |
| RAM | 4 GB | 8 GB |
| Disk | 2 GB | 3 GB |

**Note:** First run downloads transformer models (~500MB) and spaCy model (~50MB). Subsequent runs use cached models.

## Getting Started

**Quickest path:** Install [Just](https://just.systems), then run `just dev`. See all options below.

| Option | Local Install | CLI/IDE | Docker Required | Use WriteScore | Contribute |
|--------|:-------------:|:-------:|:---------------:|----------------|------------|
| ✓ **Native (Just)** | Yes | CLI | No | `just install` | `just dev` |
| **Native (Just)** | Yes | IDE | No | `just install`, open in any IDE | `just dev`, open in any IDE |
| Native (Manual) | Yes | CLI | No | [Instructions](#native-manual) | [Instructions](#native-manual) |
| Native (Manual) | Yes | IDE | No | [Instructions](#native-manual), open in any IDE | [Instructions](#native-manual), open in any IDE |
| Devcontainer | No | CLI | Yes | [Instructions](#devcontainer-cli) | [Instructions](#devcontainer-cli) |
| Devcontainer | No | IDE | Yes | VS Code → "Reopen in Container" | Same |
| Codespaces | No | CLI | No | [Instructions](#codespaces-cli) | [Instructions](#codespaces-cli) |
| Codespaces | No | IDE | No | GitHub → Code → Create codespace | Same |

After setup, run `just test` (or `pytest` for manual installs) to verify.

### Installing Just

| OS | Command |
|----|---------|
| **Windows** | `winget install Casey.Just` (or `choco install just` / `scoop install just`) |
| macOS | `brew install just` |
| Ubuntu/Debian | `sudo apt install just` |
| Fedora | `sudo dnf install just` |
| Arch Linux | `sudo pacman -S just` |
| Via Cargo | `cargo install just` |
| Via Conda | `conda install -c conda-forge just` |

> **Windows users:** All `just` commands work in PowerShell and CMD. For manual setup, use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

### Native Manual

For users who prefer not to install Just.

**Use WriteScore:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
python -m spacy download en_core_web_sm
```

**Contribute:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
pre-commit install
pre-commit install --hook-type commit-msg
```

### Devcontainer CLI

```bash
devcontainer up --workspace-folder "$(pwd)" && \
devcontainer exec --workspace-folder "$(pwd)" just install
```

For contributors, replace `just install` with `just dev`.

### Codespaces CLI

```bash
gh codespace create -r BOHICA-LABS/writescore && \
gh codespace ssh
```

Then run `just install` (users) or `just dev` (contributors).

### Available Commands

| Command | Description |
|---------|-------------|
| `just` | List available commands |
| `just install` | Install package + spacy model |
| `just dev` | Full dev setup with pre-commit hooks |
| `just test` | Run unit and integration tests |
| `just test-fast` | Run tests excluding slow markers |
| `just test-all` | Run all tests |
| `just lint` | Check code with ruff |
| `just format` | Format code with ruff |
| `just coverage` | Generate HTML coverage report |
| `just clean` | Remove build artifacts |

## Why WriteScore?

**The Problem**: AI detection tools give binary "AI/human" verdicts without explaining why or how to improve.

**The Solution**: WriteScore analyzes 12+ writing dimensions to identify specific patterns that make text sound AI-generated, then provides actionable recommendations.

**Key Differentiators**:
- **Actionable feedback** — Know exactly what to fix, not just "this seems AI-generated"
- **Multi-dimensional analysis** — Examines vocabulary, sentence variety, formatting patterns, and more
- **Quality-focused** — Treats writing improvement as the goal, not accusation
- **Transparent scoring** — See how each dimension contributes to your score

**When to use WriteScore**:
- Polishing AI-assisted drafts to sound more natural
- Identifying mechanical patterns in your own writing
- Quality checks before publishing

**When NOT to use**:
- Academic integrity enforcement (use dedicated tools)
- Legal proof of authorship
- Detection of latest-generation models with high confidence

## Features

- **Dual Scoring** — Detection risk + quality score in one analysis
- **12 Analysis Dimensions** — From vocabulary patterns to syntactic complexity
- **Multiple Modes** — Fast checks to comprehensive analysis
- **Actionable Insights** — Specific recommendations ranked by impact
- **Batch Processing** — Analyze entire directories
- **Score History** — Track improvements over time

## Usage

```bash
# Basic analysis
writescore analyze document.md

# Detailed findings with recommendations
writescore analyze document.md --detailed

# Show dual scores (detection risk + quality)
writescore analyze document.md --show-scores

# Fast mode for quick checks
writescore analyze document.md --mode fast

# Full analysis for final review
writescore analyze document.md --mode full

# Batch process a directory
writescore analyze --batch docs/
```

## Analysis Modes

| Mode | Speed | Best For |
|------|-------|----------|
| **fast** | Fastest | Quick checks, CI/CD |
| **adaptive** | Balanced | Default, most documents |
| **sampling** | Medium | Large documents |
| **full** | Slowest | Final review, maximum accuracy |

See the [Analysis Modes Guide](docs/analysis-modes-guide.md) for details.

## Troubleshooting

### Slow First Run

**This is normal.** First analysis downloads transformer models (~500MB) and caches them. Subsequent runs are much faster.

### Out of Memory

**Quick fix:** Use `--mode fast` for lower memory usage:

```bash
writescore analyze document.md --mode fast
```

On macOS Apple Silicon, if you see MPS memory errors:

```bash
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
writescore analyze document.md
```

### ModuleNotFoundError / Command Not Found

**Quick fix:** `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)

**Diagnostic table:**

| Where did you install? | Current terminal | Fix |
|------------------------|------------------|-----|
| venv (`.venv/`) | venv not activated | `source .venv/bin/activate` |
| venv (`.venv/`) | Different venv activated | Activate correct venv or reinstall |
| Devcontainer | Native terminal | Run inside container or install natively |
| Codespaces | Local terminal | Install natively |
| Unknown | — | Run diagnostic commands below |

**Diagnostic commands:**

```bash
# Check if writescore is anywhere in PATH
which writescore

# Check if installed in current venv
pip show writescore

# Check common venv locations
ls -la .venv/bin/writescore 2>/dev/null || echo "Not in .venv"
ls -la venv/bin/writescore 2>/dev/null || echo "Not in venv"
```

**Common fixes:**

```bash
# Activate venv (if installed there)
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run inside devcontainer (if installed there)
devcontainer exec --workspace-folder "$(pwd)" writescore analyze README.md

# Or reinstall natively
just install  # or: pip install -e . && python -m spacy download en_core_web_sm
```

### Can't find model 'en_core_web_sm'

```bash
python -m spacy download en_core_web_sm
```

### NLTK Data Missing

If you see `LookupError` mentioning NLTK data:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, components, patterns |
| [Analysis Modes Guide](docs/analysis-modes-guide.md) | Mode comparison and usage |
| [Development History](docs/DEVELOPMENT-HISTORY.md) | Project evolution and roadmap |
| [Migration Guide](MIGRATION-v6.0.0.md) | Upgrading from AI Pattern Analyzer |
| [Changelog](CHANGELOG.md) | Version history |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Note:** This project uses [ggshield](https://github.com/GitGuardian/ggshield) for secret scanning. See [Secret Scanning setup](CONTRIBUTING.md#secret-scanning-ggshield) before your first commit.

## License

MIT License - see [LICENSE](LICENSE) for details.
