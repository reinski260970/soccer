# oddswatch

Sportmodelle, Fußball-Quotenwächter und deutsche Berichte. Kalshi ist aus dem
aktiven Betrieb entfernt: keine API-Abfragen, Kontozugriffe, Fills, Marktleiter
oder neuen Snapshots. Historische Journale und Berichte bleiben unverändert.

## Befehle

```bash
pip install -r requirements.txt
python -m oddswatch scan --dry          # Modelle, Fußball-1X2-Preisvergleich und Bericht
python -m oddswatch scan --send         # zusätzlich Journal und Telegram
python -m oddswatch daily --send        # Bilanz und Ausblick
python -m oddswatch quick --send        # API-Football-Quotenwächter für vorhandene Ziele
python -m oddswatch guard --send        # derselbe Quotenwächter
python -m oddswatch football-mongo      # separate Fußball-Mongo-Verbindung und Schema prüfen
python -m oddswatch news --send
python -m oddswatch backtest
python -m oddswatch tune
python -m oddswatch research
python -m oddswatch summary
python -m oddswatch settle              # Bilanz; offene Einträge melden, keine Ergebnisabrufe
python -m oddswatch place --ref EVENT --odds 2.1 --stake 1 --bookmaker bet365
```

## Quellen und Grenzen

- Fußball: football-data, ClubElo, eloratings und ESPN für Modelle/Spielpläne.
  API-Football liefert Bet365 und Betfair **Sportsbook**, Pinnacle als faire
  Referenz. Fehlt Pinnacle, bleibt eine vorhandene ESPN/DraftKings-Referenz.
  Orbit ist noch nicht angebunden. Neue Scan-Kandidaten derzeit nur 1X2.
- Bestehende Validierungsregeln und Fußball-Freigabesperren bleiben erhalten.
  Ohne unabhängige Referenz gibt es keine Freigabe.
- NFL, NHL und NBA: bestehende Modell-/Spielplanquellen bleiben; aktuell kein
  handelbarer Buchmacherpreis, daher keine neuen Valuebet-Freigaben.
- ICEHL, Liiga und SHL: eigene Spielplanquellen bleiben. DEL/CH/KHL benötigen eine
  Ersatzquelle; Berichte kennzeichnen diese Lücke statt „keine Spiele“ zu behaupten.
- Automatische Abrechnung und Closing-Snapshots des entfernten Anbieters entfallen.
  Offene Alteinträge bleiben offen und müssen anhand verifizierter Ergebnisse
  separat abgerechnet werden. Sie werden nicht automatisch als Verlust/VOID markiert
  und nicht als aktuelle Tipps oder News-Ziele weiterverwendet.

## Workflows und Secrets

`quick-scan.yml` enthält zwei unabhängige Jobs: Quotenwächter und Fußball-Mongo.
Cron ist alle 15 Minuten konfiguriert; GitHub kann Läufe verzögern oder auslassen.
`daily-report.yml` erzeugt den Tagesbericht mit mehreren morgendlichen Startfenstern.

| Name | Verwendung |
|---|---|
| `APIKEY` (Secret) | API-Football in Schnellscan und Tagesbericht |
| `MONGO` (Secret) | ausschließlich Fußball-Mongo |
| `MONGO_DB` (Repository-Variable, optional) | explizite Fußball-Datenbank |
| `MONGODB_URI` (Secret) | bestehende Tennis-Anbindung |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Versand |

Fehlender API-Key, Abruffehler und fehlgeschlagener Versand führen beim Wächter
zum Fehlerstatus. Kein neuer Alert ist dagegen kein Fehler. Die Journal-Sicherung
läuft auch nach Fehlern, damit bereits bestätigte Nachrichten dedupliziert bleiben.

`football-mongo` verwendet nur Leseoperationen. Auswahl: `MONGO_DB`, Datenbank im
Connection-String, sonst genau eine zugängliche Datenbank mit football/soccer im
Namen. Bei Mehrdeutigkeit oder fehlenden Rechten schlägt der Job fehl. Tennis- und
Systemdatenbanken sind ausgeschlossen. Pro Collection werden höchstens zehn
Dokumente gelesen; ausgegeben werden nur Feldnamen und Typen, keine Dokumentwerte,
URIs oder Fehlerdetails. Dies ist eine Schema-Diagnose, noch keine Fußball-Prognose
oder Valuebet-Auswertung. Nach dem ersten Lauf muss das tatsächliche Schema zugeordnet
werden. Mongo-Zugang und Atlas-Netzfreigabe müssen für den Runner funktionieren.

