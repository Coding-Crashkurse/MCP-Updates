import asyncio
from typing import Any

from mcp import Client
from mcp.client.context import ClientRequestContext
from mcp.types import ElicitRequestParams, ElicitResult

URL = "http://127.0.0.1:8004/mcp"

ANSWERS: dict[str, str] = {
    "destination": "LIS",
    "day": "friday",
    "seat": "economy",
}

rounds = 0


async def elicitation_callback(
    context: ClientRequestContext,
    params: ElicitRequestParams,
) -> ElicitResult:
    global rounds
    rounds += 1
    await asyncio.sleep(2)
    properties: dict[str, Any] = params.requested_schema["properties"]
    field = next(iter(properties))
    print(f"[Round {rounds}] {params.message} -> {ANSWERS[field]}")
    return ElicitResult(action="accept", content={field: ANSWERS[field]})


async def main() -> None:
    client = Client(
        URL,
        elicitation_callback=elicitation_callback,
        input_required_max_rounds=10,
        raise_exceptions=True,
    )
    async with client:
        booking = await client.call_tool("book_flight", {"passenger": "Markus"})
        print("Booking:", booking.structured_content)
        print("Round trips needed:", rounds)


if __name__ == "__main__":
    asyncio.run(main())
