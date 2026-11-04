# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 04.11.2026 14:14 (Wien), Spiele 04.11. bis 06.11.2026

## Datenbasis
- Elo: ClubElo live (590 Teams zugeordnet)
- Ergebnisbasis: 39120 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1152 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-185 Elo, 2 Sp.), Gibraltar (-360 Elo, 48 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-470 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 780 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 60 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 60 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 62 Teams, Europapokal-xG aus 141 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 252 | 3.56 | 3.01 | ×1.116 | 52 % |
| Conference League | 285 | 2.62 | 2.98 | ×0.921 | 47 % |
| Europa League | 243 | 2.77 | 2.95 | ×0.964 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 375 | 68.0 % | 63.2 % |
| Heimteam Außenseiter | 402 | 31.1 % | 30.1 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 8 % | 3 % | 34.00 | +164.2 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 10 % | 7 % | 19.00 | +95.6 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1 | 14 % | 7 % | 13.00 | +82.6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 16 % | 7 % | 11.00 | +75.0 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1 | 26 % | 15 % | 6.25 | +63.0 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1 | 12 % | 8 % | 12.00 | +49.0 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1 | 26 % | 18 % | 5.50 | +42.8 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 18 % | 13 % | 8.00 | +41.9 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | U2.5 | 39 % | 29 % | 3.50 | +38.2 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | U2.5 | 48 % | 34 % | 2.88 | +38.0 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | U2.5 | 40 % | 26 % | 3.40 | +34.9 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | U2.5 | 38 % | 30 % | 3.40 | +30.9 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | U2.5 | 37 % | 27 % | 3.50 | +29.7 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | X | 17 % | 13 % | 7.50 | +29.4 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 28 % | 22 % | 4.50 | +26.9 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 21 % | 18 % | 6.00 | +26.7 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 53 % | 38 % | 2.40 | +26.4 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 31 % | 23 % | 4.00 | +25.8 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 20 % | 16 % | 6.25 | +25.3 % |
| Do 05.11. 21:00 | Twente – Pafos | U2.5 | 46 % | 34 % | 2.70 | +24.5 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | X | 24 % | 18 % | 5.25 | +23.5 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | X | 19 % | 15 % | 6.50 | +22.9 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | U2.5 | 38 % | 31 % | 3.20 | +22.8 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 29 % | 23 % | 4.20 | +21.7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 49 % | 38 % | 2.50 | +21.7 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 49 % | 38 % | 2.50 | +21.4 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 19 % | 15 % | 6.25 | +21.3 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 51 % | 39 % | 2.38 | +20.2 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 50 % | 38 % | 2.38 | +18.8 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 50 % | 40 % | 2.38 | +18.7 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1 | 15 % | 12 % | 8.00 | +18.7 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 33 % | 2.75 | +17.9 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | U2.5 | 31 % | 26 % | 3.75 | +17.9 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 2 | 36 % | 29 % | 3.25 | +17.3 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | U2.5 | 34 % | 28 % | 3.40 | +17.1 % |
| Do 05.11. 21:00 | St. Truiden – Brann | U2.5 | 49 % | 39 % | 2.38 | +16.8 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 38 % | 31 % | 3.10 | +16.7 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 21 % | 17 % | 5.50 | +16.2 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 23 % | 19 % | 5.00 | +15.1 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 2 | 29 % | 24 % | 4.00 | +14.8 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | X | 20 % | 18 % | 5.75 | +14.8 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 37 % | 29 % | 3.10 | +14.7 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 42 % | 37 % | 2.70 | +13.9 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 24 % | 4.20 | +13.3 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 49 % | 41 % | 2.30 | +12.6 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 24 % | 21 % | 4.75 | +12.3 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 22 % | 19 % | 5.00 | +12.1 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | X | 23 % | 20 % | 4.75 | +10.2 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +10.1 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1 | 35 % | 32 % | 3.10 | +9.7 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | O2.5 | 65 % | 57 % | 1.67 | +8.4 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1 | 28 % | 24 % | 3.80 | +7.7 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 2 | 14 % | 13 % | 7.50 | +7.5 % |
| Do 05.11. 21:00 | Twente – Pafos | 2 | 13 % | 12 % | 8.00 | +7.1 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 2 | 29 % | 26 % | 3.70 | +6.7 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | O2.5 | 62 % | 57 % | 1.73 | +6.5 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 38 % | 2.50 | +6.5 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1 | 48 % | 41 % | 2.20 | +6.4 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | X | 25 % | 23 % | 4.33 | +6.3 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- Lens – Como: 1 Modell 41 % vs. Pinnacle 26 %
- FC Midtjylland – Ajax: U2.5 Modell 52 % vs. Pinnacle 36 %
- FC Thun – Heart Of Midlothian: U2.5 Modell 53 % vs. Pinnacle 38 %
- Hapoel Beer Sheva – OFI: 1 Modell 62 % vs. Pinnacle 45 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1710 : 2005 | 1.00 : 2.54 | 12 % | 17 % | 70 % | 69 % | 59 % | 8 % / 13 % / 79 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1768 : 1927 | 1.30 : 1.88 | 26 % | 24 % | 50 % | 62 % | 62 % | 15 % / 18 % / 67 % |
| Mi 04.11. 21:00 | Lens – Como | 1792 : 1838 | 1.64 : 1.47 | 41 % | 25 % | 34 % | 60 % | 63 % | 26 % / 25 % / 50 % |
| Mi 04.11. 21:00 | Borussia Dortmund – Real Betis | 1874 : 1814 | 2.00 : 1.22 | 55 % | 23 % | 22 % | 62 % | 61 % | 58 % / 23 % / 20 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1846 : 2006 | 1.33 : 1.92 | 26 % | 23 % | 51 % | 63 % | 63 % | 18 % / 20 % / 62 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 1769 : 1829 | 1.63 : 1.55 | 39 % | 25 % | 36 % | 62 % | 64 % | 49 % / 23 % / 29 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 1819 : 1813 | 1.81 : 1.37 | 47 % | 24 % | 29 % | 62 % | 63 % | 51 % / 26 % / 24 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1759 : 2035 | 1.00 : 2.35 | 14 % | 19 % | 67 % | 65 % | 57 % | 7 % / 15 % / 78 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 1689 : 1549 | 2.36 : 1.02 | 67 % | 19 % | 14 % | 66 % | 58 % | 70 % / 17 % / 13 % |

<details><summary>Herleitung je Team</summary>

- **AEK Athens FC**: Elo 1693 → 1710; Liga (football-data-xg, 8 Sp.): xG 2.09:0.73/Sp., Elo-Erwartung +0.96; Europapokal (3 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur +17 Elo; Tempo ×1.01
- **Real Madrid**: Elo 1995 → 2005; Liga (football-data-xg, 11 Sp.): xG 2.48:1.01/Sp., Elo-Erwartung +1.32; Europapokal (3 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur +9 Elo; Tempo ×1.04
- **Fenerbahçe**: Elo 1767 → 1768; Liga (matchpulse, 10 Sp.): xG 2.09:1.21/Sp., Elo-Erwartung +0.85; Europapokal (3 Sp.): xG-Residuum +0.00/Sp.; xG-Korrektur +1 Elo; Tempo ×1.03
- **Liverpool**: Elo 1939 → 1927; Liga (football-data-xg, 9 Sp.): xG 1.46:1.17/Sp., Elo-Erwartung +0.56; Europapokal (3 Sp.): xG-Residuum -0.18/Sp.; xG-Korrektur -12 Elo; Tempo ×0.98
- **Lens**: Elo 1802 → 1792; Liga (football-data-xg, 9 Sp.): xG 1.69:1.49/Sp., Elo-Erwartung +0.52; Europapokal (3 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur -11 Elo; Tempo ×1.00
- **Como**: Elo 1827 → 1838; Liga (football-data-xg, 10 Sp.): xG 1.86:1.25/Sp., Elo-Erwartung +0.48; Europapokal (3 Sp.): xG-Residuum +0.54/Sp.; xG-Korrektur +11 Elo; Tempo ×1.00
- **Borussia Dortmund**: Elo 1894 → 1874; Liga (matchpulse, 8 Sp.): xG 1.55:1.48/Sp., Elo-Erwartung +0.82; Europapokal (3 Sp.): xG-Residuum +0.30/Sp.; xG-Korrektur -21 Elo; Tempo ×0.98
- **Real Betis**: Elo 1826 → 1814; Liga (football-data-xg, 11 Sp.): xG 1.61:1.82/Sp., Elo-Erwartung +0.28; Europapokal (3 Sp.): xG-Residuum +0.65/Sp.; xG-Korrektur -12 Elo; Tempo ×1.04
- **RB Leipzig**: Elo 1831 → 1846; Liga (matchpulse, 8 Sp.): xG 2.48:1.60/Sp., Elo-Erwartung +0.44; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur +15 Elo; Tempo ×1.03
- **Manchester City**: Elo 2011 → 2006; Liga (football-data-xg, 9 Sp.): xG 2.07:1.27/Sp., Elo-Erwartung +1.00; Europapokal (3 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur -5 Elo; Tempo ×1.03
- **PSV Eindhoven**: Elo 1783 → 1769; Liga (matchpulse, 11 Sp.): xG 2.38:1.31/Sp., Elo-Erwartung +1.33; Europapokal (3 Sp.): xG-Residuum -0.34/Sp.; xG-Korrektur -14 Elo; Tempo ×1.01
- **Club Brugge KV**: Elo 1836 → 1829; Liga (matchpulse, 10 Sp.): xG 2.44:1.15/Sp., Elo-Erwartung +1.41; Europapokal (3 Sp.): xG-Residuum -0.24/Sp.; xG-Korrektur -7 Elo; Tempo ×1.03
- **FC Porto**: Elo 1832 → 1819; Liga (matchpulse, 10 Sp.): xG 2.21:0.83/Sp., Elo-Erwartung +1.43; Europapokal (3 Sp.): xG-Residuum -1.03/Sp.; xG-Korrektur -13 Elo; Tempo ×1.03
- **Napoli**: Elo 1826 → 1813; Liga (football-data-xg, 10 Sp.): xG 1.74:1.28/Sp., Elo-Erwartung +0.47; Europapokal (3 Sp.): xG-Residuum -1.10/Sp.; xG-Korrektur -13 Elo; Tempo ×1.00
- **Slavia Praha**: Elo 1746 → 1759; Europapokal (3 Sp.): xG-Residuum +0.66/Sp.; xG-Korrektur +13 Elo
- **Arsenal (England)**: Elo 2045 → 2035; Liga (football-data-xg, 9 Sp.): xG 1.65:0.80/Sp., Elo-Erwartung +1.21; Europapokal (3 Sp.): xG-Residuum +0.29/Sp.; xG-Korrektur -9 Elo; Tempo ×0.97
- **Viking**: Elo 1707 → 1689; Liga (matchpulse, 25 Sp.): xG 2.00:1.12/Sp., Elo-Erwartung +1.08; Europapokal (3 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur -18 Elo; Tempo ×1.00
- **Sabah FA**: Elo 1567 → 1549; Europapokal (3 Sp.): xG-Residuum -0.91/Sp.; xG-Korrektur -18 Elo

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 16:30 | Rennes – Olympiakos Piraeus | 1735 : 1747 | 1.56 : 1.21 | 45 % | 26 % | 29 % | 52 % | 56 % | 43 % / 27 % / 30 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1780 : 1754 | 1.61 : 1.12 | 48 % | 26 % | 26 % | 51 % | 55 % | 50 % / 24 % / 26 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1542 : 1622 | 1.31 : 1.35 | 35 % | 27 % | 37 % | 49 % | 55 % | 32 % / 25 % / 44 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1583 : 1616 | 1.45 : 1.23 | 42 % | 27 % | 31 % | 50 % | 55 % | 53 % / 24 % / 23 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1830 : 1663 | 2.15 : 0.83 | 67 % | 20 % | 13 % | 57 % | 50 % | 69 % / 18 % / 12 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1772 : 1785 | 1.50 : 1.17 | 44 % | 27 % | 29 % | 50 % | 54 % | 54 % / 23 % / 23 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1677 : 1688 | 1.53 : 1.19 | 45 % | 26 % | 29 % | 51 % | 55 % | 49 % / 25 % / 26 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1629 : 1914 | 0.86 : 2.09 | 14 % | 21 % | 65 % | 57 % | 51 % | 16 % / 21 % / 64 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1592 : 1572 | 1.59 : 1.14 | 47 % | 26 % | 27 % | 51 % | 55 % | 47 % / 27 % / 26 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1864 : 1726 | 2.07 : 0.90 | 64 % | 21 % | 15 % | 57 % | 52 % | 70 % / 17 % / 13 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1695 : 1840 | 1.10 : 1.49 | 27 % | 27 % | 46 % | 48 % | 52 % | 27 % / 26 % / 47 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1862 : 1660 | 2.35 : 0.78 | 72 % | 18 % | 10 % | 61 % | 49 % | 80 % / 13 % / 7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1667 : 1730 | 1.39 : 1.34 | 38 % | 27 % | 35 % | 51 % | 56 % | 31 % / 24 % / 45 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1758 : 1808 | 1.40 : 1.28 | 39 % | 27 % | 34 % | 50 % | 55 % | 42 % / 26 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1618 : 1492 | 1.98 : 0.91 | 62 % | 22 % | 16 % | 55 % | 52 % | 45 % / 26 % / 29 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1633 : 1526 | 1.89 : 0.94 | 59 % | 23 % | 18 % | 54 % | 52 % | 62 % / 21 % / 17 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1750 : 1662 | 1.85 : 0.99 | 57 % | 24 % | 19 % | 54 % | 54 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1444 : 1438 | 1.54 : 1.17 | 45 % | 26 % | 28 % | 51 % | 55 % | 53 % / 24 % / 22 % |

<details><summary>Herleitung je Team</summary>

- **Rennes**: Elo 1753 → 1735; Liga (football-data-xg, 9 Sp.): xG 2.09:2.33/Sp., Elo-Erwartung +0.23; Europapokal (2 Sp.): xG-Residuum -0.10/Sp.; xG-Korrektur -18 Elo; Tempo ×1.06
- **Olympiakos Piraeus**: Elo 1746 → 1747; Liga (football-data-xg, 9 Sp.): xG 1.78:0.72/Sp., Elo-Erwartung +1.29; Europapokal (3 Sp.): xG-Residuum +0.79/Sp.; xG-Korrektur +1 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1810 → 1780; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung -0.13; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur -30 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1734 → 1754; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung -0.07; Europapokal (2 Sp.): xG-Residuum -0.13/Sp.; xG-Korrektur +20 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1533 → 1542; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung +0.04; Europapokal (2 Sp.): xG-Residuum +1.17/Sp.; xG-Korrektur +9 Elo; Tempo ×0.98
- **Plzen**: Elo 1620 → 1622; Europapokal (2 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur +2 Elo
- **NEC Nijmegen**: Elo 1590 → 1583; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.15; Europapokal (2 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur -7 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1636 → 1616; Europapokal (3 Sp.): xG-Residuum -1.00/Sp.; xG-Korrektur -20 Elo
- **AC Milan**: Elo 1831 → 1830; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +0.50; Europapokal (3 Sp.): xG-Residuum +0.07/Sp.; xG-Korrektur -1 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1667 → 1663; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur -4 Elo
- **Real Sociedad**: Elo 1789 → 1772; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.06; Europapokal (2 Sp.): xG-Residuum -0.32/Sp.; xG-Korrektur -17 Elo; Tempo ×1.01
- **Lyon**: Elo 1792 → 1785; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.46; Europapokal (3 Sp.): xG-Residuum -0.60/Sp.; xG-Korrektur -8 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1662 → 1677; Liga (matchpulse, 10 Sp.): xG 1.74:1.01/Sp., Elo-Erwartung +0.33; Europapokal (3 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur +15 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1659 → 1688; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum -1.40/Sp.; xG-Korrektur +29 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1644 → 1629; Europapokal (2 Sp.): xG-Residuum -1.08/Sp.; xG-Korrektur -16 Elo
- **Bournemouth**: Elo 1887 → 1914; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.25; Europapokal (2 Sp.): xG-Residuum +1.65/Sp.; xG-Korrektur +27 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1594 → 1592; Europapokal (2 Sp.): xG-Residuum -0.14/Sp.; xG-Korrektur -2 Elo
- **Jagiellonia**: Elo 1591 → 1572; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.29; Europapokal (3 Sp.): xG-Residuum -0.72/Sp.; xG-Korrektur -19 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1865 → 1864; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +0.64; Europapokal (3 Sp.): xG-Residuum +1.28/Sp.; xG-Korrektur -1 Elo; Tempo ×1.01
- **Marseille**: Elo 1765 → 1726; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.30; Europapokal (2 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur -39 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1681 → 1695; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.69; Europapokal (3 Sp.): xG-Residuum +0.31/Sp.; xG-Korrektur +14 Elo; Tempo ×1.00
- **Juventus**: Elo 1828 → 1840; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +0.48; Europapokal (2 Sp.): xG-Residuum +0.08/Sp.; xG-Korrektur +12 Elo; Tempo ×0.91
- **Benfica**: Elo 1865 → 1862; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +1.65; Europapokal (3 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur -3 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1681 → 1660; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +0.84; Europapokal (2 Sp.): xG-Residuum -2.32/Sp.; xG-Korrektur -22 Elo; Tempo ×0.99
- **Celtic**: Elo 1650 → 1667; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.15; Europapokal (2 Sp.): xG-Residuum -0.47/Sp.; xG-Korrektur +17 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1707 → 1730; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +0.48; Europapokal (2 Sp.): xG-Residuum +1.15/Sp.; xG-Korrektur +24 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1746 → 1758; Europapokal (3 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur +12 Elo
- **Union St. Gilloise**: Elo 1817 → 1808; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.28; Europapokal (2 Sp.): xG-Residuum +0.07/Sp.; xG-Korrektur -9 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1630 → 1618; Europapokal (2 Sp.): xG-Residuum -0.81/Sp.; xG-Korrektur -12 Elo
- **OFI**: Elo 1490 → 1492; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung -0.18; Europapokal (2 Sp.): xG-Residuum -0.33/Sp.; xG-Korrektur +1 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1630 → 1633; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.59; Europapokal (2 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur +3 Elo; Tempo ×0.99
- **Celje**: Elo 1513 → 1526; Europapokal (3 Sp.): xG-Residuum +0.66/Sp.; xG-Korrektur +13 Elo
- **Sunderland**: Elo 1732 → 1750; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.60; Europapokal (3 Sp.): xG-Residuum +0.65/Sp.; xG-Korrektur +19 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1655 → 1662; Europapokal (2 Sp.): xG-Residuum +0.46/Sp.; xG-Korrektur +7 Elo
- **Torreense**: Elo 1452 → 1444; Europapokal (2 Sp.): xG-Residuum -0.52/Sp.; xG-Korrektur -8 Elo
- **Ararat-Armenia**: Elo 1439 → 1438; Europapokal (2 Sp.): xG-Residuum -0.06/Sp.; xG-Korrektur -1 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1682 : 1707 | 1.42 : 1.16 | 42 % | 27 % | 30 % | 48 % | 53 % | 37 % / 25 % / 39 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1576 : 1711 | 1.09 : 1.42 | 28 % | 28 % | 44 % | 46 % | 51 % | 24 % / 28 % / 48 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1759 : 1437 | 2.88 : 0.58 | 84 % | 12 % | 5 % | 67 % | 42 % | 82 % / 12 % / 6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1667 : 1416 | 2.45 : 0.67 | 76 % | 16 % | 8 % | 60 % | 45 % | 90 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1332 : 1606 | 0.84 : 1.95 | 15 % | 22 % | 63 % | 53 % | 49 % | 12 % / 19 % / 69 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1698 : 1791 | 1.22 : 1.34 | 33 % | 28 % | 39 % | 47 % | 53 % | 37 % / 26 % / 36 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1526 : 1544 | 1.42 : 1.13 | 43 % | 28 % | 29 % | 47 % | 52 % | 42 % / 26 % / 32 % |
| Do 05.11. 18:45 | KuPS – Gent | 1464 : 1649 | 0.98 : 1.57 | 23 % | 26 % | 51 % | 47 % | 50 % | 19 % / 23 % / 58 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1507 : 1474 | 1.57 : 1.07 | 48 % | 26 % | 25 % | 49 % | 52 % | 41 % / 30 % / 29 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1761 : 1622 | 1.93 : 0.83 | 63 % | 22 % | 15 % | 52 % | 49 % | 66 % / 19 % / 15 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1684 : 1380 | 2.70 : 0.59 | 82 % | 13 % | 5 % | 64 % | 42 % | – |
| Do 05.11. 21:00 | Twente – Pafos | 1731 : 1570 | 2.03 : 0.80 | 65 % | 21 % | 13 % | 54 % | 48 % | 70 % / 18 % / 12 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1684 : 1899 | 0.93 : 1.68 | 20 % | 25 % | 55 % | 48 % | 50 % | 16 % / 24 % / 60 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1665 : 1376 | 2.64 : 0.61 | 80 % | 14 % | 6 % | 63 % | 43 % | 80 % / 12 % / 7 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1710 : 1542 | 2.08 : 0.80 | 67 % | 21 % | 13 % | 55 % | 49 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1598 : 1438 | 2.03 : 0.81 | 65 % | 21 % | 13 % | 54 % | 49 % | 64 % / 22 % / 14 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1617 : 1562 | 1.68 : 1.04 | 52 % | 25 % | 23 % | 51 % | 53 % | 56 % / 24 % / 21 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1506 : 1572 | 1.30 : 1.26 | 37 % | 28 % | 35 % | 47 % | 53 % | 41 % / 28 % / 32 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1712 → 1682; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +0.93; Europapokal (2 Sp.): xG-Residuum -0.39/Sp.; xG-Korrektur -31 Elo; Tempo ×1.00
- **Ajax**: Elo 1701 → 1707; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +0.82; Europapokal (2 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur +5 Elo; Tempo ×1.01
- **Aarhus**: Elo 1593 → 1576; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.22; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -17 Elo; Tempo ×0.99
- **SC Braga**: Elo 1706 → 1711; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +0.64; Europapokal (2 Sp.): xG-Residuum +0.37/Sp.; xG-Korrektur +4 Elo; Tempo ×0.96
- **Atalanta**: Elo 1781 → 1759; Liga (football-data-xg, 10 Sp.): xG 1.53:1.88/Sp., Elo-Erwartung +0.21; Europapokal (2 Sp.): xG-Residuum +0.01/Sp.; xG-Korrektur -22 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1444 → 1437; Europapokal (2 Sp.): xG-Residuum -0.52/Sp.; xG-Korrektur -7 Elo
- **FK Crvena Zvezda**: Elo 1663 → 1667; Europapokal (2 Sp.): xG-Residuum +0.28/Sp.; xG-Korrektur +4 Elo
- **Inter Club d'Escaldes**: Elo 1426 → 1416; Europapokal (2 Sp.): xG-Residuum -0.70/Sp.; xG-Korrektur -10 Elo
- **Lincoln Red Imps FC**: Elo 1356 → 1332; Europapokal (2 Sp.): xG-Residuum -1.67/Sp.; xG-Korrektur -24 Elo
- **HNK Hajduk Split**: Elo 1602 → 1606; Europapokal (2 Sp.): xG-Residuum +0.29/Sp.; xG-Korrektur +4 Elo
- **Trabzonspor**: Elo 1700 → 1698; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.44; Europapokal (2 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -2 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1786 → 1791; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.17; Europapokal (2 Sp.): xG-Residuum -0.91/Sp.; xG-Korrektur +6 Elo; Tempo ×0.97
- **FC Thun**: Elo 1546 → 1526; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung +0.02; Europapokal (2 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur -20 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1545 → 1544; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.51; Europapokal (2 Sp.): xG-Residuum +1.10/Sp.; xG-Korrektur -1 Elo; Tempo ×1.00
- **KuPS**: Elo 1468 → 1464; Europapokal (2 Sp.): xG-Residuum -0.29/Sp.; xG-Korrektur -4 Elo
- **Gent**: Elo 1641 → 1649; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.21; Europapokal (2 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur +7 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1513 → 1507; Liga (matchpulse, 27 Sp.): xG 1.49:1.66/Sp., Elo-Erwartung -0.01; Europapokal (2 Sp.): xG-Residuum +0.74/Sp.; xG-Korrektur -6 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1491 → 1474; Europapokal (2 Sp.): xG-Residuum -1.17/Sp.; xG-Korrektur -17 Elo
- **Monaco**: Elo 1790 → 1761; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.45; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -29 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1621 → 1622; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.38; Europapokal (2 Sp.): xG-Residuum -1.80/Sp.; xG-Korrektur +1 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1692 → 1684; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +0.81; Europapokal (2 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur -8 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1383 → 1380; Europapokal (2 Sp.): xG-Residuum -0.23/Sp.; xG-Korrektur -3 Elo
- **Twente**: Elo 1683 → 1731; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +0.71; Europapokal (2 Sp.): xG-Residuum +1.85/Sp.; xG-Korrektur +48 Elo; Tempo ×1.00
- **Pafos**: Elo 1580 → 1570; Europapokal (2 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur -9 Elo
- **Getafe**: Elo 1684 → 1684; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.49; Europapokal (2 Sp.): xG-Residuum +0.73/Sp.; xG-Korrektur +1 Elo; Tempo ×0.93
- **Brighton**: Elo 1903 → 1899; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.35; Europapokal (2 Sp.): xG-Residuum -1.05/Sp.; xG-Korrektur -4 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1675 → 1665; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +0.79; Europapokal (2 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -10 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1384 → 1376; Europapokal (2 Sp.): xG-Residuum -0.55/Sp.; xG-Korrektur -8 Elo
- **Panathinaikos**: Elo 1671 → 1710; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +0.82; Europapokal (2 Sp.): xG-Residuum +1.65/Sp.; xG-Korrektur +39 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1515 → 1542; Europapokal (2 Sp.): xG-Residuum +1.90/Sp.; xG-Korrektur +27 Elo
- **Universitatea Craiova**: Elo 1599 → 1598; Europapokal (2 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -2 Elo
- **Egnatia Rrogozhinë**: Elo 1432 → 1438; Europapokal (2 Sp.): xG-Residuum +0.43/Sp.; xG-Korrektur +6 Elo
- **St. Truiden**: Elo 1617 → 1617; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.07; Europapokal (2 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur -0 Elo; Tempo ×1.04
- **Brann**: Elo 1582 → 1562; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.32; Europapokal (2 Sp.): xG-Residuum +0.75/Sp.; xG-Korrektur -19 Elo; Tempo ×1.02
- **Riga**: Elo 1499 → 1506; Europapokal (2 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur +7 Elo
- **FK Jablonec**: Elo 1547 → 1572; Europapokal (2 Sp.): xG-Residuum +1.73/Sp.; xG-Korrektur +25 Elo

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 43 Spiele ausgewertet, Log-Loss 1X2 Modell 0.961
- Gegen Pinnacle (43 Spiele): Modell 0.961 vs. Pinnacle 0.947 (kleiner = besser)
- Value-Wetten: 54, Ergebnis -10.92 Einheiten, ROI -20.2 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
