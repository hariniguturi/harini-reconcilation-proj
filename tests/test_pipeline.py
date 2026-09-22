from datetime import date

from office_recon.pipeline import fifth_business_day, run_reconciliation
from scripts_helper import write_inputs


def test_fifth_business_day_skips_weekend():
    # 1 Sep 2026 is a Tuesday, so the fifth business day is 7 Sep 2026.
    assert fifth_business_day(2026, 9) == date(2026, 9, 7)


def test_end_to_end_sample_run(tmp_dirs, settings):
    incoming, outgoing = tmp_dirs
    write_inputs(incoming)

    result = run_reconciliation(
        input_dir=incoming,
        output_dir=outgoing,
        settings=settings,
        reporting_date=date(2026, 8, 31),
    )

    assert result.report_path.exists()
    assert (outgoing / "carry_forward_ledger.xlsx").exists()
    assert (outgoing / "carry_forward.db").exists()

    by_ref = result.reconciled.set_index("reference_no")
    assert by_ref.loc["REF-1001", "reversal_status"] == "FULL_REVERSAL"
    assert by_ref.loc["REF-2001", "reversal_status"] == "PART_REVERSAL"
    assert by_ref.loc["REF-3001", "reversal_status"] == "PENDING"
    assert by_ref.loc["REF-4001", "business_status"] == "OVERDUE"
    assert by_ref.loc["REF-EXC-001", "tat_status"] == "EXCEPTION"
    assert by_ref.loc["REF-CF-FULL", "reversal_status"] == "FULL_REVERSAL"
    assert by_ref.loc["REF-CF-PART", "reversal_status"] == "PART_REVERSAL"
    assert by_ref.loc["REF-CF-PART", "residual_balance"] == 700.0

    carried = set(result.carry_forward["reference_no"])
    assert "REF-1001" not in carried
    assert "REF-CF-FULL" not in carried
    assert "REF-2001" in carried
    assert "REF-3001" in carried
    assert "REF-4001" in carried
    assert "REF-EXC-001" in carried
    assert "REF-CF-PART" in carried

    unmatched = set(result.unmatched_reversals["reference_no"])
    assert "REV-ORPHAN" in unmatched

    assert result.counts["Full Reversals"] == 2
    assert result.counts["Part Reversals"] == 2
    assert result.counts["Pending"] == 3
    assert result.counts["Overdue"] == 3
