# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for WriteScore
# Build with: pyinstaller packaging/pyinstaller/writescore.spec

import os
import sys
from pathlib import Path

# Find the package location
import writescore
package_path = Path(writescore.__file__).parent

# Find spacy model location
import spacy
spacy_path = Path(spacy.__file__).parent

# Find the en_core_web_sm model
try:
    import en_core_web_sm
    spacy_model_path = Path(en_core_web_sm.__file__).parent
except ImportError:
    # Try to find it in spacy's data directory
    spacy_model_path = None
    for data_path in spacy.util.get_data_path().iterdir():
        if data_path.name.startswith('en_core_web_sm'):
            spacy_model_path = data_path
            break

# Find NLTK data
import nltk
nltk_data_path = None
for path in nltk.data.path:
    p = Path(path)
    if p.exists() and (p / 'tokenizers').exists():
        nltk_data_path = p
        break

block_cipher = None

# Hidden imports for dynamic dependencies
hidden_imports = [
    'writescore',
    'writescore.cli',
    'writescore.cli.main',
    'writescore.core',
    'writescore.dimensions',
    'writescore.scoring',
    'writescore.utils',
    # ML dependencies
    'torch',
    'transformers',
    'spacy',
    'spacy.lang.en',
    'nltk',
    'scipy',
    'scipy.special',
    'numpy',
    'sklearn',
    'sklearn.utils._cython_blas',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._quad_tree',
    'sklearn.tree._utils',
    # Click and CLI
    'click',
    'rich',
    # Text processing
    'marko',
    'textstat',
    'textacy',
    # SpaCy model
    'en_core_web_sm',
    # Thinc (spacy backend)
    'thinc',
    'thinc.backends',
    # Transformers internals
    'transformers.models',
    'transformers.models.distilbert',
]

# Data files to include
datas = []

# Add pyproject.toml for version info in frozen builds
repo_root = package_path.parent.parent  # src/writescore -> src -> repo root
pyproject_path = repo_root / "pyproject.toml"
if pyproject_path.exists():
    datas.append((str(pyproject_path), "."))

# Add spacy package data
datas.append((str(spacy_path), "spacy"))

# Add spacy model if found
if spacy_model_path and spacy_model_path.exists():
    datas.append((str(spacy_model_path), f"en_core_web_sm"))

# Add NLTK data if available
if nltk_data_path and nltk_data_path.exists():
    datas.append((str(nltk_data_path), "nltk_data"))

# Add package data
if (package_path / "data").exists():
    datas.append((str(package_path / "data"), "writescore/data"))

a = Analysis(
    ['../../src/writescore/cli/main.py'],
    pathex=['../../src'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='writescore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
