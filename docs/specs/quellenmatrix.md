# Daily Signal – Anforderungen an Nachrichtenquellen

> **Status:** Anforderungsspezifikation, Entwurf v1.0\
> **Stand:** 12. November 2026\
> **Geltungsbereich:** Quellenrecherche, Freigabe, Datenzugriff, Ingestion, Belegführung, Speicherung, LLM-Verarbeitung und Veröffentlichung\
> **Produkt:** Öffentlicher, nichtkommerzieller Nachrichtenüberblick mit täglich 5–8 relevanten Ereignissen, Schwerpunkt Deutschland/Europa\
> **Budget:** Keine kostenpflichtigen News-Feeds oder Nachrichtenlizenzen für das MVP; Hosting und LLM sind ausgenommen.

## 1. Zweck und Abgrenzung

Daily Signal soll Nachrichten nicht durch freie Websuche beschaffen. Die Anwendung verwendet eine **explizit gepflegte Whitelist geprüfter Nachrichten- und Primärquellen**. Die Sammlung erfolgt kontinuierlich; aus dem vergangenen Kalendertag (`Europe/Berlin`) werden 5–8 relevante Ereignisse ausgewählt, geprüft, mit Quellen versehen und zusammengefasst.

Dieses Dokument definiert **Anforderungen an die Quellen**, nicht den vollständigen REST-API-Vertrag oder die Prompt-Spezifikation. Einzelne Zahlen in diesem Dokument sind als **initiale, vor Inbetriebnahme zu evaluierende Betriebsgrenzen** gekennzeichnet.

**Verbindliche Grundsätze:**

1. Kein ungeprüfter Web-Crawler, keine Suchmaschinen-Scraping-Pipeline, keine spontane Aufnahme neuer Domains durch ein LLM.
2. Journalistische Zuverlässigkeit **und** rechtliche Nutzbarkeit sind **zwei getrennte Freigabeprüfungen**.
3. Öffentlicher Zugriff, RSS-Verfügbarkeit, kostenlose Registrierung oder ein fehlender Login sind **keine** Lizenz zur KI-Verarbeitung oder Weiterveröffentlichung.
4. Nichtkommerzielle Nutzung der eigenen Website bedeutet **nicht automatisch**, dass sämtliche Drittinhalte für dieses Vorhaben genutzt werden dürfen.
5. Quellen bleiben mit jedem veröffentlichten Ereignis und jeder wesentlichen Behauptung nachvollziehbar verknüpft.
6. Nicht ausreichend belegte Inhalte werden ausgeschlossen; bei ungenügender Gesamtabdeckung wird **kein** Tagesbericht veröffentlicht (`fail closed`).
7. Eine Behördenmeldung ist eine **Primärquelle für eine Behördenäußerung oder -entscheidung**, keine automatisch unabhängige Bestätigung ihrer politischen Bewertung.

### 1.1 Anforderungsklassen

- **MUSS:** Ohne Erfüllung ist eine Quelle für den betreffenden Verarbeitungsschritt nicht zugelassen.
- **SOLL:** Qualitätsziel; Abweichung begründen und dokumentieren.
- **KANN:** Spätere Erweiterung.

## 2. Quellentypen und redaktionelle Abdeckung

Registry und Quelleigenschaften sind vorhanden. Aufnahmeprüfung, Rollenlogik und Coverage-Auswertung folgen mit der Ingestion.

| ID | Priorität | Anforderung | Nachweis / Abnahme | Status |
| --- | --- | --- | --- | --- |
| SRC-001 | MUSS | Jede Quelle einem festen Typ zuordnen: `editorial` (journalistische Redaktion) oder `primary` (Dokument, Behörde, Statistik, Originalveröffentlichung). | Typ in Quellenregister; Rollenlogik in der Pipeline. | offen |
| SRC-002 | MUSS | Informationen über Nachrichtenereignisse aus unabhängiger redaktioneller Berichterstattung und/oder geeigneten Primärbelegen gewinnen; Primärquellen nicht als vollwertigen Ersatz für journalistische Einordnung behandeln. | Quelltypen pro Ereignis sichtbar. | offen |
| SRC-003 | MUSS | Alle eingesetzten Quellen stehen auf einer explizit versionierten Whitelist; neue URLs oder Domains werden nicht durch KI automatisch freigegeben. | Ingestion lehnt unbekannte Quell-IDs ab. | offen |
| SRC-004 | MUSS | Für Quellen redaktionelle Trägerschaft, Betreiber, Veröffentlichungsland, Hauptsprache(n), Themen- und Regionalabdeckung dokumentieren. | Vollständiger Quellenstammdatensatz. | offen |
| SRC-005 | SOLL | Schwerpunkt auf Deutschland und Europa; international bedeutsame Ereignisse dürfen nicht unterdrückt werden. | Regionale Coverage-Metriken über 30 Tage. | offen |
| SRC-006 | SOLL | Zielbestand von 6–8 **tatsächlich freigegebenen** und komplementären journalistischen Quellen; zusätzliche geeignete Primärquellen. Das ist ein Ziel, kein Beweis, dass kostenlose Lizenzen verfügbar sind. | Freigegebene Quellenmatrix. | offen |
| SRC-007 | MUSS | Vor öffentlichem Regelbetrieb mindestens 3 redaktionell unabhängige und rechtlich nutzbare Nachrichtenanbieter aus mindestens 2 voneinander unabhängigen Eigentümer-/Redaktionsgruppen sowie relevante DE/EU- und internationale Abdeckung nachweisen; andernfalls Launch blockieren. | Go-live-Gate im Quellenbericht. | offen |
| SRC-008 | MUSS | Originalsprache erhalten; Ausgaben dürfen deutsch sein, aber Übersetzungen dürfen keine neuen Behauptungen erzeugen. | Sprachfelder, Qualitätsstichproben. | offen |
| SRC-009 | SOLL | Politik, Wirtschaft, Gesellschaft, Wissenschaft, Technologie, Gesundheit und Umwelt angemessen abdecken; nicht alles muss jede einzelne Quelle liefern. | Coverage-Matrix je Thema. | offen |
| SRC-010 | SOLL | Keine einzelne Redaktion soll die Auswahl dauerhaft dominieren; Dominanz über eine 30-Tage-Verteilung messen. | Dashboard / Qualitätsbericht. | offen |

