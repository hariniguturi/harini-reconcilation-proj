"""Link each reversal to its original credit on Reference No. / Original Credit Ref."""

from __future__ import annotations

import pandas as pd

from office_recon.config import Settings


def _as_abs_amount(series: pd.Series) -> pd.Series:
    return series.fillna(0).astype(float).abs()


def split_credits_and_reversals(
    monthly: pd.DataFrame, settings: Settings
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return credits, reversals, and leftover rows that could not be classified."""
    df = monthly.copy()
    credit_mask = df["txn_type"].isin(settings.credit_txn_types)
    reversal_mask = df["txn_type"].isin(settings.reversal_txn_types)

    # Signed amounts: a negative row with no recognised type is treated as a reversal.
    inferred_reversal = (~credit_mask) & (~reversal_mask) & (df["amount"] < 0)
    inferred_credit = (~credit_mask) & (~reversal_mask) & (df["amount"] >= 0)

    credits = df.loc[credit_mask | inferred_credit].copy()
    reversals = df.loc[reversal_mask | inferred_reversal].copy()
    leftover = df.loc[~(credit_mask | reversal_mask | inferred_reversal | inferred_credit)]
    return credits, reversals, leftover


def _open_items_from_credits(credits: pd.DataFrame) -> pd.DataFrame:
    items = credits.copy()
    items["open_amount"] = _as_abs_amount(items["amount"])
    items["ageing_start_date"] = items["txn_date"]
    items["source"] = "CURRENT"
    items["match_key"] = items["reference_no"]
    items["original_credit_ref"] = items["reference_no"]
    return items


def _open_items_from_carry_forward(carry_forward: pd.DataFrame) -> pd.DataFrame:
    if carry_forward.empty:
        return pd.DataFrame()
    items = carry_forward.copy()
    items["open_amount"] = _as_abs_amount(items["pending_balance"])
    items["source"] = "CARRY_FORWARD"
    items["match_key"] = items["reference_no"]
    items["txn_date"] = items["ageing_start_date"]
    items["txn_type"] = "CARRY_FORWARD"
    items["amount"] = items["pending_balance"]
    items["narration"] = items.get("narration", "Brought forward from prior cycle")
    if "original_credit_ref" not in items.columns:
        items["original_credit_ref"] = items["reference_no"]
    items["original_credit_ref"] = items["original_credit_ref"].fillna(
        items["reference_no"]
    )
    return items


def reversal_matcher(
    monthly: pd.DataFrame,
    carry_forward: pd.DataFrame,
    settings: Settings,
) -> dict[str, pd.DataFrame]:
    credits, reversals, leftover = split_credits_and_reversals(monthly, settings)

    open_current = _open_items_from_credits(credits)
    open_prior = _open_items_from_carry_forward(carry_forward)
    open_items = pd.concat([open_current, open_prior], ignore_index=True, sort=False)

    if open_items.empty:
        reversals = reversals.copy()
        reversals["matched"] = False
        return {
            "open_items": open_items,
            "reversals": reversals,
            "matches": pd.DataFrame(),
            "unmatched_reversals": reversals,
            "leftover": leftover,
        }

    rev = reversals.copy()
    rev["reversal_amount"] = _as_abs_amount(rev["amount"])
    rev["match_key"] = rev["original_credit_ref"]
    missing_link = rev["match_key"].isna() | (
        rev["match_key"].astype(str).str.strip() == ""
    )
    if not settings.require_original_credit_ref_for_pointing:
        rev.loc[missing_link, "match_key"] = rev.loc[missing_link, "reference_no"]
        missing_link = rev["match_key"].isna() | (
            rev["match_key"].astype(str).str.strip() == ""
        )
    else:
        pointing = rev["account_type"].astype(str).str.upper().eq("POINTING")
        # BASIC reversals may fall back to their own reference if the link is blank.
        rev.loc[missing_link & ~pointing, "match_key"] = rev.loc[
            missing_link & ~pointing, "reference_no"
        ]
        missing_link = rev["match_key"].isna() | (
            rev["match_key"].astype(str).str.strip() == ""
        )

    rev["matched"] = False
    matches = open_items.merge(
        rev.loc[~missing_link],
        how="inner",
        on="match_key",
        suffixes=("_credit", "_reversal"),
    )
    if not matches.empty:
        matches["matched"] = True
        matched_keys = set(matches["match_key"].astype(str))
        rev.loc[rev["match_key"].astype(str).isin(matched_keys), "matched"] = True

    unmatched = rev.loc[~rev["matched"]].copy()
    return {
        "open_items": open_items,
        "reversals": rev,
        "matches": matches,
        "unmatched_reversals": unmatched,
        "leftover": leftover,
    }


def reversal_totals(matches: pd.DataFrame) -> pd.DataFrame:
    if matches.empty:
        return pd.DataFrame(
            columns=["match_key", "reversal_count", "reversal_total", "linked_refs"]
        )
    grouped = (
        matches.groupby("match_key", as_index=False)
        .agg(
            reversal_count=("reversal_amount", "size"),
            reversal_total=("reversal_amount", "sum"),
            linked_refs=("reference_no_reversal", lambda s: ", ".join(s.astype(str))),
        )
    )
    return grouped
