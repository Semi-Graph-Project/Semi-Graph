from semigraph.benchmark.finreflectkg import (
    canonical_chunk_id,
    convert_question,
    gold_entity_aliases,
    is_conservative_entity_alias,
    normalize_entity_type,
    normalize_relation_type,
    question_tickers,
    strict_ticker_questions,
)


def _question():
    return {
        "question_id": 7,
        "question": "How are the two disclosures connected?",
        "answer": "By two cited facts.",
        "pattern": "ORG -> Discloses -> FIN_METRIC -> Impacted_By -> EVENT",
        "hop_count": 2,
        "document_relationship": "inter_document_same_company",
        "path_data": {
            "start_node": {"name": "CSCO", "type": "ORG"},
            "intermediate_node": {"name": "Revenue", "type": "FIN_METRIC"},
            "end_node": {"name": "Acquisition", "type": "EVENT"},
            "hop_1_rel": {
                "source_file": "CSCO_10k_2024.pdf",
                "page_id": "page_10",
                "chunk_id": "chunk_1",
            },
            "hop_2_rel": {
                "source_file": "CSCO_10k_2023.pdf",
                "page_id": "page_20",
                "chunk_id": "chunk_2",
            },
        },
    }


def test_canonical_chunk_id_is_global():
    assert canonical_chunk_id("CSCO_10k_2024.pdf", "page_76", "chunk_4") == (
        "CSCO_10k_2024.pdf::page_76::chunk_4"
    )


def test_ontology_normalization_keeps_reference_schema_clean():
    assert normalize_relation_type("produce") == "PRODUCES"
    assert normalize_relation_type("works_for") == "WORKS_FOR"
    assert normalize_relation_type("arbitrary free-form verb") is None
    assert normalize_entity_type("regulative_requirement") == "REGULATORY_REQUIREMENT"
    assert normalize_entity_type("made_up_type") is None


def test_question_tickers_are_derived_from_evidence_files():
    assert question_tickers([_question()]) == {"CSCO"}


def test_strict_ticker_filter_requires_every_evidence_source_in_scope():
    csco_only = _question()
    cross_company = _question()
    cross_company["question_id"] = 8
    cross_company["path_data"]["hop_2_rel"]["source_file"] = "AAPL_10k_2023.pdf"

    selected = strict_ticker_questions([csco_only, cross_company], {"CSCO"})

    assert [question["question_id"] for question in selected] == [7]


def test_converter_creates_one_required_group_per_hop():
    question = _question()
    available = {
        "CSCO_10k_2024.pdf::page_10::chunk_1",
        "CSCO_10k_2023.pdf::page_20::chunk_2",
    }
    converted = convert_question(question, available)

    assert converted is not None
    assert converted["id"] == "FRKG007"
    assert converted["gold_evidence_groups"] == {
        "hop_1": ["CSCO_10k_2024.pdf::page_10::chunk_1"],
        "hop_2": ["CSCO_10k_2023.pdf::page_20::chunk_2"],
    }
    assert converted["gold_entities"] == ["csco", "revenue", "acquisition"]


def test_converter_skips_question_when_evidence_is_missing():
    assert convert_question(_question(), set()) is None


def test_conservative_aliases_cover_morphology_company_and_segment_suffixes():
    assert is_conservative_entity_alias(
        "deferred tax assets and liabilities",
        "deferred tax asset and liability",
        "FIN_METRIC",
    )
    assert is_conservative_entity_alias("intc", "intel", "ORG")
    assert is_conservative_entity_alias("other segment", "other", "SEGMENT")
    assert not is_conservative_entity_alias("other segment", "other", "FIN_METRIC")
    assert not is_conservative_entity_alias(
        "kirsten m. spears",
        "kirsten m. spear",
        "PERSON",
    )
    assert not is_conservative_entity_alias(
        "net revenue",
        "net revenue %",
        "FIN_METRIC",
    )


def test_gold_aliases_require_same_type_and_gold_chunk_provenance():
    question = _question()
    question["path_data"]["start_node"] = {"name": "INTC", "type": "ORG"}
    question["path_data"]["intermediate_node"] = {
        "name": "Revenues",
        "type": "FIN_METRIC",
    }
    chunk_1 = "CSCO_10k_2024.pdf::page_10::chunk_1"
    aliases = gold_entity_aliases(
        question,
        [chunk_1, "CSCO_10k_2023.pdf::page_20::chunk_2"],
        {
            chunk_1: {
                ("revenue", "FIN_METRIC"),
                ("revenue", "SEGMENT"),
            }
        },
        all_graph_entities={("intel", "COMP")},
    )

    assert aliases == {
        "intc": ["intel"],
        "revenues": ["revenue"],
    }
