# Daily Signal entwickeln

| Einstieg | Inhalt |
|---|---|
| [Produktspezifikationen](produkt.md) | DS-IDs für API, Datenhaltung, Rechte, Auswertung, Veröffentlichung und Betrieb. Jeder Abschnitt nennt seinen Status und sein Abnahmeverhalten. |
| [Quellenmatrix](quellenmatrix.md) | Einzelanforderungen mit stabilen IDs, Priorität, Abnahmekriterium und Status. Enthält auch Betriebsparameter, Audit-Checklisten und Go-live-Kriterien. |
| [Redaktionelle Auswahl](quellenpruefung.md) | Dokumentierte Befunde zu den drei Startkandidaten. |
| [Architekturpaket v1.0](daily-signal-v1.0/README.md) | Entwurfsgrundlage mit Referenzschema, Beispielkonfiguration und Zielstruktur. Laufende Änderungen gehören in die aktiven Specs. |

**Implementiert** bedeutet, dass das beschriebene Verhalten im Repository nachvollziehbar umgesetzt ist. Bei redaktionellen Kriterien zählt der dokumentierte Prüfbefund für alle drei Startkandidaten. **Offen** umfasst auch teilweise vorhandene Grundlagen. MUSS, SOLL und KANN bezeichnen die Priorität unabhängig vom Status.

Für eine Änderung zuerst die betroffenen IDs und Abnahmekriterien bestimmen. Neue Anforderungen erhalten eine neue ID. Den Status anhand des normalen Anwendungspfads und passender Tests aktualisieren. Die Quellenmatrix führt Betriebsnachweise und Freigaben eigenständig. Ein bestandener Softwaretest ist keine Quellenfreigabe.

Die Detailverträge sind [OpenAPI](../../contracts/openapi.yaml), [Quellenkonfiguration](../../config/sources.yaml), [Methodik](../../config/methodology.yaml) und [Migrationen](../../migrations/versions/0001_initial.py). Änderungen an diesen Verträgen mit ihren Specs und Beispielen im selben Änderungssatz pflegen.
