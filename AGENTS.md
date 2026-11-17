# Daily Signal

## Entwicklung anhand der Specs

1. Beginne bei [docs/specs/README.md](docs/specs/README.md). Benenne die betroffenen DS-IDs und bei Quellenarbeit die IDs der Quellenmatrix im Arbeitsplan oder Pull Request.
2. Beschreibe neues oder geändertes Verhalten zuerst als überprüfbares Abnahmekriterium. Vergib stabile IDs und verwende für ausstehendes oder teilweise umgesetztes Verhalten den Status `offen`.
3. Implementiere den beschriebenen Anwendungspfad und prüfe auch relevante Fehlerfälle. Pflege bei Vertragsänderungen OpenAPI, Konfiguration, Migrationen und Beispiele im selben Änderungssatz.
4. Setze den Status erst mit nachvollziehbarem Nachweis auf `implementiert`. Verlinke bei Produkt-Specs Umsetzung und Test, bei Quellenprüfungen den tatsächlichen Auditbefund. Halte verbleibende Abnahmelücken explizit offen.
5. Führe `uv run pytest tests/contract/test_specs.py` und die betroffenen Fachtests aus. Vor Abschluss gelten die Prüfungen in der [CI](.github/workflows/ci.yml). Für Integrationstests ist eine isolierte PostgreSQL-Testdatenbank erforderlich. Übersprungene Tests im Ergebnis ausweisen.

Schichtung und Laufzeitgrenzen stehen in [docs/architecture.md](docs/architecture.md). Der Seed bleibt ohne produktive Rechte. Im normalen Entwicklungs- und Testlauf synthetische Fixtures verwenden.
