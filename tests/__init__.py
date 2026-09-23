"""Tests for the Fi Collar integration."""

from __future__ import annotations

import sys
from pathlib import Path

# Add pyficollar and homeassistant-ficollar root to sys.path
REPO_ROOT = Path(__file__).parent.parent.resolve()
PYFICOLLAR_ROOT = (REPO_ROOT.parent / "pyficollar").resolve()

for path_dir in [str(REPO_ROOT), str(PYFICOLLAR_ROOT)]:
    if Path(path_dir).exists() and path_dir not in sys.path:
        sys.path.insert(0, path_dir)

from tests.mock_ha import setup_mock_homeassistant

setup_mock_homeassistant()
