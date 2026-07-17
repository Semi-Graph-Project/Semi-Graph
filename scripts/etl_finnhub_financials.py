
import argparse

from semigraph.config import get_config
from semigraph.financial.etl import run_financial_etl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-company-count", type=int, default=14)
    parser.add_argument("--ticker", action="append")
    args = parser.parse_args()

    cfg = get_config()
    if args.expected_company_count != cfg.financial_expected_company_count:
        raise SystemExit("CLI expected count does not match Config")

    summary = run_financial_etl(cfg=cfg, only_tickers=args.ticker)
    print(summary.model_dump_json(indent=2))
    if summary.status == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()