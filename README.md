# Daily Signal

Für die Entwicklung gelten die [Produktspezifikationen und die Quellenmatrix](docs/specs/README.md). Der [Arbeitsablauf](AGENTS.md) beschreibt die Pflege von Anforderungen, Status und Prüfnachweisen.

Daily Signal ist eine **read-only Public API** für veröffentlichte Tagesberichte.
Pro `Europe/Berlin`-Kalendertag liefert sie die aktuell veröffentlichte
Berichtsrevision mit 5–8 Nachrichten-Stories, einem Tages-Score von 1 bis 5 und
den zugehörigen Attributions-Snapshots. Die API gibt ausschließlich eigene
Daily-Signal-Zusammenfassungen zurück, keine Fremd-Volltexte.

## Zweck

- Öffentliche, rein lesende HTTP-Schnittstelle für Tagesberichte.
- Ein Berichtstag enthält eine geordnete Liste von Stories (`rank` 1–8) mit
  Richtung, Impact, Kategorie, Region und Quellen-Attribution.
- Der Tages-Score verdichtet die Story-Richtungen zu einem Wert von 1 bis 5
  inklusive Rohwert, Label, Confidence und Erklärung
  (siehe [docs/scoring-methodology.md](docs/scoring-methodology.md)).
- Sichtbar ist ausschließlich `status='published' AND is_current=true`.
  Unveröffentlichte Tage fehlen im Kalender und erhalten nie einen Ersatz-Score.
- Revisionen sind unveränderlich: eine Korrektur erzeugt eine neue Revision, die
  zur aktuellen Revision wird; die vorherige wird nicht mehr ausgeliefert.

## Status

Dieses Repository enthält das **Fundament** des Systems, kein vollständiges
Redaktions- und Publikationssystem. Umgesetzt sind:

- Datenbankschema (14 Tabellen) als Alembic-Migration `0001`,
- read-only API mit ETags, Rate-Limit, standardisiertem Fehler-Envelope und
  Health-Checks,
- Quellen- und Methodik-Konfiguration sowie der rights-locked Seed,
- Worker- und Scheduler-Prozesse (Heartbeat bzw. 03:30-Tick mit DB-Lock),
- Docker-Compose-Laufzeit und CI (Lint, Typprüfung, Tests, Container-Build).

**Nicht implementiert** sind Ingestion/Feed-Adapter, Event-Clustering,
LLM-Provider-Aufrufe, Berichtsgenerierung, Validierungs- und
Publikationsworkflow sowie Korrektur- und Lösch-/Purge-Prozesse. Der Scheduler
meldet eine fällige Analyse nur und schreibt bewusst keinen Bericht. Details in
[docs/architecture.md](docs/architecture.md) und im Spezifikationspaket
[docs/specs/daily-signal-v1.0/README.md](docs/specs/daily-signal-v1.0/README.md).

## Quickstart

