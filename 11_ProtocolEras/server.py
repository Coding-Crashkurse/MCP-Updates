from mcp.server.mcpserver import Context, MCPServer
from mcp.types import PROTOCOL_VERSION_META_KEY

server = MCPServer("ProtocolErasServer", version="1.0.0")

MODERN = "2026-07-28"


@server.tool(description="Report which protocol era this request arrived on")
async def which_era(ctx: Context) -> dict[str, str]:
    meta = ctx.request_context.meta or {}
    version = str(meta.get(PROTOCOL_VERSION_META_KEY) or ctx.request_context.protocol_version)
    return {
        "protocol_version": version,
        "era": "sessionless" if version >= MODERN else "handshake",
        "back_channel": "no" if version >= MODERN else "yes",
    }


@server.tool(description="Add two integers")
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8011)
