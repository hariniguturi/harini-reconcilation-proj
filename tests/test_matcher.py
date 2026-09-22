from office_recon.reversal_matcher import reversal_matcher, reversal_totals


def test_one_to_one_full_match(sample_monthly, empty_carry, settings):
    result = reversal_matcher(sample_monthly, empty_carry, settings)
    totals = reversal_totals(result["matches"])
    row = totals.loc[totals["match_key"] == "REF-1001"].iloc[0]
    assert row["reversal_total"] == 1500.0
    assert row["reversal_count"] == 1


def test_one_to_many_reversals(settings, empty_carry):
    import pandas as pd
    from datetime import date

    monthly = pd.DataFrame(
        [
            {
                "account_code": "OA1006",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 1),
                "txn_type": "CREDIT",
                "reference_no": "C1",
                "original_credit_ref": pd.NA,
                "amount": 1000.0,
                "branch_code": "BR001",
                "narration": "c",
            },
            {
                "account_code": "OA1006",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 2),
                "txn_type": "REVERSAL",
                "reference_no": "R1",
                "original_credit_ref": "C1",
                "amount": -400.0,
                "branch_code": "BR001",
                "narration": "r1",
            },
            {
                "account_code": "OA1006",
                "account_type": "POINTING",
                "txn_date": date(2026, 8, 3),
                "txn_type": "REVERSAL",
                "reference_no": "R2",
                "original_credit_ref": "C1",
                "amount": -250.0,
                "branch_code": "BR001",
                "narration": "r2",
            },
        ]
    )
    result = reversal_matcher(monthly, empty_carry, settings)
    totals = reversal_totals(result["matches"])
    assert float(totals.loc[0, "reversal_total"]) == 650.0
    assert int(totals.loc[0, "reversal_count"]) == 2


def test_unmatched_reversal_is_retained(sample_monthly, empty_carry, settings):
    import pandas as pd
    from datetime import date

    extra = sample_monthly.copy()
    extra = pd.concat(
        [
            extra,
            pd.DataFrame(
                [
                    {
                        "account_code": "OA1009",
                        "account_type": "POINTING",
                        "txn_date": date(2026, 8, 20),
                        "txn_type": "REVERSAL",
                        "reference_no": "ORPHAN",
                        "original_credit_ref": "NO-SUCH-CREDIT",
                        "amount": -50.0,
                        "branch_code": "BR002",
                        "narration": "orphan",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    result = reversal_matcher(extra, empty_carry, settings)
    refs = set(result["unmatched_reversals"]["reference_no"])
    assert "ORPHAN" in refs
