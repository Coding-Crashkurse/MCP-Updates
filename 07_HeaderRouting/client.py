import asyncio
import json

from mcp import Client

URL = "http://127.0.0.1:8007/mcp"


async def main() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        tools = await client.list_tools()
        schema = next(t for t in tools.tools if t.name == "execute_query").input_schema
        print("Annotated schema:", json.dumps(schema["properties"], indent=2))

        result = await client.call_tool(
            "execute_query",
            {"region": "eu-west1", "tenant": "acme", "query": "SELECT 1"},
        )
        print("Query result:", result.structured_content)

        headers = await client.call_tool("show_headers")
        print("Headers seen by the server:", headers.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
