import json
from utils.statehandler import AgentState
from utils.globals import CHAT_MODEL, FALLBACK_MODEL
from utils.retriever import retrieve_documents
from langchain_core.tools import tool
from typing_extensions import Annotated, Optional
from utils.agentutils import create_agent
from langgraph.prebuilt import ToolNode

@tool(parse_docstring=True)
def retrieve_documents_tool(query: Annotated[str, "Detailed search query for which to retrieve documents."], k: Annotated[Optional[int], "The number of top documents to return. Defaults to 5."] = 5):
    """
    Retrieve the top-k most relevant documents for a given query using an ensemble of semantic and keyword (BM25) retrieval.

    Args:
        query (str): Detailed search query for which to retrieve documents.
        k (int, optional): The number of top documents to return. Defaults to 5.

    Returns:
        List[dict]: A list of processed opportunity data as dictionaries.
    """
    docs = retrieve_documents(query, k)

    processed_docs = []
    for doc in docs:
        data = json.loads(doc.page_content)
        # data['score'] = doc.metadata.get('score', 0)
        processed_docs.append(data)
    return processed_docs

ragtools = [retrieve_documents_tool]
ragtools_node = ToolNode(ragtools)

def ragagent_node(state: AgentState):
    """
    RAG agent node: fetches related documents using retriever and passes them to the LLM based on the latest message.
    """
    system_prompt = """You MUST always call the retrieve_documents_tool first to get relevant information before answering any query. 
    Use the user's query as the search parameter. After getting the documents, provide a detailed answer based on the retrieved information."""
    
    try:
        model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=ragtools)
        response = model.invoke(state["messages"])
    except Exception:
        model = create_agent(FALLBACK_MODEL, system_message=system_prompt, tools=ragtools)
        response = model.invoke(state["messages"])
    
    return {"messages": [response]}