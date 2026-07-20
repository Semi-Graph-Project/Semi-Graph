"""Build the 60-question financial Agent E2E benchmark from PostgreSQL.

Gold rows are read independently from the curated serving view.  The builder
does not call ``financial_search`` or the production SQL compiler, so it does
not copy the Agent's parsed intent or retrieved output into the gold labels.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from semigraph.config import get_config
from semigraph.financial.db import financial_connection


DEFAULT_OUTPUT = Path("benchmark/datasets/financial_agent_e2e_60.yaml")
EXPECTED_CATEGORY_COUNTS = {
    "single_company_lookup": 12,
    "multi_company_comparison": 12,
    "multi_year_trend": 12,
    "derived_metric": 12,
    "unsupported_abstention": 12,
}


def _answerable_cases() -> list[dict[str, Any]]:
    """Hand-authored intents; their numeric labels are populated from DB."""

    return [
        # 1-12: one company, one reported metric, one fiscal year.
        _case("single_company_lookup", "What was NVDA's revenue in FY2025?", ["NVDA"], "revenue", "lookup", 2025, 2025),
        _case("single_company_lookup", "What was AMD's net income in FY2024?", ["AMD"], "net_income", "lookup", 2024, 2024),
        _case("single_company_lookup", "What were AVGO's total assets in FY2024?", ["AVGO"], "total_assets", "lookup", 2024, 2024),
        _case("single_company_lookup", "What was MU's operating cash flow in FY2025?", ["MU"], "operating_cash_flow", "lookup", 2025, 2025),
        _case("single_company_lookup", "What was INTC's research and development expense in FY2024?", ["INTC"], "research_and_development", "lookup", 2024, 2024),
        _case("single_company_lookup", "What was QCOM's diluted EPS in FY2024?", ["QCOM"], "diluted_eps", "lookup", 2024, 2024),
        _case("single_company_lookup", "What were TXN's current assets in FY2025?", ["TXN"], "current_assets", "lookup", 2025, 2025),
        _case("single_company_lookup", "What was AMAT's gross profit in FY2024?", ["AMAT"], "gross_profit", "lookup", 2024, 2024),
        _case("single_company_lookup", "What was KLAC's capital expenditure in FY2025?", ["KLAC"], "capital_expenditure", "lookup", 2025, 2025),
        _case("single_company_lookup", "What was LRCX's stockholders' equity in FY2025?", ["LRCX"], "stockholders_equity", "lookup", 2025, 2025),
        _case("single_company_lookup", "What were AMKR's current liabilities in FY2024?", ["AMKR"], "current_liabilities", "lookup", 2024, 2024),
        _case("single_company_lookup", "What was RMBS's operating income in FY2024?", ["RMBS"], "operating_income", "lookup", 2024, 2024),

        # 13-24: two companies, one comparable metric and fiscal year.
        _case("multi_company_comparison", "Compare NVDA's and AMD's revenue in FY2025.", ["NVDA", "AMD"], "revenue", "compare", 2025, 2025),
        _case("multi_company_comparison", "Compare the FY2025 gross margins of AMAT and LRCX.", ["AMAT", "LRCX"], "gross_margin", "compare", 2025, 2025),
        _case("multi_company_comparison", "Which company had the higher net margin in FY2024, INTC or AMD?", ["INTC", "AMD"], "net_margin", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare MU's and QCOM's operating cash flow in FY2024.", ["MU", "QCOM"], "operating_cash_flow", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare the FY2024 free cash flow of AVGO and TXN.", ["AVGO", "TXN"], "free_cash_flow", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare KLAC's and AMAT's ROA in FY2024.", ["KLAC", "AMAT"], "roa", "compare", 2024, 2024),
        _case("multi_company_comparison", "Which company had the higher current ratio in FY2024, COHR or ENTG?", ["COHR", "ENTG"], "current_ratio", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare the FY2025 ROE of NVDA and AVGO.", ["NVDA", "AVGO"], "roe", "compare", 2025, 2025),
        _case("multi_company_comparison", "Which company had the higher R&D intensity in FY2024, QCOM or TXN?", ["QCOM", "TXN"], "rd_intensity", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare AMD's and INTC's year-over-year revenue growth in FY2024.", ["AMD", "INTC"], "revenue_growth_yoy", "compare", 2024, 2024),
        _case("multi_company_comparison", "Compare the FY2025 net margins of LRCX and KLAC.", ["LRCX", "KLAC"], "net_margin", "compare", 2025, 2025),
        _case("multi_company_comparison", "Compare COHR's and RMBS's year-over-year net income growth in FY2024.", ["COHR", "RMBS"], "net_income_growth_yoy", "compare", 2024, 2024),

        # 25-36: one company, one metric, three ordered fiscal years.
        _case("multi_year_trend", "Show NVDA's annual revenue trend from FY2024 through FY2026.", ["NVDA"], "revenue", "trend", 2024, 2026),
        _case("multi_year_trend", "How did AMD's net income change from FY2023 through FY2025?", ["AMD"], "net_income", "trend", 2023, 2025),
        _case("multi_year_trend", "Show AMAT's gross margin trend from FY2023 through FY2025.", ["AMAT"], "gross_margin", "trend", 2023, 2025),
        _case("multi_year_trend", "How did MU's free cash flow change from FY2023 through FY2025?", ["MU"], "free_cash_flow", "trend", 2023, 2025),
        _case("multi_year_trend", "Show INTC's annual revenue from FY2023 through FY2025.", ["INTC"], "revenue", "trend", 2023, 2025),
        _case("multi_year_trend", "How did AVGO's net margin change from FY2023 through FY2025?", ["AVGO"], "net_margin", "trend", 2023, 2025),
        _case("multi_year_trend", "Show QCOM's operating margin trend from FY2023 through FY2025.", ["QCOM"], "operating_margin", "trend", 2023, 2025),
        _case("multi_year_trend", "How did TXN's research and development expense change from FY2023 through FY2025?", ["TXN"], "research_and_development", "trend", 2023, 2025),
        _case("multi_year_trend", "Show KLAC's current ratio from FY2023 through FY2025.", ["KLAC"], "current_ratio", "trend", 2023, 2025),
        _case("multi_year_trend", "How did LRCX's gross margin change from FY2023 through FY2025?", ["LRCX"], "gross_margin", "trend", 2023, 2025),
        _case("multi_year_trend", "Show ENTG's free cash flow margin from FY2023 through FY2025.", ["ENTG"], "free_cash_flow_margin", "trend", 2023, 2025),
        _case("multi_year_trend", "How did RMBS's revenue change from FY2023 through FY2025?", ["RMBS"], "revenue", "trend", 2023, 2025),

        # 37-48: deterministic metrics calculated by the financial pipeline.
        _case("derived_metric", "What was NVDA's gross margin in FY2025?", ["NVDA"], "gross_margin", "lookup", 2025, 2025),
        _case("derived_metric", "What was AMD's operating margin in FY2024?", ["AMD"], "operating_margin", "lookup", 2024, 2024),
        _case("derived_metric", "What was AVGO's net margin in FY2024?", ["AVGO"], "net_margin", "lookup", 2024, 2024),
        _case("derived_metric", "What was INTC's R&D intensity in FY2024?", ["INTC"], "rd_intensity", "lookup", 2024, 2024),
        _case("derived_metric", "What was MU's free cash flow in FY2025?", ["MU"], "free_cash_flow", "lookup", 2025, 2025),
        _case("derived_metric", "What was AMAT's free cash flow margin in FY2024?", ["AMAT"], "free_cash_flow_margin", "lookup", 2024, 2024),
        _case("derived_metric", "What was TXN's year-over-year revenue growth in FY2025?", ["TXN"], "revenue_growth_yoy", "lookup", 2025, 2025),
        _case("derived_metric", "What was COHR's year-over-year net income growth in FY2025?", ["COHR"], "net_income_growth_yoy", "lookup", 2025, 2025),
        _case("derived_metric", "What was KLAC's current ratio in FY2025?", ["KLAC"], "current_ratio", "lookup", 2025, 2025),
        _case("derived_metric", "What was LRCX's ROA in FY2025?", ["LRCX"], "roa", "lookup", 2025, 2025),
        _case("derived_metric", "What was RMBS's ROE in FY2024?", ["RMBS"], "roe", "lookup", 2024, 2024),
        _case("derived_metric", "What was COHR's fallback-derived gross profit in FY2024?", ["COHR"], "gross_profit", "lookup", 2024, 2024),
    ]


def _unsupported_cases() -> list[dict[str, Any]]:
    definitions = [
        ("Forecast NVDA's revenue for FY2030.", "forecast_not_supported", ["empty_evidence", "query_spec_validation"]),
        ("What was ARM's net margin in FY2025?", "no_financial_data_for_company", ["no_corpus_ticker", "empty_evidence"]),
        ("What was AAPL's revenue in FY2025?", "company_outside_corpus", ["no_corpus_ticker"]),
        ("What was NVDA's dividend yield in FY2025?", "unsupported_metric", ["query_spec_validation"]),
        ("What was NVDA's debt-to-equity ratio in FY2025?", "unsupported_metric", ["query_spec_validation"]),
        ("Which stock should I buy, NVDA or AMD?", "normative_investment_advice", ["insufficient_evidence", "query_spec_validation"]),
        ("What will AMD's stock price be tomorrow?", "future_price_not_supported", ["insufficient_evidence", "empty_evidence"]),
        ("What was ASML's revenue in FY2024?", "company_outside_corpus", ["no_corpus_ticker"]),
        ("What was NVDA's EBITDA in FY2025?", "unsupported_metric", ["query_spec_validation"]),
        ("Compare NVDA's and AMD's P/E ratios as of 2024-12-31.", "historical_snapshot_not_available", ["query_spec_validation", "insufficient_evidence"]),
        ("What was NVDA's gross margin in Q4 FY2025?", "quarterly_derived_metric_not_available", ["empty_evidence"]),
        ("What was the combined FY2025 revenue of every semiconductor company worldwide?", "unbounded_universe", ["no_corpus_ticker", "query_spec_validation"]),
    ]
    return [
        {
            "category": "unsupported_abstention",
            "query": query,
            "expected_tool": "financial",
            "expected_outcome": "abstain",
            "reason_code": reason,
            "gold_spec": None,
            "expected_template_id": None,
            "expected_row_count": 0,
            "gold_rows": [],
            "reference_answer": (
                "The available data or capability is insufficient to answer this question. "
                "The Agent must abstain clearly and must not fabricate a value or recommendation."
            ),
            "acceptable_behavior": {
                "must_indicate_insufficient_or_unsupported": True,
                "must_not_provide_requested_value_or_advice": True,
                "acceptable_trace_signals": signals,
            },
        }
        for query, reason, signals in definitions
    ]


def _case(
    category: str,
    query: str,
    tickers: list[str],
    metric: str,
    operation: str,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    expected_rows = (
        end_year - start_year + 1
        if operation == "trend"
        else len(tickers)
    )
    template_id = (
        "periodic.trend.v1"
        if operation == "trend"
        else f"periodic.{operation}.filtered.v1"
    )
    return {
        "category": category,
        "query": query,
        "expected_tool": "financial",
        "expected_outcome": "answer",
        "gold_spec": {
            "tickers": tickers,
            "metrics": [metric],
            "frequency": "annual",
            "operation": operation,
            "start_year": start_year,
            "end_year": end_year,
            "quarter": None,
            "aggregation": None,
            "sort_order": "desc",
            "limit": 5,
        },
        "expected_template_id": template_id,
        "expected_row_count": expected_rows,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _display_value(metric: str, value: Decimal, unit: str) -> str:
    if unit.lower() == "ratio":
        if metric == "current_ratio":
            return f"{value:.4f}x"
        return f"{value * Decimal('100'):.4f}%"
    return f"{value:f} {unit}"


def _load_gold_rows(conn: Any, case: dict[str, Any]) -> list[dict[str, Any]]:
    spec = case["gold_spec"]
    tickers = spec["tickers"]
    metric = spec["metrics"][0]
    rows = conn.execute(
        """
        SELECT evidence_id, ticker, frequency, fiscal_year, fiscal_quarter,
               period_end, metric, value, unit, source_kind, status, provenance
        FROM financial.agent_periodic_metrics
        WHERE ticker = ANY(%s)
          AND metric = %s
          AND frequency = %s
          AND fiscal_year BETWEEN %s AND %s
          AND status = 'ok'
          AND value IS NOT NULL
        ORDER BY ticker, metric, period_end ASC, evidence_id
        """,
        (
            tickers,
            metric,
            spec["frequency"],
            spec["start_year"],
            spec["end_year"],
        ),
    ).fetchall()
    if len(rows) != case["expected_row_count"]:
        raise RuntimeError(
            f"{case['query']!r}: expected {case['expected_row_count']} gold rows, "
            f"found {len(rows)}"
        )

    result: list[dict[str, Any]] = []
    for row in rows:
        value = Decimal(row["value"])
        result.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "ticker": row["ticker"],
                "frequency": row["frequency"],
                "fiscal_year": row["fiscal_year"],
                "fiscal_quarter": row["fiscal_quarter"],
                "period_end": row["period_end"].isoformat(),
                "metric": row["metric"],
                "value": format(value, "f"),
                "unit": row["unit"],
                "display_value": _display_value(row["metric"], value, row["unit"]),
                "source_kind": row["source_kind"],
                "provenance": _json_safe(row["provenance"]),
            }
        )
    return result


def _reference_answer(rows: list[dict[str, Any]]) -> str:
    return "; ".join(
        f"{row['ticker']} FY{row['fiscal_year']} {row['metric']} = {row['display_value']}"
        for row in rows
    )


def build_dataset() -> dict[str, Any]:
    cfg = get_config()
    answerable = _answerable_cases()
    unsupported = _unsupported_cases()
    cases = answerable + unsupported

    with financial_connection(readonly=True, cfg=cfg) as conn:
        run = conn.execute(
            """
            SELECT run_id::text AS run_id, finished_at
            FROM financial.ingestion_runs
            WHERE status = 'succeeded'
            ORDER BY finished_at DESC NULLS LAST
            LIMIT 1
            """
        ).fetchone()
        for case in answerable:
            case["gold_rows"] = _load_gold_rows(conn, case)
            case["reference_answer"] = _reference_answer(case["gold_rows"])
            case["numeric_tolerance"] = {
                "retrieved_value": "exact_decimal",
                "final_answer_relative": 0.005,
            }

    for index, case in enumerate(cases, start=1):
        case["id"] = f"FIN-E2E-{index:03d}"

    counts = Counter(case["category"] for case in cases)
    if len(cases) != 60 or dict(counts) != EXPECTED_CATEGORY_COUNTS:
        raise RuntimeError(f"invalid benchmark composition: {dict(counts)}")

    return {
        "metadata": {
            "name": "SemiGraph Financial Agent E2E 60",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "question_count": len(cases),
            "category_counts": EXPECTED_CATEGORY_COUNTS,
            "gold_source": "financial.agent_periodic_metrics PostgreSQL view",
            "gold_generation": "independent direct SQL; no financial_search or production SQL compiler",
            "database_reference_run_id": run["run_id"] if run else None,
            "database_reference_finished_at": _json_safe(run["finished_at"]) if run else None,
            "agent_ticker_scope": list(cfg.tickers),
            "critical_spec_fields": [
                "tickers",
                "metrics",
                "frequency",
                "operation",
                "start_year",
                "end_year",
                "quarter",
                "aggregation",
            ],
            "evaluation_levels": [
                "tool_selection",
                "query_spec",
                "sql_execution",
                "retrieved_values",
                "final_answer",
                "abstention",
            ],
            "limitations": [
                "Gold answers are frozen from the current PostgreSQL view and must be regenerated after ETL updates.",
                "Final-answer numeric scoring permits 0.5% relative error for readable rounding; retrieved rows require exact Decimal equality.",
                "Unsupported questions test safe abstention and do not have numeric gold rows.",
            ],
        },
        "queries": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = build_dataset()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(dataset, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    print(f"Wrote {len(dataset['queries'])} questions to {args.output}")


if __name__ == "__main__":
    main()
