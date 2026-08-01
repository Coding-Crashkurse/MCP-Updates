import asyncio

from mcp import Client
from mcp.client.caching import CacheConfig, InMemoryResponseCacheStore

URL = "http://127.0.0.1:8006/mcp"


async def main() -> None:
    cache = CacheConfig(store=InMemoryResponseCacheStore(), partition="demo")
    async with Client(URL, cache=cache, raise_exceptions=True) as client:
        tools = await client.list_tools()
        print("Tools ttl_ms:", tools.ttl_ms, "scope:", tools.cache_scope)
        print("Tools:", [tool.name for tool in tools.tools])

        await client.list_tools()
        print("Second list served from cache")

        fresh = await client.list_tools(cache_mode="refresh")
        print("Forced refresh:", [tool.name for tool in fresh.tools])

        first = await client.read_resource("counter://reads")
        second = await client.read_resource("counter://reads")
        bypassed = await client.read_resource("counter://reads", cache_mode="bypass")

        print("Read 1 (network):", first.contents[0].text)
        print("Read 2 (cache):", second.contents[0].text)
        print("Read 3 (bypass):", bypassed.contents[0].text)


if __name__ == "__main__":
    asyncio.run(main())
