from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Frequency = Literal["annual", "quarterly"]
StatementType = Literal["income", "balance", "cash_flow"]



class CanonicalFact(BaseModel):
    ticker: str
    frequency: Frequency
    fiscal_year: int
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    period_start: date | None = None
    period_end: date
    accepted_at: datetime | None = None
    filed_date: date | None = None
    accession: str | None = None
    form: str | None = None
    statement_type: StatementType
    canonical_metric: str
    source_concept: str
    source_label: str | None = None
    source_row_index: int
    value: Decimal
    unit: str


class DerivedMetric(BaseModel):
    ticker: str
    fiscal_year: int
    period_end: date
    metric: str
    value: Decimal | None
    unit: str
    formula_version: str = "v1"
    input_fact_ids: list[int] = Field(default_factory=list)
    status: Literal["ok", "missing_input", "zero_denominator"]
    missing_inputs: list[str] = Field(default_factory=list)


