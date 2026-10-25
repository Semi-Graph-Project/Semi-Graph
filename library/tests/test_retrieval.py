"""Deterministic tests for retrieval kernels and their performance seams."""

from pathlib import Path

import pytest

from semigraph_sdk.config import SDKConfig
from semigraph_sdk.retrieval.graph import graph_retrieve
from semigraph_sdk.retrieval.encoder import QueryEncoder
from semigraph_sdk.retrieval.ppr import rank_chunks, rank_entities
from semigraph_sdk.retrieval.projection import ensure_projection, projection_name
from semigraph_sdk.retrieval.query import validate_query
from semigraph_sdk.retrieval.seeds import select_seeds
from semigraph_sdk.retrieval.triple_cache import TripleVectorCache
from semigraph_sdk.retrieval.vector import vector_retrieve
from semigraph_sdk.retrieval.models import InvalidQueryError, RetrievalConfigError


def make_config(**overrides):
    payload = {
        "workspace_id": "semigraph-sdk-tests",
        "database": {
            "uri": "bolt://localhost:7687", "user": "neo4j", "name": "neo4j",
        },
        "embedding": {
            "model": "fake/model", "revision": "main", "dimension": 2,
        },
        "secrets_file": Path("/tmp/semigraph-sdk-tests.env"),
        "config_path": Path("/tmp/semigraph-sdk-tests.yaml"),
    }
    payload.update(overrides)
    return SDKConfig.model_validate(payload)


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class VectorSession:
    def __init__(self):
        self.queries = []

    def run(self, query, **params):
        self.queries.append((query, params))
        if "db.index.vector.queryNodes" in query:
            return Rows([{"chunk_id": "chunk-a", "score": 0.91}])
        return Rows([{
            "chunk_id": "chunk-a",
            "text": "Pump P7 uses a ceramic seal.",
            "entities": [],
            "assertions": [],
        }])


def test_vector_kernel_uses_sdk_index_and_hydrates_only_selected_chunk():
    session = VectorSession()
    encoded = []

    chunks, trace = vector_retrieve(
        session,
        make_config(),
        query="What material does P7 use?",
        top_k=4,
        encode=lambda query: encoded.append(query) or [0.2, 0.8],
    )

    assert encoded == ["What material does P7 use?"]
    assert session.queries[0][1]["index_name"] == "sg_chunk_embedding"
    assert session.queries[0][1]["top_k"] == 4
    assert chunks[0]["text"] == "Pump P7 uses a ceramic seal."
    assert chunks[0]["score_kind"] == "cosine"
    assert trace["candidate_count"] == 1


def test_query_encoder_loads_one_embedder_and_reuses_it(monkeypatch):
    import semigraph_sdk.retrieval.encoder as encoder_module

    instances = []

    class FakeEmbedder:
        def __init__(self, _config):
            self.calls = []
            instances.append(self)

        def embed(self, texts):
            self.calls.append(texts)
            return [[0.6, 0.8]]

    monkeypatch.setattr(encoder_module, "SentenceTransformerEmbedder", FakeEmbedder)
    encoder = QueryEncoder(make_config().embedding)

    assert encoder.encode("first") == [0.6, 0.8]
    assert encoder.encode("second") == [0.6, 0.8]
    assert len(instances) == 1
    assert instances[0].calls == [["first"], ["second"]]