> **Geografische Zielgröße:** Für die spätere Auswahl der Tagesmeldungen werden ungefähr 60–70 % Deutschland-/Europa-Bezug angestrebt, **keine starre Quellenquote**. Nachrichtenschwere hat Vorrang vor Quoten.

## 3. Journalistische Qualitätskriterien

Der Quellenaudit dokumentiert Träger, Ausrichtung und Redaktionsregeln. Für die übrigen Kriterien fehlen vollständige Stichproben, Klassifikation oder laufende Beobachtung.

| ID | Priorität | Anforderung | Erwarteter Beleg | Status |
| --- | --- | --- | --- | --- |
| QLT-001 | MUSS | Identifizierbarer Herausgeber, Verantwortliche und nachvollziehbare redaktionelle Organisation. | Impressum / About / Eigentümerangaben. | implementiert |
| QLT-002 | MUSS | Erkennbare Trennung von Nachricht, Kommentar, Werbung und gesponsertem Inhalt. | Publikationsregeln / Stichproben. | offen |
| QLT-003 | MUSS | Transparenter Umgang mit Fehlerkorrekturen, Aktualisierungen und Widerrufen. | Korrekturpolitik oder dokumentiertes Verfahren. | offen |
| QLT-004 | MUSS | Wesentliche Tatsachenbehauptungen sind prinzipiell auf Originalbelege, Reporterrecherche oder überprüfbare Aussagen zurückführbar. | Redaktionelle Stichprobe. | offen |
| QLT-005 | MUSS | Keine offenkundigen Desinformations-, Bot-, Spam- oder reine Content-Farm-Angebote als redaktionelle Kernquelle. | Quellenaudit. | implementiert |
| QLT-006 | MUSS | Meinungsbeiträge, Prognosen und unbestätigte Behauptungen als solche kennzeichnen; für die Faktengrundlage getrennt behandeln. | Beitragstyp im Datenmodell. | offen |
| QLT-007 | SOLL | Regelmäßig und aktuell veröffentlichte Berichterstattung, die den Tagesrhythmus unterstützt. | Feed-Monitoring über Testzeitraum. | offen |
| QLT-008 | SOLL | Unterschiedliche redaktionelle Perspektiven und Länder berücksichtigen, ohne unzuverlässige Positionen künstlich aufzuwerten. | Dokumentierte Auswahlbegründung. | implementiert |
| QLT-009 | MUSS | Offizielle Stellen und Verbände als interessengebundene Primärquellen kennzeichnen; Behauptungen über tatsächliche Wirkungen unabhängig gegenprüfen, soweit möglich. | `source_role`, `claim_type` und Beleglage. | offen |
| QLT-010 | SOLL | Qualitätsprobleme quellenbezogen dokumentieren: häufige Korrekturen, lückenhafte Zeitstempel, unklare Autorschaft, unzuverlässige Verfügbarkeit. | Historie im Quellenregister. | offen |

**Nicht als Qualitätsmaßstab verwenden:** reine Reichweite, Klickzahlen, Häufigkeit derselben Agenturmeldung, politische Übereinstimmung oder LLM-Behauptungen über einen Publisher ohne belegbare Kriterien.

## 4. Rechtliche und lizenzbezogene Anforderungen (hartes Freigabe-Gate)

Die folgende Prüfung ist **pro Quelle und bei Bedarf pro Beitrag** durchzuführen. Sie ersetzt keine juristische Beratung. Bei Zweifel wird die betroffene Nutzungsart gesperrt, bis eine belastbare Rechteklärung vorliegt.

Rechteflags, Artikel-Ausnahmen und Attributionsfelder sind vorhanden. Eine Freigabe pro Nutzungsart und deren Durchsetzung über die gesamte Pipeline stehen aus.

