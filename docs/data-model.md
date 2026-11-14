# Datenmodell

Das relationale Schema umfasst **14 Tabellen** und wird als Alembic-Migration
`0001` verwaltet. `docs/specs/daily-signal-v1.0/schema.sql` ist die
Referenzdarstellung; produktiv gilt allein die Migration. UUIDs werden von der
Anwendung erzeugt, alle Zeitstempel sind UTC-aware (`TIMESTAMPTZ`).

## Tabellen nach Verantwortlichkeit

### 1. Publisher und Quellen

| Tabelle | Zweck |
|---|---|
| `publisher_groups` | Verlag/Organisation (`slug`, `name`, `country_code`). |
| `news_sources` | Quelle mit Typ (`editorial`/`primary`), `review_status`, `enabled`; `enabled` nur bei `review_status='approved'` erlaubt. |
| `source_feeds` | Feed je Quelle (`rss`/`atom`/`api`), Poll-Intervall, ETag/Last-Modified, Fehlerzähler. |
| `source_permissions` | **Versionierte Rechteprofile** je Quelle (`UNIQUE (source_id, revision)`). |

### 2. Eingangs-Items und geschützte Volltexte

| Tabelle | Zweck |
|---|---|
| `source_items` | Artikel-Metadaten und artikelbezogene Rechte-Metadaten; bindet `permission_id` und `feed_id`. |
| `source_item_content` | Geschützter Originalvolltext mit **verpflichtendem `expires_at`** (1:0..1 zu `source_items`). |

### 3. Ereignisse und Belege

| Tabelle | Zweck |
|---|---|
| `events` | Geclustertes Ereignis mit Region und Kategorie. |
| `event_items` | n:m-Verknüpfung Ereignis ↔ Artikel. |
| `event_claims` | Einzelaussagen eines Ereignisses mit `verification_status` (`supported`/`disputed`/`unverified`). |
| `claim_evidence` | Belege je Aussage mit Rolle (`supports`/`contradicts`/`context`) und Artikelbezug. |

### 4. Pipeline-Läufe

| Tabelle | Zweck |
|---|---|
| `pipeline_runs` | Ein Lauf je Job-Typ (`ingestion`/`daily_analysis`/`correction`/`cleanup`), Status, Modell-/Prompt-/Methodik-Version, Kosten, `quality_checks`. |

### 5. Berichte und Veröffentlichung

| Tabelle | Zweck |
|---|---|
| `daily_reports` | **Eine Zeile je Datum und Revision**; hält Score, Status und `is_current`. |
| `daily_report_stories` | Geordnete Stories (`rank` 1–8) einer Revision mit Richtung, Impact, Kategorie, Region, `content_basis`. |
| `story_sources` | **Attributions-Snapshot** je Story und Artikel. |

## Beziehungen

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

## Revisionsmodell

- `daily_reports` enthält **eine Zeile je `(report_date, revision)`**. Es gibt
  bewusst **keine** zweite, redundante Tabelle `report_revisions`.
- Ein partieller Unique-Index (`uq_current_published_report_per_day`) erzwingt
  höchstens **eine** aktuelle veröffentlichte Revision pro Datum
  (`WHERE is_current AND status='published'`).
- `daily_report_stories` und `story_sources` gehören exakt zu dieser Revision.
  Eine Korrektur legt eine neue Revision an und schaltet `is_current` um; die
  vorherige Revision bleibt unverändert erhalten.
- `daily_report_stories.direction` und `direction_value` sind über
  `direction_consistent` gekoppelt: `negative` → -2/-1, `positive` → 1/2,
  `neutral` → 0, `mixed`/`unknown` → `NULL`.
- `adaptation_metadata_required` verlangt bei `content_basis='adaptation'`
  Lizenzcode, Lizenz-URL und Änderungshinweis.

## Rechte-Profile (versioniert) und Attribution

- Rechteprofile sind **revisionsbezogen**: `source_permissions` hat
  `UNIQUE (source_id, revision)`, jedes Profil trägt Lizenz-, Terms- und
  Scope-Angaben sowie die einzelnen Permission-Flags.
- Ein Artikel bindet über `source_items.permission_id` die zugrunde gelegte
  Rechte-Revision und besitzt zusätzlich individuelle Rechte-Metadaten
  (`license_verified`, `contains_third_party_material`). Artikelbezogene
  Ausnahmen haben Vorrang vor den Standardrechten einer Quelle.
- `story_sources` speichert den zum Veröffentlichungszeitpunkt nötigen
  **Attribution-Snapshot** (Publisher, URL, Titel, Autor, Lizenz, Attribution,
  Agentur, `content_modified`). Dadurch bleibt die Attribution stabil, auch
  wenn sich der Originalartikel später ändert.
- `source_item_content` ist geschützter Volltext und nur zulässig, solange
  erlaubt; `expires_at` ist `NOT NULL`, ein Index
  (`ix_source_item_content_expiry`) unterstützt das Löschen abgelaufener
  Inhalte.

## Durch SQL erzwungene Invarianten

Einige Regeln lassen sich als `CHECK`/Unique-Constraint abbilden und sind im
Schema aktiv:

- `published_report_complete`: Ein veröffentlichter Bericht hat Headline,
  Summary, Score, Rohwert, Label, Erklärung, `published_at` und Confidence
  `high`/`medium`.
- `current_report_is_published`: `is_current` nur bei `status='published'`.
- `source_enable_requires_approval`: `enabled` nur bei `review_status='approved'`.
- `permission_approval_has_auditor`: `review_status='approved'` verlangt
  `approved_by` und `approved_at`.
- `rank BETWEEN 1 AND 8`, `impact BETWEEN 1 AND 5`,
  `score BETWEEN 1 AND 5`, `raw_score BETWEEN -2 AND 2`.

## Durch die Publikationstransaktion erzwungene Invarianten

Andere Regeln betreffen Zeilenzahlen oder Beziehungen über mehrere Tabellen und
können von `CHECK`-Constraints **nicht** validiert werden. Sie werden in der
**Publikationstransaktion** geprüft, nicht durch SQL:

1. **5–8 Stories** pro Bericht.
2. Alle referenzierten **Claims sind `supported`**.
3. **Geprüfte Rechte** (Freigabe, verifizierte Lizenz, keine Fremdmaterialien).
4. **Quellenunabhängigkeit** der Stories (nicht nur eine Quelle).
5. **Schwellen-Konsistenz**: Label, `raw_score` und `value` passen zu den
   konfigurierten Score-Grenzen.
6. **Umschaltung der aktuellen Revision** (`is_current`) als Teil derselben
   Transaktion.

Im Fundament ist diese Transaktion noch nicht implementiert; die Regeln sind
hier festgehalten, damit der spätere Publikationsworkflow sie einhält.
