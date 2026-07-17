from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from semigraph.financial.metrics import ALIAS_TO_METRIC, local_concept_name
from semigraph.financial.models import CanonicalFact


STATEMENTS = {
    "ic": "income",
    "bs": "balance",
    "cf": "cash_flow",
}


def _accepted_sort_key(report: dict) -> tuple[str, str]:
    return (
        str(report.get("acceptedDate") or ""),
        str(report.get("filedDate") or ""),
    )


def select_latest_reports(
    reports: list[dict],
    *,
    limit: int,
) -> list[dict]:
    latest_by_period: dict[str, dict] = {}
    for report in reports:
        period_end = str(report.get("endDate") or "")
        if not period_end:
            continue
        current = latest_by_period.get(period_end)
        if current is None or _accepted_sort_key(report) > _accepted_sort_key(current):
            latest_by_period[period_end] = report

    return sorted(
        latest_by_period.values(),
        key=lambda row: str(row["endDate"]),
        reverse=True,
    )[:limit]


def normalize_report(
    *,
    ticker: str,
    frequency: str,
    report: dict,
) -> list[CanonicalFact]:
    candidates: dict[str, CanonicalFact] = {}
    report_body = report.get("report") or {}

    for source_key, statement_type in STATEMENTS.items():
        rows = report_body.get(source_key) or []
        for row_index, row in enumerate(rows):
            source_concept = str(row.get("concept") or "")
            local_name = local_concept_name(source_concept)
            definition = ALIAS_TO_METRIC.get(local_name)
            if definition is None or definition.statement != statement_type:
                continue

            try:
                value = Decimal(str(row["value"]))
            except (KeyError, InvalidOperation, TypeError):
                continue

            fact = CanonicalFact(
                ticker=ticker,
                frequency=frequency,
                fiscal_year=int(report["year"]),
                fiscal_quarter=(
                    int(report["quarter"])
                    if frequency == "quarterly" and report.get("quarter")
                    else None
                ),
                period_start=report.get("startDate"),
                period_end=report["endDate"],
                accepted_at=report.get("acceptedDate"),
                filed_date=report.get("filedDate"),
                accession=report.get("accessNumber"),
                form=report.get("form"),
                statement_type=statement_type,
                canonical_metric=definition.name,
                source_concept=source_concept,
                source_label=row.get("label"),
                source_row_index=row_index,
                value=abs(value) if definition.cash_outflow else value,
                unit=str(row.get("unit") or definition.unit),
            )

            existing = candidates.get(definition.name)
            if existing is None:
                candidates[definition.name] = fact
                continue

            alias_order = definition.aliases
            existing_alias = local_concept_name(existing.source_concept)
            if alias_order.index(local_name) < alias_order.index(existing_alias):
                candidates[definition.name] = fact

    return list(candidates.values())