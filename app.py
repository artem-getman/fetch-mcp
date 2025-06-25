from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import asyncio, time
import json
import logging
from mcp_server_fetch.server import fetch_url, Fetch, check_may_autonomously_fetch_url
from mcp.types import TextContent
from pydantic import ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """SSE stream for Claude MCP integration - proactively send tools"""
    # Send endpoint event first
    yield "event: endpoint\ndata: /mcp\n\n"
    
    # Wait a moment for initialization
    await asyncio.sleep(1)
    
    # Proactively send tools list since Claude doesn't request it
    tools_data = {
        "jsonrpc": "2.0",
        "method": "notifications/tools/list_changed",
        "params": {
            "tools": [
                {
                    "name": "fetch",
                    "description": "Fetch content from a URL and convert to markdown",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch"
                            },
                            "max_length": {
                                "type": "integer",
                                "default": 5000,
                                "description": "Maximum number of characters to return"
                            },
                            "raw": {
                                "type": "boolean", 
                                "default": False,
                                "description": "Return raw HTML instead of markdown"
                            }
                        },
                        "required": ["url"]
                    }
                }
            ]
        }
    }
    
    yield f"event: message\ndata: {json.dumps(tools_data)}\n\n"
    logger.info(f"Sent tools notification via SSE: {json.dumps(tools_data, indent=2)}")
    
    # Continue with keepalive
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
        
        # Log incoming request
        logger.info(f"MCP Request: {json.dumps(data, indent=2)}")
        
        # Validate JSON-RPC 2.0 format
        if data.get("jsonrpc") != "2.0":
            error_response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"}
            }
            logger.info(f"MCP Error Response: {json.dumps(error_response, indent=2)}")
            return error_response
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"Handling method: {method} with params: {params}")
        
        if method == "initialize":
            # MCP initialization handshake - Claude web expects exact format
            client_version = params.get("protocolVersion", "")
            expected_version = "2024-11-05"
            
            # Validate protocol version
            if client_version != expected_version:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Unsupported protocol version",
                        "data": {
                            "supported": [expected_version],
                            "requested": client_version
                        }
                    }
                }
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": expected_version,
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "fetch-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            logger.info(f"Initialize Response: {json.dumps(response, indent=2)}")
            return response
        
        elif method == "notifications/initialized":
            # Claude sends this after successful initialization - no response needed
            logger.info("Received notifications/initialized - no response needed")
            return Response(status_code=204)
        
        elif method == "notifications/cancelled":
            # Claude sends timeout notifications that we should acknowledge - no response needed
            logger.info("Received notifications/cancelled - no response needed")
            return Response(status_code=204)
        
        elif method == "resources/list":
            # Return empty resources list - Claude expects this even if we have no resources
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            }
            logger.info(f"Resources List Response: {json.dumps(response, indent=2)}")
            return response
        
        elif method == "tools/list":
            # Return available tools
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "fetch",
                            "description": "Fetch content from a URL and convert to markdown",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The URL to fetch"
                                    },
                                    "max_length": {
                                        "type": "integer",
                                        "default": 5000,
                                        "description": "Maximum number of characters to return"
                                    },
                                    "raw": {
                                        "type": "boolean", 
                                        "default": False,
                                        "description": "Return raw HTML instead of markdown"
                                    }
                                },
                                "required": ["url"]
                            }
                        }
                    ]
                }
            }
            logger.info(f"Tools List Response: {json.dumps(response, indent=2)}")
            return response
        
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
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"}
            }
            logger.info(f"Unknown method '{method}' - Error Response: {json.dumps(error_response, indent=2)}")
            return error_response
    
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }
        logger.error(f"Exception in handle_mcp: {str(e)} - Error Response: {json.dumps(error_response, indent=2)}")
        return error_response

