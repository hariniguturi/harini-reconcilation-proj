"""Read the monthly sheet, branch master, and prior-cycle carry-forward ledger."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MONTHLY_COLUMNS = {
    "account code": "account_code",
    "account_code": "account_code",
    "account type": "account_type",
    "account_type": "account_type",
    "txn date": "txn_date",
    "txn_date": "txn_date",
    "transaction date": "txn_date",
    "txn type": "txn_type",
    "txn_type": "txn_type",
    "transaction type": "txn_type",
    "reference no.": "reference_no",
    "reference no": "reference_no",
    "reference_no": "reference_no",
    "original credit ref.": "original_credit_ref",
    "original credit ref": "original_credit_ref",
    "original_credit_ref": "original_credit_ref",
    "amount": "amount",
    "branch code": "branch_code",
    "branch_code": "branch_code",
    "narration": "narration",
}

BRANCH_COLUMNS = {
    "branch code": "branch_code",
    "branch_code": "branch_code",
    "branch name": "branch_name",
    "branch_name": "branch_name",
    "email": "email",
    "region": "region",
}

CARRY_FORWARD_COLUMNS = {
    "account code": "account_code",
    "account_code": "account_code",
    "account type": "account_type",
    "account_type": "account_type",
    "reference no.": "reference_no",
    "reference no": "reference_no",
    "reference_no": "reference_no",
    "original credit ref.": "original_credit_ref",
    "original credit ref": "original_credit_ref",
    "original_credit_ref": "original_credit_ref",
    "pending balance": "pending_balance",
    "pending_balance": "pending_balance",
    "ageing start date": "ageing_start_date",
    "ageing_start_date": "ageing_start_date",
    "status": "status",
    "branch code": "branch_code",
    "branch_code": "branch_code",
}

TAT_EXCEPTION_COLUMNS = {
    "reference no.": "reference_no",
    "reference no": "reference_no",
    "reference_no": "reference_no",
    "reason": "reason",
    "expiry date": "expiry_date",
    "expiry_date": "expiry_date",
}


def _normalise_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    rename = {}
    for column in df.columns:
        key = str(column).strip().lower()
        if key in mapping:
            rename[column] = mapping[key]
    out = df.rename(columns=rename).copy()
    return out


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str)
    raise ValueError(f"Unsupported file type: {path}")


def _blank_to_na(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        out[column] = out[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return out


def load_monthly_sheet(path: Path) -> pd.DataFrame:
    df = _blank_to_na(_normalise_columns(_read_table(path), MONTHLY_COLUMNS))
    if "txn_date" in df.columns:
        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.date
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "txn_type" in df.columns:
        df["txn_type"] = df["txn_type"].astype(str).str.strip().str.upper()
    if "account_code" in df.columns:
        df["account_code"] = df["account_code"].astype(str).str.strip().str.upper()
    if "account_type" in df.columns:
        df["account_type"] = df["account_type"].astype(str).str.strip().str.upper()
        df["account_type"] = df["account_type"].replace({"NAN": pd.NA, "NONE": pd.NA})
    if "reference_no" in df.columns:
        df["reference_no"] = df["reference_no"].astype(str).str.strip()
    if "original_credit_ref" in df.columns:
        df["original_credit_ref"] = df["original_credit_ref"].astype(str).str.strip()
        df.loc[
            df["original_credit_ref"].isin({"nan", "None", "<NA>", ""}),
            "original_credit_ref",
        ] = pd.NA
    return df


def load_branch_master(path: Path) -> pd.DataFrame:
    df = _blank_to_na(_normalise_columns(_read_table(path), BRANCH_COLUMNS))
    if "branch_code" in df.columns:
        df["branch_code"] = df["branch_code"].astype(str).str.strip()
    return df


def load_carry_forward(path: Path | None) -> pd.DataFrame:
    empty = pd.DataFrame(
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
    if path is None or not path.exists():
        return empty
    df = _blank_to_na(_normalise_columns(_read_table(path), CARRY_FORWARD_COLUMNS))
    if df.empty:
        return empty
    if "ageing_start_date" in df.columns:
        df["ageing_start_date"] = pd.to_datetime(
            df["ageing_start_date"], errors="coerce"
        ).dt.date
    if "pending_balance" in df.columns:
        df["pending_balance"] = pd.to_numeric(df["pending_balance"], errors="coerce")
    if "account_code" in df.columns:
        df["account_code"] = df["account_code"].astype(str).str.strip().str.upper()
    if "account_type" in df.columns:
        df["account_type"] = df["account_type"].astype(str).str.strip().str.upper()
    return df


def load_tat_exceptions_file(path: Path | None) -> pd.DataFrame:
    empty = pd.DataFrame(columns=["reference_no", "reason", "expiry_date"])
    if path is None or not path.exists():
        return empty
    df = _blank_to_na(_normalise_columns(_read_table(path), TAT_EXCEPTION_COLUMNS))
    if "expiry_date" in df.columns:
        df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce").dt.date
    return df


def resolve_input_file(input_dir: Path, stems: list[str]) -> Path | None:
    """Find the first matching xlsx/xls/csv in the input folder."""
    for stem in stems:
        for suffix in (".xlsx", ".xls", ".csv"):
            candidate = input_dir / f"{stem}{suffix}"
            if candidate.exists():
                return candidate
    return None


def load_inputs(input_dir: Path) -> dict[str, pd.DataFrame | Path | None]:
    monthly_path = resolve_input_file(
        input_dir, ["monthly_office_account_sheet", "monthly_sheet"]
    )
    branch_path = resolve_input_file(input_dir, ["branch_master"])
    carry_path = resolve_input_file(
        input_dir, ["carry_forward_ledger", "carry_forward"]
    )
    exception_path = resolve_input_file(input_dir, ["tat_exceptions"])

    if monthly_path is None:
        raise FileNotFoundError(
            f"Monthly office account sheet not found in {input_dir}"
        )
    if branch_path is None:
        raise FileNotFoundError(f"Branch master not found in {input_dir}")

    return {
        "monthly": load_monthly_sheet(monthly_path),
        "branch": load_branch_master(branch_path),
        "carry_forward": load_carry_forward(carry_path),
        "tat_exceptions_file": load_tat_exceptions_file(exception_path),
        "monthly_path": monthly_path,
        "branch_path": branch_path,
        "carry_forward_path": carry_path,
        "tat_exceptions_path": exception_path,
    }
