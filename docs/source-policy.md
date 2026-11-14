# Quellen- und Rechtspolitik

> **Es sind keine Quellen produktiv freigegeben.** Alle drei registrierten
> Quellen sind zunächst `review_status: in_review`, `enabled: false`,
> `permissions_approved: false`, und **alle** produktiven Permission-Flags sind
> `false`.

Die maßgebliche Konfiguration steht in [config/sources.yaml](../config/sources.yaml)
und wird vom Seed (`python -m daily_signal.cli seed-sources`) in die Datenbank
übernommen. Der Seed ist **fail-closed**: `load_sources_config` und
`seed_sources` lehnen jede Konfiguration ab, die Rechte erteilt, bevor sie die
Datenbank berührt.

## Die drei Quellen

| Slug | Name | Land | Sprache | Lizenz | Feed |
|---|---|---|---|---|---|
| `global-voices` | Global Voices | NL | en | `CC-BY-3.0` | `https://globalvoices.org/feed/` |
| `netzpolitik-org` | netzpolitik.org | DE | de | `CC-BY-NC-SA-4.0` | `https://netzpolitik.org/feed` |
| `el-salto` | El Salto | ES | es | `CC-BY-SA-3.0-ES` | `https://www.elsaltodiario.com/general/feed` |

Für jede Quelle gilt:

- `review_status: in_review`, `enabled: false`, `permissions_approved: false`.
- Lizenz, Lizenz-URL, Terms-URL, `content_scope` und
  `attribution_requirements` sind dokumentiert.
- Alle Rechteflags des ersten Rechteprofils sind `false`:
  `fetch_metadata`, `fetch_full_text`, `analyze_content`, `store_temporary`,
  `store_long_term`, `send_to_external_llm`, `create_embeddings`,
  `create_adaptations`, `republish_original_content`, `publish_derivatives`,
  `republish_media`.

## Keine automatischen Freigaben

- Aus einer **CC-Lizenz** oder der bloßen **RSS-Verfügbarkeit** folgt **keine**
  pauschale Freigabe aller Verarbeitungsschritte. Die Lizenz beschreibt die
  rechtliche Grundlage, nicht die getroffene Freigabe.
- Die einzelnen Nutzungsarten – Metadaten, Volltext, Analyse, temporäre und
  langfristige Speicherung, externe LLM-Übermittlung, Embeddings, Bearbeitungen,
  Veröffentlichung von Derivaten, Mediennutzung – werden **getrennt**
  autorisiert.
- **Artikelbezogene Ausnahmen haben Vorrang** vor den Standardrechten einer
  Quelle. Jeder Artikel trägt eigene Rechte-Metadaten (`license_verified`,
  `contains_third_party_material`).
- BY-SA- und BY-NC-SA-Bearbeitungen dürfen nicht blind zu einem einheitlich
  lizenzierten Werk vermischt werden. Eigene, auf Fakten beruhende
  Formulierungen und lizenzierte Bearbeitungen werden systemseitig
  unterschieden (`content_basis`: `facts_synthesis` vs. `adaptation`). Ob ein
  konkreter Output eine Bearbeitung ist, bleibt gegebenenfalls ein rechtlicher
  Prüfpunkt.

## Freigabe ist eine separate, auditierte Aktion

Eine Freigabe erfolgt **nicht** durch einen Umgebungsvariablenwechsel und
**nicht** über einen öffentlichen Endpunkt. Sie ist eine eigene, nachvollziehbare
Aktion:

- `source_permissions.review_status='approved'` verlangt laut Constraint
  `permission_approval_has_auditor` sowohl `approved_by` als auch `approved_at`.
- `news_sources.enabled=true` ist laut `source_enable_requires_approval` nur bei
  `review_status='approved'` erlaubt.
- Rechteprofile sind versioniert (`UNIQUE (source_id, revision)`), sodass jede
  Änderung als neue Revision nachvollziehbar bleibt.

Die öffentliche Route `GET /v1/sources` liefert ausschließlich Quellen, die
freigegeben, aktiviert und mit einem freigegebenen Rechteprofil versehen sind –
im Fundament also eine leere Liste.

## Betriebsregeln

- **Rohtexte und Prompts nie in Logs.** Fehler- und Performance-Logs enthalten
  IDs und technische Metriken, keine Original-Volltexte oder fremdlizenzierten
  Inhalte.
- **Keine Browser-Search-Pipeline.** Als Quellenadapter sind ausschließlich
  freigegebene, dokumentierte offizielle Feeds und APIs vorgesehen.
- **Keine produktiven Abrufe vor Freigabe.** Bis zur Freigabe werden keine
  Quellen produktiv gepollt.

## Noch offen

Vor einem produktiven Start sind technische Feed-Smoke-Tests, die
artikelbezogene Rechteprüfung je Quelle, die Implementierung von Freigabe- und
Löschlogik sowie die Dokumentation der tatsächlichen Attributions- und
ShareAlike-Pflichten pro Output erforderlich. Siehe
[docs/specs/daily-signal-v1.0/README.md](specs/daily-signal-v1.0/README.md).
