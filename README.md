# MCP Fetch Server – Render Deployment

This repository packages the official **Model Context Protocol (MCP) Fetch** server for easy deployment on [Render.com](https://render.com).

## What’s inside

| Path | Purpose |
|------|---------|
| `mcp_server_fetch/` | Up-stream MCP Fetch server code (copied from <https://github.com/modelcontextprotocol/servers/tree/main/src/fetch>). |
| `requirements.txt` | Minimal dependency list extracted from upstream `pyproject.toml`. |
| `start.sh` | Launch script Render executes (`python -m mcp_server_fetch --host 0.0.0.0 --port $PORT`). |
| `render.yaml` | Declarative Render service definition (starter plan, Python 3.11, health-check at `/sse`). |

## Deployment (Render)

1. **Push code to GitHub** – already pushed to `https://github.com/artem-getman/fetch-mcp`.
2. **Render dashboard → New Web Service**
   * Pick the GitHub repo.
   * Ensure the service name is **`mcp-fetch`** (this drives the subdomain `mcp-fetch.onrender.com`).
   * Render auto-reads `render.yaml`; no extra config needed.
3. Wait for build & deploy. Health check passes when `/sse` returns HTTP 200.
4. Confirm SSE endpoint:
   ```bash
   curl https://mcp-fetch.onrender.com/sse --no-buffer | head -n 5
   ```

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m mcp_server_fetch --host 0.0.0.0 --port 8000
# In another shell:
curl http://localhost:8000/sse --no-buffer | head -n 5
```

## Next tasks / open items

* **Automate Render deploy** – Use Render API to create service & poll status programmatically.
* **CI** – Add GitHub Actions to run lint (`ruff`) & type-check (`pyright`).
* **Docker** – Optional lightweight container for local testing.
* **Docs** – Expand usage examples for fetch tool.
