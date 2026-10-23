# UEFA-Club v1 – Champions League · Europa League · Conference League
Stand 23.10.2026 12:28 (Wien), Spiele 23.10. bis 25.10.2026

## Datenbasis
- ClubElo: 661 Vereine
- Kalibrierung (aktuelles Elo (Näherung, bis genug Schnappschüsse vorliegen)): 1279 Europapokalspiele → 1.32 Tore je Team bei Gleichstand, Heimvorteil 77 Elo, Steigung 0.860 (176 Elo ≈ 1 Tor Differenz); reiner Fit 1.32 Tore / 80 Elo, Richtung Prior 1.35 / 60 geschrumpft
- xG: Liga-xG für 0 Teams, Europapokal-xG aus 132 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 377 | 3.22 | 2.84 | ×1.095 | 51 % |
| Conference League | 539 | 2.72 | 2.87 | ×0.958 | 46 % |
| Europa League | 363 | 2.69 | 2.81 | ×0.970 | 47 % |

## Value-Kandidaten (Bet365)
Keine Wette über der Schwelle (Edge ≥ 5 %, Abweichung zu Pinnacle ≤ 15 Pp.).

Keine bewertbaren Spiele im Zeitraum (0 angesetzt).

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 34 Spiele ausgewertet, Log-Loss 1X2 Modell 1.021
- Gegen Pinnacle (34 Spiele): Modell 1.021 vs. Pinnacle 1.003 (kleiner = besser)
- Value-Wetten: 42, Ergebnis -4.62 Einheiten, ROI -11.0 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
ClubElo-Stärke → Tormatrix (Poisson, Dixon-Coles), Steigung passend zu ClubElos eigener Siegerwartung; Torniveau und Heimvorteil an Europapokal-Ergebnissen geschätzt. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
