import secrets
from typing import Annotated

from pydantic import BaseModel, Field

from mcp import MCPError
from mcp.server.mcpserver import MCPServer
from mcp.types import INVALID_PARAMS

server = MCPServer("ServerHandlesServer")

CartHandle = Annotated[
    str,
    Field(description="Opaque cart handle returned by create_cart", min_length=8),
]


class CartItem(BaseModel):
    sku: str
    quantity: int = Field(ge=1)


class Cart(BaseModel):
    handle: str
    items: list[CartItem]
    total_quantity: int


CARTS: dict[str, list[CartItem]] = {}


def load(handle: str) -> list[CartItem]:
    if handle not in CARTS:
        raise MCPError(code=INVALID_PARAMS, message="unknown or expired cart handle")
    return CARTS[handle]


@server.tool(description="Create a cart and return its handle")
def create_cart() -> str:
    handle = secrets.token_urlsafe(12)
    CARTS[handle] = []
    return handle


@server.tool(description="Add an item to a cart identified by its handle")
def add_item(cart: CartHandle, sku: str, quantity: int = 1) -> Cart:
    items = load(cart)
    items.append(CartItem(sku=sku, quantity=quantity))
    return Cart(
        handle=cart,
        items=items,
        total_quantity=sum(item.quantity for item in items),
    )


@server.tool(description="Read a cart identified by its handle")
def get_cart(cart: CartHandle) -> Cart:
    items = load(cart)
    return Cart(
        handle=cart,
        items=items,
        total_quantity=sum(item.quantity for item in items),
    )


@server.tool(description="Discard a cart")
def drop_cart(cart: CartHandle) -> str:
    load(cart)
    del CARTS[cart]
    return "dropped"


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8010)
