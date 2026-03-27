#!/bin/bash
set -e

echo "=== Agent-See MCP Server Deployment ==="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your TARGET_URL and API credentials."
    exit 1
fi

# Source .env
export $(grep -v '^#' .env | xargs)

if [ -z "$TARGET_URL" ] || [ "$TARGET_URL" = "https://your-saas-site.com" ]; then
    echo "ERROR: Please set TARGET_URL in .env"
    exit 1
fi

# Detect deployment method
if command -v flyctl &> /dev/null; then
    echo "Fly.io detected. Deploying with flyctl..."
    flyctl deploy
elif command -v railway &> /dev/null; then
    echo "Railway detected. Deploying with railway..."
    railway up
elif command -v docker &> /dev/null; then
    echo "Docker detected. Building and running locally..."
    docker compose up --build -d
    echo ""
    echo "MCP server running at http://localhost:${PORT:-8000}"
else
    echo "No deployment tool found. Options:"
    echo "  1. Install Docker: docker compose up --build"
    echo "  2. Install Fly.io: flyctl deploy"
    echo "  3. Install Railway: railway up"
    echo "  4. Run directly: pip install -e . && python server.py"
fi
