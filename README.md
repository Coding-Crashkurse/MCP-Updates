# MCP `2026-07-28` — nur die neuen Features

Zwölf eigenständige Server/Client-Paare gegen das offizielle Python-SDK `mcp==2.0.0`.
Jedes Kapitel zeigt genau eine Neuerung der Spec-Revision `2026-07-28`. Nichts hier
existierte in `2025-11-25` in dieser Form.

```bash
uv sync
cd 01_StatelessCore
uv run python server.py      # Terminal 1
uv run python client.py      # Terminal 2
```

Jedes Kapitel hat seinen eigenen Port (`8001` … `8012`), damit mehrere Server
parallel laufen können.

---

## 01_StatelessCore — Der Handshake ist weg

Bis `2025-11-25` begann jede Verbindung mit `initialize` + `notifications/initialized`,
und der Server hielt danach Sitzungszustand über den `Mcp-Session-Id`-Header. Beides ist
ersatzlos gestrichen. Stattdessen ist **jeder einzelne Request selbstbeschreibend**: er
trägt Protokollversion, Client-Identität und Client-Capabilities in `_meta`
(`io.modelcontextprotocol/protocolVersion`, `clientInfo`, `clientCapabilities`), und der
Server stempelt seine Identität in `_meta` jedes Results. Das ist die Grundlage für alles
andere — erst dadurch kann ein MCP-Server auf Serverless/Edge laufen und hinter einem
Load Balancer ohne Sticky Sessions skalieren. Das Kapitel gibt die empfangenen
`_meta`-Felder einfach zurück, damit man sieht, was wirklich über die Leitung geht.

## 02_ServerDiscover — Der neue Einstiegspunkt

Wenn es kein `initialize` mehr gibt, braucht es trotzdem einen Weg, um vor dem ersten
echten Aufruf zu erfahren, was ein Server kann. Dafür ist `server/discover` da: eine
neue RPC-Methode, die **jeder Server implementieren MUSS**, und die unterstützte
Protokollversionen, Capabilities und Server-Identität liefert. Clients dürfen sie
aufrufen, müssen aber nicht — auf stdio dient sie zusätzlich als Backward-Compat-Probe,
um eine alte von einer neuen Gegenstelle zu unterscheiden. Der Rückgabewert ist selbst
cachebar (`ttlMs`/`cacheScope`), man kann ihn also einmal holen und wiederverwenden.

## 03_MRTR — Multi Round-Trip Requests

Das ist die tiefgreifendste Änderung. Server können keine eigenen Requests mehr an den
Client schicken — der Rückkanal, über den bisher `elicitation/create`,
`sampling/createMessage` und `roots/list` liefen, existiert nicht mehr. Stattdessen
antwortet der Server mit einem `InputRequiredResult` (`resultType: "input_required"`),
das im Feld `inputRequests` beschreibt, was er braucht; der Client sammelt die Antworten
und **wiederholt den ursprünglichen Request** mit `inputResponses` und einer neuen
JSON-RPC-ID. Der Grund ist derselbe wie beim stateless Core: ein Tool, das mitten im Lauf
auf eine Antwort wartet, blockiert einen Worker und braucht eine offene Verbindung — mit
MRTR ist jede Runde ein unabhängiger Request, der auf einer beliebigen Instanz landen
darf. Das Kapitel zeigt beide Seiten: einmal die Runden von Hand (man sieht das rohe
`InputRequiredResult`), einmal von der `Client`-Schleife automatisch gefahren, und
zusätzlich den neuen Fehler `-32021`, wenn der Client die nötige Capability gar nicht
angemeldet hat.

## 04_RequestState — Zustand, der durch den Client wandert

Weil zwischen zwei MRTR-Runden nichts serverseitig gespeichert werden soll, gibt der
Server seinen Zwischenstand als opaken String `requestState` an den Client, der ihn beim
Retry unverändert zurückschickt. Clients dürfen ihn **nicht** interpretieren oder
verändern. Sicherheitsseitig ist das der interessante Teil: `requestState` ist
per Definition angreifer-kontrollierter Input, deshalb schreibt die Spec vor, ihn zu
integritätsschützen (HMAC/AEAD) und gegen Replay mit Principal, kurzer TTL und einem
Request-Identifier zu binden. Im SDK erledigt das `RequestStateSecurity` mit
AES-256-GCM und Key-Rotation. Das Kapitel fährt eine dreirundige Buchung, bei der der
Server zwischen den Runden nichts im Speicher behält.

