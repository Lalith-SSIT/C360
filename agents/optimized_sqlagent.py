from langchain_community.utilities import SQLDatabase
from utils.globals import CHAT_MODEL
from utils.agentutils import create_agent
from langgraph.prebuilt import ToolNode
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool, InfoSQLDatabaseTool
from sqlalchemy import create_engine
# from utils.cache import sql_cache
import hashlib

# SQL Server connection - reuse existing connection
connection_string = "mssql+pyodbc://@DESKTOP-4J53D2I\\C360/C360?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
db = SQLDatabase(engine=engine, include_tables=["Opportunity", "Account", "Product", "Support_Ticket", "Pipeline", "Activity", "Contract"])

# Use only essential tools
sql_query_tool = QuerySQLDatabaseTool(db=db, handle_tool_error=True)
sql_schema_tool = InfoSQLDatabaseTool(db=db, handle_tool_error=True)

sqltools = [sql_query_tool, sql_schema_tool]
sqltools_node = ToolNode(sqltools)

def sqlagent_node(state):
    """
    Optimized SQL Agent with caching and streamlined prompts.
    """
    
    # Check cache for similar queries
    query_text = state["messages"][-1].content
    # cache_key = hashlib.md5(query_text.encode()).hexdigest()
    # cached_result = sql_cache.get(cache_key)
    # if cached_result:
        # return {"messages": [cached_result]}
    
    system_prompt = """You are a SQL agent for CRM data. Be direct and efficient.

Tables: Account, Activity, Pipeline, Opportunity, Contract, Support_Ticket, Product

Quick execution:
1. For simple queries, go straight to sql_db_query
2. Only use sql_schema_tool if you get column errors
3. Keep responses concise and data-focused

Common patterns:
- "top N" → SELECT TOP N
- "count" → SELECT COUNT(*)  
- "list" → SELECT columns FROM table"""
    
    model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=sqltools)
    response = model.invoke(state["messages"])
    
    # Cache successful responses
    # sql_cache.set(cache_key, response)
    
    return {"messages": [response]}