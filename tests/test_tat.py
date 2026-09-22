from datetime import date

import pandas as pd

from office_recon.ageing_calculator import ageing_calculator
from office_recon.reversal_matcher import reversal_matcher
from office_recon.tat_checker import tat_checker


def test_overdue_without_exception(settings, empty_carry, reporting_date):
    monthly = pd.DataFrame(
        [
            {
                "account_code": "OA1003",
                "account_type": "BASIC",
                "txn_date": date(2026, 8, 10),
                "txn_type": "CREDIT",
                "reference_no": "OLD-1",
                "original_credit_ref": pd.NA,
                "amount": 100.0,
                "branch_code": "BR001",
                "narration": "old",
            }
        ]
    )
    matched = reversal_matcher(monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    checked = tat_checker(aged, reporting_date, settings)
    row = checked.iloc[0]
    assert row["tat_status"] == "OVERDUE"
    assert row["business_status"] == "OVERDUE"
    assert row["days_overdue"] == 14


def test_documented_exception_is_not_overdue(settings, empty_carry, reporting_date):
    monthly = pd.DataFrame(
        [
            {
                "account_code": "OA1004",
                "account_type": "BASIC",
                "txn_date": date(2026, 8, 1),
                "txn_type": "CREDIT",
                "reference_no": "REF-EXC-001",
                "original_credit_ref": pd.NA,
                "amount": 980.0,
                "branch_code": "BR002",
                "narration": "legal hold",
            }
        ]
    )
    matched = reversal_matcher(monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    checked = tat_checker(aged, reporting_date, settings)
    assert checked.iloc[0]["tat_status"] == "EXCEPTION"
    assert checked.iloc[0]["business_status"] == "PENDING"
