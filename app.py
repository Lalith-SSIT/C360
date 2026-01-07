import os
from dotenv import load_dotenv

# Load environment files with precedence: .env.local > .env.dev
# load_dotenv('.env.dev')  # Load dev first
load_dotenv('.env.local')  # Local overrides dev
# from huggingface_hub import login
# login(token=os.getenv("HUGGINGFACEHUB_API_TOKEN"))


from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from graph import app as graph_app
from utils.logger import get_c360_logger
from fastapi.middleware.cors import CORSMiddleware



server_logger = get_c360_logger('server_app', level=logging.INFO, console=True)

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UUID -> List of messages mapping
sessions: Dict[str, Dict] = {}

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    files: Optional[list] = []

class SessionData(BaseModel):
    messages: list
    last_activity: datetime

# def cleanup_expired_sessions():
#     cutoff = datetime.now() - timedelta(minutes=4)
#     expired = [sid for sid, data in sessions.items() if data['last_activity'] < cutoff]
#     for sid in expired:
#         del sessions[sid]
@api.get("/sessions", response_model=Dict[str, SessionData])
def get_sessions():
    return sessions

import asyncio

@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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
        
        # Run synchronous invoke in a thread pool with a timeout
        try:
            # Initialize full state for the graph
            initial_state = {
                "messages": session['messages'][-2:],
                "next": "Supervisor",
                "current": "Supervisor",
                "counter": 0,
                "files": []
            }
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    graph_app.invoke,
                    initial_state,
                    {"recursion_limit": 100}, # 100 is safer for multi-agent loops
                ),
                timeout=300.0  # 300 second timeout
            )
        except asyncio.TimeoutError:
            server_logger.error(f"Graph execution timed out for session {session_id}")
            return {"response": "The request timed out. Please try a simpler question or try again later.", "session_id": session_id}
        except Exception as graph_err:
            server_logger.error(f"Graph invocation failed: {str(graph_err)}")
            raise graph_err
        
        if response and "messages" in response and response["messages"] and hasattr(response["messages"][-1], 'content'):
            content = response["messages"][-1].content
            if isinstance(content, list):
                content = "\n".join(content)
            session["messages"].append(("assistant", content))
            
            server_logger.info(f"Generated response for session {session_id}: {content[:100]}...")
            
            files = response.get("files", [])
            if files:
                server_logger.info(f"Response includes files: {files}")
            
            return {"response": content, "session_id": session_id, "files": files}
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

def start_server():
    host = os.getenv("HOST", "0.0.0.0")
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    
    server_logger.info(f"Starting Sales Copilot server on {host}:{port}")
    uvicorn.run(api, host=host, port=port, workers=workers)

if __name__ == "__main__":
    start_server()