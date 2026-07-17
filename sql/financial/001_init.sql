-- Financial staging schema, migration 001.
--
-- Design layers:
--   1. control/ingestion: run-level audit and company universe
--   2. raw staging: immutable Finnhub payloads and run associations
--   3. canonical/derived: normalized facts and deterministic metrics
--   4. market/vendor: quote snapshots and selected vendor metrics
--
-- This migration intentionally creates tables only. Curated Agent views are
-- added in a later migration after the ingestion contract is exercised.

BEGIN;

CREATE SCHEMA IF NOT EXISTS financial;

CREATE TABLE IF NOT EXISTS financial.schema_migrations (
    version         integer PRIMARY KEY,
    description     text NOT NULL,
    applied_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS financial.ingestion_runs (
    run_id                  uuid PRIMARY KEY,
    started_at              timestamptz NOT NULL DEFAULT now(),
    finished_at             timestamptz,
    status                  text NOT NULL
                            CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    expected_company_count  integer NOT NULL CHECK (expected_company_count > 0),
    discovered_tickers      text[] NOT NULL DEFAULT '{}',
    successful_tickers      text[] NOT NULL DEFAULT '{}',
    failed_tickers          jsonb NOT NULL DEFAULT '{}'::jsonb,
    stats                   jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE IF NOT EXISTS financial.companies (
    ticker              varchar(10) PRIMARY KEY,
    active              boolean NOT NULL DEFAULT true,
    graph_seen_at       timestamptz NOT NULL,
    first_ingested_at   timestamptz,
    last_ingested_at    timestamptz,
    CHECK (ticker = upper(ticker)),
    CHECK (ticker <> '')
);

CREATE TABLE IF NOT EXISTS financial.raw_payloads (
    raw_payload_id       bigserial PRIMARY KEY,
    first_seen_run_id    uuid NOT NULL
                         REFERENCES financial.ingestion_runs(run_id),
    ticker               varchar(10) NOT NULL
                         REFERENCES financial.companies(ticker),
    endpoint             text NOT NULL
                         CHECK (
                             endpoint IN (
                                 'financials_reported',
                                 'basic_financials',
                                 'quote'
                             )
                         ),
    frequency            text NOT NULL DEFAULT 'none'
                         CHECK (frequency IN ('annual', 'quarterly', 'none')),
    fetched_at           timestamptz NOT NULL DEFAULT now(),
    payload_sha256       char(64) NOT NULL
                         CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    payload              jsonb NOT NULL,
    UNIQUE (ticker, endpoint, frequency, payload_sha256),
    CHECK (
        (endpoint = 'financials_reported' AND frequency IN ('annual', 'quarterly'))
        OR (endpoint IN ('basic_financials', 'quote') AND frequency = 'none')
    )
);

-- A payload can be observed by multiple ETL runs without duplicating the
-- JSONB document. This preserves both content idempotency and run history.
CREATE TABLE IF NOT EXISTS financial.ingestion_run_payloads (
    run_id          uuid NOT NULL
                    REFERENCES financial.ingestion_runs(run_id),
    raw_payload_id  bigint NOT NULL
                    REFERENCES financial.raw_payloads(raw_payload_id),
    observed_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, raw_payload_id)
);

CREATE TABLE IF NOT EXISTS financial.financial_facts (
    fact_id            bigserial PRIMARY KEY,
    raw_payload_id     bigint NOT NULL
                       REFERENCES financial.raw_payloads(raw_payload_id),
    ticker             varchar(10) NOT NULL
                       REFERENCES financial.companies(ticker),
    frequency          text NOT NULL
                       CHECK (frequency IN ('annual', 'quarterly')),
    fiscal_year        integer NOT NULL CHECK (fiscal_year BETWEEN 1900 AND 2100),
    fiscal_quarter     smallint,
    period_start       date,
    period_end         date NOT NULL,
    accepted_at        timestamptz,
    filed_date         date,
    accession          text,
    form               text,
    statement_type     text NOT NULL
                       CHECK (statement_type IN ('income', 'balance', 'cash_flow')),
    canonical_metric   text NOT NULL,
    source_concept     text NOT NULL,
    source_label       text,
    source_row_index   integer NOT NULL CHECK (source_row_index >= 0),
    value              numeric(30, 8) NOT NULL,
    unit               text NOT NULL,
    UNIQUE (raw_payload_id, frequency, period_end, canonical_metric),
    CHECK (
        (frequency = 'annual' AND fiscal_quarter IS NULL)
        OR (
            frequency = 'quarterly'
            AND fiscal_quarter BETWEEN 1 AND 4
        )
    ),
    CHECK (period_start IS NULL OR period_start <= period_end)
);

CREATE TABLE IF NOT EXISTS financial.derived_metrics (
    derived_id       bigserial PRIMARY KEY,
    ticker           varchar(10) NOT NULL
                     REFERENCES financial.companies(ticker),
    frequency        text NOT NULL CHECK (frequency = 'annual'),
    fiscal_year      integer NOT NULL CHECK (fiscal_year BETWEEN 1900 AND 2100),
    period_end       date NOT NULL,
    metric           text NOT NULL,
    value            numeric(30, 8),
    unit             text NOT NULL,
    formula_version  text NOT NULL,
    input_fact_ids   bigint[] NOT NULL DEFAULT '{}',
    status           text NOT NULL
                     CHECK (status IN ('ok', 'missing_input', 'zero_denominator')),
    missing_inputs   text[] NOT NULL DEFAULT '{}',
    UNIQUE (ticker, frequency, period_end, metric, formula_version)
);

CREATE TABLE IF NOT EXISTS financial.market_snapshots (
    snapshot_id      bigserial PRIMARY KEY,
    raw_payload_id   bigint NOT NULL UNIQUE
                     REFERENCES financial.raw_payloads(raw_payload_id),
    ticker            varchar(10) NOT NULL
                     REFERENCES financial.companies(ticker),
    source_time       timestamptz,
    fetched_at        timestamptz NOT NULL DEFAULT now(),
    current_price     numeric(20, 6),
    change_amount     numeric(20, 6),
    change_percent    numeric(20, 6),
    high_price        numeric(20, 6),
    low_price         numeric(20, 6),
    open_price        numeric(20, 6),
    previous_close    numeric(20, 6)
);

CREATE TABLE IF NOT EXISTS financial.vendor_metrics (
    vendor_metric_id  bigserial PRIMARY KEY,
    raw_payload_id    bigint NOT NULL
                      REFERENCES financial.raw_payloads(raw_payload_id),
    ticker            varchar(10) NOT NULL
                      REFERENCES financial.companies(ticker),
    metric            text NOT NULL,
    value             numeric(30, 8),
    unit              text NOT NULL,
    fetched_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (raw_payload_id, metric)
);

CREATE INDEX IF NOT EXISTS idx_raw_payloads_lookup
    ON financial.raw_payloads (ticker, endpoint, frequency, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_facts_lookup
    ON financial.financial_facts
       (ticker, canonical_metric, frequency, period_end DESC);

CREATE INDEX IF NOT EXISTS idx_financial_facts_period
    ON financial.financial_facts (period_end DESC, fiscal_year, fiscal_quarter);

CREATE INDEX IF NOT EXISTS idx_derived_metrics_lookup
    ON financial.derived_metrics (ticker, metric, period_end DESC);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_lookup
    ON financial.market_snapshots (ticker, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_vendor_metrics_lookup
    ON financial.vendor_metrics (ticker, metric, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_payloads_json
    ON financial.raw_payloads USING gin (payload);

INSERT INTO financial.schema_migrations(version, description)
VALUES (1, 'initial financial staging schema')
ON CONFLICT (version) DO NOTHING;

COMMIT;
