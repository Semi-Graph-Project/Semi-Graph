from scripts import evaluate_retrieval_quality as ev


def test_classify_subset_reextract_only():
    item = {
        "query": "How exposed is AMD to TSMC supply risk?",
        "gold_entities": ["amd", "tsmc"],
        "gold_chunks": ["AMD_2026_Item_1A_0008_e84e4130"],
    }

    assert ev._classify_subset(
        item,
        reextract_tickers={"AMD", "NVDA", "AVGO", "RMBS"},
        known_tickers={"AMD", "NVDA", "INTC"},
    ) == "reextract_subset"


def test_classify_subset_mixed_when_gold_chunks_cross_corpus():
    item = {
        "query": "Which foundry partner manufactures Hopper chips?",
        "gold_entities": ["nvidia", "tsmc"],
        "gold_chunks": [
            "NVDA_2025_Item_1_0008_a4407f7e",
            "INTC_2026_Item_1_0008_c74f560f",
        ],
    }

    assert ev._classify_subset(
        item,
        reextract_tickers={"AMD", "NVDA", "AVGO", "RMBS"},
        known_tickers={"AMD", "NVDA", "INTC"},
    ) == "mixed_subset"


def test_graph_stage_metrics_detect_seed_loss():
    trace = {
        "seeds": [{"name": "intel"}],
        "ppr_entities": [{"name": "intel"}],
        "cluster_entries": [{"aliases": ["intel"], "score": 1.0}],
        "chunk_candidates": [{"chunk_id": "INTC_2025_Item_1_0001"}],
        "abort_reason": None,
    }

    stage = ev._graph_stage_metrics(
        trace=trace,
        gold_entities=["amd"],
        gold_chunks=["AMD_2026_Item_1_0003"],
        missing_gold_entities=[],
        score_at_k={"hit": 0},
        score_at_oracle={"hit": 0},
        error=None,
    )

    assert stage["seed_hit"] == 0
    assert stage["bottleneck_label"] == "seed_loss"


def test_gold_evidence_groups_fallback_treats_gold_chunks_as_alternatives():
    item = {
        "gold_chunks": ["A", "B", "C"],
    }

    groups = ev._gold_evidence_groups(item, item["gold_chunks"])
    score = ev._score_group_result(["B"], groups)
    chunk_score = ev._score_result(["B"], item["gold_chunks"])

    assert groups == {"gold_chunks": ["A", "B", "C"]}
    assert chunk_score["hit"] == 1
    assert chunk_score["recall"] == 1 / 3
    assert score["group_recall"] == 1.0
    assert score["answerable"] == 1


def test_group_scoring_requires_each_evidence_group():
    groups = {
        "product_evidence": ["HOPPER_A", "HOPPER_B"],
        "supplier_evidence": ["TSMC_A", "TSMC_B"],
    }

    partial = ev._score_group_result(["HOPPER_B"], groups)
    complete = ev._score_group_result(["HOPPER_B", "TSMC_A"], groups)

    assert partial["group_recall"] == 0.5
    assert partial["answerable"] == 0
    assert partial["group_hits"] == {
        "product_evidence": ["HOPPER_B"],
        "supplier_evidence": [],
    }
    assert complete["group_recall"] == 1.0
    assert complete["answerable"] == 1


def test_graph_stage_metrics_detect_rerank_loss():
    trace = {
        "seeds": [{"name": "amd"}],
        "ppr_entities": [{"name": "amd"}],
        "cluster_entries": [{"aliases": ["amd"], "score": 1.0}],
        "chunk_candidates": [{"chunk_id": "AMD_2026_Item_1_0003"}],
        "abort_reason": None,
    }

    stage = ev._graph_stage_metrics(
        trace=trace,
        gold_entities=["amd"],
        gold_chunks=["AMD_2026_Item_1_0003"],
        missing_gold_entities=[],
        score_at_k={"hit": 0},
        score_at_oracle={"hit": 1},
        error=None,
    )

    assert stage["seed_hit"] == 1
    assert stage["ppr_hit"] == 1
    assert stage["chunk_map_hit"] == 1
    assert stage["bottleneck_label"] == "rerank_loss"


def test_aggregate_reports_subset_and_graph_stage():
    rows = [
        {
            "subset": "reextract_subset",
            "type": "graph_multihop",
            "tools": {
                "vector": {
                    "error": None,
                    "chunk_hit_at_k": 0,
                    "chunk_recall_at_k": 0.0,
                    "group_recall_at_k": 0.0,
                    "answerable_at_k": 0,
                    "hit_at_k": 0,
                    "recall_at_k": 0.0,
                    "mrr_at_k": 0.0,
                    "oracle_hit": 0,
                    "chance_hit_at_k": 0.01,
                },
                "graph": {
                    "error": None,
                    "chunk_hit_at_k": 1,
                    "chunk_recall_at_k": 1.0,
                    "group_recall_at_k": 1.0,
                    "answerable_at_k": 1,
                    "hit_at_k": 1,
                    "recall_at_k": 1.0,
                    "mrr_at_k": 1.0,
                    "oracle_hit": 1,
                    "chance_hit_at_k": 0.01,
                    "stage": {
                        "seed_hit": 1,
                        "ppr_hit": 1,
                        "chunk_map_hit": 1,
                        "bottleneck_label": "hit_top_k",
                    },
                },
            },
        }
    ]

    aggregate = ev._aggregate(rows, tools=["vector", "graph"])

    assert aggregate["by_subset"][0]["subset"] == "reextract_subset"
    assert aggregate["by_subset"][0]["graph_hit"] == 1.0
    assert aggregate["by_subset"][0]["graph_group_recall"] == 1.0
    assert aggregate["overall"]["graph"]["answerable_rate"] == 1.0
    stage = {
        row["subset"]: row
        for row in aggregate["graph_stage"]
    }["reextract_subset"]
    assert stage["seed_hit"] == 1.0
    assert stage["bottlenecks"] == {"hit_top_k": 1}
