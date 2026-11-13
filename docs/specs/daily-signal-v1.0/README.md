# Daily Signal – Datenmodell, OpenAPI und Repository-Layout (v1.0)

Dies ist ein **implementierungsnahes Architekturpaket**, kein laufendes Anwendungssystem.

## Dateien

| Datei | Zweck |
|---|---|
| `schema.sql` | PostgreSQL-Referenzschema (14 Tabellen, Indizes, Constraints). In Produktion durch Alembic-Migration abbilden, nicht zusätzlich ausführen. |
| `openapi.yaml` | Öffentlicher OpenAPI-3.1-Vertrag: 7 read-only Fachrouten plus 2 Betriebs-Healthchecks. |
| `repository-structure.md` | Zielstruktur, Modulverantwortlichkeiten, Laufzeitkonventionen, Compose-Services und erste Schritte. |
| `sources.yaml` | Beispiel für die drei ausgewählten Quellen; alle ausdrücklich `in_review` und deaktiviert. |

## Relationales Modell

```text
publisher_groups 1 ── * news_sources 1 ── * source_feeds
                              │
                              ├── * source_permissions (versionierte Rechteprofile)
                              └── * source_items 1 ── 0..1 source_item_content
                                           │
                                           ├── * event_items * ── 1 events
                                           │                        └── * event_claims
                                           │                                  └── * claim_evidence * ── source_items
                                           │
                                           └── * story_sources * ── daily_report_stories
                                                                      │
                                                                      ├── 1 events
                                                                      └── 1 daily_reports

daily_reports * ── 0..1 pipeline_runs
```

**Revisionsmodell:** `daily_reports` enthält **eine Zeile je Datum und Revision**. Mit `is_current` und einem partiellen Unique-Index gibt es höchstens eine aktuelle veröffentlichte Revision pro Datum. `daily_report_stories` und `story_sources` gehören exakt zu dieser Revision. Es gibt bewusst keine zweite, redundante Tabelle `report_revisions`.

**Lizenzmodell:** Rechteprofile sind revisionsbezogen. Ein Artikel bindet die zugrunde gelegte Rechte-Revision, besitzt aber zusätzlich seine individuellen Rechte-Metadaten. `story_sources` speichert den zum Veröffentlichungszeitpunkt nötigen Attribution-Snapshot. Geschützte Originalvolltexte liegen – soweit überhaupt erlaubt – nur in `source_item_content` mit verpflichtendem Ablaufzeitpunkt.

**Keine automatischen Freigaben:** Aus CC-Lizenz oder RSS-Verfügbarkeit folgt keine pauschale Freigabe aller Verarbeitungsschritte. Die drei ausgewählten Quellen haben anfangs keine produktiven Rechteflags. Die externe LLM-Übermittlung setzt gesonderte Prüfung voraus.

**Beispielhafte Quellkonfiguration:**

- Global Voices – `CC-BY-3.0`, RSS `https://globalvoices.org/feed/`
- netzpolitik.org – `CC-BY-NC-SA-4.0`, RSS `https://netzpolitik.org/feed`
- El Salto – **`CC-BY-SA-3.0-ES`**, RSS `https://www.elsaltodiario.com/general/feed`

**Urheberrechtlich relevante Bearbeitungen** unter BY-SA und BY-NC-SA dürfen nicht blind zu einem einheitlich lizenzierten Werk vermischt werden. Eigene, auf Fakten beruhende Formulierungen und lizenzierte Bearbeitungen müssen systemseitig unterschieden werden. Ob ein konkreter Output eine Bearbeitung ist, bleibt gegebenenfalls ein rechtlicher Prüfpunkt.

## Öffentliche Semantik

- Nur `status='published' AND is_current=true` ist öffentlich sichtbar.
- Ein `Story.id` ist eine versionsgebundene Daily-Report-Story, **keine** artikelübergreifende Ereignis-ID.
- `Europe/Berlin` bestimmt den Berichtstag; Datenbankzeitstempel sind `TIMESTAMPTZ`.
- Unveröffentlichte Tage fehlen im Kalender und erhalten keinen Score 3.
- Für 5–8 Nachrichten und die Erfüllung sämtlicher QA-Kriterien ist der Publikationsworkflow verantwortlich; SQL-`CHECK`-Constraints können keine Zeilenanzahl in einer Beziehung validieren.
- Tageswert: gewichtetes Mittel aus `direction_value * impact^2` für `negative`, `neutral`, `positive`. `mixed/unknown` werden ausgeschlossen. Grenzen: `< -1.1 → 1`, `[-1.1,-0.3) → 2`, `[-0.3,0.3] → 3`, `(0.3,1.1] → 4`, `> 1.1 → 5`.
- Score-Farben: `#CF6666`, `#DE9A57`, `#B8AC69`, `#85B78A`, `#43A779`.
- Veröffentlichung nur mit Confidence `high` oder `medium` und abgeschlossener Qualitätsprüfung.
- `GET /v1/days?from=...&to=...` akzeptiert maximal **366 Tage inklusive**.

## Designentscheidung zur Uhrzeit

Die Tagesauswertung wird frühestens **03:30 Uhr Europe/Berlin** ausgelöst. Die ursprünglich erwogene Zeit 02:00 Uhr liegt in der deutschen Sommer-/Winterzeitumstellung und ist daher für eine lokale Cron-Ausführung ungeeignet. Ein regelmäßiger Scheduler-Tick mit DB-Job-Lock und Catch-up-Funktion ist robuster als eine rein einmalige Cron-Ausführung.

## Vor dem produktiven Start noch notwendig

1. Technische Feed-Smoke-Tests (Struktur, ETag/Last-Modified, Rate-Limits, Korrekturen).
2. Artikelbezogene Rechteprüfung und Prüfung des tatsächlichen LLM-Providers.
3. Implementierung der Freigabe- und Löschlogik.
4. Referenzdaten für mindestens 30 Tage zur Qualitäts- und Coverage-Evaluation.
5. Dokumentation der tatsächlichen Attribution und ShareAlike-Pflichten pro Output.

## Eingrenzung

Das SQL enthält keine vollständige Verwaltungsoberfläche, Authentifizierungs-/Benutzerkonten oder Frontend-Tabellen. API und Scheduler sind absichtlich voneinander getrennt. Für das MVP wird keine Queue-Infrastruktur vorausgesetzt.
