#!/bin/bash

# Start Ollama service in background
ollama serve &

# Wait for Ollama to be ready
sleep 10

# Start your application
python app.py