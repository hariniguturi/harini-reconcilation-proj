"""Schema, duplicate, date, and total checks on the three input files."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from office_recon.config import Settings

REQUIRED_MONTHLY = [
    "account_code",
    "txn_date",
    "txn_type",
    "reference_no",
    "amount",
    "branch_code",
]
REQUIRED_BRANCH = ["branch_code", "branch_name", "email"]
REQUIRED_CARRY = ["account_code", "reference_no", "pending_balance", "ageing_start_date"]


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    monthly_count: int = 0
    monthly_amount_total: float = 0.0

    def raise_if_failed(self) -> None:
        if not self.ok:
            joined = "\n".join(f"- {item}" for item in self.errors)
            raise ValueError(f"Input validation failed:\n{joined}")


def _missing_columns(df: pd.DataFrame, required: list[str], label: str) -> list[str]:
    missing = [col for col in required if col not in df.columns]
    if missing:
        return [f"{label} is missing required columns: {missing}"]
    return []


def validate_inputs(
    monthly: pd.DataFrame,
    branch: pd.DataFrame,
    carry_forward: pd.DataFrame,
    settings: Settings,
) -> ValidationResult:
    result = ValidationResult(ok=True)
    result.errors.extend(_missing_columns(monthly, REQUIRED_MONTHLY, "Monthly sheet"))
    result.errors.extend(_missing_columns(branch, REQUIRED_BRANCH, "Branch master"))
    if not carry_forward.empty:
        result.errors.extend(
            _missing_columns(carry_forward, REQUIRED_CARRY, "Carry-forward ledger")
        )

    if result.errors:
        result.ok = False
        return result

    if monthly.empty:
        result.errors.append("Monthly sheet has no rows.")

    invalid_dates = monthly["txn_date"].isna().sum()
    if invalid_dates:
        result.errors.append(f"Monthly sheet has {invalid_dates} invalid txn dates.")

    invalid_amounts = monthly["amount"].isna().sum()
    if invalid_amounts:
        result.errors.append(f"Monthly sheet has {invalid_amounts} invalid amounts.")

    blank_refs = monthly["reference_no"].isna() | (
        monthly["reference_no"].astype(str).str.strip() == ""
    )
    if blank_refs.any():
        result.errors.append(
            f"Monthly sheet has {int(blank_refs.sum())} blank Reference No. values."
        )

    credit_mask = monthly["txn_type"].isin(settings.credit_txn_types)
    credit_refs = monthly.loc[credit_mask, "reference_no"]
    dupes = credit_refs[credit_refs.duplicated(keep=False)]
    if not dupes.empty:
        result.errors.append(
            "Duplicate credit Reference No. values: "
            + ", ".join(sorted(dupes.astype(str).unique())[:10])
        )

    unknown_accounts = sorted(
        {
            code
            for code in monthly["account_code"].dropna().astype(str)
            if not settings.is_approved_account(code)
        }
    )
    if unknown_accounts:
        result.warnings.append(
            "Rows found for account codes not in the nine-account master: "
            + ", ".join(unknown_accounts)
        )

    unknown_branches = sorted(
        set(monthly["branch_code"].dropna().astype(str))
        - set(branch["branch_code"].dropna().astype(str))
    )
    if unknown_branches:
        result.warnings.append(
            "Branch codes in the monthly sheet are missing from branch master: "
            + ", ".join(unknown_branches[:10])
        )

    result.monthly_count = int(len(monthly))
    result.monthly_amount_total = float(monthly["amount"].fillna(0).sum())
    result.ok = not result.errors
    return result
