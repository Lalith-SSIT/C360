from pydantic import BaseModel
from typing_extensions import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str
    current: str
    counter: int
    files: Annotated[List[str], lambda x, y: x + y]