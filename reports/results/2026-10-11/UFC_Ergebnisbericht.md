# UFC-AI: Ergebnisse und konservative Kelly-Auswertung

Stand: 11. Oktober 2026. Alle Beträge sind simulierte Geldeinheiten bei **10.000 Startkapital pro Auswertungszeitraum**. Das Archiv bezeichnet seine ursprünglichen Einsätze als USD. Es wurde keine Währungsumrechnung vorgenommen. Bei gleicher Bankrollhöhe gelten die relativen Ergebnisse ebenso für ein Euro-Szenario.

## Die angefragten Zeiträume

| Zeitraum | Richtige Picks / entschiedene Kämpfe | Trefferquote | Belegte Kelly-Wetten | Einsatz | Gewinn/Verlust im belegten Teil-Szenario | Rendite aufs Startkapital | Fehlende potenzielle Wettquoten |
|---|---:|---:|---:|---:|---:|---:|---:|
| Letzte 3 Karten: 26.09., 03.10., 10.10. | 26 / 37 | 70,27 % | 1 | 300,00 | **−300,00** | −3,00 % | 1 |
| Dieses Jahr: 01.01.–11.10.2026 | 272 / 434 | 62,67 % | 8 | 2.344,61 | **−188,13** | −1,88 % | 58 |
| Seit Trainingsende: nach 29.08.2026 | 46 / 74 | 62,16 % | 5 | 1.513,07 | **+150,36** | +1,50 % | 1 |

**Diese drei Geldsummen sind keine vollständigen historischen Gewinne/Verluste.** Sie zeigen das Szenario, in dem ausschließlich die belegten Quoten verwendet und die Datenlücken ausgelassen werden. Eine fehlende Quote kann sowohl eine zusätzliche gewonnene als auch eine verlorene Wette verbergen. Auch spätere Einsätze würden sich dadurch ändern. Die Beträge sind deshalb weder Untergrenzen noch Obergrenzen.

Die jüngsten drei Karten enthalten zwei nachträglich rekonstruierte Modelltests und eine gespeicherte Vorab-Prognose. Die Jahresauswertung kombiniert archivierte jährliche Walk-forward-Prognosen mit dem später eingefrorenen Produktionsmodell. Sie ist kein durchgehender Live-Track-Record eines einzigen Modellstands.

## Die letzten Veranstaltungen einzeln

Die folgenden Einsätze und Gewinne verwenden eine ab 05.09. fortgeschriebene Bankroll mit ursprünglich 10.000. Deshalb beträgt die Wette vom 03.10. hier 313,93; bei einem eigenständigen Neustart für die letzten drei Karten wären es 300,00.

| Datum / Karte | Richtige Picks | Kelly-Wetten | Einsatz | Gewinn/Verlust | Herkunft / Abdeckung |
|---|---:|---:|---:|---:|---|
| 05.09. – Hooker vs Parnasse | 6 / 14 | 0 | 0,00 | 0,00 | Gespeicherte Beta-Picks; vollständig innerhalb dieser Karte |
| 12.09. – Noche UFC, Silva vs Delgado | 6 / 11 | 2 | 600,00 | −14,29 | Gespeicherte Beta-Picks; ein abgesagter Kampf ohne Gewinn/Verlust |
| 19.09. – UFC 331, Van vs Pantoja 2 | 8 / 12 | 2 | 599,14 | +478,58 | Gespeicherte Beta-Picks; ein abgesagter Kampf ohne Gewinn/Verlust |
| 26.09. – Rosas Jr. vs Barcelos | 8 / 12 | 0 belegt | 0,00 belegt | 0,00 belegt; **unvollständig** | Nachträglich rekonstruiert; Quote für Alatengheili–John Castaneda fehlt |
| 03.10. – UFC 332, Silva vs Wang | 10 / 14 | 1 | 313,93 | −313,93 | Nachträglich rekonstruiert; Wette auf Mick Parkin verloren |
| 10.10. – Allen vs Duncan | **8 / 11** | **0** | **0,00** | **0,00** | Modell und Quoten am 10.10. um 18:29:57 UTC gespeichert, vor dem Event |

