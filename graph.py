from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, START, END
from agents.supervisor import supervisor_node
from agents.ragagent import ragagent_node, ragtools_node
from agents.sqlagent import sqlagent_node, sqltools_node, sqltools
from agents.analysisagent import analysisagent_node
from agents.businessagent import businessagent_node
from utils.statehandler import AgentState
from langgraph.prebuilt import tools_condition


def route_supervisor(state):
    return state.get("next", "Business Agent")

# def file_parser_node(state):
#     """Parse file paths from agent response and add to state"""
#     files = []
    
#     # Check if response contains file_path
#     if state["messages"] and hasattr(state["messages"][-1], 'content'):
#         content = state["messages"][-1].content
#         if "file_path=" in content:
#             # Extract file path
#             lines = content.split('\n')
#             for line in lines:
#                 if line.startswith("file_path="):
#                     filepath = line.replace("file_path=", "")
#                     files.append(filepath)
            
#             # Clean the response content
#             state["messages"][-1].content = content.replace(f"file_path={filepath}", "").strip()
    
#     result = {"messages": state["messages"]}
#     if files:
#         result["files"] = files
#     return result

# def human_input_node(state):
#     """Get user input and continue conversation"""
#     user_input = input("\nYour question (type 'end' to quit): ")
#     if user_input.lower() == 'end':
#         return {"messages": [("user", "end")], "next": "END"}
#     return {"messages": [("user", user_input)]}

# def should_continue(state):
#     """Check if conversation should continue"""
#     last_message = state["messages"][-1] if state["messages"] else None
#     if last_message and hasattr(last_message, 'content') and last_message.content == "end":
#         return "END"
#     return "Supervisor"

# Under development
def error_fallback(state):
    if "Error" in state["messages"][-1].content and state["messages"][-1].name in sqltools:
        print("Error detected in the last message. Retrying...")
        if state["counter"] < 5:
            print("continue to work from here")
    


graph = StateGraph(AgentState)
# graph.add_node('Human', human_input_node)
graph.add_node('Supervisor', supervisor_node)
graph.add_node('RAG Agent', ragagent_node)
graph.add_node('SQL Agent', sqlagent_node)
graph.add_node('Analysis Agent', analysisagent_node)
graph.add_node('Business Agent', businessagent_node)
graph.add_node('RAG_Tools', ragtools_node)
graph.add_node('SQL_Tools', sqltools_node)

graph.add_edge(START, 'Supervisor')
# graph.add_conditional_edges('Human', should_continue, {"Supervisor": "Supervisor", "END": END})
graph.add_conditional_edges('Supervisor', route_supervisor, {"RAG Agent": "RAG Agent", "SQL Agent": "SQL Agent", "Analysis Agent": "Analysis Agent", "Business Agent": "Business Agent"})
graph.add_conditional_edges('RAG Agent', tools_condition, {"tools": "RAG_Tools", "__end__": "Supervisor"})
graph.add_conditional_edges('SQL Agent', tools_condition, {"tools": "SQL_Tools", "__end__": "Supervisor"})
graph.add_edge('Analysis Agent', 'Supervisor')
graph.add_edge('RAG_Tools', 'RAG Agent')
graph.add_edge('SQL_Tools', 'SQL Agent')
graph.add_edge('Business Agent', END)
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