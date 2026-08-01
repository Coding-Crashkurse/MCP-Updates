import asyncio
from typing import Any, Awaitable, Callable

from mcp import Client, MCPError
from mcp.types import (
    HEADER_MISMATCH,
    INVALID_PARAMS,
    MISSING_REQUIRED_CLIENT_CAPABILITY,
    UNSUPPORTED_PROTOCOL_VERSION,
)

URL = "http://127.0.0.1:8009/mcp"

SPEC_RESERVED = {
    HEADER_MISMATCH: "HeaderMismatch",
    MISSING_REQUIRED_CLIENT_CAPABILITY: "MissingRequiredClientCapability",
    UNSUPPORTED_PROTOCOL_VERSION: "UnsupportedProtocolVersion",
}


def classify(code: int) -> str:
    if code in SPEC_RESERVED:
        return f"spec reserved ({SPEC_RESERVED[code]})"
    if -32099 <= code <= -32020:
        return "spec reserved range"
    if -32019 <= code <= -32000:
        return "implementation defined range"
    return "json-rpc core"


async def attempt(label: str, call: Callable[[], Awaitable[Any]]) -> None:
    try:
        result = await call()
        print(f"{label}: ok ->", getattr(result, "structured_content", result))
    except MCPError as error:
        code = error.error.code
        print(f"{label}: {code} [{classify(code)}] {error.error.message}")


async def main() -> None:
    print("Reserved codes:", SPEC_RESERVED, "invalid params:", INVALID_PARAMS)

    async with Client(URL, raise_exceptions=True) as client:
        await attempt(
            "reserve valid",
            lambda: client.call_tool("reserve", {"item": "chair", "quantity": 1}),
        )
        await attempt(
            "reserve zero",
            lambda: client.call_tool("reserve", {"item": "chair", "quantity": 0}),
        )
        await attempt(
            "reserve sold out",
            lambda: client.call_tool("reserve", {"item": "table", "quantity": 1}),
        )
        await attempt("always fails", lambda: client.call_tool("always_fails"))
        await attempt("missing resource", lambda: client.read_resource("inventory://lamp"))


if __name__ == "__main__":
    asyncio.run(main())
