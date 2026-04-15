#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PDF_FILE = "data/processed/10Q-NFLX.pdf"

loader = PyPDFLoader(PDF_FILE)
raw_documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,     
    length_function=len,
    separators=["\n\n", "\n", " ", ""] 
)
documents = text_splitter.split_documents(raw_documents)

llm = ChatGoogleGenerativeAI(
    model="models/gemini-flash-latest",
    temperature=0,
    )

llm_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=[
        "Company",          
        "FinancialMetric",  
        "TimePeriod",       
        "RiskFactor",       
        "Region",           
        "Product",          
        "Person",            
    ],
    
    allowed_relationships=[
        "REPORTED",         
        "HAS_VALUE",        
        "DURING_PERIOD",    
        "OPERATES_IN",      
        "COMPETES_WITH",    
        "INCREASED_BY",     
        "DECREASED_BY",     
        "RELATED_TO",       
    ],
)

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)

def test_llm(prompt: str) -> str:
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error during LLM invocation: {e}")
        raise

def graph_emb(documents, llm_transformer, graph):
    for i, doc in enumerate(documents):
        print(f"Process {i+1}/{len(documents)}...")
        try:
            graph_document = llm_transformer.convert_to_graph_documents([doc])
            if graph_document:
                print(f"Nodes : {len(graph_document[0].nodes)}")
                print(f"Relationships: {len(graph_document[0].relationships)}")
                graph.add_graph_documents(graph_document) 
                print(f"Success : (Nodes: {len(graph_document[0].nodes)})")
            else:
                print("No relation")

            print("Delay 5 Sec")
            time.sleep(5) 

        except Exception as e:
            print("exeption ",e)
            if "429" in str(e):
                print("60 Sec wait for rate limit")
                time.sleep(60)
def deepseek_emb():
    test_docs = raw_documents[10:12]
    graph_document = llm_transformer.convert_to_graph_documents(test_docs)
    

if __name__ == "__main__":
    # graph_emb(documents, llm_transformer, graph)

    print(raw_documents[10:12])
