import asyncio

from mcp import Client

URL = "http://127.0.0.1:8002/mcp"


async def main() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        discovered = await client.session.discover()

        print("Supported versions:", discovered.supported_versions)
        print("Instructions:", discovered.instructions)
        print("Tools capability:", discovered.capabilities.tools)
        print("Resources capability:", discovered.capabilities.resources)
        print("Extensions:", discovered.capabilities.extensions)
        print("Cache hint:", discovered.ttl_ms, discovered.cache_scope)

        if discovered.capabilities.tools is not None:
            tools = await client.list_tools()
            print("Tools:", [tool.name for tool in tools.tools])


if __name__ == "__main__":
    asyncio.run(main())
