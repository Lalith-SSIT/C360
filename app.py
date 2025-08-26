import os
from dotenv import load_dotenv
from huggingface_hub import login
load_dotenv()
login(token=os.getenv("HUGGINGFACEHUB_API_TOKEN"))


from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import uvicorn
import uuid
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from graph import app as graph_app
from utils.logger import get_c360_logger

server_logger = get_c360_logger('server_app', level=logging.INFO, console=True)

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
    # Log incoming request
    server_logger.info(f"Received chat request: {request.query}")
    
    # cleanup_expired_sessions()
    
    # Create new session or get existing
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'messages': [],
            'last_activity': datetime.now()
        }
        server_logger.info(f"Created new session: {session_id}")
    else:
        session_id = request.session_id
        server_logger.info(f"Using existing session: {session_id}")
    
    session = sessions[session_id]
    
    # Handle end command
    if request.query.lower() == 'end':
        server_logger.info(f"Session ended: {session_id}")
        # del sessions[session_id]
        return ChatResponse(response="Session ended", session_id=session_id)
    
    # Add user query to existing messages
    session['messages'].append(("user", request.query))
    session['last_activity'] = datetime.now()
    
    try:
        server_logger.info(f"Processing query with graph app for session: {session_id}")
        response = graph_app.invoke(
            {"messages": session['messages'][-5:]},
            {"recursion_limit": 150},
        )
        
        if response and "messages" in response and response["messages"] and hasattr(response["messages"][-1], 'content'):
            content = response["messages"][-1].content
            if isinstance(content, list):
                content = "\n".join(content)
            session["messages"].append(("assistant", content))
            
            server_logger.info(f"Generated response for session {session_id}: {content[:100]}...")
            
            if response["files"] != None:
                server_logger.info(f"Response includes files: {response['files']}")
                return {"response": content, "session_id": session_id, "files": response["files"]}
            
            return {"response": content, "session_id": session_id}
        else:
            server_logger.warning(f"Improper response from model for session: {session_id}")
            return {"response": "Improper response from model", "session_id": session_id}
    except Exception as e:
        server_logger.error(f"Exception at endpoint for session {session_id}: {e}")
        return {"response": "No response from model", "session_id": session_id}

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
    server_logger.info("Starting C360 server on port 8000")
    uvicorn.run(api, host="0.0.0.0", port=8000)