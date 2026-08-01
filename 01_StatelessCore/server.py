from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.types import (
    CLIENT_CAPABILITIES_META_KEY,
    CLIENT_INFO_META_KEY,
    PROTOCOL_VERSION_META_KEY,
)

server = MCPServer("StatelessCoreServer", version="1.0.0")


@server.tool(description="Return the per-request metadata the client sent")
async def inspect_request(ctx: Context) -> dict[str, Any]:
    meta = ctx.request_context.meta or {}
    return {
        "protocol_version": meta.get(PROTOCOL_VERSION_META_KEY),
        "client_info": meta.get(CLIENT_INFO_META_KEY),
        "client_capabilities": meta.get(CLIENT_CAPABILITIES_META_KEY),
        "method": ctx.request_context.method,
        "request_id": str(ctx.request_context.request_id),
    }


@server.tool(description="Add two integers")
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8001)