## 05_Subscriptions — `subscriptions/listen`

Der frühere Weg für serverseitige Änderungsmeldungen war ein eigenständiger SSE-Stream
per HTTP GET, dazu `resources/subscribe` und `resources/unsubscribe`. Alles drei ist weg
und durch **eine** Methode ersetzt: `subscriptions/listen` ist ein langlebiger POST,
dessen Response-Stream offen bleibt. Der Client meldet explizit an, was er hören will
(`toolsListChanged`, `promptsListChanged`, `resourcesListChanged`,
`resourceSubscriptions`), der Server bestätigt den tatsächlich gewährten Filter und
taggt Notifications mit `io.modelcontextprotocol/subscriptionId`. Wichtig für die
Praxis: Request-bezogene Notifications wie `notifications/progress` laufen **nicht**
hierüber, sondern weiterhin auf dem Response-Stream ihres eigenen Requests.

## 06_Caching — `ttlMs` und `cacheScope`

Neu ist, dass `tools/list`, `prompts/list`, `resources/list`, `resources/read` und
`resources/templates/list` **verpflichtend** zwei Cache-Felder liefern: `ttlMs` als
Freshness-Hinweis in Millisekunden und `cacheScope` mit `"public"` oder `"private"`.
`public` erlaubt geteilten Intermediaries das Cachen, `private` nicht — bei
nutzerspezifischen Daten ist die falsche Wahl ein echtes Datenleck. Das ergänzt die
bestehenden `listChanged`-Notifications, ersetzt sie aber nicht: TTL senkt das Polling,
Notifications liefern die Sofort-Invalidierung. Passend dazu SOLLEN Server `tools/list`
in **deterministischer Reihenfolge** ausliefern, damit clientseitige Caches und
LLM-Prompt-Caches überhaupt treffen können.

## 07_HeaderRouting — Gateways müssen den Body nicht mehr lesen

Auf jedem Streamable-HTTP-POST sind jetzt `Mcp-Method` und (bei `tools/call`,
`resources/read`, `prompts/get`) `Mcp-Name` **Pflicht**, zusätzlich zum bekannten
`MCP-Protocol-Version`. Damit können Load Balancer, API-Gateways und
Observability-Tools routen, autorisieren und rate-limiten, ohne JSON zu parsen.
Ergänzend kann ein Server einzelne Tool-Parameter mit `x-mcp-header` annotieren; der
Client spiegelt deren Werte dann als `Mcp-Param-{Name}` in die Header — praktisch für
Region- oder Tenant-Routing. Sicherheitsanker: der Server **MUSS** Header gegen Body
validieren und bei Abweichung mit `400` und `-32020 HeaderMismatch` ablehnen, damit
Gateway und Server nie auf unterschiedliche Wahrheiten schauen.

## 08_Extensions — Protokollerweiterungen ohne Fork

`ClientCapabilities` und `ServerCapabilities` haben ein neues `extensions`-Feld, über das
Funktionalität jenseits des Kerns ausgehandelt werden kann. Eine Extension trägt einen
Reverse-DNS-Identifier (`com.example/audit`), kann eigene RPC-Methoden registrieren,
zusätzliche Tools und Resources beisteuern und Tool-Calls abfangen. Die Aushandlung ist
beidseitig und pro Request: der Server bewirbt seine Capability, der Client meldet in
`_meta`, was er versteht — die Extension muss selbst prüfen, bevor sie ihr Verhalten
ändert. Das ist der Mechanismus, mit dem Tasks aus dem Kern herausgelöst wurden
(`io.modelcontextprotocol/tasks`), und über den Vendor-Features künftig laufen, ohne die
Spec aufzublähen.

## 09_ErrorCodes — Nummernkreise mit Regeln

