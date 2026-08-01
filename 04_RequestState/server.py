from typing import Annotated

from pydantic import BaseModel, Field

from mcp.server.mcpserver import Elicit, MCPServer, Resolve
from mcp.server.request_state import RequestStateSecurity

SEALING_KEY = "0123456789abcdef0123456789abcdef"

server = MCPServer(
    "RequestStateServer",
    request_state_security=RequestStateSecurity(keys=[SEALING_KEY], ttl=1.0),
)


class Destination(BaseModel):
    destination: str = Field(description="Airport code, for example LIS")


class TravelDay(BaseModel):
    day: str = Field(description="Departure day, for example friday")


class Seat(BaseModel):
    seat: str = Field(description="Seat class: economy or business")


def ask_destination() -> None:
    return Elicit("Where would you like to fly?", Destination)


def ask_day() -> None:
    return Elicit("Which day do you want to depart?", TravelDay)


def ask_seat() -> None:
    return Elicit("Which seat class?", Seat)


@server.tool(description="Book a flight across several sealed round trips")
async def book_flight(
    passenger: str,
    destination: Annotated[Destination, Resolve(ask_destination)],
    day: Annotated[TravelDay, Resolve(ask_day)],
    seat: Annotated[Seat, Resolve(ask_seat)],
) -> dict[str, str]:
    return {
        "passenger": passenger,
        "destination": destination.destination,
        "day": day.day,
        "seat": seat.seat,
    }


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8004)
