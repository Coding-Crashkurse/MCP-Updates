import asyncio

from mcp import Client

URL = "http://127.0.0.1:8018/mcp"

PRIVACY_IDENTIFIER = "com.example/privacy"


async def main() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        discovered = await client.session.discover()
        extensions = discovered.capabilities.extensions or {}
        print("Advertised extensions:", extensions)

        if PRIVACY_IDENTIFIER not in extensions:
            print("Server does not speak", PRIVACY_IDENTIFIER)
            return

        result = await client.call_tool(
            "login",
            {"username": "markus", "password": "geheim123"},
            meta={PRIVACY_IDENTIFIER: {"redact": ["password"]}},
        )
        print("Result:", result.content[0].text)
        print("Structured:", result.structured_content)

        log = await client.call_tool("read_privacy_log")
        print("Server log:", log.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
