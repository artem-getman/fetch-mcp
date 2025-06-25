from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import asyncio, time

app = FastAPI()

async def event_stream():
    """Minimal SSE stream to satisfy Render health check / Claude handshake."""
    # Immediately send a greeting event, then keepalive pings every 30s.
    yield "event: hello\ndata: fetch-mcp ready\n\n"
    while True:
        await asyncio.sleep(30)
        yield f"event: ping\ndata: {int(time.time())}\n\n"

@app.get("/sse")
async def sse() -> StreamingResponse:
    return StreamingResponse(event_stream(), media_type="text/event-stream")