Voraussetzungen: Python 3.13, [uv](https://docs.astral.sh/uv/) und Docker.

Lokale Installation:

```powershell
uv sync --locked
```

Docker Compose startet PostgreSQL, führt die Migration und den Quellen-Seed als
eigenen `migrate`-Schritt aus und startet danach API, Worker und Scheduler. Die
Basis-`compose.yaml` verlangt `POSTGRES_USER`, `POSTGRES_PASSWORD` und
`POSTGRES_DB`; deshalb **muss** `--env-file .env.example` mitgegeben werden. Die Zugangsdaten in `.env.example`
sind nur für die lokale Entwicklung gedacht und müssen außerhalb der lokalen
Entwicklung ersetzt werden:

```powershell
docker compose --env-file .env.example up -d --build
docker compose --env-file .env.example ps
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod "http://localhost:8000/v1/days?from=2026-11-01&to=2026-11-30"
```

Ein leerer Kalender liefert exakt
`{"from":"2026-11-01","to":"2026-11-30","days":[]}`. `/v1/days/latest` liefert
ohne veröffentlichten Bericht `404` im standardisierten Fehlerformat.

Für die lokale Entwicklung mit veröffentlichtem DB-Port, gemountetem Quellcode
und der Testdatenbank wird die Dev-Override-Datei dazugelegt:

```powershell
docker compose --env-file .env.example -f compose.yaml -f compose.dev.yaml up -d --build
```

Herunterfahren inklusive Volume:

```powershell
docker compose --env-file .env.example down -v
```

## Endpunkte

Alle Fachrouten sind `GET`, rein lesend und unter `/v1` versioniert. Die beiden
Health-Routen gehören nicht zur versionierten Fach-API.

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/v1/days?from=YYYY-MM-DD&to=YYYY-MM-DD` | Veröffentlichte Kalendertage im inklusiven Bereich, aufsteigend; maximal **366 Tage inklusive**, `from <= to`. |
| `GET` | `/v1/days/latest` | Letzter veröffentlichter Bericht (nicht zwingend „gestern“). |
| `GET` | `/v1/days/{date}` | Aktuelle veröffentlichte Revision für ein Berlin-Datum. |
| `GET` | `/v1/days/{date}/stories` | Stories des Tages; Filter `direction`, `category`, `region` werden mit AND kombiniert. |
| `GET` | `/v1/stories/{id}` | Story-Snapshot aus einem aktuellen Bericht. |
| `GET` | `/v1/sources` | Aktuell freigegebene öffentliche Quellen. |
| `GET` | `/v1/methodology` | Aktuelle öffentliche Scoring-Methodik. |
| `GET` | `/health/live` | Liveness; berührt die Datenbank nicht. |
| `GET` | `/health/ready` | Readiness inklusive Datenbank-Konnektivität. |

Antwortverhalten:

- `ETag` + `If-None-Match` → `304 Not Modified`. Der Report-ETag ist
  `"<report-id>:<revision>"`, der Kalender-ETag ein Hash aus Bereich und
  enthaltenen Revisionen.
- Fehler kommen im Envelope `{"error": {"code", "message", "requestId"}}`.
- `429` bei überschrittenem Rate-Limit, mit `Retry-After`.
- Jede Antwort trägt `X-Request-ID`.

Der verbindliche Vertrag steht in [contracts/openapi.yaml](contracts/openapi.yaml);
Beispiel-Payloads liegen in [contracts/examples/](contracts/examples/).

## Tests

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -v
```

Die Integrationstests benötigen `TEST_DATABASE_URL`. Ist die Variable nicht
gesetzt, werden sie übersprungen statt zu fehlschlagen. Beispiel gegen die
Compose-Dev-Datenbank:

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://daily_signal:daily_signal@localhost:5432/daily_signal_test"
uv run pytest -v
```

CI (`.github/workflows/ci.yml`) führt Lint, Formatprüfung, strikte Typprüfung,
Migrationstest und Contract-/API-Tests aus.

## Quellenrechte

> **Warnung:** Es sind keine Quellen produktiv freigegeben.

Alle drei registrierten Quellen sind anfangs `review_status: in_review`,
`enabled: false` und `permissions_approved: false`; sämtliche produktiven
Permission-Flags sind `false`. Aus einer CC-Lizenz oder der Verfügbarkeit eines
RSS-Feeds folgt **keine** automatische Freigabe: Jede Nutzungsart
(Metadaten, Volltext, Analyse, externe LLM-Übermittlung, Veröffentlichung) wird
getrennt und artikelbezogen geprüft. Eine Freigabe ist eine separate,
protokollierte Aktion mit `approved_by`/`approved_at`. Rohtexte und Prompts
dürfen nie in Logs landen. Details in
[docs/source-policy.md](docs/source-policy.md).

## Repository-Struktur

```text
daily-signal/
├── .github/workflows/        CI (Lint, Typen, Tests) und Container-Build
├── config/                   sources.yaml, methodology.yaml
├── contracts/                openapi.yaml + examples/
├── docs/                     architecture, data-model, source-policy,
│                             scoring-methodology, adr/, specs/
├── migrations/               Alembic-Umgebung und initiale Migration 0001
├── src/daily_signal/
│   ├── api/                  FastAPI-Routen, Schemas, Middleware, ETags, Fehler
│   ├── application/          Queries, Ports, Methodik-Loader
│   ├── domain/               Enums, Scoring, Lizenzregeln
│   ├── infrastructure/db/    ORM-Modelle, Session, Repositories, Seed
│   ├── jobs/                 worker, scheduler
│   ├── core/                 config, clock, logging
│   ├── cli.py                seed-sources / worker / scheduler
│   └── main.py               App-Factory
├── tests/                    unit/, integration/, contract/, fixtures/
├── compose.yaml, compose.dev.yaml, Dockerfile
├── pyproject.toml, uv.lock, alembic.ini, .env.example
└── README.md
```

## Nicht-Ziele und nächste Schritte

Ausdrücklich **nicht** Teil dieses Fundaments sind: Feed-Adapter und
HTTP-Ingestion, Event-Clustering, LLM-Provider-Integration und Prompt-Ausführung,
Berichtsgenerierung, Validierungs-/Publikations-/Korrekturworkflow,
Content-Purge-Jobs, Authentifizierung, Admin-UI, Caddy/TLS-Terminierung und
Produktions-Deployments.

Die nächsten Schritte (siehe Spezifikationspaket) sind insbesondere:
technische Feed-Smoke-Tests, artikelbezogene Rechteprüfung je Quelle,
Implementierung der Freigabe- und Löschlogik, Referenzdaten für mindestens 30
Tage zur Qualitäts- und Coverage-Evaluation sowie die Dokumentation der
tatsächlichen Attributions- und ShareAlike-Pflichten pro Output.

## Dokumentation

- [docs/architecture.md](docs/architecture.md) – Modularer Monolith, Schichten, Prozesse, Migrationen, ETags.
- [docs/data-model.md](docs/data-model.md) – 14 Tabellen, Revisions- und Rechte-Modell.
- [docs/source-policy.md](docs/source-policy.md) – Quellen, Lizenzen und Freigaberegeln.
- [docs/scoring-methodology.md](docs/scoring-methodology.md) – Formel, Schwellen, Farben, Confidence.
- [docs/adr/0001-modular-monolith.md](docs/adr/0001-modular-monolith.md) – Architektur-Entscheidung.
- [docs/specs/daily-signal-v1.0/](docs/specs/daily-signal-v1.0/) – Spezifikationspaket (Datenmodell, OpenAPI, Repository-Layout).
- [contracts/openapi.yaml](contracts/openapi.yaml) – verbindlicher öffentlicher API-Vertrag.
