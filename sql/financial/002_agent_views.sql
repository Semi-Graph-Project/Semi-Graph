-- Curated, read-only serving views for the financial Agent.
-- Raw Finnhub JSON stays behind these stable long-format interfaces.

BEGIN;

CREATE OR REPLACE VIEW financial.latest_financial_facts AS
WITH ranked AS (
    SELECT
        f.*,
        row_number() OVER (
            PARTITION BY
                f.ticker,
                f.frequency,
                f.period_end,
                f.canonical_metric
            ORDER BY
                f.accepted_at DESC NULLS LAST,
                f.filed_date DESC NULLS LAST,
                f.raw_payload_id DESC
        ) AS revision_rank
    FROM financial.financial_facts AS f
)
SELECT *
FROM ranked
WHERE revision_rank = 1;

CREATE OR REPLACE VIEW financial.agent_periodic_metrics AS
SELECT
    fact_id::text AS evidence_id,
    ticker,
    frequency,
    fiscal_year,
    fiscal_quarter,
    period_end,
    canonical_metric AS metric,
    value,
    unit,
    'reported'::text AS source_kind,
    'ok'::text AS status,
    jsonb_build_object(
        'fact_id', fact_id,
        'accession', accession,
        'source_concept', source_concept,
        'raw_payload_id', raw_payload_id
    ) AS provenance
FROM financial.latest_financial_facts

UNION ALL

SELECT
    ('derived:' || derived_id)::text AS evidence_id,
    ticker,
    frequency,
    fiscal_year,
    NULL::smallint AS fiscal_quarter,
    period_end,
    metric,
    value,
    unit,
    'derived'::text AS source_kind,
    status,
    jsonb_build_object(
        'derived_id', derived_id,
        'formula_version', formula_version,
        'input_fact_ids', input_fact_ids,
        'missing_inputs', missing_inputs
    ) AS provenance
FROM financial.derived_metrics AS derived
WHERE NOT (
    derived.metric = 'gross_profit'
    AND EXISTS (
        SELECT 1
        FROM financial.latest_financial_facts AS reported
        WHERE reported.ticker = derived.ticker
          AND reported.frequency = derived.frequency
          AND reported.period_end = derived.period_end
          AND reported.canonical_metric = 'gross_profit'
    )
);

CREATE OR REPLACE VIEW financial.agent_market_metrics AS
WITH latest_quote AS (
    SELECT DISTINCT ON (ticker) *
    FROM financial.market_snapshots
    ORDER BY ticker, fetched_at DESC, snapshot_id DESC
),
latest_vendor AS (
    SELECT DISTINCT ON (ticker, metric) *
    FROM financial.vendor_metrics
    ORDER BY ticker, metric, fetched_at DESC, vendor_metric_id DESC
)
SELECT
    ('quote:' || snapshot_id)::text AS evidence_id,
    ticker,
    fetched_at AS observed_at,
    metric_rows.metric,
    metric_rows.value,
    metric_rows.unit,
    'finnhub_quote'::text AS source_kind,
    jsonb_build_object(
        'snapshot_id', snapshot_id,
        'raw_payload_id', raw_payload_id,
        'source_time', source_time
    ) AS provenance
FROM latest_quote
CROSS JOIN LATERAL (
    VALUES
        ('current_price', current_price, 'USD'),
        ('previous_close', previous_close, 'USD'),
        ('day_change_percent', change_percent, 'percent')
) AS metric_rows(metric, value, unit)

UNION ALL

SELECT
    ('vendor:' || vendor_metric_id)::text AS evidence_id,
    ticker,
    fetched_at AS observed_at,
    metric,
    value,
    unit,
    'finnhub_vendor_metric'::text AS source_kind,
    jsonb_build_object(
        'vendor_metric_id', vendor_metric_id,
        'raw_payload_id', raw_payload_id
    ) AS provenance
FROM latest_vendor;

INSERT INTO financial.schema_migrations(version, description)
VALUES (2, 'curated financial agent views')
ON CONFLICT (version) DO NOTHING;

COMMIT;
