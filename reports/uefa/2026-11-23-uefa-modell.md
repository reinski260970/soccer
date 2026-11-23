# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 23.11.2026 17:25 (Wien), Spiele 23.11. bis 25.11.2026

## Datenbasis
- Elo: ClubElo live (590 Teams zugeordnet)
- Ergebnisbasis: 39963 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1157 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-190 Elo, 2 Sp.), Gibraltar (-345 Elo, 49 Sp.), Hungary (-120 Elo, 4 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-465 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 825 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 55 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 31 Teams, Europapokal-xG aus 186 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.00 | ×1.130 | 51 % |
| Conference League | 303 | 2.60 | 2.98 | ×0.915 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.963 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 401 | 66.8 % | 62.4 % |
| Heimteam Außenseiter | 421 | 31.4 % | 30.0 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Mi 25.11. 21:00 | Atletico Madrid – Viking | 2 | 9 % | 4 % | 21.00 | +97.8 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 2 | 15 % | 10 % | 10.00 | +48.1 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | 1 | 34 % | 21 % | 4.33 | +46.5 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | X | 15 % | 8 % | 9.00 | +35.9 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1 | 12 % | 9 % | 11.00 | +31.1 % |
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | U2.5 | 35 % | – | 3.75 | +30.8 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | U2.5 | 38 % | 27 % | 3.40 | +29.9 % |
| Mi 25.11. 18:45 | Slavia Praha – Villarreal | 1 | 42 % | 32 % | 3.10 | +29.9 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | U2.5 | 26 % | – | 5.00 | +29.8 % |
| Mi 25.11. 21:00 | Inter – VfB Stuttgart | U2.5 | 32 % | – | 4.00 | +28.3 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 2 | 18 % | 15 % | 7.00 | +25.6 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | U2.5 | 38 % | 29 % | 3.20 | +20.6 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | 2 | 15 % | 12 % | 8.00 | +19.6 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1 | 40 % | 35 % | 2.90 | +15.7 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | U2.5 | 34 % | – | 3.40 | +15.0 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | U2.5 | 33 % | 28 % | 3.40 | +13.8 % |
| Mi 25.11. 21:00 | Lille – Bayern München | 2 | 72 % | 59 % | 1.57 | +13.5 % |
| Mi 25.11. 21:00 | Sporting CP – Manchester United | 1 | 46 % | 39 % | 2.45 | +13.5 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | X | 19 % | 15 % | 6.00 | +13.4 % |
| Mi 25.11. 21:00 | Paris Saint Germain – AS Roma | 2 | 15 % | 13 % | 7.50 | +13.3 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | U2.5 | 30 % | – | 3.75 | +12.0 % |
| Mi 25.11. 21:00 | Paris Saint Germain – AS Roma | U2.5 | 33 % | 29 % | 3.40 | +11.6 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | X | 13 % | 11 % | 8.50 | +10.7 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | X | 24 % | 20 % | 4.50 | +9.8 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | X | 17 % | 13 % | 6.50 | +9.5 % |
| Mi 25.11. 21:00 | Lille – Bayern München | O2.5 | 69 % | 61 % | 1.57 | +8.6 % |
| Mi 25.11. 21:00 | Shakhtar Donetsk – Fenerbahçe | O2.5 | 62 % | 56 % | 1.73 | +6.9 % |

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | 1774 : 1670 | 2.22 : 1.13 | 61 % | 21 % | 18 % | 65 % | 61 % | 63 % / 19 % / 18 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1817 : 1874 | 1.66 : 1.56 | 40 % | 24 % | 36 % | 62 % | 64 % | 35 % / 24 % / 42 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | 2026 : 1888 | 2.27 : 1.01 | 65 % | 20 % | 15 % | 64 % | 57 % | 68 % / 19 % / 12 % |
| Di 24.11. 21:00 | Manchester City – Napoli | 1998 : 1809 | 2.65 : 0.95 | 73 % | 16 % | 11 % | 70 % | 57 % | 75 % / 15 % / 10 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 1865 : 1761 | 2.26 : 1.15 | 62 % | 20 % | 18 % | 66 % | 62 % | 69 % / 16 % / 15 % |
| Di 24.11. 21:00 | Feyenoord – FC Porto | 1736 : 1832 | 1.54 : 1.70 | 34 % | 24 % | 41 % | 63 % | 65 % | 34 % / 26 % / 40 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | 2015 : 1779 | 2.98 : 0.88 | 79 % | 13 % | 8 % | 74 % | 56 % | 81 % / 11 % / 8 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1514 : 1814 | 0.99 : 2.58 | 12 % | 17 % | 71 % | 69 % | 58 % | 9 % / 13 % / 78 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 1850 : 1712 | 2.37 : 1.05 | 66 % | 19 % | 15 % | 67 % | 59 % | 76 % / 15 % / 10 % |
| Mi 25.11. 18:45 | Slavia Praha – Villarreal | 1777 : 1820 | 1.68 : 1.49 | 42 % | 24 % | 34 % | 61 % | 64 % | 32 % / 24 % / 45 % |
| Mi 25.11. 18:45 | Sabah FA – Barcelona | 1550 : 2052 | 0.67 : 4.05 | 2 % | 6 % | 92 % | 85 % | 48 % | 5 % / 7 % / 88 % |
| Mi 25.11. 21:00 | Lille – Bayern München | 1755 : 2066 | 0.96 : 2.61 | 11 % | 16 % | 72 % | 69 % | 58 % | 19 % / 22 % / 59 % |
| Mi 25.11. 21:00 | Paris Saint Germain – AS Roma | 2010 : 1875 | 2.39 : 1.07 | 66 % | 19 % | 15 % | 67 % | 60 % | 69 % / 18 % / 13 % |
| Mi 25.11. 21:00 | Sporting CP – Manchester United | 1834 : 1848 | 1.81 : 1.42 | 46 % | 24 % | 30 % | 63 % | 64 % | 39 % / 25 % / 36 % |
| Mi 25.11. 21:00 | Inter – VfB Stuttgart | 1949 : 1811 | 2.43 : 1.08 | 67 % | 19 % | 15 % | 68 % | 60 % | 68 % / 17 % / 15 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | 1900 : 1690 | 2.73 : 0.90 | 75 % | 15 % | 9 % | 70 % | 56 % | 88 % / 8 % / 4 % |
| Mi 25.11. 21:00 | Shakhtar Donetsk – Fenerbahçe | 1700 : 1770 | 1.60 : 1.59 | 38 % | 25 % | 37 % | 62 % | 64 % | 36 % / 27 % / 37 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | 1828 : 1928 | 1.50 : 1.69 | 34 % | 24 % | 42 % | 62 % | 64 % | 21 % / 20 % / 58 % |

<details><summary>Herleitung je Team</summary>

- **Bodo/Glimt**: Elo 1782 → 1774; Liga (matchpulse, 27 Sp.): xG 2.34:0.98/Sp., Elo-Erwartung +1.57; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur -9 Elo; Tempo ×1.01
- **Lask Linz**: Elo 1643 → 1670; Liga (matchpulse, 13 Sp.): xG 2.18:1.08/Sp., Elo-Erwartung +0.66; Europapokal (4 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +26 Elo; Tempo ×1.01
- **Galatasaray**: Elo 1824 → 1817; Liga (matchpulse, 12 Sp.): xG 2.15:0.96/Sp., Elo-Erwartung +1.22; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Aston Villa**: Elo 1895 → 1874; Liga (football-data-xg, 10 Sp.): xG 1.37:1.86/Sp., Elo-Erwartung +0.29; Europapokal (4 Sp.): xG-Residuum +0.51/Sp.; xG-Korrektur -21 Elo; Tempo ×1.02
- **Arsenal (England)**: Elo 2045 → 2026; Liga (football-data-xg, 10 Sp.): xG 1.61:0.76/Sp., Elo-Erwartung +1.20; Europapokal (4 Sp.): xG-Residuum -0.42/Sp.; xG-Korrektur -18 Elo; Tempo ×0.96
- **Borussia Dortmund**: Elo 1904 → 1888; Liga (matchpulse, 10 Sp.): xG 1.55:1.35/Sp., Elo-Erwartung +0.87; Europapokal (4 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur -16 Elo; Tempo ×0.96
- **Manchester City**: Elo 1999 → 1998; Liga (football-data-xg, 10 Sp.): xG 2.04:1.25/Sp., Elo-Erwartung +0.91; Europapokal (4 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur -0 Elo; Tempo ×1.02
- **Napoli**: Elo 1821 → 1809; Liga (football-data-xg, 11 Sp.): xG 1.79:1.24/Sp., Elo-Erwartung +0.44; Europapokal (4 Sp.): xG-Residuum -1.13/Sp.; xG-Korrektur -11 Elo; Tempo ×1.00
- **RB Leipzig**: Elo 1841 → 1865; Liga (matchpulse, 10 Sp.): xG 2.76:1.56/Sp., Elo-Erwartung +0.49; Europapokal (4 Sp.): xG-Residuum -0.05/Sp.; xG-Korrektur +24 Elo; Tempo ×1.04
- **Lens**: Elo 1777 → 1761; Liga (football-data-xg, 10 Sp.): xG 1.73:1.56/Sp., Elo-Erwartung +0.36; Europapokal (4 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur -16 Elo; Tempo ×1.01
- **Feyenoord**: Elo 1705 → 1736; Liga (matchpulse, 13 Sp.): xG 2.66:1.20/Sp., Elo-Erwartung +0.81; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur +32 Elo; Tempo ×1.03
- **FC Porto**: Elo 1844 → 1832; Liga (matchpulse, 11 Sp.): xG 2.15:0.81/Sp., Elo-Erwartung +1.48; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **Real Madrid**: Elo 2003 → 2015; Liga (football-data-xg, 12 Sp.): xG 2.47:0.94/Sp., Elo-Erwartung +1.38; Europapokal (4 Sp.): xG-Residuum +0.50/Sp.; xG-Korrektur +12 Elo; Tempo ×1.04
- **PSV Eindhoven**: Elo 1788 → 1779; Liga (matchpulse, 13 Sp.): xG 2.44:1.32/Sp., Elo-Erwartung +1.33; Europapokal (4 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Slovan Bratislava**: Elo 1544 → 1514; Europapokal (4 Sp.): xG-Residuum -1.23/Sp.; xG-Korrektur -30 Elo
- **Real Betis**: Elo 1828 → 1814; Liga (football-data-xg, 12 Sp.): xG 1.63:1.73/Sp., Elo-Erwartung +0.31; Europapokal (4 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -14 Elo; Tempo ×1.03
- **Como**: Elo 1841 → 1850; Liga (football-data-xg, 11 Sp.): xG 1.71:1.30/Sp., Elo-Erwartung +0.56; Europapokal (4 Sp.): xG-Residuum +1.09/Sp.; xG-Korrektur +9 Elo; Tempo ×1.00
- **AEK Athens FC**: Elo 1698 → 1712; Liga (football-data-xg, 9 Sp.): xG 2.15:0.71/Sp., Elo-Erwartung +0.98; Europapokal (4 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur +14 Elo; Tempo ×1.02
- **Slavia Praha**: Elo 1750 → 1777; Europapokal (4 Sp.): xG-Residuum +1.09/Sp.; xG-Korrektur +27 Elo
- **Villarreal**: Elo 1789 → 1820; Liga (football-data-xg, 12 Sp.): xG 2.00:1.07/Sp., Elo-Erwartung +0.07; Europapokal (4 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur +31 Elo; Tempo ×1.01
- **Sabah FA**: Elo 1567 → 1550; Europapokal (4 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur -17 Elo
- **Barcelona**: Elo 2035 → 2052; Liga (football-data-xg, 12 Sp.): xG 3.24:1.11/Sp., Elo-Erwartung +1.60; Europapokal (4 Sp.): xG-Residuum -0.34/Sp.; xG-Korrektur +17 Elo; Tempo ×1.10
- **Lille**: Elo 1774 → 1755; Liga (football-data-xg, 10 Sp.): xG 1.31:1.50/Sp., Elo-Erwartung +0.34; Europapokal (4 Sp.): xG-Residuum +0.02/Sp.; xG-Korrektur -19 Elo; Tempo ×0.98
- **Bayern München**: Elo 2040 → 2066; Liga (matchpulse, 10 Sp.): xG 3.22:0.99/Sp., Elo-Erwartung +1.76; Europapokal (4 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur +25 Elo; Tempo ×1.04
- **Paris Saint Germain**: Elo 1991 → 2010; Europapokal (4 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +19 Elo
- **AS Roma**: Elo 1870 → 1875; Liga (football-data-xg, 11 Sp.): xG 2.39:1.27/Sp., Elo-Erwartung +0.73; Europapokal (4 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur +5 Elo; Tempo ×1.04
- **Sporting CP**: Elo 1863 → 1834; Liga (matchpulse, 11 Sp.): xG 1.72:0.82/Sp., Elo-Erwartung +1.61; Europapokal (4 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur -30 Elo; Tempo ×1.00
- **Manchester United**: Elo 1846 → 1848; Liga (football-data-xg, 10 Sp.): xG 1.74:1.78/Sp., Elo-Erwartung -0.00; Europapokal (4 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur +2 Elo; Tempo ×1.04
- **Inter**: Elo 1947 → 1949; Liga (football-data-xg, 11 Sp.): xG 2.62:0.98/Sp., Elo-Erwartung +1.21; Europapokal (4 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur +2 Elo; Tempo ×1.03
- **VfB Stuttgart**: Elo 1819 → 1811; Liga (matchpulse, 10 Sp.): xG 1.86:2.02/Sp., Elo-Erwartung +0.36; Europapokal (4 Sp.): xG-Residuum +0.76/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Atletico Madrid**: Elo 1915 → 1900; Liga (football-data-xg, 12 Sp.): xG 1.61:1.13/Sp., Elo-Erwartung +0.83; Europapokal (4 Sp.): xG-Residuum -0.12/Sp.; xG-Korrektur -15 Elo; Tempo ×0.99
- **Viking**: Elo 1704 → 1690; Liga (matchpulse, 27 Sp.): xG 2.06:1.13/Sp., Elo-Erwartung +1.06; Europapokal (4 Sp.): xG-Residuum -0.76/Sp.; xG-Korrektur -14 Elo; Tempo ×1.00
- **Shakhtar Donetsk**: Elo 1672 → 1700; Europapokal (4 Sp.): xG-Residuum +1.14/Sp.; xG-Korrektur +28 Elo
- **Fenerbahçe**: Elo 1781 → 1770; Liga (matchpulse, 12 Sp.): xG 1.90:1.29/Sp., Elo-Erwartung +0.95; Europapokal (4 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur -11 Elo; Tempo ×1.03
- **Club Brugge KV**: Elo 1842 → 1828; Liga (matchpulse, 12 Sp.): xG 2.34:1.11/Sp., Elo-Erwartung +1.42; Europapokal (4 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur -14 Elo; Tempo ×1.03
- **Liverpool**: Elo 1942 → 1928; Liga (football-data-xg, 10 Sp.): xG 1.58:1.31/Sp., Elo-Erwartung +0.57; Europapokal (4 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -15 Elo; Tempo ×1.00

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 88 Spiele ausgewertet, Log-Loss 1X2 Modell 0.983
- Gegen Pinnacle (88 Spiele): Modell 0.983 vs. Pinnacle 0.962 (kleiner = besser)
- Value-Wetten: 115, Ergebnis +5.01 Einheiten, ROI +4.4 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
