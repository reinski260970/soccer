# oddswatch

Selbstständiger Scan, unabhängige Bewertung und Preisvergleich für Fußball
(Bundesliga, 2. Bundesliga, österreichische Bundesliga, UEFA), NFL, NHL und NBA,
mit getrennten Ledgern, CLV-Nachkontrolle und deutschen CEO- und Telegram-Texten.

## Befehle

```bash
python -m oddswatch scan                 # Scan (7 Tage Freigabe, 14 Tage Watchlist) + Journal + Bericht
python -m oddswatch scan --dry           # nur Bericht, nichts ins Journal
python -m oddswatch scan --send          # zusätzlich Telegram-Versand (Bot API)
python -m oddswatch daily --send         # Tagesbericht: Auswertung, Profit-Status, Ausblick (nur bei Neuigkeiten)
python -m oddswatch news --send          # News-Agent: Warnungen zu Freigaben/Watchlist
python -m oddswatch closing              # Kalshi-Preise offener Tipps sichern (kurz vor Anstoß = Closing Line)
python -m oddswatch verify               # offene Tipps gegen Live-Preis prüfen (mit Rechenweg und Links)
python -m oddswatch backtest             # Modell gegen Markt (Walk-forward, CLV) -> data/validation.json
python -m oddswatch quick --send         # Schnellscan Kalshi vs. DraftKings (für den 15-Minuten-Takt)
python -m oddswatch guard --send         # Quotenwächter: CEO-Tipps gegen Pinnacle/Bet365/Betfair
python -m oddswatch tennis --send        # Tennis-Valuebets aus MongoDB Atlas (tennis_db), nur neue Tipps
python -m oddswatch settle               # Kalshi-Ergebnisse abrufen, abrechnen, CLV
python -m oddswatch place --ref KXNFLGAME-26OCT04DETCAR-CAR --odds 2.66 --stake 0.75
python -m oddswatch send reports/<datum>-telegram.txt
python -m oddswatch summary
python -m oddswatch kalshi-check         # Kalshi-Key prüfen (nur lesend: Kontostand)
python -m oddswatch import-fills         # deine Kalshi-Trades -> data/journal/placed.csv
python -m pytest -q
```

## Ablauf

1. **Daten**: football-data.co.uk (Ergebnisse, echte xG ab 2026/27, bet365-Closing
   für AT), ESPN (Spielpläne, Ergebnisse, NFL-/NBA-Verletzungen, NBA-Leistungsträger
   nach PPG, DraftKings-Referenzlinie),
   NHL-API (Ergebnisse, 5v5-Tore, PP/PK), Kalshi-API (Preise, Orderbuch-Tiefe, Ergebnisse),
   eloratings.net (Elo der Nationalteams, Länderspiele mit Elo vor dem Spiel),
   ClubElo (Elo der Vereine, aus den UEFA-Länderseiten, da die CSV-API HTTP 502 liefert),
   hockeyarchives.info (europäisches Eishockey, Ergebnisse mit Dritteln, Vorsaison und
   laufende Saison), Liiga-API, SHL-API, ICEHL-Datenfeed (Spielplan + Ergebnisse).
2. **Modelle**: Fußball und Eishockey mit Poisson (Dixon-Coles, Zeitverfall, im Fußball
   Tore und xG je 50 %), NFL und NBA mit Punkte-Rating (Offense/Defense, Heimvorteil,
   σ aus Residuen). NBA zu Saisonbeginn aus der Vorsaison (als Schätzung markiert).
   **UEFA** (`models/elo.py`): Elo → Torerwartung `log λ = a ± b·(ΔElo + Heim)/400` →
   Dixon-Coles-1X2. Nations League: a, b per Poisson-ML auf ~5.000 Länderspielen der
   letzten fünf Jahre kalibriert (Heimvorteil 100 Elo, Remisquote 22,7 % vs. 23,2 % real).
   Champions/Europa/Conference League: ClubElo mit der Steigung b aus dem
   Länderspielmodell, Heimvorteil 65 Elo und 1,35 Tore je Team angenommen (Schätzung),
   dazu eine **xG-Korrektur**: 50 % von (xG − xGA) − (Tore − Gegentore) je Spiel ×
   ≈ 216 Elo/Tor × n/(n+10), aus den football-data-Ligen mit xG (E0, SP1, I1, F1, D1,
   N1, P1, B1, T1, SC0, G1). Im Bericht stehen je Team xG, xGA und Tore:Gegentore je
   Spiel; in Bundesliga und 2. BL ebenso (dort Tore und xG je 50 % im Poisson-Fit).
   Vereinsnamen werden streng abgeglichen (Alias, gleicher Name oder Token-Teilmenge,
   nur eindeutig); ohne Treffer wird das Spiel nicht bewertet.
   **Eishockey Europa** (`scan_hockey_eu`): DEL, National League (CH), SHL, Liiga und KHL
   über die Kalshi-Serien (Spielplan + Preis; Titel „Gast vs Heim“, Anspielzeit aus dem
   Ticker in US-Ostküstenzeit). Poisson auf 60-Minuten-Tore (Vorsaison + laufende Saison,
   Halbwertszeit 240 Tage, Ridge 8), Verlängerung/Penalty wie NHL geschätzt verteilt.
   ICE Hockey League: faire Quoten aus dem ICEHL-Feed, ohne Kalshi-Serie nicht handelbar;
   Extraliga CZ/SK, Norwegen, Dänemark ebenso ohne Preis.
   **Belastung** (NBA/NFL/NHL, `models/fatigue.py`, Spielorte in `venues.py`): je Team
   Ruhetage (Back-to-back bzw. kurze Woche/Bye), Anreise in km und Stunden, Zeitzonen-
   Abstand zur Heimat, Höhe ≥ 1000 m, Klimazonenwechsel und in der NFL Kälte im Freien.
   Die Effekte werden per Ridge-Regression auf die Modellresiduen der Vorsaison
   geschätzt (nicht angenommen) und als Margenkorrektur eingerechnet.