| ID | Priorität | Anforderung | Konsequenz bei Nichterfüllung | Status |
| --- | --- | --- | --- | --- |
| LIC-001 | MUSS | Offizielle Nutzungsbedingungen, API-Bedingungen und Lizenztexte mit URL, Prüftag, Lizenzversion und Nachweis archivieren (soweit Dokumentationskopie erlaubt; sonst URL, Datum und Prüfergebnis). | Keine Freigabe. | offen |
| LIC-002 | MUSS | Für jeden Schritt getrennte Rechte ermitteln: **Abruf**, maschinelle Analyse/Text- und Data-Mining, vorübergehende Speicherung, dauerhafte Speicherung, Übermittlung an externen LLM-Provider, Embeddings, Übersetzung/Bearbeitung, Veröffentlichung und Weitergabe über API. | Nur nachweislich erlaubte Schritte aktivieren. | offen |
| LIC-003 | MUSS | Klären, ob die Rechte für einen **öffentlich zugänglichen**, nichtkommerziellen Dienst gelten; private RSS-Lektüre ist nicht gleich öffentliche Veröffentlichung. | Keine öffentliche Nutzung ohne Freigabe. | offen |
| LIC-004 | MUSS | Nutzungsverbote, Rechtevorbehalte, Robot-/API-Regeln und Zugriffsbeschränkungen respektieren; keine Umgehung von Bezahlschranken oder technisch-rechtlichen Beschränkungen. | Quelle ausschließen/sperren. | offen |
| LIC-005 | MUSS | Lizenzbedingungen auf **Artikelebene** beachten: Agenturtexte, Gastbeiträge, Fotos, eingebettete Medien, Zitate und fremdes Material können abweichende Rechte haben. | Betroffene Inhalte/Ausschnitte ausschließen. | offen |
| LIC-006 | MUSS | Bei Weiterverwendung: geforderte Quellen-, Urheber-, Lizenz- und Änderungsangaben je Datensatz bereitstellen; Pflichtlinks nicht entfernen. | Veröffentlichung blockieren. | offen |
| LIC-007 | MUSS | Keine geschützten Artikeltexte, langen Auszüge, Bilder, Logos oder Schlagzeilen als API-Inhalt redistribuieren, sofern das nicht explizit erlaubt oder anderweitig rechtlich geklärt ist. Eigene Ereignisüberschriften bevorzugen. | Nur erlaubte Metadaten/Links und eigene Texte. | offen |
| LIC-008 | MUSS | Lösch-, Aktualisierungs-, Speicher- und Fristvorgaben technisch erzwingen (inkl. temporärer Caches, Logs und soweit erforderlich Backups). | Keine Speicherung ohne Retention-Regel. | offen |
| LIC-009 | MUSS | Bei CC-Lizenzen konkrete Variante prüfen: `BY` = Namensnennung; `NC` = nichtkommerziell; `SA` = Weitergabe abgeleiteter Inhalte unter kompatiblen gleichen Bedingungen; `ND` = keine öffentliche Weitergabe von Bearbeitungen auf Basis der Lizenz. | Lizenzkonformes Publikationsmodell je Inhalt. | offen |
| LIC-010 | MUSS | Bei `SA`-Material prüfen, ob die erzeugte Darstellung eine **Bearbeitung** darstellt und ob deren Lizenzierung mit der Website/API-Veröffentlichung vereinbar ist. Lizenzpflicht nicht pauschal auf alle unabhängigen Inhalte übertragen. | Bei Unklarheit nicht veröffentlichen. | offen |
| LIC-011 | MUSS | Mit LLM-Provider prüfen, ob Datenverarbeitungsbedingungen, Speicherfristen und etwaige Trainingsnutzung mit Quellenrechten vereinbar sind; **kein** unkontrollierter Versand geschützter Rohtexte. | Externe LLM-Verarbeitung deaktivieren. | offen |
| LIC-012 | MUSS | Nur eigene oder eindeutig freigegebene Artikel-/Quellen-Metadaten langfristig speichern; die bloße Speicherung einer URL darf nicht mit unbegrenztem Kopieren des Artikels verwechselt werden. | Datenfeld-/Inhaltssperre. | offen |
| LIC-013 | MUSS | Redaktionelle Korrekturen, Rücknahmen sowie berechtigte Lösch- oder Unterlassungsbegehren bearbeiten können. | Unpublishing/Korrektur-Workflow. | offen |
| LIC-014 | MUSS | Jede Quelle bei Lizenzänderung oder abgelaufener Freigabe erneut prüfen; bei unklarer neuer Fassung vorsorglich `suspended` setzen. | Automatischer Verarbeitungsstopp. | offen |
| LIC-015 | SOLL | Website, API und eventuelle künftige Einnahmequellen regelmäßig erneut auf Vereinbarkeit mit `NC`-Lizenzbedingungen prüfen. | Re-Review bei geändertem Geschäftsmodell. | offen |
| LIC-016 | MUSS | Datenschutz und Persönlichkeitsrechte unabhängig vom Urheberrecht beachten; sensible oder personenbezogene Angaben nur mit sachlichem Nachrichtenbezug verarbeiten. | Maskieren, minimieren oder ausschließen. | offen |

### 4.1 Explizite Rechte-Matrix je Quelle

Die Freigabe wird **nicht** als einzelnes `license = approved` modelliert. Sie besteht aus getrennten Schaltern, die standardmäßig alle `false` sind:

| Verarbeitungsrecht | Feld | Standard |
| --- | --- | --- |
| Metadaten abrufen | `fetch_metadata` | `false` |
| Inhalts-/Textkörper abrufen | `fetch_full_text` | `false` |
| Text für Event-Analyse verwenden | `analyze_content` | `false` |
| Inhalte temporär persistieren | `store_temporary` | `false` |
| Inhalte langfristig persistieren | `store_long_term` | `false` |
| Inhalte an externen LLM übermitteln | `send_to_external_llm` | `false` |
| Embeddings aus Inhalt erzeugen/speichern | `create_embeddings` | `false` |
| Bearbeiten/Übersetzen | `create_adaptations` | `false` |
| Originaltext/geschützte Titel öffentlich anzeigen | `republish_original_content` | `false` |
| Eigene abgeleitete Zusammenfassungen veröffentlichen | `publish_derivatives` | `false` |
| Bildmaterial zeigen | `republish_media` | `false` |

Rechte gelten mindestens für `(source_id, content_scope, license_version)` und können durch **beitragsspezifische Einschränkungen** übersteuert werden. Die Freigabe jedes Schritts erfolgt nur bei dokumentierter Berechtigung; allgemeine technische Machbarkeit genügt nicht.

### 4.2 Quellenhinweise und Attribution

Bei veröffentlichter Meldung ausgeben können:

- Offizieller Publikationsname und (falls erforderlich) Originalautor.
- Kanonische Artikel-URL (HTTPS).
- Originalveröffentlichungsdatum und ggf. Aktualisierungsdatum.
- Lizenzkennung und Lizenz-URL, wenn erforderlich.
- Hinweise zur Veränderung/Übersetzung, soweit erforderlich.
- Einordnung `editorial` vs. `primary`, bei Bedarf Originalagentur.

