import asyncio

from mcp import Client
from mcp.client.client import ConnectMode

URL = "http://127.0.0.1:8011/mcp"

MODES: list[ConnectMode] = ["auto", "2026-07-28", "legacy"]


async def probe(mode: ConnectMode) -> None:
    async with Client(URL, mode=mode, raise_exceptions=True) as client:
        era = await client.call_tool("which_era")
        print(f"mode={mode:<12} negotiated={client.protocol_version:<12} {era.structured_content}")


async def main() -> None:
    for mode in MODES:
        await probe(mode)


if __name__ == "__main__":
    asyncio.run(main())
