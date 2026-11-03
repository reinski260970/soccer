# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 03.11.2026 07:24 (Wien), Spiele 03.11. bis 05.11.2026

## Datenbasis
- Elo: **eigene Elo-Rechnung** (ClubElo von GitHub aus gesperrt), verankert an ClubElo vom 24.10.2026 (205 Teams), seither 807 Spiele eingerechnet
- Ergebnisbasis: 39013 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1150 Teams
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 771 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.41 Tore je Team bei Gleichstand, Steigung 0.833 (×1.00 ggü. ClubElo-Erwartung, 171 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 68 Elo, Heimteam Außenseiter 68 Elo (reiner Fit 70 / 70, Steigung ×1.00, Tore 1.42; Richtung Prior geschrumpft)
- xG: Liga-xG für 77 Teams, Europapokal-xG aus 132 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 243 | 3.59 | 2.99 | ×1.123 | 52 % |
| Conference League | 285 | 2.62 | 2.94 | ×0.928 | 47 % |
| Europa League | 243 | 2.77 | 2.94 | ×0.965 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 387 | 64.6 % | 60.7 % |
| Heimteam Außenseiter | 381 | 33.1 % | 31.9 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 11 % | 3 % | 34.00 | +282.7 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 19 % | 7 % | 11.00 | +110.3 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 10 % | 7 % | 15.00 | +55.1 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 18 % | 13 % | 8.00 | +40.8 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | X | 28 % | 20 % | 5.00 | +37.6 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 32 % | 23 % | 4.20 | +36.2 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1 | 26 % | 18 % | 5.25 | +35.9 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | U2.5 | 39 % | 29 % | 3.50 | +35.7 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 21 % | 15 % | 6.50 | +35.1 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1 | 14 % | 9 % | 9.50 | +34.3 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | U2.5 | 30 % | – | 4.50 | +33.8 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | U2.5 | 51 % | 37 % | 2.60 | +32.9 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1 | 24 % | 17 % | 5.50 | +29.7 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 31 % | 24 % | 4.20 | +29.7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 40 % | 31 % | 3.20 | +27.1 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | U2.5 | 37 % | 30 % | 3.40 | +26.8 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 2 | 18 % | 14 % | 7.00 | +25.8 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | U2.5 | 46 % | 35 % | 2.70 | +25.1 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | U2.5 | 52 % | 38 % | 2.40 | +24.8 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 26 % | 22 % | 4.75 | +24.2 % |
| Mi 04.11. 21:00 | Lens – Como | 1 | 41 % | 32 % | 3.00 | +24.2 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 2 | 54 % | 39 % | 2.30 | +23.2 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 51 % | 38 % | 2.40 | +23.2 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | X | 21 % | 17 % | 6.00 | +23.1 % |
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1 | 33 % | 27 % | 3.70 | +22.4 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | X | 17 % | 13 % | 7.00 | +21.6 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | X | 17 % | 13 % | 7.00 | +21.6 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | U2.5 | 36 % | 28 % | 3.40 | +21.0 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 20 % | 17 % | 6.00 | +20.5 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 48 % | 38 % | 2.50 | +19.4 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 2 | 31 % | 26 % | 3.80 | +19.2 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 22 % | 18 % | 5.50 | +18.9 % |
| Do 05.11. 21:00 | Twente – Pafos | U2.5 | 44 % | 35 % | 2.70 | +18.9 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 50 % | 39 % | 2.38 | +18.2 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 34 % | 2.75 | +17.7 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 49 % | 39 % | 2.38 | +17.4 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 49 % | 40 % | 2.38 | +16.9 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | X | 19 % | 15 % | 6.25 | +16.9 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | U2.5 | 36 % | 30 % | 3.20 | +16.8 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1 | 13 % | 9 % | 9.00 | +16.4 % |
| Do 05.11. 21:00 | St. Truiden – Brann | U2.5 | 48 % | 39 % | 2.40 | +15.2 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 2 | 27 % | 24 % | 4.20 | +14.8 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | U2.5 | 36 % | 30 % | 3.20 | +14.7 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 24 % | 21 % | 4.75 | +14.1 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 48 % | 40 % | 2.38 | +13.7 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 24 % | 4.20 | +12.8 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | U2.5 | 35 % | 30 % | 3.20 | +12.4 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 41 % | 35 % | 2.70 | +11.5 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 48 % | 41 % | 2.30 | +11.4 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 18 % | 16 % | 6.25 | +11.1 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 36 % | 30 % | 3.10 | +11.1 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | U2.5 | 52 % | 46 % | 2.15 | +10.8 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 2 | 14 % | 11 % | 8.00 | +10.7 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | O2.5 | 63 % | 55 % | 1.73 | +9.3 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 22 % | 20 % | 5.00 | +9.1 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 22 % | 20 % | 5.00 | +9.0 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | X | 23 % | 20 % | 4.75 | +8.9 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +8.8 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 2 | 36 % | 32 % | 3.00 | +7.8 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | U2.5 | 31 % | 27 % | 3.50 | +7.4 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | U2.5 | 49 % | 44 % | 2.20 | +7.4 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | X | 23 % | 20 % | 4.75 | +7.4 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 38 % | 2.50 | +6.5 % |
| Do 05.11. 21:00 | St. Truiden – Brann | X | 25 % | 24 % | 4.20 | +6.3 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 2 | 24 % | 21 % | 4.50 | +6.1 % |
| Di 03.11. 21:00 | Feyenoord – Inter | U2.5 | 35 % | 32 % | 3.00 | +5.8 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | X | 24 % | 22 % | 4.33 | +5.2 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | U2.5 | 46 % | 43 % | 2.30 | +5.2 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1 | 68 % | 61 % | 1.55 | +5.1 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- FK Crvena Zvezda – Inter Club d'Escaldes: U2.5 Modell 43 % vs. Pinnacle 27 %
- Lincoln Red Imps FC – HNK Hajduk Split: 1 Modell 39 % vs. Pinnacle 12 %
- Hapoel Beer Sheva – OFI: 1 Modell 64 % vs. Pinnacle 45 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1711 : 1812 | 1.47 : 1.69 | 33 % | 24 % | 42 % | 61 % | 63 % | 27 % / 25 % / 48 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | 1805 : 1810 | 1.85 : 1.42 | 47 % | 24 % | 29 % | 64 % | 64 % | 44 % / 23 % / 33 % |
| Di 03.11. 21:00 | Manchester United – AS Roma | 1812 : 1853 | 1.72 : 1.53 | 42 % | 24 % | 34 % | 63 % | 65 % | 42 % / 24 % / 34 % |
| Di 03.11. 21:00 | Feyenoord – Inter | 1754 : 1919 | 1.34 : 2.00 | 25 % | 23 % | 52 % | 65 % | 64 % | 25 % / 23 % / 52 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 1758 : 1749 | 1.86 : 1.34 | 49 % | 24 % | 27 % | 62 % | 63 % | 53 % / 23 % / 24 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | 2021 : 1878 | 2.56 : 1.07 | 69 % | 17 % | 13 % | 70 % | 61 % | 76 % / 13 % / 11 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 1885 : 2060 | 1.28 : 2.00 | 24 % | 23 % | 54 % | 64 % | 63 % | 35 % / 25 % / 39 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | 1797 : 2007 | 1.18 : 2.13 | 20 % | 21 % | 59 % | 64 % | 62 % | 22 % / 21 % / 57 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 1631 : 1537 | 2.21 : 1.13 | 61 % | 21 % | 18 % | 65 % | 61 % | 69 % / 17 % / 14 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1698 : 1982 | 1.03 : 2.54 | 13 % | 17 % | 70 % | 69 % | 60 % | 9 % / 13 % / 78 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1742 : 1918 | 1.27 : 2.00 | 24 % | 23 % | 54 % | 63 % | 63 % | 17 % / 20 % / 62 % |
| Mi 04.11. 21:00 | Lens – Como | 1779 : 1821 | 1.67 : 1.50 | 41 % | 25 % | 34 % | 61 % | 64 % | 32 % / 24 % / 45 % |
| Mi 04.11. 21:00 | Borussia Dortmund – Real Betis | 1860 : 1793 | 2.10 : 1.20 | 58 % | 22 % | 21 % | 64 % | 62 % | 55 % / 23 % / 22 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1828 : 1986 | 1.35 : 1.96 | 26 % | 23 % | 51 % | 64 % | 64 % | 18 % / 20 % / 62 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 1758 : 1812 | 1.66 : 1.57 | 40 % | 24 % | 36 % | 63 % | 65 % | 47 % / 22 % / 32 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 1805 : 1787 | 1.91 : 1.34 | 50 % | 23 % | 26 % | 63 % | 63 % | 49 % / 25 % / 26 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1761 : 2033 | 1.02 : 2.38 | 14 % | 19 % | 67 % | 66 % | 58 % | 9 % / 15 % / 76 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 1674 : 1532 | 2.44 : 1.02 | 68 % | 18 % | 14 % | 67 % | 59 % | – |

<details><summary>Herleitung je Team</summary>

- **Shakhtar Donetsk**: Elo 1696 → 1711; Europapokal (3 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +15 Elo
- **Sporting CP**: Elo 1854 → 1812; Liga (matchpulse, 10 Sp.): xG 1.70:0.85/Sp., Elo-Erwartung +1.96; Europapokal (3 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -42 Elo; Tempo ×1.00
- **Galatasaray**: Elo 1821 → 1805; Liga (matchpulse, 10 Sp.): xG 2.27:0.93/Sp., Elo-Erwartung +1.71; Europapokal (3 Sp.): xG-Residuum -0.14/Sp.; xG-Korrektur -15 Elo; Tempo ×1.03
- **VfB Stuttgart**: Elo 1840 → 1810; Liga (matchpulse, 8 Sp.): xG 1.94:2.13/Sp., Elo-Erwartung +1.04; Europapokal (3 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur -30 Elo; Tempo ×1.03
- **Manchester United**: Elo 1825 → 1812; Liga (football-data-xg, 9 Sp.): xG 1.53:1.66/Sp., Elo-Erwartung +0.28; Europapokal (3 Sp.): xG-Residuum +0.13/Sp.; xG-Korrektur -13 Elo; Tempo ×1.02
- **AS Roma**: Elo 1868 → 1853; Liga (football-data-xg, 10 Sp.): xG 2.26:1.37/Sp., Elo-Erwartung +1.26; Europapokal (3 Sp.): xG-Residuum -0.18/Sp.; xG-Korrektur -16 Elo; Tempo ×1.03
- **Feyenoord**: Elo 1730 → 1754; Liga (matchpulse, 11 Sp.): xG 2.89:1.07/Sp., Elo-Erwartung +1.28; Europapokal (3 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur +24 Elo; Tempo ×1.03
- **Inter**: Elo 1930 → 1919; Liga (football-data-xg, 10 Sp.): xG 2.70:1.06/Sp., Elo-Erwartung +1.67; Europapokal (3 Sp.): xG-Residuum -0.93/Sp.; xG-Korrektur -11 Elo; Tempo ×1.04
- **Bodo/Glimt**: Elo 1774 → 1758; Liga (matchpulse, 25 Sp.): xG 2.38:0.96/Sp., Elo-Erwartung +1.74; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur -16 Elo; Tempo ×1.02
- **Lille**: Elo 1779 → 1749; Liga (football-data-xg, 9 Sp.): xG 1.41:1.49/Sp., Elo-Erwartung +0.75; Europapokal (3 Sp.): xG-Residuum -0.13/Sp.; xG-Korrektur -31 Elo; Tempo ×0.98
- **Barcelona**: Elo 2020 → 2021; Liga (football-data-xg, 11 Sp.): xG 3.39:1.06/Sp., Elo-Erwartung +2.14; Europapokal (3 Sp.): xG-Residuum -0.63/Sp.; xG-Korrektur +1 Elo; Tempo ×1.10
- **Aston Villa**: Elo 1911 → 1878; Liga (football-data-xg, 9 Sp.): xG 1.20:1.68/Sp., Elo-Erwartung +0.80; Europapokal (3 Sp.): xG-Residuum +1.03/Sp.; xG-Korrektur -33 Elo; Tempo ×1.00
- **Atletico Madrid**: Elo 1924 → 1885; Liga (football-data-xg, 11 Sp.): xG 1.61:1.09/Sp., Elo-Erwartung +1.47; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -39 Elo; Tempo ×0.99
- **Bayern München**: Elo 2042 → 2060; Liga (matchpulse, 8 Sp.): xG 3.59:0.91/Sp., Elo-Erwartung +2.44; Europapokal (3 Sp.): xG-Residuum +0.80/Sp.; xG-Korrektur +18 Elo; Tempo ×1.05
- **Villarreal**: Elo 1789 → 1797; Liga (football-data-xg, 11 Sp.): xG 1.97:1.09/Sp., Elo-Erwartung +0.61; Europapokal (3 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur +8 Elo; Tempo ×1.01
- **Paris Saint Germain**: Elo 1986 → 2007; Europapokal (3 Sp.): xG-Residuum +1.05/Sp.; xG-Korrektur +21 Elo
- **Lask Linz**: Elo 1627 → 1631; Liga (matchpulse, 11 Sp.): xG 2.16:1.12/Sp., Elo-Erwartung +0.83; Europapokal (3 Sp.): xG-Residuum -0.38/Sp.; xG-Korrektur +4 Elo; Tempo ×1.00
- **Slovan Bratislava**: Elo 1557 → 1537; Europapokal (3 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -20 Elo
- **AEK Athens FC**: Elo 1689 → 1698; Liga (football-data-xg, 8 Sp.): xG 2.09:0.73/Sp., Elo-Erwartung +1.18; Europapokal (3 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur +9 Elo; Tempo ×1.01
- **Real Madrid**: Elo 2001 → 1982; Liga (football-data-xg, 11 Sp.): xG 2.48:1.01/Sp., Elo-Erwartung +2.00; Europapokal (3 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur -19 Elo; Tempo ×1.04
- **Fenerbahçe**: Elo 1757 → 1742; Liga (matchpulse, 10 Sp.): xG 2.09:1.21/Sp., Elo-Erwartung +1.28; Europapokal (3 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur -15 Elo; Tempo ×1.03
- **Liverpool**: Elo 1942 → 1918; Liga (football-data-xg, 9 Sp.): xG 1.46:1.17/Sp., Elo-Erwartung +0.99; Europapokal (3 Sp.): xG-Residuum +0.10/Sp.; xG-Korrektur -23 Elo; Tempo ×0.98
- **Lens**: Elo 1801 → 1779; Liga (football-data-xg, 9 Sp.): xG 1.69:1.49/Sp., Elo-Erwartung +0.88; Europapokal (3 Sp.): xG-Residuum +0.16/Sp.; xG-Korrektur -22 Elo; Tempo ×1.00
- **Como**: Elo 1830 → 1821; Liga (football-data-xg, 10 Sp.): xG 1.86:1.25/Sp., Elo-Erwartung +1.02; Europapokal (3 Sp.): xG-Residuum +0.56/Sp.; xG-Korrektur -9 Elo; Tempo ×1.00
- **Borussia Dortmund**: Elo 1896 → 1860; Liga (matchpulse, 8 Sp.): xG 1.55:1.48/Sp., Elo-Erwartung +1.39; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur -36 Elo; Tempo ×0.98
- **Real Betis**: Elo 1827 → 1793; Liga (football-data-xg, 11 Sp.): xG 1.61:1.82/Sp., Elo-Erwartung +0.85; Europapokal (3 Sp.): xG-Residuum +0.62/Sp.; xG-Korrektur -34 Elo; Tempo ×1.04
- **RB Leipzig**: Elo 1830 → 1828; Liga (matchpulse, 8 Sp.): xG 2.48:1.60/Sp., Elo-Erwartung +0.97; Europapokal (3 Sp.): xG-Residuum +0.13/Sp.; xG-Korrektur -1 Elo; Tempo ×1.03
- **Manchester City**: Elo 2000 → 1986; Liga (football-data-xg, 9 Sp.): xG 2.07:1.27/Sp., Elo-Erwartung +1.37; Europapokal (3 Sp.): xG-Residuum +0.46/Sp.; xG-Korrektur -15 Elo; Tempo ×1.03
- **PSV Eindhoven**: Elo 1782 → 1758; Liga (matchpulse, 11 Sp.): xG 2.38:1.31/Sp., Elo-Erwartung +1.62; Europapokal (3 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -25 Elo; Tempo ×1.01
- **Club Brugge KV**: Elo 1840 → 1812; Liga (matchpulse, 10 Sp.): xG 2.44:1.15/Sp., Elo-Erwartung +1.97; Europapokal (3 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -28 Elo; Tempo ×1.03
- **FC Porto**: Elo 1833 → 1805; Liga (matchpulse, 10 Sp.): xG 2.21:0.83/Sp., Elo-Erwartung +1.81; Europapokal (3 Sp.): xG-Residuum -1.11/Sp.; xG-Korrektur -28 Elo; Tempo ×1.03
- **Napoli**: Elo 1816 → 1787; Liga (football-data-xg, 10 Sp.): xG 1.74:1.28/Sp., Elo-Erwartung +0.93; Europapokal (3 Sp.): xG-Residuum -0.99/Sp.; xG-Korrektur -29 Elo; Tempo ×1.00
- **Slavia Praha**: Elo 1752 → 1761; Europapokal (3 Sp.): xG-Residuum +0.48/Sp.; xG-Korrektur +9 Elo
- **Arsenal (England)**: Elo 2060 → 2033; Liga (football-data-xg, 9 Sp.): xG 1.65:0.80/Sp., Elo-Erwartung +1.77; Europapokal (3 Sp.): xG-Residuum +0.44/Sp.; xG-Korrektur -27 Elo; Tempo ×0.97
- **Viking**: Elo 1705 → 1674; Liga (matchpulse, 25 Sp.): xG 2.00:1.12/Sp., Elo-Erwartung +1.28; Europapokal (3 Sp.): xG-Residuum -1.21/Sp.; xG-Korrektur -31 Elo; Tempo ×1.00
- **Sabah FA**: Elo 1558 → 1532; Europapokal (3 Sp.): xG-Residuum -1.30/Sp.; xG-Korrektur -26 Elo

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 16:30 | Rennes – Olympiakos Piraeus | 1715 : 1737 | 1.53 : 1.26 | 43 % | 26 % | 31 % | 53 % | 57 % | 42 % / 27 % / 31 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1746 : 1729 | 1.62 : 1.14 | 48 % | 26 % | 26 % | 52 % | 55 % | 49 % / 24 % / 27 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1536 : 1622 | 1.29 : 1.39 | 34 % | 27 % | 39 % | 50 % | 55 % | 33 % / 25 % / 42 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1573 : 1609 | 1.44 : 1.26 | 41 % | 27 % | 32 % | 51 % | 55 % | 53 % / 24 % / 23 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1809 : 1663 | 2.12 : 0.87 | 66 % | 21 % | 14 % | 57 % | 52 % | 71 % / 17 % / 11 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1746 : 1769 | 1.48 : 1.23 | 42 % | 27 % | 31 % | 51 % | 55 % | 52 % / 24 % / 24 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1660 : 1687 | 1.49 : 1.25 | 42 % | 27 % | 31 % | 52 % | 56 % | 49 % / 25 % / 26 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1627 : 1901 | 0.88 : 2.08 | 14 % | 21 % | 65 % | 57 % | 52 % | 16 % / 21 % / 63 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1588 : 1569 | 1.63 : 1.13 | 48 % | 26 % | 26 % | 52 % | 55 % | 48 % / 27 % / 26 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1833 : 1716 | 2.04 : 0.94 | 62 % | 22 % | 16 % | 57 % | 54 % | 68 % / 18 % / 14 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1676 : 1818 | 1.11 : 1.51 | 27 % | 27 % | 46 % | 49 % | 53 % | 26 % / 25 % / 49 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1851 : 1657 | 2.37 : 0.79 | 72 % | 18 % | 10 % | 61 % | 50 % | 79 % / 13 % / 7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1667 : 1712 | 1.45 : 1.32 | 40 % | 27 % | 34 % | 52 % | 57 % | 31 % / 25 % / 44 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1753 : 1791 | 1.45 : 1.28 | 40 % | 27 % | 33 % | 51 % | 56 % | 43 % / 26 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1628 : 1493 | 2.07 : 0.89 | 64 % | 21 % | 15 % | 57 % | 52 % | 45 % / 26 % / 29 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1618 : 1524 | 1.89 : 0.96 | 59 % | 23 % | 18 % | 54 % | 53 % | 62 % / 21 % / 17 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1724 : 1656 | 1.82 : 1.03 | 55 % | 24 % | 21 % | 54 % | 55 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1454 : 1437 | 1.62 : 1.14 | 48 % | 26 % | 26 % | 52 % | 55 % | 53 % / 24 % / 22 % |

<details><summary>Herleitung je Team</summary>

- **Rennes**: Elo 1744 → 1715; Liga (football-data-xg, 9 Sp.): xG 2.09:2.33/Sp., Elo-Erwartung +0.53; Europapokal (2 Sp.): xG-Residuum -0.06/Sp.; xG-Korrektur -29 Elo; Tempo ×1.06
- **Olympiakos Piraeus**: Elo 1744 → 1737; Liga (football-data-xg, 9 Sp.): xG 1.78:0.72/Sp., Elo-Erwartung +1.54; Europapokal (3 Sp.): xG-Residuum +0.80/Sp.; xG-Korrektur -7 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1780 → 1746; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung +0.01; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -34 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1722 → 1729; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung +0.31; Europapokal (2 Sp.): xG-Residuum -0.02/Sp.; xG-Korrektur +8 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1540 → 1536; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung +0.26; Europapokal (2 Sp.): xG-Residuum +1.24/Sp.; xG-Korrektur -4 Elo; Tempo ×0.98
- **Plzen**: Elo 1619 → 1622; Europapokal (2 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +3 Elo
- **NEC Nijmegen**: Elo 1587 → 1573; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.39; Europapokal (2 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur -14 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1633 → 1609; Europapokal (3 Sp.): xG-Residuum -1.20/Sp.; xG-Korrektur -24 Elo
- **AC Milan**: Elo 1827 → 1809; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +1.00; Europapokal (3 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur -18 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1674 → 1663; Europapokal (2 Sp.): xG-Residuum -0.76/Sp.; xG-Korrektur -11 Elo
- **Real Sociedad**: Elo 1783 → 1746; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.58; Europapokal (2 Sp.): xG-Residuum -0.29/Sp.; xG-Korrektur -38 Elo; Tempo ×1.01
- **Lyon**: Elo 1791 → 1769; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.82; Europapokal (3 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -22 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1659 → 1660; Liga (matchpulse, 10 Sp.): xG 1.74:1.01/Sp., Elo-Erwartung +0.78; Europapokal (3 Sp.): xG-Residuum +0.22/Sp.; xG-Korrektur +1 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1673 → 1687; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +1.12; Europapokal (2 Sp.): xG-Residuum -1.41/Sp.; xG-Korrektur +14 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1645 → 1627; Europapokal (2 Sp.): xG-Residuum -1.28/Sp.; xG-Korrektur -18 Elo
- **Bournemouth**: Elo 1886 → 1901; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.65; Europapokal (2 Sp.): xG-Residuum +1.89/Sp.; xG-Korrektur +14 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1594 → 1588; Europapokal (2 Sp.): xG-Residuum -0.45/Sp.; xG-Korrektur -6 Elo
- **Jagiellonia**: Elo 1597 → 1569; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.54; Europapokal (3 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur -28 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1843 → 1833; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +1.06; Europapokal (3 Sp.): xG-Residuum +1.65/Sp.; xG-Korrektur -10 Elo; Tempo ×1.01
- **Marseille**: Elo 1768 → 1716; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.68; Europapokal (2 Sp.): xG-Residuum -0.52/Sp.; xG-Korrektur -52 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1668 → 1676; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.88; Europapokal (3 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur +8 Elo; Tempo ×1.00
- **Juventus**: Elo 1824 → 1818; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +0.98; Europapokal (2 Sp.): xG-Residuum +0.16/Sp.; xG-Korrektur -6 Elo; Tempo ×0.91
- **Benfica**: Elo 1868 → 1851; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +2.06; Europapokal (3 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur -17 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1693 → 1657; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +1.13; Europapokal (2 Sp.): xG-Residuum -2.65/Sp.; xG-Korrektur -36 Elo; Tempo ×0.99
- **Celtic**: Elo 1656 → 1667; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.23; Europapokal (2 Sp.): xG-Residuum -0.79/Sp.; xG-Korrektur +11 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1709 → 1712; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +0.98; Europapokal (2 Sp.): xG-Residuum +0.98/Sp.; xG-Korrektur +3 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1737 → 1753; Europapokal (3 Sp.): xG-Residuum +0.79/Sp.; xG-Korrektur +16 Elo
- **Union St. Gilloise**: Elo 1818 → 1791; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.82; Europapokal (2 Sp.): xG-Residuum +0.34/Sp.; xG-Korrektur -27 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1645 → 1628; Europapokal (2 Sp.): xG-Residuum -1.15/Sp.; xG-Korrektur -16 Elo
- **OFI**: Elo 1500 → 1493; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung +0.03; Europapokal (2 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur -8 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1627 → 1618; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.83; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -9 Elo; Tempo ×0.99
- **Celje**: Elo 1517 → 1524; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur +7 Elo
- **Sunderland**: Elo 1711 → 1724; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.39; Europapokal (3 Sp.): xG-Residuum +0.76/Sp.; xG-Korrektur +13 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1654 → 1656; Europapokal (2 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur +3 Elo
- **Torreense**: Elo 1453 → 1454; Europapokal (2 Sp.): xG-Residuum +0.11/Sp.; xG-Korrektur +2 Elo
- **Ararat-Armenia**: Elo 1444 → 1437; Europapokal (2 Sp.): xG-Residuum -0.46/Sp.; xG-Korrektur -7 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1672 : 1701 | 1.42 : 1.21 | 41 % | 27 % | 31 % | 49 % | 54 % | 35 % / 25 % / 40 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1558 : 1701 | 1.09 : 1.49 | 27 % | 27 % | 46 % | 48 % | 52 % | 24 % / 29 % / 47 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1717 : 1429 | 2.77 : 0.63 | 82 % | 13 % | 6 % | 66 % | 44 % | 81 % / 12 % / 6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1670 : 1486 | 2.20 : 0.77 | 70 % | 19 % | 11 % | 57 % | 48 % | 89 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1556 : 1602 | 1.37 : 1.25 | 39 % | 28 % | 33 % | 48 % | 54 % | 12 % / 20 % / 68 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1684 : 1779 | 1.24 : 1.38 | 33 % | 27 % | 40 % | 49 % | 54 % | 37 % / 26 % / 37 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1515 : 1552 | 1.38 : 1.21 | 40 % | 28 % | 32 % | 48 % | 53 % | 40 % / 27 % / 34 % |
| Do 05.11. 18:45 | KuPS – Gent | 1438 : 1632 | 0.98 : 1.65 | 22 % | 26 % | 53 % | 49 % | 51 % | 20 % / 23 % / 57 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1493 : 1484 | 1.55 : 1.12 | 46 % | 27 % | 27 % | 50 % | 54 % | 42 % / 30 % / 28 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1743 : 1606 | 1.98 : 0.84 | 64 % | 22 % | 15 % | 54 % | 50 % | 64 % / 20 % / 16 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1671 : 1373 | 2.75 : 0.60 | 82 % | 13 % | 5 % | 65 % | 42 % | – |
| Do 05.11. 21:00 | Twente – Pafos | 1738 : 1571 | 2.13 : 0.80 | 68 % | 20 % | 12 % | 56 % | 49 % | 71 % / 17 % / 12 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1661 : 1897 | 0.90 : 1.81 | 18 % | 24 % | 58 % | 51 % | 50 % | 16 % / 24 % / 60 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1651 : 1369 | 2.68 : 0.62 | 80 % | 14 % | 6 % | 64 % | 44 % | 79 % / 13 % / 8 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1705 : 1538 | 2.15 : 0.81 | 68 % | 20 % | 12 % | 57 % | 49 % | 61 % / 22 % / 17 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1605 : 1441 | 2.11 : 0.80 | 67 % | 20 % | 13 % | 56 % | 49 % | 62 % / 22 % / 15 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1596 : 1556 | 1.68 : 1.07 | 51 % | 25 % | 24 % | 52 % | 54 % | 56 % / 24 % / 21 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1499 : 1558 | 1.33 : 1.28 | 37 % | 28 % | 35 % | 48 % | 54 % | 40 % / 28 % / 32 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1719 → 1672; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +1.32; Europapokal (2 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -47 Elo; Tempo ×1.00
- **Ajax**: Elo 1708 → 1701; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +1.13; Europapokal (2 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur -7 Elo; Tempo ×1.01
- **Aarhus**: Elo 1587 → 1558; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.50; Europapokal (2 Sp.): xG-Residuum -0.58/Sp.; xG-Korrektur -29 Elo; Tempo ×0.99
- **SC Braga**: Elo 1711 → 1701; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +1.01; Europapokal (2 Sp.): xG-Residuum +0.30/Sp.; xG-Korrektur -10 Elo; Tempo ×0.96
- **Atalanta**: Elo 1759 → 1717; Liga (football-data-xg, 9 Sp.): xG 1.39:2.05/Sp., Elo-Erwartung +0.58; Europapokal (2 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur -43 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1438 → 1429; Europapokal (2 Sp.): xG-Residuum -0.64/Sp.; xG-Korrektur -9 Elo
- **FK Crvena Zvezda**: Elo 1673 → 1670; Europapokal (2 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -4 Elo
- **Inter Club d'Escaldes**: Elo 1505 → 1486; Europapokal (2 Sp.): xG-Residuum -1.32/Sp.; xG-Korrektur -19 Elo
- **Lincoln Red Imps FC**: Elo 1606 → 1556; Europapokal (2 Sp.): xG-Residuum -3.49/Sp.; xG-Korrektur -50 Elo
- **HNK Hajduk Split**: Elo 1600 → 1602; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur +2 Elo
- **Trabzonspor**: Elo 1701 → 1684; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.92; Europapokal (2 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur -17 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1790 → 1779; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.72; Europapokal (2 Sp.): xG-Residuum -0.67/Sp.; xG-Korrektur -11 Elo; Tempo ×0.97
- **FC Thun**: Elo 1551 → 1515; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung +0.40; Europapokal (2 Sp.): xG-Residuum +0.16/Sp.; xG-Korrektur -36 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1561 → 1552; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.64; Europapokal (2 Sp.): xG-Residuum +0.76/Sp.; xG-Korrektur -9 Elo; Tempo ×1.00
- **KuPS**: Elo 1446 → 1438; Europapokal (2 Sp.): xG-Residuum -0.55/Sp.; xG-Korrektur -8 Elo
- **Gent**: Elo 1642 → 1632; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.67; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -10 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1506 → 1493; Liga (matchpulse, 27 Sp.): xG 1.48:1.66/Sp., Elo-Erwartung +0.15; Europapokal (2 Sp.): xG-Residuum +1.31/Sp.; xG-Korrektur -14 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1504 → 1484; Europapokal (2 Sp.): xG-Residuum -1.45/Sp.; xG-Korrektur -21 Elo
- **Monaco**: Elo 1781 → 1743; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -38 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1615 → 1606; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.67; Europapokal (2 Sp.): xG-Residuum -1.42/Sp.; xG-Korrektur -10 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1692 → 1671; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +1.15; Europapokal (2 Sp.): xG-Residuum +0.32/Sp.; xG-Korrektur -21 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1386 → 1373; Europapokal (2 Sp.): xG-Residuum -0.95/Sp.; xG-Korrektur -14 Elo
- **Twente**: Elo 1699 → 1738; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +1.07; Europapokal (2 Sp.): xG-Residuum +2.75/Sp.; xG-Korrektur +39 Elo; Tempo ×1.00
- **Pafos**: Elo 1581 → 1571; Europapokal (2 Sp.): xG-Residuum -0.68/Sp.; xG-Korrektur -10 Elo
- **Getafe**: Elo 1676 → 1661; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.06; Europapokal (2 Sp.): xG-Residuum +0.90/Sp.; xG-Korrektur -15 Elo; Tempo ×0.93
- **Brighton**: Elo 1908 → 1897; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.79; Europapokal (2 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur -11 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1676 → 1651; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +1.17; Europapokal (2 Sp.): xG-Residuum -0.05/Sp.; xG-Korrektur -25 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1391 → 1369; Europapokal (2 Sp.): xG-Residuum -1.57/Sp.; xG-Korrektur -22 Elo
- **Panathinaikos**: Elo 1671 → 1705; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +1.06; Europapokal (2 Sp.): xG-Residuum +2.14/Sp.; xG-Korrektur +34 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1518 → 1538; Europapokal (2 Sp.): xG-Residuum +1.41/Sp.; xG-Korrektur +20 Elo
- **Universitatea Craiova**: Elo 1604 → 1605; Europapokal (2 Sp.): xG-Residuum +0.06/Sp.; xG-Korrektur +1 Elo
- **Egnatia Rrogozhinë**: Elo 1440 → 1441; Europapokal (2 Sp.): xG-Residuum +0.02/Sp.; xG-Korrektur +0 Elo
- **St. Truiden**: Elo 1607 → 1596; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.46; Europapokal (2 Sp.): xG-Residuum +0.61/Sp.; xG-Korrektur -11 Elo; Tempo ×1.04
- **Brann**: Elo 1580 → 1556; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.50; Europapokal (2 Sp.): xG-Residuum +1.92/Sp.; xG-Korrektur -24 Elo; Tempo ×1.02
- **Riga**: Elo 1497 → 1499; Europapokal (2 Sp.): xG-Residuum +0.14/Sp.; xG-Korrektur +2 Elo
- **FK Jablonec**: Elo 1541 → 1558; Europapokal (2 Sp.): xG-Residuum +1.18/Sp.; xG-Korrektur +17 Elo

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 34 Spiele ausgewertet, Log-Loss 1X2 Modell 1.021
- Gegen Pinnacle (34 Spiele): Modell 1.021 vs. Pinnacle 1.003 (kleiner = besser)
- Value-Wetten: 42, Ergebnis -4.62 Einheiten, ROI -11.0 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Hinweise
- Liga 261/2026: API-Football /fixtures?league=261&season=2026&timezone=UTC: HTTP 429 · {"get": "","parameters": [],"errors": {"rateLimit": "Too many requests. You have reached your per-minute request limit. Please wait a few seconds before retrying or upgrade your plan for higher limits."},"results": 0,"paging": {"current": 1,"total": 1},"response": []}
- ClubElo heute nicht erreichbar (ClubElo nicht erreichbar (https://clubelo.com/ARM: HTTP 403 · <!DOCTYPE html><html lang="en-US"><head><title>Just a mome) – eigene Elo-Rechnung

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
