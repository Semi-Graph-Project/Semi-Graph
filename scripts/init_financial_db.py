from psycopg import sql

from semigraph.config import get_config
from semigraph.financial.db import financial_connection


def main() -> None:
    cfg = get_config()
    migration_dir = cfg.project_root / "sql" / "financial"
    migration_paths = sorted(migration_dir.glob("[0-9][0-9][0-9]_*.sql"))
    if not migration_paths:
        raise RuntimeError(f"No financial migrations found in {migration_dir}")

    with financial_connection(readonly=False, cfg=cfg) as conn:
        for migration_path in migration_paths:
            conn.execute(migration_path.read_text(encoding="utf-8"))

        conn.execute(
            sql.SQL(
                """
                DO $block$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_roles WHERE rolname = {role_literal}
                    ) THEN
                        EXECUTE format(
                            'CREATE ROLE %I LOGIN PASSWORD %L',
                            {role_literal},
                            {password_literal}
                        );
                    END IF;
                END
                $block$;
                """
            ).format(
                role_literal=sql.Literal(cfg.postgres_agent_user),
                password_literal=sql.Literal(cfg.postgres_agent_password),
            )
        )

        conn.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier("semigraph"),
                sql.Identifier(cfg.postgres_agent_user),
            )
        )
        conn.execute(
            sql.SQL("GRANT USAGE ON SCHEMA financial TO {}").format(
                sql.Identifier(cfg.postgres_agent_user)
            )
        )
        conn.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA financial TO {}").format(
                sql.Identifier(cfg.postgres_agent_user)
            )
        )
        conn.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA financial "
                "GRANT SELECT ON TABLES TO {}"
            ).format(sql.Identifier(cfg.postgres_agent_user))
        )

    print("Financial schema initialized.")


if __name__ == "__main__":
    main()
