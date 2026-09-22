"""Import the sample-data writer without treating scripts/ as a package."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from create_sample_data import write_sample_inputs as write_inputs  # noqa: E402
