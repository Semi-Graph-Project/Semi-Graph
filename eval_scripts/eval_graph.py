
from pathlib import Path
import json
import sys
import statistics
import time

from dotenv import load_dotenv
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402
from semigraph.online.graph_search import graph_search as production_graph_search  # noqa: E402



def graph_search(question: str, top_k: int = 5) -> list[dict]:
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri

    profile = cfg.agent_retrieval["graph"]

    return production_graph_search(
        question,
        top_k_chunks=top_k,
        top_k_entities=int(profile["top_k_entities"]),
        top_k_triples=int(profile["top_k_triples"]),
        top_k_chunk_seeds=int(profile.get("top_k_chunk_seeds", 5)),
        chunk_seed_vector_index="gold_chunk_embedding",
        damping=float(profile["damping"]),
        use_expansion=bool(profile["use_expansion"]),
        seed_mode=str(profile["seed_mode"]),
        candidate_pool_k=int(profile["candidate_pool_k"]),
        ppr_seed_weight_mode=str(profile["ppr_seed_weight_mode"]),
        ppr_graph_mode=str(profile["ppr_graph_mode"]),
        graph_triple_filter=str(profile["triple_filter"]),
        cfg=cfg,
    )


result = graph_search("What are the risks of AMD's reliance on TSMC for chip manufacturing?", top_k=5)

print(result)