Lizenzpflichtige Attribution darf nicht erst in versteckten internen Logs existieren. Die REST-API muss die erforderlichen Felder bereitstellen, damit das spätere Frontend rechtskonform darstellen kann.

## 5. Technische Integrationsanforderungen

Seed, Feed-URLs und DB-Felder sind vorhanden. Ein produktiver Abrufpfad und die Adaptertests fehlen.

| ID | Priorität | Anforderung | Abnahme | Status |
| --- | --- | --- | --- | --- |
| TEC-001 | MUSS | Nur offizielle, dokumentierte RSS/Atom-Feeds oder REST-APIs der freigegebenen Anbieter nutzen; kein allgemeiner Browser-Search und kein ungenehmigtes HTML-Scraping. | Adapter-Allowlist. | offen |
| TEC-002 | MUSS | Pro Quelle ein konfigurierbarer Adapter mit Authentifizierung, Feed-URL(s), Timeout, Abrufintervall und Parser. | Adaptertests mit Fixtures. | offen |
| TEC-003 | MUSS | HTTPS, Zertifikatsprüfung, begrenzte Redirects und URL-/Host-Allowlist; Schutz vor SSRF und internen IP-Zielen. | Security-Tests. | offen |
| TEC-004 | MUSS | HTTP-Fehler differenzieren; Rate-Limits/\`Retry-After\` einhalten; Backoff mit Jitter, Timeout und obere Retry-Grenze. | Integrationstests. | offen |
| TEC-005 | MUSS | Wenn unterstützt, `ETag`/\`If-None-Match\` oder `Last-Modified`/\`If-Modified-Since\` verwenden. | Abrufprotokoll. | offen |
| TEC-006 | MUSS | Abrufe idempotent: doppelte Einträge nicht erneut speichern; stabile IDs bevorzugen, sonst kanonische URL plus Quell-ID. | Mehrfachabruf-Test. | offen |
| TEC-007 | MUSS | Artikelzeitstempel, Updatezeitstempel und Abrufzeit getrennt speichern; UTC intern, Tageszuordnung nach `Europe/Berlin`. | Tests über DST-Wechsel. | offen |
| TEC-008 | MUSS | Zeiträume aufgrund des **Ereignisdatums** interpretieren; das Veröffentlichungsdatum allein ist nicht immer Ereignisdatum. Beide getrennt modellieren. | Beispiele mit Vor- und Nachberichten. | offen |
| TEC-009 | MUSS | Revisions- und Korrektursignale erkennen; bei geändertem Artikel nicht stillschweigend die Historie überschreiben. | Änderungshistorie. | offen |
| TEC-010 | MUSS | Volltexte, HTML, Kommentare, eingebettete URLs und LLM-Inhalte als **untrusted input** behandeln. | Sanitizing/Injection-Tests. | offen |
| TEC-011 | MUSS | Datenfelder einheitlich normalisieren (Sprache, Publisher, Titel, URL, GUID, Datum, Kategorie, Content-Typ, Lizenzstatus). | Normalisierungstests. | offen |
| TEC-012 | MUSS | Originalveröffentlichungsquelle und syndizierende Quelle unterscheiden; Agentur-Übernahmen dürfen nicht als unabhängige Bestätigungen zählen. | Provenienz-Datenmodell. | offen |
| TEC-013 | MUSS | Je Quelle Rate-Limits, Abrufquote, Fehlerquote und letzten erfolgreichen Import erfassen. | Betriebsmetriken. | offen |
| TEC-014 | SOLL | Initial alle 30 Minuten abrufen; je Feed entsprechend Lizenz, Aktualisierungsfrequenz und technischen Limits anpassen. | Feed-Konfiguration. | offen |
| TEC-015 | SOLL | RSS/Atom zuerst; externe APIs nutzen, wenn sie bessere Metadaten, Rechteklärung oder Korrekturhinweise liefern. | Adapter-Entscheidung dokumentiert. | offen |
| TEC-016 | SOLL | Einträge mit fehlendem Datum, ungültiger URL oder widersprüchlichem Ursprung in eine Quarantäne stellen. | Quarantäne-Status. | offen |
| TEC-017 | KANN | Historische Nachimporte mit gesonderter Rechtegrundlage und Quotensteuerung ermöglichen. | Backfill-Job. | offen |

### 5.1 Vorläufige Betriebsparameter

```
source_ingestion:
  default_poll_interval_minutes: 30
  http_timeout_seconds: 15
  max_redirects: 3
  retry_attempts: 3
  rate_limit_behavior: respect_retry_after
  conditional_requests: true
  canonical_urls: true
  default_content_retention: none
  unknown_license_policy: deny
  unknown_domain_policy: deny
  llm_external_transfer_default: deny
