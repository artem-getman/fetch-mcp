from fastapi import FastAPI, Response
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
async def oauth_discovery():
    return {
        "issuer": "https://fetch-mcp",
        "authorization_endpoint": "https://fetch-mcp/authorize",
        "token_endpoint": "https://fetch-mcp/token",
        "registration_endpoint": "/register",
    }

@app.post("/register")
async def oauth_register():
    # Return a dummy public client so the UI finishes handshake
    return {
        "client_id": "fetch-mcp-public-client",
        "client_id_issued_at": 0,
        "token_endpoint_auth_method": "none",
    }

# Quiet 404s for / and favicons
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

