"""Ranking strategies for retrieved chunks."""

from __future__ import annotations

import re
from enum import Enum

import numpy as np

from semigraph.config import Config, get_config
from semigraph.online.cross_encoder_runtime import predict_cross_encoder_scores


class RerankMode(str, Enum):
    METADATA = "company+fiscal_year"
    CROSS_ENCODER = "cross_encoder"


def company_rerank(
    query: str,
    chunks: list[dict],
    cfg: Config | None = None,
    boost: float = 1.25,
) -> list[dict]:
    """Boost chunks whose ID prefix matches a company named in the query."""
    cfg = cfg or get_config()
    normalized_query = f" {' '.join(re.findall(r'[a-z0-9]+', query.lower()))} "
    explicit_tickers = set(re.findall(r"\b[A-Z]{2,5}\b", query))
    company_names = getattr(cfg, "graph_repair_filer_aliases", {})
    known_tickers = {
        str(ticker).upper()
        for ticker in getattr(cfg, "tickers", company_names)
    }
    matched_tickers = explicit_tickers & known_tickers
    matched_tickers.update({
        str(ticker).upper()
        for ticker, name in company_names.items()
        if f" {' '.join(re.findall(r'[a-z0-9]+', str(name).lower()))} "
        in normalized_query
    })
    if not matched_tickers:
        return chunks

    reranked: list[dict] = []
    for chunk in chunks:
        item = dict(chunk)
        chunk_id = str(item.get("chunk_id") or "").upper()
        if any(chunk_id.startswith(f"{ticker}_") for ticker in matched_tickers):
            item["score"] = float(item.get("score") or 0.0) * boost
        reranked.append(item)

    return sorted(
        reranked,
        key=lambda item: float(item.get("score") or 0.0),
        reverse=True,
    )


def fiscal_year_rerank(
    query: str,
    chunks: list[dict],
    boost: float = 1.15,
) -> list[dict]:
    """Boost chunks whose fiscal year is explicitly mentioned in the query."""
    query_years = {
        int(year)
        for year in re.findall(r"\b20\d{2}\b", query)
    }
    if not query_years:
        return chunks

    reranked: list[dict] = []
    for chunk in chunks:
        item = dict(chunk)
        try:
            fiscal_year = int(item.get("fiscal_year"))
        except (TypeError, ValueError):
            fiscal_year = None
        if fiscal_year in query_years:
            item["score"] = float(item.get("score") or 0.0) * boost
        reranked.append(item)

    return sorted(
        reranked,
        key=lambda item: float(item.get("score") or 0.0),
        reverse=True,
    )


def cross_encoder_rerank(
    query: str,
    chunks: list[dict],
) -> list[dict]:
    """Rerank chunks using a cross-encoder model."""

    if not chunks:
        return []

    pairs: list[tuple[str, str]] = []
    for index, chunk in enumerate(chunks):
        text = chunk.get("text")
        if not isinstance(text, str):
            raise ValueError(f"chunks[{index}]['text'] must be a string")
        pairs.append((query, text))

    scores = predict_cross_encoder_scores(pairs)
    scores = np.asarray(scores, dtype=float).reshape(-1)
    if len(scores) != len(chunks):
        raise ValueError(
            "Cross-encoder returned "
            f"{len(scores)} scores for {len(chunks)} chunks"
        )
    if not np.isfinite(scores).all():
        raise ValueError("Cross-encoder returned a non-finite score")

    ranking = np.argsort(-scores)

    return [chunks[i] for i in ranking]
