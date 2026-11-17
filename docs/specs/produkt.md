# Produktspezifikationen

Basis der Bestandsaufnahme ist `a24fea7` vom Stand am 17. November 2026. Die verlinkten Tests bezeichnen vorhandene Prüfpunkte. Fachliche Detailverträge stehen im [API-Vertrag](../../contracts/openapi.yaml), im [Datenmodell](../data-model.md), in der [Scoring-Methodik](../scoring-methodology.md) und in der [Quellenmatrix](quellenmatrix.md).

## DS-001 Laufzeit und Architektur

Status: implementiert

Ein Python-3.13-Paket mit getrennter API, Anwendungslogik, Domäne und Infrastruktur. API, Scheduler und Worker laufen als getrennte Prozesse aus demselben Image. Compose wartet auf PostgreSQL 17 und auf den erfolgreichen Migrations- und Seed-Schritt. Nur die Dev-Konfiguration veröffentlicht den DB-Port.

Umsetzung: [compose.yaml](../../compose.yaml) · Prüfung: [tests/unit/test_cli.py](../../tests/unit/test_cli.py)

## DS-002 Datenmodell und Migration

Status: implementiert

Alembic legt die 14 Tabellen an. Eindeutige Datumsrevision, höchstens eine aktuelle veröffentlichte Revision, Grenzen für Rang, Impact und Score, Ablaufdatum für Volltext und erforderliche Lizenzfelder für Bearbeitungen sind auf DB-Ebene verankert. Details und Beziehungen stehen im Datenmodell.

Umsetzung: [migrations/versions/0001_initial.py](../../migrations/versions/0001_initial.py) · Prüfung: [tests/integration/test_migrations.py](../../tests/integration/test_migrations.py)

## DS-003 Quellenregister und Seed

Status: implementiert

Wiederholtes Seeding registriert Global Voices (CC-BY-3.0), netzpolitik.org (CC-BY-NC-SA-4.0) und El Salto (CC-BY-SA-3.0-ES). Der Ausgangszustand ist in_review, deaktiviert und ohne produktive Rechte. Eine freigebende Seed-Konfiguration wird zurückgewiesen.

Umsetzung: [src/daily_signal/infrastructure/db/seed.py](../../src/daily_signal/infrastructure/db/seed.py) · Prüfung: [tests/integration/test_seed.py](../../tests/integration/test_seed.py)

## DS-004 Rechteprüfung in der Domäne

Status: implementiert

Die Publikationsregel verlangt ein genehmigtes Rechteprofil, verifizierte Artikellizenz, Analyse- und Veröffentlichungsrecht. Fremdmaterial sperrt den Artikel. Bearbeitung, Volltext und externer Modellaufruf erfordern jeweils ihr eigenes Recht.

Umsetzung: [src/daily_signal/domain/licensing.py](../../src/daily_signal/domain/licensing.py) · Prüfung: [tests/unit/test_rights.py](../../tests/unit/test_rights.py)

## DS-005 Tages-Score und Methodik

Status: implementiert

Für negative, neutrale und positive Stories gilt Σ(Richtungswert × Impact²) / Σ(Impact²). Mixed und unknown entfallen aus beiden Summen. Ohne bewertbare Story gibt es keinen Score. Methodik v1.0.0 definiert Schwellen, Grenzinklusion, fünf Labels und Farben gemäß Scoring-Methodik. Die API liefert die beim Start validierte Konfiguration.

Umsetzung: [src/daily_signal/domain/scoring.py](../../src/daily_signal/domain/scoring.py) · Prüfung: [tests/unit/test_scoring.py](../../tests/unit/test_scoring.py)

## DS-006 Öffentliche Berichte

Status: implementiert

Kalender liefert aktuelle veröffentlichte Revisionen aufsteigend, maximal 366 Tage inklusive. Fehlende Tage fehlen im Kalender. Latest bezeichnet das jüngste veröffentlichte Datum. Detail, Storyliste und Story-ID blenden ersetzte Revisionen aus. Filter für Richtung, Kategorie und Region gelten gemeinsam. Story-ID und Attribution gehören zur Revision.

Umsetzung: [src/daily_signal/infrastructure/db/repositories/reports.py](../../src/daily_signal/infrastructure/db/repositories/reports.py) · Prüfung: [tests/integration/test_api_reports.py](../../tests/integration/test_api_reports.py)

## DS-007 Quellen- und Methodik-API

Status: implementiert

GET /v1/sources liefert nur aktivierte, freigegebene Quellen mit freigegebenem Rechteprofil. Nach initialem Seed bleibt die Liste leer. GET /v1/methodology liefert die öffentliche Methodik. Die sieben Fachrouten und zwei Healthchecks folgen dem versionierten HTTP-Vertrag.

Umsetzung: [src/daily_signal/api/v1/router.py](../../src/daily_signal/api/v1/router.py) · Prüfung: [tests/integration/test_api_sources.py](../../tests/integration/test_api_sources.py)

## DS-008 HTTP-Verhalten und Betriebssignale

Status: implementiert

Live prüft den Prozess, Ready die DB. Fehler enthalten Code, Nachricht und Request-ID. Rate-Limiting liefert 429 mit Retry-After. Report- und Kalender-ETags erlauben bedingte GETs mit leerem 304. CORS folgt der Konfiguration. Logs verwenden die vorgesehenen technischen Felder.

Umsetzung: [src/daily_signal/api/middleware.py](../../src/daily_signal/api/middleware.py) · Prüfung: [tests/unit/test_api_middleware.py](../../tests/unit/test_api_middleware.py)

