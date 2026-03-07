"""Sprint 5: One-click deployment for generated MCP servers.

Generates cloud deployment configs (Docker Compose, fly.toml, Railway,
render.yaml) and a deploy CLI command so users can go from
  agent-see convert → agent-see deploy
with zero infrastructure setup.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_docker_compose(server_dir: Path) -> str:
    """Generate docker-compose.yml for local/cloud deployment."""
    return """version: "3.8"

services:
  mcp-server:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    environment:
      - TARGET_URL=${TARGET_URL}
      - API_KEY=${API_KEY:-}
      - API_KEY_HEADER=${API_KEY_HEADER:-}
      - API_KEY_VALUE=${API_KEY_VALUE:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost', 8000)); s.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
"""


def generate_fly_toml(app_name: str) -> str:
    """Generate fly.toml for Fly.io deployment."""
    safe_name = app_name.replace(".", "-").replace("/", "-").replace(":", "-")[:30]
    return f"""app = "{safe_name}"
primary_region = "iad"

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[env]
  PORT = "8000"
"""


def generate_railway_config() -> str:
    """Generate railway.json for Railway deployment."""
    return json.dumps(
        {
            "$schema": "https://railway.app/railway.schema.json",
            "build": {"builder": "DOCKERFILE", "dockerfilePath": "Dockerfile"},
            "deploy": {
                "numReplicas": 1,
                "startCommand": "python server.py",
                "healthcheckPath": "/",
                "restartPolicyType": "ON_FAILURE",
            },
        },
        indent=2,
    )


def generate_render_yaml(app_name: str) -> str:
    """Generate render.yaml for Render deployment."""
    safe_name = app_name.replace(".", "-").replace("/", "-")[:30]
    return f"""services:
  - type: web
    name: {safe_name}
    runtime: docker
    plan: free
    healthCheckPath: /
    envVars:
      - key: TARGET_URL
        sync: false
      - key: API_KEY
        sync: false
      - key: PORT
        value: 8000
"""


def generate_env_example() -> str:
    """Generate .env.example showing required config."""
    return """# Target SaaS URL (required)
TARGET_URL=https://your-saas-site.com

# Authentication (optional - choose one method)
# Method 1: Bearer token
API_KEY=your-api-key-here

# Method 2: Custom header
# API_KEY_HEADER=X-API-Key
# API_KEY_VALUE=your-api-key-here

# Server port
PORT=8000
"""


def generate_deploy_script() -> str:
    """Generate a deploy.sh helper script."""
    return """#!/bin/bash
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
"""


def generate_deployment_configs(
    server_dir: Path,
    app_name: str = "mcp-server",
) -> dict[str, Path]:
    """Generate all deployment configuration files.

    Args:
        server_dir: The MCP server output directory
        app_name: Application name for cloud deployments

    Returns:
        Dict mapping config name to file path
    """
    configs: dict[str, Path] = {}

    # Docker Compose
    compose_path = server_dir / "docker-compose.yml"
    compose_path.write_text(generate_docker_compose(server_dir))
    configs["docker_compose"] = compose_path

    # Fly.io
    fly_path = server_dir / "fly.toml"
    fly_path.write_text(generate_fly_toml(app_name))
    configs["fly_toml"] = fly_path

    # Railway
    railway_path = server_dir / "railway.json"
    railway_path.write_text(generate_railway_config())
    configs["railway"] = railway_path

    # Render
    render_path = server_dir / "render.yaml"
    render_path.write_text(generate_render_yaml(app_name))
    configs["render"] = render_path

    # .env.example
    env_path = server_dir / ".env.example"
    env_path.write_text(generate_env_example())
    configs["env_example"] = env_path

    # deploy.sh
    deploy_path = server_dir / "deploy.sh"
    deploy_path.write_text(generate_deploy_script())
    deploy_path.chmod(0o755)
    configs["deploy_script"] = deploy_path

    logger.info(f"Generated {len(configs)} deployment configs in {server_dir}")
    return configs
