from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp.server.extension import Extension, ToolBinding
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

REDACTION_MARKER = "****"


class PrivacyExtension(Extension):
    """Redacts tool-call arguments the client marked as private.

    The client stamps `_meta["com.example/privacy"] = {"redact": ["password"]}`
    onto a `tools/call`. Every argument named there is masked in this
    extension's log, and its value is scrubbed out of the result before the
    response leaves the server. Clients that never send the `_meta` key are
    completely unaffected.
    """

    identifier = "com.example/privacy"

    def __init__(self) -> None:
        self.log: list[dict[str, Any]] = []

    def settings(self) -> dict[str, Any]:
        return {"redactionMarker": REDACTION_MARKER}

    def tools(self) -> list[ToolBinding]:
        return [ToolBinding(fn=self.read_privacy_log)]

    async def intercept_tool_call(
        self,
        params: CallToolRequestParams,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        meta = params.meta or {}
        marked = meta.get(self.identifier) or {}
        private_fields = set(marked.get("redact", ()))
        arguments = params.arguments or {}

        self.log.append(
            {
                "tool": params.name,
                "arguments": {
                    name: REDACTION_MARKER if name in private_fields else value
                    for name, value in arguments.items()
                },
            }
        )

        result = await call_next(ctx)

        secrets = [str(arguments[name]) for name in private_fields if name in arguments]
        if secrets and isinstance(result, CallToolResult):
            for block in result.content:
                if isinstance(block, TextContent):
                    for secret in secrets:
                        block.text = block.text.replace(secret, REDACTION_MARKER)
            if result.structured_content is not None:
                result.structured_content = _scrub(result.structured_content, secrets)
        return result

    def read_privacy_log(self) -> list[dict[str, Any]]:
        return list(self.log)


def _scrub(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, REDACTION_MARKER)
        return value
    if isinstance(value, dict):
        return {key: _scrub(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item, secrets) for item in value]
    return value


privacy = PrivacyExtension()
server = MCPServer("PrivacyServer", extensions=[privacy])


@server.tool(description="Log in and echo what the server received")
def login(username: str, password: str) -> str:
    return f"Hallo {username}, dein Passwort {password} wurde akzeptiert"


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8018)