## DS-009 Scheduler und Worker-Grundbetrieb

Status: implementiert

Worker prüft die DB per Heartbeat. Scheduler tickt beim Start und standardmäßig alle 15 Minuten. Ab 03:30 Europe/Berlin meldet er den vorigen lokalen Kalendertag unter Advisory Lock. Der Tick gibt den Lock wieder frei und erzeugt im Fundament keinen Laufdatensatz.

Umsetzung: [src/daily_signal/jobs/scheduler.py](../../src/daily_signal/jobs/scheduler.py) · Prüfung: [tests/integration/test_scheduler.py](../../tests/integration/test_scheduler.py)

## DS-010 CI und Container-Build

Status: implementiert

Push und Pull Request prüfen mit uv.lock Lint, Format, Typen, Verträge und Tests inklusive PostgreSQL. Ein eigener Workflow baut das Image mit Commit-SHA als Tag.

Umsetzung: [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · Prüfung: [tests/unit/test_ci_workflows.py](../../tests/unit/test_ci_workflows.py)

## DS-011 Quellenfreigabe und laufender Audit

Status: offen

Ein manueller Freigabeschritt dokumentiert Prüfer, Zeitpunkt, Rechte-Revision, redaktionelle und technische Prüfung. Sperrung, Ablauf oder Terms-Änderung stoppen betroffene Verarbeitungsschritte. Abnahme gemäß LIC und OPS der Quellenmatrix. Vorhanden sind die DB-Constraints und die gesperrte Startkonfiguration.

## DS-012 Eingang und Normalisierung

Status: offen

Adapter für die drei offiziellen Feeds prüfen Rechte vor Abruf, normalisieren und deduplizieren Artikel und erkennen Änderungen. Für jeden Feed sind Smoke-Tests sowie Fehler-, Retry-, 304-, Quarantäne- und Dublettenfälle nach TEC nachzuweisen.

## DS-013 Ereignisse und Belegketten

Status: offen

Updates und Dubletten einem Ereignis zuordnen, Agenturübernahmen als gemeinsame Evidenzlinie behandeln. Wesentliche Claims müssen auf erlaubte Artikel zurückführbar sein. Widersprüche und fehlende unabhängige Evidenz führen zur Kennzeichnung oder Sperre nach EVD.

## DS-014 Modellverarbeitung und Berichtsentwurf

Status: offen

Extraktion, Ranking und Zusammenfassung verwenden versionierte Prompts und validierte strukturierte Ausgaben. Externe Übertragung setzt Providerprüfung und Artikelrechte voraus. Der Entwurf enthält 5–8 eigenständige, belegte Ereignisse des Berliner Vortags, gewichtet nach Relevanz und Auswirkungen. Die Domäne berechnet den Score. Bei unzureichender Abdeckung bleibt der Tag unveröffentlicht.

## DS-015 Validierung und Veröffentlichung

Status: offen

QA prüft 5–8 Stories, unterstützte Claims, unabhängige Evidenz, Rechte, Attribution, Score-Schwellen und Confidence high oder medium. Stories, Attributions-Snapshots, QA-Ergebnis und Current-Umschaltung werden atomar gespeichert. Ein fehlgeschlagener Check oder Transaktionsabbruch darf keinen teilweise sichtbaren Bericht erzeugen.

## DS-016 Korrektur, Rücknahme und Löschung

Status: offen

Korrekturen erzeugen eine neue Revision und wechseln atomar die öffentliche Fassung. Rücknahmen und Rechteentzug müssen bis in die API wirken. Ein Purge-Job entfernt abgelaufene Volltexte gemäß Rechteprofil. Abnahme mit alter Story-ID, Rücknahme und wiederholtem Löschlauf.

## DS-017 Dauerhafte Tagesverarbeitung

Status: offen

Fällige Tage persistent und idempotent beanspruchen, bearbeiten und nach Neustart nachholen. Zwei Prozesse, wiederholte Ticks und ein Neustart zwischen Claim und Abschluss dürfen keinen doppelten veröffentlichten Bericht erzeugen. Der derzeitige Advisory Lock deckt nur die Dauer eines Ticks ab.

## DS-018 Abnahme vor öffentlichem Regelbetrieb

Status: offen

Mindestens drei rechtlich nutzbare unabhängige Redaktionen aus mindestens zwei Gruppen mit DE/EU- und internationaler Abdeckung. Mindestens 30 Testtage oder belastbare historische/simulierte Fälle auswerten. Bei Quellenausfall muss die Veröffentlichung sperren. Go-live-Checkliste und Betriebsparameter stehen in der Quellenmatrix.

## DS-019 Produktionsbereitstellung

Status: offen

API über Caddy erreichbar machen, PostgreSQL und Jobs intern halten, eindeutige Image-Version bereitstellen und vor API-Wechsel migrieren. Der vorhandene Container-Workflow baut mit push: false. Ein Release samt produktiver Proxy-Konfiguration ist im Repository noch nicht belegt.

## DS-020 Semantischer Vertragsvergleich

Status: offen

Fachvertrag und generiertes OpenAPI auch hinsichtlich Parameter, Antwortcodes und Payload-Schemas vergleichen. Die bestehende Prüfung vergleicht Routen, Methoden und operationId. Zusätzliche Beispiel- und API-Tests decken einzelne Payloads ab. Eine inkompatible Schemaänderung muss den Vergleich fehlschlagen lassen.
