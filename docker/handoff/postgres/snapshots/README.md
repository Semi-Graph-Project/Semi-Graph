# PostgreSQL handoff snapshot

`semigraph.sql.gz` is a generated artifact and must not be committed. Create a
plain SQL dump without owners, privileges, roles, or passwords. The handoff
image creates the read-only `semigraph_agent` role from environment variables
after restoring the data.
