from mcp.server.mcpserver import MCPServer

server = MCPServer(
    "DiscoverServer",
    version="2.1.0",
    instructions="A catalogue server. Call server/discover before anything else.",
)


@server.tool(description="List catalogue entries")
def list_items() -> list[str]:
    return ["chair", "table", "sofa"]


@server.resource("catalogue://info", description="Static catalogue description")
def catalogue_info() -> str:
    return "Furniture catalogue, 3 entries."


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8002)
