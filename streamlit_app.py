import streamlit as st
import requests
import time
import pandas as pd
import io
import logging
from utils.logger import get_c360_logger

client_logger = get_c360_logger('streamlit_app', level=logging.INFO, console=True)

st.set_page_config(page_title="C360 - Customer Intelligence")

st.title("C360 - Customer 360 Intelligence Platform")
st.markdown("Ask questions about your customer data using natural language")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False
    
# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "files" in message and message["files"]:
            for filepath in message["files"]:
                st.dataframe(pd.read_csv(filepath))

def disable():
    st.session_state.processing = True



user_query = st.chat_input("Ask a question", key="user_input", disabled=st.session_state.processing, on_submit=disable())
# New Chat button
with st.container(gap="small", horizontal_alignment="right", vertical_alignment="bottom"):
    if st.button("🔄", key="new_chat", help="Start a new conversation"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


    if user_query:
        # Log user query
        client_logger.info(f"User query: {user_query}")
        
        # Set processing state and add user message
        st.session_state.processing = True
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        with st.chat_message("user"):
            st.write(user_query)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                raw_response = requests.post("http://localhost:8000/chat", json={"query": user_query, "session_id": st.session_state.get("session_id", "")})
                response_data = raw_response.json()
            
            # Store session_id and display response
            if response_data["session_id"]:
                st.session_state.session_id = response_data["session_id"]
            
            st.write(response_data["response"])
            
            # Display dataframes for current response
            if "files" in response_data and response_data["files"]:
                for filepath in response_data["files"]:
                    st.dataframe(pd.read_csv(filepath))
            
                # print(response_data["response"])
        
            # Log assistant response
            client_logger.info(f"Assistant response: {response_data['response']}")
            
            # for handler in client_logger.handlers:
            #     handler.flush()

            st.session_state.messages.append({"role": "assistant", "content": response_data["response"], "files": response_data["files"]})
        
        st.session_state.processing = False
        st.rerun()