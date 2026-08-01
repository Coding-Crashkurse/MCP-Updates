from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server.mcpserver import Elicit, MCPServer, Resolve

server = MCPServer("MRTRServer")


class Placement(BaseModel):
    region: Literal["eu-central", "us-east", "ap-south"] = Field(
        description="Where the database should be provisioned"
    )


def ask_placement() -> Elicit:
    return Elicit("In which region should the database run?", Placement)


@server.tool(description="Provision a managed database instance")
def provision_database(
    name: str,
    placement: Annotated[Placement, Resolve(ask_placement)],
) -> dict[str, str]:
    return {"name": name, "region": placement.region}


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8003)