Die Draw-Paarung Melissa Gatto–Ernesta Kareckaite vom 10.10. wurde anhand der [offiziellen UFC-Scorecards](https://jp.ufc.com/news/ufc-fight-night-allen-vs-duncan-official-scorecards) als Unentschieden bestätigt. Moneyline-Wetten werden hier mit Einsatzrückzahlung behandelt; der Kampf zählt nicht zur Trefferquote. ESPN markierte beide Kämpferinnen ohne Sieger. Dieses Ergebnis wurde deshalb ausdrücklich dokumentiert und nicht automatisch als Niederlage gewertet.

Zum Vergleich: 100 auf jeden quotierten Modell-Pick des 10.10. hätte **+367,56** ergeben, einschließlich der Picks mit wenig UFC-Daten und mit Rückzahlung beim Draw. Diese Vergleichsrechnung entspricht nicht der gefilterten Kelly-Strategie.

## Nur die tatsächlich gespeicherten Vorab-Picks

Die Karten vom 05.09., 12.09., 19.09. und 10.10. sind als Vorab-Picks dokumentiert. Zusammen: **4 zulässige Wetten, 3 gewonnen**, Einsatz **1.199,14**, Gewinn **+464,29** bei fortgeschriebener Bankroll. Rendite aufs eingesetzte Kapital: **38,72 %**, aufs Startkapital: **4,64 %**.

Die frühere Zahl **+464,98** bleibt korrekt für die alternative Rechnung mit **festen 10.000 vor jeder Karte**, also jeweils 300 pro zulässiger Wette. Mit dieser festen Basis ergeben sich für die drei angefragten Teil-Szenarien −300,00 / −169,54 / +164,98. Beide Varianten stehen getrennt in den CSV-Dateien.

Dieser Vorab-Nachweis deckt vier Karten ab und ersetzt keinen vollständigen Nachweis aller Karten seit Trainingsende. Vier Wetten reichen auch nicht, um dauerhaft positive Ergebnisse nachzuweisen.

## Festgelegte Wettregel

- Beide Kämpfer haben vor dem Kampf mindestens **5 dokumentierte UFC-Kämpfe**. Debüts und geringe UFC-Historie werden ausgeschlossen.
- Modell-Wahrscheinlichkeit für den Pick mindestens **60 %**.
- Modell-EV mindestens **+10 %**, berechnet als `Wahrscheinlichkeit × Dezimalquote − 1`.
- **Viertel-Kelly**: `0,25 × EV / (Dezimalquote − 1)`.
- Höchstens **3 % der Bankroll pro Kampf**; höchstens **12,5 % pro Karte**, bei Bedarf proportionale Kürzung.
- Alle Einsätze einer Karte beziehen sich auf dieselbe Bankroll vor der Karte. Erst nach der Karte wird ihr gesamtes Ergebnis verbucht.
- Ohne belegte Quote oder ausreichende UFC-Historie wird keine belegte Wette angesetzt. Fehlende Quoten geeigneter Picks bleiben als Lücken sichtbar.

Das ist die bestehende konservative Filterregel, keine nachträglich optimierte Auswahl der Gewinner. **Kelly ist nicht risikofrei und hier nicht als mathematisch „sicherste“ Strategie nachgewiesen.** Die UFC-Anzahl ist ein Datenfilter, kein Beweis für kalibrierte Modellwahrscheinlichkeiten. Steuern, Gebühren, Limits, Slippage und abweichende Buchmacher-Abrechnungsregeln sind nicht enthalten.

## Modelle, Quoten und Datenlücken

Der aktuelle eingefrorene 42-Feature-Mix verwendet 55 % CatBoost und 45 % logistische Regression. Sein Trainingsdaten-Ende ist **29.08.2026**. Für den 26.09. und 03.10. wurden nur Kampfresultate und Fighter-Historien **vor dem jeweiligen Event** verwendet; auch der Elo-Replay wurde entsprechend gekürzt. Es wurde nicht nachtrainiert. Die Wahrscheinlichkeiten dieser beiden Karten wurden dennoch erst nach den Ergebnissen rekonstruiert und sind entsprechend gekennzeichnet.

Die Rekonstruktionen verwenden ausschließlich ESPN-Quoten aus dem ausdrücklich bezeichneten Feld `close`, vom selben Anbieter und über Kämpfer-IDs zugeordnet. Die Quoten wurden nach dem Event abgerufen; es gibt dafür keinen eigenen gespeicherten Vorab-Zeitstempel. Es wird daher weder Vorab-Verfügbarkeit noch tatsächlich ausführbare historische Wettausführung behauptet. Für den 03.10. fehlt zusätzlich die Quote von Anthony Romero–Marcus McGhee; wegen zu geringer UFC-Historie beeinflusst dies die gefilterte Strategie nicht.

Für Januar bis August liegen **360 archivierte Walk-forward-Prognosen über 29 Karten** vor. Laut dem zugehörigen Code wurde das 2026-Modell ausschließlich auf Jahren **vor 2026** trainiert; das heutige, auch auf 2026 trainierte Produktionsmodell wurde dafür nicht rückwirkend verwendet. Das Quotenarchiv deckt jedoch nur **115 Kämpfe bis 28.03.** ab. Für April bis August fehlen 245 Kampfquoten, darunter **57 Picks**, die bereits den Historien- und Wahrscheinlichkeitsfilter erfüllen. Auch erneute ESPN-Abfragen lieferten dafür keine expliziten archivierten Schlussquoten. Diese Märkte wurden nicht erfunden und nicht als erwiesene Null-Ergebnisse behandelt.

Zusammen mit Alatengheili–John Castaneda ergeben sich **58 unbekannte mögliche Wetten im Jahreszeitraum**. Erst mit diesen Quoten lässt sich entscheiden, welche davon den EV-Filter erfüllen, und eine vollständige Geldsumme berechnen.

## Veröffentlichtes Ergebnis-Paket

Dieser GitHub-Upload enthält den Bericht und aggregierte Karten- und Zeitraum-Ergebnisse. Einzelne Modellwahrscheinlichkeiten, Kampf-Ledger und Rohbelege sind nicht Teil dieses Uploads. Das zuvor separat bereitgestellte vollständige Ergebnis-Paket enthält diese Nachrechnungsdaten.

Die Auswertung wurde gegen die archivierte September-Abrechnung, die Event-Limits und die Bankroll-Arithmetik geprüft. Sie betrifft die vorhandenen 42-Feature-Production-v1/Beta-Artefakte und wertet nicht die 46-Feature-Sherdog-Production-v2 des Repository-README aus.
