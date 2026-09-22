# Office Account Reconciliation

Python pipeline for monthly **Basic / Pointing (OAP)** office-account reconciliation, following the *Office Account Reconciliation Solution Design* (v1.0, 18 September 2026).

Power Automate Desktop only downloads the SharePoint Excel files. Everything after that — validate, classify, link reversals, residuals, ageing, TAT, carry-forward, and the branch workbook — runs here.

## What it does

1. Reads the monthly sheet, branch master, and prior-cycle carry-forward ledger (does not change the originals).
2. Validates required columns, dates, amounts, and duplicate credit references.
3. Tags each row **BASIC** or **POINTING** from the sheet, falling back to `config/settings.yaml`.
4. Links reversals to original credits on **Original Credit Ref. = Reference No.** (one-to-many supported).
5. Calculates residual balance and ageing from the original / carry-forward start date.
6. Merges unresolved prior-cycle items so the ageing clock does not reset.
7. Flags **OVERDUE** when pending / part-reversal items exceed 7 days, unless a documented exception exists.
8. Writes the month-end branch workbook and the next-cycle ledger (CSV, Excel, SQLite).
9. Logs counts and exceptions.

## Run it

```powershell
python -m pip install -r requirements.txt
python scripts/create_sample_data.py
python run_reconciliation.py --input-dir data/input --output-dir data/output --reporting-date 2026-08-31
python -m pytest -q
```

PAD should drop files into `data/input` with these names:

| File | Purpose |
|------|---------|
| `monthly_office_account_sheet.xlsx` | Monthly transactions for the nine office accounts |
| `branch_master.xlsx` | Branch code, name, email, region |
| `carry_forward_ledger.xlsx` | Prior-cycle pending / part-reversal balances (optional on first run) |

Outputs land in `data/output`:

- `office_account_reconciliation_YYYY-MM-DD.xlsx` — Reconciliation_Summary, Pending_PartReversal, Overdue_Entries, Processing_Summary
- `carry_forward_ledger.xlsx` / `.csv` / `carry_forward.db` — next month’s opening ledger
- `reconciliation.log`

## Assumed defaults (Section 9 is still open)

The design lists these as pending Finance / Branch Operations decisions. The code is config-driven so they can change without a rewrite:

| Decision | Default used now |
|----------|------------------|
| Nine office account codes | `OA1001`–`OA1009` in `config/settings.yaml` |
| Basic vs Pointing rule | Sheet `Account Type`, else the master `type` |
| Match hierarchy | Reversal `Original Credit Ref.` → credit `Reference No.` |
| Amount tolerance | `0.01` |
| TAT | 7 calendar days |
| Ageing basis | Original credit date / persisted ageing start date → reporting date |
| Part-reversal residual | credit (or brought-forward) amount − sum of linked reversals |
| TAT exceptions | `tat_exceptions` in settings, or `data/input/tat_exceptions.xlsx` |

Replace the placeholder account codes and exception list before a production run.

## Project layout

```
config/settings.yaml          business rules
src/office_recon/             pipeline modules named in the design
scripts/create_sample_data.py sample SharePoint-style inputs
tests/                        classification, matching, ageing, TAT, carry-forward
run_reconciliation.py         CLI
```
