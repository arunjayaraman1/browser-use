#!/bin/bash
# Script to run the Streamlit UI

echo "Starting Streamlit UI..."
echo "UI will be available at http://localhost:8501"
echo ""

# Check if streamlit is installed, if not, install it
if ! uv run python -c "import streamlit" 2>/dev/null; then
	echo "Streamlit not found. Installing..."
	uv pip install streamlit requests
fi

# Try port 8501, if busy try 8502, then 8503
PORT=8501
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
	echo "Port $PORT is in use, trying next port..."
	PORT=$((PORT + 1))
	if [ $PORT -gt 8510 ]; then
		echo "Error: Could not find available port between 8501-8510"
		exit 1
	fi
done

echo "Starting Streamlit UI on port $PORT..."
uv run streamlit run backend/ui.py --server.port $PORT