Bisher war der JSON-RPC-Server-Error-Bereich Wildwuchs. Jetzt gilt eine klare
Aufteilung: `-32000` bis `-32019` bleibt implementierungsdefiniert (bestehende
SDK-Nutzung ist bestandsgeschützt), `-32020` bis `-32099` ist für die Spec reserviert.
Konkret neu vergeben: `-32020 HeaderMismatch`, `-32021 MissingRequiredClientCapability`,
`-32022 UnsupportedProtocolVersion`. Außerdem wandert „Resource nicht gefunden" von
`-32002` auf `-32602` (Invalid Params), um sich an JSON-RPC zu halten. Für dich heißt
das: eigene Fehlercodes gehören ab jetzt in den `-3200x`-Bereich, nicht darüber.

## 10_ServerHandles — Zustand ohne Sessions

Weil es keine Protokoll-Sessions mehr gibt, brauchen Server, die über mehrere Aufrufe
hinweg Zustand halten wollen, ein neues Muster: sie prägen selbst ein Handle und geben
es als ganz normales Tool-Ergebnis zurück; der Client bzw. das Modell reicht es bei
Folgeaufrufen als gewöhnliches Argument weiter. Das ist explizit die von SEP-2567
empfohlene Migration für alles, was früher an der Session hing. Der Vorteil ist, dass der
Zustand sichtbar und adressierbar wird statt implizit an einer Verbindung zu kleben — er
überlebt Verbindungsabbrüche und funktioniert über Instanzgrenzen hinweg. Das Kapitel
demonstriert genau das: derselbe Warenkorb wird über zwei komplett getrennte
Verbindungen weiterbenutzt.

## 11_ProtocolEras — Alt und neu nebeneinander

Es gibt jetzt zwei klar getrennte Protokoll-Ären: die Handshake-Ära (`≤ 2025-11-25`) mit
`initialize`, Sessions und Rückkanal, und die sessionlose Ära (`2026-07-28`). Ein Client
kann `mode="auto"` fahren (moderne Anfrage zuerst, bei einem `400` den Body prüfen und
nur bei unbekanntem Fehler auf `initialize` zurückfallen), eine Version festnageln oder
bewusst `legacy` erzwingen. Das ist der praktische Migrationspfad: derselbe Server
bedient beide Welten, und man kann pro Client entscheiden, wann umgestellt wird. Das
Kapitel fährt alle drei Modi gegen denselben Server und zeigt, was jeweils ausgehandelt
wird — inklusive der Frage, ob ein Rückkanal existiert.

## 12_Observability — OpenTelemetry statt Logging

Das Logging-Feature ist mit `2026-07-28` deprecated, `logging/setLevel` wurde entfernt,
und der Log-Level wird nur noch pro Request über `io.modelcontextprotocol/logLevel`
gesetzt. Als Ersatz dokumentiert die Spec jetzt offiziell die W3C-Trace-Context-
Propagation über `_meta`: `traceparent`, `tracestate` und `baggage`. Damit hängt ein
MCP-Call an derselben Trace wie der HTTP-Request, der ihn ausgelöst hat, und wie die
Datenbank-Query, die er nach sich zieht — das konnte MCP-Logging nie leisten. Das
Kapitel schickt Trace-Context mit und ohne, und zeigt, wie das SDK den `traceparent`
aus `_meta` parst und validiert — inklusive Sampled-Flag; ein kaputter `traceparent`
wird verworfen.

---

## Bewusst nicht enthalten

- **Roots, Sampling, Logging** — mit `2026-07-28` deprecated (Entfernung frühestens
  2027-07-28). Kein neues Feature, sondern Altlast.
- **Elicitation als solches** — gibt es seit `2025-06-18`. Neu ist nur der Transportweg,
  und der steckt in `03_MRTR`.
- **Structured Outputs** — seit `2025-06-18`. Neu sind lediglich die gelockerten
  Schema-Regeln (SEP-2106).
- **Tasks-Extension** — im offiziellen SDK bisher nur als Typen vorhanden, ohne
  Implementierung. Nutzbar aktuell nur über `fastmcp-tasks`.
#   M C P - U p d a t e s  
 