from mcp.server.caching import CacheHint
from mcp.server.mcpserver import MCPServer

server = MCPServer(
    "CachingServer",
    cache_hints={
        "tools/list": CacheHint(ttl_ms=300_000, scope="public"),
        "prompts/list": CacheHint(ttl_ms=300_000, scope="public"),
        "resources/list": CacheHint(ttl_ms=60_000, scope="public"),
        "resources/read": CacheHint(ttl_ms=5_000, scope="private"),
        "resources/templates/list": CacheHint(ttl_ms=300_000, scope="public"),
    },
)

READS = {"count": 0}


@server.tool(description="Add two integers")
def add(a: int, b: int) -> int:
    return a + b


@server.tool(description="Subtract two integers")
def subtract(a: int, b: int) -> int:
    return a - b


@server.resource("counter://reads", description="How often this resource was read")
def read_counter() -> str:
    READS["count"] += 1
    return str(READS["count"])


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8006)
