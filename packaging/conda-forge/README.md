# Conda-forge Recipe for WriteScore

This directory contains the conda-forge recipe template for WriteScore.

## Submitting to conda-forge

To get WriteScore on conda-forge, follow the [staged-recipes process](https://conda-forge.org/docs/maintainer/adding_pkgs.html):

### 1. Fork staged-recipes

Fork [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes) on GitHub.

### 2. Create a recipe branch

```bash
git clone https://github.com/YOUR-USERNAME/staged-recipes.git
cd staged-recipes
git checkout -b add-writescore
```

### 3. Add the recipe

```bash
mkdir -p recipes/writescore
cp /path/to/writescore/packaging/conda-forge/meta.yaml recipes/writescore/
```

### 4. Lint and test locally (optional)

```bash
# Install conda-build
conda install conda-build conda-verify

# Build locally
conda build recipes/writescore
```

### 5. Submit PR

```bash
git add recipes/writescore/meta.yaml
git commit -m "Add writescore recipe"
git push origin add-writescore
```

Then open a PR to `conda-forge/staged-recipes`.

## Important Notes

### Dependencies

Some dependencies have different names on conda-forge:
- `torch` → `pytorch`
- spaCy models are separate packages: `spacy-model-en_core_web_sm`

### NLTK Data

NLTK data is not bundled in conda packages. Users need to download it:

```python
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
```

However, WriteScore handles this automatically on first run.

### Transformer Models

Transformer models (~500MB) are downloaded on first use from HuggingFace.
This happens automatically and models are cached.

## After Acceptance

Once the PR is merged:

1. A feedstock repository `writescore-feedstock` will be created
2. You'll be added as a maintainer
3. New releases are detected automatically from PyPI
4. Or you can trigger rebuilds manually

## Updating the Recipe

After initial submission, updates happen in the feedstock:

```bash
# Fork and clone writescore-feedstock
git clone https://github.com/YOUR-USERNAME/writescore-feedstock.git
cd writescore-feedstock

# Update version and sha256 in recipe/meta.yaml
# Then submit PR
```

The [conda-forge-bot](https://github.com/regro-cf-autotick-bot) often auto-detects
PyPI releases and creates update PRs automatically.

## Installation (Once Published)

```bash
# Add conda-forge channel if not already
conda config --add channels conda-forge

# Install
conda install writescore

# Or with mamba (faster)
mamba install writescore
```
