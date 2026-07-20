"""Validated intent contract for deterministic financial queries."""

from __future__ import annotations

from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from semigraph.config import get_config


class _StringEnum(str, Enum):
    """Python 3.10-compatible string enum."""

    def __str__(self) -> str:
        return self.value


class Frequency(_StringEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    SNAPSHOT = "snapshot"


class Operation(_StringEnum):
    LOOKUP = "lookup"
    COMPARE = "compare"
    TREND = "trend"
    RANK = "rank"
    AGGREGATE = "aggregate"


class Aggregation(_StringEnum):
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"


class SortOrder(_StringEnum):
    ASC = "asc"
    DESC = "desc"


_METRIC_REGISTRY = get_config().financial_metric_registry
REPORTED_METRICS = _METRIC_REGISTRY["reported"]
DERIVED_METRICS = _METRIC_REGISTRY["derived"]
PERIODIC_METRICS = REPORTED_METRICS | DERIVED_METRICS
SNAPSHOT_METRICS = _METRIC_REGISTRY["snapshot"]


class FinancialQuerySpec(BaseModel):
    """A safe, typed representation of a user's financial query intent."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    tickers: list[str] = Field(min_length=1)
    metrics: list[str] = Field(min_length=1)
    frequency: Frequency
    operation: Operation
    start_year: int | None = Field(default=None, ge=2000, le=2100)
    end_year: int | None = Field(default=None, ge=2000, le=2100)
    quarter: int | None = Field(default=None, ge=1, le=4)
    aggregation: Aggregation | None = None
    sort_order: SortOrder = SortOrder.DESC
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must not be blank")
        return query

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, values: list[str]) -> list[str]:
        tickers = list(
            dict.fromkeys(
                value.strip().upper()
                for value in values
                if value.strip()
            )
        )
        if not tickers:
            raise ValueError("tickers must not be blank")
        return tickers

    @field_validator("metrics")
    @classmethod
    def normalize_metrics(cls, values: list[str]) -> list[str]:
        metrics = list(
            dict.fromkeys(
                value.strip().lower()
                for value in values
                if value.strip()
            )
        )
        if not metrics:
            raise ValueError("metrics must not be blank")
        return metrics

    @model_validator(mode="after")
    def validate_combination(self) -> "FinancialQuerySpec":
        allowed_metrics = (
            SNAPSHOT_METRICS
            if self.frequency == Frequency.SNAPSHOT
            else PERIODIC_METRICS
        )
        unsupported = sorted(set(self.metrics) - allowed_metrics)
        if unsupported:
            raise ValueError(f"Unsupported metrics: {unsupported}")

        if (
            self.start_year
            and self.end_year
            and self.start_year > self.end_year
        ):
            raise ValueError("start_year must be <= end_year")

        if self.frequency == Frequency.SNAPSHOT:
            if any(
                value is not None
                for value in (self.start_year, self.end_year, self.quarter)
            ):
                raise ValueError("snapshot queries cannot use fiscal period filters")
            if self.operation not in {
                Operation.LOOKUP,
                Operation.COMPARE,
                Operation.RANK,
            }:
                raise ValueError(
                    "snapshot queries support lookup, compare, and rank only"
                )
        else:
            has_one_year_boundary = (self.start_year is None) != (
                self.end_year is None
            )
            if (
                self.operation in {Operation.LOOKUP, Operation.COMPARE}
                and has_one_year_boundary
            ):
                raise ValueError(
                    "lookup and compare require both start_year and end_year; "
                    "for one fiscal year, set both to the same year"
                )
            if self.quarter is not None and self.frequency != Frequency.QUARTERLY:
                raise ValueError("quarter is valid only for quarterly queries")

        if self.operation == Operation.COMPARE and len(self.tickers) < 2:
            raise ValueError("compare requires at least two tickers")
        if self.operation == Operation.RANK and len(self.metrics) != 1:
            raise ValueError("rank requires exactly one metric")
        if self.operation == Operation.AGGREGATE:
            if self.aggregation is None or len(self.metrics) != 1:
                raise ValueError("aggregate requires one metric and aggregation")
        elif self.aggregation is not None:
            raise ValueError("aggregation is valid only for aggregate")

        return self


__all__ = [
    "Aggregation",
    "DERIVED_METRICS",
    "FinancialQuerySpec",
    "Frequency",
    "Operation",
    "PERIODIC_METRICS",
    "REPORTED_METRICS",
    "SNAPSHOT_METRICS",
    "SortOrder",
]
