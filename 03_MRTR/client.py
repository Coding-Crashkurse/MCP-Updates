import asyncio

from mcp import Client, MCPError
from mcp.client.context import ClientRequestContext
from mcp.types import ElicitRequestParams, ElicitResult, InputRequiredResult

URL = "http://127.0.0.1:8003/mcp"


async def elicitation_callback(
    context: ClientRequestContext,
    params: ElicitRequestParams,
) -> ElicitResult:
    return ElicitResult(action="accept", content={"region": "eu-central"})


async def manual_rounds() -> None:
    client = Client(URL, elicitation_callback=elicitation_callback, raise_exceptions=True)
    async with client:
        # Round 1: the server answers with input_required instead of a result.
        pending = await client.session.call_tool(
            "provision_database", {"name": "orders"}, allow_input_required=True
        )
        assert isinstance(pending, InputRequiredResult)
        key, request = next(iter(pending.input_requests.items()))
        print("server asks:", request.params.message)

        # Round 2: repeat the request, now carrying the answer and the state.
        final = await client.session.call_tool(
            "provision_database",
            {"name": "orders"},
            input_responses={key: ElicitResult(action="accept", content={"region": "eu-central"})},
            request_state=pending.request_state,
        )
        print("final:", final.structured_content)


async def automatic_rounds() -> None:
    client = Client(URL, elicitation_callback=elicitation_callback, raise_exceptions=True)
    async with client:
        result = await client.call_tool("provision_database", {"name": "orders"})
        print("final:", result.structured_content)


async def without_capability() -> None:
    async with Client(URL, raise_exceptions=True) as client:
        try:
            await client.call_tool("provision_database", {"name": "orders"})
        except MCPError as error:
            print("rejected:", error.error.code, error.error.message)


async def main() -> None:
    print("--- manual round trips ---")
    await manual_rounds()
    print("--- automatic round trips ---")
    await automatic_rounds()
    print("--- client without the elicitation capability ---")
    await without_capability()


if __name__ == "__main__":
    asyncio.run(main())
