from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os
import json

def chunk_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    docs = []
    for opp_id, opp_data in data.items():
        page_content = json.dumps(opp_data, indent=2)
        metadata = {
            "opportunity_id": opp_id,
            "source": file_path
        }
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs

# Usage
docs = chunk_data("opportunitie_dict.txt")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

chroma_vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="chroma_index_dir"
)
chroma_vectorstore.add_documents(documents=docs)

chroma_vectorstore.persist()