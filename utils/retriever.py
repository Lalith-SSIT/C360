from langchain_postgres import PGVector
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_community.retrievers import BM25Retriever
import os
from urllib.parse import quote_plus


# Connection string from environment variables
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'YourStrong!Passw0rd')
db_name = os.getenv('DB_NAME', 'sales_copilot')

connection_string = f"postgresql+psycopg://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"

pg_vectorstore = PGVector(
    embeddings=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"),
    collection_name="sales_copilot",
    connection=connection_string
)

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def retrieve_documents(query: str, k: int = 5):
    """
    Retrieve top-k documents relevant to the query.
    Args:
        query (str): The search query.
        k (int): Number of documents to retrieve.
    Returns:
        List of documents.
    """
    embedded_query = embeddings.embed_query(query)
    doc_scores = pg_vectorstore.similarity_search_with_score_by_vector(embedded_query, k)
    if not doc_scores:
        return []

    docs, semantic_scores = zip(*doc_scores)
    # Normalize semantic scores to [0, 1]
    import numpy as np
    semantic_scores = np.array(semantic_scores)

    # BM25Retriever expects a list of Document objects
    keyword_based_retriever = BM25Retriever.from_documents(list(docs))
    bm25_docs = keyword_based_retriever.invoke(query)
    bm25_order = {doc.page_content: i for i, doc in enumerate(bm25_docs)}
    n_bm25 = len(bm25_docs)

    results = []
    for i, doc in enumerate(docs):
        bm25_rank = bm25_order.get(doc.page_content, n_bm25)
        bm25_score = (n_bm25 - bm25_rank - 1) / (n_bm25 - 1) if n_bm25 > 1 else 1.0
        doc.metadata = dict(doc.metadata) if doc.metadata else {}
        doc.metadata["score"] = (0.8 * bm25_score) + (0.4 * float(semantic_scores[i]))
        results.append(doc)

    results = sorted(results, key=lambda doc: doc.metadata.get("score", 0), reverse=True)
    # Remove results with score == 0
    results = [doc for doc in results if doc.metadata.get("score", 0) > 0]
    return results