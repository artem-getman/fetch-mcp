# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a deployment wrapper for the MCP (Model Context Protocol) Fetch server, packaged for easy deployment on Render.com. The project provides web fetching capabilities to AI models through both MCP protocol and HTTP endpoints.

## Architecture

The project consists of two main components:

1. **MCP Server** (`mcp_server_fetch/`) - Core MCP protocol implementation with web fetching capabilities
   - `server.py` - Main MCP server with fetch tool and prompt handlers
   - Supports robots.txt checking, HTML-to-markdown conversion, and content pagination
   - Runs via stdio protocol for MCP clients

2. **FastAPI Web Service** (`app.py`) - HTTP wrapper for Render deployment  
   - Provides `/sse` endpoint for health checks and Claude UI integration
   - Includes OAuth2 discovery endpoints for Claude integration
   - Handles CORS for browser-based clients

## Development Commands

### Local Development
```bash
# Set up virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server (for Render deployment)
uvicorn app:app --host 0.0.0.0 --port 8000

# Run MCP server directly (for MCP client testing)
python -m mcp_server_fetch --host 0.0.0.0 --port 8001
```

### Testing Endpoints
```bash
# Test SSE endpoint
curl http://localhost:8000/sse --no-buffer | head -n 5

# Test OAuth discovery
curl http://localhost:8000/.well-known/oauth-authorization-server
```

## Key Configuration

- **Render deployment**: Uses `start.sh` which runs the FastAPI app via uvicorn
- **Health check**: Render checks `/sse` endpoint  
- **Python version**: 3.11 (specified in `render.yaml`)
- **Dependencies**: Minimal set extracted from upstream MCP servers project

## MCP Server Features

The fetch server provides:
- `fetch` tool for autonomous web requests (respects robots.txt)
- `fetch` prompt for manual web requests (bypasses robots.txt)
- Content pagination via `start_index` and `max_length` parameters
- HTML-to-markdown conversion using readabilipy
- Custom User-Agent support and proxy configuration