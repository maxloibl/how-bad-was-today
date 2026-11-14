# ADR 0001: Modularer Monolith mit drei Prozessen

- Status: akzeptiert
- Datum: 2026-11-13

## Kontext

Daily Signal besteht aus einer öffentlichen, rein lesenden API sowie
Hintergrundarbeit (Ingestion, spätere Tagesanalyse, Aufräumjobs), die
periodisch und zuverlässig laufen muss. Die Anwendungsdomäne ist noch klein,
das Team ist klein, und das Fundament soll schnell lauffähig, testbar und
wartbar sein. Gleichzeitig sollen sich die Prozesse später unabhängig skalieren
und absichern lassen, ohne den Anwendungscode zu duplizieren.

## Entscheidung

Wir bauen **einen modularen Monolithen**: ein Python-Paket (`src/daily_signal`)
und **ein Container-Image**, aus dem **drei Prozesse** mit unterschiedlichen
Entrypoints gestartet werden:

- `api` – öffentliche read-only HTTP-API (`uvicorn daily_signal.main:app`),
- `worker` – Hintergrundarbeit (`python -m daily_signal.cli worker`),
- `scheduler` – periodischer Tick (`python -m daily_signal.cli scheduler`).

Hinzu kommt ein einmaliger `migrate`-Schritt (`alembic upgrade head` plus
Quellen-Seed), auf den die anderen Services warten.

Die innere Struktur folgt der Abhängigkeitsregel `api → application → domain`;
`infrastructure/db/` implementiert die in `application/` deklarierten Ports.
Die Prozesse teilen sich Codebasis, Modelle und Konfiguration, laufen aber als
getrennte Betriebseinheiten. Es gibt **kein** öffentliches Admin-Interface;
administrative Aktionen laufen über abgesicherte CLI-Kommandos und Deployment.

## Betrachtete Alternativen

1. **Getrennte Services/Repositories** (eigene API-, Ingestion- und
   Scheduler-Dienste mit eigenen Deployments). Verworfen für das Fundament:
   höherer Betriebs- und Koordinationsaufwand, doppelte Modelle/Verträge und
   mehr Reibung, solange die Domäne und das Team klein sind.
2. **Queue-first-Architektur** (z. B. Redis/Celery oder ein Message-Broker von
   Beginn an). Verworfen für das MVP: zusätzliche Infrastruktur und
   Betriebskomplexität, ohne dass im Fundament echte Joblast existiert. Für das
   MVP genügt DB-basiertes Job-Claiming mit Advisory Locks.
3. **Ein einzelner Prozess für alles**. Verworfen: API und Hintergrundarbeit
   haben unterschiedliche Laufzeit-, Fehler- und Skalierungsprofile; eine
   Trennung in Prozesse ist günstig und verbessert die Isolation.

## Konsequenzen

Positiv:

- Ein Paket, ein Image, eine Versionslinie – einfache Builds, Tests und
  Deployments.
- Prozesse bleiben logisch und betrieblich getrennt und lassen sich später
  einzeln skalieren oder herauslösen.
- Klare Schichtung und Ports halten die Domäne frei von Framework- und
  Providerdetails.

Negativ / Risiken:

- Die Prozesse teilen sich ein Release; ein Rollback betrifft alle.
- Ohne Broker braucht Idempotenz und Catch-up besondere Sorgfalt. Der
  Scheduler nutzt deshalb einen PostgreSQL-Advisory-Lock und markiert eine
  fällige Analyse nur; durableres Catch-up (z. B. ein Claim-Row in
  `pipeline_runs`) ist als nächster Schritt vorgesehen.
- Ein späteres Herauslösen einzelner Prozesse erfordert bewusste Schnitte,
  wird aber durch die bestehende Port-/Schichtgrenze begünstigt.
