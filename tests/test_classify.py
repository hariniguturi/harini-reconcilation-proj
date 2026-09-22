from office_recon.classify import classify_account_type


def test_classify_uses_sheet_type_when_present(sample_monthly, settings):
    out = classify_account_type(sample_monthly, settings)
    assert set(out["account_type"]) <= {"BASIC", "POINTING"}
    pointing = out.loc[out["reference_no"] == "REF-2001", "account_type"].iloc[0]
    assert pointing == "POINTING"


def test_classify_falls_back_to_account_master(settings):
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "account_code": "OA1008",
                "account_type": None,
                "txn_date": None,
                "txn_type": "CREDIT",
                "reference_no": "X",
                "amount": 1,
                "branch_code": "BR001",
            }
        ]
    )
    out = classify_account_type(df, settings)
    assert out.loc[0, "account_type"] == "POINTING"
    assert bool(out.loc[0, "in_scope"]) is True


def test_unknown_account_is_out_of_scope(settings):
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "account_code": "OA9999",
                "account_type": "BASIC",
                "txn_date": None,
                "txn_type": "CREDIT",
                "reference_no": "X",
                "amount": 1,
                "branch_code": "BR001",
            }
        ]
    )
    out = classify_account_type(df, settings)
    assert bool(out.loc[0, "in_scope"]) is False
