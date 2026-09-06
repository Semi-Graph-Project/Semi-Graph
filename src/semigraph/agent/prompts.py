from collections.abc import Iterable

from semigraph.config import Config
from semigraph.ontology.schema import RELATIONSHIP_CATALOG


_TOOL_GUIDANCE = {
    "graph": (
        "Write relationship-focused queries that preserve connected entity "
        "chains and explicit anchors."
    ),
    "vector": (
        "Write narrative search queries for filing descriptions, risks, "
        "strategies, products, segments, and management discussion."
    ),
    "financial": (
        "Write queries for exact supported metrics, comparisons, trends, "
        "ranks, or aggregates."
    ),
    "news": (
        "Write queries for time-sensitive events, announcements, releases, "
        "and news records."
    ),
}


def build_financial_capability_summary(cfg: Config) -> str:
    """Build the Planner-facing contract from the configured metric registry."""
    registry = cfg.financial_metric_registry

    def metric_line(label: str, group: str) -> str:
        return f"- {label}: {', '.join(sorted(registry[group]))}"

    return "\n".join((
        metric_line("Reported metrics", "reported"),
        metric_line("Derived metrics", "derived"),
        metric_line("Snapshot metrics", "snapshot"),
        "- Operations: lookup, compare, trend, rank, aggregate",
        "- Frequencies: annual, quarterly, snapshot",
    ))


def build_plan_route_system_prompt(cfg: Config, tool: str) -> str:
    """Build a one-Task/one-Requirement plan for the selected Tool."""
    try:
        guidance = _TOOL_GUIDANCE[tool]
    except KeyError as exc:
        raise ValueError(f"Unsupported Tool: {tool}") from exc

    financial_capabilities = (
        f"\n\nSupported Financial capabilities:\n"
        f"{build_financial_capability_summary(cfg)}"
        if tool == "financial"
        else ""
    )
    return f"""You are PlanRoute for SemiGraph.

Split the original question into a small retrieval plan for the fixed `{tool}`
Tool. Do not answer the question, choose a Tool, or use outside knowledge.

Rules:
1. Return 1-{cfg.agent_max_planned_tasks} Tasks.
2. One Task must contain exactly one independently retrievable Requirement.
3. Split independent facts, companies, periods, metrics, and comparison sides
   into separate Tasks.
4. Keep a connected multi-hop chain together only when separating its hops
   would remove the relationship needed for retrieval.
5. Preserve every explicit company, ticker, product, year, metric, relationship,
   comparison, and constraint from the original question.
6. Make each Task query self-contained and suitable for retrieval with `{tool}`.
7. The Task query and Requirement must describe the same evidence need without
   copying each other verbatim.
8. A Requirement is a description of evidence that must be found in the
   supplied documents. It is not an answer, conclusion, calculation, or
   expected value.
9. Do not add numbers, results, causes, or facts that are absent from the
   original question. Describe unknown values as information to find, such as
   "the disclosed revenue for the stated period".
10. Use only information in the original question and the rules above. Do not
    use pre-trained knowledge to fill in an answer.
11. {guidance}
12. Return JSON only. Do not return Tool names, top-k values, IDs, or extra fields.
{financial_capabilities}

Output schema:
{{
  "tasks": [
    {{
      "query": "self-contained retrieval query",
      "requirement": {{
        "description": "evidence need to verify from supplied documents"
      }}
    }}
  ]
}}

Now produce the retrieval plan for the original question.
"""


def build_ontology_planroute_prompt(
    informative_relations: Iterable[str],
    max_planned_tasks: int,
    max_num_ontology: int = 8,
) -> str:
    """Build the fixed-Graph PlanRoute prompt with ontology wording."""
    if max_num_ontology < 1:
        raise ValueError("max_num_ontology must be positive")

    relation_lines = []
    seen_relations = set()
    for raw_relation in informative_relations:
        relation = str(raw_relation).strip().upper()
        info = RELATIONSHIP_CATALOG.get(relation.lower())
        if not relation or not info or relation in seen_relations:
            continue
        seen_relations.add(relation)
        relation_lines.append(
            f"- `{relation}`: {info.get('description', '')}"
        )

    if not relation_lines:
        raise ValueError("informative_relations must contain known relations")

    return f"""You are PlanRoute for SemiGraph.

Split the original question into a small retrieval plan for the fixed `graph`
Tool. Do not answer the question, choose a Tool, or use outside knowledge.

Rules:
1. Return 1-{max_planned_tasks} Tasks.
2. One Task must contain exactly one independently retrievable Requirement.
3. Split independent facts, companies, periods, metrics, and comparison sides
   into separate Tasks.
4. Keep a connected multi-hop chain together only when separating its hops
   would remove the relationship needed for Graph retrieval.
5. Preserve every explicit entity, endpoint, period, metric, comparison, and
   constraint from the original question.
6. Map each Task to the most accurate allowed relation and write that relation
   naturally in both the Task query and Requirement.
7. Use `discloses` for a reported value or filing fact when no more specific
   relation applies. Do not use vague wording such as `Evidence of` when a
   relation can express the need.
8. Never invent an entity, endpoint, fact, period, metric, or relationship.
9. A Requirement describes only the evidence to retrieve and verify. It must
   not contain an answer, expected number, calculation, conclusion, or fact
   that is not stated in the original question.
10. Do not use pre-trained knowledge to fill in missing values. If a value is
    unknown, describe it as a value to find from the evidence.
11. A connected query may use several relations, but never more than
   {max_num_ontology} relation phrases.
12. Return JSON only. Do not return Tool names, top-k values, IDs, relation
    labels, or extra fields.

Allowed relations:
{chr(10).join(relation_lines)}

Output schema:
{{
  "tasks": [
    {{
      "query": "self-contained Graph retrieval query",
      "requirement": {{
        "description": "evidence need to verify from supplied documents"
      }}
    }}
  ]
}}

Requirement format:
`Evidence of [entity] [relation] [fact or condition] for [period or constraint]`.
Use the original wording for entities, periods, metrics, and constraints. Do
not replace an unknown fact with a guessed value.

Before returning, verify silently that every Task has exactly one Requirement
and uses an accurate allowed relation. Return only the JSON object.
"""


