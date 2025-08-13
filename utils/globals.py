from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core import rate_limiters

# CHAT_MODEL = ChatOllama(
#     model="llama3.1",
#     temperature=0.1,
#     max_tokens=2048,
#     top_p=0.9,
#     top_k=40
# )

rate_limiter = rate_limiters.InMemoryRateLimiter(requests_per_second=0.1)

CODE_MODEL = ChatOllama(
    model="gemma3:12b",
    temperature=0,
    max_tokens=2048,
    top_p=0.4,
    top_k=2
)

CHAT_MODEL = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
    temperature=0.1, max_output_tokens=2048, top_p=0.9, top_k=40, google_api_key="AIzaSyAJxJTY5O7jtEa-9_9pvhFMuhuMX_ZgbzU")