3. **Fair – nur besser als der Markt**: Referenz ist der de-vigged DraftKings-Kurs
   (über ESPN), unabhängig vom Kalshi-Preis. `p_final = w·p_model + (1−w)·p_markt`,
   wobei `w > 0` nur gilt, wenn das Modell für Liga und Marktart im Walk-forward-Backtest
   besser war als der Markt (`python -m oddswatch backtest` → `data/validation.json`:
   LogLoss-bestes w > 0, ≥ 200 Tipps, positiver CLV gegen die Pinnacle-Closing-Line).
   Stand 29.09.2026: in keiner Liga/Marktart erfüllt (Bundesliga 1X2 CLV −7,6 %,
   Über/Unter −4,1 %, 2. BL 1X2 −4,5 %) → `w = 0`, reiner Preisvergleich; das Modell
   steht nur zur Information im Bericht. Ohne DraftKings-Linie keine Freigabe
   (NFL/NHL/NBA/UEFA/Eishockey ohne historische Quoten gelten als nicht validiert).
4. **Preis**: Kalshi-Ask inkl. Taker-Gebühr (Order ≈ 100 Kontrakte).
   Orbit und bet365 sind hier nicht abrufbar und werden nie ungeprüft verwendet.
   **Über/Unter & Handicap** (`lines.py`): Kalshi-Linienleiter gegen die DraftKings-Linie,
   nur exakt gleiche Linie (Total: JA = Über, NEIN = Unter; Handicap: JA = Favorit −x,
   NEIN = Außenseiter +x) für NFL, NHL, NBA, Bundesliga, 2. BL, UCL, UEL, UECL, Nations
   League. BTTS: keine DraftKings-Referenz über ESPN, nicht bewertet.
5. **Freigabe (PLAY)**: wenn der Kalshi-Preis inkl. Gebühr die spielbare Mindestquote
   (1,03 / p_final, also EV ≥ 3 % gegen den fairen Marktpreis) erreicht, je Event einer.
   WATCH bei Informationsvorbehalt (News, z. B. QB fehlt), dünnem Kalshi-Orderbuch
   (Spread > 10 ¢) oder fehlender DraftKings-Referenz.

   Einsatz: ¼-Kelly mit Schätzungsabschlag, mindestens 0,25 und maximal 2 EH.
6. **Journal** (`data/journal/`): `forecasts.csv` (alle Prognosen),
   `valuebets.csv` (freigegebene Tipps), `placed.csv` (tatsächlich gespielt).
   Kalshi-Snapshots (`data/snapshots/`) liefern die Closing Line für den CLV.

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

## Kalshi-Konto (nur lesend)

Die Variablen `KALSHI_API_KEY_ID` und `KALSHI_PRIVATE_KEY` (PEM-Text, auch einzeilig
mit `\n`) oder `KALSHI_PRIVATE_KEY_PATH` setzen. `import-fills` übernimmt Käufe
dedupliziert nach `placed.csv`: Quote inkl. Gebühr, Einsatz in EH (Standard 1 EH = 10 $,
änderbar über `ODDSWATCH_EH_USD` oder `--eh-usd`) und Verweis auf die zugehörige
Valuebet-Freigabe. Das Modul sendet nur GET-Anfragen und platziert keine Orders.

