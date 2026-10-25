"""Contract tests for Engine.query without Neo4j or paid LLM services."""

from pathlib import Path
import json
import os
import subprocess
from threading import RLock
from types import ModuleType, SimpleNamespace
import sys

import pytest

from semigraph_sdk.config import SDKConfig
from semigraph_sdk.retrieval.models import (
    CorpusChangedError,
    CorpusNotReadyError,
    InvalidQueryError,
    LLMNotConfiguredError,
    OptionalDependencyError,
    RetrievalBackendError,
    RetrievalStatus,
)
from semigraph_sdk.retrieval.query import query_engine
from semigraph_sdk.retrieval.triple_cache import TripleVectorCache


def make_config():
    return SDKConfig.model_validate({
        "workspace_id": "semigraph-sdk-tests",
        "database": {"uri": "bolt://localhost:7687", "user": "neo4j", "name": "neo4j"},
        "embedding": {"model": "fake/model", "revision": "main", "dimension": 2},
        "secrets_file": Path("/tmp/semigraph-sdk-tests.env"),
        "config_path": Path("/tmp/semigraph-sdk-tests.yaml"),
        "llm": {
            "provider": "openai", "model": "fake", "api_key_key": "FAKE_KEY",
        },
        "retrieval": {"agent": {"max_planned_tasks": 1}},
    })


class FakeSession:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def run(self, query, **_params):
        if "MATCH (m:SDKMeta" in query:
            revision = self.driver.revisions.pop(0) if self.driver.revisions else self.driver.last_revision
            self.driver.last_revision = revision
            return FakeRecord({
                "owner": self.driver.config.workspace_id,
                "search_ready": self.driver.ready,
                "corpus_revision": revision,
                "embedding_fingerprint": self.driver.config.embedding.fingerprint,
            })
        return FakeRows([])


class FakeRecord:
    def __init__(self, record):
        self.record = record

    def single(self):
        return self.record


class FakeRows:
    def __init__(self, rows):
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeDriver:
    def __init__(self, config, revisions=None, ready=True):
        self.config = config
        self.revisions = list(revisions or [1])
        self.last_revision = 1
        self.ready = ready

    def session(self, **_kwargs):
        return FakeSession(self)


class FakeEngine:
    def __init__(self, config=None, revisions=None, ready=True):
        self.config = config or make_config()
        self._driver = FakeDriver(self.config, revisions=revisions, ready=ready)
        self._triple_cache = TripleVectorCache()
        self._projection_lock = RLock()
        self.setup_called = False
        self.encoder = type("Encoder", (), {"encode": lambda _self, _query: [1.0, 0.0]})()

    def setup(self):
        self.setup_called = True

    def _get_query_encoder(self):
        return self.encoder


def _rows(_session, _config, *, query, top_k, **_kwargs):
    return ([{
        "chunk_id": "chunk-a", "text": "Pump P7 uses a ceramic seal.",
        "rank": 1, "score": 0.91, "score_kind": "cosine",
        "entities": [], "assertions": [],
    }][:top_k], {"candidate_count": 1, "query": query})


