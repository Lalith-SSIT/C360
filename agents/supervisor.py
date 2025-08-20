from utils.statehandler import AgentState
# from langgraph.types import Command
from utils.globals import CHAT_MODEL
from utils.agentutils import create_agent
# from utils.retriever import retrieve_documents


def supervisor_node(state: AgentState):
    """
    Supervisor node that decides which agent to run based on the latest message using HuggingFace chat model.
    The LLM itself determines the next agent by returning 'sql_agent' or 'rag_agent'.
    """

    # Get the latest message
    latest_message = state["messages"][-1].content

    # Prompt the LLM to decide the next agent with explicit rules and examples
    system_prompt = """You are a supervisor agent. Decide which agent should handle the query:

**SQL Agent - Use for:**
- Specific data queries with estimable size (counts, top N records, specific columns)
- Database operations: "List top 5 accounts based on least ticket count"
- Aggregations: "List top 2 stages in pipeline based on their count"
- Filtered queries: "Show opportunities with status 'active'"

**RAG Agent - Use for:**
- Comprehensive data requests: "Give me the entire data of IBM"
- Unstructured information: "Give me the opportunities status" (explanation/meaning)


**Rules:**
1. If query asks for specific, limited database records or columns like asking lists, anything that involves metric alculation like avg, max → sql_agent
2. If query asks for comprehensive/entire data or explanations → rag_agent
3. If unsure → rag_agent

**Response Format:**
First line: agent name (sql_agent or rag_agent)
Second line: reasoning

Example:
Query: "Tell me all the products that comes under software products"
sql_agent
Because the query asks for products that are filtered based on the category=software.

Query: "Summarize the data available in opportunities"
rag_agent
Because the query asks for comprehensive/entire data which is unstructured and large."""
    
    model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=[])
    # response = model.invoke([
    #     {"role": "user", "content": latest_message}
    # ])
    response = model.invoke(state["messages"])
    response_text = response.content.strip() if hasattr(response, "content") else str(response).strip()
    
    # Extract agent from first line
    first_line = response_text.split('\n')[0].strip().lower()
    
    # Determine next agent based on LLM response
    if "sql_agent" in first_line:
        next_agent = "SQL Agent"
    elif "rag_agent" in first_line:
        next_agent = "RAG Agent"
    else:
        next_agent = "RAG Agent"  # Default fallback
    
    return {"next": next_agent}