from semigraph.agent.graph import build_agent
import semigraph.agent.nodes as nodes


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeToolResponse:
    def __init__(self, name: str, args: dict):
        self.tool_calls = [{
            "name": name,
            "args": args,
        }]


class TestPhaseDGraphIntegration:

    def test_graph_completes_single_pass_and_strips_invalid_citations(
        self, monkeypatch
    ):
        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["Describe AMD strategy"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    return _FakeToolResponse(
                        "vector",
                        {"query": "AMD strategy"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    return _FakeResponse(
                        "AMD focuses on AI accelerators and data center growth."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"sufficient": true, "reason": "Evidence is enough to answer.", "retry_query": "", "feedback": ""}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    return _FakeResponse(
                        "AMD focuses on AI accelerators [1]. Unsupported extra citation [99]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_vector(query: str, top_k_chunks: int, cfg):
            assert query == "AMD strategy"
            assert top_k_chunks == nodes.DEFAULT_TOP_K
            return [{
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD is focused on AI accelerators and data center expansion.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setitem(nodes.RETRIEVERS, "vector", fake_vector)

        graph = build_agent()
        result = graph.invoke({"original_query": "What is AMD strategy?"})

        assert result["final_answer"] == "AMD focuses on AI accelerators [1]. Unsupported extra citation."
        assert result["citation_map"] == [{
            "citation_index": 1,
            "chunk_id": "c1",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1",
            "text": "AMD is focused on AI accelerators and data center expansion.",
        }]
        assert result["round"] == 1
        assert result["stop_reason"] == "sufficient"
        assert len(result["tool_call_log"]) == 1
        assert len(result["reflection_history"]) == 1

    def test_graph_retries_once_with_reflection_feedback_then_synthesizes(
        self, monkeypatch
    ):
        calls = {"tool_select": 0, "reflect": 0}

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]
                user = messages[1]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["How exposed is AMD to TSMC supply risk?"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    calls["tool_select"] += 1
                    if "Reflection feedback:" in user:
                        assert "supplier relationship evidence" in user
                        return _FakeToolResponse(
                            "graph",
                            {"query": "AMD supplier dependency and TSMC supply chain risk"},
                        )
                    return _FakeToolResponse(
                        "vector",
                        {"query": "AMD strategy"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    if "Selected tool: graph" in user:
                        return _FakeResponse(
                            "The evidence shows AMD relies on TSMC as an external manufacturing partner."
                        )
                    return _FakeResponse(
                        "The evidence only describes AMD strategy and does not address supplier exposure."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    calls["reflect"] += 1
                    if calls["reflect"] == 1:
                        return _FakeResponse(
                            '{"sufficient": false, "reason": "Current evidence covers strategy but not supplier exposure.", "retry_query": "AMD supplier dependency and TSMC supply chain risk", "feedback": "Search for supplier relationship evidence."}'
                        )
                    return _FakeResponse(
                        '{"sufficient": true, "reason": "Evidence now covers supplier dependency.", "retry_query": "", "feedback": ""}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    assert "reflection_reason: Evidence now covers supplier dependency." in user
                    return _FakeResponse(
                        "AMD appears exposed to TSMC supply risk because its evidence mentions reliance on an external manufacturing partner [1]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_vector(query: str, top_k_chunks: int, cfg):
            return [{
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD describes its AI and data center strategy.",
            }]

        def fake_graph(query: str, top_k_chunks: int, cfg):
            assert query == "AMD supplier dependency and TSMC supply chain risk"
            return [{
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Risk_Factors",
                "text": "AMD relies on TSMC as an external manufacturing partner.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setitem(nodes.RETRIEVERS, "vector", fake_vector)
        monkeypatch.setitem(nodes.RETRIEVERS, "graph", fake_graph)

        graph = build_agent()
        result = graph.invoke({
            "original_query": "How exposed is AMD to TSMC supply risk?",
        })

        assert result["final_answer"].startswith(
            "AMD appears exposed to TSMC supply risk"
        )
        assert result["round"] == 2
        assert result["stop_reason"] == "sufficient"
        assert result["tool_call_log"] == [
            {
                "round": 0,
                "subquery": "How exposed is AMD to TSMC supply risk?",
                "tool": "vector",
                "query": "AMD strategy",
                "top_k_chunks": nodes.DEFAULT_TOP_K,
                "n_chunks": 1,
                "status": "ok",
            },
            {
                "round": 1,
                "subquery": "How exposed is AMD to TSMC supply risk?",
                "tool": "graph",
                "query": "AMD supplier dependency and TSMC supply chain risk",
                "top_k_chunks": nodes.DEFAULT_TOP_K,
                "n_chunks": 1,
                "status": "ok",
            },
        ]
        assert len(result["reflection_history"]) == 2
        assert result["reflection_history"][0]["stop_reason"] == "needs_more_evidence"
        assert result["reflection_history"][1]["stop_reason"] == "sufficient"
        assert result["citation_map"] == [{
            "citation_index": 1,
            "chunk_id": "c2",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Risk_Factors",
            "text": "AMD relies on TSMC as an external manufacturing partner.",
        }]

    def test_graph_processes_all_subqueries_before_synthesizing(
        self, monkeypatch
    ):
        calls = {"tool_select": 0, "reflect": 0}
        observed_tools = []

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]
                user = messages[1]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["What does AMD say about AI strategy?", "What is AMD gross margin for the last 4 fiscal quarters?"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    calls["tool_select"] += 1
                    if "gross margin" in user:
                        return _FakeToolResponse(
                            "financial",
                            {"query": "AMD gross margin last 4 fiscal quarters"},
                        )
                    return _FakeToolResponse(
                        "vector",
                        {"query": "AMD AI strategy"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    if "Selected tool: financial" in user:
                        observed_tools.append("financial")
                        return _FakeResponse(
                            "The evidence reports AMD gross margin figures across recent fiscal quarters."
                        )
                    observed_tools.append("vector")
                    return _FakeResponse(
                        "The evidence says AMD is focusing on AI accelerators and data center strategy."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    calls["reflect"] += 1
                    if "Current subquery: What is AMD gross margin for the last 4 fiscal quarters?" in user:
                        return _FakeResponse(
                            '{"sufficient": true, "reason": "Current evidence is sufficient for the gross margin subquery.", "retry_query": "", "feedback": ""}'
                        )
                    return _FakeResponse(
                        '{"sufficient": true, "reason": "Current evidence is sufficient for the AI strategy subquery.", "retry_query": "", "feedback": ""}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    assert "subquery_1:" in user
                    assert "subquery_2:" in user
                    return _FakeResponse(
                        "AMD says it is focusing on AI accelerators and data center strategy [1]. Its recent gross margin figures are also available in the retrieved financial evidence [2]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_vector(query: str, top_k_chunks: int, cfg):
            assert query == "AMD AI strategy"
            return [{
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD is focusing on AI accelerators and data center strategy.",
            }]

        def fake_financial(query: str, top_k_chunks: int, cfg):
            assert query == "AMD gross margin last 4 fiscal quarters"
            return [{
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "financial_metrics",
                "text": "AMD gross margin figures are available for the last four fiscal quarters.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setitem(nodes.RETRIEVERS, "vector", fake_vector)
        monkeypatch.setitem(nodes.RETRIEVERS, "financial", fake_financial)

        graph = build_agent()
        result = graph.invoke({
            "original_query": "What does AMD say about AI strategy, and what is AMD gross margin for the last 4 fiscal quarters?",
        })

        assert observed_tools == ["vector", "financial"]
        assert calls["tool_select"] == 2
        assert calls["reflect"] == 2
        assert result["current_subquery_idx"] == 1
        assert result["completed_subqueries"] == [
            {
                "subquery_idx": 0,
                "subquery": "What does AMD say about AI strategy?",
                "stop_reason": "sufficient",
                "reflection_reason": "Current evidence is sufficient for the AI strategy subquery.",
                "round": 1,
            },
            {
                "subquery_idx": 1,
                "subquery": "What is AMD gross margin for the last 4 fiscal quarters?",
                "stop_reason": "sufficient",
                "reflection_reason": "Current evidence is sufficient for the gross margin subquery.",
                "round": 1,
            },
        ]
        assert len(result["tool_call_log"]) == 2
        assert result["citation_map"] == [
            {
                "citation_index": 1,
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1",
                "text": "AMD is focusing on AI accelerators and data center strategy.",
            },
            {
                "citation_index": 2,
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "financial_metrics",
                "text": "AMD gross margin figures are available for the last four fiscal quarters.",
            },
        ]

    def test_graph_advances_to_next_subquery_after_max_rounds(
        self, monkeypatch
    ):
        reflect_calls = {"supplier": 0, "revenue": 0}

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]
                user = messages[1]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["What supplier dependence does AMD have?", "What is AMD revenue?"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    if "What is AMD revenue?" in user:
                        return _FakeToolResponse(
                            "financial",
                            {"query": "AMD revenue"},
                        )
                    return _FakeToolResponse(
                        "graph",
                        {"query": "AMD supplier dependence"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    if "Selected tool: financial" in user:
                        return _FakeResponse(
                            "The evidence reports AMD revenue."
                        )
                    return _FakeResponse(
                        "The evidence is still too generic to pin down supplier dependence."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    if "Current subquery: What is AMD revenue?" in user:
                        reflect_calls["revenue"] += 1
                        return _FakeResponse(
                            '{"sufficient": true, "reason": "Current evidence is sufficient for the revenue subquery.", "retry_query": "", "feedback": ""}'
                        )
                    reflect_calls["supplier"] += 1
                    return _FakeResponse(
                        '{"sufficient": false, "reason": "Still missing specific supplier dependence evidence.", "retry_query": "AMD supplier dependence", "feedback": "Use the graph retriever again."}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    assert "stop_reason: max_rounds" in user
                    return _FakeResponse(
                        "Based on the evidence available so far, AMD revenue is available [2], but supplier dependence remains only partially supported [1]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_graph(query: str, top_k_chunks: int, cfg):
            return [{
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Risk_Factors",
                "text": "AMD discusses supply chain dependence in general terms.",
            }]

        def fake_financial(query: str, top_k_chunks: int, cfg):
            return [{
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "financial_metrics",
                "text": "AMD revenue is reported in its financial results.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setitem(nodes.RETRIEVERS, "graph", fake_graph)
        monkeypatch.setitem(nodes.RETRIEVERS, "financial", fake_financial)

        graph = build_agent()
        result = graph.invoke({
            "original_query": "What supplier dependence does AMD have, and what is AMD revenue?",
        })

        assert reflect_calls["supplier"] == nodes.MAX_REFLECTION_ROUNDS - 1
        assert reflect_calls["revenue"] == 1
        assert result["stop_reason"] == "sufficient"
        assert result["completed_subqueries"] == [
            {
                "subquery_idx": 0,
                "subquery": "What supplier dependence does AMD have?",
                "stop_reason": "max_rounds",
                "reflection_reason": (
                    f"Forced stop at round {nodes.MAX_REFLECTION_ROUNDS}: reached max reflection rounds "
                    f"({nodes.MAX_REFLECTION_ROUNDS})."
                ),
                "round": nodes.MAX_REFLECTION_ROUNDS,
            },
            {
                "subquery_idx": 1,
                "subquery": "What is AMD revenue?",
                "stop_reason": "sufficient",
                "reflection_reason": "Current evidence is sufficient for the revenue subquery.",
                "round": 1,
            },
        ]
        assert len(result["tool_call_log"]) == nodes.MAX_REFLECTION_ROUNDS + 1
        assert result["citation_map"] == [
            {
                "citation_index": 2,
                "chunk_id": "c2",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "financial_metrics",
                "text": "AMD revenue is reported in its financial results.",
            },
            {
                "citation_index": 1,
                "chunk_id": "c1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Risk_Factors",
                "text": "AMD discusses supply chain dependence in general terms.",
            },
        ]

    def test_graph_synthesis_keeps_financial_chunk_after_news_noise(
        self, monkeypatch
    ):
        calls = {"tool_select": 0, "reflect": 0}

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]
                user = messages[1]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["What is AMD latest FY2025 revenue?"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    calls["tool_select"] += 1
                    if calls["tool_select"] == 1:
                        return _FakeToolResponse(
                            "news",
                            {"query": "AMD latest revenue news"},
                        )
                    return _FakeToolResponse(
                        "financial",
                        {"query": "AMD FY2025 revenue"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    if "Selected tool: financial" in user:
                        return _FakeResponse(
                            "The evidence directly reports AMD FY2025 revenue."
                        )
                    return _FakeResponse(
                        "The retrieval mostly contains recent news snippets and does not report the annual revenue figure."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    calls["reflect"] += 1
                    if calls["reflect"] == 1:
                        return _FakeResponse(
                            '{"sufficient": false, "reason": "Current evidence is noisy news coverage and does not provide the FY2025 revenue number.", "retry_query": "AMD FY2025 revenue", "feedback": "Use the financial retriever for the annual metric."}'
                        )
                    return _FakeResponse(
                        '{"sufficient": true, "reason": "Current evidence is sufficient for AMD FY2025 revenue.", "retry_query": "", "feedback": ""}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    assert "AMD FY2025 revenue was $100 billion." in user
                    return _FakeResponse(
                        "AMD FY2025 revenue was $100 billion [1]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_news(query: str, top_k_chunks: int, cfg):
            assert query == "AMD latest revenue news"
            return [
                {
                    "chunk_id": f"news_{i}",
                    "ticker": "AMD",
                    "fiscal_year": "2025",
                    "section": "news",
                    "text": f"News noise chunk {i} about market reactions.",
                }
                for i in range(1, 9)
            ]

        def fake_financial(query: str, top_k_chunks: int, cfg):
            assert query == "AMD FY2025 revenue"
            return [{
                "chunk_id": "fin_1",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "financial_metrics",
                "text": "AMD FY2025 revenue was $100 billion.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setattr(nodes, "_should_force_financial_tool", lambda *args: False)
        monkeypatch.setitem(nodes.RETRIEVERS, "news", fake_news)
        monkeypatch.setitem(nodes.RETRIEVERS, "financial", fake_financial)

        graph = build_agent()
        result = graph.invoke({
            "original_query": "What is AMD latest FY2025 revenue?",
        })

        assert result["final_answer"] == "AMD FY2025 revenue was $100 billion [1]."
        assert result["citation_map"] == [{
            "citation_index": 1,
            "chunk_id": "fin_1",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "financial_metrics",
            "text": "AMD FY2025 revenue was $100 billion.",
        }]

    def test_graph_forces_exit_at_max_rounds(
        self, monkeypatch
    ):
        calls = {"reflect": 0}

        class FakeLLM:
            def bind_tools(self, _schemas):
                return self

            def invoke(self, messages):
                system = messages[0]["content"]

                if system == nodes.PLANNER_SYSTEM_PROMPT:
                    return _FakeResponse(
                        '{"subqueries": ["How exposed is AMD to TSMC supply risk?"]}'
                    )
                if system == nodes.TOOL_SELECT_SYSTEM_PROMPT:
                    return _FakeToolResponse(
                        "vector",
                        {"query": "AMD supply risk"},
                    )
                if system == nodes.OBSERVE_SYSTEM_PROMPT:
                    return _FakeResponse(
                        "The evidence remains partial and does not fully answer the question."
                    )
                if system == nodes.REFLECT_SYSTEM_PROMPT:
                    calls["reflect"] += 1
                    return _FakeResponse(
                        '{"sufficient": false, "reason": "Still missing supplier dependence evidence.", "retry_query": "AMD TSMC dependence", "feedback": "Search more directly for supplier dependence."}'
                    )
                if system == nodes.SYNTHESIZE_SYSTEM_PROMPT:
                    return _FakeResponse(
                        "Based on the evidence available so far, the answer remains partial [1]."
                    )
                raise AssertionError(f"Unexpected prompt: {system}")

        def fake_vector(query: str, top_k_chunks: int, cfg):
            return [{
                "chunk_id": f"c_{query}",
                "ticker": "AMD",
                "fiscal_year": "2025",
                "section": "Item_1A",
                "text": "AMD discusses supply chain risks in general terms.",
            }]

        monkeypatch.setattr(nodes, "get_config", lambda: "cfg-sentinel")
        monkeypatch.setattr(nodes, "get_llm", lambda cfg: FakeLLM())
        monkeypatch.setitem(nodes.RETRIEVERS, "vector", fake_vector)

        graph = build_agent()
        result = graph.invoke({
            "original_query": "How exposed is AMD to TSMC supply risk?",
        })

        assert result["stop_reason"] == "max_rounds"
        assert result["round"] == nodes.MAX_REFLECTION_ROUNDS
        assert len(result["tool_call_log"]) == nodes.MAX_REFLECTION_ROUNDS
        assert len(result["reflection_history"]) == nodes.MAX_REFLECTION_ROUNDS
        assert result["reflection_history"][-1]["stop_reason"] == "max_rounds"
        assert calls["reflect"] == nodes.MAX_REFLECTION_ROUNDS - 1
