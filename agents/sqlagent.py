from langchain_community.utilities import SQLDatabase
from utils.globals import CHAT_MODEL, CODE_MODEL, TODAY, FALLBACK_MODEL
from utils.agentutils import create_agent
from langgraph.prebuilt import ToolNode
from langchain_community.tools.sql_database.tool import ListSQLDatabaseTool, QuerySQLCheckerTool, QuerySQLDatabaseTool, InfoSQLDatabaseTool
from sqlalchemy import create_engine, text
import pandas as pd
import os
import datetime
import uuid
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool

# SQL Server connection configuration - initialize once
connection_string = "mssql+pyodbc://@DESKTOP-4J53D2I\\C360/C360?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(connection_string)
db = SQLDatabase(engine=engine, include_tables=["Opportunity", "Account", "Product", "Support_Ticket", "Pipeline", "Activity", "Contract"])

# Module-level variable to track current session's files
# _current_session_files = []


@tool(parse_docstring=True)
def sql_query_tool(
    query: Annotated[str, "A detailed and correct SQL query."], 
    state: Annotated[dict, InjectedState]
) -> str:
    """Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.

    Args:
        query: A detailed and correct SQL query.
    """
    
    # Execute query directly to get column names and data
    # db_tool = QuerySQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
    # raw_output = db_tool._run(query)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = result.fetchall()
            
            if not rows:
                return "No data found for the query."
            
            # Convert to list of tuples for DataFrame
            parsed_output = [tuple(row) for row in rows]
            df = pd.DataFrame(parsed_output, columns=columns)
    except Exception as e:
        return f"Error executing query: {str(e)} with query: {query}"

    if len(parsed_output) > 0:
        if len(df) > 1:
            # Create file
            os.makedirs("outputs", exist_ok=True)
            timestamp = TODAY.strftime("%Y%m%d_%H%M%S")
            filename = f"info_{timestamp}.csv"
            filepath = os.path.join("outputs", filename)
            df.to_csv(filepath, index=False)
            
            # Directly update state
            if "files" not in state:
                state["files"] = []
            state["files"].append(filepath)
            
            # Return clean output without file_path
            return f"\n{df.head(4).to_string()}, {df.describe().to_string()}\n\n"
        return df.to_string()
    return str(parsed_output)


# sql_query_tool = QuerySQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
sql_querychecker_tool = QuerySQLCheckerTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
sql_list_database_tool = ListSQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
sql_schema_tool = InfoSQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)

# class SQLQueryTool(QuerySQLDatabaseTool):
#     """
#     Custom tool to validate table names and columns against the database schema.
#     """

#     def _run(self, query: str) -> str:
#         raw_output = super()._run(query)
#         parsed_output: pd.DataFrame = None 
#         if isinstance(raw_output, str):
#             try:
#                 # Attempt to parse the output as a Python dictionary
#                 parsed_output = eval(raw_output, {"datetime": datetime})
#             except Exception as e:
#                 print("Ending up here", e)
#                 return "Too large context to process"
#         else:
#             parsed_output = raw_output

#         if isinstance(parsed_output, list) and len(parsed_output) > 0 and isinstance(parsed_output[0], (list, tuple, dict)):
#             df = pd.DataFrame(parsed_output)
#             if len(df) > 20:
#                 # Create file for full results
#                 os.makedirs("outputs", exist_ok=True)
#                 timestamp = TODAY.strftime("%Y%m%d_%H%M%S")
#                 filename = f"info_{timestamp}.csv"
#                 filepath = os.path.join("outputs", filename)
#                 df.to_csv(filepath, index=False)
#                 # Add to module-level tracking
#                 # global _current_session_files
#                 # _current_session_files.append(filepath)
#                 return f"\n{df.head(20).to_string(), df.describe().to_string()}\n\nfile_path={filepath}"
#             return df.to_string()
#         return str(parsed_output)

# sql_query_tool = SQLQueryTool(db=db, llm=CODE_MODEL, handle_tool_error=True)

sqltools = [sql_query_tool, sql_querychecker_tool, sql_list_database_tool, sql_schema_tool]
sqltools_node = ToolNode(sqltools)


today_date = TODAY.strftime("%d %b %Y")
def sqlagent_node(state):
    """
    SQL Agent that uses pre-initialized LLM to process natural language queries.
    Args:
        state (dict): Should contain 'query' with natural language question.
    Returns:
        Query result or error message.
    """
    
    system_prompt = f"""You are a SQL agent for CRM data analysis. Your PRIMARY tool is sql_query_tool - use it to execute queries and get results.

TABLES:
The CRM contains structured tables with the following entities:
1. Account: Table of Company-level metadata including industry, region, lifecycle stage, account score, and contact details.
2. Activity: Table of Sales and marketing engagement logs (type, outcome, score, action items).
3. Pipeline: Table of Deal progress with stages, close probability, deal size, and expected close dates.
4. Opportunity: Table of Product-linked opportunities with status, revenue, and creation/close dates.
5. Contract: Table of Active or expired contracts with values, types, and renewal status.
6. Support_Ticket: Table of Customer support issues linked to contracts with resolution times and satisfaction scores.
7. Product: Table of Metadata on all products and pricing details, including discounts and launch status.

WORKFLOW:
1. Use sql_query_tool to execute SQL queries directly
2. Only use other tools (schema, checker, list) if sql_query_tool fails
3. Keep trying different approaches until you get data
4. Focus on getting results, not perfect queries

RULES:
- sql_query_tool is your main tool - use it first and most often
- Other tools are utilities - use sparingly only when needed
- Don't quit after using utility tools - always return to sql_query_tool
- Use YEAR(), MONTH(), DAY() functions (not STRFTIME)
- Search with LIKE '%text%' for partial matches

Your job is to retrieve data only. After getting SQL results, format your response as:

"Executed [SQL query] and gathered info regarding [what the query found in general terms].

Results: [Show the actual query results/findings]

[Analysis decision]"

Analysis decision:
- If SQL result completely answers the user's question: "Analysis complete - SQL results fully answer the question."
- If SQL result needs specific additional work: "Analysis needed: [Specify exactly what analysis is required that SQL cannot do, e.g., 'statistical correlation analysis', 'trend forecasting', 'clustering analysis', 'predictive modeling']"

Decision Rules:
- Direct aggregations answering the exact question asked = Analysis complete
- Grouped business metrics (win rates, revenue by segments) answering the question = Analysis complete
- Raw data needing statistical analysis, predictions, or advanced analytics = Specify the exact analysis type needed

Always try to find some related data before giving up. Be specific about what analysis is needed - don't just say "further analysis"

Today: {today_date}"""

    
    try:
        model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=sqltools)
        response = model.invoke(state["messages"])
    except Exception:
        from utils.globals import FALLBACK_MODEL
        model = create_agent(FALLBACK_MODEL, system_message=system_prompt, tools=sqltools)
        response = model.invoke(state["messages"])
    
    return {"messages": [response]}