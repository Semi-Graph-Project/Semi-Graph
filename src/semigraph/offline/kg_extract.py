
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """A named entity detected by GLiNER.
        \n\n
        Attr:
            text
            label
            score
    """
    text: str
    label: str      # matches NODE_CATALOG key e.g. "Company", "RiskFactor"
    score: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Stage 1 — GLiNER entity detection
# ---------------------------------------------------------------------------

# Map ontology node types → GLiNER-friendly label strings
# GLiNER uses these strings as "entity type" prompts to the model
GLINER_LABEL_MAP: dict[str, str] = {
    "Company":            "company or corporation",
    "BusinessSegment":    "business segment or division",
    "Product":            "product or platform",
    "Technology":         "technology or architecture",
    "GeographicMarket":   "country or geographic region",
    "Industry":           "industry or market sector",
    "RiskFactor":         "risk factor or business risk",
    "Executive":          "executive officer or board director",
    "StrategicInitiative": "strategic initiative or program",
    "FiscalYear":          "fiscal year or annual reporting period",
}

# Inverted map: gliner label string → ontology key
_LABEL_TO_ONTOLOGY = {v: k for k, v in GLINER_LABEL_MAP.items()}

# Derive section → node types from schema.py (single source of truth)
# schema uses "Item 1" (space), chunker uses "Item_1" (underscore) — translate on load
from semigraph.ontology.schema import SECTION_CONFIG  # noqa: E402

SECTION_LABELS: dict[str, list[str]] = {
    section.replace(" ", "_"): cfg["nodes"]
    for section, cfg in SECTION_CONFIG.items()
}

_gliner_model = None  # module-level cache — load once, reuse


def _get_gliner_model(model_name: str = "urchade/gliner_medium-v2.1"):
    """Lazy-load GLiNER model. Cached after first call."""
    global _gliner_model
    if _gliner_model is None:
        try:
            from gliner import GLiNER  # type: ignore
            print(f"[GLiNER] Loading model: {model_name}")
            _gliner_model = GLiNER.from_pretrained(model_name)
            print("[GLiNER] Model ready.")
        except ImportError as e:
            raise ImportError(
                "GLiNER not installed. Run: pip install gliner"
            ) from e
    return _gliner_model


def extract_entities_gliner(
    text: str,
    section: str,
    threshold: float = 0.4,
    model_name: str = "urchade/gliner_medium-v2.1",
) -> List[Entity]:
    """
    Stage 1: Detect named entities from chunk text using GLiNER.

    Args:
        text:       Raw chunk text (markdown stripped ideally).
        section:    Section key e.g. "Item_1A" — controls which labels to detect.
        threshold:  Minimum confidence score (default 0.4).
        model_name: HuggingFace model id for GLiNER.

    Returns:
        List[Entity] deduplicated by (text, label).
    """
    ontology_keys = SECTION_LABELS.get(section, list(GLINER_LABEL_MAP.keys()))
    gliner_labels = [GLINER_LABEL_MAP[k] for k in ontology_keys if k in GLINER_LABEL_MAP]

    if not gliner_labels:
        return []

    model = _get_gliner_model(model_name)

    # GLiNER has an internal token limit (~512); predict_entities handles long text
    # by sliding window when the model supports it, but we keep chunks ≤4500 chars
    # so this is within safe limits for the medium model.
    raw = model.predict_entities(text, gliner_labels, threshold=threshold)

    seen: set[tuple[str, str]] = set()
    entities: List[Entity] = []

    for hit in raw:
        ontology_label = _LABEL_TO_ONTOLOGY.get(hit["label"], hit["label"])
        key = (hit["text"].strip(), ontology_label)
        if key in seen:
            continue
        seen.add(key)
        entities.append(Entity(
            text=hit["text"].strip(),
            label=ontology_label,
            score=round(hit["score"], 4),
        ))

    return entities
