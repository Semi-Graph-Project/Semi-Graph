#!/usr/bin/env bash

snapshot=/snapshots/neo4j.dump
marker=/data/.semigraph-snapshot-loaded

if [[ -f "${marker}" ]]; then
    echo "[handoff] Neo4j snapshot already loaded"
    return 0
fi

if [[ ! -f "${snapshot}" ]]; then
    echo >&2 "[handoff] Missing ${snapshot} in the database image"
    return 1
fi

if [[ -d /data/databases/neo4j ]] \
    && find /data/databases/neo4j -type f -print -quit | grep -q .; then
    echo >&2 "[handoff] Refusing to overwrite a non-empty Neo4j named volume"
    return 1
fi

echo "[handoff] Loading Neo4j snapshot"
${neo4j_admin_cmd} database load neo4j \
    --from-path=/snapshots \
    --overwrite-destination=true

touch "${marker}"
chown neo4j:neo4j "${marker}"