Abhängigkeiten: `pip install -r requirements.txt`

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
Im Schnellscan-Workflow läuft `tennis --send` nach dem Kalshi-Scan (Secret `MONGODB_URI`).

## Schnellscan (15-Minuten-Takt)

`python -m oddswatch quick --send` vergleicht ohne Modell-Fit (≈ 1 Minute) alle Spiele
der nächsten 7 Tage mit DraftKings-Linie (ESPN) und Kalshi-Orderbuch: Sieger, Über/Unter
und Handicap auf identischer Linie; NFL, NHL, NBA, Bundesliga, 2. BL, UCL, UEL, UECL,
Nations League, Premier League, La Liga, Serie A. Freigabe bei Kalshi inkl. Gebühr ≥ 3 %
über dem de-vigged DraftKings-Kurs. Neue Tipps: Journal + Telegram (je Tipp und
Preisstufe einmal, Zustand in `data/journal/quick_alerts.json`). Jeder Lauf sichert die
Kalshi-Preise offener Tipps (Closing Line) und rechnet beendete Tipps ab.

Zeitsteuerung: `.github/workflows/quick-scan.yml` (cron alle 15 Minuten). Geplante
Workflows laufen nur vom Standard-Branch – aktiv, sobald die Datei auf `main` liegt und
die Repository-Secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` und `APIKEY`
(API-Football, für den Quotenwächter) gesetzt sind.

## Quotenwächter (Pinnacle, Bet365, Betfair)

`python -m oddswatch guard --send` beobachtet alles, was der CEO ausgibt – Freigaben und
Watchlist (`data/journal/watchlist.json`) plus offene Freigaben aus dem Journal – in den
Fußball-Märkten 1X2 und Über/Unter, bis 14 Tage vor Anstoß. Quelle ist API-Football
(`sources/apifootball.py`, Schlüssel in `APIKEY`): Pinnacle de-vigged als faire Referenz,
Bet365 und Betfair (Sportsbook, nicht Exchange) als spielbare Preise. Spiele werden über
Anstoß (±90 Min.) und beide Teamnamen zugeordnet, U19/U21 zu anderer Zeit fallen raus.

Telegram-Meldung, einmal je Tipp, Buchmacher und Preisstufe (+5 %,
Zustand in `data/journal/odds_guard.json`):
- **SPIELBAR**: Bet365/Betfair ≥ spielbare Mindestquote (EV ≥ 3 % gegen Pinnacle fair)
- **MARKT GEGEN FREIGABE** (nur PLAY): Pinnacle fair liegt über dem Freigabepreis.
  Der Wächter warnt nur, der CEO entscheidet.

Läuft in jedem Schnellscan mit (15-Minuten-Takt, ≈ 1 Abruf je Spieltag und je Spiel,
also ≈ 1.000 von 7.500 Anfragen/Tag). Ohne `APIKEY` wird er übersprungen, Fehler brechen
den Schnellscan nie ab. NFL/NHL/NBA/Eishockey sind nicht abgedeckt (API-Football = Fußball).

## Modellforschung

`python -m oddswatch research` vergleicht Modellvarianten über 13 Ligen mit Tuning- und
Holdout-Saisons: sagt die Abweichung Modell − Eröffnungsquote die Linienbewegung bis zum
Closing voraus (CLV)? Stand 29.09.2026: Schuss-xG-Varianten zeigen ein echtes, aber
kleines Signal (Steigung ≈ 0,03), die Tipps nach Abweichung haben dennoch CLV −7 bis
−10 % (Holdout) – kein Modell ist besser als der Markt, daher reiner Preisvergleich.

## Betfair-/Bet365-Scan (API-Football)

Stündlich im Schnellscan (`oddswatch/bfscan.py`, Schlüssel `APIKEY`): alle Spiele der
nächsten 7 Tage in Bundesliga, 2. BL, AT-Bundesliga, Premier League, La Liga, Serie A,
Ligue 1, UCL, UEL, UECL und Nations League. Pinnacle (de-vigged je Markt) ist der faire
Kurs, Betfair- und Bet365-**Sportsbook** sind die spielbaren Preise (API-Football liefert
nicht die Betfair-Börse; Marge 106–111 % im 1X2). Märkte: 1X2, Über/Unter und Asian
Handicap auf halben Linien. Freigabe bei EV ≥ 3 % gegen Pinnacle-fair. Journal-Referenz
`AF:<Fixture>:<Markt>`; Closing Line = letzter Pinnacle-Snapshot vor Anstoß
(`data/snapshots/apifootball-*.jsonl`), Abrechnung über das API-Football-Ergebnis.
Achtung: API-Football nennt beim Asian Handicap für beide Seiten die Heim-Linie
("Away -0.5" = Gast +0,5).
