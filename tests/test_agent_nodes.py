import semigraph.agent.nodes as nodes


def _financial_chunk(**overrides):
    chunk = {
        "chunk_id": "fin-29-1",
        "text": "NVDA revenue raw financial text",
        "ticker": "NVDA",
        "fiscal_year": 2024,
        "fiscal_quarter": None,
        "frequency": "annual",
        "section": "Financial_revenue",
        "score": 1.0,
        "metric": "revenue",
        "value": "60922000000",
        "unit": "usd",
        "period_end": "2024-01-28",
        "observed_at": None,
        "status": "ok",
        "source_kind": "reported",
        "provenance": {
            "fact_id": 29,
            "accession": "0001045810-24-000029",
            "source_concept": "us-gaap_Revenues",
            "debug_blob": "must not enter prompt",
        },
    }
    chunk.update(overrides)
    return chunk


def test_financial_chunk_format_is_readable_and_exact_for_observation():
    formatted = nodes._format_chunks_for_observation([_financial_chunk()])

    assert "FINANCIAL" in formatted
    assert "metric=revenue" in formatted
    assert "period=FY2024 (as of 2024-01-28)" in formatted
    assert "value=$60.92B (exact=60922000000 usd)" in formatted
    assert '"fact_id": 29' in formatted
    assert "debug_blob" not in formatted


def test_financial_chunk_format_uses_percent_and_keeps_full_citation_data():
    chunk = _financial_chunk(
        metric="gross_margin",
        section="Financial_gross_margin",
        value="0.5425",
        unit="ratio",
        source_kind="derived",
        provenance={
            "derived_id": 7,
            "input_fact_ids": [29, 30],
            "formula_version": "v1",
            "debug_blob": "kept outside prompt",
        },
    )

    formatted, citation_lookup = nodes._format_chunks_for_synthesis([chunk])

    assert "evidence_type=financial" in formatted
    assert "value=54.25% (exact=0.5425 ratio)" in formatted
    assert '"input_fact_ids": [29, 30]' in formatted
    assert "debug_blob" not in formatted
    assert citation_lookup[1]["provenance"]["debug_blob"] == "kept outside prompt"


