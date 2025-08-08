# C360 - Customer 360 Intelligence Platform

A comprehensive customer intelligence platform that combines SQL database querying with RAG (Retrieval-Augmented Generation) capabilities for enhanced customer insights.

## Features

- **SQL Agent**: Natural language to SQL query conversion for customer data analysis
- **RAG Agent**: Document-based question answering using vector embeddings
- **Supervisor Agent**: Orchestrates between different agents based on query type
- **Multi-modal Data Processing**: Handles structured (SQL) and unstructured (documents) data

## Architecture

- **Agents**: Modular agent system with specialized capabilities
- **Utils**: Shared utilities for database connections, vector stores, and configurations
- **Data**: Customer data including accounts, opportunities, activities, and products

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file

3. Run the application:
```bash
python app.py
```

## Data Sources

- SQL Server database with customer tables (Account, Opportunity, Product, Activity)
- Document embeddings stored in ChromaDB vector store
- CSV data files for batch processing

## Technologies Used

- LangChain for agent orchestration
- ChromaDB for vector storage
- SQL Server for structured data
- Streamlit for web interface