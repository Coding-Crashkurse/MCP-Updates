import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.subscriptions import InMemorySubscriptionBus
from mcp.shared.subscriptions import ToolsListChanged

REGISTER_DELAY_SECONDS = 10

EXTRA_TOOLS: dict[str, str] = {}

# Created up front so both the MCPServer and the background task share it;
# publishing here reaches every active subscriptions/listen stream.
bus = InMemorySubscriptionBus()


async def register_delayed_tools(server: MCPServer) -> None:
    await asyncio.sleep(REGISTER_DELAY_SECONDS)

    @server.tool(name="shout", description="Generated tool shout")
    def shout(text: str) -> str:
        return text.upper()

    EXTRA_TOOLS["shout"] = "shout"
    # Only clients already listening receive this; a client that connects
    # after the delay just sees the tool in tools/list.
    await bus.publish(ToolsListChanged())


@asynccontextmanager
async def delayed_tools_lifespan(server: MCPServer) -> AsyncIterator[None]:
    task = asyncio.create_task(register_delayed_tools(server))
    try:
        yield
    finally:
        task.cancel()


server = MCPServer("SubscriptionsServer", lifespan=delayed_tools_lifespan, subscriptions=bus)


@server.tool(description="List the currently registered extra tools")
def list_extras() -> list[str]:
    return sorted(EXTRA_TOOLS)


@server.resource("status://build", description="Current build status")
def build_status() -> str:
    return "green"


@server.tool(description="Mark the build status as changed")
async def touch_status(ctx: Context) -> str:
    await ctx.notify_resource_updated("status://build")
    return "notified"


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8005)