## News-Agent

`news.py` prüft die Spiele mit Freigabe oder Watchlist-Eintrag (`data/journal/watchlist.json`,
nach jedem Scan aktualisiert, plus offene Freigaben aus dem Journal) gegen Sportseiten:

| Liga | Quellen |
|---|---|
| NFL / NBA | ESPN, CBS Sports, RotoWire |
| NHL | ESPN, NHL.com, RotoWire |
| Bundesliga / 2. Bundesliga | ESPN, kicker (+ Sportschau für die 1. Liga) |
| Österreich | ORF, derStandard, abseits.at, Austrian Soccer Board (Forum) |
| UEFA (Nations League, CL, EL, ECL) | ESPN, kicker (Nationalmannschaft, CL, EL) |

Materiell sind Ausfall, Sperre, Trainerwechsel, fraglich, Verletzung, Rückkehr/Startelf
und Schonung; QB-Themen gelten immer als schwer. Das Team muss Hauptthema sein (Titel
bzw. einzige ESPN-Teamkategorie), Sammelartikel zählen nicht. Bestätigt ist eine
Meldung, wenn eine zweite Redaktion dieselbe Person/dasselbe Team meldet; Forumsbeiträge
gelten als Hinweis und bestätigen nie. Der Agent warnt nur, der CEO entscheidet.
Gemeldete Artikel stehen in `news_seen.txt` (keine Wiederholung), alle in `news.csv`.

## Telegram ohne Make

Die Umgebungsvariablen `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` setzen, dann
`python -m oddswatch scan --send` oder `python -m oddswatch send <datei>`.
Als gesendet gilt eine Nachricht nur, wenn Telegram `ok=true` und eine `message_id` liefert.

## Tennis (MongoDB Atlas, nur lesend)

`python -m oddswatch tennis` liest aus der Datenbank `tennis_db` des Tennis-Runners
(`sources/tennis_atlas.py`): offene, freigegebene Valuebets ab heute aus
`valuebets_active` und die Bilanz aus `valuebets_history` (Tipps, Ergebnis in EH, ROI,
Median-CLV). Bericht: `reports/<datum>-tennis.md`. Mit `--send` gehen nur neue Tipps
bzw. neue Quoten an Telegram (Zustand in `data/journal/tennis_alerts.json`), `--all`
sendet alle offenen.

Die Tipps kommen aus dem ML-Modell des Runners (Quoten von tennisexplorer) und werden
von oddswatch nie als PLAY freigegeben: KANDIDAT nur bei belegtem Vorteil
(≥ 200 abgerechnete Tipps, ROI > 0, Median-CLV > 0), sonst INFO.
Stand 29.09.2026: 319 Tipps, −5,9 EH bei 196 EH Einsatz (ROI ≈ −3 %) → INFO.

Verbindung: `MONGODB_URI` (Connection-String eines Datenbankbenutzers mit Rolle
`read` auf `tennis_db`, in Atlas unter *Database Access* anlegen; die IP bzw. GitHub-
Runner unter *Network Access* freigeben), optional `MONGODB_DB` (Standard `tennis_db`).
Ohne `MONGODB_URI` meldet der Bericht das und bricht nichts anderes ab.

## Modellforschung

`python -m oddswatch research` vergleicht Modellvarianten über 13 Ligen mit Tuning- und
Holdout-Saisons: sagt die Abweichung Modell − Eröffnungsquote die Linienbewegung bis zum
Closing voraus (CLV)? Stand 29.09.2026: Schuss-xG-Varianten zeigen ein echtes, aber
kleines Signal (Steigung ≈ 0,03), die Tipps nach Abweichung haben dennoch CLV −7 bis
−10 % (Holdout) – kein Modell ist besser als der Markt, daher reiner Preisvergleich.
