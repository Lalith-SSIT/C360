from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core import rate_limiters
from langchain_openai import ChatOpenAI
from datetime import datetime
import configparser

# Load config and initialize models
config = configparser.ConfigParser()
config.read('config.ini')
provider = config['models']['provider']

# CHAT_MODEL = ChatOllama(
#     model="llama3.1",
#     temperature=0.1,
#     max_tokens=2048,
#     top_p=0.9,
#     top_k=40
# )


TODAY = datetime.now()
RATE_LIMITER = rate_limiters.InMemoryRateLimiter(requests_per_second=0.1)

CODE_MODEL = ChatOllama(
    model="gemma3:12b",
    temperature=0,
    max_tokens=2048,
    top_p=0.4,
    top_k=2
)


if provider == "openai":
    CHAT_MODEL = ChatOpenAI(model=config['openai']['chat_model'])
elif provider == "gemini":
    CHAT_MODEL = ChatGoogleGenerativeAI(
        model=config['gemini']['chat_model'],
        temperature=0.1,
        max_output_tokens=2048,
        top_p=0.9, top_k=40,
        rate_limiter=RATE_LIMITER
    )
else:
    CHAT_MODEL = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
        temperature=0.1, max_output_tokens=2048, top_p=0.9, top_k=40, rate_limiter=RATE_LIMITER)

# Fallback model for all agents
FALLBACK_MODEL = ChatOllama(model="llama3.1", temperature=0.1)