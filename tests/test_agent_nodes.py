import semigraph.agent.nodes as nodes


def test_synthesis_formatter_keeps_full_chunk_text():
    chunk = {
        "chunk_id": "C1",
        "text": "start-" + "x" * 3_000 + "-important-tail",
    }

    formatted, _ = nodes._format_chunks_for_synthesis([chunk])

    assert "-important-tail" in formatted