class TestExecuteNode:

    def test_execute_dispatches_selected_retriever_and_updates_state(
        self, monkeypatch
    ):
        calls = {}

        def fake_retriever(query: str, top_k_chunks: int, cfg):
            calls["query"] = query
            calls["top_k_chunks"] = top_k_chunks
            calls["cfg"] = cfg
            return [
                {"chunk_id": "c1", "text": "alpha"},
                {"chunk_id": "c2", "text": "beta"},
            ]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setitem(nodes.RETRIEVERS, "graph", fake_retriever)

        state = {
            "subqueries": ["Which supplier serves NVIDIA?"],
            "current_subquery_idx": 0,
            "next_tool": {
                "name": "graph",
                "args": {
                    "query": "NVIDIA supplier relationship",
                    "top_k_chunks": 3,
                },
            },
            "chunks_history": [{"chunk_id": "old", "text": "existing"}],
            "tool_call_log": [],
            "round": 1,
        }

        result = nodes.execute_node(state)

        assert calls == {
            "query": "NVIDIA supplier relationship",
            "top_k_chunks": 3,
            "cfg": "cfg-sentinel",
        }
        assert result["latest_chunks"] == [
            {"chunk_id": "c1", "text": "alpha"},
            {"chunk_id": "c2", "text": "beta"},
        ]
        assert result["chunks_history"] == [
            {"chunk_id": "old", "text": "existing"},
            {"chunk_id": "c1", "text": "alpha"},
            {"chunk_id": "c2", "text": "beta"},
        ]
        assert result["tool_call_log"] == [{
            "round": 1,
            "subquery": "Which supplier serves NVIDIA?",
            "tool": "graph",
            "query": "NVIDIA supplier relationship",
            "top_k_chunks": 3,
            "n_chunks": 2,
            "status": "ok",
        }]

    def test_execute_falls_back_to_current_subquery_when_query_missing(
        self, monkeypatch
    ):
        calls = {}

        def fake_retriever(query: str, top_k_chunks: int, cfg):
            calls["query"] = query
            calls["top_k_chunks"] = top_k_chunks
            return []

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setitem(nodes.RETRIEVERS, "vector", fake_retriever)

        state = {
            "original_query": "Describe AMD strategy",
            "subqueries": ["Describe AMD strategy"],
            "current_subquery_idx": 0,
            "next_tool": {
                "name": "vector",
                "args": {},
            },
        }

        result = nodes.execute_node(state)

        assert calls["query"] == "Describe AMD strategy"
        assert calls["top_k_chunks"] == nodes.DEFAULT_TOP_K
        assert result["latest_chunks"] == []
        assert result["tool_call_log"][0]["status"] == "ok"

    def test_execute_logs_missing_retriever_without_crashing(self):
        state = {
            "subqueries": ["What is AMD revenue?"],
            "current_subquery_idx": 0,
            "next_tool": {
                "name": "missing_tool",
                "args": {"query": "What is AMD revenue?"},
            },
            "chunks_history": [{"chunk_id": "old", "text": "existing"}],
            "tool_call_log": [],
        }

        result = nodes.execute_node(state)

        assert result["chunks_history"] == [
            {"chunk_id": "old", "text": "existing"},
        ]
        assert result["latest_chunks"] == []
        assert result["tool_call_log"][0]["status"] == "error"
        assert "No retriever found" in result["tool_call_log"][0]["error"]

    def test_execute_logs_retriever_exception_without_crashing(
        self, monkeypatch
    ):
        def fake_retriever(query: str, top_k_chunks: int, cfg):
            raise RuntimeError("boom")

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setitem(nodes.RETRIEVERS, "news", fake_retriever)

        state = {
            "subqueries": ["What is the latest AMD news?"],
            "current_subquery_idx": 0,
            "next_tool": {
                "name": "news",
                "args": {"query": "AMD latest news"},
            },
            "chunks_history": [{"chunk_id": "old", "text": "existing"}],
            "tool_call_log": [],
            "round": 2,
        }

        result = nodes.execute_node(state)

        assert result["chunks_history"] == [
            {"chunk_id": "old", "text": "existing"},
        ]
        assert result["latest_chunks"] == []
        assert result["tool_call_log"] == [{
            "round": 2,
            "subquery": "What is the latest AMD news?",
            "tool": "news",
            "query": "AMD latest news",
            "top_k_chunks": nodes.DEFAULT_TOP_K,
            "n_chunks": 0,
            "status": "error",
            "error": "boom",
        }]

    def test_execute_persists_structured_retrieval_trace(self, monkeypatch):
        def fake_retriever(query: str, top_k_chunks: int, cfg):
            return {
                "chunks": [{"chunk_id": "c1", "text": "evidence"}],
                "trace": {
                    "retriever": "graph",
                    "profile": "phase_t",
                    "parameters": {"ppr_graph_mode": "entity_chunk"},
                    "seed_count": 3,
                    "candidate_count": 100,
                    "reranker": {"status": "ok"},
                },
            }

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setitem(nodes.RETRIEVERS, "graph", fake_retriever)

        result = nodes.execute_node({
            "subqueries": ["How does AMD depend on TSMC?"],
            "current_subquery_idx": 0,
            "next_tool": {
                "name": "graph",
                "args": {"query": "AMD TSMC dependency"},
            },
            "round": 1,
        })

        trace = result["retrieval_trace_history"][-1]
        assert trace["status"] == "ok"
        assert trace["profile"] == "phase_t"
        assert trace["parameters"]["ppr_graph_mode"] == "entity_chunk"
        assert trace["seed_count"] == 3
        assert trace["candidate_count"] == 100
        assert trace["returned_chunk_ids"] == ["c1"]


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeToolResponse:
    def __init__(self, name: str, args: dict):
        self.tool_calls = [{
            "name": name,
            "args": args,
        }]


