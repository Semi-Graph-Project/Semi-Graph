import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()
from pydantic import BaseModel, Field
import time
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# --- 1. Setup Neo4j & LLM ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.0
)

@dataclass
class Ontology:
    common_nodes = [
        "Document",
        "Section",
        "Chunk",
        "Company",
        "FiscalYear",
        "Technology"
    ]

    common_relationships = [
        "(:Document)-[:CONTAINS_SECTION]->(:Section)",
        "(:Section)-[:HAS_CHUNK]->(:Chunk)",
        "(:Chunk)-[:NEXT_CHUNK]->(:Chunk)",
        "(:Document)-[:FILED_BY]->(:Company)",
        "(:Document)-[:FOR_FISCAL_YEAR]->(:FiscalYear)",
        "(:Chunk)-[:MENTIONS]->(:Technology)",
    ]
    
    item1_nodes = [
        "BusinessSegment",
        "ProductLine",
        "GeographicMarket",
    ]

    item1_relationships = [
        "(:Company)-[:HAS_SEGMENT]->(:BusinessSegment)",
        "(:BusinessSegment)-[:HAS_PRODUCT_LINE]->(:ProductLine)",
        "(:BusinessSegment)-[:SERVES_MARKET]->(:GeographicMarket)",
    ]


    item1A_nodes = [
        "RiskCategory",
        "RiskFactor",
        "RiskDriver",
        "RiskEvent",
        "Impact",
    ]
    item1A_relationships=[
        "(:RiskEvent)-[:DRIVEN_BY]->(:RiskDriver)",
        "(:RiskEvent)-[:LEADS_TO]->(:Impact)",
        "(:Company)-[:FACED_OF]->(:RiskEvent)",
        "(:RiskFactor)-[:CATEGORIZED_AS]->(:RiskCategory)",
        "(:RiskEvent)-[:IS_A]->(:RiskFactor)",
        "(:Chunk)-[:MENTIONS]->(:RiskEvent)",

    ]

    item5_nodes = [
        "RepurchaseAuthorization", 
        "RepurchaseActivity",  
        "DividendPayout",      
        "StockPerformance"       
    ]
    item5_relationships = [
        "(:Company)-[:AUTHORIZED]->(:RepurchaseAuthorization)",
        "(:RepurchaseAuthorization)-[:EXECUTED_AS]->(:RepurchaseActivity)",
        "(:Chunk)-[:REPORTS_METRIC]->(:RepurchaseActivity)",
        "(:Company)-[:DECLARED]->(:DividendPayout)",
        "(:DividendPayout)-[:PAID_IN]->(:FiscalYear)",
    ]
    item7_nodes = [
        "FinancialMetric",   
        "PerformanceDriver",
    ]
    item7_relationships = [
        "(:PerformanceDriver)-[:IMPACTED]->(:FinancialMetric)",

        "(:FinancialMetric)-[:REPORTED_IN]->(:FiscalYear)",
        
        "(:FinancialMetric)-[:PART_OF]->(:FinancialMetric)", 
        "(:Chunk)-[:MENTIONS]->(:FinancialMetric)"
    ]

    item8_nodes = [
        "FinancialTable",
        "LineItem",
        "AccountingPolicy",
        "AuditOpinion"
    ]

    item8_relationships = [
        "(:Chunk)-[:CONTAINS_TABLE]->(:FinancialTable)",
        "(:FinancialTable)-[:HAS_ROW]->(:LineItem)",
        "(:LineItem)-[:REPORTED_FOR]->(:FiscalYear)",
        "(:LineItem)-[:AGGREGATES]->(:LineItem)", 
        "(:Chunk)-[:DEFINES_POLICY]->(:AccountingPolicy)",
        "(:AccountingPolicy)-[:GOVERNS]->(:LineItem)",
        "(:Document)-[:HAS_AUDIT]->(:AuditOpinion)"
    ]
# node_schemas = {
    
# }

