# Scoring-Methodik

Die Scoring-Methodik ist versioniert und wird über `GET /v1/methodology`
ausgeliefert. Die maßgeblichen Werte stehen in
[config/methodology.yaml](../config/methodology.yaml); die Anwendung lädt und
validiert sie beim Start **fail-closed** (`application/methodology.py`).

- Version: `1.0.0`
- Zeitzone: `Europe/Berlin`
- Score-Skala: `5`

## Formel

Der Tagesrohwert ist das **mit dem Quadrat des Impact gewichtete Mittel** der
Story-Richtungswerte:

```text
raw = Σ (direction_value_i * impact_i²) / Σ (impact_i²)
```

- Berücksichtigt werden ausschließlich die Richtungen `negative`, `neutral` und
  `positive`. Deren `direction_value` ist `-2/-1`, `0` bzw. `1/2`.
- **`mixed` und `unknown` werden ausgeschlossen**: Sie tragen keinen
  Richtungswert (`direction_value = NULL`) und gehen nicht in Zähler oder Nenner
  ein.
- Die Gewichtung mit `impact²` verstärkt die Wirkung wichtiger Stories
  überproportional. `relevance_weights.impact` ist auf `100` gesetzt.
- Gibt es keine bewertbare Story, kann kein Tages-Score gebildet werden
  (`NoScorableStoriesError`); es wird kein Ersatz-Score vergeben.

## Schwellen und Score-Werte

Der Rohwert liegt in `[-2, 2]` und wird über vier Grenzen auf die Werte 1–5
abgebildet (`score_thresholds: [-1.1, -0.3, 0.3, 1.1]`):

| Rohwert `raw` | Score `value` | Label |
|---|---|---|
| `raw < -1.1` | 1 | `very_negative` |
| `-1.1 ≤ raw < -0.3` | 2 | `negative` |
| `-0.3 ≤ raw ≤ 0.3` | 3 | `mixed` |
| `0.3 < raw ≤ 1.1` | 4 | `positive` |
| `raw > 1.1` | 5 | `very_positive` |

Die Grenzen sind inklusiv um das mittlere Band `[-0.3, 0.3]` gelegt; links und
rechts schließen die Intervalle die jeweilige Grenze mit ein.

## Farben

Jedes Label hat eine feste Farbe (`score_colors`), die die API unverändert
ausliefert:

| Label | Farbe |
|---|---|
| `very_negative` | `#CF6666` |
| `negative` | `#DE9A57` |
| `mixed` | `#B8AC69` |
| `positive` | `#85B78A` |
| `very_positive` | `#43A779` |

## Confidence

`confidence` beschreibt, wie belastbar der Tages-Score ist:

- **`high`** und **`medium`** sind veröffentlichungsfähig.
- **`limited`** existiert im Schema, ist aber **nicht** veröffentlichungsfähig.

## Publikationsschwelle

Ein Bericht wird nur veröffentlicht, wenn **alle** folgenden Bedingungen
erfüllt sind:

1. Confidence ist `high` oder `medium`.
2. Die Qualitätsprüfung ist abgeschlossen (5–8 Stories, unterstützte Claims,
   geprüfte Rechte, Quellenunabhängigkeit, Schwellen-Konsistenz).
3. Der Score ist vollständig: `value`, `rawValue`, `label`, `confidence` und
   `explanation`.

Diese Regeln spiegeln sich in den SQL-Constraints `published_report_complete`
und `current_report_is_published` und werden zusätzlich im (noch nicht
implementierten) Publikationsworkflow durchgesetzt. Nur `status='published' AND
is_current=true` ist öffentlich sichtbar; unveröffentlichte Tage erhalten nie
einen Ersatz-Score.

## Beispiel

Fünf Stories mit Richtungswerten `-2, 0, +2, -1, +1` und Impacts `1, 2, 1, 1, 1`:

```text
raw = (-2·1 + 0·4 + 2·1 + (-1)·1 + 1·1) / (1 + 4 + 1 + 1 + 1) = 0 / 8 = 0
```

`raw = 0` liegt im Band `[-0.3, 0.3]`, also Score **3**, Label **`mixed`**.
Dieses Beispiel entspricht dem veröffentlichten Beispiel in
[contracts/examples/daily-report.json](../contracts/examples/daily-report.json).