class TestObserveNode:

    def test_observe_summarizes_latest_chunks_and_appends_history(
        self, monkeypatch
    ):
        captured = {}

        class FakeLLM:
            def invoke(self, messages):
                captured["messages"] = messages
                return _FakeResponse("AMD's strategy evidence centers on AI and data center growth.")

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "subqueries": ["Describe AMD strategy"],
            "current_subquery_idx": 0,
            "next_tool": {"name": "vector", "args": {"query": "AMD strategy"}},
            "latest_chunks": [{
                "chunk_id": "c1",
                "text": "AMD is focused on AI accelerators and data center expansion.",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
            }],
            "observation_history": [{
                "round": 0,
                "subquery": "old",
                "tool": "graph",
                "n_chunks": 1,
                "observation_text": "old observation",
            }],
            "round": 1,
        }

        result = nodes.observe_node(state)

        assert result["observation_text"] == (
            "AMD's strategy evidence centers on AI and data center growth."
        )
        assert len(result["observation_history"]) == 2
        assert result["observation_history"][-1] == {
            "round": 1,
            "subquery": "Describe AMD strategy",
            "tool": "vector",
            "n_chunks": 1,
            "observation_text": (
                "AMD's strategy evidence centers on AI and data center growth."
            ),
        }
        assert captured["messages"][0]["content"] == nodes.OBSERVE_SYSTEM_PROMPT
        assert "Subquery: Describe AMD strategy" in captured["messages"][1]["content"]
        assert "Selected tool: vector" in captured["messages"][1]["content"]
        assert "[c1] AMD FY2025 Item_1" in captured["messages"][1]["content"]

    def test_observe_returns_no_evidence_without_calling_llm(
        self, monkeypatch
    ):
        def fail_if_called(_cfg):
            raise AssertionError("LLM should not be called when no chunks exist")

        monkeypatch.setattr(nodes, "get_llm", fail_if_called)

        state = {
            "subqueries": ["Describe AMD strategy"],
            "current_subquery_idx": 0,
            "next_tool": {"name": "vector", "args": {}},
            "latest_chunks": [],
            "observation_history": [],
            "round": 2,
        }

        result = nodes.observe_node(state)

        assert result["observation_text"] == "The retrieval did not find evidence."
        assert result["observation_history"] == [{
            "round": 2,
            "subquery": "Describe AMD strategy",
            "tool": "vector",
            "n_chunks": 0,
            "observation_text": "The retrieval did not find evidence.",
        }]

    def test_observe_falls_back_when_llm_raises(
        self, monkeypatch
    ):
        class FailingLLM:
            def invoke(self, _messages):
                raise RuntimeError("llm down")

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FailingLLM())

        state = {
            "original_query": "What is AMD strategy?",
            "next_tool": {"name": "vector", "args": {"query": "AMD strategy"}},
            "latest_chunks": [{
                "chunk_id": "c1",
                "text": "AMD highlighted AI and data center demand in its filing.",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
            }],
            "observation_history": [],
            "round": 3,
        }

        result = nodes.observe_node(state)

        assert "Observation fallback:" in result["observation_text"]
        assert "AMD FY2025 Item_1" in result["observation_text"]
        assert result["observation_history"][0]["round"] == 3


class TestToolSelectNode:

    def test_tool_select_uses_retry_query_when_present(
        self, monkeypatch
    ):
        captured = {}

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                captured["messages"] = messages
                return _FakeToolResponse(
                    "graph",
                    {"query": "AMD supplier dependency and TSMC supply chain risk"},
                )

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "subqueries": ["Describe AMD strategy"],
            "current_subquery_idx": 0,
            "retry_query": "AMD supplier dependency and TSMC supply chain risk",
            "reflection_feedback": (
                "Search for supplier relationship evidence, not general strategy."
            ),
        }

        result = nodes.tool_select_node(state)

        assert result["next_tool"] == {
            "name": "graph",
            "args": {"query": "AMD supplier dependency and TSMC supply chain risk"},
        }
        assert (
            "Query candidate: AMD supplier dependency and TSMC supply chain risk"
            in captured["messages"][1]["content"]
        )
        assert (
            "Reflection feedback: Search for supplier relationship evidence, not general strategy."
            in captured["messages"][1]["content"]
        )

    def test_tool_select_prefers_financial_for_latest_metric_queries(
        self, monkeypatch
    ):
        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, _messages):
                return _FakeToolResponse(
                    "news",
                    {"query": "AMD latest FY2025 revenue and EPS"},
                )

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "subqueries": ["What is AMD latest FY2025 revenue and EPS?"],
            "current_subquery_idx": 0,
        }

        result = nodes.tool_select_node(state)

        assert result["next_tool"] == {
            "name": "financial",
            "args": {
                "query": "What is AMD latest FY2025 revenue and EPS?",
                "top_k_chunks": nodes.DEFAULT_TOP_K,
            },
        }


