from langchain_community.utilities import SQLDatabase
from utils.globals import CHAT_MODEL, CODE_MODEL, TODAY
from utils.agentutils import create_agent
from langgraph.prebuilt import ToolNode
from langchain_community.tools.sql_database.tool import ListSQLDatabaseTool, QuerySQLCheckerTool, QuerySQLDatabaseTool, InfoSQLDatabaseTool
from sqlalchemy import create_engine
import ast
import pandas as pd
import os
import datetime
import uuid

# SQL Server connection configuration - initialize once
connection_string = "mssql+pyodbc://@DESKTOP-4J53D2I\\C360/C360?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(connection_string)
db = SQLDatabase(engine=engine, include_tables=["Opportunity", "Account", "Product", "Support_Ticket", "Pipeline", "Activity", "Contract"])

# Module-level variable to track current session's files
# _current_session_files = []

from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool

# @tool(parse_docstring=True)
# def sql_query_tool(
#     query: Annotated[str, "A detailed and correct SQL query."], 
#     state: Annotated[dict, InjectedState]
# ) -> str:
#     """Execute a SQL query against the database and get back the result.
#     If the query is not correct, an error message will be returned.
#     If an error is returned, rewrite the query, check the query, and try again.

#     Args:
#         query: A detailed and correct SQL query.
#     """
    
#     # Your existing SQL execution logic
#     db_tool = QuerySQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
#     raw_output = db_tool._run(query)
    
#     # Check if raw_output is an error message
#     # if isinstance(raw_output, str) and ("Error:" in raw_output or "error" in raw_output.lower()):
#     #     return raw_output
    
#     # Your existing parsing logic
#     if isinstance(raw_output, str):
#         try:
#             parsed_output = eval(raw_output, {"datetime": datetime})
#         except Exception as e:
#             return f"{raw_output}"
#     else:
#         parsed_output = raw_output

#     if isinstance(parsed_output, list) and len(parsed_output) > 0:
#         df = pd.DataFrame(parsed_output)
#         if len(df) > 20:
#             # Create file
#             os.makedirs("outputs", exist_ok=True)
#             timestamp = TODAY.strftime("%Y%m%d_%H%M%S")
#             filename = f"info_{timestamp}.csv"
#             filepath = os.path.join("outputs", filename)
#             df.to_csv(filepath, index=False)
            
#             # Directly update state
#             if "files" not in state:
#                 state["files"] = []
#             state["files"].append(filepath)
            
#             # Return clean output without file_path
#             return f"\n{df.head(20).to_string()}, {df.describe().to_string()}\n\n"
#         return df.to_string()
#     return str(parsed_output)


sql_query_tool = QuerySQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
sql_querychecker_tool = QuerySQLCheckerTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
sql_list_database_tool = ListSQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)
# sql_schema_tool = InfoSQLDatabaseTool(db=db, llm=CODE_MODEL, handle_tool_error=True)

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


date = TODAY.strftime("%d %b %Y")
def sqlagent_node(state):
    """
    SQL Agent that uses pre-initialized LLM to process natural language queries.
    Args:
        state (dict): Should contain 'query' with natural language question.
    Returns:
        Query result or error message.
    """
    
    system_prompt = f"""You are an AI Sales Co-Pilot integrated with a CRM system backed by a relational database.

The CRM contains structured tables with the following entities:
1. Account: Table of Company-level metadata including industry, region, lifecycle stage, account score, and contact details.
2. Activity: Table of Sales and marketing engagement logs (type, outcome, score, action items).
3. Pipeline: Table of Deal progress with stages, close probability, deal size, and expected close dates.
4. Opportunity: Table of Product-linked opportunities with status, revenue, and creation/close dates.
5. Contract: Table of Active or expired contracts with values, types, and renewal status.
6. Support_Ticket: Table of Customer support issues linked to contracts with resolution times and satisfaction scores.
7. Product: Table of Metadata on all products and pricing details, including discounts and launch status.

Your job is to:
- Interpret queries from sales representatives
- Retrieve structured data to provide insights
- Recommend personalized next steps, emails, talking points, or actions
- Surface risks, cross-sell/upsell opportunities, or churn signals
- Maintain a business-professional yet helpful and actionable tone

Considerations:
- Use fields like Stage, Expected_Close_date, Deal_Size, and Probability to predict win chances
- Use Customer_Satisfaction_Score, Issue_Type, and Contract_Value to assess account health
- Suggest actions from Activity and Action_item fields
- Recommend follow-ups based on Opportunity_Status, Pipeline_Stage, and Contract_End_Date

TECHNICAL EXECUTION:
1. Start with sql_list_database_tool to get actual table names
2. If you get "Invalid object name" errors, use the real table names from step 1
3. Make sure you are following proper column names and types and case sensitivity
4. Get table schemas to see actual column names
5. Search across text columns using LIKE with wildcards
6. When a query fails, immediately try the next logical approach
7. Do not use STRFTIME as it is not supported, instead check with Year, Month, Day functions
8. Do not execute all the tools everytime.

ERROR RECOVERY: If sql_query_tool returns an error:
- Read the error message carefully
- Use actual table/column names (not placeholders) which you can get from sql_info_tool
- Try different tables or search patterns
- Continue until you find the data or exhaust all options

Output Format:
- Response: A personalized, data-informed message, insight, or action plan
- Rationale: Provide a clear, concise, and structured explanation of why this response makes sense. Highlight data points, context, and any assumptions made. Ensure the explanation is understandable to a business leader without technical jargon.
- Next Steps: Suggest 1-3 actionable recommendations that the user (sales rep, manager, or leader) can take to move forward. The steps must be practical, context-aware, and aligned with sales objectives (e.g., advancing deals, improving forecasts, strengthening customer relationships, or reducing churn).

Today's date: {date}
    """

    
    model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=sqltools)
    response = model.invoke(state["messages"])
    
    result = {"messages": [response]}
    return result