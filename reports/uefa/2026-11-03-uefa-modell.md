# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 03.11.2026 07:49 (Wien), Spiele 03.11. bis 05.11.2026

## Datenbasis
- Elo: **eigene Elo-Rechnung** (ClubElo von GitHub aus gesperrt), verankert an ClubElo vom 24.10.2026 (205 Teams), seither 823 Spiele eingerechnet
- Ergebnisbasis: 39109 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1152 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-230 Elo, 2 Sp.), Estonia (-225 Elo, 2 Sp.), Gibraltar (-395 Elo, 48 Sp.), Hungary (-170 Elo, 4 Sp.), Iceland (-170 Elo, 4 Sp.), San-Marino (-500 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 771 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.732 (×0.87 ggü. ClubElo-Erwartung, 197 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 96 Elo, Heimteam Außenseiter 60 Elo (reiner Fit 105 / 60, Steigung ×0.84, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 77 Teams, Europapokal-xG aus 132 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 243 | 3.59 | 2.99 | ×1.124 | 52 % |
| Conference League | 285 | 2.62 | 2.96 | ×0.924 | 47 % |
| Europa League | 243 | 2.77 | 2.94 | ×0.965 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 383 | 67.6 % | 63.5 % |
| Heimteam Außenseiter | 385 | 30.4 % | 29.5 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 5 % | 3 % | 34.00 | +85.4 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 10 % | 7 % | 15.00 | +54.3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1 | 13 % | 12 % | 11.00 | +46.9 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1 | 15 % | 9 % | 9.50 | +42.8 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 18 % | 13 % | 8.00 | +41.7 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 13 % | 7 % | 11.00 | +41.5 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 34 % | 23 % | 4.20 | +41.0 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 33 % | 24 % | 4.20 | +38.4 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | U2.5 | 39 % | 29 % | 3.50 | +37.9 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1 | 26 % | 18 % | 5.25 | +35.8 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1 | 24 % | 17 % | 5.50 | +34.7 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | U2.5 | 30 % | – | 4.50 | +34.4 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | U2.5 | 38 % | 30 % | 3.40 | +29.5 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1 | 14 % | 9 % | 9.00 | +29.0 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | X | 18 % | 13 % | 7.00 | +28.9 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | U2.5 | 47 % | 35 % | 2.70 | +28.2 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | U2.5 | 53 % | 38 % | 2.40 | +27.5 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 52 % | 38 % | 2.40 | +25.6 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | U2.5 | 37 % | 28 % | 3.40 | +25.4 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 19 % | 15 % | 6.50 | +24.3 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 2 | 54 % | 39 % | 2.30 | +24.2 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 2 | 33 % | 26 % | 3.80 | +23.8 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | U2.5 | 35 % | 27 % | 3.50 | +22.9 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 38 % | 31 % | 3.20 | +22.7 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | X | 20 % | 17 % | 6.00 | +22.4 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | X | 19 % | 15 % | 6.25 | +21.3 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 39 % | 30 % | 3.10 | +20.9 % |
| Do 05.11. 21:00 | Twente – Pafos | U2.5 | 45 % | 35 % | 2.70 | +20.7 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 19 % | 16 % | 6.25 | +20.5 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 20 % | 17 % | 6.00 | +20.1 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 2 | 17 % | 14 % | 7.00 | +20.1 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 50 % | 39 % | 2.38 | +19.9 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 48 % | 38 % | 2.50 | +19.9 % |
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1 | 32 % | 27 % | 3.70 | +19.8 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 50 % | 39 % | 2.38 | +19.5 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 34 % | 2.75 | +19.0 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 50 % | 40 % | 2.38 | +18.9 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | X | 17 % | 13 % | 7.00 | +18.8 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 22 % | 18 % | 5.50 | +18.6 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 25 % | 22 % | 4.75 | +17.4 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | U2.5 | 37 % | 30 % | 3.20 | +17.4 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | U2.5 | 37 % | 30 % | 3.20 | +17.1 % |
| Mi 04.11. 21:00 | Lens – Como | 1 | 39 % | 32 % | 3.00 | +17.0 % |
| Do 05.11. 21:00 | St. Truiden – Brann | U2.5 | 48 % | 39 % | 2.40 | +16.4 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 49 % | 40 % | 2.38 | +15.6 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 2 | 38 % | 32 % | 3.00 | +14.1 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 24 % | 4.20 | +13.9 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | U2.5 | 35 % | 30 % | 3.20 | +13.5 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 49 % | 41 % | 2.30 | +13.3 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | U2.5 | 32 % | 27 % | 3.50 | +13.0 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 23 % | 21 % | 4.75 | +11.6 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 22 % | 20 % | 5.00 | +11.0 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +10.0 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 2 | 35 % | 31 % | 3.10 | +9.7 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | X | 23 % | 20 % | 4.75 | +9.6 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | 1 | 51 % | 44 % | 2.15 | +9.4 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | X | 23 % | 20 % | 4.75 | +9.4 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | U2.5 | 50 % | 44 % | 2.20 | +9.2 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | O2.5 | 63 % | 55 % | 1.73 | +9.0 % |
| Di 03.11. 21:00 | Feyenoord – Inter | U2.5 | 36 % | 32 % | 3.00 | +8.5 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 22 % | 20 % | 5.00 | +7.9 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 38 % | 2.50 | +7.5 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 2 | 13 % | 11 % | 8.00 | +7.4 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | X | 24 % | 22 % | 4.33 | +6.0 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 39 % | 35 % | 2.70 | +5.8 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 2 | 40 % | 37 % | 2.62 | +5.6 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | U2.5 | 37 % | 31 % | 2.88 | +5.4 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | U2.5 | 46 % | 43 % | 2.30 | +5.3 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 2 | 36 % | 32 % | 2.90 | +5.1 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | X | 21 % | 20 % | 5.00 | +5.1 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- FC Midtjylland – Ajax: U2.5 Modell 52 % vs. Pinnacle 37 %
- Hapoel Beer Sheva – OFI: 1 Modell 63 % vs. Pinnacle 45 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1720 : 1823 | 1.44 : 1.69 | 32 % | 25 % | 43 % | 61 % | 63 % | 27 % / 25 % / 48 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | 1815 : 1809 | 1.93 : 1.33 | 51 % | 23 % | 26 % | 63 % | 63 % | 44 % / 23 % / 33 % |
| Di 03.11. 21:00 | Manchester United – AS Roma | 1816 : 1861 | 1.65 : 1.56 | 40 % | 24 % | 36 % | 62 % | 64 % | 42 % / 24 % / 34 % |
| Di 03.11. 21:00 | Feyenoord – Inter | 1767 : 1930 | 1.34 : 1.95 | 26 % | 23 % | 51 % | 64 % | 64 % | 25 % / 23 % / 52 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 1775 : 1750 | 1.95 : 1.25 | 53 % | 23 % | 24 % | 62 % | 62 % | 53 % / 23 % / 24 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | 2037 : 1881 | 2.59 : 1.03 | 71 % | 17 % | 12 % | 70 % | 60 % | 76 % / 13 % / 11 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 1893 : 2079 | 1.26 : 2.00 | 23 % | 23 % | 54 % | 63 % | 62 % | 35 % / 25 % / 39 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | 1806 : 2011 | 1.20 : 2.05 | 22 % | 22 % | 56 % | 63 % | 61 % | 22 % / 21 % / 57 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 1637 : 1540 | 2.23 : 1.10 | 62 % | 20 % | 17 % | 65 % | 60 % | 69 % / 17 % / 14 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1706 : 1994 | 1.06 : 2.43 | 14 % | 18 % | 67 % | 68 % | 60 % | 9 % / 13 % / 78 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1748 : 1923 | 1.28 : 1.94 | 24 % | 23 % | 52 % | 62 % | 62 % | 17 % / 20 % / 62 % |
| Mi 04.11. 21:00 | Lens – Como | 1784 : 1833 | 1.60 : 1.53 | 39 % | 25 % | 36 % | 60 % | 63 % | 32 % / 24 % / 45 % |
| Mi 04.11. 21:00 | Borussia Dortmund – Real Betis | 1861 : 1794 | 2.12 : 1.17 | 59 % | 21 % | 20 % | 64 % | 61 % | 55 % / 23 % / 22 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1833 : 1995 | 1.33 : 1.94 | 26 % | 23 % | 51 % | 63 % | 63 % | 18 % / 20 % / 62 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 1765 : 1828 | 1.59 : 1.60 | 37 % | 24 % | 38 % | 62 % | 64 % | 47 % / 22 % / 32 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 1818 : 1792 | 1.98 : 1.27 | 53 % | 23 % | 24 % | 63 % | 62 % | 49 % / 25 % / 26 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1765 : 2045 | 1.03 : 2.30 | 15 % | 19 % | 66 % | 65 % | 58 % | 9 % / 15 % / 76 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 1685 : 1536 | 2.44 : 1.00 | 69 % | 18 % | 13 % | 67 % | 58 % | – |

<details><summary>Herleitung je Team</summary>

- **Shakhtar Donetsk**: Elo 1695 → 1720; Europapokal (3 Sp.): xG-Residuum +1.08/Sp.; xG-Korrektur +25 Elo
- **Sporting CP**: Elo 1856 → 1823; Liga (matchpulse, 10 Sp.): xG 1.70:0.85/Sp., Elo-Erwartung +1.54; Europapokal (3 Sp.): xG-Residuum -0.24/Sp.; xG-Korrektur -33 Elo; Tempo ×1.00
- **Galatasaray**: Elo 1821 → 1815; Liga (matchpulse, 10 Sp.): xG 2.27:0.93/Sp., Elo-Erwartung +1.50; Europapokal (3 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -7 Elo; Tempo ×1.03
- **VfB Stuttgart**: Elo 1840 → 1809; Liga (matchpulse, 8 Sp.): xG 1.94:2.13/Sp., Elo-Erwartung +0.86; Europapokal (3 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur -31 Elo; Tempo ×1.03
- **Manchester United**: Elo 1829 → 1816; Liga (football-data-xg, 9 Sp.): xG 1.53:1.66/Sp., Elo-Erwartung +0.10; Europapokal (3 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -13 Elo; Tempo ×1.02
- **AS Roma**: Elo 1871 → 1861; Liga (football-data-xg, 10 Sp.): xG 2.26:1.37/Sp., Elo-Erwartung +1.02; Europapokal (3 Sp.): xG-Residuum -0.32/Sp.; xG-Korrektur -10 Elo; Tempo ×1.03
- **Feyenoord**: Elo 1731 → 1767; Liga (matchpulse, 11 Sp.): xG 2.89:1.07/Sp., Elo-Erwartung +1.08; Europapokal (3 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur +36 Elo; Tempo ×1.03
- **Inter**: Elo 1931 → 1930; Liga (football-data-xg, 10 Sp.): xG 2.70:1.06/Sp., Elo-Erwartung +1.36; Europapokal (3 Sp.): xG-Residuum -0.99/Sp.; xG-Korrektur -1 Elo; Tempo ×1.04
- **Bodo/Glimt**: Elo 1774 → 1775; Liga (matchpulse, 25 Sp.): xG 2.38:0.96/Sp., Elo-Erwartung +1.46; Europapokal (3 Sp.): xG-Residuum +0.42/Sp.; xG-Korrektur +1 Elo; Tempo ×1.02
- **Lille**: Elo 1779 → 1750; Liga (football-data-xg, 9 Sp.): xG 1.41:1.49/Sp., Elo-Erwartung +0.59; Europapokal (3 Sp.): xG-Residuum -0.15/Sp.; xG-Korrektur -29 Elo; Tempo ×0.98
- **Barcelona**: Elo 2021 → 2037; Liga (football-data-xg, 11 Sp.): xG 3.39:1.06/Sp., Elo-Erwartung +1.81; Europapokal (3 Sp.): xG-Residuum -0.58/Sp.; xG-Korrektur +16 Elo; Tempo ×1.10
- **Aston Villa**: Elo 1912 → 1881; Liga (football-data-xg, 9 Sp.): xG 1.20:1.68/Sp., Elo-Erwartung +0.54; Europapokal (3 Sp.): xG-Residuum +0.72/Sp.; xG-Korrektur -31 Elo; Tempo ×1.00
- **Atletico Madrid**: Elo 1926 → 1893; Liga (football-data-xg, 11 Sp.): xG 1.61:1.09/Sp., Elo-Erwartung +1.25; Europapokal (3 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -33 Elo; Tempo ×0.99
- **Bayern München**: Elo 2042 → 2079; Liga (matchpulse, 8 Sp.): xG 3.59:0.91/Sp., Elo-Erwartung +2.03; Europapokal (3 Sp.): xG-Residuum +0.89/Sp.; xG-Korrektur +37 Elo; Tempo ×1.05
- **Villarreal**: Elo 1791 → 1806; Liga (football-data-xg, 11 Sp.): xG 1.97:1.09/Sp., Elo-Erwartung +0.52; Europapokal (3 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur +15 Elo; Tempo ×1.01
- **Paris Saint Germain**: Elo 1987 → 2011; Europapokal (3 Sp.): xG-Residuum +1.06/Sp.; xG-Korrektur +24 Elo
- **Lask Linz**: Elo 1627 → 1637; Liga (matchpulse, 11 Sp.): xG 2.16:1.12/Sp., Elo-Erwartung +0.76; Europapokal (3 Sp.): xG-Residuum -0.18/Sp.; xG-Korrektur +10 Elo; Tempo ×1.00
- **Slovan Bratislava**: Elo 1556 → 1540; Europapokal (3 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -17 Elo
- **AEK Athens FC**: Elo 1690 → 1706; Liga (football-data-xg, 8 Sp.): xG 2.09:0.73/Sp., Elo-Erwartung +1.00; Europapokal (3 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur +16 Elo; Tempo ×1.01
- **Real Madrid**: Elo 2001 → 1994; Liga (football-data-xg, 11 Sp.): xG 2.48:1.01/Sp., Elo-Erwartung +1.69; Europapokal (3 Sp.): xG-Residuum +0.19/Sp.; xG-Korrektur -8 Elo; Tempo ×1.04
- **Fenerbahçe**: Elo 1757 → 1748; Liga (matchpulse, 10 Sp.): xG 2.09:1.21/Sp., Elo-Erwartung +1.13; Europapokal (3 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur -9 Elo; Tempo ×1.03
- **Liverpool**: Elo 1942 → 1923; Liga (football-data-xg, 9 Sp.): xG 1.46:1.17/Sp., Elo-Erwartung +0.69; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -19 Elo; Tempo ×0.98
- **Lens**: Elo 1802 → 1784; Liga (football-data-xg, 9 Sp.): xG 1.69:1.49/Sp., Elo-Erwartung +0.71; Europapokal (3 Sp.): xG-Residuum +0.14/Sp.; xG-Korrektur -18 Elo; Tempo ×1.00
- **Como**: Elo 1834 → 1833; Liga (football-data-xg, 10 Sp.): xG 1.86:1.25/Sp., Elo-Erwartung +0.82; Europapokal (3 Sp.): xG-Residuum +0.64/Sp.; xG-Korrektur -1 Elo; Tempo ×1.00
- **Borussia Dortmund**: Elo 1897 → 1861; Liga (matchpulse, 8 Sp.): xG 1.55:1.48/Sp., Elo-Erwartung +1.17; Europapokal (3 Sp.): xG-Residuum +0.38/Sp.; xG-Korrektur -36 Elo; Tempo ×0.98
- **Real Betis**: Elo 1827 → 1794; Liga (football-data-xg, 11 Sp.): xG 1.61:1.82/Sp., Elo-Erwartung +0.71; Europapokal (3 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur -34 Elo; Tempo ×1.04
- **RB Leipzig**: Elo 1830 → 1833; Liga (matchpulse, 8 Sp.): xG 2.48:1.60/Sp., Elo-Erwartung +0.81; Europapokal (3 Sp.): xG-Residuum +0.06/Sp.; xG-Korrektur +3 Elo; Tempo ×1.03
- **Manchester City**: Elo 2000 → 1995; Liga (football-data-xg, 9 Sp.): xG 2.07:1.27/Sp., Elo-Erwartung +1.01; Europapokal (3 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur -5 Elo; Tempo ×1.03
- **PSV Eindhoven**: Elo 1782 → 1765; Liga (matchpulse, 11 Sp.): xG 2.38:1.31/Sp., Elo-Erwartung +1.37; Europapokal (3 Sp.): xG-Residuum -0.29/Sp.; xG-Korrektur -17 Elo; Tempo ×1.01
- **Club Brugge KV**: Elo 1842 → 1828; Liga (matchpulse, 10 Sp.): xG 2.44:1.15/Sp., Elo-Erwartung +1.54; Europapokal (3 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -14 Elo; Tempo ×1.03
- **FC Porto**: Elo 1835 → 1818; Liga (matchpulse, 10 Sp.): xG 2.21:0.83/Sp., Elo-Erwartung +1.42; Europapokal (3 Sp.): xG-Residuum -1.16/Sp.; xG-Korrektur -17 Elo; Tempo ×1.03
- **Napoli**: Elo 1817 → 1792; Liga (football-data-xg, 10 Sp.): xG 1.74:1.28/Sp., Elo-Erwartung +0.74; Europapokal (3 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -25 Elo; Tempo ×1.00
- **Slavia Praha**: Elo 1752 → 1765; Europapokal (3 Sp.): xG-Residuum +0.54/Sp.; xG-Korrektur +12 Elo
- **Arsenal (England)**: Elo 2062 → 2045; Liga (football-data-xg, 9 Sp.): xG 1.65:0.80/Sp., Elo-Erwartung +1.35; Europapokal (3 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur -16 Elo; Tempo ×0.97
- **Viking**: Elo 1706 → 1685; Liga (matchpulse, 25 Sp.): xG 2.00:1.12/Sp., Elo-Erwartung +1.07; Europapokal (3 Sp.): xG-Residuum -1.04/Sp.; xG-Korrektur -21 Elo; Tempo ×1.00
- **Sabah FA**: Elo 1557 → 1536; Europapokal (3 Sp.): xG-Residuum -0.95/Sp.; xG-Korrektur -21 Elo

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 16:30 | Rennes – Olympiakos Piraeus | 1719 : 1745 | 1.47 : 1.29 | 41 % | 27 % | 33 % | 52 % | 56 % | 42 % / 27 % / 31 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1757 : 1734 | 1.67 : 1.08 | 51 % | 25 % | 24 % | 52 % | 54 % | 49 % / 24 % / 27 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1540 : 1622 | 1.28 : 1.38 | 34 % | 27 % | 39 % | 50 % | 55 % | 33 % / 25 % / 42 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1574 : 1609 | 1.40 : 1.28 | 39 % | 27 % | 34 % | 50 % | 55 % | 53 % / 24 % / 23 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1818 : 1664 | 2.12 : 0.85 | 66 % | 20 % | 13 % | 57 % | 51 % | 71 % / 17 % / 11 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1746 : 1776 | 1.41 : 1.26 | 40 % | 27 % | 33 % | 50 % | 55 % | 52 % / 24 % / 24 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1669 : 1694 | 1.44 : 1.27 | 41 % | 27 % | 33 % | 51 % | 55 % | 49 % / 25 % / 26 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1628 : 1913 | 0.89 : 2.02 | 15 % | 22 % | 63 % | 56 % | 52 % | 16 % / 21 % / 63 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1591 : 1568 | 1.67 : 1.08 | 50 % | 25 % | 24 % | 52 % | 54 % | 48 % / 27 % / 26 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1836 : 1716 | 2.04 : 0.92 | 63 % | 22 % | 16 % | 57 % | 53 % | 68 % / 18 % / 14 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1682 : 1828 | 1.09 : 1.50 | 27 % | 27 % | 46 % | 48 % | 52 % | 26 % / 25 % / 49 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1867 : 1662 | 2.35 : 0.78 | 72 % | 18 % | 10 % | 61 % | 49 % | 79 % / 13 % / 7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1676 : 1721 | 1.40 : 1.33 | 38 % | 27 % | 35 % | 51 % | 56 % | 31 % / 25 % / 44 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1754 : 1804 | 1.37 : 1.32 | 38 % | 27 % | 35 % | 50 % | 55 % | 43 % / 26 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1631 : 1500 | 2.03 : 0.89 | 63 % | 21 % | 15 % | 56 % | 52 % | 45 % / 26 % / 29 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1623 : 1528 | 1.89 : 0.94 | 59 % | 23 % | 18 % | 54 % | 52 % | 62 % / 21 % / 17 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1738 : 1660 | 1.86 : 0.99 | 57 % | 23 % | 19 % | 54 % | 54 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1456 : 1441 | 1.64 : 1.09 | 50 % | 26 % | 25 % | 52 % | 54 % | 53 % / 24 % / 22 % |

<details><summary>Herleitung je Team</summary>

- **Rennes**: Elo 1748 → 1719; Liga (football-data-xg, 9 Sp.): xG 2.09:2.33/Sp., Elo-Erwartung +0.42; Europapokal (2 Sp.): xG-Residuum -0.02/Sp.; xG-Korrektur -28 Elo; Tempo ×1.06
- **Olympiakos Piraeus**: Elo 1745 → 1745; Liga (football-data-xg, 9 Sp.): xG 1.78:0.72/Sp., Elo-Erwartung +1.31; Europapokal (3 Sp.): xG-Residuum +0.69/Sp.; xG-Korrektur -1 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1787 → 1757; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung -0.29; Europapokal (2 Sp.): xG-Residuum -0.46/Sp.; xG-Korrektur -30 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1724 → 1734; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung +0.25; Europapokal (2 Sp.): xG-Residuum -0.15/Sp.; xG-Korrektur +10 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1541 → 1540; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung +0.20; Europapokal (2 Sp.): xG-Residuum +1.12/Sp.; xG-Korrektur -1 Elo; Tempo ×0.98
- **Plzen**: Elo 1620 → 1622; Europapokal (2 Sp.): xG-Residuum +0.13/Sp.; xG-Korrektur +2 Elo
- **NEC Nijmegen**: Elo 1589 → 1574; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.32; Europapokal (2 Sp.): xG-Residuum +0.40/Sp.; xG-Korrektur -15 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1633 → 1609; Europapokal (3 Sp.): xG-Residuum -1.06/Sp.; xG-Korrektur -24 Elo
- **AC Milan**: Elo 1830 → 1818; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +0.80; Europapokal (3 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur -12 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1676 → 1664; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -12 Elo
- **Real Sociedad**: Elo 1785 → 1746; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.49; Europapokal (2 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -39 Elo; Tempo ×1.01
- **Lyon**: Elo 1792 → 1776; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.65; Europapokal (3 Sp.): xG-Residuum -0.58/Sp.; xG-Korrektur -16 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1661 → 1669; Liga (matchpulse, 10 Sp.): xG 1.74:1.01/Sp., Elo-Erwartung +0.55; Europapokal (3 Sp.): xG-Residuum +0.02/Sp.; xG-Korrektur +8 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1673 → 1694; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +1.01; Europapokal (2 Sp.): xG-Residuum -1.41/Sp.; xG-Korrektur +21 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1645 → 1628; Europapokal (2 Sp.): xG-Residuum -1.08/Sp.; xG-Korrektur -18 Elo
- **Bournemouth**: Elo 1889 → 1913; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.42; Europapokal (2 Sp.): xG-Residuum +1.55/Sp.; xG-Korrektur +23 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1593 → 1591; Europapokal (2 Sp.): xG-Residuum -0.13/Sp.; xG-Korrektur -2 Elo
- **Jagiellonia**: Elo 1598 → 1568; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.48; Europapokal (3 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur -29 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1843 → 1836; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +0.88; Europapokal (3 Sp.): xG-Residuum +1.50/Sp.; xG-Korrektur -7 Elo; Tempo ×1.01
- **Marseille**: Elo 1770 → 1716; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.54; Europapokal (2 Sp.): xG-Residuum -0.60/Sp.; xG-Korrektur -54 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1668 → 1682; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.74; Europapokal (3 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur +15 Elo; Tempo ×1.00
- **Juventus**: Elo 1827 → 1828; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +0.79; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur +1 Elo; Tempo ×0.91
- **Benfica**: Elo 1870 → 1867; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +1.62; Europapokal (3 Sp.): xG-Residuum +0.41/Sp.; xG-Korrektur -3 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1694 → 1662; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +0.99; Europapokal (2 Sp.): xG-Residuum -2.33/Sp.; xG-Korrektur -32 Elo; Tempo ×0.99
- **Celtic**: Elo 1656 → 1676; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.15; Europapokal (2 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur +20 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1710 → 1721; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +0.88; Europapokal (2 Sp.): xG-Residuum +1.28/Sp.; xG-Korrektur +11 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1740 → 1754; Europapokal (3 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +14 Elo
- **Union St. Gilloise**: Elo 1820 → 1804; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.42; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur -16 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1644 → 1631; Europapokal (2 Sp.): xG-Residuum -0.80/Sp.; xG-Korrektur -13 Elo
- **OFI**: Elo 1501 → 1500; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung -0.17; Europapokal (2 Sp.): xG-Residuum -0.56/Sp.; xG-Korrektur -1 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1627 → 1623; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur -5 Elo; Tempo ×0.99
- **Celje**: Elo 1515 → 1528; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur +13 Elo
- **Sunderland**: Elo 1717 → 1738; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.66; Europapokal (3 Sp.): xG-Residuum +0.44/Sp.; xG-Korrektur +21 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1654 → 1660; Europapokal (2 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur +6 Elo
- **Torreense**: Elo 1455 → 1456; Europapokal (2 Sp.): xG-Residuum +0.11/Sp.; xG-Korrektur +2 Elo
- **Ararat-Armenia**: Elo 1443 → 1441; Europapokal (2 Sp.): xG-Residuum -0.16/Sp.; xG-Korrektur -3 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1676 : 1709 | 1.36 : 1.23 | 39 % | 28 % | 33 % | 48 % | 53 % | 35 % / 25 % / 40 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1560 : 1713 | 1.06 : 1.48 | 26 % | 27 % | 46 % | 47 % | 51 % | 24 % / 29 % / 47 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1717 : 1428 | 2.63 : 0.64 | 79 % | 14 % | 6 % | 63 % | 44 % | 81 % / 12 % / 6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1674 : 1356 | 2.74 : 0.60 | 82 % | 13 % | 5 % | 65 % | 43 % | 89 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1290 : 1604 | 0.81 : 2.04 | 13 % | 21 % | 66 % | 54 % | 49 % | 12 % / 20 % / 68 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1685 : 1782 | 1.20 : 1.38 | 32 % | 28 % | 40 % | 48 % | 53 % | 37 % / 26 % / 37 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1510 : 1552 | 1.31 : 1.23 | 38 % | 28 % | 34 % | 47 % | 52 % | 40 % / 27 % / 34 % |
| Do 05.11. 18:45 | KuPS – Gent | 1436 : 1642 | 0.96 : 1.63 | 22 % | 26 % | 53 % | 48 % | 50 % | 20 % / 23 % / 57 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1480 : 1482 | 1.44 : 1.17 | 43 % | 27 % | 30 % | 48 % | 53 % | 42 % / 30 % / 28 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1745 : 1609 | 1.94 : 0.83 | 63 % | 22 % | 15 % | 53 % | 49 % | 64 % / 20 % / 16 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1678 : 1380 | 2.60 : 0.61 | 80 % | 14 % | 6 % | 62 % | 43 % | – |
| Do 05.11. 21:00 | Twente – Pafos | 1746 : 1567 | 2.12 : 0.78 | 68 % | 20 % | 12 % | 55 % | 48 % | 71 % / 17 % / 12 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1668 : 1901 | 0.91 : 1.72 | 19 % | 25 % | 56 % | 49 % | 50 % | 16 % / 24 % / 60 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1651 : 1377 | 2.50 : 0.65 | 78 % | 15 % | 7 % | 61 % | 44 % | 79 % / 13 % / 8 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1713 : 1545 | 2.11 : 0.80 | 67 % | 20 % | 13 % | 56 % | 49 % | 61 % / 22 % / 17 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1601 : 1444 | 2.04 : 0.81 | 66 % | 21 % | 13 % | 54 % | 49 % | 62 % / 22 % / 15 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1600 : 1553 | 1.72 : 1.02 | 53 % | 25 % | 22 % | 52 % | 53 % | 56 % / 24 % / 21 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1502 : 1563 | 1.28 : 1.29 | 36 % | 28 % | 36 % | 47 % | 53 % | 40 % / 28 % / 32 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1719 → 1676; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +1.10; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur -43 Elo; Tempo ×1.00
- **Ajax**: Elo 1709 → 1709; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +0.96; Europapokal (2 Sp.): xG-Residuum -0.17/Sp.; xG-Korrektur -0 Elo; Tempo ×1.01
- **Aarhus**: Elo 1590 → 1560; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.41; Europapokal (2 Sp.): xG-Residuum -0.70/Sp.; xG-Korrektur -29 Elo; Tempo ×0.99
- **SC Braga**: Elo 1714 → 1713; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur -2 Elo; Tempo ×0.96
- **Atalanta**: Elo 1762 → 1717; Liga (football-data-xg, 9 Sp.): xG 1.39:2.05/Sp., Elo-Erwartung +0.45; Europapokal (2 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur -45 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1435 → 1428; Europapokal (2 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur -8 Elo
- **FK Crvena Zvezda**: Elo 1673 → 1674; Europapokal (2 Sp.): xG-Residuum +0.08/Sp.; xG-Korrektur +1 Elo
- **Inter Club d'Escaldes**: Elo 1364 → 1356; Europapokal (2 Sp.): xG-Residuum -0.53/Sp.; xG-Korrektur -9 Elo
- **Lincoln Red Imps FC**: Elo 1317 → 1290; Europapokal (2 Sp.): xG-Residuum -1.66/Sp.; xG-Korrektur -27 Elo
- **HNK Hajduk Split**: Elo 1601 → 1604; Europapokal (2 Sp.): xG-Residuum +0.13/Sp.; xG-Korrektur +2 Elo
- **Trabzonspor**: Elo 1701 → 1685; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.83; Europapokal (2 Sp.): xG-Residuum +0.08/Sp.; xG-Korrektur -17 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1791 → 1782; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.60; Europapokal (2 Sp.): xG-Residuum -0.79/Sp.; xG-Korrektur -10 Elo; Tempo ×0.97
- **FC Thun**: Elo 1551 → 1510; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung +0.41; Europapokal (2 Sp.): xG-Residuum +0.21/Sp.; xG-Korrektur -41 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1561 → 1552; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.63; Europapokal (2 Sp.): xG-Residuum +0.89/Sp.; xG-Korrektur -8 Elo; Tempo ×1.00
- **KuPS**: Elo 1443 → 1436; Europapokal (2 Sp.): xG-Residuum -0.43/Sp.; xG-Korrektur -7 Elo
- **Gent**: Elo 1644 → 1642; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.46; Europapokal (2 Sp.): xG-Residuum -0.13/Sp.; xG-Korrektur -3 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1506 → 1480; Liga (matchpulse, 27 Sp.): xG 1.48:1.66/Sp., Elo-Erwartung +0.25; Europapokal (2 Sp.): xG-Residuum +0.69/Sp.; xG-Korrektur -26 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1502 → 1482; Europapokal (2 Sp.): xG-Residuum -1.19/Sp.; xG-Korrektur -20 Elo
- **Monaco**: Elo 1783 → 1745; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.61; Europapokal (2 Sp.): xG-Residuum -0.57/Sp.; xG-Korrektur -38 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1616 → 1609; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.55; Europapokal (2 Sp.): xG-Residuum -1.71/Sp.; xG-Korrektur -7 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1694 → 1678; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +0.96; Europapokal (2 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur -16 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1386 → 1380; Europapokal (2 Sp.): xG-Residuum -0.41/Sp.; xG-Korrektur -7 Elo
- **Twente**: Elo 1701 → 1746; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +0.91; Europapokal (2 Sp.): xG-Residuum +1.83/Sp.; xG-Korrektur +45 Elo; Tempo ×1.00
- **Pafos**: Elo 1581 → 1567; Europapokal (2 Sp.): xG-Residuum -0.85/Sp.; xG-Korrektur -14 Elo
- **Getafe**: Elo 1680 → 1668; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.23; Europapokal (2 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur -12 Elo; Tempo ×0.93
- **Brighton**: Elo 1908 → 1901; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.52; Europapokal (2 Sp.): xG-Residuum -0.55/Sp.; xG-Korrektur -7 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1676 → 1651; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +1.08; Europapokal (2 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -25 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1391 → 1377; Europapokal (2 Sp.): xG-Residuum -0.84/Sp.; xG-Korrektur -14 Elo
- **Panathinaikos**: Elo 1672 → 1713; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +0.91; Europapokal (2 Sp.): xG-Residuum +1.67/Sp.; xG-Korrektur +41 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1516 → 1545; Europapokal (2 Sp.): xG-Residuum +1.74/Sp.; xG-Korrektur +28 Elo
- **Universitatea Craiova**: Elo 1603 → 1601; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -1 Elo
- **Egnatia Rrogozhinë**: Elo 1439 → 1444; Europapokal (2 Sp.): xG-Residuum +0.32/Sp.; xG-Korrektur +5 Elo
- **St. Truiden**: Elo 1608 → 1600; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.27; Europapokal (2 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur -9 Elo; Tempo ×1.04
- **Brann**: Elo 1581 → 1553; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.41; Europapokal (2 Sp.): xG-Residuum +0.71/Sp.; xG-Korrektur -28 Elo; Tempo ×1.02
- **Riga**: Elo 1494 → 1502; Europapokal (2 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur +8 Elo
- **FK Jablonec**: Elo 1541 → 1563; Europapokal (2 Sp.): xG-Residuum +1.36/Sp.; xG-Korrektur +22 Elo

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 34 Spiele ausgewertet, Log-Loss 1X2 Modell 1.021
- Gegen Pinnacle (34 Spiele): Modell 1.021 vs. Pinnacle 1.003 (kleiner = besser)
- Value-Wetten: 42, Ergebnis -4.62 Einheiten, ROI -11.0 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Hinweise
- ClubElo heute nicht erreichbar (ClubElo nicht erreichbar (https://clubelo.com/ARM: HTTP 403 · <!DOCTYPE html><html lang="en-US"><head><title>Just a mome) – eigene Elo-Rechnung

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
