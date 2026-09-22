"""Orchestrate the nine processing steps from the design document."""

from __future__ import annotations

import argparse
import calendar
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from office_recon.ageing_calculator import ageing_calculator
from office_recon.carry_forward import build_carry_forward, persist_carry_forward
from office_recon.classify import classify_account_type
from office_recon.config import ROOT, Settings, load_settings
from office_recon.load_inputs import load_inputs
from office_recon.logging_setup import setup_logging
from office_recon.report_generator import processing_counts, report_generator
from office_recon.reversal_matcher import reversal_matcher
from office_recon.tat_checker import tat_checker
from office_recon.validators import validate_inputs


@dataclass
class RunResult:
    reconciled: pd.DataFrame
    carry_forward: pd.DataFrame
    unmatched_reversals: pd.DataFrame
    counts: dict[str, int]
    report_path: Path
    log_path: Path
    reporting_date: date


def fifth_business_day(year: int, month: int) -> date:
    day = date(year, month, 1)
    seen = 0
    while True:
        if day.weekday() < 5:
            seen += 1
            if seen == 5:
                return day
        day += timedelta(days=1)


def infer_reporting_date(monthly: pd.DataFrame) -> date:
    dates = [d for d in monthly["txn_date"].dropna().tolist()]
    if not dates:
        today = date.today()
        last = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, last)
    latest = max(dates)
    last = calendar.monthrange(latest.year, latest.month)[1]
    return date(latest.year, latest.month, last)


def next_month(value: date) -> tuple[int, int]:
    if value.month == 12:
        return value.year + 1, 1
    return value.year, value.month + 1


def run_reconciliation(
    input_dir: Path,
    output_dir: Path,
    settings: Settings | None = None,
    reporting_date: date | None = None,
    settings_path: Path | None = None,
) -> RunResult:
    settings = settings or load_settings(settings_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "reconciliation.log"
    logger = setup_logging(log_path)

    logger.info("Step 1: Load inputs from %s", input_dir)
    loaded = load_inputs(input_dir)
    monthly = loaded["monthly"]
    branch = loaded["branch"]
    carry_forward = loaded["carry_forward"]
    extra_exceptions = loaded["tat_exceptions_file"]

    report_as_of = reporting_date or infer_reporting_date(monthly)
    due_year, due_month = next_month(report_as_of)
    due_date = fifth_business_day(due_year, due_month)
    logger.info("Reporting date %s | branch pack due by %s", report_as_of, due_date)

    logger.info("Step 2: Validate inputs")
    validation = validate_inputs(monthly, branch, carry_forward, settings)
    for warning in validation.warnings:
        logger.warning(warning)
    validation.raise_if_failed()
    logger.info(
        "Monthly rows=%s amount_total=%.2f",
        validation.monthly_count,
        validation.monthly_amount_total,
    )

    logger.info("Step 3: Classify account type (Basic / Pointing)")
    classified = classify_account_type(monthly, settings)
    out_of_scope = int((~classified["in_scope"]).sum())
    if out_of_scope:
        logger.warning("Skipping %s rows whose account code is not in the master", out_of_scope)
    classified = classified.loc[classified["in_scope"]].copy()

    logger.info("Step 4: Link reversals to original credits")
    matched = reversal_matcher(classified, carry_forward, settings)
    logger.info(
        "Open items=%s reversals=%s matches=%s unmatched_reversals=%s",
        len(matched["open_items"]),
        len(matched["reversals"]),
        len(matched["matches"]),
        len(matched["unmatched_reversals"]),
    )

    logger.info("Step 5: Calculate residuals and ageing")
    aged = ageing_calculator(
        matched["open_items"], matched["matches"], report_as_of, settings
    )

    logger.info("Step 6: Carry-forward already merged into open items")

    logger.info("Step 7: Apply 7-day TAT rule")
    reconciled = tat_checker(aged, report_as_of, settings, extra_exceptions)

    logger.info("Step 8: Generate report and next-cycle carry-forward")
    counts = processing_counts(reconciled)
    input_files = [
        str(loaded["monthly_path"]),
        str(loaded["branch_path"]),
    ]
    if loaded["carry_forward_path"] is not None:
        input_files.append(str(loaded["carry_forward_path"]))

    report_path = output_dir / f"office_account_reconciliation_{report_as_of.isoformat()}.xlsx"
    report_generator(
        reconciled=reconciled,
        branch=branch,
        unmatched_reversals=matched["unmatched_reversals"],
        counts=counts,
        output_path=report_path,
        reporting_date=report_as_of,
        input_files=input_files,
        fifth_business_day=due_date,
    )
    next_ledger = build_carry_forward(reconciled)
    persist_carry_forward(next_ledger, output_dir)

    logger.info("Step 9: Processing summary %s", counts)
    logger.info("Report written to %s", report_path)
    logger.info("Carry-forward rows written: %s", len(next_ledger))

    return RunResult(
        reconciled=reconciled,
        carry_forward=next_ledger,
        unmatched_reversals=matched["unmatched_reversals"],
        counts=counts,
        report_path=report_path,
        log_path=log_path,
        reporting_date=report_as_of,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Office Account Reconciliation (Basic / Pointing)"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ROOT / "data" / "input",
        help="Folder where PAD drops the monthly sheet, branch master, and ledger",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "output",
        help="Folder for the month-end workbook, carry-forward, and log",
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=ROOT / "config" / "settings.yaml",
    )
    parser.add_argument(
        "--reporting-date",
        type=str,
        default="",
        help="YYYY-MM-DD. Defaults to month-end of the latest transaction date.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    reporting_date = (
        date.fromisoformat(args.reporting_date) if args.reporting_date else None
    )
    result = run_reconciliation(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        settings_path=args.settings,
        reporting_date=reporting_date,
    )
    logging.getLogger("office_recon").info(
        "Finished. %s full / %s part / %s pending / %s overdue",
        result.counts["Full Reversals"],
        result.counts["Part Reversals"],
        result.counts["Pending"],
        result.counts["Overdue"],
    )
    return 0
