import os
from dotenv import load_dotenv
from huggingface_hub import login
load_dotenv()
login(os.getenv("HUGGINGFACEHUB_API_TOKEN"))


from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import uvicorn
import uuid
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from graph import app as graph_app

api = FastAPI()

# UUID -> List of messages mapping
sessions: Dict[str, Dict] = {}

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# def cleanup_expired_sessions():
#     cutoff = datetime.now() - timedelta(minutes=4)
#     expired = [sid for sid, data in sessions.items() if data['last_activity'] < cutoff]
#     for sid in expired:
#         del sessions[sid]
@api.get("/sessions")
def get_sessions():
    return sessions

@api.post("/chat")
def chat(request: ChatRequest):
    # cleanup_expired_sessions()
    
    # Create new session or get existing
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'messages': [],
            'last_activity': datetime.now()
        }
    else:
        session_id = request.session_id
    
    session = sessions[session_id]
    
    # Handle end command
    if request.query.lower() == 'end':
        # del sessions[session_id]
        return ChatResponse(response="Session ended", session_id=session_id)
    
    # Add user query to existing messages
    session['messages'].append(("user", request.query))
    session['last_activity'] = datetime.now()
    
    response = graph_app.invoke(
        {"messages": session['messages']},
        {"recursion_limit": 150},
        )
    
    session["messages"].append(("assistant", response["messages"][-1].content))
    return {"response": response["messages"][-1].content, "session_id": session_id} if not isinstance(response, HumanMessage) else "Nothing to respond"

    # def generate_stream():
        # events = graph_app.stream(
        #     {"messages": session['messages']},
        #     {"recursion_limit": 150},
        #     stream_mode="values"
        # )
        
        # for event in events:
        #     if "messages" in event and event["messages"]:
        #         last_msg = event["messages"][-1]
        #         print(last_msg.pretty_print())
        #         if last_msg.__class__.__name__ == 'HumanMessage':
        #             continue
        #         if hasattr(last_msg, 'content') and last_msg.content:
        #             data = {"response": last_msg.content,
        #                     "session_id": session_id}
        #             session['messages'].append(("assistant", last_msg.content))
        #             yield f"{json.dumps(data)}\n"
    
    # return StreamingResponse(generate_stream(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)