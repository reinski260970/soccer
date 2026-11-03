# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 03.11.2026 07:37 (Wien), Spiele 03.11. bis 05.11.2026

## Datenbasis
- Elo: **eigene Elo-Rechnung** (ClubElo von GitHub aus gesperrt), verankert an ClubElo vom 24.10.2026 (205 Teams), seither 823 Spiele eingerechnet
- Ergebnisbasis: 39109 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1152 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-245 Elo, 2 Sp.), Estonia (-220 Elo, 2 Sp.), Gibraltar (-355 Elo, 48 Sp.), Hungary (-165 Elo, 4 Sp.), Iceland (-160 Elo, 4 Sp.), San-Marino (-445 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 771 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (×1.00 ggü. ClubElo-Erwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 72 Elo, Heimteam Außenseiter 64 Elo (reiner Fit 75 / 65, Steigung ×1.00, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 77 Teams, Europapokal-xG aus 132 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 243 | 3.59 | 2.97 | ×1.130 | 52 % |
| Conference League | 285 | 2.62 | 2.92 | ×0.933 | 47 % |
| Europa League | 243 | 2.77 | 2.92 | ×0.970 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 388 | 65.2 % | 61.2 % |
| Heimteam Außenseiter | 380 | 32.4 % | 31.4 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 11 % | 3 % | 34.00 | +269.7 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 19 % | 7 % | 11.00 | +107.5 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1 | 14 % | 12 % | 11.00 | +57.0 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 10 % | 7 % | 15.00 | +50.3 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 17 % | 13 % | 8.00 | +39.1 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 33 % | 23 % | 4.20 | +38.4 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | U2.5 | 39 % | 29 % | 3.50 | +35.8 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | U2.5 | 30 % | – | 4.50 | +34.2 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | U2.5 | 52 % | 37 % | 2.60 | +34.0 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1 | 25 % | 18 % | 5.25 | +33.3 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 31 % | 24 % | 4.20 | +31.6 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 20 % | 15 % | 6.50 | +31.4 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1 | 14 % | 9 % | 9.50 | +31.0 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | U2.5 | 38 % | 30 % | 3.40 | +28.2 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1 | 23 % | 17 % | 5.50 | +27.0 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | U2.5 | 52 % | 38 % | 2.40 | +25.8 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | U2.5 | 46 % | 35 % | 2.70 | +25.3 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 39 % | 31 % | 3.20 | +25.3 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 2 | 54 % | 39 % | 2.30 | +24.7 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 52 % | 38 % | 2.40 | +24.0 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 2 | 18 % | 14 % | 7.00 | +23.1 % |
| Mi 04.11. 21:00 | Lens – Como | 1 | 41 % | 32 % | 3.00 | +22.5 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | X | 20 % | 17 % | 6.00 | +22.1 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 26 % | 22 % | 4.75 | +21.8 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | U2.5 | 36 % | 28 % | 3.40 | +21.6 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 20 % | 17 % | 6.00 | +21.5 % |
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1 | 33 % | 27 % | 3.70 | +21.1 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 2 | 32 % | 26 % | 3.80 | +20.8 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | X | 17 % | 13 % | 7.00 | +20.4 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | X | 17 % | 13 % | 7.00 | +20.2 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 48 % | 38 % | 2.50 | +20.2 % |
| Do 05.11. 21:00 | Twente – Pafos | U2.5 | 44 % | 35 % | 2.70 | +20.1 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 50 % | 39 % | 2.38 | +19.0 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 50 % | 39 % | 2.38 | +18.4 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | U2.5 | 37 % | 30 % | 3.20 | +18.2 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 21 % | 18 % | 5.50 | +18.1 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 34 % | 2.75 | +18.0 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 50 % | 40 % | 2.38 | +18.0 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | X | 19 % | 15 % | 6.25 | +16.1 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | U2.5 | 36 % | 30 % | 3.20 | +15.6 % |
| Do 05.11. 21:00 | St. Truiden – Brann | U2.5 | 48 % | 39 % | 2.40 | +15.4 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 48 % | 40 % | 2.38 | +14.7 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 24 % | 21 % | 4.75 | +13.4 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 24 % | 4.20 | +13.4 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1 | 13 % | 9 % | 9.00 | +13.1 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | U2.5 | 35 % | 30 % | 3.20 | +13.1 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 2 | 27 % | 24 % | 4.20 | +12.7 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 49 % | 41 % | 2.30 | +12.4 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 36 % | 30 % | 3.10 | +11.0 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 41 % | 35 % | 2.70 | +9.8 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 2 | 36 % | 32 % | 3.00 | +9.5 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 18 % | 16 % | 6.25 | +9.4 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +9.3 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | O2.5 | 63 % | 55 % | 1.73 | +8.8 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | X | 23 % | 20 % | 4.75 | +8.7 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | U2.5 | 49 % | 44 % | 2.20 | +8.3 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 22 % | 20 % | 5.00 | +8.2 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 2 | 13 % | 11 % | 8.00 | +7.8 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | U2.5 | 31 % | 27 % | 3.50 | +7.7 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | X | 22 % | 20 % | 5.00 | +7.5 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 21 % | 20 % | 5.00 | +7.2 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | X | 23 % | 20 % | 4.75 | +7.1 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 38 % | 2.50 | +6.8 % |
| Di 03.11. 21:00 | Feyenoord – Inter | U2.5 | 36 % | 32 % | 3.00 | +6.6 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1 | 68 % | 61 % | 1.55 | +5.7 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | X | 24 % | 22 % | 4.33 | +5.6 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | U2.5 | 46 % | 43 % | 2.30 | +5.6 % |
| Do 05.11. 21:00 | St. Truiden – Brann | X | 25 % | 24 % | 4.20 | +5.5 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 2 | 40 % | 37 % | 2.62 | +5.3 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- FK Crvena Zvezda – Inter Club d'Escaldes: U2.5 Modell 43 % vs. Pinnacle 27 %
- Hapoel Beer Sheva – OFI: 1 Modell 65 % vs. Pinnacle 45 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1712 : 1811 | 1.46 : 1.69 | 33 % | 25 % | 43 % | 61 % | 63 % | 27 % / 25 % / 48 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | 1805 : 1809 | 1.83 : 1.42 | 47 % | 24 % | 30 % | 63 % | 64 % | 44 % / 23 % / 33 % |
| Di 03.11. 21:00 | Manchester United – AS Roma | 1811 : 1852 | 1.69 : 1.54 | 41 % | 24 % | 35 % | 63 % | 65 % | 42 % / 24 % / 34 % |
| Di 03.11. 21:00 | Feyenoord – Inter | 1753 : 1918 | 1.32 : 2.00 | 24 % | 23 % | 53 % | 64 % | 64 % | 25 % / 23 % / 52 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 1757 : 1748 | 1.86 : 1.32 | 50 % | 24 % | 27 % | 62 % | 63 % | 53 % / 23 % / 24 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | 2020 : 1877 | 2.58 : 1.05 | 70 % | 17 % | 13 % | 70 % | 60 % | 76 % / 13 % / 11 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 1884 : 2059 | 1.26 : 2.01 | 23 % | 23 % | 54 % | 64 % | 63 % | 35 % / 25 % / 39 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | 1797 : 2007 | 1.16 : 2.15 | 19 % | 21 % | 59 % | 64 % | 61 % | 22 % / 21 % / 57 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 1630 : 1538 | 2.22 : 1.11 | 62 % | 20 % | 18 % | 65 % | 60 % | 69 % / 17 % / 14 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1697 : 1981 | 1.02 : 2.56 | 13 % | 17 % | 70 % | 69 % | 59 % | 9 % / 13 % / 78 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1741 : 1917 | 1.25 : 2.00 | 23 % | 23 % | 54 % | 63 % | 62 % | 17 % / 20 % / 62 % |
| Mi 04.11. 21:00 | Lens – Como | 1779 : 1820 | 1.65 : 1.50 | 41 % | 25 % | 35 % | 61 % | 63 % | 32 % / 24 % / 45 % |
| Mi 04.11. 21:00 | Borussia Dortmund – Real Betis | 1858 : 1792 | 2.11 : 1.18 | 58 % | 22 % | 20 % | 64 % | 61 % | 55 % / 23 % / 22 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1828 : 1985 | 1.33 : 1.96 | 25 % | 23 % | 52 % | 64 % | 64 % | 18 % / 20 % / 62 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 1757 : 1811 | 1.64 : 1.58 | 39 % | 24 % | 36 % | 62 % | 64 % | 47 % / 22 % / 32 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 1804 : 1787 | 1.92 : 1.32 | 51 % | 23 % | 26 % | 63 % | 63 % | 49 % / 25 % / 26 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1761 : 2032 | 1.00 : 2.39 | 14 % | 19 % | 68 % | 66 % | 58 % | 9 % / 15 % / 76 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 1673 : 1533 | 2.45 : 1.00 | 69 % | 18 % | 13 % | 67 % | 58 % | – |

<details><summary>Herleitung je Team</summary>

- **Shakhtar Donetsk**: Elo 1696 → 1712; Europapokal (3 Sp.): xG-Residuum +0.80/Sp.; xG-Korrektur +16 Elo
- **Sporting CP**: Elo 1854 → 1811; Liga (matchpulse, 10 Sp.): xG 1.70:0.85/Sp., Elo-Erwartung +1.98; Europapokal (3 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -43 Elo; Tempo ×1.00
- **Galatasaray**: Elo 1821 → 1805; Liga (matchpulse, 10 Sp.): xG 2.27:0.93/Sp., Elo-Erwartung +1.73; Europapokal (3 Sp.): xG-Residuum -0.12/Sp.; xG-Korrektur -16 Elo; Tempo ×1.03
- **VfB Stuttgart**: Elo 1840 → 1809; Liga (matchpulse, 8 Sp.): xG 1.94:2.13/Sp., Elo-Erwartung +1.06; Europapokal (3 Sp.): xG-Residuum +0.77/Sp.; xG-Korrektur -31 Elo; Tempo ×1.03
- **Manchester United**: Elo 1825 → 1811; Liga (football-data-xg, 9 Sp.): xG 1.53:1.66/Sp., Elo-Erwartung +0.30; Europapokal (3 Sp.): xG-Residuum +0.11/Sp.; xG-Korrektur -14 Elo; Tempo ×1.02
- **AS Roma**: Elo 1868 → 1852; Liga (football-data-xg, 10 Sp.): xG 2.26:1.37/Sp., Elo-Erwartung +1.28; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -16 Elo; Tempo ×1.03
- **Feyenoord**: Elo 1730 → 1753; Liga (matchpulse, 11 Sp.): xG 2.89:1.07/Sp., Elo-Erwartung +1.30; Europapokal (3 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur +23 Elo; Tempo ×1.03
- **Inter**: Elo 1930 → 1918; Liga (football-data-xg, 10 Sp.): xG 2.70:1.06/Sp., Elo-Erwartung +1.69; Europapokal (3 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur -12 Elo; Tempo ×1.04
- **Bodo/Glimt**: Elo 1774 → 1757; Liga (matchpulse, 25 Sp.): xG 2.38:0.96/Sp., Elo-Erwartung +1.76; Europapokal (3 Sp.): xG-Residuum +0.36/Sp.; xG-Korrektur -17 Elo; Tempo ×1.02
- **Lille**: Elo 1779 → 1748; Liga (football-data-xg, 9 Sp.): xG 1.41:1.49/Sp., Elo-Erwartung +0.77; Europapokal (3 Sp.): xG-Residuum -0.13/Sp.; xG-Korrektur -31 Elo; Tempo ×0.98
- **Barcelona**: Elo 2020 → 2020; Liga (football-data-xg, 11 Sp.): xG 3.39:1.06/Sp., Elo-Erwartung +2.16; Europapokal (3 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur -0 Elo; Tempo ×1.10
- **Aston Villa**: Elo 1911 → 1877; Liga (football-data-xg, 9 Sp.): xG 1.20:1.68/Sp., Elo-Erwartung +0.82; Europapokal (3 Sp.): xG-Residuum +1.01/Sp.; xG-Korrektur -34 Elo; Tempo ×1.00
- **Atletico Madrid**: Elo 1924 → 1884; Liga (football-data-xg, 11 Sp.): xG 1.61:1.09/Sp., Elo-Erwartung +1.49; Europapokal (3 Sp.): xG-Residuum -0.18/Sp.; xG-Korrektur -40 Elo; Tempo ×0.99
- **Bayern München**: Elo 2042 → 2059; Liga (matchpulse, 8 Sp.): xG 3.59:0.91/Sp., Elo-Erwartung +2.46; Europapokal (3 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +17 Elo; Tempo ×1.05
- **Villarreal**: Elo 1789 → 1797; Liga (football-data-xg, 11 Sp.): xG 1.97:1.09/Sp., Elo-Erwartung +0.63; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur +8 Elo; Tempo ×1.01
- **Paris Saint Germain**: Elo 1986 → 2007; Europapokal (3 Sp.): xG-Residuum +1.05/Sp.; xG-Korrektur +21 Elo
- **Lask Linz**: Elo 1627 → 1630; Liga (matchpulse, 11 Sp.): xG 2.16:1.12/Sp., Elo-Erwartung +0.85; Europapokal (3 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur +4 Elo; Tempo ×1.00
- **Slovan Bratislava**: Elo 1557 → 1538; Europapokal (3 Sp.): xG-Residuum -0.99/Sp.; xG-Korrektur -20 Elo
- **AEK Athens FC**: Elo 1689 → 1697; Liga (football-data-xg, 8 Sp.): xG 2.09:0.73/Sp., Elo-Erwartung +1.20; Europapokal (3 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +8 Elo; Tempo ×1.01
- **Real Madrid**: Elo 2001 → 1981; Liga (football-data-xg, 11 Sp.): xG 2.48:1.01/Sp., Elo-Erwartung +2.02; Europapokal (3 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur -20 Elo; Tempo ×1.04
- **Fenerbahçe**: Elo 1757 → 1741; Liga (matchpulse, 10 Sp.): xG 2.09:1.21/Sp., Elo-Erwartung +1.30; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur -16 Elo; Tempo ×1.03
- **Liverpool**: Elo 1942 → 1917; Liga (football-data-xg, 9 Sp.): xG 1.46:1.17/Sp., Elo-Erwartung +1.01; Europapokal (3 Sp.): xG-Residuum +0.08/Sp.; xG-Korrektur -24 Elo; Tempo ×0.98
- **Lens**: Elo 1801 → 1779; Liga (football-data-xg, 9 Sp.): xG 1.69:1.49/Sp., Elo-Erwartung +0.90; Europapokal (3 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -22 Elo; Tempo ×1.00
- **Como**: Elo 1830 → 1820; Liga (football-data-xg, 10 Sp.): xG 1.86:1.25/Sp., Elo-Erwartung +1.04; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur -10 Elo; Tempo ×1.00
- **Borussia Dortmund**: Elo 1896 → 1858; Liga (matchpulse, 8 Sp.): xG 1.55:1.48/Sp., Elo-Erwartung +1.41; Europapokal (3 Sp.): xG-Residuum +0.53/Sp.; xG-Korrektur -38 Elo; Tempo ×0.98
- **Real Betis**: Elo 1827 → 1792; Liga (football-data-xg, 11 Sp.): xG 1.61:1.82/Sp., Elo-Erwartung +0.87; Europapokal (3 Sp.): xG-Residuum +0.62/Sp.; xG-Korrektur -35 Elo; Tempo ×1.04
- **RB Leipzig**: Elo 1830 → 1828; Liga (matchpulse, 8 Sp.): xG 2.48:1.60/Sp., Elo-Erwartung +0.99; Europapokal (3 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur -2 Elo; Tempo ×1.03
- **Manchester City**: Elo 2000 → 1985; Liga (football-data-xg, 9 Sp.): xG 2.07:1.27/Sp., Elo-Erwartung +1.39; Europapokal (3 Sp.): xG-Residuum +0.43/Sp.; xG-Korrektur -16 Elo; Tempo ×1.03
- **PSV Eindhoven**: Elo 1782 → 1757; Liga (matchpulse, 11 Sp.): xG 2.38:1.31/Sp., Elo-Erwartung +1.64; Europapokal (3 Sp.): xG-Residuum -0.29/Sp.; xG-Korrektur -26 Elo; Tempo ×1.01
- **Club Brugge KV**: Elo 1840 → 1811; Liga (matchpulse, 10 Sp.): xG 2.44:1.15/Sp., Elo-Erwartung +1.99; Europapokal (3 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -29 Elo; Tempo ×1.03
- **FC Porto**: Elo 1833 → 1804; Liga (matchpulse, 10 Sp.): xG 2.21:0.83/Sp., Elo-Erwartung +1.83; Europapokal (3 Sp.): xG-Residuum -1.12/Sp.; xG-Korrektur -29 Elo; Tempo ×1.03
- **Napoli**: Elo 1816 → 1787; Liga (football-data-xg, 10 Sp.): xG 1.74:1.28/Sp., Elo-Erwartung +0.95; Europapokal (3 Sp.): xG-Residuum -0.99/Sp.; xG-Korrektur -29 Elo; Tempo ×1.00
- **Slavia Praha**: Elo 1752 → 1761; Europapokal (3 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur +9 Elo
- **Arsenal (England)**: Elo 2060 → 2032; Liga (football-data-xg, 9 Sp.): xG 1.65:0.80/Sp., Elo-Erwartung +1.79; Europapokal (3 Sp.): xG-Residuum +0.43/Sp.; xG-Korrektur -28 Elo; Tempo ×0.97
- **Viking**: Elo 1705 → 1673; Liga (matchpulse, 25 Sp.): xG 2.00:1.12/Sp., Elo-Erwartung +1.30; Europapokal (3 Sp.): xG-Residuum -1.19/Sp.; xG-Korrektur -32 Elo; Tempo ×1.00
- **Sabah FA**: Elo 1558 → 1533; Europapokal (3 Sp.): xG-Residuum -1.28/Sp.; xG-Korrektur -25 Elo

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 16:30 | Rennes – Olympiakos Piraeus | 1714 : 1736 | 1.51 : 1.27 | 42 % | 26 % | 31 % | 53 % | 57 % | 42 % / 27 % / 31 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1744 : 1729 | 1.63 : 1.13 | 48 % | 26 % | 26 % | 52 % | 55 % | 49 % / 24 % / 27 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1535 : 1622 | 1.27 : 1.40 | 33 % | 27 % | 39 % | 50 % | 55 % | 33 % / 25 % / 42 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1572 : 1609 | 1.42 : 1.27 | 40 % | 27 % | 33 % | 50 % | 55 % | 53 % / 24 % / 23 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1809 : 1663 | 2.13 : 0.85 | 66 % | 20 % | 13 % | 57 % | 51 % | 71 % / 17 % / 11 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1745 : 1768 | 1.45 : 1.23 | 42 % | 27 % | 31 % | 50 % | 55 % | 52 % / 24 % / 24 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1659 : 1686 | 1.47 : 1.25 | 41 % | 27 % | 32 % | 51 % | 56 % | 49 % / 25 % / 26 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1626 : 1900 | 0.87 : 2.09 | 14 % | 21 % | 65 % | 57 % | 51 % | 16 % / 21 % / 63 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1587 : 1568 | 1.64 : 1.12 | 49 % | 26 % | 25 % | 52 % | 55 % | 48 % / 27 % / 26 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1832 : 1715 | 2.05 : 0.93 | 63 % | 21 % | 16 % | 57 % | 53 % | 68 % / 18 % / 14 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1675 : 1817 | 1.09 : 1.51 | 27 % | 27 % | 46 % | 48 % | 52 % | 26 % / 25 % / 49 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1850 : 1656 | 2.38 : 0.78 | 73 % | 17 % | 10 % | 61 % | 50 % | 79 % / 13 % / 7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1667 : 1712 | 1.43 : 1.32 | 39 % | 27 % | 34 % | 52 % | 56 % | 31 % / 25 % / 44 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1753 : 1790 | 1.43 : 1.28 | 40 % | 27 % | 33 % | 51 % | 55 % | 43 % / 26 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1628 : 1492 | 2.09 : 0.87 | 65 % | 21 % | 14 % | 57 % | 51 % | 45 % / 26 % / 29 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1617 : 1524 | 1.89 : 0.95 | 59 % | 23 % | 18 % | 54 % | 53 % | 62 % / 21 % / 17 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1725 : 1656 | 1.83 : 1.01 | 56 % | 24 % | 20 % | 54 % | 54 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1454 : 1437 | 1.62 : 1.12 | 49 % | 26 % | 26 % | 52 % | 55 % | 53 % / 24 % / 22 % |

<details><summary>Herleitung je Team</summary>

- **Rennes**: Elo 1744 → 1714; Liga (football-data-xg, 9 Sp.): xG 2.09:2.33/Sp., Elo-Erwartung +0.55; Europapokal (2 Sp.): xG-Residuum -0.06/Sp.; xG-Korrektur -30 Elo; Tempo ×1.06
- **Olympiakos Piraeus**: Elo 1744 → 1736; Liga (football-data-xg, 9 Sp.): xG 1.78:0.72/Sp., Elo-Erwartung +1.56; Europapokal (3 Sp.): xG-Residuum +0.77/Sp.; xG-Korrektur -8 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1780 → 1744; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung +0.04; Europapokal (2 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -35 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1722 → 1729; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung +0.33; Europapokal (2 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur +7 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1540 → 1535; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung +0.29; Europapokal (2 Sp.): xG-Residuum +1.26/Sp.; xG-Korrektur -5 Elo; Tempo ×0.98
- **Plzen**: Elo 1619 → 1622; Europapokal (2 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur +4 Elo
- **NEC Nijmegen**: Elo 1587 → 1572; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.41; Europapokal (2 Sp.): xG-Residuum +0.62/Sp.; xG-Korrektur -15 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1633 → 1609; Europapokal (3 Sp.): xG-Residuum -1.20/Sp.; xG-Korrektur -24 Elo
- **AC Milan**: Elo 1827 → 1809; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +1.02; Europapokal (3 Sp.): xG-Residuum +0.21/Sp.; xG-Korrektur -19 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1674 → 1663; Europapokal (2 Sp.): xG-Residuum -0.78/Sp.; xG-Korrektur -11 Elo
- **Real Sociedad**: Elo 1783 → 1745; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.60; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur -39 Elo; Tempo ×1.01
- **Lyon**: Elo 1791 → 1768; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.84; Europapokal (3 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -23 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1659 → 1659; Liga (matchpulse, 10 Sp.): xG 1.74:1.01/Sp., Elo-Erwartung +0.80; Europapokal (3 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +0 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1673 → 1686; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +1.14; Europapokal (2 Sp.): xG-Residuum -1.41/Sp.; xG-Korrektur +13 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1645 → 1626; Europapokal (2 Sp.): xG-Residuum -1.28/Sp.; xG-Korrektur -18 Elo
- **Bournemouth**: Elo 1886 → 1900; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.67; Europapokal (2 Sp.): xG-Residuum +1.87/Sp.; xG-Korrektur +14 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1594 → 1587; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -7 Elo
- **Jagiellonia**: Elo 1597 → 1568; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.56; Europapokal (3 Sp.): xG-Residuum -0.68/Sp.; xG-Korrektur -29 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1843 → 1832; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +1.08; Europapokal (3 Sp.): xG-Residuum +1.63/Sp.; xG-Korrektur -11 Elo; Tempo ×1.01
- **Marseille**: Elo 1768 → 1715; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.70; Europapokal (2 Sp.): xG-Residuum -0.52/Sp.; xG-Korrektur -53 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1668 → 1675; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.90; Europapokal (3 Sp.): xG-Residuum +0.46/Sp.; xG-Korrektur +7 Elo; Tempo ×1.00
- **Juventus**: Elo 1824 → 1817; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +1.00; Europapokal (2 Sp.): xG-Residuum +0.14/Sp.; xG-Korrektur -7 Elo; Tempo ×0.91
- **Benfica**: Elo 1868 → 1850; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +2.08; Europapokal (3 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur -18 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1693 → 1656; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +1.15; Europapokal (2 Sp.): xG-Residuum -2.65/Sp.; xG-Korrektur -37 Elo; Tempo ×0.99
- **Celtic**: Elo 1656 → 1667; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.25; Europapokal (2 Sp.): xG-Residuum -0.80/Sp.; xG-Korrektur +10 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1709 → 1712; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +1.00; Europapokal (2 Sp.): xG-Residuum +0.98/Sp.; xG-Korrektur +2 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1737 → 1753; Europapokal (3 Sp.): xG-Residuum +0.81/Sp.; xG-Korrektur +16 Elo
- **Union St. Gilloise**: Elo 1818 → 1790; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.84; Europapokal (2 Sp.): xG-Residuum +0.32/Sp.; xG-Korrektur -29 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1645 → 1628; Europapokal (2 Sp.): xG-Residuum -1.15/Sp.; xG-Korrektur -16 Elo
- **OFI**: Elo 1500 → 1492; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung +0.05; Europapokal (2 Sp.): xG-Residuum -0.49/Sp.; xG-Korrektur -9 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1627 → 1617; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.85; Europapokal (2 Sp.): xG-Residuum -0.06/Sp.; xG-Korrektur -10 Elo; Tempo ×0.99
- **Celje**: Elo 1517 → 1524; Europapokal (3 Sp.): xG-Residuum +0.37/Sp.; xG-Korrektur +7 Elo
- **Sunderland**: Elo 1711 → 1725; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.41; Europapokal (3 Sp.): xG-Residuum +0.76/Sp.; xG-Korrektur +13 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1654 → 1656; Europapokal (2 Sp.): xG-Residuum +0.16/Sp.; xG-Korrektur +2 Elo
- **Torreense**: Elo 1453 → 1454; Europapokal (2 Sp.): xG-Residuum +0.13/Sp.; xG-Korrektur +2 Elo
- **Ararat-Armenia**: Elo 1444 → 1437; Europapokal (2 Sp.): xG-Residuum -0.44/Sp.; xG-Korrektur -6 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1671 : 1700 | 1.40 : 1.21 | 41 % | 27 % | 32 % | 48 % | 54 % | 35 % / 25 % / 40 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1557 : 1700 | 1.07 : 1.49 | 27 % | 27 % | 46 % | 47 % | 52 % | 24 % / 29 % / 47 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1715 : 1429 | 2.78 : 0.62 | 82 % | 13 % | 5 % | 66 % | 44 % | 81 % / 12 % / 6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1670 : 1485 | 2.22 : 0.76 | 70 % | 19 % | 11 % | 57 % | 48 % | 89 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1329 : 1602 | 0.84 : 2.01 | 14 % | 22 % | 64 % | 54 % | 50 % | 12 % / 20 % / 68 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1683 : 1778 | 1.22 : 1.39 | 32 % | 27 % | 40 % | 48 % | 53 % | 37 % / 26 % / 37 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1514 : 1551 | 1.36 : 1.22 | 40 % | 28 % | 33 % | 48 % | 53 % | 40 % / 27 % / 34 % |
| Do 05.11. 18:45 | KuPS – Gent | 1438 : 1631 | 0.96 : 1.65 | 21 % | 26 % | 53 % | 49 % | 51 % | 20 % / 23 % / 57 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1491 : 1483 | 1.55 : 1.11 | 47 % | 27 % | 27 % | 50 % | 53 % | 42 % / 30 % / 28 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1742 : 1604 | 1.99 : 0.83 | 64 % | 22 % | 14 % | 54 % | 49 % | 64 % / 20 % / 16 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1670 : 1373 | 2.77 : 0.59 | 82 % | 13 % | 5 % | 65 % | 42 % | – |
| Do 05.11. 21:00 | Twente – Pafos | 1732 : 1571 | 2.11 : 0.80 | 67 % | 20 % | 13 % | 56 % | 49 % | 71 % / 17 % / 12 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1661 : 1896 | 0.89 : 1.81 | 18 % | 24 % | 59 % | 51 % | 50 % | 16 % / 24 % / 60 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1649 : 1369 | 2.69 : 0.62 | 81 % | 13 % | 6 % | 64 % | 43 % | 79 % / 13 % / 8 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1704 : 1538 | 2.16 : 0.80 | 68 % | 20 % | 12 % | 57 % | 49 % | 61 % / 22 % / 17 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1605 : 1441 | 2.13 : 0.79 | 68 % | 20 % | 12 % | 56 % | 49 % | 62 % / 22 % / 15 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1595 : 1551 | 1.70 : 1.05 | 52 % | 25 % | 23 % | 52 % | 54 % | 56 % / 24 % / 21 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1498 : 1558 | 1.31 : 1.29 | 37 % | 28 % | 36 % | 48 % | 53 % | 40 % / 28 % / 32 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1719 → 1671; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +1.34; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur -48 Elo; Tempo ×1.00
- **Ajax**: Elo 1708 → 1700; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +1.15; Europapokal (2 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur -8 Elo; Tempo ×1.01
- **Aarhus**: Elo 1587 → 1557; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.52; Europapokal (2 Sp.): xG-Residuum -0.56/Sp.; xG-Korrektur -30 Elo; Tempo ×0.99
- **SC Braga**: Elo 1711 → 1700; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +1.03; Europapokal (2 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur -11 Elo; Tempo ×0.96
- **Atalanta**: Elo 1759 → 1715; Liga (football-data-xg, 9 Sp.): xG 1.39:2.05/Sp., Elo-Erwartung +0.60; Europapokal (2 Sp.): xG-Residuum +0.31/Sp.; xG-Korrektur -44 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1438 → 1429; Europapokal (2 Sp.): xG-Residuum -0.62/Sp.; xG-Korrektur -9 Elo
- **FK Crvena Zvezda**: Elo 1673 → 1670; Europapokal (2 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur -3 Elo
- **Inter Club d'Escaldes**: Elo 1504 → 1485; Europapokal (2 Sp.): xG-Residuum -1.32/Sp.; xG-Korrektur -19 Elo
- **Lincoln Red Imps FC**: Elo 1357 → 1329; Europapokal (2 Sp.): xG-Residuum -1.99/Sp.; xG-Korrektur -28 Elo
- **HNK Hajduk Split**: Elo 1600 → 1602; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur +2 Elo
- **Trabzonspor**: Elo 1701 → 1683; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.94; Europapokal (2 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur -18 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1790 → 1778; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.74; Europapokal (2 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur -12 Elo; Tempo ×0.97
- **FC Thun**: Elo 1551 → 1514; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung +0.43; Europapokal (2 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -37 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1561 → 1551; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.66; Europapokal (2 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur -9 Elo; Tempo ×1.00
- **KuPS**: Elo 1446 → 1438; Europapokal (2 Sp.): xG-Residuum -0.53/Sp.; xG-Korrektur -8 Elo
- **Gent**: Elo 1642 → 1631; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.69; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -11 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1506 → 1491; Liga (matchpulse, 27 Sp.): xG 1.48:1.66/Sp., Elo-Erwartung +0.17; Europapokal (2 Sp.): xG-Residuum +1.31/Sp.; xG-Korrektur -15 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1504 → 1483; Europapokal (2 Sp.): xG-Residuum -1.45/Sp.; xG-Korrektur -21 Elo
- **Monaco**: Elo 1781 → 1742; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.78; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -39 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1615 → 1604; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.69; Europapokal (2 Sp.): xG-Residuum -1.44/Sp.; xG-Korrektur -11 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1692 → 1670; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +1.17; Europapokal (2 Sp.): xG-Residuum +0.32/Sp.; xG-Korrektur -22 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1386 → 1373; Europapokal (2 Sp.): xG-Residuum -0.93/Sp.; xG-Korrektur -13 Elo
- **Twente**: Elo 1699 → 1732; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +1.09; Europapokal (2 Sp.): xG-Residuum +1.99/Sp.; xG-Korrektur +33 Elo; Tempo ×1.00
- **Pafos**: Elo 1581 → 1571; Europapokal (2 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur -9 Elo
- **Getafe**: Elo 1676 → 1661; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.08; Europapokal (2 Sp.): xG-Residuum +0.89/Sp.; xG-Korrektur -15 Elo; Tempo ×0.93
- **Brighton**: Elo 1908 → 1896; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.81; Europapokal (2 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1676 → 1649; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +1.19; Europapokal (2 Sp.): xG-Residuum -0.07/Sp.; xG-Korrektur -26 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1391 → 1369; Europapokal (2 Sp.): xG-Residuum -1.55/Sp.; xG-Korrektur -22 Elo
- **Panathinaikos**: Elo 1671 → 1704; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +1.08; Europapokal (2 Sp.): xG-Residuum +2.11/Sp.; xG-Korrektur +33 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1518 → 1538; Europapokal (2 Sp.): xG-Residuum +1.43/Sp.; xG-Korrektur +20 Elo
- **Universitatea Craiova**: Elo 1604 → 1605; Europapokal (2 Sp.): xG-Residuum +0.06/Sp.; xG-Korrektur +1 Elo
- **Egnatia Rrogozhinë**: Elo 1440 → 1441; Europapokal (2 Sp.): xG-Residuum +0.02/Sp.; xG-Korrektur +0 Elo
- **St. Truiden**: Elo 1607 → 1595; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.48; Europapokal (2 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur -12 Elo; Tempo ×1.04
- **Brann**: Elo 1580 → 1551; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.52; Europapokal (2 Sp.): xG-Residuum +1.15/Sp.; xG-Korrektur -29 Elo; Tempo ×1.02
- **Riga**: Elo 1497 → 1498; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur +2 Elo
- **FK Jablonec**: Elo 1541 → 1558; Europapokal (2 Sp.): xG-Residuum +1.20/Sp.; xG-Korrektur +17 Elo

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
