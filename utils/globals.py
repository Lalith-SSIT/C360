from langchain_ollama import ChatOllama

CHAT_MODEL = ChatOllama(
    model="llama3.1",
    temperature=0.1,
    max_tokens=2048,
    top_p=0.9,
    top_k=40
)

CODE_MODEL = ChatOllama(
    model="gemma3:12b",
    temperature=0,
    max_tokens=2048,
    top_p=0.4,
    top_k=2
)