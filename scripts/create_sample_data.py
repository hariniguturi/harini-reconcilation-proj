"""Build the sample SharePoint-style Excel files used for a first run and tests."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INPUT_DIR = ROOT / "data" / "input"


def write_sample_inputs(input_dir: Path = INPUT_DIR) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)

    monthly = pd.DataFrame(
        [
            # Full reversal — Basic
            {
                "Account Code": "OA1001",
                "Account Type": "BASIC",
                "Txn Date": date(2026, 8, 3),
                "Txn Type": "CREDIT",
                "Reference No.": "REF-1001",
                "Original Credit Ref.": None,
                "Amount": 1500.00,
                "Branch Code": "BR001",
                "Narration": "Customer refund posted",
            },
            {
                "Account Code": "OA1001",
                "Account Type": "BASIC",
                "Txn Date": date(2026, 8, 5),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-1001",
                "Original Credit Ref.": "REF-1001",
                "Amount": -1500.00,
                "Branch Code": "BR001",
                "Narration": "Full reversal of REF-1001",
            },
            # Part reversal — Pointing
            {
                "Account Code": "OA1006",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 10),
                "Txn Type": "CREDIT",
                "Reference No.": "REF-2001",
                "Original Credit Ref.": None,
                "Amount": 4000.00,
                "Branch Code": "BR002",
                "Narration": "Outward clearing credit",
            },
            {
                "Account Code": "OA1006",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 12),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-2001A",
                "Original Credit Ref.": "REF-2001",
                "Amount": -1500.00,
                "Branch Code": "BR002",
                "Narration": "Partial reversal 1",
            },
            {
                "Account Code": "OA1006",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 18),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-2001B",
                "Original Credit Ref.": "REF-2001",
                "Amount": -500.00,
                "Branch Code": "BR002",
                "Narration": "Partial reversal 2",
            },
            # Pending, still inside 7-day TAT at month end? Ageing from 28 Aug to 31 Aug = 3 days
            {
                "Account Code": "OA1002",
                "Account Type": "BASIC",
                "Txn Date": date(2026, 8, 28),
                "Txn Type": "CREDIT",
                "Reference No.": "REF-3001",
                "Original Credit Ref.": None,
                "Amount": 750.00,
                "Branch Code": "BR001",
                "Narration": "Unclaimed credit awaiting reversal",
            },
            # Overdue without exception — ageing from 10 Aug to 31 Aug = 21 days
            {
                "Account Code": "OA1003",
                "Account Type": "BASIC",
                "Txn Date": date(2026, 8, 10),
                "Txn Type": "CREDIT",
                "Reference No.": "REF-4001",
                "Original Credit Ref.": None,
                "Amount": 2200.00,
                "Branch Code": "BR003",
                "Narration": "Clearing difference not reversed",
            },
            # Documented TAT exception (see settings.yaml REF-EXC-001)
            {
                "Account Code": "OA1004",
                "Account Type": "BASIC",
                "Txn Date": date(2026, 8, 1),
                "Txn Type": "CREDIT",
                "Reference No.": "REF-EXC-001",
                "Original Credit Ref.": None,
                "Amount": 980.00,
                "Branch Code": "BR002",
                "Narration": "Legal hold — do not escalate",
            },
            # New reversals against items brought forward
            {
                "Account Code": "OA1007",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 8),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-CF-01",
                "Original Credit Ref.": "REF-CF-FULL",
                "Amount": -600.00,
                "Branch Code": "BR001",
                "Narration": "Closes prior-cycle pending item",
            },
            {
                "Account Code": "OA1008",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 15),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-CF-02",
                "Original Credit Ref.": "REF-CF-PART",
                "Amount": -200.00,
                "Branch Code": "BR003",
                "Narration": "Further part reversal of brought-forward item",
            },
            # Unmatched pointing reversal
            {
                "Account Code": "OA1009",
                "Account Type": "POINTING",
                "Txn Date": date(2026, 8, 20),
                "Txn Type": "REVERSAL",
                "Reference No.": "REV-ORPHAN",
                "Original Credit Ref.": "REF-DOES-NOT-EXIST",
                "Amount": -125.00,
                "Branch Code": "BR002",
                "Narration": "No original credit on file",
            },
        ]
    )

    branches = pd.DataFrame(
        [
            {
                "Branch Code": "BR001",
                "Branch Name": "MG Road",
                "Email": "mgroad.ops@bank.example",
                "Region": "South",
            },
            {
                "Branch Code": "BR002",
                "Branch Name": "Bandra West",
                "Email": "bandra.ops@bank.example",
                "Region": "West",
            },
            {
                "Branch Code": "BR003",
                "Branch Name": "Connaught Place",
                "Email": "cp.ops@bank.example",
                "Region": "North",
            },
        ]
    )

    carry_forward = pd.DataFrame(
        [
            {
                "Account Code": "OA1007",
                "Account Type": "POINTING",
                "Reference No.": "REF-CF-FULL",
                "Original Credit Ref.": "REF-CF-FULL",
                "Pending Balance": 600.00,
                "Ageing Start Date": date(2026, 7, 20),
                "Status": "PENDING",
                "Branch Code": "BR001",
            },
            {
                "Account Code": "OA1008",
                "Account Type": "POINTING",
                "Reference No.": "REF-CF-PART",
                "Original Credit Ref.": "REF-CF-PART",
                "Pending Balance": 900.00,
                "Ageing Start Date": date(2026, 7, 18),
                "Status": "PART_REVERSAL",
                "Branch Code": "BR003",
            },
        ]
    )

    monthly.to_excel(input_dir / "monthly_office_account_sheet.xlsx", index=False)
    branches.to_excel(input_dir / "branch_master.xlsx", index=False)
    carry_forward.to_excel(input_dir / "carry_forward_ledger.xlsx", index=False)


if __name__ == "__main__":
    write_sample_inputs()
    print(f"Sample input files written to {INPUT_DIR}")
