import os
import time
from dotenv import load_dotenv
from typing_extensions import Doc

load_dotenv()

from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph
from concurrent.futures import ThreadPoolExecutor, as_completed


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


llm = ChatOpenAI(
    model="deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.0
)
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=3000,  # Increased from 1500
    chunk_overlap=400, 
    length_function=len,
    separators=["\n\n", "\n", " ", ""] 
)

allowed_nodes = [
    "Company",
    "Segment",
    "Product/Service",
    "Technology/Model",
    "RevenueSource",
    "Competitor",
    "Goal/Commitment",
    
    # --- เพิ่มใหม่เพื่อทดแทน Property ---
    "Region",       # แทน Property: location, country
    "RawMaterial",  # แทนรายละเอียดใน Product description
    "RiskFactor",   # แทน Item 1A context
    "Supplier"      # แยกจาก Competitor ชัดเจน
]

allowed_relationships = [
    "(Company)-[:HAS_SEGMENT]->(Segment)",
    "(Segment)-[:OFFERS_PRODUCT]->(Product)",
    "(Product)-[:POWERED_BY]->(Technology)",
    "(Segment)-[:GENERATES_REVENUE_VIA]->(RevenueSource)",
    "(Product)-[:COMPETES_WITH]->(Competitor)",
    "(Company)-[:INVESTS_IN]->(Technology)",

    "(Segment)-[:OPERATES_IN]->(Region)",
    "(RevenueSource)-[:DERIVED_FROM]->(Region)", 
    
    "(Product)-[:DEPENDS_ON_MATERIAL]->(RawMaterial)",
    "(Company)-[:SOURCES_FROM]->(Supplier)",
    
    "(RiskFactor)-[:THREATENS]->(Product)",
    "(RiskFactor)-[:THREATENS]->(RevenueSource)"
]
# allowed_relationships = [
#     "HAS_SEGMENT",
#     "OFFERS_PRODUCT",
#     "POWERED_BY",
#     "GENERATES_REVENUE_VIA",
#     "COMPETES_WITH",
#     "INVESTS_IN",
#     "OPERATES_IN",
#     "DERIVED_FROM",
#     "DEPENDS_ON_MATERIAL",
#     "SOURCES_FROM",
#     "THREATENS"
# ]

transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=allowed_nodes,
    allowed_relationships=allowed_relationships,
    ignore_tool_usage=True,
)

def fetch_section_chunks() -> List[str]:
    with open("data/processed/sections/full-submission_10-K_1_Item 1.md","r") as f:
        lines = f.readlines()
        section = '\n'.join(lines)

    print(len(section))
    chunks = text_splitter.split_text(section)

    return chunks


def process_single_chunk(chunk, chunk_idx) -> dict:
    try:
        chunk_doc = Document(page_content=chunk)
        graph_document = transformer.convert_to_graph_documents([chunk_doc])
        
        if graph_document:
            for node in graph_document[0].nodes:
                if node.properties is None:
                    node.properties = {}
                
                node.properties['name'] = node.id
                node.properties['source_chunk'] = chunk_idx

            print(f"DEBUG Chunk {chunk_idx} Node 0: {graph_document[0].nodes[0]}")

        return {
            'success': True,
            'chunk_idx': chunk_idx,
            'nodes': len(graph_document[0].nodes) if graph_document else 0,
            'relationships': len(graph_document[0].relationships) if graph_document else 0,
            'graph_doc': graph_document[0] if graph_document else None
        }
    except Exception as e:
        return {'success': False, 'chunk_idx': chunk_idx, 'error': str(e)}

def kg_extraction() -> None:
    chunks = fetch_section_chunks()
    print(f"Total chunks: {len(chunks)}")

    # chunk_doc = Document(page_content=chunks[2])
    # graph_document = transformer.convert_to_graph_documents([chunk_doc])
    # print(f"Nodes : {len(graph_document[0].nodes)}")
    # print(f"Relationships: {len(graph_document[0].relationships)}")

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        try:
            chunk_doc = Document(page_content=chunk)
            graph_document = transformer.convert_to_graph_documents([chunk_doc])
            if graph_document:
                print(f"Nodes extracted: {len(graph_document[0].nodes)}")
                print(f"Relationships extracted: {len(graph_document[0].relationships)}")

                # Print sample output
                print("\n--- Sample Node ---")
                print(graph_document[0].nodes[0])

                # print("Saving to Neo4j...")
                # graph.add_graph_documents(graph_document)
            print(f"Chunk {i+1} processed successfully.")
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")

# def kg_extraction_parallel() -> None:
#     chunks = fetch_section_chunks()
#     print(f"Total chunks: {len(chunks)}")
    
#     # Adjust max_workers based on your API rate limits
#     # For OpenAI: 3-5, for local models: CPU_COUNT
#     max_workers = 5
    
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         # Submit all tasks
#         futures = {
#             executor.submit(process_single_chunk, chunk, i): i 
#             for i, chunk in enumerate(chunks)
#         }
        
#         # Process results as they complete
#         for future in as_completed(futures):
#             result = future.result()
#             if result['success']:
#                 print(f"✓ Chunk {result['chunk_idx']+1}: "
#                       f"{result['nodes']} nodes, {result['relationships']} rels")
#                 # Batch save to Neo4j later
#             else:
#                 print(f"✗ Chunk {result['chunk_idx']+1}: {result['error']}")

def kg_extraction_parallel() -> None:
    chunks = fetch_section_chunks()
    print(f"Total chunks: {len(chunks)}")
    
    max_workers = 5
    all_graph_docs = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_chunk, chunk, i): i 
            for i, chunk in enumerate(chunks)
        }
        
        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                print(f"✓ Chunk {result['chunk_idx']+1}: "
                      f"{result['nodes']} nodes, {result['relationships']} rels")
                
                # 📦 เก็บไว้ก่อน
                if result['graph_doc']:
                    all_graph_docs.append(result['graph_doc'])
            else:
                print(f"✗ Chunk {result['chunk_idx']+1}: {result['error']}")
    
    if all_graph_docs:
        print(f"\n💾 Saving {len(all_graph_docs)} graph documents to Neo4j...")
        try:
            graph.add_graph_documents(all_graph_docs)
            print(f"✅ Successfully saved all documents!")
        except Exception as e:
            print(f"❌ Neo4j batch save error: {e}")



if __name__ == "__main__":
    kg_extraction_parallel()
    # pass