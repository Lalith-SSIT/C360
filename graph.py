from langgraph.graph import StateGraph, START, END
from agents.supervisor import supervisor_node
from agents.ragagent import ragagent_node, ragtools_node
from agents.sqlagent import sqlagent_node, sqltools_node, sqltools
from utils.statehandler import AgentState
from langgraph.prebuilt import tools_condition


def route_supervisor(state):
    return state.get("next", "RAG Agent")

def human_input_node(state):
    """Get user input and continue conversation"""
    user_input = input("\nYour question (type 'end' to quit): ")
    if user_input.lower() == 'end':
        return {"messages": [("user", "end")], "next": "END"}
    return {"messages": [("user", user_input)]}

def should_continue(state):
    """Check if conversation should continue"""
    last_message = state["messages"][-1] if state["messages"] else None
    if last_message and hasattr(last_message, 'content') and last_message.content == "end":
        return "END"
    return "Supervisor"

# Under development
def error_fallback(state):
    if "Error" in state["messages"][-1].content and state["messages"][-1].name in sqltools:
        print("Error detected in the last message. Retrying...")
        if state["counter"] < 5:
            print("continue to work from here")
    


graph = StateGraph(AgentState)
graph.add_node('Human', human_input_node)
graph.add_node('Supervisor', supervisor_node)
graph.add_node('RAG Agent', ragagent_node)
graph.add_node('SQL Agent', sqlagent_node)
graph.add_node('RAG_Tools', ragtools_node)
graph.add_node('SQL_Tools', sqltools_node)

graph.add_edge(START, 'Supervisor')
# graph.add_conditional_edges('Human', should_continue, {"Supervisor": "Supervisor", "END": END})
graph.add_conditional_edges('Supervisor', route_supervisor, {"RAG Agent": "RAG Agent", "SQL Agent": "SQL Agent"})
graph.add_conditional_edges('RAG Agent', tools_condition, {"tools": "RAG_Tools", "__end__": END})
graph.add_conditional_edges('SQL Agent', tools_condition, {"tools": "SQL_Tools", "__end__": END})
graph.add_edge('RAG_Tools', 'RAG Agent')
graph.add_edge('SQL_Tools', 'SQL Agent')
app = graph.compile()
       

if __name__ == "__main__":
    print("Welcome! Ask me anything about your data.")
    
    try:
        # Save the graph as a PNG image
        graph_image_path = "images/graph.png"
        app.get_graph().draw_mermaid_png(output_file_path=graph_image_path)
    except Exception as e:
        print(f"Graph visualization error: {e}")
    
    # # Start conversation loop
    # events = app.stream(
    #     {"messages": []},
    #     {"recursion_limit": 150},
    #     stream_mode="values"
    # )

    # for event in events:
    #     if "messages" in event and event["messages"]:
    #         last_msg = event["messages"][-1]
    #         if hasattr(last_msg, 'content') and last_msg.content != "end":
    #             print(last_msg.pretty_print())