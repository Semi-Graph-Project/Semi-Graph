"""Unit tests for KGStore filing-level cleanup."""
from __future__ import annotations

from semigraph.offline.chunker import Chunk
from semigraph.offline.kg_store import KGStore


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def single(self):
        return self._row


class _FakeTx:
    def __init__(self, chunk_ids):
        self.chunk_ids = chunk_ids
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query.strip(), params))
        if "RETURN collect(DISTINCT c.chunk_id)" in query:
            return _FakeResult({"chunk_ids": self.chunk_ids})
        return _FakeResult({})


class _FakeSession:
    def __init__(self, tx):
        self.tx = tx
        self.write_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_write(self, fn):
        self.write_calls += 1
        return fn(self.tx)


class _FakeDriver:
    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session


def test_reset_filing_deletes_previous_filing_subgraph():
    tx = _FakeTx(["c1", "c2"])
    session = _FakeSession(tx)
    store = KGStore(driver=_FakeDriver(session))

    store.reset_filing("KLAC", "2025", "10-K")

    assert session.write_calls == 1
    queries = [q for q, _ in tx.calls]
    first_query, first_params = tx.calls[0]

    assert "MATCH (s:Section {doc_key: $doc_key})-[:HAS_CHUNK]->(c:Chunk)" in first_query
    assert first_params == {"doc_key": "KLAC_2025_10-K"}
    assert any("MATCH ()-[r]->()" in q and "r.source_chunk IN $chunk_ids" in q for q in queries)
    assert any("MATCH (c:Chunk)" in q and "DETACH DELETE c" in q for q in queries)
    assert any("MATCH (s:Section {doc_key: $doc_key})" in q for q in queries)
    assert any("MATCH (d:Document {doc_key: $doc_key})" in q for q in queries)
    assert any("MATCH (e:Entity)" in q and "DETACH DELETE e" in q for q in queries)


def test_ensure_chunk_persists_filing_type():
    tx = _FakeTx([])
    session = _FakeSession(tx)
    store = KGStore(driver=_FakeDriver(session))
    chunk = Chunk(
        chunk_id="KLAC_2025_Item_1_0000_deadbeef",
        text="sample text",
        ticker="KLAC",
        fiscal_year="2025",
        filing_type="10-K",
        section="Item_1",
        char_count=11,
        token_estimate=3,
    )

    store._ensure_chunk(tx, "KLAC_2025_10-K", chunk)

    query, params = tx.calls[0]
    assert "c.filing_type = $filing_type" in query
    assert params["filing_type"] == "10-K"
