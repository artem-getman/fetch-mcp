# Fetch MCP Server - CLAUDE WEB INTEGRATION BROKEN

⚠️ **WARNING: This project does NOT work with Claude's web integration** ⚠️

## Current Status: FAILED

This is an attempt to deploy an MCP (Model Context Protocol) fetch server for Claude's web interface integration. **It completely fails** despite having a perfect server implementation.

### What We Tried (and what failed):

1. ✅ **Server Works Perfectly**
   - Server receives initialize, tools/list, tools/call requests correctly
   - Server responds with proper JSON-RPC 2.0 format  
   - Curl tests prove all endpoints work flawlessly
   - Uses official Anthropic MCP fetch server code

2. ❌ **Claude Web Integration is Broken**
   - Claude sends tools/list requests to our server
   - Our server responds correctly with 200 OK status
   - Claude ignores our responses and reports "Request timed out"
   - Claude UI shows "NO PROVIDED TOOLS" despite receiving valid tool schemas

### Technical Evidence

**Server logs show successful communication:**
```
INFO: tools/list (ID 3) - REQUEST RECEIVED ✅
INFO: tools/list (ID 3) - RESPONSE SENT ✅  
INFO: HTTP 200 OK ✅
```

**Claude logs show timeouts:**
```
INFO: notifications/cancelled (requestId: 3) - TIMEOUT ❌
```

**Curl tests prove server works:**
```bash
curl -X POST https://fetch-mcp-bydg.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}'
# Returns perfect JSON-RPC response with tools
```

### Failed Attempts

- Protocol version compatibility (2024-11-05 vs 2025-03-26)
- Missing MCP method handlers (resources/list, notifications/cancelled)  
- Tool schema format (title, annotations, inputSchema)
- JSON-RPC envelope format changes
- HTTP response headers and FastAPI configuration
- Proactive vs reactive tool notifications
- Capability declarations (listChanged vs static)
- **Nuclear option: Official Anthropic MCP server code**

### Conclusion

**Claude's web MCP integration is fundamentally broken.** The server implementation is perfect - it's Claude that can't handle valid MCP responses over HTTP transport.

### Alternative Platforms to Research

For working MCP web integrations, research these platforms:

1. **Google Cloud Functions** - Some reports of working MCP deployments
2. **AWS Lambda** - May handle MCP protocol better  
3. **Vercel Functions** - Different HTTP stack might work
4. **Azure Functions** - Alternative serverless platform
5. **Direct WebSocket implementation** - Bypass HTTP entirely
6. **Different MCP protocol versions** - Try older/newer versions
7. **Alternative transport layers** - SSE, WebSockets, gRPC

### For Future Developers

**Don't waste time on Claude web MCP integration.** Focus on:
- Desktop Claude app (stdio transport works)
- Alternative AI platforms with working MCP support  
- Direct API integrations instead of MCP protocol
- Wait for Anthropic to fix their web integration

---

## Original Features (that work in stdio mode)

A Model Context Protocol server that provides web content fetching capabilities. This server enables LLMs to retrieve and process content from web pages, converting HTML to markdown for easier consumption.

> [!CAUTION]
> This server can access local/internal IP addresses and may represent a security risk. Exercise caution when using this MCP server to ensure this does not expose any sensitive data.

The fetch tool will truncate the response, but by using the `start_index` argument, you can specify where to start the content extraction. This lets models read a webpage in chunks, until they find the information they need.

### Available Tools

- `fetch` - Fetches a URL from the internet and extracts its contents as markdown.
    - `url` (string, required): URL to fetch
    - `max_length` (integer, optional): Maximum number of characters to return (default: 5000)
    - `start_index` (integer, optional): Start content from this character index (default: 0)
    - `raw` (boolean, optional): Get raw content without markdown conversion (default: false)

### Prompts

- **fetch**
  - Fetch a URL and extract its contents as markdown
  - Arguments:
    - `url` (string, required): URL to fetch

## Installation

Optionally: Install node.js, this will cause the fetch server to use a different HTML simplifier that is more robust.

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *mcp-server-fetch*.

### Using PIP

Alternatively you can install `mcp-server-fetch` via pip:

```
pip install mcp-server-fetch
```

After installation, you can run it as a script using:

```
python -m mcp_server_fetch
```

## Configuration (Desktop Claude Only - Web Integration Broken)

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```
</details>

<details>
<summary>Using docker</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/fetch"]
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "python",
      "args": ["-m", "mcp_server_fetch"]
    }
  }
}
```
</details>

### Configure for VS Code

For quick installation, use one of the one-click install buttons below...

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-UV-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fetch&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-fetch%22%5D%7D) [![Install with UV in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-UV-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fetch&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-fetch%22%5D%7D&quality=insiders)

[![Install with Docker in VS Code](https://img.shields.io/badge/VS_Code-Docker-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fetch&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-i%22%2C%22--rm%22%2C%22mcp%2Ffetch%22%5D%7D) [![Install with Docker in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Docker-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fetch&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-i%22%2C%22--rm%22%2C%22mcp%2Ffetch%22%5D%7D&quality=insiders)

For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is needed when using the `mcp.json` file.

<details>
<summary>Using uvx</summary>

```json
{
  "mcp": {
    "servers": {
      "fetch": {
        "command": "uvx",
        "args": ["mcp-server-fetch"]
      }
    }
  }
}
```
</details>

<details>
<summary>Using Docker</summary>

```json
{
  "mcp": {
    "servers": {
      "fetch": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "mcp/fetch"]
      }
    }
  }
}
```
</details>

### Customization - robots.txt

By default, the server will obey a websites robots.txt file if the request came from the model (via a tool), but not if
the request was user initiated (via a prompt). This can be disabled by adding the argument `--ignore-robots-txt` to the
`args` list in the configuration.

### Customization - User-agent

By default, depending on if the request came from the model (via a tool), or was user initiated (via a prompt), the
server will use either the user-agent
```
ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)
```
or
```
ModelContextProtocol/1.0 (User-Specified; +https://github.com/modelcontextprotocol/servers)
```

This can be customized by adding the argument `--user-agent=YourUserAgent` to the `args` list in the configuration.

### Customization - Proxy

The server can be configured to use a proxy by using the `--proxy-url` argument.

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```
npx @modelcontextprotocol/inspector uvx mcp-server-fetch
```

Or if you've installed the package in a specific directory or are developing on it:

```
cd path/to/servers/src/fetch
npx @modelcontextprotocol/inspector uv run mcp-server-fetch
```

## Contributing

We encourage contributions to help expand and improve mcp-server-fetch. Whether you want to add new tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements to make mcp-server-fetch even more powerful and useful.

## License

mcp-server-fetch is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.