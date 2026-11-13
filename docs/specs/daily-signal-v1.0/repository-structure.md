# Daily Signal – Repository-Struktur v1.0

## Architektur

Ein Python-Paket als modularer Monolith. HTTP-API, Ingestion-Worker und Scheduler verwenden denselben Anwendungscode und dasselbe Container-Image, jedoch unterschiedliche Prozess-Entrypoints. Kein öffentliches Admin-Interface; administrative Aktionen erfolgen über abgesicherte CLI-Kommandos. Datenbankmigrationen mit Alembic, keine automatische Tabellenerstellung beim API-Start.

```text
daily-signal/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── container.yml
├── config/
│   └── sources.yaml
├── contracts/
│   ├── openapi.yaml
│   └── examples/
│       ├── daily-report.json
│       └── api-error.json
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── source-policy.md
│   ├── scoring-methodology.md
│   └── adr/
│       └── 0001-modular-monolith.md
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   └── daily_signal/
│       ├── __init__.py
│       ├── main.py
│       ├── cli.py
│       ├── api/
│       │   ├── dependencies.py
│       │   ├── errors.py
│       │   ├── schemas/
│       │   │   ├── days.py
│       │   │   ├── stories.py
│       │   │   ├── sources.py
│       │   │   └── methodology.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── days.py
│       │       ├── stories.py
│       │       ├── sources.py
│       │       └── methodology.py
│       ├── domain/
│       │   ├── enums.py
│       │   ├── scoring.py
│       │   ├── licensing.py
│       │   └── entities.py
│       ├── application/
│       │   ├── ports/
│       │   │   ├── news_feed.py
│       │   │   ├── language_model.py
│       │   │   └── repositories.py
│       │   ├── queries/
│       │   │   ├── get_daily_report.py
│       │   │   └── list_daily_reports.py
│       │   └── workflows/
│       │       ├── ingest_sources.py
│       │       ├── cluster_events.py
│       │       ├── evaluate_day.py
│       │       ├── validate_report.py
│       │       └── publish_report.py
│       ├── infrastructure/
│       │   ├── db/
│       │   │   ├── base.py
│       │   │   ├── models.py
│       │   │   ├── session.py
│       │   │   └── repositories/
│       │   │       ├── reports.py
│       │   │       ├── sources.py
│       │   │       └── events.py
│       │   ├── feeds/
│       │   │   ├── http_client.py
│       │   │   ├── parser.py
│       │   │   └── adapters/
│       │   │       ├── global_voices.py
│       │   │       ├── netzpolitik.py
│       │   │       └── el_salto.py
│       │   └── llm/
│       │       ├── http_provider.py
│       │       ├── output_schemas.py
│       │       └── prompts/
│       │           └── v1/
│       │               ├── extract.md
│       │               ├── rank.md
│       │               └── summarize.md
│       ├── jobs/
│       │   ├── scheduler.py
│       │   ├── ingest.py
│       │   ├── analyze.py
│       │   └── purge.py
│       └── core/
│           ├── config.py
│           ├── logging.py
│           └── clock.py
├── tests/
│   ├── unit/
│   │   ├── test_scoring.py
│   │   ├── test_rights.py
│   │   └── test_clustering.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_migrations.py
│   │   └── test_ingestion.py
│   ├── contract/
│   │   └── test_openapi.py
│   └── fixtures/
│       ├── sample_feeds/
│       └── expected_reports/
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── compose.yaml
├── compose.dev.yaml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## Verantwortlichkeiten

| Paket | Verantwortung | Darf nicht |
|---|---|---|
| `api/` | HTTP-Routing, DTO-Validierung, Statuscodes, ETag, CORS | Geschäftslogik/LLM-Aufruf ausführen |
| `domain/` | Bewertungsalgorithmus, Typen, Lizenzregeln | FastAPI/SQLAlchemy/HTTP importieren |
| `application/` | Use-Cases, Workflows, Port-Interfaces, Publikations-Policy | Providerdetails enthalten |
| `infrastructure/db/` | ORM, Abfragen, Transaktionen, Advisory Locks | HTTP-Responses erstellen |
| `infrastructure/feeds/` | RSS/Atom-Adapter, sicheres HTTP, Normalisierung | Nicht freigegebene Quellen produktiv abrufen |
| `infrastructure/llm/` | REST-Client, Prompt-Versionierung, Schema-Parsing | Endgültigen Tages-Score frei erfinden |
| `jobs/` | Periodische Prozess-Entrypoints, Retry, Jobstatus | Öffentliche Endpunkte bereitstellen |

## Wichtige Konventionen

1. **Python-Paket**: `src/`-Layout, Installation über `uv sync --locked`, `uv.lock` im Git-Repository.
2. **Modellierung**: SQLAlchemy-2-`Mapped[...]`, `mapped_column()`, Alembic-Migrationen im Repository. `schema.sql` ist Referenz, keine zweite produktive Migrationsquelle.
3. **API-first**: `contracts/openapi.yaml` ist fachlicher Vertrag. CI vergleicht generiertes FastAPI-OpenAPI mit diesem Vertrag (semantisch, nicht bloß Textvergleich).
4. **API-Route-Reihenfolge**: `/v1/days/latest` vor `/v1/days/{date}` registrieren.
5. **UTC und Kalendertage**: Datenbankzeitstempel in UTC, `DATE` für `Europe/Berlin`-Berichtstag; Datumsgrenzen mit `zoneinfo` bilden.
6. **Scheduler**: alle 15 Minuten zuverlässigen `tick` ausführen. Die tägliche Analyse darf nach 03:30 Uhr Europe/Berlin starten. Idempotenz und DB-Lock verhindern doppelte Jobs; Neustarts holen ausgefallene Runs nach.
7. **Quellenfreigabe**: Alle drei Seed-Quellen zunächst `in_review`, `enabled: false`, alle Permission-Flags `false`; Freigabe separat und nachvollziehbar. Ein einfacher Umgebungsvariablenwechsel darf dies nicht umgehen.
8. **Eingangsrechte**: Artikelmetadaten, Volltexte, externe LLM-Übertragung und Veröffentlichung getrennt autorisieren; artikelbezogene Ausnahmen haben Vorrang vor der Standardlizenz einer Quelle.
9. **Quellennachweise**: Nachweise und Attribution am `source_item` und unveränderlich als Snapshot an `story_sources` speichern.
10. **Berichtsrevisionen**: Jede Zeile in `daily_reports` ist eine unveränderliche Revision. Die einzige aktuelle veröffentlichte Revision hat `is_current=true`; keine In-Place-Änderung veröffentlichter Inhalte.
11. **Transaktionale Veröffentlichung**: `daily_report_stories` (5–8), `story_sources`, QA-Ergebnis und Current-Revision-Umschaltung in einer DB-Transaktion.
12. **Keine Rohtexte in Logs**: Fehler- und Performance-Logs enthalten IDs und technische Metriken, keine Original-Volltexte oder LLM-Prompts mit fremdlizenzierten Inhalten.
13. **Keine Browser-Search-Pipeline**: Nur freigegebene, dokumentierte offizielle Feeds und APIs als Quellenadapter.
14. **Public API read-only**: Management über geschützte CLI und Deployment; keine öffentlichen Endpunkte für Jobs, Prompts oder freizugebende Quellen.

## Vorgesehene Compose-Services

| Service | Prozess | Öffentlich? |
|---|---|---|
| `api` | `uvicorn daily_signal.main:app --host 0.0.0.0 --port 8000` | Nur über Caddy |
| `worker` | `python -m daily_signal.cli worker` | Nein |
| `scheduler` | `python -m daily_signal.cli scheduler` | Nein |
| `db` | PostgreSQL | Nein |

In der einfachen Umsetzung kann `worker` ein DB-basiertes Job-Claiming verwenden; externe Queue ist für das MVP nicht erforderlich. Keine Host-Port-Freigabe für PostgreSQL in Produktion. Das Image wird in CI gebaut und unveränderlich versioniert; Migrationen werden vor der neuen API-Version als eigener kontrollierter Deploy-Schritt ausgeführt.

## Erste lokale Einrichtung (Reihenfolge)

1. Repository, `pyproject.toml`, `.python-version`, `uv.lock`, `.env.example`, Dockerfile und Compose-Dateien anlegen.
2. `contracts/openapi.yaml` und `docs/data-model.md` einchecken.
3. SQLAlchemy-Basisklasse, ORM-Modelle und eine initiale Alembic-Migration erstellen.
4. PostgreSQL und API lokal starten; `/health/live` und `/health/ready` testen.
5. Read-only Endpunkte gegen Fixtures aufbauen; API-Contract-Tests ergänzen.
6. Drei Quellen mit den Werten aus `config/sources.yaml` seed-en; keine produktiven Abrufe vor Freigabe.
7. Erst danach Feed-Adapter, LLM-Provider und Veröffentlichungsworkflow implementieren.

## Definition of Done für dieses Gerüst

- `uv sync --locked` funktioniert.
- `docker compose up -d --build` startet API und PostgreSQL und danach Worker/Scheduler ohne Crashloops.
- `alembic upgrade head` ist auf leerer Datenbank erfolgreich und idempotente Wiederholung funktioniert.
- `GET /health/live` und `GET /health/ready` liefern `200` bei gesundem System.
- `GET /v1/days?from=2026-11-01&to=2026-11-30` liefert zunächst `{"from":"2026-11-01","to":"2026-11-30","days":[]}`.
- `GET /v1/days/latest` liefert ohne Bericht `404` im standardisierten Fehlerformat.
- Alle drei Quellen sind registriert, `in_review`, deaktiviert, mit gesperrten produktiven Berechtigungen.
- CI führt Linting, Typprüfung, Tests, Migrations- und API-Kontraktprüfung aus.
