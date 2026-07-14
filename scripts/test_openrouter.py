from langchain_openrouter import ChatOpenRouter

llm = ChatOpenRouter(model="anthropic/claude-3.5-sonnet")

response = llm.invoke("สวัสดี OpenRouter กับ LangChain ใช้งานอย่างไร?")
print(response.content)
