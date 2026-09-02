FROM neo4j:2025.04-community@sha256:80cc874b30cc7a5a75b76b8deb7cb652d60c7d2fa5bad639155d0bdef1a48509

ARG SNAPSHOT
ENV EXTENSION_SCRIPT=/opt/semigraph/load-snapshot.sh

COPY --chmod=755 load-snapshot.sh /opt/semigraph/load-snapshot.sh
COPY snapshots/${SNAPSHOT}/neo4j.dump /snapshots/neo4j.dump
