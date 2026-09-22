from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from office_recon.config import load_settings


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def reporting_date():
    return date(2026, 8, 31)


@pytest.fixture
def sample_monthly() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "account_code": "OA1001",
                "account_type": "BASIC",
                "txn_date": date(2026, 8, 3),
                "txn_type": "CREDIT",
                "reference_no": "REF-1001",
                "original_credit_ref": pd.NA,
                "amount": 1500.0,
                "branch_code": "BR001",
                "narration": "full",
            },
            {
                "account_code": "OA1001",
                "account_type": "BASIC",
                "txn_date": date(2026, 8, 5),
                "txn_type": "REVERSAL",
                "reference_no": "REV-1001",
                "original_credit_ref": "REF-1001",
                "amount": -1500.0,
                "branch_code": "BR001",
                "narration": "full rev",
            },
            {
                "account_code": "OA1006",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 10),
                "txn_type": "CREDIT",
                "reference_no": "REF-2001",
                "original_credit_ref": pd.NA,
                "amount": 4000.0,
                "branch_code": "BR002",
                "narration": "part",
            },
            {
                "account_code": "OA1006",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 12),
                "txn_type": "REVERSAL",
                "reference_no": "REV-2001",
                "original_credit_ref": "REF-2001",
                "amount": -1000.0,
                "branch_code": "BR002",
                "narration": "part rev",
            },
            {
                "account_code": "OA1002",
                "account_type": "BASIC",
                "txn_date": date(2026, 8, 28),
                "txn_type": "CREDIT",
                "reference_no": "REF-3001",
                "original_credit_ref": pd.NA,
                "amount": 750.0,
                "branch_code": "BR001",
                "narration": "pending",
            },
        ]
    )


@pytest.fixture
def empty_carry() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "account_code",
            "account_type",
            "reference_no",
            "original_credit_ref",
            "pending_balance",
            "ageing_start_date",
            "status",
            "branch_code",
        ]
    )


@pytest.fixture
def branch_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "branch_code": "BR001",
                "branch_name": "MG Road",
                "email": "mg@bank.example",
                "region": "South",
            },
            {
                "branch_code": "BR002",
                "branch_name": "Bandra",
                "email": "ba@bank.example",
                "region": "West",
            },
        ]
    )


@pytest.fixture
def tmp_dirs(tmp_path: Path):
    incoming = tmp_path / "input"
    outgoing = tmp_path / "output"
    incoming.mkdir()
    outgoing.mkdir()
    return incoming, outgoing
