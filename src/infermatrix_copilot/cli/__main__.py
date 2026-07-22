"""Enable `python -m infermatrix_copilot.cli` (parity with the old flat module)."""

import sys

from .entry import main

sys.exit(main())
