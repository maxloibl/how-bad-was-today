# Architektur

Daily Signal ist ein **modularer Monolith**: ein Python-Paket
(`src/daily_signal`) und ein Container-Image, aus dem mehrere Prozesse mit
unterschiedlichen Entrypoints gestartet werden. Die Schichtung trennt
HTTP-Vertrag, Anwendungsfälle und Domänenregeln klar von der Infrastruktur.

## Schichten und Abhängigkeitsregel

```text
api/  ─────────▶  application/  ─────────▶  domain/
                      ▲
                      │ implementiert Ports
              infrastructure/db/
```

- **`domain/`** enthält reine Fachlogik und Typen: `enums.py`, den
  Scoring-Algorithmus (`scoring.py`) und die Lizenz-/Rechteprüfung
  (`licensing.py`). Es importiert weder FastAPI noch SQLAlchemy noch HTTP.
- **`application/`** beschreibt Use-Cases und Port-Interfaces
  (`ports/repositories.py`), die Queries (`get_daily_report.py`,
  `list_daily_reports.py`) und das Laden der Methodik (`methodology.py`). Es
  kennt keine Provider- oder Datenbankdetails.
- **`api/`** bildet den öffentlichen OpenAPI-Vertrag ab: Routing, DTO-Validierung,
  Statuscodes, ETags, Rate-Limit, Fehler-Envelope und CORS. Es enthält keine
  Geschäftslogik.
- **`infrastructure/db/`** implementiert die Ports mit SQLAlchemy-2-Modellen,
  Repositories, Sessions und Advisory Locks. Es erzeugt keine HTTP-Antworten.
- **`jobs/`** enthält die periodischen Prozess-Entrypoints (`worker.py`,
  `scheduler.py`).
- **`core/`** bündelt querschnittliche Bausteine: `config.py`, `clock.py`
  (Europe/Berlin/UTC) und `logging.py`.

Die Abhängigkeit zeigt immer nach innen: `api → application → domain`.
`infrastructure` implementiert die in `application` deklarierten Ports; `domain`
hängt von nichts Framework-spezifischem ab.

## Prozesse

Alle Prozesse teilen Codebasis und Image (`daily-signal:latest`) und
unterscheiden sich nur im Kommando:

| Prozess | Entrypoint | Aufgabe |
|---|---|---|
| `api` | `uvicorn daily_signal.main:app` | Öffentliche, read-only HTTP-API. |
| `worker` | `python -m daily_signal.cli worker` | Heartbeat und späteres Hintergrundarbeiten; prüft die DB mit `SELECT 1`. |
| `scheduler` | `python -m daily_signal.cli scheduler` | Tick alle `SCHEDULER_TICK_SECONDS`; ab 03:30 Europe/Berlin markiert er eine fällige Tagesanalyse unter Advisory Lock. |
| `migrate` | `alembic upgrade head && python -m daily_signal.cli seed-sources` | Einmaliger, kontrollierter Migrations- und Seed-Schritt. |

**Kein Admin-Interface:** Die API ist rein lesend. Administrative Aktionen
laufen über abgesicherte CLI-Kommandos (z. B. `seed-sources`) bzw. über
Deployment-Prozesse, nicht über öffentliche Endpunkte.

**Ehrliche Platzhalter:** Worker und Scheduler sind bewusst defensiv. Der
Scheduler schreibt im Fundament **keinen** `pipeline_runs`-Eintrag und keinen
Ersatzbericht, sondern loggt nur `daily_analysis_due`; dadurch bleiben
Catch-up-Semantik und Idempotenz ehrlich, bis der echte Workflow existiert.
Fehler werden mit Klassenname und Message geloggt – niemals mit
Artikel-Volltexten oder Prompts.

## Migrationen als kontrollierter Schritt

Das Schema entsteht **ausschließlich** über Alembic, nie beim API-Start. In
Compose läuft der `migrate`-Service einmalig `alembic upgrade head` und danach
den Quellen-Seed; `api`, `worker` und `scheduler` starten erst nach
erfolgreichem Abschluss (`condition: service_completed_successfully`). Die
Migration ist idempotent und wird bei einem leeren Schema genauso erfolgreich
ausgeführt wie bei bereits migriertem Stand. `docs/specs/.../schema.sql` ist
Referenz, keine zweite produktive Migrationsquelle.

## ETag- und Revisions-Semantik

- Ein Bericht wird durch `(report-id, revision)` identifiziert. Der ETag ist
  `"<report-id>:<revision>"`, sodass eine neue Revision den Cache invalidiert.
- Der Kalender-ETag ist ein SHA-256-Hash aus angefragtem Bereich und den
  enthaltenen `(id, revision)`-Paaren.
- Ein passendes `If-None-Match` (einzelner Tag, Liste, schwacher `W/`-Tag oder
  `*`) führt zu `304 Not Modified` ohne Body.
- Ausgeliefert wird nur die aktuelle veröffentlichte Revision
  (`is_current=true`, `status='published'`). Ersetzte Revisionen und ihre Stories
  sind nicht öffentlich erreichbar; eine Story-ID ist ein
  revisionsgebundener Snapshot, keine artikel- oder tagesübergreifende
  Ereignis-ID.

## Uhrzeit und Kalendertag

Der Berichtstag ist ein `Europe/Berlin`-Kalendertag; Datenbankzeitstempel sind
UTC (`TIMESTAMPTZ`). Die Tagesauswertung darf frühestens **03:30 Europe/Berlin**
starten; die ursprünglich erwogene Zeit 02:00 liegt in der
Sommer-/Winterzeitumstellung und ist für lokale Cron-Ausführung ungeeignet.

## Nicht implementiert

Feed-Adapter/HTTP-Ingestion, Event-Clustering, LLM-Provider-Aufrufe,
Berichtsgenerierung, Validierungs-/Publikations-/Korrekturworkflow und
Content-Purge-Jobs existieren im Fundament nicht. Siehe
[docs/data-model.md](data-model.md) und das Spezifikationspaket
[docs/specs/daily-signal-v1.0/README.md](specs/daily-signal-v1.0/README.md).
