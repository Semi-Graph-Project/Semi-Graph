from dotenv import load_dotenv

from semigraph.offline.chunker import chunk_section
from semigraph.offline.kg_extract import extract_chunk

load_dotenv()


if __name__ == "__main__":
    section_path = "/home/kantinan/programming/project/data/processed/NVDA/FY2026-10K/Item_1.md"
    with open(section_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_section(text, ticker="NVDA", fiscal_year="2026", section="Item_1")
    print(f"Total chunks: {len(chunks)}")

    result = extract_chunk(chunks[0].text, section="Item_1")
    print(f"\nNodes: {len(result.nodes)}")
    for n in result.nodes:
        print(f"  [{n.type}] {n.id}")

    print(f"\nRelationships: {len(result.relationships)}")
    for r in result.relationships:
        print(f"  ({r.source} :{r.source_type}) -[:{r.type}]-> ({r.target} :{r.target_type})")