class TestReflectNode:

    def test_reflect_marks_sufficient_from_llm_json(
        self, monkeypatch
    ):
        class FakeLLM:
            def invoke(self, _messages):
                return _FakeResponse(
                    '{"sufficient": true, "reason": "Evidence directly answers the original query.", "retry_query": "", "feedback": ""}'
                )

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "original_query": "What is AMD strategy?",
            "subqueries": ["Describe AMD strategy"],
            "current_subquery_idx": 0,
            "observation_text": "AMD focuses on AI and data center growth.",
            "observation_history": [],
            "tool_call_log": [],
            "round": 0,
        }

        result = nodes.reflect_node(state)

        assert result["sufficient"] is True
        assert result["round"] == 1
        assert result["reflection_reason"] == (
            "Evidence directly answers the original query."
        )
        assert result["retry_query"] == ""
        assert result["reflection_feedback"] == ""
        assert result["reflection_history"][-1]["sufficient"] is True
        assert result["stop_reason"] == "sufficient"

    def test_reflect_marks_insufficient_with_retry_query(
        self, monkeypatch
    ):
        class FakeLLM:
            def invoke(self, _messages):
                return _FakeResponse(
                    '{"sufficient": false, "reason": "Current evidence is about strategy, not supplier exposure.", "retry_query": "AMD supplier dependency and TSMC supply chain risk", "feedback": "Search for supplier relationship evidence."}'
                )

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "subqueries": ["How exposed is AMD to TSMC supply risk?"],
            "current_subquery_idx": 0,
            "observation_text": "AMD focuses on AI and data center growth.",
            "observation_history": [],
            "tool_call_log": [],
            "round": 0,
        }

        result = nodes.reflect_node(state)

        assert result["sufficient"] is False
        assert result["round"] == 1
        assert result["retry_query"] == (
            "AMD supplier dependency and TSMC supply chain risk"
        )
        assert result["reflection_feedback"] == (
            "Search for supplier relationship evidence."
        )
        assert result["stop_reason"] == "needs_more_evidence"

    def test_reflect_forces_sufficient_at_hard_cap(self):
        state = {
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "subqueries": ["How exposed is AMD to TSMC supply risk?"],
            "current_subquery_idx": 0,
            "observation_text": "AMD focuses on AI and data center growth.",
            "observation_history": [],
            "tool_call_log": [],
            "round": nodes.MAX_REFLECTION_ROUNDS - 1,
        }

        result = nodes.reflect_node(state)

        assert result["sufficient"] is True
        assert result["round"] == nodes.MAX_REFLECTION_ROUNDS
        assert result["stop_reason"] == "max_rounds"
        assert result["retry_query"] == ""
        assert result["reflection_feedback"] == ""

    def test_reflect_fallback_on_invalid_json(
        self, monkeypatch
    ):
        class FakeLLM:
            def invoke(self, _messages):
                return _FakeResponse("not json")

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "subqueries": ["How exposed is AMD to TSMC supply risk?"],
            "current_subquery_idx": 0,
            "observation_text": "AMD focuses on AI and data center growth.",
            "observation_history": [],
            "tool_call_log": [],
            "round": 0,
        }

        result = nodes.reflect_node(state)

        assert result["sufficient"] is False
        assert result["round"] == 1
        assert result["retry_query"] == "How exposed is AMD to TSMC supply risk?"
        assert result["stop_reason"] == "reflection_fallback"
        assert "Reflection fallback:" in result["reflection_reason"]

    def test_route_after_reflect(self):
        assert nodes._route_after_reflect({"sufficient": False}) == "tool_select"
        assert nodes._route_after_reflect({
            "sufficient": True,
            "stop_reason": "sufficient",
            "subqueries": ["q1", "q2"],
            "current_subquery_idx": 0,
        }) == "advance_subquery"
        assert nodes._route_after_reflect({
            "sufficient": True,
            "stop_reason": "sufficient",
            "subqueries": ["q1", "q2"],
            "current_subquery_idx": 1,
        }) == "synthesize"
        assert nodes._route_after_reflect({
            "sufficient": True,
            "stop_reason": "max_rounds",
            "subqueries": ["q1", "q2"],
            "current_subquery_idx": 0,
        }) == "advance_subquery"


class TestAdvanceSubqueryNode:

    def test_advance_subquery_moves_index_and_resets_retry_state(self):
        state = {
            "subqueries": ["Describe AMD strategy", "What is AMD gross margin?"],
            "current_subquery_idx": 0,
            "round": 3,
            "retry_query": "AMD AI strategy",
            "reflection_feedback": "Search more specifically for product strategy.",
            "reflection_reason": "Current evidence is enough for the first subquery.",
            "stop_reason": "sufficient",
            "latest_chunks": [{"chunk_id": "c1", "text": "alpha"}],
            "observation_text": "alpha",
            "completed_subqueries": [],
        }

        result = nodes.advance_subquery_node(state)

        assert result["current_subquery_idx"] == 1
        assert result["round"] == 0
        assert result["retry_query"] == ""
        assert result["reflection_feedback"] == ""
        assert result["reflection_reason"] == ""
        assert result["stop_reason"] == "advance_subquery"
        assert result["latest_chunks"] == []
        assert result["observation_text"] == ""
        assert result["completed_subqueries"] == [{
            "subquery_idx": 0,
            "subquery": "Describe AMD strategy",
            "stop_reason": "sufficient",
            "reflection_reason": "Current evidence is enough for the first subquery.",
            "round": 3,
        }]


