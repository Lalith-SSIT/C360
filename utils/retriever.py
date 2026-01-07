from langchain_postgres import PGVector
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
import os
from urllib.parse import quote_plus
from utils.db import get_engine_v3

# Connection from shared utility
engine = get_engine_v3()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

pg_vectorstore = PGVector(
    embeddings=embeddings,
    collection_name="sales_copilot",
    connection=engine
)

def retrieve_documents(query: str, k: int = 5):
    """
    Retrieve top-k documents relevant to the query using semantic search.
    """
    embedded_query = embeddings.embed_query(query)
    doc_scores = pg_vectorstore.similarity_search_with_score_by_vector(embedded_query, k)
    
    results = []
    if doc_scores:
        for doc, score in doc_scores:
            doc.metadata = dict(doc.metadata) if doc.metadata else {}
            doc.metadata["score"] = float(score)
            results.append(doc)
    return results