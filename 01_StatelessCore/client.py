import asyncio

from mcp import Client
from mcp.types import Implementation

URL = "http://127.0.0.1:8001/mcp"


async def main() -> None:
    client = Client(
        URL,
        client_info=Implementation(name="StatelessCoreClient", version="1.0.0"),
        mode="2026-07-28",
        raise_exceptions=True,
    )
    async with client:
        print("Connected without a handshake - nothing sent yet")

        first = await client.call_tool("inspect_request")
        print("Request 1 metadata:", first.structured_content)
        print("Request 1 server stamp:", first.meta)

        second = await client.call_tool("add", {"a": 21, "b": 21})
        print("Request 2 result:", second.structured_content)
        print("Request 2 server stamp:", second.meta)


if __name__ == "__main__":
    asyncio.run(main())
