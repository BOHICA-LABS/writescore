# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for WriteScore
# Build with: pyinstaller packaging/pyinstaller/writescore.spec

import os
import sys
from pathlib import Path

# Find the package location
import writescore
package_path = Path(writescore.__file__).parent

# Find spacy and nltk data locations
import spacy
import nltk

spacy_path = Path(spacy.__file__).parent
nltk_data = Path(nltk.data.path[0]) if nltk.data.path else None

# Find transformers cache
transformers_cache = Path.home() / ".cache" / "huggingface"

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
    'nltk',
    'scipy',
    'numpy',
    'sklearn',
    # Click and CLI
    'click',
    'rich',
    # Text processing
    'marko',
    'textstat',
    'textacy',
]

# Data files to include
datas = [
    # SpaCy model (en_core_web_sm)
    (str(spacy_path / "data"), "spacy/data"),
]

# Add NLTK data if available
if nltk_data and nltk_data.exists():
    datas.append((str(nltk_data), "nltk_data"))

# Add package data
datas.append((str(package_path / "data"), "writescore/data"))

a = Analysis(
    ['../../src/writescore/cli/main.py'],
    pathex=[],
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