item8_node_schemas = {
    "FinancialTable": {
        "definition": "A structured table representing a standard financial statement.",
        "examples": ["Consolidated Balance Sheets", "Statements of Operations", "Cash Flow Statements"],
        "properties": {
            "name": "Standardized table name (required)",
            "unit_scale": "Millions/Thousands/Billions (required)",
            "currency": "USD/EUR (required)"
        },
        "extraction_hints": "Identify table headers. Usually found at the beginning of Item 8."
    },

    "LineItem": {
        "definition": "A specific financial accounting entry within a statement.",
        "examples": ["Net Sales", "Cost of Goods Sold", "Total Assets", "Retained Earnings"],
        "properties": {
            "name": "Standardized name (e.g., 'Revenue') (required)",
            "original_label": "Exact text in row (e.g., 'Net sales') (optional)",
            "value": "Numeric value (float) (required)",
            "row_order": "Index for reconstruction (integer) (optional)",
            "is_total": "Boolean (True if it's a sum row like Total Assets) (optional)"
        },
        "extraction_hints": "Extract row by row. Must link to FiscalYear column headers."
    },

    "AccountingPolicy": {
        "definition": "Principles and procedures implemented by the company to prepare financial statements.",
        "examples": ["Revenue Recognition", "Lease Accounting (ASC 842)", "Stock-Based Compensation"],
        "properties": {
            "name": "Policy topic (required)",
            "standard_ref": "Reference to GAAP/IFRS code if mentioned (e.g., ASC 606) (optional)",
            "description": "Summary of the method used (required)"
        },
        "extraction_hints": "Found in 'Notes to Consolidated Financial Statements' (Note 1 or 2)."
    },

    "AuditOpinion": {
        "definition": "The auditor's statement regarding the fairness of the financial statements.",
        "examples": ["Unqualified Opinion", "Qualified Opinion", "Adverse Opinion"],
        "properties": {
            "auditor_name": "Firm name (e.g., PwC, EY) (required)",
            "opinion_type": "Unqualified/Qualified/Critical Audit Matter (required)",
            "date": "Date of signing (optional)"
        },
        "extraction_hints": "Look for 'Report of Independent Registered Public Accounting Firm'."
    }
}

class GraphNode(BaseModel):
    id: str
    type: str
    properties: Optional[dict] = Field(description="Attributes of the node")

class GraphRelationship(BaseModel):
    source: str
    source_type: str
    target: str
    target_type: str
    type: str
    properties: Optional[dict] = Field(description="Attributes of the relationship")

