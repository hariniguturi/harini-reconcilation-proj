"""Persist unresolved pending / part-reversal balances for the next cycle."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

LEDGER_COLUMNS = [
    "account_code",
    "account_type",
    "reference_no",
    "original_credit_ref",
    "pending_balance",
    "ageing_start_date",
    "status",
    "branch_code",
]


def build_carry_forward(reconciled: pd.DataFrame) -> pd.DataFrame:
    open_mask = reconciled["reversal_status"].isin(["PENDING", "PART_REVERSAL"])
    ledger = reconciled.loc[open_mask].copy()
    if ledger.empty:
        return pd.DataFrame(columns=LEDGER_COLUMNS)

    ledger["pending_balance"] = ledger["residual_balance"]
    ledger["status"] = ledger["business_status"]
    ledger["original_credit_ref"] = ledger["original_credit_ref"].fillna(
        ledger["reference_no"]
    )
    return ledger[LEDGER_COLUMNS].reset_index(drop=True)


def write_carry_forward_csv(ledger: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(path, index=False)
    return path


def write_carry_forward_xlsx(ledger: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_excel(path, index=False)
    return path


def write_carry_forward_sqlite(ledger: pd.DataFrame, db_path: Path) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        ledger.to_sql("carry_forward_ledger", conn, if_exists="replace", index=False)
    return db_path


def persist_carry_forward(ledger: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    csv_path = output_dir / "carry_forward_ledger.csv"
    xlsx_path = output_dir / "carry_forward_ledger.xlsx"
    db_path = output_dir / "carry_forward.db"
    return {
        "csv": write_carry_forward_csv(ledger, csv_path),
        "xlsx": write_carry_forward_xlsx(ledger, xlsx_path),
        "sqlite": write_carry_forward_sqlite(ledger, db_path),
    }
