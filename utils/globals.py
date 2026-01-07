from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core import rate_limiters
from langchain_openai import ChatOpenAI
from datetime import datetime
import configparser
import os

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


try:
    if provider == "openai":
        CHAT_MODEL = ChatOpenAI(model=config['openai']['chat_model'])
    elif provider == "gemini":
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found. Falling back to Ollama.")
            raise ValueError("Missing API key")
        CHAT_MODEL = ChatGoogleGenerativeAI(
            model=config['gemini']['chat_model'],
            temperature=0.1,
            max_output_tokens=2048,
            top_p=0.9, top_k=40,
            rate_limiter=RATE_LIMITER,
            google_api_key=api_key
        )
    else:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found. Falling back to Ollama.")
            raise ValueError("Missing API key")
        CHAT_MODEL = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
            temperature=0.1, max_output_tokens=2048, top_p=0.9, top_k=40, rate_limiter=RATE_LIMITER, google_api_key=api_key)
except Exception as e:
    print(f"Failed to initialize {provider} model: {e}. Using Ollama fallback.")
    CHAT_MODEL = ChatOllama(
        model="llama3.1:latest",
        temperature=0.1,
        max_tokens=2048,
        top_p=0.9,
        top_k=40
    )

# Fallback model for all agents
FALLBACK_MODEL = ChatOllama(model="llama3.1:latest", temperature=0.1)