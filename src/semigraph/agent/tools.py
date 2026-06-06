"""
Sub-step C2: เขียน TOOL_SCHEMAS ใน tools.py
ไฟล์ที่จะสร้าง: src/semigraph/agent/tools.py (ใหม่)

สิ่งที่ต้องเขียน:

ตัวแปร module-level TOOL_SCHEMAS: list[dict] — 4 schemas (vector / graph / financial / news)
แต่ละ schema มี shape OpenAI function calling: {"type": "function", "function": {"name", "description", "parameters"}}
name ต้องตรง RETRIEVERS key เป๊ะ → ใช้ "vector", "graph", "financial", "news" (ดู Constraint #2) — อย่า ใช้ vector_search
description = เอามาจาก plan §Tool Select (เขียนละเอียดไว้แล้ว) — นี่คือสิ่งที่ LLM ใช้ตัดสินใจ ยิ่งคม router accuracy ยิ่งสูง
parameters = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]} — แค่ query พอ (Constraint #3)
ทำไมแบบนี้: name คือสะพานเชื่อม D.3 → D.4. ถ้า name ≠ RETRIEVERS key, D.4 ต้องมี mapping table มาแปลอีกชั้น = จุดพังเพิ่ม. ตั้งชื่อให้ตรงตั้งแต่ต้น = zero mapping

Counterfactual: ถ้าใส่ top_k_chunks ใน required → LLM ต้องเดาตัวเลข chunk ทุกครั้ง (มันไม่รู้ context ว่าควร 5 หรือ 10) → คุณจะได้ค่ามั่วๆ. ปล่อยให้ D.4 ใส่ default=5 เองดีกว่า




"""


TOOL_SCHEMAS: list[dict] = [
    {
        "type" : "function",
        "function": {
            "name": "graph",
            "description": "Relational reasoning across entities — supplier chains, customer relationships, subsidiaries, competitive positioning (X → Y → Z multi-hop paths in a knowledge graph)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to query the knowledge graph.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "vector",
            "description": "semantic similarity search over SEC filing narrative — business strategy, product descriptions, risk factors, management commentary. Use when the question asks what a company SAYS or DESCRIBES about a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The input text to retrieve vector embeddings for.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "financial",
            "description": "Retrieve financial data and insights based on a natural language query. This tool can access financial databases and APIs to provide relevant information such as stock prices, financial statements, market trends, and other financial metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to retrieve financial data and insights.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "news",
            "description": "Retrieve the latest news articles and updates based on a natural language query. This tool can access news databases and APIs to provide relevant information such as recent events, market news, company announcements, and other newsworthy topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to retrieve the latest news articles and updates.",
                    }
                },
                "required": ["query"],
            }
        }
    }


]