class GraphExtractionSchema(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

def build_node_schema_prompt(node_schemas: dict) -> str:
    """Generate detailed schema documentation for LLM"""
    schema_sections = []
    
    for node_type, schema in node_schemas.items():
        section = f"""
**{node_type}**
Definition: {schema['definition']}
Examples: {', '.join(f'"{ex}"' for ex in schema['examples'])}
Properties to extract: {', '.join(f"{k} ({v})" for k, v in schema['properties'].items())}
Extraction hints: {schema['extraction_hints']}
"""
        schema_sections.append(section)
    
    return "\n".join(schema_sections)

class DeepSeekGraphTransformer:
    def __init__(self, llm, allowed_nodes, allowed_relationships,node_schemas=None):
        self.llm = llm
        self.allowed_nodes = allowed_nodes
        self.allowed_relationships = allowed_relationships
        self.node_schemas = node_schemas or {} 
        self.parser = JsonOutputParser(pydantic_object=GraphExtractionSchema)

        schema_docs = build_node_schema_prompt(self.node_schemas) if self.node_schemas else ""

        # if not schema_docs:
        #     print("--- No Schema!! ---")
        # system_prompt = (
        #     "You are an expert data analyst extracting a knowledge graph from a company's 10-K filing. "
        #     "Your task is to identify specific entities and their relationships from the input text.\n\n"
            
        #     "STRICT RULES FOR ID GENERATION:\n"
        #     "1. **Use the ACTUAL NAME found in the text** as the 'id' (e.g., 'Google Cloud', 'YouTube', 'Sundar Pichai').\n"
        #     "2. **NEVER use generic IDs** like 'Product_1', 'Segment_A', 'Company_1'. If no specific name is found, do not create the node.\n"
        #     "3. **Entity Resolution:** Use the most complete name (e.g., use 'Alphabet Inc.' instead of 'the Company' if possible).\n\n"
            
        #     f"Allowed Node Types: {', '.join(allowed_nodes)}\n"
        #     f"Allowed Relationship Types: {', '.join(allowed_relationships)}\n\n"
            
        #     "Schema Rules (Context):\n"
        #     "- 'Google Services' and 'Google Cloud' are BusinessSegments.\n"
        #     "- 'Android', 'Chrome', 'YouTube' are ProductLines.\n"
        #     "- 'Advertising', 'Subscription' are RevenueSources.\n\n"

        #     "SUMMARY GENERATION:\n"
        #     "- For each node, generate a 'summary' property (1-2 sentences) describing:\n"
        #     "  * What the entity is\n"
        #     "  * Its key attributes from the text\n"
        #     "  * Its relationship to the company\n"
        #     "Example: {{'id': 'Google Cloud', 'type': 'BusinessSegment', "
        #     "'properties': {{'summary': 'A business segment of Alphabet focusing on cloud computing services, "
        #     "including infrastructure and platform solutions.'}}}}\n"
            
        #     "Return the output strictly in JSON format matching the schema."
        #     "\n{format_instructions}"
            
        # )
        # else:
        system_prompt = (
            "You are an expert data analyst extracting a knowledge graph from a company's 10-K filing. "
            "Your task is to identify specific entities and their relationships from the input text.\n\n"
            
            "=== ENTITY SCHEMA DOCUMENTATION ===\n"
            f"{schema_docs}\n"  
            "=== END SCHEMA ===\n\n"
            
            "STRICT RULES FOR ID GENERATION:\n"
            "1. **Use the ACTUAL NAME found in the text** as the 'id' (e.g., 'Google Cloud', 'YouTube').\n"
            "2. **NEVER use generic IDs** like 'Product_1', 'Risk_A'. If no specific name exists, create a descriptive ID from the text.\n"
            "3. **Entity Resolution:** Use the most complete name when the same entity appears multiple times.\n\n"
            "4. **Fiscal year is pure number of year (e.g., 2024 , 2025)"
            
            f"Allowed Node Types: {', '.join(allowed_nodes)}\n"
            f"Allowed Relationship Types: {', '.join(allowed_relationships)}\n\n"
            
            "PROPERTY GENERATION:\n"
            "- Follow the property schema defined above for each node type (if have schema)\n"
            "- ** Always include 'summary' property (1-2 sentences) for context **\n"
            "- Extract quantitative data when available (revenue, percentages, dollar amounts)\n"
            "- If property is marked (optional) and not found in text, omit it\n\n"
            
            "Return the output strictly in JSON format matching the schema."
            "\n{format_instructions}"
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        self.chain = self.prompt | self.llm | self.parser


    def validate_node_properties(self, node: dict, node_type: str) -> dict:
        """Validate and enrich node properties based on schema"""
        if node_type not in self.node_schemas:
            return node
        
        schema = self.node_schemas[node_type]
        properties = node.get('properties', {})
        
        # Check required properties
        required_props = [k for k, v in schema['properties'].items() if '(required)' in v]
        missing = [p for p in required_props if p not in properties]
        
        if missing:
            print(f"<--> Warning: Node '{node['id']}' of type '{node_type}' missing required properties: {missing}")
        
        # Add type hint for downstream processing
        properties['_node_type_definition'] = schema['definition']
        
        return {**node, 'properties': properties}
        
    def convert_to_graph_documents(self, documents: List[Document]) -> List[GraphDocument]:
        results = []
        for doc in documents:
            try:
                # 1. Run Chain
                start_time = time.time()
                raw_data = self.chain.invoke({
                    "input": doc.page_content,
                    "format_instructions": self.parser.get_format_instructions()
                })
                end_time = time.time()
                llm_time = end_time - start_time
                print(f"LLM processing time: {llm_time:.2f} seconds")

                # 2. Convert raw JSON to Neo4j GraphDocument objects
                # nodes = [
                #     Node(id=n['id'], type=n['type'], properties=n.get('properties', {}))
                #     for n in raw_data['nodes']
                #     if n['type'] in self.allowed_nodes # Filter types
                # ]

                nodes = []
                for n in raw_data['nodes']:
                    if n['type'] in self.allowed_nodes:
                        validated = self.validate_node_properties(n, n['type'])  
                        nodes.append(
                            Node(id=validated['id'], 
                                type=validated['type'], 
                                properties=validated.get('properties', {}))
                        )                
                
                rels = []
                for r in raw_data['relationships']:
                    # Simple filter to ensure types match schema
                    # (In production, you might want stricter validation)
                    source_node = Node(id=r['source'], type=r['source_type'])
                    target_node = Node(id=r['target'], type=r['target_type'])
                    
                    rels.append(Relationship(
                        source=source_node,
                        target=target_node,
                        type=r['type'],
                        properties=r.get('properties', {})
                    ))
                
                results.append(GraphDocument(nodes=nodes, relationships=rels, source=doc))
                
            except Exception as e:
                print(f"Error processing document: {e}")
        return results
    

    def process_single_chunk(self, chunk, chunk_idx) -> dict:
        try:
            chunk_doc = Document(page_content=chunk)
            graph_document = self.convert_to_graph_documents([chunk_doc])

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


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=4500, chunk_overlap=600, length_function=len
)



graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)


