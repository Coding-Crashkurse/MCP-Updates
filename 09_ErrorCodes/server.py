from mcp import MCPError
from mcp.server.mcpserver import MCPServer
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS

server = MCPServer("ErrorCodesServer")

VENDOR_RATE_LIMITED = -32010

INVENTORY = {"chair": 3, "table": 0}


@server.tool(description="Reserve a number of items from the inventory")
def reserve(item: str, quantity: int) -> dict[str, int]:
    if quantity < 1:
        raise MCPError(code=INVALID_PARAMS, message="quantity must be at least 1")
    if item not in INVENTORY:
        raise MCPError(code=INVALID_PARAMS, message=f"unknown item {item!r}")
    if INVENTORY[item] < quantity:
        raise MCPError(
            code=VENDOR_RATE_LIMITED,
            message=f"only {INVENTORY[item]} left",
            data={"available": INVENTORY[item]},
        )
    INVENTORY[item] -= quantity
    return {"reserved": quantity, "remaining": INVENTORY[item]}


@server.tool(description="Fail with a plain internal error")
def always_fails() -> str:
    raise MCPError(code=INTERNAL_ERROR, message="backend unavailable")


@server.resource("inventory://{item}", description="Stock level for one item")
def stock(item: str) -> str:
    if item not in INVENTORY:
        raise MCPError(code=INVALID_PARAMS, message=f"unknown item {item!r}")
    return str(INVENTORY[item])


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8009)
