from langchain_ollama import ChatOllama
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, List
import json
from dotenv import load_dotenv

load_dotenv()

# Define tools
@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions"""
    try:
        return str(eval(expression))
    except:
        return "Invalid expression"

@tool
def weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather in {city}: Sunny, 25°C"

# State
class AgentState(TypedDict):
    messages: List[dict]

# Initialize model and bind tools
llm = ChatOllama(model="llama3.1")
tools = [calculator, weather]
llm_with_tools = llm.bind_tools(tools)

# Nodes
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    return "tools" if hasattr(last_message, 'tool_calls') and last_message.tool_calls else END

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()

# Run
if __name__ == "__main__":
    result = app.invoke({"messages": [{"role": "user", "content": "Calculate 15 * 7"}]})
    print(result["messages"][-1].content)