import asyncio

from mcp import Client, MCPError

URL = "http://127.0.0.1:8010/mcp"


async def main() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        created = await client.call_tool("create_cart")
        handle = created.structured_content["result"]
        print("Handle:", handle)

        await client.call_tool("add_item", {"cart": handle, "sku": "ABC-1", "quantity": 2})
        await client.call_tool("add_item", {"cart": handle, "sku": "XYZ-9"})

        cart = await client.call_tool("get_cart", {"cart": handle})
        print("Cart:", cart.structured_content)

    async with Client(URL, raise_exceptions=True) as fresh:
        again = await fresh.call_tool("get_cart", {"cart": handle})
        print("Same handle on a new connection:", again.structured_content)

        await fresh.call_tool("drop_cart", {"cart": handle})
        try:
            await fresh.call_tool("get_cart", {"cart": handle})
        except MCPError as error:
            print("After drop:", error.error.code, error.error.message)


if __name__ == "__main__":
    asyncio.run(main())
