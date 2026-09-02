# Neo4j handoff snapshots

Snapshot dumps are generated artifacts and must not be committed. Before
building the private images, place one `neo4j.dump` in each directory:

```text
snapshots/production/neo4j.dump
snapshots/controlled/neo4j.dump
snapshots/finreflectkg/neo4j.dump
```

Build each image with the matching `SNAPSHOT` argument. Only the user database
is included; never ship `system.dump` because it contains database users and
authentication state.
