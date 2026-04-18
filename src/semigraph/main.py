from semigraph.offline.chunker import chunk_filing
from semigraph.offline.kg_extract import extract_entities_gliner
from semigraph.config import get_config
from semigraph.offline.chunker import chunk_section
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


if __name__ == "__main__":

    #load NVDA item_1.md

    with open("/home/kantinan/programming/project/data/processed/NVDA/FY2026-10K/Item_1.md", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_section(text, ticker="NVDA", fiscal_year="2026", section="Item_1")
    
    print(chunks[2].text)
    entities = extract_entities_gliner(chunks[0].text, section="Item_1",threshold=0.3)
    print("----------")
    for e in entities:
        print(f"  [{e.label}] {e.text}")

    
