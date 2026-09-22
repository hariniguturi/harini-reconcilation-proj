from datetime import date

import pandas as pd

from office_recon.ageing_calculator import ageing_calculator
from office_recon.carry_forward import build_carry_forward, persist_carry_forward
from office_recon.reversal_matcher import reversal_matcher
from office_recon.tat_checker import tat_checker


def test_only_open_items_are_persisted(
    sample_monthly, empty_carry, settings, reporting_date
):
    matched = reversal_matcher(sample_monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    checked = tat_checker(aged, reporting_date, settings)
    ledger = build_carry_forward(checked)
    refs = set(ledger["reference_no"])
    assert "REF-1001" not in refs
    assert "REF-2001" in refs
    assert "REF-3001" in refs
    part = ledger.loc[ledger["reference_no"] == "REF-2001"].iloc[0]
    assert part["pending_balance"] == 3000.0


def test_sqlite_round_trip(tmp_path, sample_monthly, empty_carry, settings, reporting_date):
    matched = reversal_matcher(sample_monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    checked = tat_checker(aged, reporting_date, settings)
    ledger = build_carry_forward(checked)
    paths = persist_carry_forward(ledger, tmp_path)
    assert paths["sqlite"].exists()
    assert paths["csv"].exists()
    reloaded = pd.read_csv(paths["csv"])
    assert len(reloaded) == len(ledger)


def test_prior_cycle_item_can_close_this_month(settings, reporting_date):
    monthly = pd.DataFrame(
        [
            {
                "account_code": "OA1007",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 8),
                "txn_type": "REVERSAL",
                "reference_no": "REV-CF",
                "original_credit_ref": "REF-CF-FULL",
                "amount": -600.0,
                "branch_code": "BR001",
                "narration": "close bf",
            }
        ]
    )
    carry = pd.DataFrame(
        [
            {
                "account_code": "OA1007",
                "account_type": "POINTING",
                "reference_no": "REF-CF-FULL",
                "original_credit_ref": "REF-CF-FULL",
                "pending_balance": 600.0,
                "ageing_start_date": date(2026, 7, 20),
                "status": "PENDING",
                "branch_code": "BR001",
            }
        ]
    )
    matched = reversal_matcher(monthly, carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    checked = tat_checker(aged, reporting_date, settings)
    assert checked.iloc[0]["reversal_status"] == "FULL_REVERSAL"
    assert checked.iloc[0]["ageing_days"] == 42
    assert build_carry_forward(checked).empty