def fetch_section_chunks(path) -> List[str]:
    if not os.path.exists(path):
        print("File not found, creating dummy data for test.")
        return ["Alphabet Inc. reports Google in two segments: Google Services and Google Cloud."]
        
    with open(path, "r") as f:
        section = f.read()
    return text_splitter.split_text(section)


def kg_extraction() -> None:
    chunks = fetch_section_chunks()
    print(f"Total chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[0:3]):
        print(f"Chunk {i+1} length: {len(chunk)} characters")
        try:
            chunk_doc = Document(page_content=chunk)

            print("Extracting...")
            graph_documents = transformer.convert_to_graph_documents([chunk_doc])
            
            if graph_documents:
                print(f"Nodes extracted: {len(graph_documents[0].nodes)}")
                print(f"Relationships extracted: {len(graph_documents[0].relationships)}")
                
                # Print some node and relationship samples
                if graph_documents[0].nodes:
                    print("Sample Node:", graph_documents[0].nodes[0])
                    print("Sample Node Properties:", graph_documents[0].nodes[0].properties)
                if graph_documents[0].relationships:
                    print("Sample Relationship:", graph_documents[0].relationships[0])
                    print("Sample Relationship Properties:", graph_documents[0].relationships[0].properties)
        
            else:
                print(f"No data extracted from chunk {i+1}.\n")

        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")

def save_to_neo4j_in_batches(graph_docs: List[GraphDocument], batch_size: int = 5):
    """Save graph documents in smaller batches to prevent timeout"""
    if not graph_docs:
        print("No documents to save")
        return
    
    print("Warming up connection...")
    try:
        graph.query("RETURN 1")
        time.sleep(0.5)
    except Exception as e:
        print("exeption WarmUp : ",e)
    total = len(graph_docs)
    saved = 0
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = graph_docs[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        try:
            print(f"💾 Saving batch {batch_num}/{(total+batch_size-1)//batch_size} "
                  f"({len(batch)} documents)...")
            
            graph.add_graph_documents(batch)
            saved += len(batch)
            print(f"   ✅ Batch {batch_num} saved successfully")
            
        except Exception as e:
            failed += len(batch)
            print(f" Batch {batch_num} failed: {e}")
            
            # 🔥 Fallback: Try saving one by one in this batch
            print(f"   🔄 Retrying batch {batch_num} documents individually...")
            for j, doc in enumerate(batch):
                try:
                    graph.add_graph_documents([doc])
                    saved += 1
                    print(f"  Document {i+j+1} saved")
                except Exception as e2:
                    failed += 1
                    print(f"      Document {i+j+1} failed: {e2}")
    
    print(f"\n Saved: {saved}/{total}, Failed: {failed}/{total}")
     
def kg_extraction_parallel(path) -> None:
    chunks = fetch_section_chunks(path=path)
    print(f"Total chunks: {len(chunks)}")
    print(f'<<< Simple Chunk >>> \n{chunks[0][0:500]}\n---------\n\n')
    
    max_workers = 16
    all_graph_docs = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(transformer.process_single_chunk, chunk, i): i 
            for i, chunk in enumerate(chunks)
        }
        
        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                print(f"✓ Chunk {result['chunk_idx']+1}: "
                      f"{result['nodes']} nodes, {result['relationships']} rels")
                
               
                if result['graph_doc']:
                    all_graph_docs.append(result['graph_doc'])
            else:
                print(f"✗ Chunk {result['chunk_idx']+1}: {result['error']}")


    if all_graph_docs:
        print(f"\n Saving {len(all_graph_docs)} graph documents to Neo4j...")
        save_to_neo4j_in_batches(all_graph_docs, batch_size=5)


if __name__ == "__main__":
    print("::: Run Process Item1 :: ")


    # path = "data/processed/sections24-000022/full-submission_10-K_1_Item 1.md"
    # allowed_nodes = Ontology.common_nodes + Ontology.item1_nodes
    # allowed_relationships = Ontology.common_relationships + Ontology.item1_relationships

    # transformer = DeepSeekGraphTransformer(
    #     llm=llm,
    #     allowed_nodes=allowed_nodes,
    #     allowed_relationships=allowed_relationships,
    #     node_schemas=None,
        
    # )
    # kg_extraction_parallel(path)

    # print("\nSleep 1 s For item1A.... \n")
    # time.sleep(1)

    # path = "data/processed/sections24-000022/full-submission_10-K_1_Item 1A.md"
    # allowed_nodes = Ontology.common_nodes + Ontology.item1A_nodes
    # allowed_relationships = Ontology.common_relationships + Ontology.item1A_relationships

    # transformer = DeepSeekGraphTransformer(
    #     llm=llm,
    #     allowed_nodes=allowed_nodes,
    #     allowed_relationships=allowed_relationships,
    #     node_schemas=None,
        
    # )
    # kg_extraction_parallel(path)


    # print("\nSleep 1 s For item5.... \n")
    # time.sleep(1)

    # path = "data/processed/sections24-000022/full-submission_10-K_1_Item 5.md"
    # allowed_nodes = Ontology.common_nodes + Ontology.item5_nodes
    # allowed_relationships = Ontology.common_relationships + Ontology.item5_relationships

    # transformer = DeepSeekGraphTransformer(
    #     llm=llm,
    #     allowed_nodes=allowed_nodes,
    #     allowed_relationships=allowed_relationships,
    #     node_schemas=None,
        
    # )
    # kg_extraction_parallel(path)
    
    # print("\nSleep 1 s For item7 .... \n")
    # time.sleep(1)

    # path = "data/processed/sections24-000022/full-submission_10-K_1_Item 7.md"
    # allowed_nodes = Ontology.common_nodes + Ontology.item7_nodes
    # allowed_relationships = Ontology.common_relationships + Ontology.item7_relationships

    # transformer = DeepSeekGraphTransformer(
    #     llm=llm,
    #     allowed_nodes=allowed_nodes,
    #     allowed_relationships=allowed_relationships,
    #     node_schemas=None,
        
    # )
    # kg_extraction_parallel(path)

    path = "data/processed/sections24-000022/full-submission_10-K_1_Item 8.md"
    allowed_nodes = Ontology.common_nodes + Ontology.item8_nodes
    allowed_relationships = Ontology.common_relationships + Ontology.item8_relationships

    transformer = DeepSeekGraphTransformer(
        llm=llm,
        allowed_nodes=allowed_nodes,
        allowed_relationships=allowed_relationships,
        node_schemas=item8_node_schemas,
        
    )
    kg_extraction_parallel(path)