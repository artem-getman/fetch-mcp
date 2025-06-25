from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import asyncio, time

app = FastAPI()

# Allow browser-based clients (Claude settings panel) to access SSE
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
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

