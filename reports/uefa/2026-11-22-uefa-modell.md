# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 22.11.2026 14:34 (Wien), Spiele 22.11. bis 24.11.2026

## Datenbasis
- Elo: ClubElo live (590 Teams zugeordnet)
- Ergebnisbasis: 39844 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1156 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-190 Elo, 2 Sp.), Gibraltar (-345 Elo, 49 Sp.), Hungary (-120 Elo, 4 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-465 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 825 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 55 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 17 Teams, Europapokal-xG aus 186 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.00 | ×1.130 | 51 % |
| Conference League | 303 | 2.60 | 2.98 | ×0.915 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.963 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 397 | 67.3 % | 62.6 % |
| Heimteam Außenseiter | 425 | 31.3 % | 30.1 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1 | 12 % | 9 % | 13.00 | +55.2 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 2 | 15 % | 11 % | 10.00 | +48.4 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | U2.5 | 26 % | – | 5.00 | +30.4 % |
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | U2.5 | 35 % | – | 3.50 | +21.9 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | 2 | 15 % | 12 % | 8.00 | +19.5 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | X | 17 % | 14 % | 7.00 | +18.1 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 2 | 18 % | 16 % | 6.50 | +16.3 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | U2.5 | 34 % | – | 3.40 | +14.9 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | U2.5 | 38 % | 31 % | 3.00 | +13.0 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1 | 40 % | 36 % | 2.80 | +12.0 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | X | 19 % | 17 % | 5.75 | +8.8 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | U2.5 | 34 % | 30 % | 3.20 | +7.2 % |
| Di 24.11. 21:00 | Manchester City – Napoli | 2 | 11 % | 10 % | 10.00 | +7.2 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | O2.5 | 64 % | 58 % | 1.67 | +6.2 % |

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | 1775 : 1669 | 2.23 : 1.13 | 62 % | 20 % | 18 % | 65 % | 61 % | 62 % / 19 % / 19 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1818 : 1875 | 1.66 : 1.56 | 40 % | 24 % | 36 % | 62 % | 64 % | 36 % / 24 % / 40 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | 2027 : 1888 | 2.27 : 1.01 | 65 % | 20 % | 15 % | 64 % | 57 % | 69 % / 19 % / 12 % |
| Di 24.11. 21:00 | Manchester City – Napoli | 1999 : 1810 | 2.66 : 0.95 | 73 % | 16 % | 11 % | 70 % | 57 % | 76 % / 15 % / 10 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 1865 : 1761 | 2.26 : 1.15 | 62 % | 20 % | 18 % | 66 % | 62 % | 67 % / 16 % / 16 % |
| Di 24.11. 21:00 | Feyenoord – FC Porto | 1736 : 1832 | 1.54 : 1.70 | 34 % | 24 % | 41 % | 63 % | 65 % | 35 % / 26 % / 39 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | 2015 : 1779 | 2.98 : 0.88 | 79 % | 13 % | 8 % | 74 % | 56 % | 81 % / 11 % / 8 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1514 : 1814 | 0.99 : 2.58 | 12 % | 17 % | 71 % | 69 % | 58 % | 9 % / 14 % / 77 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 1850 : 1713 | 2.37 : 1.05 | 66 % | 19 % | 15 % | 66 % | 59 % | 72 % / 17 % / 11 % |

<details><summary>Herleitung je Team</summary>

- **Bodo/Glimt**: Elo 1783 → 1775; Liga (matchpulse, 27 Sp.): xG 2.34:0.98/Sp., Elo-Erwartung +1.57; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur -9 Elo; Tempo ×1.01
- **Lask Linz**: Elo 1643 → 1669; Liga (matchpulse, 13 Sp.): xG 2.18:1.09/Sp., Elo-Erwartung +0.66; Europapokal (4 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +26 Elo; Tempo ×1.01
- **Galatasaray**: Elo 1826 → 1818; Liga (matchpulse, 12 Sp.): xG 2.15:0.96/Sp., Elo-Erwartung +1.22; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Aston Villa**: Elo 1896 → 1875; Liga (football-data-xg, 10 Sp.): xG 1.37:1.86/Sp., Elo-Erwartung +0.29; Europapokal (4 Sp.): xG-Residuum +0.51/Sp.; xG-Korrektur -21 Elo; Tempo ×1.02
- **Arsenal (England)**: Elo 2045 → 2027; Liga (football-data-xg, 10 Sp.): xG 1.61:0.76/Sp., Elo-Erwartung +1.20; Europapokal (4 Sp.): xG-Residuum -0.44/Sp.; xG-Korrektur -19 Elo; Tempo ×0.96
- **Borussia Dortmund**: Elo 1904 → 1888; Liga (matchpulse, 10 Sp.): xG 1.55:1.35/Sp., Elo-Erwartung +0.88; Europapokal (4 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur -16 Elo; Tempo ×0.96
- **Manchester City**: Elo 1999 → 1999; Liga (football-data-xg, 10 Sp.): xG 2.04:1.25/Sp., Elo-Erwartung +0.91; Europapokal (4 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur -1 Elo; Tempo ×1.02
- **Napoli**: Elo 1821 → 1810; Liga (football-data-xg, 11 Sp.): xG 1.79:1.24/Sp., Elo-Erwartung +0.44; Europapokal (4 Sp.): xG-Residuum -1.13/Sp.; xG-Korrektur -11 Elo; Tempo ×1.00
- **RB Leipzig**: Elo 1841 → 1865; Liga (matchpulse, 10 Sp.): xG 2.76:1.56/Sp., Elo-Erwartung +0.50; Europapokal (4 Sp.): xG-Residuum -0.05/Sp.; xG-Korrektur +24 Elo; Tempo ×1.04
- **Lens**: Elo 1777 → 1761; Liga (football-data-xg, 10 Sp.): xG 1.73:1.56/Sp., Elo-Erwartung +0.37; Europapokal (4 Sp.): xG-Residuum -0.67/Sp.; xG-Korrektur -16 Elo; Tempo ×1.01
- **Feyenoord**: Elo 1705 → 1736; Liga (matchpulse, 13 Sp.): xG 2.66:1.21/Sp., Elo-Erwartung +0.80; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur +31 Elo; Tempo ×1.02
- **FC Porto**: Elo 1844 → 1832; Liga (matchpulse, 11 Sp.): xG 2.15:0.81/Sp., Elo-Erwartung +1.48; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **Real Madrid**: Elo 2003 → 2015; Liga (football-data-xg, 12 Sp.): xG 2.47:0.94/Sp., Elo-Erwartung +1.38; Europapokal (4 Sp.): xG-Residuum +0.50/Sp.; xG-Korrektur +12 Elo; Tempo ×1.04
- **PSV Eindhoven**: Elo 1787 → 1779; Liga (matchpulse, 13 Sp.): xG 2.44:1.32/Sp., Elo-Erwartung +1.32; Europapokal (4 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Slovan Bratislava**: Elo 1544 → 1514; Europapokal (4 Sp.): xG-Residuum -1.23/Sp.; xG-Korrektur -30 Elo
- **Real Betis**: Elo 1828 → 1814; Liga (football-data-xg, 12 Sp.): xG 1.63:1.73/Sp., Elo-Erwartung +0.30; Europapokal (4 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -14 Elo; Tempo ×1.03
- **Como**: Elo 1841 → 1850; Liga (football-data-xg, 11 Sp.): xG 1.71:1.30/Sp., Elo-Erwartung +0.56; Europapokal (4 Sp.): xG-Residuum +1.09/Sp.; xG-Korrektur +9 Elo; Tempo ×1.00
- **AEK Athens FC**: Elo 1698 → 1713; Liga (football-data-xg, 9 Sp.): xG 2.15:0.71/Sp., Elo-Erwartung +0.97; Europapokal (4 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur +14 Elo; Tempo ×1.02

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 88 Spiele ausgewertet, Log-Loss 1X2 Modell 0.983
- Gegen Pinnacle (88 Spiele): Modell 0.983 vs. Pinnacle 0.962 (kleiner = besser)
- Value-Wetten: 115, Ergebnis +5.01 Einheiten, ROI +4.4 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
