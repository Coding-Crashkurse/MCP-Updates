import asyncio

from mcp import Client
from mcp.client.subscriptions import ResourceUpdated, ServerEvent, ToolsListChanged

URL = "http://127.0.0.1:8005/mcp"


def describe(event: ServerEvent) -> str:
    if isinstance(event, ToolsListChanged):
        return "tools list changed"
    if isinstance(event, ResourceUpdated):
        return f"resource updated: {event.uri}"
    return type(event).__name__


async def main() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        listener = client.listen(
            tools_list_changed=True,
            resource_subscriptions=["status://build"],
        )
        async with listener as subscription:
            print("Subscription id:", subscription.subscription_id)
            print("Honored filter:", subscription.honored)

            await client.call_tool("touch_status")

            print("Waiting for the server's delayed tool registration...")
            for _ in range(2):
                event = await asyncio.wait_for(anext(aiter(subscription)), timeout=15)
                print("Event:", describe(event))

        tools = await client.list_tools(cache_mode="refresh")
        print("Tools now:", [tool.name for tool in tools.tools])


if __name__ == "__main__":
    asyncio.run(main())
