#!/usr/bin/env bash
# Export private database snapshots for the advisor handoff release.

set -Eeuo pipefail
umask 077

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUTPUT_ARG=${1:-"${PROJECT_ROOT}/handoff-assets/advisor-data-v1"}
MIN_FREE_GB=${HANDOFF_MIN_FREE_GB:-4}

mkdir -p "${OUTPUT_ARG}"
OUTPUT_DIR=$(cd "${OUTPUT_ARG}" && pwd)

required_commands=(docker gzip sha256sum df)
for command_name in "${required_commands[@]}"; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo >&2 "Missing required command: ${command_name}"
        exit 1
    fi
done

free_kb=$(df -Pk "${OUTPUT_DIR}" | awk 'NR == 2 {print $4}')
required_kb=$((MIN_FREE_GB * 1024 * 1024))
if (( free_kb < required_kb )); then
    echo >&2 "Snapshot export requires at least ${MIN_FREE_GB} GB free in ${OUTPUT_DIR}"
    exit 1
fi

assets=(
    production.neo4j.dump
    controlled.neo4j.dump
    finreflectkg.neo4j.dump
    semigraph.postgres.sql.gz
    SHA256SUMS
)
for asset in "${assets[@]}"; do
    if [[ -e "${OUTPUT_DIR}/${asset}" || -e "${OUTPUT_DIR}/${asset}.partial" ]]; then
        echo >&2 "Refusing to overwrite existing asset: ${OUTPUT_DIR}/${asset}"
        exit 1
    fi
done

active_compose_file=
active_service=
active_was_running=0

restore_active_service() {
    if (( active_was_running )); then
        docker compose -f "${active_compose_file}" start "${active_service}" >/dev/null
        active_was_running=0
    fi
}
trap restore_active_service EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

dump_neo4j() {
    local compose_file=$1
    local service=$2
    local asset_name=$3
    local partial="${OUTPUT_DIR}/${asset_name}.partial"

    active_compose_file=${compose_file}
    active_service=${service}
    active_was_running=0
    if [[ -n $(docker compose -f "${compose_file}" ps --status running -q "${service}") ]]; then
        active_was_running=1
        docker compose -f "${compose_file}" stop "${service}"
    fi

    echo "Exporting ${service} to ${asset_name} (database is offline briefly)"
    docker compose -f "${compose_file}" run --rm --no-deps -T \
        --user neo4j --entrypoint neo4j-admin "${service}" \
        database dump neo4j --to-stdout >"${partial}"

    mv "${partial}" "${OUTPUT_DIR}/${asset_name}"
    restore_active_service
    active_compose_file=
    active_service=
}

cd "${PROJECT_ROOT}"
dump_neo4j docker-compose.yml neo4j production.neo4j.dump
dump_neo4j docker-compose.controlled.yml neo4j-controlled controlled.neo4j.dump
dump_neo4j docker-compose.finreflectkg.yml neo4j-finreflectkg finreflectkg.neo4j.dump

echo "Exporting PostgreSQL without stopping the service"
docker exec semigraph-postgres sh -c \
    'pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-owner --no-privileges' \
    | gzip -9 >"${OUTPUT_DIR}/semigraph.postgres.sql.gz.partial"
mv "${OUTPUT_DIR}/semigraph.postgres.sql.gz.partial" \
    "${OUTPUT_DIR}/semigraph.postgres.sql.gz"

(
    cd "${OUTPUT_DIR}"
    sha256sum \
        production.neo4j.dump \
        controlled.neo4j.dump \
        finreflectkg.neo4j.dump \
        semigraph.postgres.sql.gz >SHA256SUMS
    chmod 600 "${assets[@]}"
    sha256sum --check SHA256SUMS
)

echo "Snapshots ready in ${OUTPUT_DIR}"
echo "Do not commit this directory or any system.dump file."