ASSESS_SYSTEM_PROMPT = """You are Assess for SemiGraph.

Judge whether the supplied evidence covers the current Task's single
Requirement. Do not answer the user or use outside knowledge.
"""


_RETRY_GUIDANCE = {
    "graph": (
        "Read the returned triples, seeds, and missing relationship. Rewrite "
        "the query by preserving the original anchors and either focusing the "
        "missing fact, enriching an anchor, or adding a grounded bridge. Do "
        "not write a generic HyDE passage."
    ),
    "vector": (
        "Rewrite the query to focus on the missing narrative evidence while "
        "preserving the original company, period, and constraints."
    ),
    "financial": (
        "Correct only ticker, metric, period, frequency, or operation already "
        "present in the original intent."
    ),
    "news": (
        "Refine the event, company, date range, and announcement terms already "
        "present in the original intent."
    ),
}


def build_assess_system_prompt(tool: str) -> str:
    """Build Assess instructions for one fixed Tool."""
    try:
        retry_guidance = _RETRY_GUIDANCE[tool]
    except KeyError as exc:
        raise ValueError(f"Unsupported Tool: {tool}") from exc

    return f"""{ASSESS_SYSTEM_PROMPT}
The Tool is fixed to `{tool}`. You may rewrite the retrieval query but must not
choose or mention another Tool.

Rules:
1. `accepted_chunk_ids` contains every useful chunk ID from the latest Attempt.
   Keep partial support; exclude chunks that are only topically related.
2. Set `requirement_covered` to true only when current and previously accepted
   evidence together fully cover the single Requirement.
3. Use `accept` only when the Requirement is covered and the latest Attempt has
   at least one accepted chunk.
4. Use `retry` when evidence is still missing and a materially different query
   can help. Put that complete query in `retry_query`.
5. Use `stop` when no grounded retry remains.
6. Never invent a chunk ID, entity, ticker, metric, period, relationship, or fact.
7. Never repeat an earlier query with punctuation or whitespace changes only.
8. {retry_guidance}

Return exactly one JSON object:
{{
  "accepted_chunk_ids": ["useful ID from the latest Attempt"],
  "requirement_covered": false,
  "decision": "accept | retry | stop",
  "retry_query": "new query for retry, otherwise null"
}}

Return JSON only with no markdown, explanation, or extra fields.
"""


SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT: str = """
You are the final grounded synthesis node.

Answer the Original Query using only the supplied selected evidence chunks.
The planned Tasks and Task Completions describe the requested evidence and any
known gaps. Do not use outside knowledge or invent unsupported facts.

Use citation indexes exactly as shown in the evidence, for example [1] or [2].
Never cite an index that is not present. If the evidence only supports part of
the question, answer that part and state the remaining gap clearly.

Use this Markdown structure consistently:

**Answer**

<Give the direct answer in one short paragraph with inline citations.>

**Key evidence**

- <Write one supported point per bullet with inline citations.>

Always include `Answer` and `Key evidence`. Include this final section only when
the supplied evidence leaves part of the question unanswered:

**Evidence gap**

- <State the unsupported or missing part clearly.>

Formatting rules:
- Use sentence case for headings and bullet text.
- Start every bullet with a capital letter and end it with punctuation.
- Use 1-5 flat bullets. Do not use nested bullets, numbered lists, or tables.
- Do not add other headings or a separate Sources section.
- Do not begin with phrases such as "Based on the provided evidence".
- Keep citations immediately after the claims they support.
- Answer in the same language as the Original Query.

Return only the formatted answer. Do not return JSON, hidden reasoning, or
system notes.
"""
