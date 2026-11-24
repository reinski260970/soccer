# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 24.11.2026 17:19 (Wien), Spiele 24.11. bis 26.11.2026

## Datenbasis
- Elo: ClubElo live (589 Teams zugeordnet)
- Ergebnisbasis: 39981 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1157 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-180 Elo, 2 Sp.), Gibraltar (-345 Elo, 49 Sp.), Hungary (-120 Elo, 4 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-465 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 825 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 55 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 77 Teams, Europapokal-xG aus 186 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.00 | ×1.130 | 51 % |
| Conference League | 303 | 2.60 | 2.98 | ×0.915 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.963 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 402 | 66.7 % | 62.3 % |
| Heimteam Außenseiter | 420 | 31.4 % | 29.9 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Mi 25.11. 21:00 | Atletico Madrid – Viking | 2 | 9 % | 4 % | 34.00 | +199.3 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | 1 | 23 % | 11 % | 11.00 | +151.8 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | X | 14 % | 8 % | 12.00 | +73.7 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | X | 22 % | 13 % | 7.50 | +67.7 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | 2 | 16 % | 8 % | 10.00 | +64.2 % |
| Do 26.11. 21:00 | SC Braga – KuPS | 2 | 8 % | 5 % | 19.00 | +49.6 % |
| Do 26.11. 18:45 | Ajax – FC Thun | 2 | 11 % | 8 % | 13.00 | +49.4 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 2 | 15 % | 10 % | 10.00 | +48.8 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | X | 26 % | 17 % | 5.50 | +45.3 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | 2 | 12 % | 8 % | 12.00 | +44.7 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | U2.5 | 38 % | 27 % | 3.75 | +41.6 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | 1 | 32 % | 21 % | 4.33 | +39.9 % |
| Do 26.11. 18:45 | Ajax – FC Thun | X | 20 % | 11 % | 7.00 | +38.5 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 2 | 18 % | 13 % | 7.50 | +38.1 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | U2.5 | 46 % | 31 % | 3.00 | +36.8 % |
| Mi 25.11. 18:45 | Slavia Praha – Villarreal | 1 | 44 % | 30 % | 3.10 | +34.9 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | X | 17 % | 12 % | 8.00 | +33.2 % |
| Do 26.11. 21:00 | SC Braga – KuPS | X | 16 % | 11 % | 8.00 | +31.1 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | X | 17 % | 12 % | 7.50 | +31.0 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | 2 | 16 % | 13 % | 8.00 | +30.9 % |
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | U2.5 | 35 % | – | 3.75 | +30.8 % |
| Do 26.11. 18:45 | Dinamo Zagreb – Bayer Leverkusen | U2.5 | 47 % | 36 % | 2.75 | +29.6 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | U2.5 | 37 % | 27 % | 3.50 | +28.7 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | X | 13 % | 9 % | 10.00 | +28.1 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | U2.5 | 26 % | – | 5.00 | +27.6 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | U2.5 | 40 % | 30 % | 3.20 | +27.3 % |
| Mi 25.11. 21:00 | Inter – VfB Stuttgart | U2.5 | 32 % | – | 4.00 | +27.2 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | U2.5 | 53 % | 39 % | 2.40 | +26.8 % |
| Do 26.11. 18:45 | Plzen – Benfica | U2.5 | 46 % | 33 % | 2.75 | +25.4 % |
| Do 26.11. 18:45 | Pafos – FC Midtjylland | U2.5 | 53 % | 40 % | 2.35 | +24.6 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | X | 19 % | 15 % | 6.50 | +24.1 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | U2.5 | 41 % | 32 % | 3.00 | +24.0 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | X | 22 % | 16 % | 5.50 | +23.2 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | 2 | 8 % | 7 % | 15.00 | +23.2 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | U2.5 | 51 % | 39 % | 2.40 | +22.8 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | U2.5 | 44 % | 35 % | 2.75 | +22.1 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | 2 | 23 % | 18 % | 5.25 | +21.4 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | 2 | 9 % | 7 % | 13.00 | +21.1 % |
| Mi 25.11. 21:00 | Sporting CP – Manchester United | 1 | 48 % | 38 % | 2.50 | +20.7 % |
| Do 26.11. 21:00 | SC Braga – KuPS | U2.5 | 41 % | 31 % | 2.88 | +19.4 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | U2.5 | 34 % | – | 3.50 | +19.2 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1 | 39 % | 32 % | 3.00 | +18.3 % |
| Do 26.11. 21:00 | NEC Nijmegen – Rennes | U2.5 | 47 % | 38 % | 2.50 | +18.3 % |
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | X | 21 % | 17 % | 5.75 | +18.1 % |
| Do 26.11. 18:45 | Plzen – Benfica | X | 24 % | 19 % | 5.00 | +17.7 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | X | 16 % | 11 % | 7.50 | +17.3 % |
| Mi 25.11. 21:00 | Lille – Bayern München | 2 | 72 % | 58 % | 1.62 | +16.9 % |
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | 2 | 18 % | 14 % | 6.50 | +16.9 % |
| Do 26.11. 21:00 | CSKA Sofia – Trabzonspor | U2.5 | 51 % | 41 % | 2.30 | +16.6 % |
| Do 26.11. 18:45 | Marseille – Levski Sofia | 2 | 15 % | 13 % | 8.00 | +16.4 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | U2.5 | 34 % | 30 % | 3.40 | +16.2 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | U2.5 | 51 % | 41 % | 2.25 | +15.8 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | U2.5 | 29 % | – | 4.00 | +15.8 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | X | 24 % | 20 % | 4.75 | +15.0 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | X | 21 % | 16 % | 5.50 | +12.8 % |
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | U2.5 | 36 % | 31 % | 3.10 | +12.5 % |
| Do 26.11. 18:45 | FK Jablonec – FC Lugano | 1 | 33 % | 29 % | 3.40 | +12.2 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | X | 17 % | 15 % | 6.50 | +11.8 % |
| Do 26.11. 18:45 | FK Jablonec – FC Lugano | U2.5 | 54 % | 46 % | 2.08 | +11.6 % |
| Do 26.11. 18:45 | Plzen – Benfica | 1 | 19 % | 16 % | 5.75 | +11.5 % |
| Do 26.11. 21:00 | Crystal Palace – Real Sociedad | U2.5 | 47 % | 39 % | 2.38 | +11.5 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1 | 12 % | 9 % | 9.00 | +11.4 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | X | 19 % | 15 % | 5.75 | +11.1 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | X | 21 % | 17 % | 5.25 | +10.8 % |
| Do 26.11. 21:00 | FC Nordsjaelland – Panathinaikos | U2.5 | 51 % | 44 % | 2.15 | +10.6 % |
| Do 26.11. 18:45 | Dinamo Zagreb – Bayer Leverkusen | X | 24 % | 22 % | 4.50 | +10.2 % |
| Do 26.11. 21:00 | Ferencvarosi TC – Celje | 2 | 14 % | 12 % | 8.00 | +9.9 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | X | 26 % | 22 % | 4.20 | +9.6 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | O2.5 | 63 % | 55 % | 1.73 | +9.6 % |
| Do 26.11. 21:00 | Gent – FK Crvena Zvezda | U2.5 | 55 % | 48 % | 2.00 | +9.6 % |
| Do 26.11. 21:00 | Sparta Praha – AZ Alkmaar | U2.5 | 50 % | 43 % | 2.20 | +9.3 % |
| Do 26.11. 21:00 | Ferencvarosi TC – Celje | U2.5 | 43 % | 38 % | 2.50 | +8.5 % |
| Do 26.11. 21:00 | Borac Banja Luka – Atalanta | U2.5 | 46 % | 39 % | 2.35 | +8.2 % |
| Mi 25.11. 21:00 | Lille – Bayern München | O2.5 | 69 % | 61 % | 1.57 | +8.1 % |
| Do 26.11. 21:00 | Torreense – Celtic | U2.5 | 45 % | 38 % | 2.38 | +7.8 % |
| Di 24.11. 21:00 | Manchester City – Napoli | U2.5 | 31 % | 26 % | 3.50 | +7.7 % |
| Do 26.11. 21:00 | OFI – Anderlecht | U2.5 | 49 % | 44 % | 2.20 | +7.6 % |
| Mi 25.11. 21:00 | Shakhtar Donetsk – Fenerbahçe | O2.5 | 62 % | 55 % | 1.73 | +6.9 % |
| Di 24.11. 21:00 | Feyenoord – FC Porto | 1 | 34 % | 29 % | 3.10 | +6.9 % |
| Do 26.11. 21:00 | HNK Hajduk Split – St. Truiden | U2.5 | 52 % | 46 % | 2.05 | +6.3 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | 2 | 14 % | 13 % | 7.50 | +6.1 % |
| Mi 25.11. 21:00 | Paris Saint Germain – AS Roma | 2 | 15 % | 13 % | 7.00 | +5.7 % |
| Di 24.11. 21:00 | Feyenoord – FC Porto | O2.5 | 63 % | 57 % | 1.67 | +5.1 % |
| Do 26.11. 16:30 | Kairat Almaty – Mjallby AIF | 2 | 35 % | 32 % | 3.00 | +5.1 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- Beşiktaş – Hapoel Beer Sheva: U2.5 Modell 45 % vs. Pinnacle 29 %
- Ajax – FC Thun: U2.5 Modell 45 % vs. Pinnacle 23 %
- Brann – Aarhus: U2.5 Modell 52 % vs. Pinnacle 36 %
- SC Freiburg – Twente: U2.5 Modell 53 % vs. Pinnacle 38 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 24.11. 18:45 | Bodo/Glimt – Lask Linz | 1774 : 1670 | 2.22 : 1.13 | 61 % | 21 % | 18 % | 65 % | 61 % | 69 % / 17 % / 14 % |
| Di 24.11. 18:45 | Galatasaray – Aston Villa | 1817 : 1877 | 1.63 : 1.56 | 39 % | 24 % | 36 % | 62 % | 64 % | 32 % / 25 % / 43 % |
| Di 24.11. 21:00 | Arsenal – Borussia Dortmund | 2022 : 1888 | 2.25 : 1.01 | 65 % | 20 % | 15 % | 63 % | 57 % | 65 % / 21 % / 14 % |
| Di 24.11. 21:00 | Manchester City – Napoli | 1999 : 1812 | 2.62 : 0.95 | 73 % | 16 % | 11 % | 69 % | 57 % | 74 % / 15 % / 11 % |
| Di 24.11. 21:00 | RB Leipzig – Lens | 1865 : 1766 | 2.23 : 1.16 | 61 % | 21 % | 18 % | 66 % | 62 % | 71 % / 16 % / 13 % |
| Di 24.11. 21:00 | Feyenoord – FC Porto | 1736 : 1832 | 1.54 : 1.70 | 34 % | 24 % | 41 % | 63 % | 65 % | 29 % / 26 % / 45 % |
| Di 24.11. 21:00 | Real Madrid – PSV Eindhoven | 2018 : 1779 | 3.01 : 0.88 | 80 % | 13 % | 7 % | 74 % | 56 % | 85 % / 9 % / 6 % |
| Di 24.11. 21:00 | Slovan Bratislava – Real Betis | 1514 : 1809 | 1.00 : 2.54 | 12 % | 17 % | 70 % | 69 % | 59 % | 9 % / 15 % / 76 % |
| Di 24.11. 21:00 | Como – AEK Athens FC | 1848 : 1710 | 2.35 : 1.04 | 66 % | 19 % | 15 % | 66 % | 59 % | 75 % / 15 % / 10 % |
| Mi 25.11. 18:45 | Slavia Praha – Villarreal | 1777 : 1809 | 1.72 : 1.45 | 44 % | 24 % | 32 % | 61 % | 63 % | 30 % / 24 % / 45 % |
| Mi 25.11. 18:45 | Sabah FA – Barcelona | 1550 : 2056 | 0.66 : 4.08 | 2 % | 6 % | 92 % | 85 % | 48 % | 4 % / 7 % / 89 % |
| Mi 25.11. 21:00 | Lille – Bayern München | 1756 : 2066 | 0.96 : 2.60 | 11 % | 17 % | 72 % | 69 % | 57 % | 19 % / 23 % / 58 % |
| Mi 25.11. 21:00 | Paris Saint Germain – AS Roma | 2010 : 1876 | 2.39 : 1.08 | 66 % | 19 % | 15 % | 67 % | 60 % | 68 % / 19 % / 13 % |
| Mi 25.11. 21:00 | Sporting CP – Manchester United | 1834 : 1835 | 1.86 : 1.39 | 48 % | 24 % | 28 % | 63 % | 64 % | 38 % / 26 % / 36 % |
| Mi 25.11. 21:00 | Inter – VfB Stuttgart | 1946 : 1811 | 2.43 : 1.09 | 66 % | 19 % | 15 % | 68 % | 61 % | 68 % / 17 % / 15 % |
| Mi 25.11. 21:00 | Atletico Madrid – Viking | 1910 : 1690 | 2.79 : 0.88 | 77 % | 14 % | 9 % | 71 % | 55 % | 88 % / 8 % / 4 % |
| Mi 25.11. 21:00 | Shakhtar Donetsk – Fenerbahçe | 1700 : 1769 | 1.60 : 1.59 | 38 % | 25 % | 37 % | 62 % | 64 % | 36 % / 27 % / 37 % |
| Mi 25.11. 21:00 | Club Brugge KV – Liverpool | 1828 : 1939 | 1.47 : 1.74 | 32 % | 24 % | 43 % | 62 % | 64 % | 21 % / 20 % / 59 % |

<details><summary>Herleitung je Team</summary>

- **Bodo/Glimt**: Elo 1782 → 1774; Liga (matchpulse, 27 Sp.): xG 2.34:0.98/Sp., Elo-Erwartung +1.57; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur -9 Elo; Tempo ×1.01
- **Lask Linz**: Elo 1643 → 1670; Liga (matchpulse, 13 Sp.): xG 2.18:1.08/Sp., Elo-Erwartung +0.66; Europapokal (4 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +26 Elo; Tempo ×1.01
- **Galatasaray**: Elo 1824 → 1817; Liga (matchpulse, 12 Sp.): xG 2.15:0.96/Sp., Elo-Erwartung +1.23; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Aston Villa**: Elo 1895 → 1877; Liga (football-data-xg, 11 Sp.): xG 1.34:1.72/Sp., Elo-Erwartung +0.29; Europapokal (4 Sp.): xG-Residuum +0.51/Sp.; xG-Korrektur -18 Elo; Tempo ×1.01
- **Arsenal (England)**: Elo 2045 → 2022; Liga (football-data-xg, 11 Sp.): xG 1.60:0.84/Sp., Elo-Erwartung +1.20; Europapokal (4 Sp.): xG-Residuum -0.42/Sp.; xG-Korrektur -22 Elo; Tempo ×0.96
- **Borussia Dortmund**: Elo 1904 → 1888; Liga (matchpulse, 10 Sp.): xG 1.55:1.35/Sp., Elo-Erwartung +0.87; Europapokal (4 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur -16 Elo; Tempo ×0.96
- **Manchester City**: Elo 1999 → 1999; Liga (football-data-xg, 11 Sp.): xG 2.02:1.20/Sp., Elo-Erwartung +0.91; Europapokal (4 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur +0 Elo; Tempo ×1.02
- **Napoli**: Elo 1821 → 1812; Liga (football-data-xg, 12 Sp.): xG 1.79:1.18/Sp., Elo-Erwartung +0.44; Europapokal (4 Sp.): xG-Residuum -1.13/Sp.; xG-Korrektur -8 Elo; Tempo ×0.99
- **RB Leipzig**: Elo 1841 → 1865; Liga (matchpulse, 10 Sp.): xG 2.76:1.56/Sp., Elo-Erwartung +0.49; Europapokal (4 Sp.): xG-Residuum -0.05/Sp.; xG-Korrektur +24 Elo; Tempo ×1.04
- **Lens**: Elo 1777 → 1766; Liga (football-data-xg, 11 Sp.): xG 1.79:1.49/Sp., Elo-Erwartung +0.36; Europapokal (4 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur -11 Elo; Tempo ×1.01
- **Feyenoord**: Elo 1705 → 1736; Liga (matchpulse, 13 Sp.): xG 2.66:1.20/Sp., Elo-Erwartung +0.81; Europapokal (4 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur +32 Elo; Tempo ×1.03
- **FC Porto**: Elo 1844 → 1832; Liga (matchpulse, 11 Sp.): xG 2.15:0.81/Sp., Elo-Erwartung +1.48; Europapokal (4 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **Real Madrid**: Elo 2003 → 2018; Liga (football-data-xg, 13 Sp.): xG 2.56:0.98/Sp., Elo-Erwartung +1.38; Europapokal (4 Sp.): xG-Residuum +0.50/Sp.; xG-Korrektur +14 Elo; Tempo ×1.05
- **PSV Eindhoven**: Elo 1788 → 1779; Liga (matchpulse, 13 Sp.): xG 2.44:1.32/Sp., Elo-Erwartung +1.33; Europapokal (4 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Slovan Bratislava**: Elo 1544 → 1514; Europapokal (4 Sp.): xG-Residuum -1.23/Sp.; xG-Korrektur -30 Elo
- **Real Betis**: Elo 1828 → 1809; Liga (football-data-xg, 13 Sp.): xG 1.55:1.78/Sp., Elo-Erwartung +0.31; Europapokal (4 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -20 Elo; Tempo ×1.03
- **Como**: Elo 1840 → 1848; Liga (football-data-xg, 12 Sp.): xG 1.63:1.25/Sp., Elo-Erwartung +0.55; Europapokal (4 Sp.): xG-Residuum +1.09/Sp.; xG-Korrektur +8 Elo; Tempo ×0.98
- **AEK Athens FC**: Elo 1698 → 1710; Liga (football-data-xg, 10 Sp.): xG 2.03:0.67/Sp., Elo-Erwartung +0.98; Europapokal (4 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur +12 Elo; Tempo ×1.01
- **Slavia Praha**: Elo 1750 → 1777; Europapokal (4 Sp.): xG-Residuum +1.09/Sp.; xG-Korrektur +27 Elo
- **Villarreal**: Elo 1789 → 1809; Liga (football-data-xg, 13 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.07; Europapokal (4 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur +21 Elo; Tempo ×1.01
- **Sabah FA**: Elo 1567 → 1550; Europapokal (4 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur -17 Elo
- **Barcelona**: Elo 2035 → 2056; Liga (football-data-xg, 13 Sp.): xG 3.24:1.04/Sp., Elo-Erwartung +1.60; Europapokal (4 Sp.): xG-Residuum -0.34/Sp.; xG-Korrektur +21 Elo; Tempo ×1.09
- **Lille**: Elo 1774 → 1756; Liga (football-data-xg, 11 Sp.): xG 1.28:1.44/Sp., Elo-Erwartung +0.34; Europapokal (4 Sp.): xG-Residuum +0.02/Sp.; xG-Korrektur -19 Elo; Tempo ×0.97
- **Bayern München**: Elo 2040 → 2066; Liga (matchpulse, 10 Sp.): xG 3.22:0.99/Sp., Elo-Erwartung +1.76; Europapokal (4 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur +25 Elo; Tempo ×1.04
- **Paris Saint Germain**: Elo 1991 → 2010; Europapokal (4 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +19 Elo
- **AS Roma**: Elo 1870 → 1876; Liga (football-data-xg, 12 Sp.): xG 2.44:1.34/Sp., Elo-Erwartung +0.73; Europapokal (4 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur +6 Elo; Tempo ×1.05
- **Sporting CP**: Elo 1863 → 1834; Liga (matchpulse, 11 Sp.): xG 1.72:0.82/Sp., Elo-Erwartung +1.60; Europapokal (4 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur -30 Elo; Tempo ×1.00
- **Manchester United**: Elo 1846 → 1835; Liga (football-data-xg, 11 Sp.): xG 1.64:2.01/Sp., Elo-Erwartung -0.00; Europapokal (4 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur -11 Elo; Tempo ×1.05
- **Inter**: Elo 1947 → 1946; Liga (football-data-xg, 12 Sp.): xG 2.68:1.15/Sp., Elo-Erwartung +1.21; Europapokal (4 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -0 Elo; Tempo ×1.05
- **VfB Stuttgart**: Elo 1819 → 1811; Liga (matchpulse, 10 Sp.): xG 1.86:2.02/Sp., Elo-Erwartung +0.36; Europapokal (4 Sp.): xG-Residuum +0.76/Sp.; xG-Korrektur -8 Elo; Tempo ×1.02
- **Atletico Madrid**: Elo 1915 → 1910; Liga (football-data-xg, 13 Sp.): xG 1.81:1.08/Sp., Elo-Erwartung +0.83; Europapokal (4 Sp.): xG-Residuum -0.12/Sp.; xG-Korrektur -6 Elo; Tempo ×1.00
- **Viking**: Elo 1704 → 1690; Liga (matchpulse, 27 Sp.): xG 2.06:1.13/Sp., Elo-Erwartung +1.06; Europapokal (4 Sp.): xG-Residuum -0.76/Sp.; xG-Korrektur -14 Elo; Tempo ×1.00
- **Shakhtar Donetsk**: Elo 1672 → 1700; Europapokal (4 Sp.): xG-Residuum +1.14/Sp.; xG-Korrektur +28 Elo
- **Fenerbahçe**: Elo 1780 → 1769; Liga (matchpulse, 12 Sp.): xG 1.90:1.30/Sp., Elo-Erwartung +0.95; Europapokal (4 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur -11 Elo; Tempo ×1.03
- **Club Brugge KV**: Elo 1842 → 1828; Liga (matchpulse, 12 Sp.): xG 2.34:1.11/Sp., Elo-Erwartung +1.42; Europapokal (4 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur -14 Elo; Tempo ×1.03
- **Liverpool**: Elo 1943 → 1939; Liga (football-data-xg, 11 Sp.): xG 1.83:1.25/Sp., Elo-Erwartung +0.57; Europapokal (4 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -3 Elo; Tempo ×1.01

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 26.11. 18:45 | Marseille – Levski Sofia | 1728 : 1581 | 2.10 : 0.90 | 65 % | 21 % | 15 % | 58 % | 53 % | 67 % / 19 % / 13 % |
| Do 26.11. 18:45 | Celta Vigo – Bournemouth | 1747 : 1920 | 1.09 : 1.66 | 24 % | 26 % | 50 % | 52 % | 54 % | 27 % / 27 % / 46 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | 1741 : 1615 | 1.96 : 0.91 | 61 % | 22 % | 16 % | 55 % | 52 % | 79 % / 13 % / 8 % |
| Do 26.11. 18:45 | Olympiakos Piraeus – AC Milan | 1750 : 1817 | 1.35 : 1.32 | 37 % | 27 % | 36 % | 50 % | 55 % | 34 % / 28 % / 38 % |
| Do 26.11. 18:45 | Plzen – Benfica | 1641 : 1862 | 1.00 : 1.86 | 19 % | 24 % | 57 % | 54 % | 54 % | 16 % / 19 % / 65 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | 1682 : 1440 | 2.53 : 0.73 | 76 % | 16 % | 8 % | 63 % | 48 % | 82 % / 11 % / 7 % |
| Do 26.11. 18:45 | Dinamo Zagreb – Bayer Leverkusen | 1667 : 1869 | 1.02 : 1.77 | 21 % | 24 % | 54 % | 53 % | 54 % | 21 % / 22 % / 56 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | 1816 : 1662 | 2.05 : 0.85 | 65 % | 21 % | 14 % | 56 % | 51 % | 70 % / 17 % / 13 % |
| Do 26.11. 21:00 | Crystal Palace – Real Sociedad | 1769 : 1773 | 1.60 : 1.20 | 46 % | 26 % | 28 % | 53 % | 56 % | 47 % / 24 % / 29 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | 1775 : 1539 | 2.41 : 0.71 | 75 % | 17 % | 9 % | 60 % | 47 % | 81 % / 12 % / 7 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | 1751 : 1625 | 1.95 : 0.91 | 61 % | 22 % | 16 % | 54 % | 52 % | 71 % / 16 % / 13 % |
| Do 26.11. 21:00 | NEC Nijmegen – Rennes | 1591 : 1730 | 1.20 : 1.59 | 28 % | 26 % | 46 % | 53 % | 56 % | 31 % / 24 % / 45 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | 1837 : 1611 | 2.33 : 0.72 | 73 % | 17 % | 9 % | 59 % | 47 % | 81 % / 12 % / 7 % |
| Do 26.11. 21:00 | Sparta Praha – AZ Alkmaar | 1629 : 1709 | 1.32 : 1.37 | 35 % | 27 % | 38 % | 50 % | 55 % | 34 % / 26 % / 40 % |
| Do 26.11. 21:00 | Ferencvarosi TC – Celje | 1690 : 1531 | 2.10 : 0.85 | 66 % | 21 % | 14 % | 57 % | 51 % | 70 % / 18 % / 12 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | 1752 : 1571 | 2.21 : 0.82 | 69 % | 19 % | 12 % | 58 % | 50 % | 77 % / 15 % / 8 % |
| Do 26.11. 21:00 | OFI – Anderlecht | 1503 : 1692 | 1.03 : 1.69 | 23 % | 25 % | 52 % | 51 % | 53 % | 21 % / 25 % / 54 % |
| Do 26.11. 21:00 | Torreense – Celtic | 1447 : 1668 | 1.00 : 1.87 | 19 % | 23 % | 57 % | 55 % | 54 % | 20 % / 23 % / 58 % |

<details><summary>Herleitung je Team</summary>

- **Marseille**: Elo 1769 → 1728; Liga (football-data-xg, 11 Sp.): xG 1.66:2.39/Sp., Elo-Erwartung +0.32; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur -41 Elo; Tempo ×1.05
- **Levski Sofia**: Elo 1588 → 1581; Europapokal (3 Sp.): xG-Residuum -0.38/Sp.; xG-Korrektur -8 Elo
- **Celta Vigo**: Elo 1741 → 1747; Europapokal (4 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur +6 Elo
- **Bournemouth**: Elo 1896 → 1920; Liga (football-data-xg, 11 Sp.): xG 1.90:1.21/Sp., Elo-Erwartung +0.29; Europapokal (3 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +24 Elo; Tempo ×1.01
- **Beşiktaş**: Elo 1709 → 1741; Liga (matchpulse, 12 Sp.): xG 1.94:0.82/Sp., Elo-Erwartung +0.51; Europapokal (3 Sp.): xG-Residuum +0.71/Sp.; xG-Korrektur +32 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1630 → 1615; Europapokal (3 Sp.): xG-Residuum -0.74/Sp.; xG-Korrektur -15 Elo
- **Olympiakos Piraeus**: Elo 1748 → 1750; Liga (football-data-xg, 11 Sp.): xG 1.85:0.81/Sp., Elo-Erwartung +1.30; Europapokal (4 Sp.): xG-Residuum +0.85/Sp.; xG-Korrektur +2 Elo; Tempo ×1.00
- **AC Milan**: Elo 1825 → 1817; Liga (football-data-xg, 12 Sp.): xG 1.76:1.28/Sp., Elo-Erwartung +0.46; Europapokal (4 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur -8 Elo; Tempo ×1.00
- **Plzen**: Elo 1632 → 1641; Europapokal (3 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur +9 Elo
- **Benfica**: Elo 1871 → 1862; Liga (matchpulse, 11 Sp.): xG 2.11:0.85/Sp., Elo-Erwartung +1.66; Europapokal (4 Sp.): xG-Residuum +0.43/Sp.; xG-Korrektur -9 Elo; Tempo ×1.03
- **Red Bull Salzburg**: Elo 1660 → 1682; Liga (matchpulse, 13 Sp.): xG 2.59:1.00/Sp., Elo-Erwartung +0.76; Europapokal (3 Sp.): xG-Residuum -1.43/Sp.; xG-Korrektur +21 Elo; Tempo ×1.03
- **Ararat-Armenia**: Elo 1439 → 1440; Europapokal (3 Sp.): xG-Residuum +0.07/Sp.; xG-Korrektur +1 Elo
- **Dinamo Zagreb**: Elo 1655 → 1667; Europapokal (3 Sp.): xG-Residuum +0.58/Sp.; xG-Korrektur +12 Elo
- **Bayer Leverkusen**: Elo 1866 → 1869; Liga (matchpulse, 10 Sp.): xG 2.06:1.61/Sp., Elo-Erwartung +0.64; Europapokal (4 Sp.): xG-Residuum +0.73/Sp.; xG-Korrektur +3 Elo; Tempo ×1.01
- **Union St. Gilloise**: Elo 1827 → 1816; Liga (matchpulse, 12 Sp.): xG 1.94:0.96/Sp., Elo-Erwartung +1.32; Europapokal (3 Sp.): xG-Residuum +0.27/Sp.; xG-Korrektur -11 Elo; Tempo ×0.99
- **Lech Poznan**: Elo 1678 → 1662; Liga (matchpulse, 13 Sp.): xG 1.90:1.07/Sp., Elo-Erwartung +0.81; Europapokal (3 Sp.): xG-Residuum -1.70/Sp.; xG-Korrektur -16 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1796 → 1769; Liga (football-data-xg, 11 Sp.): xG 1.41:2.18/Sp., Elo-Erwartung -0.20; Europapokal (3 Sp.): xG-Residuum -0.49/Sp.; xG-Korrektur -28 Elo; Tempo ×1.04
- **Real Sociedad**: Elo 1785 → 1773; Liga (football-data-xg, 13 Sp.): xG 1.59:1.76/Sp., Elo-Erwartung +0.05; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **Lyon**: Elo 1790 → 1775; Liga (football-data-xg, 11 Sp.): xG 1.44:1.20/Sp., Elo-Erwartung +0.44; Europapokal (4 Sp.): xG-Residuum -0.50/Sp.; xG-Korrektur -15 Elo; Tempo ×0.96
- **Lillestrom**: Elo 1536 → 1539; Liga (matchpulse, 27 Sp.): xG 1.55:1.50/Sp., Elo-Erwartung +0.05; Europapokal (3 Sp.): xG-Residuum +0.46/Sp.; xG-Korrektur +3 Elo; Tempo ×0.99
- **1899 Hoffenheim**: Elo 1733 → 1751; Liga (matchpulse, 10 Sp.): xG 1.86:1.49/Sp., Elo-Erwartung -0.05; Europapokal (3 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur +19 Elo; Tempo ×0.99
- **Sturm Graz**: Elo 1631 → 1625; Liga (matchpulse, 13 Sp.): xG 1.74:1.38/Sp., Elo-Erwartung +0.58; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur -6 Elo; Tempo ×1.00
- **NEC Nijmegen**: Elo 1599 → 1591; Liga (matchpulse, 13 Sp.): xG 1.70:1.84/Sp., Elo-Erwartung +0.17; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur -8 Elo; Tempo ×1.01
- **Rennes**: Elo 1745 → 1730; Liga (football-data-xg, 11 Sp.): xG 1.96:2.07/Sp., Elo-Erwartung +0.17; Europapokal (3 Sp.): xG-Residuum -0.34/Sp.; xG-Korrektur -15 Elo; Tempo ×1.05
- **Juventus**: Elo 1833 → 1837; Liga (football-data-xg, 12 Sp.): xG 1.50:0.74/Sp., Elo-Erwartung +0.51; Europapokal (3 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur +4 Elo; Tempo ×0.93
- **Omonia Nicosia**: Elo 1636 → 1611; Europapokal (4 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -25 Elo
- **Sparta Praha**: Elo 1637 → 1629; Europapokal (3 Sp.): xG-Residuum -0.42/Sp.; xG-Korrektur -8 Elo
- **AZ Alkmaar**: Elo 1686 → 1709; Liga (matchpulse, 13 Sp.): xG 2.28:1.27/Sp., Elo-Erwartung +0.69; Europapokal (4 Sp.): xG-Residuum +0.79/Sp.; xG-Korrektur +23 Elo; Tempo ×1.01
- **Ferencvarosi TC**: Elo 1678 → 1690; Europapokal (3 Sp.): xG-Residuum +0.62/Sp.; xG-Korrektur +12 Elo
- **Celje**: Elo 1526 → 1531; Europapokal (4 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +6 Elo
- **Sunderland**: Elo 1732 → 1752; Liga (football-data-xg, 11 Sp.): xG 1.44:1.58/Sp., Elo-Erwartung -0.58; Europapokal (4 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur +20 Elo; Tempo ×1.00
- **Jagiellonia**: Elo 1581 → 1571; Liga (matchpulse, 13 Sp.): xG 1.65:1.56/Sp., Elo-Erwartung +0.23; Europapokal (4 Sp.): xG-Residuum -0.33/Sp.; xG-Korrektur -10 Elo; Tempo ×1.01
- **OFI**: Elo 1501 → 1503; Liga (football-data-xg, 11 Sp.): xG 1.26:1.30/Sp., Elo-Erwartung -0.11; Europapokal (3 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur +1 Elo; Tempo ×1.00
- **Anderlecht**: Elo 1675 → 1692; Liga (matchpulse, 12 Sp.): xG 1.71:1.02/Sp., Elo-Erwartung +0.38; Europapokal (4 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur +17 Elo; Tempo ×0.98
- **Torreense**: Elo 1452 → 1447; Europapokal (3 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -5 Elo
- **Celtic**: Elo 1660 → 1668; Liga (matchpulse, 14 Sp.): xG 2.65:1.19/Sp., Elo-Erwartung +1.21; Europapokal (3 Sp.): xG-Residuum -0.29/Sp.; xG-Korrektur +8 Elo; Tempo ×1.04

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 26.11. 16:30 | Kairat Almaty – Mjallby AIF | 1445 : 1508 | 1.31 : 1.26 | 37 % | 28 % | 35 % | 47 % | 53 % | 40 % / 28 % / 32 % |
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | 1901 : 1612 | 2.66 : 0.63 | 80 % | 14 % | 6 % | 64 % | 44 % | 83 % / 11 % / 6 % |
| Do 26.11. 18:45 | Ajax – FC Thun | 1720 : 1527 | 2.13 : 0.75 | 69 % | 20 % | 11 % | 55 % | 47 % | 81 % / 11 % / 8 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | 1540 : 1768 | 0.90 : 1.73 | 19 % | 25 % | 56 % | 49 % | 49 % | 20 % / 23 % / 57 % |
| Do 26.11. 18:45 | Brann – Aarhus | 1563 : 1590 | 1.41 : 1.17 | 42 % | 28 % | 31 % | 48 % | 53 % | 45 % / 24 % / 31 % |
| Do 26.11. 18:45 | FK Jablonec – FC Lugano | 1558 : 1654 | 1.20 : 1.33 | 33 % | 28 % | 39 % | 46 % | 52 % | 29 % / 25 % / 46 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | 1434 : 1378 | 1.61 : 1.01 | 51 % | 26 % | 23 % | 49 % | 51 % | 60 % / 22 % / 18 % |
| Do 26.11. 18:45 | Pafos – FC Midtjylland | 1561 : 1673 | 1.17 : 1.38 | 31 % | 28 % | 41 % | 47 % | 52 % | 32 % / 27 % / 41 % |
| Do 26.11. 18:45 | FC Iberia 1999 – Getafe | 1387 : 1659 | 0.81 : 1.88 | 15 % | 23 % | 62 % | 51 % | 48 % | 14 % / 23 % / 63 % |
| Do 26.11. 18:45 | Kauno Žalgiris – Riga | 1387 : 1506 | 1.15 : 1.41 | 30 % | 28 % | 42 % | 47 % | 52 % | 27 % / 29 % / 44 % |
| Do 26.11. 21:00 | SC Freiburg – Twente | 1805 : 1748 | 1.57 : 0.98 | 50 % | 27 % | 23 % | 47 % | 50 % | 45 % / 24 % / 31 % |
| Do 26.11. 21:00 | SC Braga – KuPS | 1720 : 1465 | 2.39 : 0.65 | 76 % | 16 % | 8 % | 59 % | 44 % | 84 % / 11 % / 5 % |
| Do 26.11. 21:00 | FC Nordsjaelland – Panathinaikos | 1644 : 1714 | 1.31 : 1.30 | 36 % | 28 % | 36 % | 49 % | 54 % | 35 % / 27 % / 38 % |
| Do 26.11. 21:00 | HNK Hajduk Split – St. Truiden | 1605 : 1628 | 1.43 : 1.16 | 43 % | 27 % | 30 % | 48 % | 53 % | 44 % / 27 % / 29 % |
| Do 26.11. 21:00 | Gent – FK Crvena Zvezda | 1646 : 1676 | 1.35 : 1.13 | 41 % | 28 % | 31 % | 45 % | 51 % | 43 % / 27 % / 30 % |
| Do 26.11. 21:00 | CSKA Sofia – Trabzonspor | 1553 : 1703 | 1.11 : 1.54 | 27 % | 27 % | 47 % | 49 % | 53 % | 24 % / 25 % / 50 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | 1486 : 1671 | 0.98 : 1.58 | 23 % | 26 % | 51 % | 47 % | 50 % | 11 % / 17 % / 72 % |
| Do 26.11. 21:00 | Borac Banja Luka – Atalanta | 1473 : 1754 | 0.84 : 2.00 | 14 % | 22 % | 64 % | 54 % | 49 % | 18 % / 20 % / 62 % |

<details><summary>Herleitung je Team</summary>

- **Kairat Almaty**: Elo 1444 → 1445; Europapokal (3 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur +1 Elo
- **Mjallby AIF**: Elo 1518 → 1508; Liga (matchpulse, 29 Sp.): xG 1.42:1.63/Sp., Elo-Erwartung +0.04; Europapokal (3 Sp.): xG-Residuum +0.81/Sp.; xG-Korrektur -10 Elo; Tempo ×1.02
- **Brighton**: Elo 1896 → 1901; Liga (football-data-xg, 11 Sp.): xG 1.96:1.40/Sp., Elo-Erwartung +0.30; Europapokal (3 Sp.): xG-Residuum -0.54/Sp.; xG-Korrektur +4 Elo; Tempo ×1.03
- **Universitatea Craiova**: Elo 1607 → 1612; Europapokal (3 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur +5 Elo
- **Ajax**: Elo 1719 → 1720; Liga (matchpulse, 12 Sp.): xG 2.12:1.36/Sp., Elo-Erwartung +0.89; Europapokal (3 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur +1 Elo; Tempo ×1.00
- **FC Thun**: Elo 1550 → 1527; Liga (matchpulse, 14 Sp.): xG 1.32:1.86/Sp., Elo-Erwartung +0.01; Europapokal (3 Sp.): xG-Residuum +0.21/Sp.; xG-Korrektur -22 Elo; Tempo ×0.98
- **Heart Of Midlothian**: Elo 1534 → 1540; Liga (matchpulse, 13 Sp.): xG 1.85:1.40/Sp., Elo-Erwartung +0.44; Europapokal (3 Sp.): xG-Residuum +0.52/Sp.; xG-Korrektur +5 Elo; Tempo ×1.00
- **Monaco**: Elo 1787 → 1768; Liga (football-data-xg, 11 Sp.): xG 1.27:1.27/Sp., Elo-Erwartung +0.42; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -19 Elo; Tempo ×0.96
- **Brann**: Elo 1583 → 1563; Liga (matchpulse, 27 Sp.): xG 1.64:1.73/Sp., Elo-Erwartung +0.32; Europapokal (3 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur -20 Elo; Tempo ×1.02
- **Aarhus**: Elo 1601 → 1590; Liga (matchpulse, 15 Sp.): xG 1.56:1.45/Sp., Elo-Erwartung +0.21; Europapokal (3 Sp.): xG-Residuum -0.63/Sp.; xG-Korrektur -11 Elo; Tempo ×1.00
- **FK Jablonec**: Elo 1540 → 1558; Europapokal (3 Sp.): xG-Residuum +0.96/Sp.; xG-Korrektur +19 Elo
- **FC Lugano**: Elo 1669 → 1654; Liga (matchpulse, 14 Sp.): xG 1.87:1.31/Sp., Elo-Erwartung +0.72; Europapokal (3 Sp.): xG-Residuum -0.79/Sp.; xG-Korrektur -15 Elo; Tempo ×0.98
- **Egnatia Rrogozhinë**: Elo 1432 → 1434; Europapokal (3 Sp.): xG-Residuum +0.11/Sp.; xG-Korrektur +2 Elo
- **Lincoln Red Imps FC**: Elo 1402 → 1378; Europapokal (3 Sp.): xG-Residuum -1.21/Sp.; xG-Korrektur -24 Elo
- **Pafos**: Elo 1580 → 1561; Europapokal (3 Sp.): xG-Residuum -0.96/Sp.; xG-Korrektur -19 Elo
- **FC Midtjylland**: Elo 1700 → 1673; Liga (matchpulse, 15 Sp.): xG 1.71:1.29/Sp., Elo-Erwartung +0.80; Europapokal (3 Sp.): xG-Residuum -0.97/Sp.; xG-Korrektur -27 Elo; Tempo ×1.00
- **FC Iberia 1999**: Elo 1383 → 1387; Europapokal (3 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur +4 Elo
- **Getafe**: Elo 1670 → 1659; Liga (football-data-xg, 13 Sp.): xG 0.70:1.60/Sp., Elo-Erwartung -0.53; Europapokal (3 Sp.): xG-Residuum +0.44/Sp.; xG-Korrektur -12 Elo; Tempo ×0.95
- **Kauno Žalgiris**: Elo 1384 → 1387; Europapokal (3 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur +3 Elo
- **Riga**: Elo 1499 → 1506; Europapokal (3 Sp.): xG-Residuum +0.38/Sp.; xG-Korrektur +7 Elo
- **SC Freiburg**: Elo 1799 → 1805; Liga (matchpulse, 10 Sp.): xG 1.66:1.05/Sp., Elo-Erwartung +0.25; Europapokal (3 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur +6 Elo; Tempo ×0.95
- **Twente**: Elo 1690 → 1748; Liga (matchpulse, 13 Sp.): xG 2.52:0.87/Sp., Elo-Erwartung +0.72; Europapokal (3 Sp.): xG-Residuum +1.82/Sp.; xG-Korrektur +58 Elo; Tempo ×1.00
- **SC Braga**: Elo 1711 → 1720; Liga (matchpulse, 11 Sp.): xG 1.41:0.65/Sp., Elo-Erwartung +0.64; Europapokal (3 Sp.): xG-Residuum +0.41/Sp.; xG-Korrektur +9 Elo; Tempo ×0.96
- **KuPS**: Elo 1468 → 1465; Europapokal (3 Sp.): xG-Residuum -0.17/Sp.; xG-Korrektur -3 Elo
- **FC Nordsjaelland**: Elo 1638 → 1644; Liga (matchpulse, 15 Sp.): xG 2.09:1.24/Sp., Elo-Erwartung +0.43; Europapokal (3 Sp.): xG-Residuum -1.49/Sp.; xG-Korrektur +5 Elo; Tempo ×1.03
- **Panathinaikos**: Elo 1681 → 1714; Liga (football-data-xg, 11 Sp.): xG 2.23:0.77/Sp., Elo-Erwartung +0.87; Europapokal (3 Sp.): xG-Residuum +0.96/Sp.; xG-Korrektur +34 Elo; Tempo ×1.03
- **HNK Hajduk Split**: Elo 1602 → 1605; Europapokal (3 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur +3 Elo
- **St. Truiden**: Elo 1623 → 1628; Liga (matchpulse, 12 Sp.): xG 1.85:1.65/Sp., Elo-Erwartung +0.08; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur +5 Elo; Tempo ×1.03
- **Gent**: Elo 1638 → 1646; Liga (matchpulse, 12 Sp.): xG 1.39:0.97/Sp., Elo-Erwartung +0.16; Europapokal (3 Sp.): xG-Residuum -0.20/Sp.; xG-Korrektur +8 Elo; Tempo ×0.95
- **FK Crvena Zvezda**: Elo 1669 → 1676; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur +7 Elo
- **CSKA Sofia**: Elo 1526 → 1553; Europapokal (3 Sp.): xG-Residuum +1.39/Sp.; xG-Korrektur +28 Elo
- **Trabzonspor**: Elo 1701 → 1703; Liga (matchpulse, 12 Sp.): xG 2.02:1.50/Sp., Elo-Erwartung +0.47; Europapokal (3 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur +3 Elo; Tempo ×1.05
- **Inter Club d'Escaldes**: Elo 1504 → 1486; Europapokal (3 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur -19 Elo
- **FC Copenhagen**: Elo 1684 → 1671; Liga (matchpulse, 15 Sp.): xG 1.51:1.01/Sp., Elo-Erwartung +0.71; Europapokal (3 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur -13 Elo; Tempo ×0.96
- **Borac Banja Luka**: Elo 1491 → 1473; Europapokal (3 Sp.): xG-Residuum -0.91/Sp.; xG-Korrektur -18 Elo
- **Atalanta**: Elo 1779 → 1754; Liga (football-data-xg, 12 Sp.): xG 1.63:1.96/Sp., Elo-Erwartung +0.19; Europapokal (3 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur -25 Elo; Tempo ×1.03

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 88 Spiele ausgewertet, Log-Loss 1X2 Modell 0.983
- Gegen Pinnacle (88 Spiele): Modell 0.983 vs. Pinnacle 0.962 (kleiner = besser)
- Value-Wetten: 115, Ergebnis +5.01 Einheiten, ROI +4.4 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
