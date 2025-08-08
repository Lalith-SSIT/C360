from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command
from langgraph.graph import END
from pydantic import BaseModel, Field


def create_agent(llm, system_message: str, tools=None):
    '''Create an agent'''
    prompt = ChatPromptTemplate(
    [
        (
            "system",
            "You have access to the following tools: \n{tool_names}. \nUse them appropriately. Below are the worker specific guidelines:\n\n{system_message}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]) if tools else [])
    output = prompt | llm.bind_tools(tools)
    return output


def agent_with_structured_op(llm, tool_choice=None, tools=None):
    llm_with_structure = llm.bind_tools(tools, tool_choice=tool_choice)
    return llm_with_structure