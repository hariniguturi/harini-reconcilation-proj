"""Load YAML settings and expose typed helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = ROOT / "config" / "settings.yaml"


@dataclass(frozen=True)
class OfficeAccount:
    code: str
    name: str
    type: str  # BASIC | POINTING


@dataclass(frozen=True)
class TatException:
    reference_no: str
    reason: str
    expiry_date: date | None


@dataclass(frozen=True)
class Settings:
    tat_days: int
    amount_tolerance: Decimal
    due_by_business_day: int
    credit_txn_types: frozenset[str]
    reversal_txn_types: frozenset[str]
    require_original_credit_ref_for_pointing: bool
    office_accounts: dict[str, OfficeAccount]
    tat_exceptions: dict[str, TatException]
    raw: dict[str, Any]

    def account_type(self, account_code: str) -> str | None:
        account = self.office_accounts.get(str(account_code).strip().upper())
        return account.type if account else None

    def is_approved_account(self, account_code: str) -> bool:
        return str(account_code).strip().upper() in self.office_accounts

    def exception_for(self, reference_no: str, as_of: date) -> TatException | None:
        item = self.tat_exceptions.get(str(reference_no).strip())
        if item is None:
            return None
        if item.expiry_date is not None and as_of > item.expiry_date:
            return None
        return item


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def load_settings(path: Path | None = None) -> Settings:
    settings_path = path or DEFAULT_SETTINGS_PATH
    with open(settings_path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    accounts = {}
    for row in raw.get("office_accounts", []):
        code = str(row["code"]).strip().upper()
        accounts[code] = OfficeAccount(
            code=code,
            name=str(row.get("name", code)),
            type=str(row.get("type", "BASIC")).strip().upper(),
        )

    exceptions = {}
    for row in raw.get("tat_exceptions", []):
        ref = str(row["reference_no"]).strip()
        exceptions[ref] = TatException(
            reference_no=ref,
            reason=str(row.get("reason", "Documented exception")),
            expiry_date=_parse_date(row.get("expiry_date")),
        )

    return Settings(
        tat_days=int(raw.get("tat_days", 7)),
        amount_tolerance=Decimal(str(raw.get("amount_tolerance", "0.01"))),
        due_by_business_day=int(raw.get("due_by_business_day", 5)),
        credit_txn_types=frozenset(
            t.strip().upper() for t in raw.get("credit_txn_types", ["CREDIT"])
        ),
        reversal_txn_types=frozenset(
            t.strip().upper() for t in raw.get("reversal_txn_types", ["REVERSAL"])
        ),
        require_original_credit_ref_for_pointing=bool(
            raw.get("require_original_credit_ref_for_pointing", True)
        ),
        office_accounts=accounts,
        tat_exceptions=exceptions,
        raw=raw,
    )
