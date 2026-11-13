# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 13.11.2026 14:23 (Wien), Spiele 13.11. bis 15.11.2026

## Datenbasis
- Elo: **eigene Elo-Rechnung** (ClubElo von GitHub aus gesperrt), verankert an ClubElo vom 05.11.2026 (485 Teams), seither 433 Spiele eingerechnet
- Ergebnisbasis: 39568 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1153 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Bosnia (-215 Elo, 70 Sp.), Croatia (-25 Elo, 83 Sp.), Denmark (+15 Elo, 112 Sp.), Dnipro-1 (-175 Elo, 2 Sp.), Gibraltar (-355 Elo, 48 Sp.), Iceland (-110 Elo, 4 Sp.), Moldova (-320 Elo, 58 Sp.), Norway (+15 Elo, 125 Sp.), Poland (+5 Elo, 136 Sp.), San-Marino (-465 Elo, 28 Sp.), Slovenia (-135 Elo, 95 Sp.), Sweden (-70 Elo, 110 Sp.), Wales (-355 Elo, 40 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 825 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 60 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 60 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 0 Teams, Europapokal-xG aus 186 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.00 | ×1.129 | 51 % |
| Conference League | 303 | 2.60 | 2.99 | ×0.914 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.962 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 403 | 67.7 % | 62.7 % |
| Heimteam Außenseiter | 419 | 30.3 % | 30.0 % |

## Value-Kandidaten (Bet365)
Keine Wette über der Schwelle (Edge ≥ 5 %, Abweichung zu Pinnacle ≤ 15 Pp.).

Keine bewertbaren Spiele im Zeitraum (0 angesetzt).

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 88 Spiele ausgewertet, Log-Loss 1X2 Modell 0.983
- Gegen Pinnacle (88 Spiele): Modell 0.983 vs. Pinnacle 0.962 (kleiner = besser)
- Value-Wetten: 115, Ergebnis +5.01 Einheiten, ROI +4.4 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Hinweise
- ClubElo heute nicht erreichbar (ClubElo nicht erreichbar (https://clubelo.com/ARM: HTTP 403 · <!DOCTYPE html><html lang="en-US"><head><title>Just a mome) – eigene Elo-Rechnung

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
