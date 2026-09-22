"""Entry point: python run_reconciliation.py --input-dir data/input --output-dir data/output"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from office_recon.pipeline import main


if __name__ == "__main__":
    raise SystemExit(main())