```

Diese Werte sind Konfigurationsdefaults und werden pro Quelle durch deren offiziellen Vorgaben überschrieben.

## 6. Datenqualität, Belegführung und Mehrfachbestätigung

Das Schema bildet Artikel, Ereignisse, Claims und Evidenz ab. Erzeugung und Prüfung der Belegkette stehen aus.

| ID | Priorität | Anforderung | Abnahme | Status |
| --- | --- | --- | --- | --- |
| EVD-001 | MUSS | Jede Meldung erhält mindestens eine identifizierbare erlaubte Quelle mit Original-URL. | Kein `Story` ohne `sources`. | offen |
| EVD-002 | MUSS | Jede wesentliche veröffentlichte Tatsachenbehauptung intern auf konkrete Evidenz-/Artikel-IDs zurückführen. | Claim-Evidence-Referenzen. | offen |
| EVD-003 | MUSS | Für kontroverse oder weitreichende Behauptungen grundsätzlich zwei unabhängige Belege anstreben; Ausnahmen für unmittelbar authentisch belegbare Primärfakten dokumentieren. | Belegprüfung. | offen |
| EVD-004 | MUSS | Gleiche Agenturmeldung bei unterschiedlichen Publishern als dieselbe ursprüngliche Evidenzlinie erkennen. | `originating_agency` / `evidence_group_id`. | offen |
| EVD-005 | MUSS | Quellenkonflikte erkennen, dokumentieren und in Ausgaben offen ausweisen oder die Nachricht sperren. | Widerspruchs-Testfälle. | offen |
| EVD-006 | MUSS | Dubletten und fortlaufende Updates zum gleichen Ereignis zusammenführen; Neuigkeiten getrennt markieren. | Event-Clustering-Tests. | offen |
| EVD-007 | MUSS | Behauptungen mit Kennzeichnung `confirmed`, `reported`, `disputed`, `unverified` führen; `unverified` darf nicht als gesicherte Tatsache erscheinen. | Strukturierte Claim-Stati. | offen |
| EVD-008 | MUSS | Vollständige Provenienz der Quelle bis zur veröffentlichten Zusammenfassung: Quelle → Artikel/Datensatz → Ereignis → Claim → Tagesbericht. | Audit-Abfrage möglich. | offen |
| EVD-009 | SOLL | Bei bedeutsamen Zahlen den Bezugszeitraum, Messdefinition und Ursprung der Statistik erhalten. | Stichproben für Wirtschafts-/Gesundheitsdaten. | offen |
| EVD-010 | SOLL | Quellenaktualisierungen während der letzten Stunden vor Tagesabschluss berücksichtigen; keine Annahme, ein RSS-Feed archiviere alle Meldungen. | Ingestion-Monitoring. | offen |

**Wichtige Unterscheidung:** Zwei redaktionell unabhängige Publisher können dieselbe Agenturmeldung verbreiten. Diese Beiträge können nützlich sein, sind aber nicht automatisch **zwei unabhängige Tatsachenbestätigungen**.

## 7. Auswahl- und Abdeckungsanforderungen

Es gibt noch keine Auswahlpipeline und keine ausgewertete Referenzperiode.

| ID | Priorität | Anforderung | Abnahme | Status |
| --- | --- | --- | --- | --- |
| COV-001 | MUSS | Relevante Artikel und Primärdaten für den vergangenen Tag sammeln; Auswahl auf nachgewiesene Ereignisse beschränken. | Bericht verweist nur auf belegte Ereignisse. | offen |
| COV-002 | MUSS | Ereignisse nach Relevanz, Auswirkungen und belegter Neuigkeit priorisieren; nicht nach bloßer Artikelhäufigkeit. | Ranking-Tests. | offen |
| COV-003 | MUSS | Kein künstliches positives/negatives Gegengewicht allein für den Score einfügen. | Auswahlregel dokumentiert. | offen |
| COV-004 | MUSS | Pro veröffentlichtem Tag 5–8 eigenständige, ausreichend belegte Ereignisse; andernfalls nicht veröffentlichen statt aufzufüllen. | Publication Gate. | offen |
| COV-005 | MUSS | Quellenabdeckung überwachen; wenn wesentliche Quellgruppen ausgefallen oder nur Primär-PR-Meldungen verfügbar sind, Report blockieren. | Source-health-/coverage-Gate. | offen |
| COV-006 | SOLL | Schwerpunkt Deutschland/Europa und zusätzlich die wichtigsten internationalen Ereignisse abbilden. | Monatlicher Regionalreport. | offen |
| COV-007 | SOLL | Die Auswahl soll sich nicht nur auf institutionelle Pressemitteilungen stützen. | Anteil eigenständiger redaktioneller Evidenz. | offen |
| COV-008 | SOLL | Für eine bewertbare langfristige Qualität mindestens 30 Tage mit dokumentierter Source-Coverage evaluieren. | Evaluationsbericht. | offen |

**Initialer Vorschlag für das automatische Tages-Publication-Gate** (vor Produktivstart mit Testdaten kalibrieren):

- Mindestens 5 vollständig geprüfte, eigenständige Ereignisse.
- Für jede veröffentlichte wesentliche Behauptung Evidenzzuordnung vorhanden.
- Kein nicht freigegebener Inhaltsverarbeitungsschritt.
- Mindestens 3 rechtlich zulässige, aktuell erreichbare journalistische Quellen als Pool; keine bloße Abhängigkeit von einer einzigen Redaktion/Agentur.
- DE/EU und internationale Abdeckung über den Quellenpool vorhanden; ungewöhnliche Nachrichtenlage kann die konkrete Tagesverteilung ändern.
- Keine ungelösten schwerwiegenden Widersprüche in den ausgewählten Ereignissen.
- Keine Warnung vor einer gravierenden Ingestion-Lücke im betrachteten Tageszeitraum.

Bei Verletzung eines harten Gates: `report_status = blocked`, **keine** automatisch vergebene `3/5`.

## 8. Quellenregister und Datenmodell

### 8.1 `news_sources` (Stammdaten)

| Feld | Beispiel / Bedeutung |
| --- | --- |
| `id` | Stabile UUID |
| `slug` | `example-publication` |
| `name`, `homepage_url` | Offizieller Name, Homepage |
| `source_type` | `editorial` oder `primary` |
| `publisher_group_id` | Mediengruppe/Träger zur Unabhängigkeitsprüfung |
| `origin_country`, `languages` | Länder-/Sprachangaben |
| `regions`, `topics` | Abdeckung |
| `editorial_policy_url` | Redaktionelle Standards |
| `corrections_policy_url` | Korrekturhinweise |
| `status` | `candidate`, `in_review`, `approved`, `suspended`, `rejected` |
| `reviewed_at`, `next_review_at` | Freigabezyklen |
| `notes` | Audit-Ergebnis, Risiken, Einschränkungen |

### 8.2 `source_feeds` (technische Adapter)

`id`, `source_id`, `feed_type` (`rss`, `atom`, `rest`), `feed_url`, `allowed_hosts`, `auth_secret_ref`, `poll_interval_minutes`, `etag`, `last_modified`, `last_success_at`, `rate_limit_policy`, `enabled`.

### 8.3 `source_permissions` (verbindliche Rechte)

`id`, `source_id`, `content_scope`, `license_name`, `license_url`, `terms_url`, `terms_version`, `evidence_url`, `reviewed_at`, `next_review_at`, `retention_hours`, `required_attribution`, `required_license_notice`, `derivatives_license`, alle Rechte-Flags aus Abschnitt 4.1, `approval_reason`, `approved_by`.

### 8.4 `source_items` (verarbeitete Daten)

`id`, `source_id`, `feed_id`, `external_id`, `canonical_url`, `original_url`, `source_title` (nur soweit zulässig), `published_at`, `updated_at`, `fetched_at`, `event_time_estimate`, `language`, `content_type`, `originating_agency`, `evidence_group_id`, `content_rights_id`, `content_expires_at`, `checksum`, `ingestion_status`.

**Keine pauschale `raw_article_text`-Spalte mit unbegrenzter Speicherung.** Wenn Texte rechtlich verarbeitet werden dürfen, gehören sie in einen gesonderten, fristgesteuerten Speicher mit Retention und Zugriffskontrolle.

### 8.5 Belegbeziehungen

- `events`: normalisierte Ereignisse, Datum, Regionen und Themen.
- `event_sources`: Zuordnung von Ereignis ↔ Quellenbeleg.
- `claims`: veröffentlichungsrelevante Tatsachenbehauptungen und deren Verifikationsstatus.
- `claim_evidence`: Zuordnung von Claim ↔ konkreter Evidenz.
- `source_audits`: Prüfergebnisse, Nutzungsrechtsänderungen, Suspensionen.
- `ingestion_runs`: technische Läufe, Fehler, Quoten und Coverage.

### 8.6 Beispiel einer Quellenkonfiguration

```
id: example-source
name: Example Publisher
source_type: editorial
status: candidate
publisher_group_id: example-group
regions: [germany, europe]
languages: [de]
feeds:
  - type: rss
    url: https://example.org/feed.xml
    poll_interval_minutes: 30
