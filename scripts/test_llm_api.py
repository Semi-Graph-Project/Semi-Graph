import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

try:
    llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0)
    res = llm.invoke("Hello! Gemini what is your version?")
    print(res.content)
    
except Exception as e:
    print("An error occurred:", str(e))
    if "429" in str(e):
        print("Rate limit exceeded. Waiting for 60 seconds before retrying...")