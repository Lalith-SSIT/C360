from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever


chroma_vectorstore = Chroma(
    persist_directory="chroma_index_dir"
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


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
    doc_scores = chroma_vectorstore.similarity_search_by_vector_with_relevance_scores(embedded_query, k)
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