def test_triple_cache_warm_query_reuses_vectors_and_evicts_old_revision():
    class TripleSession:
        def __init__(self):
            self.calls = 0

        def run(self, query):
            self.calls += 1
            return Rows([
                {
                    "assertion_id": "a1", "triple_text": "P7 USES_MATERIAL ceramic",
                    "relation": "USES_MATERIAL", "head": "P7", "head_type": "Pump",
                    "tail": "ceramic", "tail_type": "Material", "embedding": [1.0, 0.0],
                },
                {
                    "assertion_id": "a2", "triple_text": "P8 USES_MATERIAL steel",
                    "relation": "USES_MATERIAL", "head": "P8", "head_type": "Pump",
                    "tail": "steel", "tail_type": "Material", "embedding": [0.0, 1.0],
                },
            ])

    session = TripleSession()
    cache = TripleVectorCache()
    params = {
        "workspace_id": "semigraph-sdk-tests",
        "database_name": "neo4j",
        "embedding_fingerprint": "fingerprint",
        "query_vector": [0.9, 0.1],
        "top_k": 2,
        "min_score": None,
    }
    first, first_hit = cache.select(session, corpus_revision=1, **params)
    warm, warm_hit = cache.select(session, corpus_revision=1, **params)
    changed, changed_hit = cache.select(session, corpus_revision=2, **params)

    assert first_hit is False and warm_hit is True and changed_hit is False
    assert session.calls == 2
    assert first[0]["assertion_id"] == warm[0]["assertion_id"] == "a1"
    assert changed[0]["score"] == pytest.approx(first[0]["score"])
    assert cache.cached_revision == 2


@pytest.mark.parametrize("mode", ["triple", "entity", "chunk"])
def test_graph_seed_modes_produce_node_ids(mode):
    class SeedSession:
        def run(self, query, **params):
            if "sg_entity_embedding" in query:
                return Rows([{"node_id": 10, "name": "P7", "type": "Pump", "score": 0.8}])
            if "sg_chunk_embedding" in query:
                return Rows([{"node_id": 11, "chunk_id": "chunk-a", "score": 0.7}])
            return Rows([{
                "assertion_id": "a1", "triple_text": "P7 USES_MATERIAL ceramic",
                "relation": "USES_MATERIAL", "head": "P7", "head_type": "Pump",
                "tail": "ceramic", "tail_type": "Material", "embedding": [1.0, 0.0],
            }])

    config = make_config(retrieval={"graph": {"seed_mode": mode}})
    seed_ids, trace = select_seeds(
        SeedSession(),
        config,
        query_vector=[1.0, 0.0],
        corpus_revision=1,
        cache=TripleVectorCache(),
    )

    assert seed_ids
    assert trace["mode"] == mode
    assert trace["selected"]


def test_graph_returns_no_seeds_without_projection_or_vector_fallback(monkeypatch):
    import semigraph_sdk.retrieval.graph as graph_module

    projection_calls = []
    monkeypatch.setattr(graph_module, "select_seeds", lambda *a, **k: ([], {"mode": "triple"}))
    monkeypatch.setattr(
        graph_module, "ensure_projection",
        lambda *a, **k: projection_calls.append(True),
    )

    chunks, trace = graph_retrieve(
        object(), make_config(), query="unknown", top_k=3, corpus_revision=1,
        encode=lambda _: [1.0, 0.0], triple_cache=TripleVectorCache(),
        projection_lock=__import__("threading").RLock(),
    )

    assert chunks == []
    assert trace["abort_reason"] == "no_seeds"
    assert projection_calls == []


def test_projection_create_race_reuses_projection_created_by_peer(monkeypatch):
    import semigraph_sdk.retrieval.graph as graph_module
    from semigraph_sdk.retrieval.projection import ProjectionError, projection_name

    class ProjectionSession:
        def run(self, query, **_params):
            if "gds.graph.exists" in query:
                return FakeSingle({"exists": True})
            return FakeSingle({
                "graphName": projection_name("semigraph-sdk-tests"),
                "nodeCount": 7,
                "relationshipCount": 9,
            })

    class FakeSingle:
        def __init__(self, record):
            self.record = record

        def single(self):
            return self.record

    monkeypatch.setattr(
        graph_module, "ensure_projection",
        lambda *_a, **_k: (_ for _ in ()).throw(ProjectionError("name already exists")),
    )
    result = graph_module._ensure_projection(ProjectionSession(), "semigraph-sdk-tests")

    assert result["created"] is False
    assert result["node_count"] == 7


class ProjectionResult:
    def __init__(self, row=None):
        self.row = row

    def single(self):
        return self.row

    def consume(self):
        return None


