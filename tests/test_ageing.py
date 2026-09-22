from office_recon.ageing_calculator import ageing_calculator
from office_recon.reversal_matcher import reversal_matcher


def test_full_partial_and_pending_statuses(
    sample_monthly, empty_carry, settings, reporting_date
):
    matched = reversal_matcher(sample_monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    by_ref = aged.set_index("reference_no")["reversal_status"]
    assert by_ref["REF-1001"] == "FULL_REVERSAL"
    assert by_ref["REF-2001"] == "PART_REVERSAL"
    assert by_ref["REF-3001"] == "PENDING"


def test_residual_and_ageing_days(
    sample_monthly, empty_carry, settings, reporting_date
):
    matched = reversal_matcher(sample_monthly, empty_carry, settings)
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], reporting_date, settings
    )
    part = aged.loc[aged["reference_no"] == "REF-2001"].iloc[0]
    assert part["residual_balance"] == 3000.0
    assert part["ageing_days"] == 21

    pending = aged.loc[aged["reference_no"] == "REF-3001"].iloc[0]
    assert pending["residual_balance"] == 750.0
    assert pending["ageing_days"] == 3
