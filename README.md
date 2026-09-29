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
3. **Fair**: `p_final = w·p_model + (1−w)·p_ref`. Die Referenz ist die de-vigged
   DraftKings-Linie, ersatzweise der Kalshi-Mittelkurs. `w` ist die angenommene
   Modellzuverlässigkeit (Fußball 0,5, Nations League 0,4, UEFA-Vereinswettbewerbe 0,3,
   NFL, NHL, NBA und europäisches Eishockey je 0,25).
4. **Preis**: Kalshi-Ask inkl. Taker-Gebühr (Order ≈ 100 Kontrakte).
   Orbit und bet365 sind hier nicht abrufbar und werden nie ungeprüft verwendet.
5. **Freigabe (PLAY)**: immer, wenn die Marktquote die spielbare Mindestquote
   („spielbar ab“ = Quote mit EV 3 %) erreicht – ohne Obergrenze für Anzahl oder Quote,
   für alle bewerteten Spiele (Fußball 14 Tage, NFL/NHL/NBA 7 Tage voraus), je Event einer.
   Zurückgehalten (WATCH) wird nur bei Informationsvorbehalt: News (z. B. QB fehlt,
   NBA-Leistungsträger ≥ 15 PPG fehlt), Modell-Markt-Divergenz > 15 Pp oder dünnem
   Kalshi-Orderbuch (Spread > 10 ¢ bzw. keine verlässliche Marktreferenz). Bei
   Zwei-Wege-Märkten dient die liquide Seite als Referenz.

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