license:
  name: unknown
  terms_url: null
  reviewed_at: null
  next_review_at: null
  retention_hours: 0
permissions:
  fetch_metadata: false
  fetch_full_text: false
  analyze_content: false
  store_temporary: false
  store_long_term: false
  send_to_external_llm: false
  create_embeddings: false
  create_adaptations: false
  republish_original_content: false
  publish_derivatives: false
  republish_media: false
```

Dies ist ein **sicherer Default**, kein Produktionsfeed. Eine Quelle darf erst nach konkreter Rechteprüfung in der Konfiguration freigeschaltet werden.

## 9. Quellen-Lifecycle, Audits und Incident-Handling

```
candidate
 |
   v
in_review ---> rejected
 |
   v
approved <--- in_review
 |
   v
suspended ---> in_review
```

Seed und Constraints sperren die Nutzung initial. Review-, Sperr-, Monitoring- und Incident-Prozesse müssen im Betrieb nachweisbar werden.

| ID | Priorität | Anforderung | Status |
| --- | --- | --- | --- |
| OPS-001 | MUSS | Freigabe ist ein dokumentierter manueller Review; LLM darf keine Quelle selbst genehmigen. | offen |
| OPS-002 | MUSS | Bei `suspended`/\`rejected\` keine weitere Ingestion, keine weitere neue LLM-Verarbeitung, keine neue Veröffentlichung aus gesperrten Inhalten. | offen |
| OPS-003 | MUSS | Rechteentzug oder relevante Änderung der Terms führt zur erneuten Prüfung sämtlicher betroffener Schritte, inklusive bereits veröffentlichter Ableitungen. | offen |
| OPS-004 | MUSS | Bei Quellenfehlern Logs mit Quell-ID, Request-ID, Fehlerklasse, Statuscode und Zeitstempel, aber ohne unerlaubte Rohtextspeicherung. | offen |
| OPS-005 | MUSS | Für Quoten- und Feed-Ausfälle Alarmierung; die übrige Pipeline darf keine Vollständigkeit vortäuschen. | offen |
| OPS-006 | MUSS | Vor Freigabe eine technische Smoke-Prüfung, rechtliche Dokumentation und redaktionelle Stichprobe bestehen. | offen |
| OPS-007 | SOLL | Wiederkehrender rechtlicher und redaktioneller Re-Review, initial alle 90 Tage sowie sofort bei bekannten Terms-Änderungen. | offen |
| OPS-008 | SOLL | Monatliche Bewertung von Quellendominanz, Abdeckung, Korrekturen und Feed-Verfügbarkeit. | offen |
| OPS-009 | KANN | Automatischer Hinweis auf geänderte Terms-Seiten; **keine** automatische Neufreigabe daraus ableiten. | offen |

**Spezielle Fälle:**

1. **Feed vorübergehend nicht verfügbar:** Retry, Degraded-Status, Coverage-Gate; keine stillschweigende Ersetzung durch Browser-Suche.
2. **Quelle verbreitet Falschmeldung:** Betroffene Claims/Events markieren, öffentlichen Bericht ggf. korrigieren, Revision erhöhen.
3. **Lizenz wird widerrufen/geändert:** Weitere Verarbeitung sofort stoppen, vorhandene Daten und Veröffentlichungen rechtlich prüfen, gegebenenfalls entfernen.
4. **Artikel wird korrigiert:** Neue Version verknüpfen; Änderungshistorie statt stiller Überschreibung.
5. **Externer LLM-Provider ändert Bedingungen:** Rechtliche Datenübermittlungsfreigabe erneut prüfen; betroffene Quellenverarbeitung bis dahin sperren.

Die verbindliche Startauswahl und die bereits nachgewiesenen redaktionellen Kriterien stehen in [Quellenprüfung](quellenpruefung.md). Die folgende Kandidatenliste dokumentiert den früheren Suchraum.

## 10. Konkrete Kandidaten für die Quellenmatrix

**Warnung:** „Technisch verfügbar“ bedeutet nicht „für Daily Signal genehmigt“. Die folgende Liste ist ein **Prüf-Backlog** mit ausdrücklich begrenzter Aussagekraft. Keine Quelle ist allein durch dieses Dokument für die produktive KI-Pipeline freigegeben.

| Quelle | Rolle | Stärke | Status für Daily Signal | Prüfschritt |
| --- | --- | --- | --- | --- |
| [tagesschau](https://www.tagesschau.de/infoservices/rssfeeds) | Editorial | Deutschland / Welt | **Nicht freigegeben**: aktuelle RSS-Hinweise schränken Veröffentlichung ein; ältere Hinweise untersagen Archivierung. | Individuelle ausdrückliche Erlaubnis für gewünschte Speicherung, KI-Nutzung, Veröffentlichung einholen oder ausschließen. |
| [The Guardian Open Platform](https://www.theguardian.com/open-platform/terms-and-conditions) | Editorial | International | **Nicht freigegeben**: publizierte Terms untersagen unter anderem KI-Analyse/Synthese mit API-Inhalten ohne gesonderte Rechte. | Für kostenloses MVP nicht einplanen. |
| [netzpolitik.org](https://netzpolitik.org/menue/) | Editorial | Digitale Gesellschaft / DE | **Kandidat**: eigene Texte grundsätzlich CC BY-NC-SA 4.0, Ausnahmen möglich. | Artikelbezogene Lizenz, Bearbeitungs-/SA-Folgen, Attribution, API-/Feed-Bedingungen und LLM-Transfer prüfen. |
| [EU-Kommission – Legal Notice](https://digital-strategy.ec.europa.eu/en/pages/legal-notice) | Primary | EU-Politik / Entscheidungen | **Kandidat**: EU-eigene Inhalte meist CC BY 4.0, ausgenommen anders markierte/ fremde Inhalte. | Konkrete Portal-/Artikellizenz und technische API prüfen; nicht als unabhängige Redaktion werten. |
| [Destatis – GENESIS](https://www.destatis.de/DE/Service/OpenData/genesis-api-webservice-oberflaeche.html) | Primary | Statistiken Deutschland | **Kandidat**: API und Datenlizenz Deutschland – Namensnennung 2.0. | API-Abruf mit aktuellem POST-Verfahren testen, Lizenzattribution umsetzen. |
| Deutsche Welle | Editorial | Deutschland / international | **Kandidat, ungeklärt**: Zugangs- und Nutzungsrechte konkret erfragen. | Offizielles Angebot, Terms und schriftliche Freigabe für KI-Pipeline prüfen. |
| Deutschlandfunk | Editorial | Deutschland / international | **Kandidat, ungeklärt**: RSS-Angebote allein reichen nicht zur Freigabe. | Nutzungsrechte und Archivierung schriftlich klären. |
| BBC News | Editorial | International | **Kandidat, ungeklärt**. | Offizielle RSS-/API-Bedingungen, Textrechte und LLM-Verwendung prüfen. |
| Reuters / AP | Editorial / Agentur | International | **Kein kostenloser MVP-Zugang vorausgesetzt**. | Nur bei gesondert geklärter Lizenz in Betracht ziehen. |

**Quellenabhängigkeit:** Wenn eine Redaktion eine fremde Agenturmeldung übernimmt, muss die tatsächliche Urheber-/Lizenzlage des konkreten Beitrags gesondert geprüft werden. Eine offene Grundlizenz des Mediums gilt nicht zwingend für solche Übernahmen.

## 11. Quellenfreigabe – obligatorische Checkliste

Diese Checkliste wird für jede einzelne Quelle ausgefüllt. **Freigabe nur, wenn sämtliche relevanten MUSS-Punkte erfüllt und dokumentiert sind.**

### Redaktionell

- Identität, Herausgeber und Eigentümer-/Trägergruppe bekannt.
- Redaktionelle Standards und Korrekturverfahren geprüft.
- Nachrichten, Meinung und Werbung unterscheidbar.
- Quellen-/Behauptungsqualität durch Stichproben geprüft.
- Quellentyp, Region, Sprache und Themenabdeckung klassifiziert.
- Unabhängigkeit von bereits vorhandenen Quellen beurteilt.

### Rechtlich

- Offizielle Terms und Lizenzversion dokumentiert.
- Rechte für automatisierten Feed-/API-Abruf geklärt.
- Rechte zur Textanalyse / Text- und Data-Mining geklärt.
- Speicherung inkl. Retention/Backup/Logs geklärt.
- Übermittlung an externen LLM-Provider geklärt.
- Bearbeitung, Übersetzung und KI-generierte Ableitungen geklärt.
- Öffentliche Veröffentlichung / API-Weitergabe geklärt.
- Attribution, Lizenzlink und Änderungskennzeichnung definiert.
- Drittmaterial/Agenturtexte und abweichende Artikelrechte berücksichtigt.
- Erforderliche Datenminimierungs- und Datenschutzmaßnahmen definiert.
- Nächster Review-Termin hinterlegt.

### Technisch

- Offizieller Feed/API-Endpunkt dokumentiert.
- Host-Allowlist, HTTPS, Auth-/Secret-Handling geprüft.
- Rate-Limit, Polling, Fehlerbehandlung und Backoff konfiguriert.
- Korrekte Zeitstempel-/Zeitzonenbehandlung getestet.
- Dubletten- und Updateerkennung getestet.
- Artikelprovenienz inklusive Ursprungsagentur verfügbar oder Einschränkung dokumentiert.
- Quarantäne und Monitoring aktiv.
- Rechtlich gesperrte Verarbeitungsschritte technisch ausgeschlossen.

### Veröffentlichung

- Pflichtangaben sind im öffentlichen Datenmodell vorhanden.
- Claim-Evidence-Referenzen können erzeugt werden.
- Unzulässige Rohtext-/Mediendaten werden nicht an die API ausgeliefert.
- Freigabestatus ist `approved`; technische und rechtliche Tests sind grün.

## 12. Go-live-Abnahme für die gesamte Quellenbasis

- Quellenmatrix aller produktiven Feeds vollständig und versioniert.
- Mindestens 3 redaktionell unabhängige **rechtlich nutzbare** Quellen und eine ausreichende DE/EU-/Welt-Abdeckung nachgewiesen; Ziel 6–8 redaktionelle Quellen.
- Primärquellen ergänzen die Nachrichtenlage, ersetzen nicht journalistische Recherchen.
- Keine Pipeline-Nutzung einer nicht freigegebenen Quelle (einschließlich externer LLM-Eingaben).
- Mindestens 30 Testtage oder entsprechend belastbare simulierte/historische Testfälle evaluiert.
- Für alle veröffentlichten Stories Quellen-URLs, erlaubte Attribution und belegte wesentliche Claims vorhanden.
- Korrekturen, Sperrungen und Lizenzablauf sind in Tests nachgewiesen.
- Ausfall mehrerer Quellen führt zu einem gesperrten Report, nicht zu erfundenen Inhalten.
- Rechtliche und technische Dokumentation liegt im Repository und ist vor Deploy prüfbar.

**Nicht bestandenes Go-live-Gate:** keine vollautomatische öffentliche Veröffentlichung. Ein lokaler Prototyp mit synthetischen Daten oder ausdrücklich erlaubten Testinhalten bleibt möglich.

## 13. Empfohlene Repository-Artefakte

```
/docs/sources/
├── SOURCE_REQUIREMENTS.md
├── SOURCE_REGISTER.md
├── LICENSING_POLICY.md
├── EDITORIAL_POLICY.md
├── ATTRIBUTION_GUIDE.md
├── QUALITY_EVALUATION.md
└── reviews/
    └── <source-slug>.md

