# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 18.11.2026 15:29 (Wien), Spiele 18.11. bis 20.11.2026

## Datenbasis
- Elo: ClubElo live (589 Teams zugeordnet)
- Ergebnisbasis: 39611 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1154 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-180 Elo, 2 Sp.), Gibraltar (-345 Elo, 49 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-470 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 825 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 76 Elo (reiner Fit 55 / 80, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 0 Teams, Europapokal-xG aus 186 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.00 | ×1.130 | 51 % |
| Conference League | 303 | 2.60 | 2.98 | ×0.915 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.963 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 400 | 67.0 % | 62.5 % |
| Heimteam Außenseiter | 422 | 31.3 % | 30.4 % |

## Value-Kandidaten (Bet365)
Keine Wette über der Schwelle (Edge ≥ 5 %, Abweichung zu Pinnacle ≤ 15 Pp.).

Keine bewertbaren Spiele im Zeitraum (0 angesetzt).

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 88 Spiele ausgewertet, Log-Loss 1X2 Modell 0.983
- Gegen Pinnacle (88 Spiele): Modell 0.983 vs. Pinnacle 0.962 (kleiner = besser)
- Value-Wetten: 115, Ergebnis +5.01 Einheiten, ROI +4.4 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
