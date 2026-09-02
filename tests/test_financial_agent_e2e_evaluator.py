"""Unit tests for Financial Agent E2E scoring helpers."""

from decimal import Decimal

from scripts.evaluate_financial_agent_e2e import (
    numeric_candidates,
    score_abstention,
    score_query_specs,
    write_outputs,
)


CRITICAL_FIELDS = [
    "tickers",
    "metrics",
    "frequency",
    "operation",
    "start_year",
    "end_year",
    "quarter",
    "aggregation",
]


def _trace(spec=None, template="periodic.lookup.filtered.v1", status="ok"):
    return {
        "tool": "financial",
        "status": status,
        "returned_count": 1 if status == "ok" else 0,
        "query_spec": spec or {},
        "parameters": {"template_id": template},
    }


def _expected_spec(**overrides):
    spec = {
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "operation": "lookup",
        "start_year": 2025,
        "end_year": 2025,
        "quarter": None,
        "aggregation": None,
    }
    spec.update(overrides)
    return spec


def test_spec_scoring_uses_later_successful_trace():
    expected = _expected_spec()
    traces = [_trace(status="skipped"), _trace(expected)]

    assert score_query_specs(
        traces,
        expected,
        CRITICAL_FIELDS,
        "periodic.lookup.filtered.v1",
    ) == (True, "exact")


def test_spec_scoring_accepts_decomposed_comparison():
    expected = _expected_spec(
        tickers=["QCOM", "TXN"],
        metrics=["rd_intensity"],
        operation="compare",
        start_year=2024,
        end_year=2024,
    )
    traces = [
        _trace(_expected_spec(
            tickers=["QCOM"],
            metrics=["rd_intensity"],
            start_year=2024,
            end_year=2024,
        )),
        _trace(_expected_spec(
            tickers=["TXN"],
            metrics=["rd_intensity"],
            start_year=2024,
            end_year=2024,
        )),
    ]

    assert score_query_specs(
        traces,
        expected,
        CRITICAL_FIELDS,
        "periodic.compare.filtered.v1",
    ) == (True, "decomposed")


def test_spec_scoring_rejects_metric_substitution():
    expected = _expected_spec(
        tickers=["AMD", "INTC"],
        metrics=["revenue_growth_yoy"],
        operation="compare",
        start_year=2024,
        end_year=2024,
    )
    substituted = _expected_spec(
        tickers=["AMD", "INTC"],
        metrics=["revenue"],
        operation="compare",
        start_year=2023,
        end_year=2024,
    )

    assert score_query_specs(
        [_trace(substituted, template="periodic.compare.filtered.v1")],
        expected,
        CRITICAL_FIELDS,
        "periodic.compare.filtered.v1",
    ) == (False, "")


def test_numeric_candidates_support_sign_before_and_after_currency():
    values = numeric_candidates(
        "FCF was -$6.12B, then $-121M, -2.1%, and −$6.12 B"
    )

    assert values.count(Decimal("-6120000000")) == 2
    assert Decimal("-121000000") in values
    assert Decimal("-0.021") in values


def test_numeric_candidates_understand_negative_direction_words():
    values = numeric_candidates(
        "AMD grew 13.69%, INTC saw a decline of 2.08%, and margin dropped "
        "to 11.43%."
    )

    assert Decimal("0.1369") in values
    assert Decimal("-0.0208") in values
    assert Decimal("0.1143") in values


def test_abstention_allows_numeric_context_when_refusal_is_explicit():
    answer = "The evidence is not sufficient to forecast tomorrow; today is $500."

    assert score_abstention(answer, []) is True


def test_abstention_accepts_missing_period_wording():
    assert score_abstention(
        "The evidence does not contain the requested date, so a comparison "
        "cannot be made.",
        [],
    ) is True
    assert score_abstention(
        "The evidence does not include Q4, so the query cannot be directly "
        "answered.",
        [],
    ) is True


def test_structured_unsupported_accepts_empty_answer_but_not_numeric_claim():
    traces = [{
        "tool": "financial",
        "reason": "unsupported_metric",
    }]

    assert score_abstention("", traces) is True
    assert score_abstention("The answer is 40.7%.", traces) is False


def test_write_outputs_replaces_checkpoint_files_atomically(tmp_path):
    write_outputs(
        tmp_path,
        [{"id": "Q1"}],
        [{"id": "Q1", "state": {}}],
        {"query_count": 1},
    )

    assert (tmp_path / "results.csv").exists()
    assert (tmp_path / "traces.jsonl").exists()
    assert (tmp_path / "summary.json").exists()
    assert list(tmp_path.glob("*.tmp")) == []
