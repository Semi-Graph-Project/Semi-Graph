FROM postgres:16-alpine@sha256:57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777

COPY snapshots/semigraph.sql.gz /docker-entrypoint-initdb.d/10-semigraph.sql.gz
COPY --chmod=755 create-agent-role.sh /docker-entrypoint-initdb.d/20-create-agent-role.sh
