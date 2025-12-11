# WriteScore

<p align="center">
  <img src="https://raw.githubusercontent.com/BOHICA-LABS/writescore/main/docs/assets/logo.svg" alt="WriteScore Logo" width="200">
</p>

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

![WriteScore CLI demo showing terminal output with analysis scores and recommendations](https://raw.githubusercontent.com/BOHICA-LABS/writescore/main/docs/assets/demo.gif)

## Quick Start

```bash
uv sync
uv run python -m spacy download en_core_web_sm
uv run writescore analyze README.md
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

**Quickest path:** Install [Just](https://just.systems), then run `just setup`. See all options below.

| Option | Local Install | CLI/IDE | Docker Required | Use WriteScore | Contribute |
|--------|:-------------:|:-------:|:---------------:|----------------|------------|
| ✓ **Docker** | No | CLI | Yes | [Instructions](#docker) | N/A |
| ✓ **pipx** | No | CLI | No | [Instructions](#pipx) | N/A |
| ✓ **Homebrew** | No | CLI | No | [Instructions](#homebrew) | N/A |
| ✓ **Standalone** | No | CLI | No | [Instructions](#standalone-executable) | N/A |
| **Native (Just)** | Yes | CLI | No | `just install` | `just setup` |
| Native (Just) | Yes | IDE | No | `just install`, open in any IDE | `just setup`, open in any IDE |
| Native (Manual) | Yes | CLI | No | [Instructions](#native-manual) | [Instructions](#native-manual) |
| Native (Manual) | Yes | IDE | No | [Instructions](#native-manual), open in any IDE | [Instructions](#native-manual), open in any IDE |
| Devcontainer | No | CLI | Yes | [Instructions](#devcontainer-cli) | [Instructions](#devcontainer-cli) |
| Devcontainer | No | IDE | Yes | VS Code → "Reopen in Container" | Same |
| Codespaces | No | CLI | No | [Instructions](#codespaces-cli) | [Instructions](#codespaces-cli) |
| Codespaces | No | IDE | No | GitHub → Code → Create codespace | Same |

After setup, run `just test` (or `uv run pytest` for manual installs) to verify.

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

> **Windows users:** All `just` commands work in PowerShell and CMD. With uv, use `uv run` prefix instead of activating the venv.

### Docker

Run WriteScore without any local installation using Docker. Models are pre-downloaded in the image.

```bash
# Analyze a file in current directory
docker run --rm -v "$(pwd):/work" -w /work ghcr.io/bohica-labs/writescore:latest analyze document.md

# With GPU support (NVIDIA)
docker run --rm --gpus all -v "$(pwd):/work" -w /work ghcr.io/bohica-labs/writescore:latest analyze document.md
```

**Optional: Install wrapper script** for native-like usage:

```bash
# Download and install
sudo curl -fsSL https://raw.githubusercontent.com/BOHICA-LABS/writescore/main/scripts/writescore-docker \
  -o /usr/local/bin/writescore
sudo chmod +x /usr/local/bin/writescore

# Now use like a native command
writescore analyze document.md
```

The wrapper auto-detects GPU (NVIDIA/AMD) and mounts files appropriately.

### pipx

Install WriteScore in an isolated environment using [pipx](https://pipx.pypa.io/). No virtual environment management required.

```bash
# Install pipx if you don't have it
# macOS: brew install pipx && pipx ensurepath
# Linux: python3 -m pip install --user pipx && pipx ensurepath

# Install WriteScore
pipx install writescore

# Use immediately (spaCy model auto-downloads on first run)
writescore analyze document.md
```

**Note:** First run downloads spaCy model (~50MB) and transformer models (~500MB). Subsequent runs are faster.

### Homebrew

Install WriteScore on macOS or Linux using [Homebrew](https://brew.sh/):

```bash
# Add the tap and install
brew tap bohica-labs/writescore
brew install writescore

# Or install directly
brew install bohica-labs/writescore/writescore

# Use immediately
writescore analyze document.md
```

The formula installs all dependencies including the spaCy language model.

### Standalone Executable

Download a pre-built executable from [GitHub Releases](https://github.com/BOHICA-LABS/writescore/releases) - no Python installation required.

| Platform | Filename |
|----------|----------|
| Linux (x64) | `writescore-linux-amd64` |
| macOS (Intel) | `writescore-darwin-amd64` |
| macOS (Apple Silicon) | `writescore-darwin-arm64` |
| Windows (x64) | `writescore-windows-amd64.exe` |

```bash
# Linux/macOS example
curl -LO https://github.com/BOHICA-LABS/writescore/releases/latest/download/writescore-linux-amd64
chmod +x writescore-linux-amd64
./writescore-linux-amd64 analyze document.md

# Move to PATH for easier access
sudo mv writescore-linux-amd64 /usr/local/bin/writescore
writescore analyze document.md
```

**Note:** Standalone executables are self-contained (~500MB) and include all models.

### Native Manual

For users who prefer not to install Just. Requires [uv](https://docs.astral.sh/uv/).

**Use WriteScore:**

```bash
uv sync
uv run python -m spacy download en_core_web_sm
```

**Contribute:**

```bash
uv sync --extra dev
uv run python -m spacy download en_core_web_sm
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
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

Then run `just install` (users) or `just setup` (contributors).

### Available Commands

| Command | Description |
|---------|-------------|
| `just` | List available commands |
| `just install` | Install package with all dependencies |
| `just setup` | Full dev setup (install + pre-commit hooks) |
| `just test` | Run fast tests (excludes slow markers) |
| `just test-all` | Run all tests including slow ones |
| `just test-cov` | Run tests with coverage report |
| `just lint` | Check code with ruff |
| `just lint-fix` | Auto-fix linting and format code |
| `just typecheck` | Run mypy type checking |
| `just check` | Run all checks (lint + typecheck) |
| `just clean` | Remove build artifacts and caches |

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

**Quick fix:** Use `uv run` prefix or activate the venv: `source .venv/bin/activate`

**Diagnostic table:**

| Where did you install? | Current terminal | Fix |
|------------------------|------------------|-----|
| uv (`.venv/`) | Not using `uv run` | Prefix with `uv run` or activate venv |
| Devcontainer | Native terminal | Run inside container or install natively |
| Codespaces | Local terminal | Install natively |
| Unknown | — | Run diagnostic commands below |

**Diagnostic commands:**

```bash
# Check if writescore is anywhere in PATH
which writescore

# Check if installed in current venv
uv pip show writescore

# Check common venv locations
ls -la .venv/bin/writescore 2>/dev/null || echo "Not in .venv"
```

**Common fixes:**

```bash
# Use uv run prefix
uv run writescore analyze README.md

# Or activate venv directly
source .venv/bin/activate  # Windows: .venv\Scripts\activate
writescore analyze README.md

# Run inside devcontainer (if installed there)
devcontainer exec --workspace-folder "$(pwd)" writescore analyze README.md

# Or reinstall natively
just install  # or: uv sync && uv run python -m spacy download en_core_web_sm
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

**Quick links:**
- [Label taxonomy](CONTRIBUTING.md#issue-and-pr-labels) — How we categorize issues and PRs
- [Secret scanning setup](CONTRIBUTING.md#secret-scanning-ggshield) — Required before your first commit
- [Code of Conduct](CODE_OF_CONDUCT.md) — Community guidelines

### Updating the Demo GIF

The README demo GIF is generated using [VHS](https://github.com/charmbracelet/vhs). To regenerate after feature changes:

```bash
# Install VHS (macOS)
brew install vhs

# Generate new demo
vhs docs/assets/demo.tape
```

The tape file is at `docs/assets/demo.tape`. Edit it to change the demo script.

## License

MIT License - see [LICENSE](LICENSE) for details.
