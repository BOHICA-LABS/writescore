# Homebrew Tap for WriteScore

This directory contains the Homebrew formula template for WriteScore.

## Setting Up the Tap

To distribute WriteScore via Homebrew, create a tap repository:

### 1. Create the tap repository

Create a new repository named `homebrew-writescore` in the BOHICA-LABS organization:

```bash
gh repo create BOHICA-LABS/homebrew-writescore --public --description "Homebrew tap for WriteScore"
```

### 2. Clone and set up the tap

```bash
cd /tmp
git clone https://github.com/BOHICA-LABS/homebrew-writescore.git
cd homebrew-writescore
mkdir Formula
```

### 3. Get the SHA256 for the PyPI release

```bash
# Get the SHA256 from PyPI
curl -sL https://pypi.org/pypi/writescore/6.4.0/json | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256'
```

### 4. Update and copy the formula

Replace `PLACEHOLDER_SHA256` in `writescore.rb` with the actual SHA256, then:

```bash
cp /path/to/writescore/packaging/homebrew/writescore.rb Formula/
```

### 5. Commit and push

```bash
git add Formula/writescore.rb
git commit -m "Add writescore formula v6.4.0"
git push origin main
```

## Users can then install with:

```bash
brew tap bohica-labs/writescore
brew install writescore
```

Or in one command:

```bash
brew install bohica-labs/writescore/writescore
```

## Updating the Formula

When releasing a new version:

1. Update the `url` with the new version
2. Update the `sha256` with the new hash from PyPI
3. Commit and push to the tap repository

Consider automating this with a GitHub Action in the tap repository that triggers on new WriteScore releases.

## Automating Updates

Create `.github/workflows/update-formula.yml` in the tap repository:

```yaml
name: Update Formula

on:
  repository_dispatch:
    types: [new-release]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to update to (e.g., 6.4.0)'
        required: true

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get release info
        id: release
        run: |
          VERSION="${{ github.event.inputs.version || github.event.client_payload.version }}"
          SHA256=$(curl -sL "https://pypi.org/pypi/writescore/${VERSION}/json" | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256')
          echo "version=${VERSION}" >> $GITHUB_OUTPUT
          echo "sha256=${SHA256}" >> $GITHUB_OUTPUT

      - name: Update formula
        run: |
          sed -i "s|writescore-[0-9.]*\.tar\.gz|writescore-${{ steps.release.outputs.version }}.tar.gz|" Formula/writescore.rb
          sed -i "s|sha256 \".*\"|sha256 \"${{ steps.release.outputs.sha256 }}\"|" Formula/writescore.rb

      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "Update writescore to ${{ steps.release.outputs.version }}"
          body: "Automated formula update for writescore ${{ steps.release.outputs.version }}"
          branch: update-${{ steps.release.outputs.version }}
```

Then trigger from the main writescore repo after PyPI release:

```bash
gh api repos/BOHICA-LABS/homebrew-writescore/dispatches \
  -f event_type=new-release \
  -f client_payload='{"version":"6.4.0"}'
```
