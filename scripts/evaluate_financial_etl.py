"""Evaluate Finnhub ETL against the original SEC 10-K XBRL filings.

The evaluator is isolated from production normalization code. It reads
PostgreSQL in read-only mode, verifies raw staging/provenance, downloads each
10-K XBRL package from SEC EDGAR, and writes CSV/JSON evidence.

Foreign issuers with no U.S. 10-K are reported as skipped and excluded from
the accuracy denominator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from lxml import etree

from semigraph.financial.db import financial_connection


DEFAULT_TICKERS = (
    "NVDA", "AVGO", "MU", "AMAT", "KLAC", "MRVL", "LRCX", "AMD",
    "TXN", "INTC", "ADI", "QCOM", "NXPI", "ALAB", "MPWR", "COHR",
    "TER", "CRDO", "MCHP", "ARM", "ON", "GFS", "MTSI", "ENTG",
    "NVMI", "RMBS", "SWKS", "QRVO",
)

CORE_METRICS = (
    "revenue",
    "net_income",
    "total_assets",
    "current_assets",
    "operating_cash_flow",
)

# Independent mapping: importing production METRICS here would let the
# evaluator repeat the same mapping error as the system under test.
SEC_CONCEPTS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
    ),
    "net_income": ("NetIncomeLoss", "ProfitLoss"),
    "total_assets": ("Assets",),
    "current_assets": ("AssetsCurrent",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
}

DURATION_METRICS = {"revenue", "net_income", "operating_cash_flow"}
SEC_ARCHIVE_ROOT = "https://www.sec.gov/Archives/edgar/data"
DEFAULT_USER_AGENT = "Mozilla/5.0 semigraph-research semigraph.research@example.com"

NS = {
    "ix": "http://www.xbrl.org/2013/inlineXBRL",
    "xbrli": "http://www.xbrl.org/2003/instance",
}
XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="Latest 28-target run by default")
    parser.add_argument("--years", type=int, default=3, help="Latest 10-Ks per company")
    parser.add_argument("--ticker", action="append", dest="tickers")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark/results/financial_etl"),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/tmp/semigraph_sec_archive_cache"),
    )
    parser.add_argument("--sec-delay", type=float, default=0.15)
    parser.add_argument("--sec-user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args()


def canonical_json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _with_source_query(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "source=semigraph", ""))


def fetch_sec_bytes(
    url: str,
    cache_dir: Path,
    user_agent: str,
    delay: float,
) -> bytes:
    cache_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(urlsplit(url).path).suffix or ".bin"
    cache_path = cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}{suffix}"
    if cache_path.exists():
        return cache_path.read_bytes()

    command = [
        "curl",
        "--fail",
        "--silent",
        "--show-error",
        "--compressed",
        "--retry",
        "4",
        "--header",
        f"User-Agent: {user_agent}",
        "--header",
        "Accept: application/json,text/plain,*/*",
        "--header",
        "Accept-Encoding: gzip, deflate",
        "--header",
        f"Host: {urlsplit(url).netloc}",
        "--header",
        "Referer: https://www.sec.gov/",
        _with_source_query(url),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            timeout=90,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"SEC request failed: {url}") from exc

    cache_path.write_bytes(completed.stdout)
    if delay:
        time.sleep(delay)
    return completed.stdout


def fetch_sec_json(url: str, **kwargs: Any) -> dict[str, Any]:
    return json.loads(fetch_sec_bytes(url, **kwargs).decode("utf-8"))


def latest_run_id(conn: Any, target_count: int) -> str:
    row = conn.execute(
        """
        SELECT run_id::text AS run_id
        FROM financial.ingestion_runs
        WHERE (stats ->> 'target_company_count')::integer = %s
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (target_count,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No ingestion run with {target_count} targets")
    return str(row["run_id"])


def load_internal_audit(
    conn: Any,
    run_id: str,
    tickers: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    run = conn.execute(
        """
        SELECT status, expected_company_count, successful_tickers,
               failed_tickers, stats
        FROM financial.ingestion_runs
        WHERE run_id = %s
        """,
        (run_id,),
    ).fetchone()
    if run is None:
        raise RuntimeError(f"Unknown run_id: {run_id}")

    payloads = conn.execute(
        """
        SELECT rp.raw_payload_id, rp.ticker, rp.endpoint, rp.frequency,
               rp.payload_sha256, rp.payload
        FROM financial.ingestion_run_payloads irp
        JOIN financial.raw_payloads rp USING (raw_payload_id)
        WHERE irp.run_id = %s
        ORDER BY rp.ticker, rp.endpoint, rp.frequency
        """,
        (run_id,),
    ).fetchall()

    payload_rows: list[dict[str, Any]] = []
    annual_payloads: dict[str, dict[str, Any]] = {}
    dimensions: Counter[tuple[str, str, str]] = Counter()
    for row in payloads:
        calculated = canonical_json_hash(row["payload"])
        stored = str(row["payload_sha256"]).strip()
        dimensions[(row["ticker"], row["endpoint"], row["frequency"])] += 1
        payload_rows.append(
            {
                "raw_payload_id": row["raw_payload_id"],
                "ticker": row["ticker"],
                "endpoint": row["endpoint"],
                "frequency": row["frequency"],
                "stored_sha256": stored,
                "calculated_sha256": calculated,
                "hash_reproducible_from_jsonb": stored == calculated,
            }
        )
        if row["endpoint"] == "financials_reported" and row["frequency"] == "annual":
            annual_payloads[row["ticker"]] = row["payload"]

    expected_dimensions = {
        (ticker, endpoint, frequency)
        for ticker in tickers
        for endpoint, frequency in (
            ("financials_reported", "annual"),
            ("financials_reported", "quarterly"),
            ("basic_financials", "none"),
            ("quote", "none"),
        )
    }
    observed_dimensions = set(dimensions)

    company_count = conn.execute(
        "SELECT count(*) AS n FROM financial.companies WHERE ticker = ANY(%s)",
        (tickers,),
    ).fetchone()["n"]
    provenance = conn.execute(
        """
        SELECT count(*) AS total,
               count(*) FILTER (
                   WHERE f.ticker = rp.ticker
                     AND rp.endpoint = 'financials_reported'
                     AND f.frequency = rp.frequency
               ) AS valid
        FROM financial.financial_facts f
        JOIN financial.raw_payloads rp USING (raw_payload_id)
        JOIN financial.ingestion_run_payloads irp USING (raw_payload_id)
        WHERE irp.run_id = %s
        """,
        (run_id,),
    ).fetchone()
    duplicate_groups = conn.execute(
        """
        SELECT count(*) AS n
        FROM (
            SELECT ticker, frequency, period_end, canonical_metric
            FROM financial.financial_facts
            WHERE ticker = ANY(%s)
            GROUP BY ticker, frequency, period_end, canonical_metric
            HAVING count(*) > 1
        ) duplicates
        """,
        (tickers,),
    ).fetchone()["n"]

    summary = {
        "run_id": run_id,
        "run_status": run["status"],
        "run_expected_company_count": run["expected_company_count"],
        "target_company_count": len(tickers),
        "successful_company_count": len(run["successful_tickers"]),
        "failed_company_count": len(run["failed_tickers"]),
        "company_rows_present": int(company_count),
        "payload_count": len(payload_rows),
        "expected_payload_count": len(tickers) * 4,
        "payload_hash_reproducible_from_jsonb": sum(
            row["hash_reproducible_from_jsonb"] for row in payload_rows
        ),
        "payload_hash_note": (
            "JSONB can normalize numeric lexical forms; a non-reproducible hash "
            "does not by itself mean the semantic payload changed."
        ),
        "missing_endpoint_dimensions": [
            list(item) for item in sorted(expected_dimensions - observed_dimensions)
        ],
        "duplicate_endpoint_dimensions": [
            list(item) for item, count in sorted(dimensions.items()) if count > 1
        ],
        "provenance_fact_count": int(provenance["total"]),
        "valid_provenance_fact_count": int(provenance["valid"]),
        "duplicate_canonical_business_key_groups": int(duplicate_groups),
    }
    return summary, payload_rows, annual_payloads


def load_db_facts(conn: Any, tickers: list[str]) -> list[dict[str, Any]]:
    return conn.execute(
        """
        SELECT fact_id, ticker, fiscal_year, period_start, period_end,
               accession, form, canonical_metric, source_concept, value, unit
        FROM financial.financial_facts
        WHERE frequency = 'annual'
          AND ticker = ANY(%s)
          AND canonical_metric = ANY(%s)
        ORDER BY ticker, period_end DESC, canonical_metric, fact_id DESC
        """,
        (tickers, list(CORE_METRICS)),
    ).fetchall()


def latest_raw_10k_filings(payload: dict[str, Any], limit: int) -> list[dict[str, str]]:
    latest_by_period: dict[str, dict[str, str]] = {}
    for report in payload.get("data", []):
        if report.get("form") != "10-K" or not report.get("accessNumber"):
            continue
        period_end = str(report.get("endDate") or "")[:10]
        if not period_end:
            continue
        candidate = {
            "accession": str(report["accessNumber"]),
            "filing_date": str(report.get("filedDate") or "")[:10],
            "period_end_from_finnhub": period_end,
            "fiscal_year_from_finnhub": str(report.get("year") or ""),
            "accepted_at": str(report.get("acceptedDate") or ""),
        }
        current = latest_by_period.get(period_end)
        if current is None or candidate["accepted_at"] > current["accepted_at"]:
            latest_by_period[period_end] = candidate
    return sorted(
        latest_by_period.values(),
        key=lambda row: row["period_end_from_finnhub"],
        reverse=True,
    )[:limit]


def filing_archive_urls(cik: int, accession: str) -> tuple[str, str]:
    directory = f"{SEC_ARCHIVE_ROOT}/{cik}/{accession.replace('-', '')}"
    return directory, f"{directory}/index.json"


def download_xbrl_package(
    cik: int,
    accession: str,
    cache_dir: Path,
    user_agent: str,
    delay: float,
) -> bytes:
    directory, index_url = filing_archive_urls(cik, accession)
    index = fetch_sec_json(
        index_url,
        cache_dir=cache_dir,
        user_agent=user_agent,
        delay=delay,
    )
    names = [item["name"] for item in index["directory"]["item"]]
    zip_names = [name for name in names if name.endswith("-xbrl.zip")]
    if not zip_names:
        raise RuntimeError(f"No XBRL ZIP in SEC filing {accession}")
    return fetch_sec_bytes(
        f"{directory}/{zip_names[0]}",
        cache_dir=cache_dir,
        user_agent=user_agent,
        delay=delay,
    )


def _local_concept(name: str | None) -> str:
    value = str(name or "")
    return value.rsplit(":", 1)[-1].removeprefix("us-gaap_")


def _text(element: Any) -> str:
    return "".join(element.itertext()).strip()


def _numeric_value(element: Any) -> Decimal | None:
    if str(element.get(XSI_NIL, "")).lower() == "true":
        return None
    raw = _text(element).replace(",", "").replace("$", "").strip()
    if raw in {"", "-", "—", "–"}:
        return None
    negative_parentheses = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()")
    try:
        value = Decimal(raw)
        scale = int(element.get("scale") or 0)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if negative_parentheses or element.get("sign") == "-":
        value = -abs(value)
    return value * (Decimal(10) ** scale)


def _context_catalog(root: Any) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for context in root.xpath("//xbrli:context", namespaces=NS):
        context_id = context.get("id")
        if not context_id:
            continue
        start = context.xpath("string(.//xbrli:startDate)", namespaces=NS) or None
        end = context.xpath("string(.//xbrli:endDate)", namespaces=NS) or None
        instant = context.xpath("string(.//xbrli:instant)", namespaces=NS) or None
        dimensions = bool(context.xpath(".//xbrli:segment/*", namespaces=NS))
        contexts[context_id] = {
            "start": start,
            "end": end or instant,
            "instant": instant,
            "dimensions": dimensions,
        }
    return contexts


def _unit_catalog(root: Any) -> dict[str, str]:
    units: dict[str, str] = {}
    for unit in root.xpath("//xbrli:unit", namespaces=NS):
        unit_id = unit.get("id")
        measure = unit.xpath("string(.//xbrli:measure)", namespaces=NS)
        if unit_id:
            units[unit_id] = measure.rsplit(":", 1)[-1] if measure else unit_id
    return units


def _dei_value(root: Any, concept: str) -> str | None:
    nodes = root.xpath(
        "//ix:nonNumeric[@name=$name]",
        namespaces=NS,
        name=f"dei:{concept}",
    )
    return _text(nodes[0]) if nodes else None


def _dei_period_end(root: Any, contexts: dict[str, dict[str, Any]]) -> str | None:
    nodes = root.xpath(
        "//ix:nonNumeric[@name='dei:DocumentPeriodEndDate']",
        namespaces=NS,
    )
    if not nodes:
        return None
    context = contexts.get(nodes[0].get("contextRef"), {})
    return context.get("end") or _text(nodes[0])


def parse_inline_xbrl(package: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        html_names = [name for name in archive.namelist() if name.lower().endswith(".htm")]
        if not html_names:
            raise RuntimeError("XBRL ZIP has no inline HTML document")
        primary = max(html_names, key=lambda name: archive.getinfo(name).file_size)
        html = archive.read(primary)

    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(html, parser=parser)
    contexts = _context_catalog(root)
    units = _unit_catalog(root)
    facts: list[dict[str, Any]] = []
    for element in root.xpath("//ix:nonFraction", namespaces=NS):
        value = _numeric_value(element)
        context = contexts.get(element.get("contextRef"))
        if value is None or context is None:
            continue
        facts.append(
            {
                "concept": _local_concept(element.get("name")),
                "value": value,
                "unit": units.get(element.get("unitRef"), element.get("unitRef") or ""),
                "context_id": element.get("contextRef"),
                **context,
            }
        )
    return {
        "document_type": _dei_value(root, "DocumentType"),
        "fiscal_year": _dei_value(root, "DocumentFiscalYearFocus"),
        "period_end": _dei_period_end(root, contexts),
        "facts": facts,
    }


def _duration_days(fact: dict[str, Any]) -> int:
    try:
        return (date.fromisoformat(fact["end"]) - date.fromisoformat(fact["start"])).days
    except (TypeError, ValueError):
        return -1


def find_gold_fact(document: dict[str, Any], metric: str) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for priority, concept in enumerate(SEC_CONCEPTS[metric]):
        for fact in document["facts"]:
            if fact["concept"] != concept or fact["end"] != document["period_end"]:
                continue
            duration = _duration_days(fact)
            if metric in DURATION_METRICS and not 300 <= duration <= 400:
                continue
            if metric not in DURATION_METRICS and fact["instant"] is None:
                continue
            candidates.append({**fact, "priority": priority, "duration_days": duration})
    if not candidates:
        return None
    if metric == "revenue":
        # Some 10-Ks expose both total revenue and a smaller revenue concept
        # (for example, one revenue stream). Among consolidated annual facts,
        # the largest allowed top-line concept is the total revenue oracle.
        candidates.sort(
            key=lambda fact: (
                fact["dimensions"],
                fact["unit"].upper() != "USD",
                -abs(fact["value"]),
                fact["priority"],
            )
        )
    else:
        candidates.sort(
            key=lambda fact: (
                fact["priority"],
                fact["dimensions"],
                fact["unit"].upper() != "USD",
                abs(365 - fact["duration_days"]) if metric in DURATION_METRICS else 0,
            )
        )
    return candidates[0]


def normalized_unit(unit: str | None) -> str:
    value = str(unit or "").strip().lower().replace("-", "_")
    return "USD" if value in {"usd", "u_usd", "unit_usd"} else value.upper()


def to_decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def compare_filing(
    ticker: str,
    cik: int,
    filing: dict[str, str],
    document: dict[str, Any],
    db_index: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sec_period_end = str(document.get("period_end") or "")[:10]
    sec_fiscal_year = str(document.get("fiscal_year") or "")
    for metric in CORE_METRICS:
        gold = find_gold_fact(document, metric)
        candidates = db_index.get((ticker, metric, sec_period_end), [])
        exact_accession = [row for row in candidates if row.get("accession") == filing["accession"]]
        db_fact = (exact_accession or candidates or [None])[0]

        gold_value = gold["value"] if gold else None
        db_value = to_decimal(db_fact["value"]) if db_fact else None
        gold_available = gold is not None
        db_present = db_fact is not None
        value_match = gold_available and db_present and gold_value == db_value
        unit_match = (
            gold_available
            and db_present
            and normalized_unit(gold["unit"]) == normalized_unit(db_fact["unit"])
        )
        concept_match = (
            db_present
            and _local_concept(db_fact["source_concept"]) in SEC_CONCEPTS[metric]
        )
        fiscal_year_match = (
            db_present and sec_fiscal_year == str(db_fact["fiscal_year"])
        )
        accession_match = (
            db_present and filing["accession"] == db_fact.get("accession")
        )

        if not gold_available:
            status = "GOLD_UNAVAILABLE"
        elif not db_present:
            status = "MISSING_IN_DB"
        elif not concept_match:
            status = "CONCEPT_MISMATCH"
        elif not unit_match:
            status = "UNIT_MISMATCH"
        elif not fiscal_year_match:
            status = "FISCAL_YEAR_MISMATCH"
        elif not accession_match:
            status = "ACCESSION_MISMATCH"
        elif not value_match:
            status = "VALUE_MISMATCH"
        else:
            status = "PASS"

        relative_error = ""
        if gold_value is not None and db_value is not None:
            denominator = max(abs(gold_value), Decimal(1))
            relative_error = str(abs(db_value - gold_value) / denominator)

        rows.append(
            {
                "ticker": ticker,
                "cik": f"{cik:010d}",
                "metric": metric,
                "status": status,
                "sec_form": document.get("document_type") or "",
                "sec_accession": filing["accession"],
                "sec_filing_date": filing["filing_date"],
                "sec_period_end": sec_period_end,
                "sec_fiscal_year": sec_fiscal_year,
                "sec_concept": gold["concept"] if gold else "",
                "sec_value": str(gold_value) if gold_value is not None else "",
                "sec_unit": gold["unit"] if gold else "",
                "finnhub_period_end": filing["period_end_from_finnhub"],
                "finnhub_fiscal_year": filing["fiscal_year_from_finnhub"],
                "db_fact_id": db_fact["fact_id"] if db_fact else "",
                "db_fiscal_year": db_fact["fiscal_year"] if db_fact else "",
                "db_accession": db_fact.get("accession") if db_fact else "",
                "db_source_concept": db_fact["source_concept"] if db_fact else "",
                "db_value": str(db_value) if db_value is not None else "",
                "db_unit": db_fact["unit"] if db_fact else "",
                "db_candidate_count": len(candidates),
                "value_match": bool(value_match),
                "unit_match": bool(unit_match),
                "concept_match": bool(concept_match),
                "fiscal_year_match": bool(fiscal_year_match),
                "accession_match": bool(accession_match),
                "period_match": sec_period_end == filing["period_end_from_finnhub"],
                "relative_error": relative_error,
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]], requested: int) -> dict[str, Any]:
    counts = Counter(row["status"] for row in rows)
    comparable = [row for row in rows if row["status"] != "GOLD_UNAVAILABLE"]
    present = [row for row in comparable if row["db_fact_id"] != ""]
    passes = [row for row in comparable if row["status"] == "PASS"]

    def ratio(n: int, d: int) -> float | None:
        return round(n / d, 6) if d else None

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["ticker"]].append(row)
    per_ticker: dict[str, Any] = {}
    for ticker, ticker_rows in sorted(grouped.items()):
        ticker_comparable = [r for r in ticker_rows if r["status"] != "GOLD_UNAVAILABLE"]
        ticker_passes = [r for r in ticker_comparable if r["status"] == "PASS"]
        per_ticker[ticker] = {
            "comparable_cells": len(ticker_comparable),
            "pass_count": len(ticker_passes),
            "full_record_accuracy": ratio(len(ticker_passes), len(ticker_comparable)),
            "status_counts": dict(Counter(r["status"] for r in ticker_rows)),
        }

    return {
        "requested_company_count": requested,
        "evaluated_company_count": len(grouped),
        "expected_cells": len(rows),
        "comparable_cells": len(comparable),
        "gold_unavailable_cells": counts["GOLD_UNAVAILABLE"],
        "db_present_cells": len(present),
        "pass_count": len(passes),
        "completeness": ratio(len(present), len(comparable)),
        "full_record_accuracy": ratio(len(passes), len(comparable)),
        "value_accuracy_when_present": ratio(
            sum(bool(row["value_match"]) for row in present), len(present)
        ),
        "unit_accuracy_when_present": ratio(
            sum(bool(row["unit_match"]) for row in present), len(present)
        ),
        "period_accuracy_when_present": ratio(
            sum(bool(row["period_match"]) for row in present), len(present)
        ),
        "status_counts": dict(counts),
        "per_ticker": per_ticker,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    if args.years <= 0 or args.sec_delay < 0:
        raise SystemExit("--years must be positive and --sec-delay non-negative")
    tickers = sorted({str(t).strip().upper() for t in (args.tickers or DEFAULT_TICKERS)})

    with financial_connection(readonly=True) as conn:
        run_id = args.run_id or latest_run_id(conn, len(tickers))
        internal, payload_rows, annual_payloads = load_internal_audit(
            conn,
            run_id=run_id,
            tickers=tickers,
        )
        db_facts = load_db_facts(conn, tickers)

    db_index: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in db_facts:
        key = (row["ticker"], row["canonical_metric"], str(row["period_end"]))
        db_index[key].append(row)

    comparison_rows: list[dict[str, Any]] = []
    skipped_no_10k: list[str] = []
    filing_errors: list[dict[str, str]] = []
    for index, ticker in enumerate(tickers, start=1):
        payload = annual_payloads.get(ticker, {})
        filings = latest_raw_10k_filings(payload, args.years)
        if not filings:
            skipped_no_10k.append(ticker)
            print(f"[{index:02d}/{len(tickers)}] {ticker}: skipped (no 10-K)")
            continue
        cik = int(payload["cik"])
        print(f"[{index:02d}/{len(tickers)}] {ticker}: evaluating {len(filings)} 10-Ks")
        for filing in filings:
            try:
                package = download_xbrl_package(
                    cik=cik,
                    accession=filing["accession"],
                    cache_dir=args.cache_dir,
                    user_agent=args.sec_user_agent,
                    delay=args.sec_delay,
                )
                document = parse_inline_xbrl(package)
                if document["document_type"] != "10-K":
                    raise RuntimeError(f"SEC document type is {document['document_type']!r}")
                comparison_rows.extend(
                    compare_filing(
                        ticker=ticker,
                        cik=cik,
                        filing=filing,
                        document=document,
                        db_index=db_index,
                    )
                )
            except Exception as exc:  # continue the audit and report the filing failure
                filing_errors.append(
                    {
                        "ticker": ticker,
                        "accession": filing["accession"],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    external = summarize(comparison_rows, len(tickers))
    external["skipped_no_10k_tickers"] = skipped_no_10k
    external["filing_errors"] = filing_errors

    output_dir = args.output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "raw_payload_integrity.csv", payload_rows)
    write_csv(output_dir / "sec_10k_fact_comparison.csv", comparison_rows)
    write_csv(output_dir / "sec_filing_errors.csv", filing_errors)

    summary = {
        "scope": {
            "tickers": tickers,
            "metrics": list(CORE_METRICS),
            "ten_k_filings_per_company": args.years,
            "filing_form": "10-K only; 20-F issuers excluded",
            "gold_source": "SEC EDGAR original inline XBRL archive",
            "filing_selection_source": "Finnhub annual raw payload",
        },
        "internal_integrity": internal,
        "sec_reconciliation": external,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Results written to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
