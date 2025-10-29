import sys
import os
import json
from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from urllib.parse import quote_plus

VECTOR_SIZE = 768

def json_to_pgvector(json_file, connection_string, collection_name="embeddings"):
    """Convert JSON to embeddings and store in pgvector using LangChain"""
    
    # Load embedding model

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to LangChain documents
    documents = []
    for primary_key, record in data.items():
        content = json.dumps(record, separators=(',', ':'))
        doc = Document(
            page_content=content,
            metadata={"id": primary_key, "source": os.path.basename(json_file)}
            )
        documents.append(doc)
    
    # Store in PGVector
    vector_store = PGVector.from_documents(
        documents=documents,
        embedding=embeddings,
        connection=connection_string,
        collection_name=collection_name
    )
    
    print(f"Stored {len(documents)} records in {collection_name}")
    return vector_store

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_to_pgvector.py <json_file> [table_name]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    table_name = sys.argv[2] if len(sys.argv) > 2 else "embeddings"
    
    # Connection string from environment variables
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME')
    
    # Validate required environment variables
    if not all([db_host, db_port, db_user, db_name]):
        print("Error: Missing required environment variables (DB_HOST, DB_PORT, DB_USER, DB_NAME)")
        sys.exit(1)
    
    connection_string = f"postgresql+psycopg://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
    collection_name = "sales_copilot"
    json_to_pgvector(json_file, connection_string, collection_name)