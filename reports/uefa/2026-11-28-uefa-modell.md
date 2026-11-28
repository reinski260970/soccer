# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 28.11.2026 15:28 (Wien), Spiele 28.11. bis 30.11.2026

## Datenbasis
- Elo: ClubElo live (589 Teams zugeordnet)
- Ergebnisbasis: 40144 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1157 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-180 Elo, 2 Sp.), Gibraltar (-345 Elo, 50 Sp.), Hungary (-120 Elo, 4 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-465 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 879 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 76 Elo (reiner Fit 55 / 80, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 0 Teams, Europapokal-xG aus 240 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 279 | 3.54 | 3.00 | ×1.119 | 51 % |
| Conference League | 321 | 2.63 | 2.98 | ×0.919 | 48 % |
| Europa League | 279 | 2.79 | 2.94 | ×0.966 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 428 | 66.6 % | 62.6 % |
| Heimteam Außenseiter | 448 | 31.7 % | 30.1 % |

## Value-Kandidaten (Bet365)
Keine Wette über der Schwelle (Edge ≥ 5 %, Abweichung zu Pinnacle ≤ 15 Pp.).

Keine bewertbaren Spiele im Zeitraum (0 angesetzt).

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 142 Spiele ausgewertet, Log-Loss 1X2 Modell 0.956
- Gegen Pinnacle (142 Spiele): Modell 0.956 vs. Pinnacle 0.934 (kleiner = besser)
- Value-Wetten: 208, Ergebnis +1.64 Einheiten, ROI +0.8 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
