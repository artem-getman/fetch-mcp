from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import asyncio, time
import json
from mcp_server_fetch.server import fetch_url, Fetch, check_may_autonomously_fetch_url
from mcp.types import TextContent
from pydantic import ValidationError

app = FastAPI()

# Allow browser-based clients (Claude settings panel) to access SSE
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

async def event_stream():
    """Minimal SSE stream to satisfy Render health check / Claude handshake."""
    # Immediately send a greeting event, then keepalive pings every 30s.
    yield "event: hello\ndata: fetch-mcp ready\n\n"
    while True:
        await asyncio.sleep(30)
        yield f"event: ping\ndata: {int(time.time())}\n\n"

@app.get("/sse")
async def sse_get() -> StreamingResponse:
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/sse")
async def sse_post() -> StreamingResponse:
    # Claude settings panel first POSTs then GETs; return same stream.
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# -- Minimal OAuth2 discovery & dynamic client registration stubs --
@app.get("/.well-known/oauth-authorization-server")
async def oauth_discovery(request: Request):
    base = str(request.base_url).rstrip("/")  # e.g. https://fetch-mcp-bydg.onrender.com
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "grant_types_supported": ["client_credentials"],
        "response_types_supported": ["token"],
    }

@app.post("/register")
async def oauth_register():
    return {
        "client_id": "fetch-mcp-public-client",
        "client_id_issued_at": int(time.time()),
        "token_endpoint_auth_method": "none",
    }

@app.post("/token")
async def oauth_token(request: Request):
    # Handle both client_credentials flow and authorization_code flow
    form_data = await request.form()
    grant_type = form_data.get("grant_type", "client_credentials")
    
    # Return a static bearer token regardless of flow type
    # A real implementation would validate the code/client/etc.
    return {
        "access_token": "fetch-mcp-access-token", 
        "token_type": "bearer", 
        "expires_in": 3600
    }

@app.get("/authorize")
async def oauth_authorize(response_type: str, client_id: str, redirect_uri: str, state: str, 
                        code_challenge: str = None, code_challenge_method: str = None,
                        scope: str = None):
    # For simplicity, auto-authorize and redirect immediately with a dummy code
    # In production, this would typically show a consent screen
    from urllib.parse import urlencode
    params = {"code": "auth_code_12345", "state": state}
    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return Response(status_code=302, headers={"Location": redirect_url})

# Quiet 404s for / and favicons
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

# MCP Protocol endpoints
@app.get("/mcp")
async def mcp_sse():
    """MCP Server-Sent Events endpoint for real-time communication"""
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/mcp")
async def handle_mcp(request: Request):
    """Handle MCP JSON-RPC 2.0 requests"""
    try:
        data = await request.json()
        
        # Validate JSON-RPC 2.0 format
        if data.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"}
            }
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        if method == "tools/list":
            # Return available tools
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "fetch",
                            "description": """Fetches a URL from the internet and optionally extracts its contents as markdown.

Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access. Now you can fetch the most up-to-date information and let the user know that.""",
                            "inputSchema": Fetch.model_json_schema()
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            # Execute tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name != "fetch":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": "Method not found"}
                }
            
            try:
                # Parse and validate arguments
                args = Fetch(**arguments)
                url = str(args.url)
                
                # Check robots.txt
                await check_may_autonomously_fetch_url(
                    url, 
                    "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)"
                )
                
                # Fetch the URL
                content, prefix = await fetch_url(
                    url, 
                    "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)",
                    force_raw=args.raw
                )
                
                # Handle pagination
                original_length = len(content)
                if args.start_index >= original_length:
                    content = "<error>No more content available.</error>"
                else:
                    truncated_content = content[args.start_index : args.start_index + args.max_length]
                    if not truncated_content:
                        content = "<error>No more content available.</error>"
                    else:
                        content = truncated_content
                        actual_content_length = len(truncated_content)
                        remaining_content = original_length - (args.start_index + actual_content_length)
                        if actual_content_length == args.max_length and remaining_content > 0:
                            next_start = args.start_index + actual_content_length
                            content += f"\n\n<error>Content truncated. Call the fetch tool with a start_index of {next_start} to get more content.</error>"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"{prefix}Contents of {url}:\n{content}"
                            }
                        ]
                    }
                }
                
            except ValidationError as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Invalid params: {str(e)}"}
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"}
            }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }

