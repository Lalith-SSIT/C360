from utils.statehandler import AgentState
# from langgraph.types import Command
from utils.globals import CHAT_MODEL, FALLBACK_MODEL
from utils.globals import FALLBACK_MODEL
from utils.agentutils import create_agent
# from utils.retriever import retrieve_documents


def supervisor_node(state: AgentState):
    """
    Supervisor node that decides which agent to run based on the latest message using HuggingFace chat model.
    The LLM itself determines the next agent by returning 'sql_agent' or 'rag_agent'.
    """

    # Check if SQL agent has provided data for analysis
    # if len(state["messages"]) > 1 and "files" in state and state["files"]:
    #     prev_msg = state["messages"][-1].content
    #     if "data retrieved" in prev_msg.lower() or "analysis needed" in prev_msg.lower():
    #         return {"next": "Analysis Agent"}

    # Get the latest message
    latest_message = state["messages"][-1].content

    # Prompt the LLM to decide the next agent with explicit rules and examples
    system_prompt = """You are a supervisor agent that routes conversations based on context and task completion status.

**ROUTING LOGIC:**

**For INITIAL queries:**
- Data queries (lists, counts, aggregations) → sql_agent
- Comprehensive data requests → rag_agent  
- Analysis requests → sql_agent (to collect data first)
- Greetings → business_agent

**For FOLLOW-UP responses (analyze conversation context):**

**After SQL Agent responds:**
- If SQL provided complete answer with clear results/insights → business_agent (for final presentation)
- If SQL says data missing/unavailable but gave partial info → business_agent (to conclude with available info)
- If SQL collected raw data but explicitly states "Analysis decision: For further analysis" → analysis_agent
- If SQL had errors and needs to retry → sql_agent

**After Analysis Agent responds:**
- If Analysis provided insights/results → business_agent (for final presentation)
- If Analysis says needs different/more data → sql_agent (to get additional data)
- If Analysis says cannot perform analysis → business_agent (to conclude)

**After RAG Agent responds:**
- If RAG provided comprehensive answer → business_agent (for final presentation)
- If RAG suggests specific data queries → sql_agent

**DECISION FRAMEWORK:**
1. Is this the first message in conversation? → Route based on query type
2. Has an agent provided a complete/partial answer? → business_agent for conclusion
3. Does an agent request specific additional work? → Route to appropriate agent
4. Is the conversation stuck/no progress possible? → business_agent to conclude

**Response Format:**
Thinking: [Analyze conversation context and what's needed next]
Agent: [agent_name]
Reason: [Why this agent should handle next step]"""
    
    try:
        model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=[])
        # Pass full conversation context for better routing decisions
        response = model.invoke(state["messages"])
        response_text = response.content.strip() if hasattr(response, "content") else str(response).strip()
    except Exception:
        model = create_agent(FALLBACK_MODEL, system_message=system_prompt, tools=[])
        response = model.invoke([
            {"role": "user", "content": latest_message}
        ])
        response_text = response.content.strip() if hasattr(response, "content") else str(response).strip()
    
    # Extract agent from COT response
    lines = response_text.split('\n')
    agent_line = ""
    for line in lines:
        if line.strip().lower().startswith('agent:'):
            agent_line = line.strip().lower()
            break
    
    if not agent_line:
        # Fallback to first line if COT format not followed
        agent_line = lines[0].strip().lower()
    
    # Determine next agent based on LLM response
    if "sql_agent" in agent_line:
        next_agent = "SQL Agent"
    elif "rag_agent" in agent_line:
        next_agent = "RAG Agent"
    elif "analysis_agent" in agent_line:
        next_agent = "Analysis Agent"
    elif "business_agent" in agent_line:
        next_agent = "Business Agent"
    else:
        next_agent = "SQL Agent"  # Default fallback
    
    return {"next": next_agent}