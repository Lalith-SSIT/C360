from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import pandas as pd
from utils.globals import CHAT_MODEL, FALLBACK_MODEL
from langchain_core.messages import AIMessage

def analysisagent_node(state):
    dataframes = []
    for files in state["files"]:
        df = pd.read_csv(files)
        dataframes.append(df)

    agent_executor = create_pandas_dataframe_agent(
        CHAT_MODEL,
        dataframes,
        agent_type="tool-calling",
        prefix="Analyze the data as if you were a sales co pilot who need to provide valuable insights based on the request.",
        allow_dangerous_code=True)

    # Get the original user query (not the system message)
    user_query = state["messages"][-1].content if hasattr(state["messages"][-1], 'content') else str(state["messages"][0])
    response = agent_executor.invoke({"input": user_query})
    return {"messages": AIMessage(response["output"])}