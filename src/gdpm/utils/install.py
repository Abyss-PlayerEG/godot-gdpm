"""Install type detection."""

from __future__ import annotations

import sys


def get_install_type() -> str:
    """Detect how gdpm was installed.

    Returns:
        'binary' - PyInstaller/Nuitka compiled
        'pip'    - pip install
        'source' - development/source install
    """
    if getattr(sys, 'frozen', False):
        return 'binary'
    try:
        from importlib.metadata import version
        version('godot-gdpm')
        return 'pip'
    except Exception:
        return 'source'
