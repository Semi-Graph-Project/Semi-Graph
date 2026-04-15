import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.7
)
messages = [
    SystemMessage(content="คุณคือผู้ช่วยอัจฉริยะที่เชี่ยวชาญภาษาไทย"),
    HumanMessage(content="เปรียบเทียบ API Deepseek-chat กับ gemini-1.5-flash ในการใช้งานด้านการวิเคราะห์ข้อมูลเชิงกราฟ"),
]

response = llm.invoke(messages)

print(response.content)