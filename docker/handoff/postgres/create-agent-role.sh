#!/bin/sh
set -eu

agent_user=${POSTGRES_AGENT_USER:-semigraph_agent}
agent_password=${POSTGRES_AGENT_PASSWORD:?POSTGRES_AGENT_PASSWORD is required}
escaped_password=$(printf '%s' "${agent_password}" | sed "s/'/''/g")

case "${agent_user}:${POSTGRES_DB}" in
    *[!A-Za-z0-9_:]*)
        echo >&2 "POSTGRES_AGENT_USER and POSTGRES_DB may contain only letters, numbers, and underscores"
        exit 1
        ;;
esac

psql --set ON_ERROR_STOP=1 \
    --username "${POSTGRES_USER}" \
    --dbname "${POSTGRES_DB}" <<SQL
CREATE ROLE ${agent_user} LOGIN PASSWORD '${escaped_password}';
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${agent_user};
GRANT USAGE ON SCHEMA public TO ${agent_user};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${agent_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${agent_user};
SQL
