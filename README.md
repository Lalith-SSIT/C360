# C360 - Customer 360 Intelligence Platform

A comprehensive customer intelligence platform that combines SQL database querying with RAG (Retrieval-Augmented Generation) capabilities for enhanced customer insights.

## Architecture

![C360 Architecture](images/graph.png)

### Agent System
- **Supervisor Agent**: Routes queries to appropriate specialized agents
- **SQL Agent**: Handles database queries and structured data analysis
- **RAG Agent**: Processes unstructured data using vector search
- **Analysis Agent**: Performs data analysis and generates insights
- **Business Agent**: Provides business-focused recommendations


## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file

3. Install Ollama locally and Microsoft SQL Server

4. Run the application:
```bash
# Console application
python app.py

# Streamlit web interface
streamlit run streamlit_app.py
```

## Data Sources

- SQL Server database with customer tables (Account, Opportunity, Product, Activity)


## Technologies Used

- **LangChain & LangGraph**: Agent creation and orchestration
- **ChromaDB**: Vector storage for RAG capabilities
- **SQL Server**: Structured data storage
- **Streamlit**: Web interface
- **Ollama**: Local LLM inference
- **Pandas**: Data manipulation and CSV export

## Recent Updates

- ✅ Added specialized Analysis and Business agents
- ✅ Implemented automated CSV export functionality
- ✅ Enhanced supervisor agent with improved query routing
- ✅ Updated Streamlit interface with better user experience

## Future Scope

- Optimizing response time for simple queries
- Setup persistent caching mechanism
- Setup fallback mechanisms for SQL queries
- Enabling artifacts mode for enhanced outputs
- Isolating SQL state for token and cost optimization
- Advanced analytics dashboard