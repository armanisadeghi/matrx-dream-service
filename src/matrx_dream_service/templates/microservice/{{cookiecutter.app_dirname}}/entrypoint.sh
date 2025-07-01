#!/bin/bash

# Disable exit on error to allow the script to continue even if a command fails
set +e

# Activate UV virtual environment
source /app/.venv/bin/activate

# Load environment variables from .env if it exists
if [ -f /app/.env ]; then
    echo "Loading environment variables from /app/.env"
    set -o allexport
    source /app/.env
    set +o allexport
else
    echo "/app/.env not found, proceeding without loading environment variables."
fi

# Ensure python-dotenv is installed
uv pip install python-dotenv

# Start the application
echo "Starting application..."
python run.py