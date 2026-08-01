from typing import Annotated

from pydantic import Field

from mcp.server.mcpserver import Context, MCPServer

server = MCPServer("HeaderRoutingServer")

Region = Annotated[
    str,
    Field(description="Region to route to", json_schema_extra={"x-mcp-header": "Region"}),
]

Tenant = Annotated[
    str,
    Field(description="Tenant identifier", json_schema_extra={"x-mcp-header": "Tenant"}),
]


@server.tool(description="Run a query in a region, mirrored into an HTTP header")
def execute_query(region: Region, tenant: Tenant, query: str) -> dict[str, str]:
    return {"region": region, "tenant": tenant, "query": query}


@server.tool(description="Show the MCP headers this request arrived with")
async def show_headers(ctx: Context) -> dict[str, str]:
    headers = ctx.headers or {}
    return {
        key: value
        for key, value in headers.items()
        if key.lower().startswith("mcp-")
    }


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8007)
