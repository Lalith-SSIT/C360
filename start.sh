#!/bin/bash

# Start Ollama service in background
ollama serve &

# Wait for Ollama to be ready
sleep 10

# Start your application
python app.py &
API_PID=$!
sleep 10
exec streamlit run streamlit_app.py --server.port=8051 --server.address=0.0.0.0