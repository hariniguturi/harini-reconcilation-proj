"""Residual balance and ageing (Full / Partial / Pending) from the original date."""

from __future__ import annotations

from datetime import date

import pandas as pd

from office_recon.config import Settings
from office_recon.reversal_matcher import reversal_totals


def ageing_calculator(
    open_items: pd.DataFrame,
    matches: pd.DataFrame,
    reporting_date: date,
    settings: Settings,
) -> pd.DataFrame:
    items = open_items.copy()
    totals = reversal_totals(matches)
    items = items.merge(totals, how="left", on="match_key")
    items["reversal_count"] = (
        pd.to_numeric(items["reversal_count"], errors="coerce").fillna(0).astype(int)
    )
    items["reversal_total"] = pd.to_numeric(
        items["reversal_total"], errors="coerce"
    ).fillna(0.0)
    items["linked_refs"] = items["linked_refs"].fillna("")

    items["residual_balance"] = (
        items["open_amount"].astype(float) - items["reversal_total"].astype(float)
    ).round(2)

    tolerance = float(settings.amount_tolerance)
    residual = items["residual_balance"]

    status = pd.Series("PENDING", index=items.index)
    status = status.mask(residual.abs() <= tolerance, "FULL_REVERSAL")
    status = status.mask(
        (residual > tolerance) & (items["reversal_total"] > 0), "PART_REVERSAL"
    )
    status = status.mask(residual < -tolerance, "OVER_REVERSED")
    items["reversal_status"] = status
    items.loc[items["residual_balance"].abs() <= tolerance, "residual_balance"] = 0.0

    items["ageing_days"] = items["ageing_start_date"].apply(
        lambda start: (reporting_date - start).days if pd.notna(start) else pd.NA
    )
    return items
