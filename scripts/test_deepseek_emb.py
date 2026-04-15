#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PDF_FILE = "data/processed/10Q-NFLX.pdf"

loader = PyPDFLoader(PDF_FILE)
raw_documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,     
    length_function=len,
    separators=["\n\n", "\n", " ", ""] 
)
documents = text_splitter.split_documents(raw_documents)


class GraphDebugCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("\n===== LLM START =====")
        for p in prompts:
            print(p)

    def on_llm_end(self, response, **kwargs):
        print("\n===== LLM END =====")
        print(response)

    def on_llm_error(self, error, **kwargs):
        print("\n===== LLM ERROR =====")
        print(error)

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.0,
    # callbacks=[GraphDebugCallback()],
    model_kwargs={
        "response_format": {"type": "json_object"}, 
        "stop": None 
    },         
)

llm_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=[
        "Company",
        "Filing",
        "FinancialAccount",
        "MonetaryValue",
        "TimePeriod",       
        "RiskFactor",       
        "Region",           
        "Product",          
        "Person",            
    ],
    
    allowed_relationships=[
        "FILED_REPORT",
        "REPORTED_ACCOUNT",    
        "HAS_VALUE",        
        "DURING_PERIOD",    
        "OPERATES_IN",      
        "COMPETES_WITH",   
        "RELATED_TO",       
    ],
    ignore_tool_usage=True,
)

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)


def deepseek_emb():
    for i, doc in enumerate(documents):
        print(f"🔍Process {i+1}/{len(documents)}...")
        try:
            graph_document = llm_transformer.convert_to_graph_documents([doc])
            if graph_document:
                print(f"Nodes : {len(graph_document[0].nodes)}")
                print(f"Relationships: {len(graph_document[0].relationships)}")

                graph.add_graph_documents(graph_document) 
                print(f"Success : (Nodes: {len(graph_document[0].nodes)})")
            else:
                print("No relation")

            print("Delay 0.5 Sec")
            time.sleep(0.2)

        except Exception as e:
            print("exeption ",e)
    # graph_document = llm_transformer.convert_to_graph_documents(test_docs)
    # if graph_document:
    #     print(f"Nodes : {len(graph_document[0].nodes)}")
    #     print(f"Relationships: {len(graph_document[0].relationships)}")
        
    else:
        print("No relation")

if __name__ == "__main__":
    # print(len(documents))
    # print(documents[30])
    deepseek_emb()