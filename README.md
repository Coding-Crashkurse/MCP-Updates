# MCP `2026-07-28` — nur die neuen Features

Zwölf eigenständige Server/Client-Paare gegen das offizielle Python-SDK `mcp==2.0.0`.
Jedes Kapitel zeigt genau eine Neuerung der Spec-Revision `2026-07-28`.

```bash
uv sync
cd 01_StatelessCore
uv run python server.py      # Terminal 1
uv run python client.py      # Terminal 2
```

Jedes Kapitel hat seinen eigenen Port (`8001` … `8012`), damit mehrere Server
parallel laufen können.

## Kapitel

| Kapitel | Neuerung |
|---|---|
| `01_StatelessCore` | `initialize`-Handshake und Sessions sind weg — jeder Request ist über `_meta` selbstbeschreibend |
| `02_ServerDiscover` | `server/discover`: neue Pflicht-Methode für Capabilities, Versionen und Server-Identität |
| `03_MRTR` | Kein Rückkanal mehr — Server antworten mit `input_required`, der Client wiederholt den Request |
| `04_RequestState` | Opaker, integritätsgeschützter Zwischenstand wandert durch den Client statt im Server zu liegen |
| `05_Subscriptions` | `subscriptions/listen` ersetzt GET-SSE-Stream und `resources/subscribe`/`unsubscribe` |
| `06_Caching` | Pflichtfelder `ttlMs` und `cacheScope` auf allen List-/Read-Ergebnissen |
| `07_HeaderRouting` | Pflicht-Header `Mcp-Method`/`Mcp-Name`; Mismatch → `400` + `-32020` |
| `08_Extensions` | `extensions`-Capability: Protokollerweiterungen per Reverse-DNS-Identifier ohne Fork |
| `09_ErrorCodes` | Spec-reservierter Bereich `-32020…-32099` mit neuen Codes `-32020/-32021/-32022` |
| `10_ServerHandles` | Zustand über explizite Handles als Tool-Argumente statt über Sessions |
| `11_ProtocolEras` | Handshake-Ära vs. sessionlose Ära — `auto`, gepinnt oder `legacy` gegen denselben Server |
| `12_Observability` | Logging deprecated — W3C Trace Context (`traceparent` & Co.) über `_meta` |

Ausführliche Erklärungen zu jedem Kapitel stehen in [scripts/script.md](scripts/script.md).

## Bewusst nicht enthalten

- **Roots, Sampling, Logging** — mit `2026-07-28` deprecated, kein neues Feature.
- **Elicitation als solches** — seit `2025-06-18`; neu ist nur der Transportweg (`03_MRTR`).
- **Structured Outputs** — seit `2025-06-18`; neu sind nur die gelockerten Schema-Regeln.
- **Tasks-Extension** — im offiziellen SDK bisher nur als Typen, ohne Implementierung.
