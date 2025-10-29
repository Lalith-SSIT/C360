#!/bin/bash

# Load and export environment variables (Enable this if you are running outside docker)
<<<<<<< HEAD
# set -a
# source .env.local
# set +a
=======
set -a
source .env.dev
set +a
>>>>>>> dev

# Start Streamlit in background
streamlit run streamlit_app.py --server.port=8051 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

# Start FastAPI application
python app.py &
API_PID=$!

# Wait for both processes
wait $STREAMLIT_PID $API_PID