/config/sources/
├── sources.yaml
└── feeds.yaml

/tests/
├── ingestion/
├── rights/
├── provenance/
└── publication_gates/
```

**Minimaler Review-Record je Quelle:** Reviewer, Prüfdatum, Terms-/Lizenz-URL, Prüfumfang, erlaubte/verbotene Schritte, Retention, Attribution, Drittmaterial-Regelung, technische Adapterdetails, Evidenz für Redaktion/Unabhängigkeit, Rest-Risiken, Freigabeentscheidung und nächster Review.

## 14. Offene Aufgaben mit Priorität

1. **P0:** Mindestens drei unabhängige journalistische Anbieter finden, deren konkrete Nutzungsbedingungen einen öffentlichen, nichtkommerziellen, KI-gestützten Nachrichtenüberblick tatsächlich erlauben; erforderlichenfalls Freigaben anfragen.
2. **P0:** Rechtliche Freigabe für jede beabsichtigte Verarbeitung **einschließlich externem LLM** nachvollziehbar dokumentieren.
3. **P0:** Technisches Quellenschema und Deny-by-Default-Rechteprüfung implementieren.
4. **P0:** Attribution, Artikel-Ausnahmen und Retention pro Quelle operationalisieren.
5. **P1:** 30-Tage-Quellenqualität und thematische Abdeckung messen.
6. **P1:** Agenturabhängigkeit und Event-Evidenzgruppen zuverlässig erkennen.
7. **P1:** Quellen-/Lizenz-Sperrung und Korrekturverfahren durch Integrationstests absichern.
8. **P2:** Weitere Regionen, Fachredaktionen und Primärdaten integrieren.

## 15. Offizielle Referenzen (für den jeweiligen Quellenaudit erneut prüfen)

- [tagesschau – RSS-Nutzung](https://www.tagesschau.de/infoservices/rssfeeds)
- [tagesschau – ältere RSS-Regelung](https://www.tagesschau.de/rssfeed-ts-104.html)
- [The Guardian – Open Platform Terms](https://www.theguardian.com/open-platform/terms-and-conditions)
- [The Guardian – API-Zugangsmodelle](https://open-platform.theguardian.com/access/)
- [netzpolitik.org – Lizenzhinweis](https://netzpolitik.org/menue/)
- [EU-Kommission – Legal Notice](https://digital-strategy.ec.europa.eu/en/pages/legal-notice)
- [Destatis – GENESIS-API und Datenlizenz](https://www.destatis.de/DE/Service/OpenData/genesis-api-webservice-oberflaeche.html)
- [GENESIS – API-Änderungen (POST statt GET seit Juli 2025)](https://genesis.destatis.de/datenbank/online/announcement)
- [Creative Commons BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- [Creative Commons – Lizenzbedingungen und Einschränkungen](https://creativecommons.org/share-your-work/licensing-considerations/version4/)

---

**Kernentscheidung:** Eine Nachrichtenquelle ist für Daily Signal erst dann produktiv verwendbar, wenn **redaktionelle Qualität, technische Stabilität, konkrete Nutzungsrechte und überprüfbare Belegführung** zugleich gegeben sind. Die automatisierte Pipeline darf diese Schranken weder durch LLM-Ausgaben noch durch technische Fallbacks umgehen.
