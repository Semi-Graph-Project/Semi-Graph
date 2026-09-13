from collections.abc import Callable

from semigraph.config import Config
from semigraph.online.graph_search import graph_search
from semigraph.online.vector_search import vector_search


def retrieve_vector(
    *,
    query: str,
    top_k_chunks: int,
    cfg: Config,
) -> list[dict]:
    """Run Vector retrieval with the configured Agent profile."""
    profile = cfg.agent_retrieval["vector"]
    return vector_search(
        query=query,
        top_k_chunks=top_k_chunks,
        candidate_pool_k=int(profile.get("candidate_pool_k", top_k_chunks)),
        vector_index=str(profile.get("vector_index", "chunk_embedding")),
        cfg=cfg,
    )


def retrieve_graph(
    *,
    query: str,
    top_k_chunks: int,
    cfg: Config,
) -> list[dict]:
    """Run Graph retrieval with the configured Agent profile."""
    profile = cfg.agent_retrieval["graph"]
    return graph_search(
        query=query,
        top_k_chunks=top_k_chunks,
        top_k_entities=int(profile.get("top_k_entities", 20)),
        damping=float(profile.get("damping", 0.5)),
        top_k_triples=int(profile.get("top_k_triples", 8)),
        top_k_chunk_seeds=int(profile.get("top_k_chunk_seeds", 5)),
        chunk_seed_vector_index=str(
            profile.get("chunk_seed_vector_index", "chunk_embedding")
        ),
        use_expansion=bool(profile.get("use_expansion", True)),
        seed_mode=str(profile.get("seed_mode", "triple")),
        candidate_pool_k=int(profile.get("candidate_pool_k", 100)),
        ppr_seed_weight_mode=str(
            profile.get("ppr_seed_weight_mode", "uniform")
        ),
        graph_triple_filter=str(profile.get("triple_filter", "none")),
        cfg=cfg,
    )


RETRIEVERS: dict[str, Callable[..., list[dict]]] = {
    "vector": retrieve_vector,
    "graph": retrieve_graph,
}