class ProjectionSession:
    def __init__(self, exists):
        self.exists = exists
        self.events = []
        self.project_query = None

    def run(self, query, **_params):
        if "gds.graph.exists" in query:
            self.events.append("exists")
            return ProjectionResult({"exists": self.exists})
        if "gds.graph.drop" in query:
            self.events.append("drop")
            self.exists = False
            return ProjectionResult({"graphName": "old"})
        if "gds.graph.list" in query:
            self.events.append("list")
            return ProjectionResult({
                "graphName": "existing", "nodeCount": 4, "relationshipCount": 3,
            })
        if "gds.graph.project" in query:
            self.events.append("project")
            self.project_query = query
            self.exists = True
            return ProjectionResult({
                "graph_name": "created", "node_count": 5, "relationship_count": 6,
            })
        raise AssertionError(f"Unexpected projection query: {query}")


def test_ensure_projection_reuses_existing_workspace_graph():
    session = ProjectionSession(exists=True)

    result = ensure_projection(session, "semigraph-sdk-tests")

    assert result == {
        "name": "existing", "node_count": 4,
        "relationship_count": 3, "created": False,
    }
    assert session.events == ["exists", "list"]


def test_ensure_projection_rebuilds_and_projects_arbitrary_sdk_relations():
    session = ProjectionSession(exists=True)

    result = ensure_projection(session, "semigraph-sdk-tests", rebuild=True)

    assert session.events == ["exists", "drop", "project"]
    assert result == {
        "name": "created", "node_count": 5,
        "relationship_count": 6, "created": True,
    }
    assert "type(r)" in session.project_query
    assert "r.source_chunk_id IS NOT NULL" in session.project_query
    assert "relationshipType: projected_type" in session.project_query
    assert projection_name("semigraph-sdk-tests").startswith("semigraph_sdk_")


def test_ppr_ranks_only_selected_chunks_and_entities_in_neo4j():
    class PageRankSession:
        def __init__(self):
            self.calls = []

        def run(self, query, **params):
            self.calls.append((query, params))
            if "WHERE node:Chunk" in query:
                return Rows([
                    {"chunk_id": "chunk-a", "score": 0.75},
                    {"chunk_id": "chunk-b", "score": 0.25},
                ])
            return Rows([{"name": "P7", "type": "Pump", "score": 0.9}])

    session = PageRankSession()
    source_refs = [{"kind": "entity", "name": "P7", "type": "Pump"}]

    chunks = rank_chunks(
        session, graph_name="sdk-graph", source_refs=source_refs,
        damping=0.5, max_iterations=20, top_k=2,
    )
    entities = rank_entities(
        session, graph_name="sdk-graph", source_refs=source_refs,
        damping=0.5, max_iterations=20, top_k=1,
    )

    assert chunks == [
        {"chunk_id": "chunk-a", "score": 0.75, "score_kind": "ppr", "rank": 1},
        {"chunk_id": "chunk-b", "score": 0.25, "score_kind": "ppr", "rank": 2},
    ]
    assert entities == [{"name": "P7", "type": "Pump", "score": 0.9, "rank": 1}]
    assert all("gds.pageRank.stream" in query for query, _ in session.calls)
    assert all(params["source_refs"] == source_refs for _, params in session.calls)
    assert session.calls[0][1]["top_k"] == 2
    assert session.calls[1][1]["top_k"] == 1


def test_query_validation_rejects_bad_modes_budgets_and_questions():
    config = make_config()
    with pytest.raises(InvalidQueryError):
        validate_query(config, " ", tool="vector", agent="none", output="chunks", top_k=1)
    with pytest.raises(InvalidQueryError):
        validate_query(config, "question", tool="magic", agent="none", output="chunks", top_k=1)
    with pytest.raises(InvalidQueryError):
        validate_query(config, "question", tool="vector", agent="none", output="chunks", top_k=True)
    with pytest.raises(RetrievalConfigError):
        validate_query(config, "question", tool="vector", agent="task_specific", output="chunks", top_k=2)
