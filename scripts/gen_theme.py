#!/usr/bin/env python3
"""Entry point kept for CMake and for direct use: python3 gen_theme.py --help."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lv_theme_yaml.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
