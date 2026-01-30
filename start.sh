#!/bin/bash

# AI Agriculture Advisors - Start Script
# Usage: ./start.sh

set -e

# Load environment variables from .env if present
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

# Load port from .env or use default
PORT=${PORT:-8123}

echo "Starting AI Agriculture Advisors on port $PORT..."
uv run uvicorn main:app --reload --port $PORT
