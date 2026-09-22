"""Tag each entry BASIC or POINTING from the account type field or account master."""

from __future__ import annotations

import pandas as pd

from office_recon.config import Settings


def classify_account_type(monthly: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    df = monthly.copy()
    if "account_type" not in df.columns:
        df["account_type"] = pd.NA

    mapped = df["account_code"].map(
        lambda code: settings.account_type(code) if pd.notna(code) else None
    )
    sheet_type = df["account_type"].replace(
        {"": pd.NA, "NAN": pd.NA, "NONE": pd.NA, "OAP": "POINTING"}
    )
    df["account_type"] = sheet_type.fillna(mapped).fillna("BASIC")
    df["account_type"] = df["account_type"].astype(str).str.upper().replace(
        {"OAP": "POINTING"}
    )
    df["in_scope"] = df["account_code"].map(settings.is_approved_account)
    return df
