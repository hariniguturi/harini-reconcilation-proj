"""Flag entries that breach the 7-day TAT unless a documented exception exists."""

from __future__ import annotations

from datetime import date

import pandas as pd

from office_recon.config import Settings, TatException


def _exceptions_from_file(file_df: pd.DataFrame) -> dict[str, TatException]:
    extras: dict[str, TatException] = {}
    if file_df is None or file_df.empty:
        return extras
    for row in file_df.itertuples(index=False):
        ref = str(getattr(row, "reference_no", "")).strip()
        if not ref:
            continue
        extras[ref] = TatException(
            reference_no=ref,
            reason=str(getattr(row, "reason", "Documented exception") or "Documented exception"),
            expiry_date=getattr(row, "expiry_date", None),
        )
    return extras


def tat_checker(
    aged: pd.DataFrame,
    reporting_date: date,
    settings: Settings,
    extra_exceptions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    df = aged.copy()
    extras = _exceptions_from_file(extra_exceptions if extra_exceptions is not None else pd.DataFrame())

    tat_status = []
    exception_reason = []
    days_overdue = []

    for row in df.itertuples(index=False):
        ref = str(getattr(row, "reference_no", "") or "")
        status = str(getattr(row, "reversal_status", ""))
        ageing = getattr(row, "ageing_days", 0)
        ageing = int(ageing) if pd.notna(ageing) else 0

        documented = settings.exception_for(ref, reporting_date) or extras.get(ref)
        if documented is not None and (
            documented.expiry_date is None or reporting_date <= documented.expiry_date
        ):
            tat_status.append("EXCEPTION")
            exception_reason.append(documented.reason)
            days_overdue.append(max(0, ageing - settings.tat_days))
            continue

        open_item = status in {"PENDING", "PART_REVERSAL"}
        if open_item and ageing > settings.tat_days:
            tat_status.append("OVERDUE")
            exception_reason.append("")
            days_overdue.append(ageing - settings.tat_days)
        elif status == "FULL_REVERSAL":
            tat_status.append("CLOSED")
            exception_reason.append("")
            days_overdue.append(0)
        elif status == "OVER_REVERSED":
            tat_status.append("EXCEPTION")
            exception_reason.append("Reversal total exceeds original credit")
            days_overdue.append(0)
        else:
            tat_status.append("WITHIN_TAT")
            exception_reason.append("")
            days_overdue.append(0)

    df["tat_status"] = tat_status
    df["exception_reason"] = exception_reason
    df["days_overdue"] = days_overdue

    # Business status used on the summary: overdue open items are escalated.
    df["business_status"] = df["reversal_status"]
    df.loc[
        (df["tat_status"] == "OVERDUE")
        & (df["reversal_status"].isin(["PENDING", "PART_REVERSAL"])),
        "business_status",
    ] = "OVERDUE"
    return df