def _agent_patch(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    llm = object()
    monkeypatch.setattr(query_module, "_build_llm", lambda _config: llm)
    monkeypatch.setattr(query_module, "_load_relation_hints", lambda *_: {})
    monkeypatch.setattr(query_module, "_synthesize", lambda _llm, _question, evidence: (
        "A ceramic seal [chunk-a] [fabricated-id]",
        {"llm_calls": 1, "citation_status": "valid", "cited_chunk_ids": ["chunk-a"]},
    ))
    monkeypatch.setattr(query_module, "vector_retrieve", _rows)
    monkeypatch.setattr(query_module, "graph_retrieve", _rows)
    return query_module


@pytest.mark.parametrize("tool", ["vector", "graph"])
@pytest.mark.parametrize("agent", ["none", "task_specific", "deepagent"])
@pytest.mark.parametrize("output", ["chunks", "answer"])
def test_all_twelve_public_query_combinations(monkeypatch, tool, agent, output):
    query_module = _agent_patch(monkeypatch)
    if agent == "task_specific":
        import semigraph_sdk.agents.graph as task_module

        def run_agent(state, selected_tool, *, runtime, generate_answer):
            assert generate_answer is False
            rows = runtime.retriever(selected_tool)(
                query="Pump P7 material", top_k_chunks=runtime.config.top_k_chunks,
            )
            return {"synthesis_input": {"accepted_chunks": rows}, "worker_results": []}

        monkeypatch.setattr(task_module, "run_agent", run_agent)
    elif agent == "deepagent":
        monkeypatch.setattr(query_module, "_check_deepagent_dependency", lambda: None)
        deep_module = ModuleType("semigraph_sdk.agents.deepagent")

        def deepagent(question, selected_tool, FullAnswer, *, runtime):
            assert FullAnswer is False
            rows = runtime.retriever(selected_tool)(
                query="Pump P7 material", top_k_chunks=runtime.config.top_k_chunks,
            )
            return {"chunks": rows, "retrieval_trace": {"selected_chunk_ids": ["chunk-a"]}}

        deep_module.Deepagent = deepagent
        monkeypatch.setitem(sys.modules, "semigraph_sdk.agents.deepagent", deep_module)

    engine = FakeEngine()
    result = query_engine(
        engine,
        "What material does P7 use?",
        tool=tool,
        agent=agent,
        output=output,
        top_k=3,
    )

    assert engine.setup_called
    assert result.status == RetrievalStatus.OK
    assert result.tool == tool and result.agent == agent and result.output == output
    assert result.chunks[0].chunk_id == "chunk-a"
    assert result.chunks[0].matches[0].tool == tool
    assert result.chunks[0].matches[0].score_kind == ("cosine" if tool == "vector" else "ppr")
    if agent != "none":
        assert result.chunks[0].matches[0].query == "Pump P7 material"
    if output == "answer":
        assert result.answer == "A ceramic seal [chunk-a]"
        assert result.trace["synthesis"]["llm_calls"] == 1
    else:
        assert result.answer is None


def test_retrieve_only_never_builds_or_calls_llm(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    monkeypatch.setattr(query_module, "vector_retrieve", _rows)
    monkeypatch.setattr(
        query_module, "_build_llm",
        lambda *_: pytest.fail("Retrieve Only must not configure an LLM"),
    )
    result = query_engine(
        FakeEngine(), "question", tool="vector", agent="none", output="chunks", top_k=3,
    )
    assert result.answer is None


def test_no_evidence_answer_skips_synthesis(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    monkeypatch.setattr(query_module, "vector_retrieve", lambda *_a, **_k: ([], {}))
    monkeypatch.setattr(
        query_module, "_build_llm",
        lambda *_: pytest.fail("No evidence must not trigger an LLM call"),
    )
    result = query_engine(
        FakeEngine(), "question", tool="vector", agent="none", output="answer", top_k=3,
    )
    assert result.status == RetrievalStatus.NO_EVIDENCE
    assert result.answer == "Do not Answer"
    assert result.trace["synthesis"]["llm_calls"] == 0


def test_task_agent_and_shared_synthesis_run_through_public_facade(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    plan = {"tasks": [{
        "query": "Pump P7 material",
        "requirement": "Identify the material used by the pump seal",
    }]}
    assessment = {
        "accepted_chunk_ids": ["chunk-a"],
        "is_covered": True,
        "retry_query": None,
        "retry_strategy": None,
    }
    answer = {
        "parts": [{
            "answer": "A ceramic seal [chunk-a] [fabricated-id]",
            "supported_facts": [{
                "claim": "The seal is ceramic.",
                "evidence_ids": ["chunk-a", "unknown-id"],
            }],
        }],
        "final_answer": "A ceramic seal [chunk-a]",
    }

    class ScriptedLLM:
        def __init__(self):
            self.responses = iter([plan, assessment, answer])
            self.calls = 0

        def invoke(self, _messages):
            self.calls += 1
            return SimpleNamespace(content=json.dumps(next(self.responses)))

    llm = ScriptedLLM()
    searches = []

    def retrieve(session, config, *, query, top_k, **_kwargs):
        searches.append(query)
        return _rows(session, config, query=query, top_k=top_k)

    monkeypatch.setattr(query_module, "_build_llm", lambda _config: llm)
    monkeypatch.setattr(query_module, "_load_relation_hints", lambda *_: {})
    monkeypatch.setattr(query_module, "vector_retrieve", retrieve)

    result = query_engine(
        FakeEngine(), "What material does P7 use?", tool="vector",
        agent="task_specific", output="answer", top_k=3,
    )

    assert llm.calls == 3  # plan, assess, then one shared synthesis call
    assert searches == ["Pump P7 material"]
    assert result.answer == "A ceramic seal [chunk-a]"
    assert result.trace["synthesis"]["invalid_citation_ids"] == ["fabricated-id"]


def test_readiness_and_revision_race_are_typed(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    monkeypatch.setattr(query_module, "vector_retrieve", _rows)
    with pytest.raises(CorpusNotReadyError):
        query_engine(
            FakeEngine(ready=False), "question", tool="vector", agent="none",
            output="chunks", top_k=3,
        )
    with pytest.raises(CorpusChangedError):
        query_engine(
            FakeEngine(revisions=[1, 2]), "question", tool="vector", agent="none",
            output="chunks", top_k=3,
        )


def test_invalid_input_fails_before_database_setup():
    engine = FakeEngine()
    with pytest.raises(InvalidQueryError):
        query_engine(engine, "", tool="vector", agent="none", output="chunks", top_k=3)
    assert engine.setup_called is False


def test_direct_sdk_import_does_not_import_deepagent_dependency():
    source = Path(__file__).resolve().parents[1] / "src"
    env = {**os.environ, "PYTHONPATH": str(source)}
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys, semigraph_sdk; assert 'deepagents' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert process.returncode == 0, process.stderr


def test_missing_deepagent_extra_has_install_hint(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    monkeypatch.setitem(sys.modules, "deepagents", None)
    with pytest.raises(OptionalDependencyError, match=r"semigraph-sdk\[deepagents\]"):
        query_module._check_deepagent_dependency()


def test_llm_provider_configuration_is_checked_before_calls():
    import semigraph_sdk.retrieval.query as query_module

    config = make_config()
    config = config.model_copy(update={
        "llm": config.llm.model_copy(update={"provider": "unknown"}),
    })
    with pytest.raises(LLMNotConfiguredError, match="llm.provider"):
        query_module._build_llm(config)


def test_database_failure_does_not_become_empty_result(monkeypatch):
    import semigraph_sdk.retrieval.query as query_module

    monkeypatch.setattr(
        query_module, "vector_retrieve",
        lambda *_a, **_k: (_ for _ in ()).throw(ConnectionError("offline")),
    )
    with pytest.raises(RetrievalBackendError, match="vector_retrieval"):
        query_engine(
            FakeEngine(), "question", tool="vector", agent="none",
            output="chunks", top_k=3,
        )