class TestDedupeChunksForSynthesis:

    def test_dedupe_prefers_chunk_id_and_preserves_first_seen_order(self):
        chunks = [
            {"chunk_id": "c1", "text": "alpha", "ticker": "AMD"},
            {"chunk_id": "c2", "text": "beta", "ticker": "AMD"},
            {"chunk_id": "c1", "text": "alpha duplicate", "ticker": "AMD"},
            "not a chunk",
            {"chunk_id": "c3", "text": "gamma", "ticker": "AMD"},
        ]

        result = nodes._dedupe_chunks_for_synthesis(chunks)

        assert result == [
            {"chunk_id": "c1", "text": "alpha", "ticker": "AMD"},
            {"chunk_id": "c2", "text": "beta", "ticker": "AMD"},
            {"chunk_id": "c3", "text": "gamma", "ticker": "AMD"},
        ]

    def test_dedupe_uses_content_fingerprint_when_chunk_id_missing(self):
        chunks = [
            {"text": "same text", "ticker": "AMD", "fiscal_year": "2025", "section": "Item_1"},
            {"text": "same text", "ticker": "AMD", "fiscal_year": "2025", "section": "Item_1"},
            {"text": "different text", "ticker": "AMD", "fiscal_year": "2025", "section": "Item_1"},
        ]

        result = nodes._dedupe_chunks_for_synthesis(chunks)

        assert result == [
            {"text": "same text", "ticker": "AMD", "fiscal_year": "2025", "section": "Item_1"},
            {"text": "different text", "ticker": "AMD", "fiscal_year": "2025", "section": "Item_1"},
        ]


class TestSynthesizeNode:

    def test_synthesize_returns_grounded_answer_and_citation_map(
        self, monkeypatch
    ):
        captured = {}

        class FakeLLM:
            def invoke(self, messages):
                captured["messages"] = messages
                return _FakeResponse(
                    "AMD appears exposed to TSMC supply risk through supplier concentration [1]. The evidence also mentions supply chain dependence in the filing [2]."
                )

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())

        state = {
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "stop_reason": "max_rounds",
            "reflection_reason": "Current evidence is partial and does not cover every supplier relationship.",
            "chunks_history": [
                {
                    "chunk_id": "c1",
                    "ticker": "AMD",
                    "fiscal_year": "2025",
                    "section": "Item_1",
                    "text": "AMD depends on external manufacturing partners such as TSMC.",
                },
                {
                    "chunk_id": "c1",
                    "ticker": "AMD",
                    "fiscal_year": "2025",
                    "section": "Item_1",
                    "text": "duplicate should be removed",
                },
                {
                    "chunk_id": "c2",
                    "ticker": "AMD",
                    "fiscal_year": "2025",
                    "section": "Risk_Factors",
                    "text": "Supply chain disruption could affect AMD operations.",
                },
            ],
        }

        result = nodes.synthesize_node(state)

        assert "TSMC supply risk" in result["final_answer"]
        assert result["citation_map"] == [
            {
                "citation_index": 1,
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD depends on external manufacturing partners such as TSMC.",
            },
            {
                "citation_index": 2,
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Risk_Factors",
                "text": "Supply chain disruption could affect AMD operations.",
            },
        ]
        assert "reflection_reason:" in captured["messages"][1]["content"]
        assert "evidence chunks:" in captured["messages"][1]["content"]
        assert "duplicate should be removed" not in captured["messages"][1]["content"]

    def test_synthesize_returns_insufficient_when_no_chunks(self):
        result = nodes.synthesize_node({
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "chunks_history": [],
        })

        assert result == {
            "final_answer": "I do not have enough evidence to answer the question.",
            "citation_map": [],
            "completed_subqueries": [{
                "subquery_idx": 0,
                "subquery": "How exposed is AMD to TSMC supply risk?",
                "stop_reason": "",
                "reflection_reason": "",
                "round": 0,
            }],
        }

    def test_synthesize_returns_fallback_when_llm_raises(
        self, monkeypatch
    ):
        class FailingLLM:
            def invoke(self, _messages):
                raise RuntimeError("llm down")

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FailingLLM())

        result = nodes.synthesize_node({
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "chunks_history": [{
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD depends on external manufacturing partners such as TSMC.",
            }],
        })

        assert result == {
            "final_answer": "I could not synthesize a grounded final answer from the current evidence.",
            "citation_map": [],
            "completed_subqueries": [{
                "subquery_idx": 0,
                "subquery": "How exposed is AMD to TSMC supply risk?",
                "stop_reason": "",
                "reflection_reason": "",
                "round": 0,
            }],
        }
