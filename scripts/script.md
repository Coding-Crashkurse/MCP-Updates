# MCP 2026-07-28: What Actually Changed

Video script. Read straight through, or jump to the section you are recording.
Every code path referenced here lives in the matching folder of this repo and runs
against the official Python SDK, `mcp==2.0.0`.

---

## Intro

On July 28th the Model Context Protocol got a new specification revision, and it is a
big one. The initialize handshake, protocol level sessions and the server to client back
channel are gone.

We look only at what is new — deprecated features like Roots and Sampling are not
covered. Twelve features, one folder each, a server and a client you can run.

---

## 1. The stateless core

Every connection used to start with a handshake — `initialize`, capabilities,
`notifications/initialized` — plus a session id on every HTTP request. That means sticky
routing, no serverless, and a restart that kills every client.

So the lifecycle is gone. Every request now carries protocol version, client identity
and capabilities in `_meta`, and the server stamps `serverInfo` into every result.
Connecting itself sends nothing — the first thing on the wire is an ordinary request.

```json
{
  "_meta": {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": { "name": "MyClient", "version": "1.0.0" },
    "io.modelcontextprotocol/clientCapabilities": {}
  }
}
```

*Demo: connecting sends nothing, and every result carries the `serverInfo` stamp.*

---

## 2. server/discover

Without a handshake, how does a client learn what a server can do? `server/discover` —
a new RPC method that every server must implement. It returns the supported protocol
versions, the capabilities and the server identity. Clients may call it but do not have
to, on stdio it doubles as a compatibility probe, and the result is cacheable.

*Demo: list tools only if a tools capability was advertised.*

---

## 3. Multi Round Trip Requests

This is the big one. A server that needed something mid request used to send its own
request down the open stream — blocked worker, open connection, state in memory.

Now it returns a result instead: `resultType` is `"input_required"`, and `inputRequests`
says what it needs. The client answers and retries the call with `inputResponses` and a
new id; the server runs the tool from the top and finishes.

```json
{
  "resultType": "input_required",
  "inputRequests": {
    "placement": { "method": "elicitation/create", "params": { "..." : "..." } }
  },
  "requestState": "opaque blob"
}
```

Two limits: the client must have declared the capability, otherwise `-32021`. And only
`tools/call`, `resources/read` and `prompts/get` may do this.

*Demo: the rounds by hand, then the same thing inside one `call_tool`.*

---

## 4. requestState

If the server keeps nothing in memory, how does it remember round one? It hands its
memory to the client. `requestState` is a sealed package: the client carries it along
and hands it back unchanged, without ever looking inside.

That means the server's own data travels through hands it cannot trust. So the server
signs or encrypts the package, ties it to the user it belongs to, to the original
request, and to a short lifetime — and rejects anything that comes back altered or too
late. In the official Python library that is one line: `RequestStateSecurity`.

*Demo: a three round booking, nothing held between rounds.*

---

## 5. subscriptions/listen

How does a client hear that the tool list changed, or that a resource was updated? The
old way was an SSE stream on HTTP GET plus `resources/subscribe`. All of it is gone.

One method replaces it: `subscriptions/listen`, a normal POST whose response stream
stays open. GET now answers `405`. You declare what you want, the server confirms what
it granted. Careful: progress and log messages still travel on their own request.

*Demo: subscribe to tool changes and one resource, trigger both.*

---

## 6. Cacheable results

Five methods must now return `ttlMs`, a freshness hint, and `cacheScope`, public or
private — the three list methods plus `resources/read` and `resources/templates/list`.

`ttlMs` cuts polling. `cacheScope` decides whether shared proxies may cache, so marking
user specific data public is a data leak, not a performance bug. This complements
`listChanged`, it does not replace it. And ship tools in deterministic order, or caches
never hit.

*Demo: a server side counter showing which reads actually arrived.*

---

## 7. Header based routing

In companies, clients and servers rarely talk to each other directly — in between sits
a gateway: load balancer, rate limiter, API gateway. Those boxes decide on headers,
but to them every MCP request looks the same: a POST to one endpoint, method and tool
name buried in the JSON body. Expose those two, and the gateway gets useful — a heavy
tool goes to a bigger pool, one hot tool gets throttled instead of the whole server,
`tools/list` gets cached at the edge.

So the body is mirrored into mandatory headers: `Mcp-Method` on every request,
`Mcp-Name` on `tools/call`, `resources/read` and `prompts/get`. Parameters can be
annotated with `x-mcp-header` and land in `Mcp-Param-{Name}`, which gives you region
or tenant routing.

```json
{
  "region": { "type": "string", "x-mcp-header": "Region" }
}
```

And the server must reject any header/body mismatch with `-32020`, or you have a
confused deputy.

---

## 8. Extensions

The core protocol will never contain everything. Both capability objects now have an
`extensions` field, and an extension is a named add on with a reverse DNS identifier
like `com.example/audit`. It can register new RPC methods, contribute tools, and
intercept tool calls. Negotiation is per request — but the framework does not filter
callers, so check what the client declared. This is how tasks left the core.

*Demo: an audit extension that counts calls and exposes its log.*

---

## 9. Error code allocation

Before you pick a number: `-32000` to `-32019` stays implementation defined, `-32020` to
`-32099` belongs to the spec. Three exist so far — `-32020` `HeaderMismatch`, `-32021`
`MissingRequiredClientCapability`, `-32022` `UnsupportedProtocolVersion`. Resource not
found also moved from `-32002` to `-32602`, Invalid Params. Keep your own codes in the
`-3200x` range.

---

## 10. Server issued handles

Some servers do need state across calls — a cart, a wizard, a long conversation. With
sessions gone the state becomes explicit: the server issues a handle, returns it as an
ordinary tool result, and the client passes it back as an ordinary argument.

No protocol machinery, just a string — which survives dropped connections and works
across instances.

*Demo: the same cart picked back up from a second connection.*

---

## 11. Protocol eras

Two eras now: the handshake era, `2025-11-25` and earlier, and the sessionless era,
`2026-07-28`. A client can run `auto`, trying modern first and inspecting the body on a
`400`, because modern servers also return `400` for version and header errors — only an
unrecognised error falls back to `initialize`. One server serves both, so you migrate at
your own pace.

*Demo: all three modes against one server, printing what got negotiated.*

---

## 12. Observability

Logging is deprecated, `logging/setLevel` is gone, and the level is set per request via
`io.modelcontextprotocol/logLevel`. The rule that trips people up: no field, no log
notifications.

The replacement is OpenTelemetry, and the spec now documents W3C trace context in
`_meta` — `traceparent`, `tracestate`, `baggage`. That gives you one trace across the
HTTP request, the tool call and the database query it causes.

*Demo: the SDK parses trace context straight out of `_meta` — sampled flag included,
malformed traceparents rejected.*

---

## Outro

Twelve things, and nearly all of them follow from one decision: make every request stand
on its own. Sessions went so servers could scale. The back channel needed a session.
MRTR replaced the back channel, `requestState` holds what MRTR drops, and handles hold
what sessions used to.

The deprecated set — Roots, Sampling, Logging, Dynamic Client Registration — has at
least twelve months, so no panic there. Every folder in this repo is a runnable pair.
