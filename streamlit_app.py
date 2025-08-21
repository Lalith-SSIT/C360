import streamlit as st
import requests
import time
import pandas as pd
import io

st.set_page_config(page_title="C360 - Customer Intelligence", page_icon="🎯")

st.title("C360 - Customer 360 Intelligence Platform")
st.markdown("Ask questions about your customer data using natural language")

# with st.sidebar:
#     st.title("Chat Sessions")
#     try:
#         response = requests.get("http://localhost:8000/sessions")
#         sessions = response.json()
#         for session_id, session_data in sessions.items():
#             st.button(session_data['name'], key=session_id)
#     except:
#         st.write("No old sessions")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "files" in message and message["files"]:
            for filepath in message["files"]:
                st.dataframe(pd.read_csv(filepath))

user_query = st.chat_input("Ask a question", key="user_input")
if user_query:
    # Add and display user message immediately
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
        
        st.session_state.messages.append({"role": "assistant", "content": response_data["response"], "files": response_data["files"]})
        # st.session_state.messages.append({"role": "assistant", "content": response_data["response"]})
        st.rerun()